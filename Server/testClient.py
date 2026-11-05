"""
Test driver for the TCP/JSON server.

1. Start your server:   python server.py   (whatever your file is called)
2. In another terminal: python test_server.py
   Optional:           python test_server.py --only Enrollment
                       python test_server.py --host 127.0.0.1 --port 8342

Each test opens a NEW connection, completes the handshake, sends one message,
and waits for a reply. Expectations:
    ok     -> got a reply whose "Response Code" is not 400/500
    400    -> got a reply with "Response Code" == "400"
    NOIMPL -> endpoint is a stub (pass); just reports what the server did

Request format used (INFO is the endpoint name, PARAMS holds the arguments):
    {"Response Code": "200",
     "MESSAGE": {"METHOD": "GET", "INFO": "userInfo", "BY": "...", "PARAMS": {...}}}
"""
import argparse
import json
import socket
import sys
import threading

HOST = "127.0.0.1"
PORT = 8342
TIMEOUT = 10.0     # seconds to wait for a reply before calling it "NO REPLY"

# Test Info
VALID_USER_ID = 1      
BAD_USER_ID = "abc"     # something int() will reject

VALID_SUBMISSION_ID = 2
BAD_SUBMISSION_ID = "ID"
MISSING_SUBMISSION_ID = 5

VALID_ENROLLMENT_COURSE_ID = 3
BAD_ENROLLMENT_COURSE_ID = 5
VALID_ENROLLMENT_STUD_ID = 8
BAD_ENROLLMENT_STU_ID = 10

VALID_COURSE_ID = 2
BAD_COURSE_ID = "ID"
MISSING_COURSE_ID = 5
VALID_COURSE_TEACHER_ID = 4
BAD_COURSE_TEACHER_ID = "ID"
MISSING_COURSE_TEACHER_ID =  15

VALID_ASSIGNMENT_ID = 2
BAD_ASSIGNMENT_ID = "ID"
VALID_ASSIGNMENT_COURSE_ID = 4
BAD_ASSIGNMENT_COURSE_ID = "ID"

VALID_ASSIGNMENT_COURSE_ID = 2
BAD_ASSIGNENT_COURSE_ID = "ID"
MISSING_ASSIGNMENT_COURSE_ID = "5"

VALID_AI_CONVERSATION_ID = 1
BAD_AI_CONVERSATION_ID = "ID"
MISSING_AI_CONVERSATION_ID = 2

_decoder = json.JSONDecoder()


# ---------------------------------------------------------------- helpers
def recv_json(sock):
    """Return first JSON object received, None on timeout, 'CLOSED' if peer closed."""
    buf = b""
    while True:
        try:
            chunk = sock.recv(4096)
        except socket.timeout:
            return None
        except OSError:
            return "CLOSED"
        if not chunk:
            return "CLOSED"
        buf += chunk
        try:
            obj, _ = _decoder.raw_decode(buf.decode("utf-8").lstrip())
            return obj
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue  # partial message, keep reading


def send(sock, raw):
    """Send one message, newline-terminated so the server can find message boundaries."""
    sock.sendall(raw + b"\n")


def connect():
    """Open a connection and complete the handshake. Returns (socket, handshake_msg)."""
    s = socket.create_connection((HOST, PORT), timeout=TIMEOUT)
    handshake = recv_json(s)
    send(s, json.dumps({"Response Code": "200",
                          "MESSAGE": {"HANDSHAKE": "True"}}).encode("utf-8"))
    return s, handshake


def msg(method, info=None, by=None, params=None):
    m = {"METHOD": method}
    if info is not None:
        m["INFO"] = info
    if by is not None:
        m["BY"] = by
    if params is not None:
        m["PARAMS"] = params
    return {"Response Code": "200", "MESSAGE": m}


def get(info, by=None, params=None):
    return msg("GET", info, by, params)


