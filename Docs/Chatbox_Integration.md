# 490 project: React chatbox integration

The chatbox is integrated into the existing `student-portal`, alongside the login prototype. Open the portal's "Open assignment chat" link or visit `http://localhost:5173/#chat`.

## Start locally (three terminals)

Install Python dependencies once from the repository root:

```
python -m pip install -r Server/requirements.txt
```

Keep the server's existing environment settings available to its dotenv loader: `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, and `OPEN_AI_KEY`. Never put server secrets in frontend `VITE_` variables. Use existing team-provided credentials; no private keys are included in this package.

Terminal 1, from the repository root:

```
python Server/SocketServer.py
```

Terminal 2, from the repository root:

```
python Server/WebSocketBridge.py
```

Terminal 3:

```
cd student-portal
npm install
npm run dev -- --port 5173 --strictPort
```

Copy `student-portal/.env.example` to `student-portal/.env` for frontend configuration. Blank Supabase configuration does not prevent the login prototype or chatbox from displaying. The WebSocket URL defaults to `ws://127.0.0.1:8343`. Restart Vite after changing `.env`.

Open the localhost URL in the browser. Double-clicking the source `index.html` will not run JSX. The original login/signup UI is preserved; it still displays prototype messages and does not authenticate students.

## Conversation flow

The local bridge connects browser WebSocket port 8343 to the existing newline-framed TCP server on port 8342. It consumes the TCP handshake and sends the required acknowledgement before forwarding requests. Requests are processed sequentially and replies keep the existing `Response Code` / `MESSAGE` envelope. The bridge forwards only the two AI POST operations, binds to loopback, and accepts the local Vite origins by default.

The chatbox sends `startAIConversation` with integer `USERID` and `SUBMISSIONID`, restores returned `MESSAGES`, stores the returned `CONVOID`, and uses `sendAIMessage` with `USERID`, `CONVOID`, and `TEXT`. User messages are limited to 4,000 characters. Busy controls prevent overlapping requests. Errors preserve the message text for retry; a lost response may already have been saved by the server, so reopen/resume the conversation before retrying after a disconnection.

The server retrieves the submission from its database/storage and owns AI history. Browser regex grading, simulated replies, and the standalone chatbox's separate `files` table upload flow are not used by this integrated screen. Uploading a new file is not implemented because the current server exposes no submission-upload route. Use an existing submission created by the team's upload/database workflow.

## Dashboard integration still needed

The local screen temporarily takes real database student and submission IDs, or pre-fills them from `?userId=123&submissionId=7#chat`. These are integration inputs, not authentication. The existing backend expects integer database IDs; a Supabase Auth UUID must be mapped to the correct student record by the team's authenticated backend. No automatic mapping can be inferred from the supplied repository.

The dashboard should eventually supply the selected submission ID and the authenticated student's identity. The backend currently trusts the client-supplied USERID: the ownership checks do not prove who the caller is. Keep this loopback-only bridge for local development until verified authentication is implemented. Do not expose it publicly as-is.

No report/test score is fabricated from chat replies. Actual test/routing output can be connected separately once the server provides it; `routeSubmission` exists as a router helper but is not dispatched by the current SocketServer POST handler.

## Validation

```
cd student-portal
npm run build
```

```
cd Server
python -m unittest test_websocket_bridge.py
```

The bridge test uses a mock TCP backend, checks handshake acknowledgement, fragmented replies, both AI operations, and rejection of unsupported operations. It makes no AI calls and changes no Supabase data. Live AI/authentication/database validation requires the team's running services.

Verified in this update: React production build, ESLint, and the offline WebSocket/TCP bridge integration test passed. Browser interaction validation could not run because this environment blocked Chromium startup.
