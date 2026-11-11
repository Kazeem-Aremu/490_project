"""
WebSocket front door for the browser (student-portal).

Browsers cannot open the raw TCP socket on 8342, so this listens on ws://127.0.0.1:8343
and hands every request to the SAME Server.handle_Requests the TCP clients use. Messages
are the same JSON envelopes described in Docs/Server_API_Documentation.md, with two
browser-only additions:

  * REQUESTID  - optional top-level field; echoed back on the reply so the page can
                 match replies to requests (AI replies can arrive out of order).
  * login      - {"MESSAGE":{"METHOD":"POST","INFO":"login","PARAMS":{"TOKEN":<supabase access token>}}}
                 Must succeed before any other request on this connection. After that the
                 server fills in USERID itself, so a page can never act as another student.

Started from SocketServer.main() in a background thread; it can also run on its own:
    py Server/WebSocketServer.py
"""
import asyncio
import json
import threading
import traceback

from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

from AuthService import AuthService

WS_HOST = "127.0.0.1"
WS_PORT = 8343

## requests whose USERID must be the signed-in user's
USER_SCOPED_POSTS = {"startAIConversation", "sendAIMessage", "createSubmission", "enrollStudent", "unenrollStudent", "createCourse",
                     "createAssignment", "assignmentFile"}
USER_SCOPED_GETS = {"StudentList"}


class WebSocketBridge:
    def __init__(self, server, host=WS_HOST, port=WS_PORT):
        self.server = server
        self.host = host
        self.port = port
        self.auth = AuthService(server.database)

    def handle(self, data, session):
        """Runs in a worker thread (database and AI calls block). Returns a response dict or None."""
        if not isinstance(data, dict) or not isinstance(data.get("MESSAGE"), dict):
            return self.server.error("400", "Missing MESSAGE object", data)
        message = data["MESSAGE"]
        method, info = message.get("METHOD"), message.get("INFO")

        if method == "HANDSHAKE":
            return None  # the TCP protocol's ack; nothing to answer

        if method == "POST" and info == "login":
            params = message.get("PARAMS") if isinstance(message.get("PARAMS"), dict) else {}
            user, problem = self.auth.login(params.get("TOKEN"))
            if problem:
                session["user"] = None
                return problem
            session["user"] = user
            return {"Response Code": "200", "MESSAGE": {"USER": user}}

        user = session.get("user")
        if user is None:
            return self.server.error("401", "Sign in first (send a login request with your session token)")

        if (method == "POST" and info in USER_SCOPED_POSTS) or (method == "GET" and info in USER_SCOPED_GETS):
            params = message.get("PARAMS")
            if not isinstance(params, dict):
                return self.server.error("400", "Missing PARAMS", data)
            data = {**data, "MESSAGE": {**message, "PARAMS": {**params, "USERID": user["id"]}}}

        return self.server.handle_Requests(data)

    async def client(self, ws):
        addr = ws.remote_address
        print(f"[ws {addr}] connected")
        session = {"user": None}
        pending = set()

        async def answer(data, request_id):
            try:
                response = await asyncio.to_thread(self.handle, data, session)
            except Exception as e:
                traceback.print_exc()
                response = self.server.error("500", f"Internal Server error: {e}")
            if response is None:
                return
            if request_id is not None:
                response = {**response, "REQUESTID": request_id}
            try:
                await ws.send(json.dumps(response, default=str))
            except ConnectionClosed:
                pass

        try:
            await ws.send(json.dumps(self.server.handshakeMsg))
            async for raw in ws:
                try:
                    data = json.loads(raw)
                except (json.JSONDecodeError, TypeError) as e:
                    await ws.send(json.dumps(self.server.error("400", f"Invalid JSON:{e}")))
                    continue
                request_id = data.get("REQUESTID") if isinstance(data, dict) else None
                ## login must finish before the requests that depend on it
                if isinstance(data, dict) and (data.get("MESSAGE") or {}).get("INFO") == "login":
                    await answer(data, request_id)
                else:
                    task = asyncio.create_task(answer(data, request_id))
                    pending.add(task)  # keep a reference until it finishes
                    task.add_done_callback(pending.discard)
        except ConnectionClosed:
            pass
        print(f"[ws {addr}] closed")

    async def run(self):
        ## max_size leaves room for two 10 MB assignment files, base64 encoded
        async with serve(self.client, self.host, self.port, max_size=32 * 2 ** 20) as ws_server:
            print(f"WebSocket listening on ws://{self.host}:{self.port}")
            await ws_server.serve_forever()


def start_in_background(server, host=WS_HOST, port=WS_PORT):
    bridge = WebSocketBridge(server, host, port)

    def run():
        try:
            asyncio.run(bridge.run())
        except OSError as e:
            print(f"WebSocket binding failed: {e}")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return bridge


if __name__ == "__main__":
    from SocketServer import Server
    asyncio.run(WebSocketBridge(Server()).run())
