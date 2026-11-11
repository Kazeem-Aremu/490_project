# 490_project

## Authors:
### Team 1
- Garrick Thomas
- Ayo Omotola
- Miles Magruder
- Jossie Gates
- Misael Ramos​

### Team 2
- Nyles Burton
- Kazeem Aremu
- Portia Ogbuja
- Faith Hall
- Osaosemwen Osifo


## Teacher:

.Azemi Asad

## Description

This project uses AI to verify genuine student understanding by asking targeted follow-up questions about their submitted work, rather than relying solely on plagiarism or similarity detection. If a student answers incorrectly, the system doesn't simply penalize them — it shifts into a hint-based mode that walks them toward the right answer. Successfully reasoning through the hints allows the student to recover partial credit, turning the integrity check into a learning opportunity rather than a purely punitive one.

## Running the project

**New to the project?** Start with [Docs/System_Handoff.md](Docs/System_Handoff.md): what the system does, how it works, its status and next steps.

Everything the students and instructors see is one React + TypeScript app in `student-portal/`. It talks to the Python server in `Server/`.

```
Browser (student-portal, Vite)                     Python (Server/)
  /           Sign in / sign up  ── Supabase Auth
  /dashboard  Assignments + uploads ──┐
  /chat       AI chat (AI tutor)    ──┤  WebSocket ws://127.0.0.1:8343   WebSocketServer.py ─┐
                                      └────────────────────────────────────►                   ├─ SocketServer.Server ─► Supabase / OpenAI
                                           TCP 127.0.0.1:8342 (test clients) ──────────────────┘
```

1. **Server**: in `Server/`, create `.env` (see `Docs/Server_API_Documentation.md` §2), then
   ```
   pip install supabase python-dotenv openai websockets pypdf python-docx
   py SocketServer.py
   ```
2. **Portal**: in `student-portal/`, put `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` (the `sb_publishable_…` key, never the secret key) in `.env.local`, then
   ```
   npm install
   npm run dev
   ```
   and open the printed address. `npm run typecheck` checks the TypeScript.
3. Sign up on the portal and choose **Student** or **Teacher**. The first sign in creates your `USER` row with that role.
   Supabase's built-in email allows only a few sign-ups per hour ("email rate limit exceeded"). Without your own SMTP server, create accounts with `py Server/createTestUser.py <email> <student|teacher> <first> <last>` (no email sent).
   For a mock class with one mock assignment, sign up as a Teacher, sign in once, then run `py Server/mockClass.py <teacher email>` (`--clean` removes it). The teacher then adds students on the dashboard with **Add students**. To use the AI tutor you must be enrolled in a course that has assignments. To try it with the seeded test data, run `py Server/linkAuthUser.py <your email> 20` (TEST Student A) and sign in again.

| Page | What it is |
|---|---|
| `/login`, `/signup`, `/forgot-password`, `/reset-password` | Sign in pages (Supabase Auth) in a shared layout (`pages/auth/`). Sign up has the Student/Teacher choice. Signing in goes to the dashboard; any other address goes to `/login`. |
| `/dashboard` | Laid out like the instructor dashboard redesign (UMES top bar, pill tabs, stat cards). **Teachers** (tabs Overview / Classes and Students / Assignment Setup): **Create class** (`createCourse`), **New assignment** with an optional PDF/DOCX assignment sheet and rubric (`createAssignment`; the AI tutor reads both), their classes, assignments and enrolled students; **Add students** enrolls the ticked students (`StudentList`, `enrollStudent`, `unenrollStudent`). **Students:** their assignments (`Enrollement` → `getCourseInfo` → `AssignmentInfo`). **View assignment / View rubric** open the teacher's files (`assignmentFile`). **Upload work** sends the file to the server (`createSubmission`); **Chat about this assignment** opens it in `/chat`. |
| `/chat` | AI chat: code checks, snapshot, and the AI tutor (`startAIConversation`, then `sendAIMessage`). Opened from the dashboard it starts (or resumes) the tutor on that upload. A file attached with 📎 can also be sent with **Start AI tutor on this file**. |
