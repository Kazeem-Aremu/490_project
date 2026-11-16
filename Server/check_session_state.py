"""
Checks the new server features against the real database.

1. Start the server in one terminal:   python Server/SocketServer.py
2. Run this in a second terminal:      python Server/check_session_state.py

Uses the test rows listed in seed_ids.json (made by databbaseSeeder.py).
Add --ai to also send one real message to the AI (uses a few tokens).
"""
import asyncio
import json
import os
import socket
import sys

HOST = "127.0.0.1"
TCP_PORT = 8342
WS_PORT = 8343
IDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_ids.json")

results = []


def report(name, passed, reply=None):
    results.append(passed)
    print(("PASS  " if passed else "FAIL  ") + name)
    if not passed and reply is not None:
        print("      server said:", json.dumps(reply, default=str)[:400])


def request(method, info, params):
    return {"Response Code": "200", "MESSAGE": {"METHOD": method, "INFO": info, "PARAMS": params}}


def ok(reply):
    return isinstance(reply, dict) and reply.get("Response Code") == "200"


async def check_websocket(ids, use_ai):
    try:
        from websockets.asyncio.client import connect
    except ImportError:
        report("websockets library installed (pip install -r Server/requirements.txt)", False)
        return

    try:
        ws_cm = connect(f"ws://{HOST}:{WS_PORT}", open_timeout=5)
        ws = await ws_cm.__aenter__()
    except OSError as e:
        report(f"WebSocket connects on port {WS_PORT} (is the server running?)", False, str(e))
        return

    async def call(method, info, params):
        await ws.send(json.dumps(request(method, info, params)))
        return json.loads(await asyncio.wait_for(ws.recv(), timeout=90))

    try:
        hello = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
        report("WebSocket connects and gets the handshake", hello.get("MESSAGE", {}).get("HANDSHAKE") == "True", hello)

        user, sub = ids["student_a"], ids["submission"]
        r = await call("POST", "routeSubmission", {
            "submissionID": str(sub), "uploadValid": "true", "compileStatus": "SUCCESS",
            "errorStatus": "", "testsPassed": "5", "testsTotal": "5", "threshold": "5"})
        session = r.get("MESSAGE", {}).get("session") if ok(r) else None
        report("routeSubmission creates a session (path A)",
               bool(session) and session.get("path") == "A", r)
        if not session:
            print("      If the error mentions Review_Sessions, run setup_review_sessions.sql in Supabase first.")
            return

        r = await call("GET", "sessionInfo", {"USERID": user, "SUBMISSIONID": sub})
        report("sessionInfo reads it back", ok(r) and r["MESSAGE"][0]["submission_id"] == sub, r)

        r = await call("GET", "sessionInfo", {"USERID": ids["student_b"], "SUBMISSIONID": sub})
        report("another student can't read it (403)", r.get("Response Code") == "403", r)

        r = await call("POST", "updateSession", {"USERID": user, "SUBMISSIONID": sub,
                                                 "current_question": 1, "questions": ["Test question 1"]})
        report("updateSession saves progress", ok(r) and r["MESSAGE"]["session"]["current_question"] == 1, r)

        r = await call("POST", "recordAnswer", {"USERID": user, "SUBMISSIONID": sub,
                                                "QUESTION": "Test question 1", "ANSWER": "test answer", "SCORE": 4})
        report("recordAnswer adds a score", ok(r) and r["MESSAGE"]["session"]["scores"][-1]["score"] == 4, r)

        r = await call("POST", "updateSession", {"USERID": ids["student_b"], "SUBMISSIONID": sub, "retry_number": 0})
        report("another student is blocked (403)", r.get("Response Code") == "403", r)

        # put the progress back so the test can be run again
        await call("POST", "updateSession", {"USERID": user, "SUBMISSIONID": sub,
                                             "current_question": 0, "questions": [], "status": "active"})

        r = await call("POST", "startAIConversation", {"USERID": user, "SUBMISSIONID": sub})
        report("startAIConversation loads the saved conversation", ok(r) and "MESSAGES" in r["MESSAGE"], r)

        if use_ai:
            print("      (asking the AI, this can take a few seconds...)")
            r = await call("POST", "sendAIMessage", {"USERID": user, "CONVOID": sub, "TEXT": "Can you give me a hint?"})
            report("sendAIMessage gets a real AI reply", ok(r) and bool(r["MESSAGE"].get("REPLY")), r)
            if ok(r):
                print("      AI said:", r["MESSAGE"]["REPLY"][:200])
    finally:
        await ws_cm.__aexit__(None, None, None)


def check_tcp(ids):
    try:
        s = socket.create_connection((HOST, TCP_PORT), timeout=10)
    except OSError as e:
        report(f"TCP connects on port {TCP_PORT} (is the server running?)", False, str(e))
        return
    with s:
        f = s.makefile("rb")
        json.loads(f.readline())  # handshake
        s.sendall(json.dumps({"MESSAGE": {"HANDSHAKE": "ACK"}}).encode() + b"\n")
        s.sendall(json.dumps(request("GET", "sessionInfo", {"USERID": ids["student_a"], "SUBMISSIONID": ids["submission"]})).encode() + b"\n")
        r = json.loads(f.readline())
        report("TCP clients still work (sessionInfo over port 8342)", ok(r), r)


def main():
    if not os.path.exists(IDS_FILE):
        print("No seed_ids.json found. Run: python Server/databbaseSeeder.py")
        sys.exit(1)
    with open(IDS_FILE) as f:
        ids = json.load(f)
    print(f"Testing with student {ids['student_a']}, submission {ids['submission']}\n")

    asyncio.run(check_websocket(ids, use_ai="--ai" in sys.argv))
    check_tcp(ids)

    print(f"\n{sum(results)}/{len(results)} checks passed")
    sys.exit(0 if results and all(results) else 1)


if __name__ == "__main__":
    main()