def judge(expect, reply):
    """Return (status, detail)."""
    shown = json.dumps(reply)[:110] if isinstance(reply, (dict, list)) else str(reply)
    if expect == "NOIMPL":
        return "INFO", f"stub endpoint -> {shown if reply is not None else 'no reply'}"
    if reply is None:
        return "FAIL", "NO REPLY (timeout) - client would hang"
    if reply == "CLOSED":
        return "FAIL", "CONNECTION CLOSED by server (handler thread probably crashed)"
    code = reply.get("Response Code") if isinstance(reply, dict) else None
    if expect == "400":
        return ("PASS", shown) if code == "400" else ("FAIL", f"expected 400, got: {shown}")
    if expect == "ok":
        return (("FAIL", f"got error: {shown}") if code in ("400", "500")
                else ("PASS", shown))
    return "FAIL", f"unknown expectation {expect}"


# ------------------------------------------------------------- test cases
# (name, payload (dict or raw bytes), expectation)
CASES = [
    # ---- userInfo
    ("userInfo: valid id",            get("userInfo", params={"USERID": VALID_USER_ID}), "ok"),
    ("userInfo: non-numeric id",      get("userInfo", params={"USERID": BAD_USER_ID}), "400"),
    ("userInfo: missing PARAMS",      get("userInfo"), "400"),

    # ---- AssignmentInfo
    ("Assignment BY CourseID: valid", get("AssignmentInfo", "CourseID", {"COURSEID": VALID_COURSE_ID}), "ok"),
    ("Assignment BY CourseID: bad",   get("AssignmentInfo", "CourseID", {"COURSEID": BAD_COURSE_ID}), "400"),
    ("Assignment BY AssignmentId: valid", get("AssignmentInfo", "AssignmentId", {"ASSIGNMENTID": VALID_ASSIGNMENT_ID}), "ok"),
    ("Assignment BY AssignmentId: bad",   get("AssignmentInfo", "AssignmentId", {"ASSIGNMENTID": BAD_ASSIGNMENT_ID}), "400"),
    ("Assignment BY unknown",         get("AssignmentInfo", "Nonsense", {}), "400"),
    ("Assignment: missing BY",        get("AssignmentInfo", None, {"COURSEID": VALID_ASSIGNMENT_ID}), "400"),

    # ---- getCourseInfo
    ("Course BY teacherID: valid",    get("getCourseInfo", "teacherID", {"teacherID": VALID_COURSE_TEACHER_ID}), "ok"),
    ("Course BY teacherID: bad",      get("getCourseInfo", "teacherID", {"teacherID": BAD_COURSE_TEACHER_ID}), "400"),
    ("Course BY CourseID: valid",     get("getCourseInfo", "CourseID", {"CourseID": VALID_COURSE_TEACHER_ID}), "ok"),
    ("Course BY CourseID: bad",       get("getCourseInfo", "CourseID", {"CourseID": BAD_COURSE_TEACHER_ID}), "400"),
    ("Course BY unknown",             get("getCourseInfo", "Nonsense", {}), "400"),

    # ---- Enrollement (spelled the way the server spells it)
    ("Enrollement BY Course: valid",  get("Enrollement", "Course", {"CourseID": VALID_ENROLLMENT_COURSE_ID}), "ok"),
    ("Enrollement BY Course: bad",    get("Enrollement", "Course", {"CourseID": BAD_ENROLLMENT_COURSE_ID}), "400"),
    ("Enrollement BY Student UserID: valid",  get("Enrollement", "UserID", {"userID": VALID_ENROLLMENT_STUD_ID}), "ok"),
    ("Enrollement BY Student UserID: bad",    get("Enrollement", "UserID", {"userID": BAD_ENROLLMENT_STU_ID}), "400"),
    ("Enrollement BY unknown",        get("Enrollement", "Nonsense", {}), "400"),

    # ---- stubbed endpoints (server currently does `pass`)
    ("reportInfo (stub)",             get("reportInfo"), "NOIMPL"),
    ("getAiConversation (stub)",      get("getAiConversation"), "NOIMPL"),
    ("POST (stub)",                   msg("POST", "anything", params={}), "NOIMPL"),

    # ---- malformed / unknown input
    ("unknown INFO",                  get("doesNotExist"), "400"),
    ("unknown METHOD",                msg("DELETE", "userInfo", params={"USERID": VALID_ID}), "400"),
    ("missing METHOD",                {"Response Code": "200", "MESSAGE": {"INFO": "userInfo"}}, "400"),
    ("missing MESSAGE key",           {"Response Code": "200"}, "400"),
    ("JSON but not an object ([])",   b"[]", "400"),
    ("invalid JSON",                  b"{this is not json", "400"),
]


