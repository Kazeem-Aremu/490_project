import socket
import json
import threading
import traceback
import os
import sys
import asyncio
from urllib.parse import urlparse

from DataBaseHandler import DataBaseHandler
from AIService import AIService, make_submission_fetcher
from AgentInterface import Teacher

# router.py / router_endpoint.py live in ../Router
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Router"))
from router_endpoint import handle_route_submission, to_record

try:  # the browser (student-portal) needs WebSockets; pip install websockets
    from websockets.asyncio.server import serve as ws_serve
    from websockets.exceptions import ConnectionClosed
except ImportError:
    ws_serve = None

#HOST = "127.0.0.1"
#PORT = 8342
hostname = socket.socket()
_decoder = json.JSONDecoder()


test_response = {"Response Code":"200", "MESSAGE":{"METHOD": "message sent"}}

# POST_ROUTES = {
#     "startAIConversation": "start_coversation",
#     "sendAIMessage":"send_message"
# }

# (INFO, BY) -> (DatabaseHandler method, key to read from MESSAGE["PARAMS"])
GET_ROUTES = {
    ("userInfo", None):                  ("getUser",               "USERID"),
    ("AssignmentInfo", "CourseID"):      ("getAssignmentByCourse", "COURSEID"),
    ("AssignmentInfo", "AssignmentId"):  ("getAssignment",         "ASSIGNMENTID"),
    ("getCourseInfo", "teacherID"):      ("getCourseByTeacher",    "teacherID"),
    ("getCourseInfo", "CourseID"):       ("getCoursebyId",         "CourseID"),
    ("Enrollement", "Course"):           ("getEnrollmentByCourse", "CourseID"),
    ("Enrollement", "UserID"):           ("getEnrollmentByUser",   "userID"),
}


SINGLE_ITEM = {"getUser", "getCoursebyId", "getAssignment"}

NOT_IMPLEMENTED_INFO = {"reportInfo"}

# ---------------------------------------------------------------- WS4 session state
# router decision -> (path, starting status)
SESSION_START = {"PASS": ("A", "active"), "FAIL": ("B", "active"), "MANUAL_REVIEW": ("instructor", "escalated")}
SESSION_STATUSES = {"active", "retry", "escalated", "complete"}
MAX_SCORE = 5  # Team1Week7E5Docs: answers are scored 1-5


