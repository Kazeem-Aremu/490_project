# Server Documentation — CSDP 490 Team 2

| | |
|---|---|
| **Server file** | `Server/SocketServer.py` |
| **Database layer** | `Server/DataBaseHandler.py` (Supabase / PostgreSQL) |
| **Transport** | TCP socket, JSON encoded as UTF-8 |
| **Default address** | `127.0.0.1:8342` |
| **Doc status** | Draft v0.1 |

> **Read [Section 8](#8-known-issues-fix-these-before-clients-integrate) first.** As currently written, `SocketServer.py` will not start (an empty `elif` body is a syntax error), and none of the GET endpoints can return data yet. This document describes the **contract the server is meant to follow**, using the same names the code uses today, plus the minimum fixes needed to make the code match it.

---

## 1. Overview

The server accepts client connections, reads one JSON request at a time, calls the matching `DataBaseHandler` method, and sends the result back as JSON. Each connected client gets its own thread.

```
Client pages (Login, Dashboard, Report, Path A / Path B)
        │   TCP + JSON
        ▼
SocketServer.py   Server.start() accepts connections
                  Server.handle_Client() one thread per client
        │   Python method calls
        ▼
DataBaseHandler.py   ──►   Supabase (Postgres tables + Storage)
```

**Security note:** the database handler uses the Supabase **service role key** (`SUPABASE_SECRET_KEY`), which bypasses Row Level Security. That means the *server* is responsible for deciding who may see what. Right now there is no authentication check, so any client that can connect can request any user's records. This needs to be addressed before real data is stored (see Section 8).

---

## 2. Setup and running

1. Create a `.env` file next to the server code (never commit it; confirm `.env` is in `.gitignore`):
   ```
   SUPABASE_URL=https://<your-project>.supabase.co
   SUPABASE_SECRET_KEY=<service role key>
   ```
2. Install dependencies: `pip install supabase python-dotenv flask`
3. Start the server: `py Server/SocketServer.py`
4. Run clients from a **second terminal**. The server must stay running.

`HOST` is `127.0.0.1`, so only programs on the same machine can connect. To accept other machines, bind to `0.0.0.0` (and open the port in the firewall).

---

## 3. Connection lifecycle

1. **Client connects.**
2. **Server speaks first.** It immediately sends the handshake:
   ```json
   {"Response Code": "200", "MESSAGE": {"HANDSHAKE": "True"}}
   ```
3. **Client must acknowledge.** The server then calls `recv()` once and **throws away whatever it receives**. The client should send an acknowledgement. Recommended:
   ```json
   {"MESSAGE": {"METHOD": "HANDSHAKE", "INFO": "ACK"}}
   ```
   The server does not reply to the acknowledgement.

   > **Gotcha:** if a client skips the ack and sends a real request straight away, the server consumes that request as the "handshake reply" and never answers it. The client then waits forever.
4. **Request / response loop.** The client sends one JSON request and waits for one JSON response.
5. **Disconnect.** When the client closes its socket, the server's `recv()` returns empty bytes and the thread ends.

---

## 4. Message format

### 4.1 Request

```json
{
  "MESSAGE": {
    "METHOD": "GET",
    "INFO":   "userInfo",
    "BY":     "UserID",
    "PARAMS": { "USERID": 1234 }
  }
}
```

| Field | Required | Meaning |
|---|---|---|
| `MESSAGE` | yes | Wrapper object for the whole request. |
| `METHOD` | yes | `"GET"` (read) or `"POST"` (write). **POST is not implemented yet.** |
| `INFO` | yes | Name of the resource being requested, e.g. `"userInfo"`. |
| `BY` | some endpoints | Which field to look up by, e.g. `"CourseID"`. Omit when an endpoint has only one lookup. |
| `PARAMS` | yes | Object holding the input values. **Key names are case-sensitive** and differ per endpoint (see Section 5). |

IDs may be sent as numbers or numeric strings. The server converts them with `int()`, so anything that is not a whole number is rejected with a 400 response.

> **Code change required:** the current code reads parameters from `data["MESSAGE"]["INFO"][...]`, but `INFO` is a string, so that lookup crashes. Parameters must be read from `data["MESSAGE"]["PARAMS"][...]` instead (Section 8, issue 2).

### 4.2 Responses

The server currently sends whatever the database handler returns, with no standard wrapper. After the fixes in Section 8, a client can receive three shapes:

| Situation | What the client receives |
|---|---|
| Success | A JSON **array of rows** (may be empty `[]` if nothing matched) |
| Database error | `{"error": "<description>"}` (a few handler functions use `"Error"` with a capital E) |
| Bad request | `{"Response Code": "400", "MESSAGE": {"ERROR": "...", "original Message": {...}}}` |

Clients should check `isinstance(response, list)` for success and treat any dict as an error for now. A standard response envelope is proposed in Section 8.3 so clients only have to handle one shape.

---

## 5. Endpoint reference (GET)

### 5.1 Summary

| # | `INFO` | `BY` | `PARAMS` key | DB handler function | Status |
|---|---|---|---|---|---|
| 1 | `userInfo` | *(none)* | `USERID` | `getUser` | Works after fix 2 |
| 2 | `AssignmentInfo` | `CourseID` | `COURSEID` | `getAssignmentByCourse` | Needs fixes 2, 3 |
| 3 | `AssignmentInfo` | `AssignmentId` | `ASSIGNMENTID` | `getAssignment` | Needs fixes 2, 3 |
| 4 | `getCourseInfo` | `teacherID` | `teacherID` | `getCourseByTeacher` | Needs fixes 2, 3 |
| 5 | `getCourseInfo` | `CourseID` | `CourseID` | `getCoursebyId` | Branch is broken; needs fixes 2, 3, 4 |
| 6 | `Enrollement` *(sic)* | `Course` | `CourseID` | `getEnrollmentByCourse` | Works after fix 2 |
| 7 | `Enrollement` *(sic)* | `UserID` | `userID` | `getEnrollmentByUser` | Works after fix 2 |
| 8 | `reportInfo` | — | — | none | **Stub** (does nothing, no reply) |
| 9 | `getAiConversation` | — | — | `getAiConversation` | **Not implemented**; handler function is also broken |

The spellings and capitalization above are exactly what the code compares against today. They are inconsistent (`Enrollement`, `teacherID` vs `COURSEID`, `AssignmentId`), so if the team normalizes them, update this table and every client at the same time.

### 5.2 Endpoint details

**1. Get a user**
```json
{"MESSAGE": {"METHOD": "GET", "INFO": "userInfo", "PARAMS": {"USERID": 1234}}}
```
Returns: `[{"id": 1234, "CREATED_AT": "2026-10-16T04:18:28+00:00", "NAME": "John Doe", "ROLE": "ADMIN"}]`

**2. Get all assignments in a course**
```json
{"MESSAGE": {"METHOD": "GET", "INFO": "AssignmentInfo", "BY": "CourseID", "PARAMS": {"COURSEID": 9876}}}
```
Returns: array of assignment rows for that course.

**3. Get one assignment**
```json
{"MESSAGE": {"METHOD": "GET", "INFO": "AssignmentInfo", "BY": "AssignmentId", "PARAMS": {"ASSIGNMENTID": 55}}}
```
Returns: array containing the assignment row (empty if not found).

**4. Get courses taught by a teacher**
```json
{"MESSAGE": {"METHOD": "GET", "INFO": "getCourseInfo", "BY": "teacherID", "PARAMS": {"teacherID": 2341}}}
```
Returns: array of course rows.

**5. Get one course by ID**
```json
{"MESSAGE": {"METHOD": "GET", "INFO": "getCourseInfo", "BY": "CourseID", "PARAMS": {"CourseID": 9876}}}
```

**6. Get enrollments for a course** (who is in it)
```json
{"MESSAGE": {"METHOD": "GET", "INFO": "Enrollement", "BY": "Course", "PARAMS": {"CourseID": 9876}}}
```
Returns: array of `{"Course_id": ..., "Student_id": ...}` rows.

**7. Get enrollments for a user** (which courses a student is in)
```json
{"MESSAGE": {"METHOD": "GET", "INFO": "Enrollement", "BY": "UserID", "PARAMS": {"userID": 4321}}}
```

**8. Report info** — placeholder. The branch contains only `pass`, so the server sends **no response** and the client will hang. Implement it or return a 501 (Section 7).

**9. AI conversation** — placeholder with no body (the syntax error). Needs a working handler first.

### 5.3 POST

`METHOD: "POST"` currently does nothing (`pass`) and sends no reply. See Section 7 for the endpoints to add.

---

## 6. Using the server from a client

Minimal Python client that handles the handshake correctly:

```python
import json
import socket

HOST, PORT = "127.0.0.1", 8342


class ServerClient:
    def __init__(self, host=HOST, port=PORT):
        self.sock = socket.create_connection((host, port), timeout=5)
        print("Handshake:", self._recv())               # server speaks first
        self._send({"MESSAGE": {"METHOD": "HANDSHAKE", "INFO": "ACK"}})

    def _send(self, obj):
        self.sock.sendall(json.dumps(obj).encode("utf-8"))

    def _recv(self):
        raw = self.sock.recv(4096)
        return json.loads(raw.decode("utf-8"))

    def get(self, info, by=None, **params):
        msg = {"METHOD": "GET", "INFO": info, "PARAMS": params}
        if by:
            msg["BY"] = by
        self._send({"MESSAGE": msg})
        return self._recv()

    def close(self):
        self.sock.close()


if __name__ == "__main__":
    c = ServerClient()
    print(c.get("userInfo", USERID=1234))
    print(c.get("AssignmentInfo", by="CourseID", COURSEID=9876))
    print(c.get("getCourseInfo", by="teacherID", teacherID=2341))
    print(c.get("Enrollement", by="UserID", userID=4321))
    c.close()
```

**Client rules of thumb**
- Wait for the handshake and send the ack before any real request.
- Always set a socket timeout (`timeout=5` above) so a missing reply raises an error instead of hanging silently.
- Send one request, then read one response, before sending the next.
- A list response is data; a dict response is an error.

**Limitations to plan around**
- `recv(1024)` (server) and `recv(4096)` (client) read a single chunk. Responses larger than the buffer, such as a long list of assignments, can arrive truncated or split. Before sending large payloads, agree on message framing (for example, a length prefix or a newline terminator).
- **Raw TCP sockets cannot be opened from a browser.** If the Login, Dashboard, and Report pages are web pages, they need a WebSocket or HTTP layer in front of this server. Python or desktop clients can use the socket directly.
- File uploads (assignments, submissions) should not travel through this JSON socket as-is. See the storage note in Section 7.

---

## 7. Endpoints to add

### 7.1 Database handler functions that already exist but have no endpoint

| Handler function | Proposed request | Notes |
|---|---|---|
| `createUser(userDataJson)` | `POST` / `INFO: "userInfo"` | Real signups should go through Supabase Auth; this is for seeding and admin use. |
| `createCourse(CourseDataJson)` | `POST` / `INFO: "getCourseInfo"` (or `"Course"`) | Teachers/admins only. |
| `setEnrollment(enrollmentData)` | `POST` / `INFO: "Enrollement"` | Adds a student to a course. |

Proposed POST shape (fields in `PARAMS` use the **database column names**, since the handler passes them straight to Supabase):
```json
{"MESSAGE": {"METHOD": "POST", "INFO": "Enrollement", "PARAMS": {"Course_id": 9876, "Student_id": 4321}}}
```
The server should **whitelist the allowed fields per endpoint** rather than forwarding any client-supplied keys to the database.

### 7.2 Endpoints required by the Interface Description that need new handler functions

| Interface Description function | New server endpoint | New handler function(s) needed |
|---|---|---|
| `OnLogin` (cookie/UID → basic account info) | Extend `GET userInfo`; add session/cookie check | Token verification via Supabase Auth |
| `getDashboard` (UID → course info + assignment list) | New composite `GET dashboard` | Combine `getEnrollmentByUser` → `getCoursebyId` → `getAssignmentByCourse` in one call |
| `uploadAssignment` | `POST AssignmentInfo` | `createAssignment`; file stored in Supabase Storage, link saved in `resource_link` |
| `UploadSubmission` | `POST Submission` | `createSubmission`; file stored in Supabase Storage, link saved in `Submission_link` |
| `getAssignment` (assignment + submissions) | Extend `GET AssignmentInfo` | `getSubmissionsByAssignment` |
| `GetReportInfo` | Finish the `reportInfo` stub | `getSubmission` (by student/assignment) plus `getAiConversation` |
| `SendMessage` / `getMessage` (AI API) | `POST AiMessage` | `createAiConversation` / `appendAiResponse`; server calls the AI API |
| `onPassPathA` / `onPassPathB` | `POST PassPath` | Update submission/conversation status; needs a pass-status column |

The handler file already has a `#Get Submission` placeholder with no functions under it. Suggested additions:
`getSubmission(submissionID)`, `getSubmissionsByAssignment(assignmentID)`, `getSubmissionsByStudent(studentID)`, `createSubmission(data)`, `createAssignment(data)`, `createAiConversation(data)`.

**About file uploads:** the Interface Description has files (DOCX, PDF, PY, TXT) going to Supabase Storage. The simplest design is for the server to hand the client a **signed upload URL** (or have the client upload directly with the Supabase client library), then send only the resulting file link through this socket. Pushing raw file bytes through a 1 KB JSON socket will not work.

### 7.3 Missing operations

No update or delete functions exist yet. Everything that writes uses `upsert`, so a "create" with an existing `id` silently **overwrites** that row. Consider switching creates to `insert` and adding explicit `update…` functions.

---

## 8. Known issues (fix these before clients integrate)

### 8.1 Blocking: the server cannot work until these are fixed

| # | Where | Problem | Fix |
|---|---|---|---|
| 1 | `SocketServer.py`, `elif … == "getAiConversation":` | The branch has no body, so Python raises an `IndentationError` and the file will not run. | Add a body or `pass` for now. |
| 2 | `SocketServer.py`, every GET branch | Parameters are read with `data["MESSAGE"]["INFO"]["USERID"]`, but `INFO` is a string, so this raises `TypeError`. The outer `except` prints it and **sends no reply**, so the client hangs. | Read from `data["MESSAGE"]["PARAMS"]["USERID"]` (and likewise for each key). |
| 3 | `DataBaseHandler.py`: `getCourseByTeacher`, `getCoursebyId`, `getAssignmentByCourse`, `getAssignment` | They compute `data` but never `return data`, so success returns `None` (JSON `null`). | Add `return data` after each `data = …` line. |
| 4 | `SocketServer.py`, `getCourseInfo` second branch | `elif ["MESSAGE"]["INFO"] == "CourseID":` indexes a list literal. | `elif data["MESSAGE"]["BY"] == "CourseID":` |
| 5 | `SocketServer.py`, final `else` | `self.emit(reply, client_socket, client_addr, client_addr)` passes 4 arguments; `emit` takes 3. | Remove the extra `client_addr`. |
| 6 | `SocketServer.py`, JSON error handler | `json.JSONDecodeErrorError` has an extra "Error". The first bad-JSON message kills the thread with `AttributeError`. | `json.JSONDecodeError` |
| 7 | `SocketServer.py`, `userInfo` branch | `except ValueError:` then `print(f"…{e}")` uses `e` but it was never defined (`as e` missing). | `except ValueError as e:` |
| 8 | `DataBaseHandler.py`, `getAiConversation` | It is a copy of `getAssignment`: queries `ASSIGNMENT`, uses undefined `AssignmentId`, and never returns. | Query `AI_CONVOS` with `AI_CONVO_ID` and `aiConvoID`, and `return data`. |

### 8.2 Non-blocking but worth fixing

- **Handshake ack is discarded** (Section 3). Either handle it explicitly or remove the extra `recv()` and let clients send requests right after the handshake.
- **Hanging clients:** the outer `except Exception` only prints. Send a `500` response there so a client never waits forever.
- **Unhandled `BY` values:** `AssignmentInfo`, `getCourseInfo`, and `Enrollement` have no `else`, so an unknown `BY` produces no reply.
- **`finally` + unbound `response`:** `finally: self.emit(response, …)` raises `UnboundLocalError` if the `try` failed before `response` was set. Build the response first, emit afterward.
- **Two Enrollment branches** call `self.emit(response, client_socket, client_socket)`; the third argument should be `client_addr`.
- **`if not data: break`** after parsing is pointless (it only triggers on `{}`); disconnects are already handled by `if not raw`.
- **`SUB_ID = "8904"`** looks like a column name that was overwritten with a value. It is probably meant to be `"id"`.
- **Case-sensitive column names:** `COURSE_TEACHER_ID = "Teacher_ID"` but `ASSIGNMENT_TEACHER_ID = "Teacher_id"`. Postgres column names are case-sensitive once quoted, so confirm each constant against the actual table.
- **Verify the spelling** of `AI_CONVO_RESPONSES = "Respnses"` against the real column.
- **Inconsistent error keys:** `"error"` vs `"Error"` in the handler. Pick one.
- **Copy-paste message:** `setEnrollment` reports "create Course DBH error".
- **Stray sockets:** the module-level `hostname = socket.socket()` and `self.hostname = socket.socket()` are never used. Delete both.
- **No authentication** (Section 1). At minimum, verify the caller's identity and role before returning user, enrollment, or report data.

### 8.3 Suggested cleanup: one dispatch table and a standard response

The repeated `try / except / finally` blocks can be replaced by one lookup table. This also guarantees every request gets exactly one reply.

```python
GET_ROUTES = {
    # (INFO, BY)                       : (PARAMS key,    DataBaseHandler method)
    ("userInfo", None):                 ("USERID",       "getUser"),
    ("AssignmentInfo", "CourseID"):     ("COURSEID",     "getAssignmentByCourse"),
    ("AssignmentInfo", "AssignmentId"): ("ASSIGNMENTID", "getAssignment"),
    ("getCourseInfo", "teacherID"):     ("teacherID",    "getCourseByTeacher"),
    ("getCourseInfo", "CourseID"):      ("CourseID",     "getCoursebyId"),
    ("Enrollement", "Course"):          ("CourseID",     "getEnrollmentByCourse"),
    ("Enrollement", "UserID"):          ("userID",       "getEnrollmentByUser"),
}

def handle_get(self, msg):
    route = GET_ROUTES.get((msg.get("INFO"), msg.get("BY")))
    if route is None:
        return {"Response Code": "400",
                "MESSAGE": {"ERROR": "Unknown GET request", "original Message": msg}}

    param_key, method_name = route
    try:
        value = int(msg["PARAMS"][param_key])
    except (KeyError, ValueError, TypeError):
        return {"Response Code": "400",
                "MESSAGE": {"ERROR": f"Missing or invalid parameter {param_key}",
                            "original Message": msg}}

    return getattr(self.database, method_name)(value)
```

And in `handle_Client`, replace the whole `if/elif` tree with:

```python
try:
    msg = data["MESSAGE"]
    if msg["METHOD"] == "GET":
        response = self.handle_get(msg)
    elif msg["METHOD"] == "POST":
        response = {"Response Code": "501", "MESSAGE": {"ERROR": "POST not implemented"}}
    else:
        response = {"Response Code": "400", "MESSAGE": {"ERROR": "Unknown METHOD"}}
except Exception as e:
    response = {"Response Code": "500", "MESSAGE": {"ERROR": str(e)}}

self.emit(response, client_socket, client_addr)
```

**Proposed standard response envelope** (so clients handle one shape):

```json
{"Response Code": "200", "DATA": [ ... ]}
{"Response Code": "400", "ERROR": "Missing or invalid parameter USERID"}
{"Response Code": "500", "ERROR": "database error ..."}
```

Adding a new endpoint then means adding one line to `GET_ROUTES` (and one handler function), not another copy of the same block.

---

## 9. Data reference (tables and columns from the handler constants)

| Table | Columns |
|---|---|
| `USER` | `id`, `CREATED_AT`, `NAME`, `ROLE` |
| `COURSE` | `id`, `created_at`, `Teacher_ID`, `Course_Name` |
| `Enrollment` | `Course_id`, `Student_id` |
| `ASSIGNMENT` | `id`, `created_at`, `Course_id`, `Teacher_id`, `resource_link`, `rubrik_link`, `Description` |
| `Submission` | `id` *(constant currently set to `"8904"`; verify)*, `Assign_id`, `Student_id`, `Submission_link` |
| `AI_Conversations` | `id`, `created_at`, `Submission_id`, `Respnses` *(verify spelling)*, `Tokens_used`, `Evaluation_score`, `AI_Score` |

Roles seen in test data: `ADMIN`, `Student`, `Teacher`.

---

## 10. Smoke-test checklist

Seed data from `driver.py`: users `1234` (Admin), `4321` (Student), `2341` (Teacher); course `9876` ("TestCourse", teacher `2341`).

| Request | Expected result |
|---|---|
| `get("userInfo", USERID=4321)` | Array with Jane Doe, role `Student` |
| `get("getCourseInfo", by="teacherID", teacherID=2341)` | Array with course `9876` |
| `get("getCourseInfo", by="CourseID", CourseID=9876)` | Array with course `9876` (after fix 4) |
| `get("userInfo", USERID="abc")` | `400` response, not a hang |
| `get("nonsense")` | `400` response, not a hang |
| Send a real request without the handshake ack | Hangs (known behavior; see Section 3) |

If any request hangs, check the **server terminal** first. It will show whether the message arrived and which line raised the exception.
