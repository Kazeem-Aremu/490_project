# Session State (WS4) and Running the Demo

## 1. Running the demo

### Quick demo (no setup)
Double-click `Understanding_Review_Prototype.html`. It runs entirely in the browser with fake data
and quick-login buttons. It keeps everything in memory, so a refresh resets it.

### Full stack
1. `Server/.env` (never commit it):
   ```
   SUPABASE_URL=https://<project>.supabase.co
   SUPABASE_SECRET_KEY=<secret / service role key>
   ANTHROPIC_API_KEY=<key>
   ```
   `AgentInterface.py` now uses Anthropic, so `OPEN_AI_KEY` from the older docs is no longer used.
2. In the Supabase SQL editor, run `Server/setup_review_sessions.sql` once.
3. `pip install -r Server/requirements.txt`
4. `python Server/databbaseSeeder.py` to create test rows (ids are saved to `seed_ids.json`).
5. `python Server/SocketServer.py`. It now listens on two ports:
   - `8342` raw TCP, for Python clients (`driver.py`, `testClient.py`)
   - `8343` WebSocket, for browsers (`student-portal` already connects here)
6. Front end: in `student-portal/`, create `.env` with `VITE_SUPABASE_URL` and
   `VITE_SUPABASE_PUBLISHABLE_KEY`, then `npm install` and `npm run dev`.

Both ports use the same JSON messages and the same handler. Over WebSocket, each frame is one
message (no `\n` needed) and the handshake ack is optional.

## 2. What the session stores

Table `Review_Sessions`, one row per submission, following the list in `Team1Week7E5Docs.md`:

| Column | Meaning |
|---|---|
| `id` | Session ID |
| `submission_id`, `user_id`, `assignment_id` | Who and what (filled from the Submission row) |
| `attempt_number` | 1 for the student's first session on this assignment, then 2, 3, ... |
| `route`, `reason_code`, `path` | Router decision: PASS → path `A`, FAIL → path `B`, MANUAL_REVIEW → `instructor` |
| `status` | `active`, `retry`, `escalated` or `complete` |
| `current_question`, `retry_number` | Where the student is in the question flow |
| `questions` | Questions asked so far (JSON list) |
| `scores` | One `{question, answer, score, retry}` per answer, score 1–5 |

Tokens used stay in `AI_Conversations.Tokens_used`, which shares the submission id.

## 3. Endpoints

**Create the session:** `POST routeSubmission` (existing router contract). On PASS, FAIL or
MANUAL_REVIEW the server creates or updates the session and returns it in `MESSAGE.session`.
REJECTED uploads create nothing.

**Read it:** `GET sessionInfo` with `PARAMS: {"SUBMISSIONID": 7}`

**Change progress:** `POST updateSession`
```json
{"MESSAGE": {"METHOD": "POST", "INFO": "updateSession",
  "PARAMS": {"USERID": 20, "SUBMISSIONID": 7, "current_question": 1, "retry_number": 0,
             "status": "active", "questions": ["Q1 ...", "Q2 ..."]}}}
```
Send only the fields you're changing.

**Save a scored answer:** `POST recordAnswer`
```json
{"MESSAGE": {"METHOD": "POST", "INFO": "recordAnswer",
  "PARAMS": {"USERID": 20, "SUBMISSIONID": 7, "QUESTION": "Q1 ...", "ANSWER": "...", "SCORE": 4}}}
```
Appends to `scores` on the server, so two requests can't overwrite each other.

Errors: `400` bad input, `403` the session belongs to another student, `404` no session yet.

## 4. Known limits
- `USERID` is still trusted as sent (see Server docs 8.2). Verify a Supabase login token per
  connection before real student data is used.
- The Path A question flow itself (generate questions, score answers, decide retry or escalate)
  isn't built yet. These endpoints are where that flow saves its state as it's built.