def _nonneg_int(v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise ValueError
    return v


def _status(v):
    if v not in SESSION_STATUSES:
        raise ValueError
    return v


def _list(v):
    if not isinstance(v, list):
        raise ValueError
    return v


# fields a client may change with updateSession, and how each is checked
SESSION_EDITABLE = {
    "current_question": _nonneg_int,
    "retry_number": _nonneg_int,
    "status": _status,
    "questions": _list,
}
class Server():
    def __init__(self):
        self.HOST = "127.0.0.1"
        self.PORT = 8342
        #self.hostname = socket.socket()
        self.server_socket = None
        self.WS_PORT = 8343  # student-portal connects to ws://127.0.0.1:8343
        self.handshakeMsg = {"Response Code":"200", "MESSAGE":{"HANDSHAKE": "True"}}
        self._session_locks = {}
        self._session_locks_guard = threading.Lock()
        self.database = DataBaseHandler()

        supabase_host = urlparse(os.environ.get("SUPABASE_URL", "")).hostname
        self.ai = AIService(self.database, fetch_text=make_submission_fetcher(supabase_host))


    ##this function is called and starts up the server
    def start(self):
        self.start_websocket()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if os.name != "nt":
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print(f"Socket created on {self.HOST}:{self.PORT}")
        try:
            self.server_socket.bind((self.HOST, self.PORT))

        except socket.error as e:
            print(f"Binding failed: {e}")
            return

        ## allows 5 connections to be wait listed
        self.server_socket.listen(5)
        print(f"Listening on {self.HOST}:{self.PORT}")
        while True:
            client_socket, client_addr = self.server_socket.accept()
            print(f"Connected to {client_addr}, starting thread")
            client_thread = threading.Thread(
                target=self.handle_Client,
                args = (client_socket, client_addr))
            client_thread.daemon = True
            client_thread.start()

    ## this function will emit the messages between client and server
    def emit(self, content, socket, addr):
        print(f"[{addr}] Emitting message {content}")
        formatContent = json.dumps(content, default=str).encode("utf-8") + b"\n"
        socket.sendall(formatContent)

    def read_message(self, sock, buf):
        while True:
            stripped = buf.lstrip()
            if stripped:
                try:
                    text  =stripped.decode("utf-8")
                    obj, end = _decoder.raw_decode(text)
                    return "ok", obj, text[end:].encode("utf-8")
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    if b"\n" in stripped:
                        _, _, rest = stripped.partition(b"\n")
                        return "bad", str(e), rest

            chunk = sock.recv(4096)
            if not chunk: 
                return "closed", None, b""
            buf += chunk

    @staticmethod
    def error(code, text, original = None):
        body = {"ERROR": text}
        if original is not None:
            body["original Message"] = original
        return {"Response Code":code, "MESSAGE":body}

   ## Routing

    def handle_Requests(self, data):
        if not isinstance(data, dict):
            return self.error("400", "Request must be a JSON object", data)

        message = data.get("MESSAGE")
        if not isinstance(message, dict):
            return self.error("400", "Missing MESSAGE object", data)

        method = message.get("METHOD")
        if method == "GET":
            return self.handle_get(message, data)
        if method == "POST":
            return self.handle_post(message, data)
        return self.error("400", f"Uknown or missing METHOD: {method!r}", data)

    @staticmethod
    def int_params(params, *keys):
        try: 
            return tuple(int(params[k]) for k in keys)
        except (KeyError, ValueError, TypeError):
            return None
        
    def handle_post(self, message, original):
        info = message.get("INFO")
        params = message.get("PARAMS")

        if not isinstance(params, dict):
            return self.error("400", "Missing PARAMS", original)
        ##Server parses request AI is in AI service
        if info == "startAIConversation":
            ids = self.int_params(params, "USERID","SUBMISSIONID")
            #text = params.get("TEXT")
            if ids is None:
                return self.error("400", "PARAS needs integer USER and SUBMISSIONID", original)
            return self.ai.start_conversation(ids[0], ids[1])

        if info == "sendAIMessage":
            ids = self.int_params(params, "USERID", "CONVOID")
            if ids is None:
                return self.error("400", "PARAMS needs integer USERID and CONVOID", original)
            return self.ai.send_message(ids[0], ids[1], params.get('TEXT'))
        if info == "routeSubmission":
            return self.route_submission(original)

        if info == "updateSession":
            ids = self.int_params(params, "USERID", "SUBMISSIONID")
            if ids is None:
                return self.error("400", "PARAMS needs integer USERID and SUBMISSIONID", original)
            return self.update_session(ids[0], ids[1], params, original)

        if info == "recordAnswer":
            ids = self.int_params(params, "USERID", "SUBMISSIONID")
            if ids is None:
                return self.error("400", "PARAMS needs integer USERID and SUBMISSIONID", original)
            return self.record_answer(ids[0], ids[1], params, original)

        return self.error("400", f"Unknown POST request:{info!r}", original)

    # ------------------------------------------------------------ session state (WS4)
    def _session_lock(self, submission_id):
        with self._session_locks_guard:
            return self._session_locks.setdefault(submission_id, threading.Lock())

    def _owned_session(self, user_id, submission_id, original):
        """Return (session, None) or (None, error reply)."""
        session = self.database.one(self.database.getSession(submission_id))
        if session is None:
            return None, self.error("404", f"No session for submission {submission_id}", original)
        if int(session["user_id"]) != user_id:
            return None, self.error("403", "This session belongs to a different student", original)
        return session, None

    def route_submission(self, original):
        """Run the WS2 router, then create or update the student's session."""
        reply = handle_route_submission(original)
        if reply.get("Response Code") != "200":
            return reply
        m = reply["MESSAGE"]
        if m["route"] == "REJECTED":
            return reply  # rejected uploads don't count as an attempt, so no session

        try:
            submission_id = int(m["submissionID"])
        except ValueError:
            return self.error("400", "submissionID must be an integer", original)
        submission = self.database.one(self.database.getSubmission(submission_id))
        if submission is None:
            return self.error("404", f"Submission {submission_id} not found", original)

        path, status = SESSION_START[m["route"]]
        row = to_record(reply)
        row.update({"submission_id": submission_id, "path": path, "status": status,
                    "user_id": submission["Student_id"], "assignment_id": submission["Assign_id"]})
        with self._session_lock(submission_id):
            if self.database.one(self.database.getSession(submission_id)) is None:
                row["attempt_number"] = self.database.countAttempts(row["user_id"], row["assignment_id"]) + 1
            saved = self.database.saveSession(row)
        m["session"] = self.database.one(saved)
        return reply

    def update_session(self, user_id, submission_id, params, original):
        changes = {}
        for field, check in SESSION_EDITABLE.items():
            if field in params:
                try:
                    changes[field] = check(params[field])
                except ValueError:
                    return self.error("400", f"Invalid value for {field}", original)
        if not changes:
            return self.error("400", "Nothing to update. Editable: " + ", ".join(SESSION_EDITABLE), original)
        with self._session_lock(submission_id):
            _, problem = self._owned_session(user_id, submission_id, original)
            if problem:
                return problem
            saved = self.database.updateSession(submission_id, changes)
        return {"Response Code": "200", "MESSAGE": {"session": self.database.one(saved)}}

    def record_answer(self, user_id, submission_id, params, original):
        """Append one scored answer, so clients never overwrite each other's scores."""
        question, answer, score = params.get("QUESTION"), params.get("ANSWER"), params.get("SCORE")
        if not isinstance(question, str) or not isinstance(answer, str):
            return self.error("400", "QUESTION and ANSWER must be strings", original)
        if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= MAX_SCORE:
            return self.error("400", f"SCORE must be an integer from 1 to {MAX_SCORE}", original)
        with self._session_lock(submission_id):
            session, problem = self._owned_session(user_id, submission_id, original)
            if problem:
                return problem
            scores = list(session.get("scores") or [])
            scores.append({"question": question, "answer": answer, "score": score,
                           "retry": session.get("retry_number", 0)})
            saved = self.database.updateSession(submission_id, {"scores": scores})
        return {"Response Code": "200", "MESSAGE": {"session": self.database.one(saved)}}


    def handle_get(self, message, original):
        info = message.get("INFO")
        by = message.get("BY")

        if info in NOT_IMPLEMENTED_INFO:
            return self.error("501", f"{info} not implemented yet", original)

        # Sessions hold a student's answers, so only that student may read them
        if info == "sessionInfo":
            params = message.get("PARAMS")
            ids = self.int_params(params, "USERID", "SUBMISSIONID") if isinstance(params, dict) else None
            if ids is None:
                return self.error("400", "PARAMS needs integer USERID and SUBMISSIONID", original)
            session, problem = self._owned_session(ids[0], ids[1], original)
            if problem:
                return problem
            return {"Response Code": "200", "MESSAGE": [session]}

        route = GET_ROUTES.get((info, by)) or GET_ROUTES.get((info, None))

        if route is None:
            return self.error("400", f"Invalid GET request (INFO = {info!r}, BY = {by!r})",original)
        db_method, param_key = route

        params = message.get("PARAMS")
        if not isinstance(params, dict) or param_key not in params:
            return self.error("400", f"Missing PARAMS.{param_key}", original)

        try:
            the_id = int(params[param_key])
        except (ValueError, TypeError):
            return self.error("400", f"PARAMS.{param_key} must be an integer", original)

        print(F"GET {info} BY {by} -> {db_method}({the_id})")

        try:
            result = getattr(self.database,db_method)(the_id)
        except Exception as e:
            traceback.print_exc()
            return self.error("500", f"Database error in {db_method}: {e}", original)

        if result is None or (db_method in SINGLE_ITEM and result == []) :
            return self.error("404", "Not found", original)

        if isinstance(result,dict) and "Response Code" in result:
            return result

        return {"Response Code": "200", "MESSAGE": result}

    def handle_Client(self, client_socket, client_addr ):
        print(f"Connected to {client_addr}")
        with client_socket:
            try:
                self.emit(self.handshakeMsg, client_socket, client_addr)
                # handshake = json.dumps(self.handshakeMsg).encode("utf-8")
                # client_socket.sendall(handshake)
                # handshake_reply_raw = client_socket.recv(1024)
                
                status , _, buf = self.read_message(client_socket, b"")
                if status == "closed":
                    return
                
                while True:
                    status, data, buf = self.read_message(client_socket, buf)
                    if status == "closed":
                        break
                    if status == "bad":
                        self.emit(self.error("400", f"Invalid JSON:{data}"), client_socket, client_addr)
                        continue

                    try:
                        response = self.handle_Requests(data)
                    except Exception as e:
                        traceback.print_exc()
                        response = self.error("500", f"Internal Server error: {e}")

                    self.emit(response, client_socket, client_addr)

            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                print(f"{client_addr} disconnected abruptly")

        print(f"Closed {client_addr}")

        
    # ------------------------------------------------------------ WebSocket door (browsers)
    def start_websocket(self):
        """Serve the same requests over WebSocket so the React portal can connect.
        Runs in a background thread next to the TCP server."""
        if ws_serve is None:
            print("websockets is not installed, so browsers can't connect. Run: pip install websockets")
            return

        async def run():
            async with ws_serve(self.handle_ws_client, self.HOST, self.WS_PORT, max_size=1_000_000):
                print(f"WebSocket listening on ws://{self.HOST}:{self.WS_PORT}")
                await asyncio.Future()  # run forever

        threading.Thread(target=lambda: asyncio.run(run()), daemon=True).start()

    async def handle_ws_client(self, ws):
        addr = ws.remote_address
        print(f"WebSocket connected: {addr}")
        try:
            await ws.send(json.dumps(self.handshakeMsg))
            async for raw in ws:  # each WebSocket frame is one whole message, no "\n" needed
                try:
                    data = json.loads(raw)
                except (json.JSONDecodeError, TypeError) as e:
                    await ws.send(json.dumps(self.error("400", f"Invalid JSON:{e}")))
                    continue
                message = data.get("MESSAGE") if isinstance(data, dict) else None
                if isinstance(message, dict) and "HANDSHAKE" in message and "METHOD" not in message:
                    continue  # handshake ack is optional over WebSocket
                try:
                    # AI calls take seconds; run in a thread so other browsers aren't blocked
                    response = await asyncio.to_thread(self.handle_Requests, data)
                except Exception as e:
                    traceback.print_exc()
                    response = self.error("500", f"Internal Server error: {e}")
                await ws.send(json.dumps(response, default=str))
        except ConnectionClosed:
            pass
        print(f"WebSocket closed: {addr}")


def main():
    server = Server()
    server.start()

if __name__ == "__main__":
    main()