def run_case(name, payload, expect):
    try:
        s, hs = connect()
    except OSError as e:
        return "ERROR", f"cannot connect to {HOST}:{PORT} ({e})"
    with s:
        raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        send(s, raw)
        reply = recv_json(s)
    return judge(expect, reply)


# ------------------------------------------------------ special scenarios
def test_handshake():
    try:
        s, hs = connect()
    except OSError as e:
        return "ERROR", f"cannot connect ({e})"
    s.close()
    ok = isinstance(hs, dict) and hs.get("MESSAGE", {}).get("HANDSHAKE") == "True"
    return ("PASS", json.dumps(hs)) if ok else ("FAIL", f"unexpected handshake: {hs}")


def test_persistent_connection():
    """Several requests on ONE connection - the while loop should keep serving."""
    try:
        s, _ = connect()
    except OSError as e:
        return "ERROR", f"cannot connect ({e})"
    with s:
        for i in range(3):
            send(s, json.dumps(get("userInfo", params={"USERID": VALID_ID})).encode())
            reply = recv_json(s)
            if reply is None or reply == "CLOSED":
                return "FAIL", f"request {i + 1}/3 got {'no reply' if reply is None else 'closed'}"
    return "PASS", "3/3 requests answered on one connection"


def test_error_then_recover():
    """After a bad request the same connection should still work."""
    try:
        s, _ = connect()
    except OSError as e:
        return "ERROR", f"cannot connect ({e})"
    with s:
        send(s, b"{bad json")
        recv_json(s)
        send(s, json.dumps(get("userInfo", params={"USERID": VALID_ID})).encode())
        reply = recv_json(s)
    if reply is None or reply == "CLOSED":
        return "FAIL", "connection unusable after a bad request"
    return "PASS", "connection still works after a bad request"


def test_concurrent_clients(n=10):
    results = []
    lock = threading.Lock()

    def worker():
        try:
            s, _ = connect()
            with s:
                send(s, json.dumps(get("userInfo", params={"USERID": VALID_ID})).encode())
                r = recv_json(s)
            good = isinstance(r, dict)
        except OSError:
            good = False
        with lock:
            results.append(good)

    threads = [threading.Thread(target=worker) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    ok = sum(results)
    return ("PASS" if ok == n else "FAIL"), f"{ok}/{n} concurrent clients got a reply"


def test_client_disconnect():
    """Abrupt disconnect shouldn't take the server down."""
    try:
        s, _ = connect()
        s.close()
        s2, hs = connect()
        s2.close()
    except OSError as e:
        return "FAIL", f"server unreachable after a client disconnected ({e})"
    return "PASS", "server accepted a new client after an abrupt disconnect"


SPECIAL = [
    ("handshake", test_handshake),
    ("persistent connection", test_persistent_connection),
    ("recover after bad request", test_error_then_recover),
    ("concurrent clients", test_concurrent_clients),
    ("client disconnect", test_client_disconnect),
]


# ------------------------------------------------------------------- main
def safe(fn, *args):
    """Run a test; a dropped/reset connection becomes a FAIL instead of a crash."""
    try:
        return fn(*args)
    except OSError as e:
        return "FAIL", f"connection error mid-test: {e} (check the server window for a traceback)"


def main():
    global HOST, PORT
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=HOST)
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--only", default="", help="run only tests whose name contains this text")
    args = ap.parse_args()
    HOST, PORT = args.host, args.port
    flt = args.only.lower()

    counts = {"PASS": 0, "FAIL": 0, "INFO": 0, "ERROR": 0}

    def report(name, status, detail):
        counts[status] += 1
        print(f"[{status:5}] {name:36} {detail}")

    print(f"Testing server at {HOST}:{PORT}\n")
    for name, fn in SPECIAL:
        if flt in name.lower():
            report(name, *safe(fn))
    for name, payload, expect in CASES:
        if flt in name.lower():
            report(name, *safe(run_case, name, payload, expect))

    print(f"\n{counts['PASS']} passed, {counts['FAIL']} failed, "
          f"{counts['INFO']} stub/info, {counts['ERROR']} errors")
    sys.exit(1 if counts["FAIL"] or counts["ERROR"] else 0)


if __name__ == "__main__":
    main()