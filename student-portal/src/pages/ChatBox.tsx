import { type KeyboardEvent, useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import "./ChatBox.css";
import { useWebSocket } from "../contexts/ClientContextProvider";
import { useAuth } from "../contexts/AuthContext";
import SiteNav from "../components/SiteNav";
import { type Assignment, assignmentLabel, loadAssignments } from "../api/assignments";

const SNAPSHOT_LINES = 15;
const MAX_ATTACH = 2 * 1024 * 1024;

/* ---------- Types ---------- */
type FileInfo = {
  id: string;
  name: string;
  size: number;
  lines: number;
  code: string;
};
// A file handed to the chat box
export type Submission = {
  name?: string;
  code: string;
  size?: number;
  sentAt?: number | string;
};
// What the dashboard passes when the student presses "Chat about this assignment"
export type ChatHandoff = { submission: Submission; assignmentId: number; submissionId: number };

type Check = { label: string; pass: boolean; detail: string; state?: "pending" | "running" | "done" };
type ChatMessage = { id: string | number; from: "bot" | "me"; text?: string; file?: FileInfo };
type Tutor = { convoId: number; fileName: string };

/* ---------- The checks run on the submitted code ---------- */
function buildChecks(code: string): Check[] {
  const lines = code.split("\n");
  const longLines = lines.filter((l) => l.length > 100).length;
  const hasTabs = lines.some((l) => /^\t/.test(l));
  const hasSpaces = lines.some((l) => /^ {2,}/.test(l));
  const todos = (code.match(/\b(TODO|FIXME)\b/g) || []).length;
  const fnCount = (code.match(/\bdef\s+\w+|\bfunction\s+\w+|\w+\s*=\s*\(?[\w\s,]*\)?\s*=>|\b(public|private|static|void|int|String)\s+\w+\s*\(/g) || []).length;
  const commentCount = (code.match(/(^|\s)(#|\/\/|\/\*)/gm) || []).length;
  const returns = (code.match(/\breturn\b/g) || []).length;

  return [
    {
      label: "File received and readable",
      pass: code.trim().length > 0,
      detail: code.trim() ? `${lines.length} lines found` : "The file is empty",
    },
    {
      label: "Defines at least one function",
      pass: fnCount > 0,
      detail: fnCount ? `${fnCount} function${fnCount > 1 ? "s" : ""} found` : "No functions detected",
    },
    {
      label: "Functions return results",
      pass: returns > 0,
      detail: returns ? `${returns} return statement${returns > 1 ? "s" : ""}` : "No return statements found",
    },
    {
      label: "Code includes comments",
      pass: commentCount > 0,
      detail: commentCount ? `${commentCount} comment${commentCount > 1 ? "s" : ""} found` : "Add comments to explain your logic",
    },
    {
      label: "No unfinished TODO / FIXME notes",
      pass: todos === 0,
      detail: todos ? `${todos} left in the file` : "Looks finished",
    },
    {
      label: "Consistent indentation",
      pass: !(hasTabs && hasSpaces),
      detail: hasTabs && hasSpaces ? "Mix of tabs and spaces" : "Indentation is consistent",
    },
    {
      label: "Lines are a readable length",
      pass: longLines === 0,
      detail: longLines ? `${longLines} line${longLines > 1 ? "s" : ""} over 100 characters` : "All lines under 100 characters",
    },
  ];
}

function ChatBox() {
  const [file, setFile] = useState<FileInfo | null>(null); // { name, size, lines, code }
  const [checks, setChecks] = useState<Check[]>([]); // each: {label, detail, pass, state}
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: 1, from: "bot", text: "Hi! Upload your work for an assignment on your Dashboard, then press \"Chat about this assignment\" and I'll go over it with you." },
  ]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const lastSent = useRef<number | string | null>(null);
  const openedSubmission = useRef<number | null>(null);
  const location = useLocation();

  // AI tutor (Python server: createSubmission -> startAIConversation -> sendAIMessage)
  const { request, isConnected } = useWebSocket();
  const { serverUser, serverError } = useAuth();
  const [assignments, setAssignments] = useState<Assignment[] | null>(null); // null = still loading
  const [assignmentId, setAssignmentId] = useState<number | "">("");
  const [tutor, setTutor] = useState<Tutor | null>(null);
  const [tutorBusy, setTutorBusy] = useState(false);

  const analysisDone = checks.length > 0 && checks.every((c) => c.state === "done");
  const passedCount = checks.filter((c) => c.state === "done" && c.pass).length;
  const doneCount = checks.filter((c) => c.state === "done").length;
  const handoff = location.state as ChatHandoff | null;

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, typing]);

  // Stop the check animation when the page really closes. (React's StrictMode unmounts and
  // remounts once in development; clearing then would leave the checks stuck on "Waiting".)
  const mounted = useRef(false);
  useEffect(() => {
    mounted.current = true;
    const t = timers;
    return () => {
      mounted.current = false;
      setTimeout(() => { if (!mounted.current) t.current.forEach(clearTimeout); }, 0);
    };
  }, []);

  function addBot(text: string) {
    setMessages((m) => [...m, { id: Date.now() + Math.random(), from: "bot", text }]);
  }

  // Shows a file in the work area and runs the checks on it
  function loadSubmission(sub: Submission) {
    if (!sub || typeof sub.code !== "string") return;
    // The same file can arrive twice (StrictMode / back navigation); only check it once
    if (sub.sentAt && lastSent.current === sub.sentAt) return;
    if (sub.sentAt) lastSent.current = sub.sentAt;
    const info: FileInfo = {
      id: "sub-" + (sub.sentAt || Date.now()),
      name: sub.name || "submission.txt",
      size: sub.size ?? new Blob([sub.code]).size,
      lines: sub.code.split("\n").length,
      code: sub.code,
    };
    setFile(info);
    runChecks(info);
  }

  // 1) Sent from the dashboard ("Chat about this assignment")
  useEffect(() => {
    if (!handoff?.submission) return;
    loadSubmission(handoff.submission);
    if (handoff.assignmentId) setAssignmentId(handoff.assignmentId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state]);

  // 2) ...then open (or resume) the AI tutor on that submission once the server knows who we are
  useEffect(() => {
    if (!handoff?.submissionId || !serverUser || openedSubmission.current === handoff.submissionId) return;
    openedSubmission.current = handoff.submissionId;
    openConversation(handoff.submissionId, handoff.submission.name || "submission");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state, serverUser]);

  // 3) The assignments this student can open an AI tutor session for (courses they're enrolled in)
  useEffect(() => {
    if (!serverUser) { setAssignments(null); return; }
    let alive = true;
    loadAssignments(request, serverUser.id)
      .then((found) => {
        if (!alive) return;
        setAssignments(found);
        if (found.length === 1) setAssignmentId((cur) => (cur === "" ? found[0].id : cur));
      })
      .catch((e: Error) => { console.error("Server:", e.message); if (alive) setAssignments([]); });
    return () => { alive = false; };
  }, [serverUser, request]);

  function runChecks(info: FileInfo) {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    const results = buildChecks(info.code);
    setChecks(results.map((r) => ({ ...r, state: "pending" })));

    results.forEach((_, i) => {
      timers.current.push(setTimeout(() => {
        setChecks((cs) => cs.map((c, j) => (j === i ? { ...c, state: "running" } : c)));
      }, i * 700 + 200));
      timers.current.push(setTimeout(() => {
        setChecks((cs) => cs.map((c, j) => (j === i ? { ...c, state: "done" } : c)));
      }, i * 700 + 750));
    });
  }

  // Attach a file in the chat
  function attachFile(f: File | undefined) {
    if (!f) return;
    if (f.size > MAX_ATTACH) { addBot(`${f.name} is larger than 2 MB, so I couldn't attach it.`); return; }
    const reader = new FileReader();
    reader.onload = () => {
      const code = String(reader.result || "");
      const att: FileInfo = { id: "att-" + Date.now(), name: f.name, size: f.size, lines: code.split("\n").length, code };
      setMessages((m) => [...m, { id: Date.now(), from: "me", file: att }]);
      setTyping(true);
      setTimeout(() => {
        addBot(`I've got ${att.name}. Press "Check this file" to look at it, then choose its assignment and start the AI tutor.`);
        setTyping(false);
      }, 600);
    };
    reader.onerror = () => addBot("Sorry, I couldn't read that file. Try a code or text file.");
    reader.readAsText(f);
  }

  // Opens the AI tutor on a submission the server already has. Calling it again resumes the
  // saved conversation (the server returns the full history).
  async function openConversation(submissionId: number, fileName: string) {
    setTutorBusy(true);
    setTyping(true);
    try {
      const convo = await request<{ CONVOID: number; MESSAGES: { role: string; content: string }[] }>({ MESSAGE: { METHOD: "POST", INFO: "startAIConversation",
        PARAMS: { SUBMISSIONID: submissionId } } });
      const stamp = Date.now();
      setTutor({ convoId: convo.CONVOID, fileName });
      setMessages((m) => [...m, ...convo.MESSAGES.map((x, i) => ({ id: `tutor-${convo.CONVOID}-${stamp}-${i}`, from: (x.role === "user" ? "me" : "bot") as ChatMessage["from"], text: x.content }))]);
    } catch (e) {
      addBot(`I couldn't start the AI tutor: ${(e as Error).message}`);
    } finally {
      setTutorBusy(false);
      setTyping(false);
    }
  }

  // Hands a file attached here to the server, then opens the AI tutor on it
  async function startTutor() {
    if (!file || assignmentId === "" || tutorBusy) return;
    setTutorBusy(true);
    setTyping(true);
    let submissionId: number;
    try {
      const sub = await request<{ SUBMISSIONID: number }>({ MESSAGE: { METHOD: "POST", INFO: "createSubmission",
        PARAMS: { ASSIGNMENTID: assignmentId, NAME: file.name, CODE: file.code } } });
      submissionId = sub.SUBMISSIONID;
    } catch (e) {
      addBot(`I couldn't start the AI tutor: ${(e as Error).message}`);
      setTutorBusy(false);
      setTyping(false);
      return;
    }
    await openConversation(submissionId, file.name);
  }

  function send() {
    const text = input.trim();
    if (!text || typing) return;
    setMessages((m) => [...m, { id: Date.now(), from: "me", text }]);
    setInput("");
    if (!tutor) {
      addBot(file
        ? `Choose the assignment for ${file.name} above and press "Start AI tutor on this file", or upload it from your Dashboard.`
        : "Upload your work on your Dashboard and press \"Chat about this assignment\" to talk with the AI tutor.");
      return;
    }
    setTyping(true);
    request<{ REPLY: string }>({ MESSAGE: { METHOD: "POST", INFO: "sendAIMessage", PARAMS: { CONVOID: tutor.convoId, TEXT: text } } })
      .then((m) => addBot(m.REPLY))
      .catch((e: Error) => addBot(`The AI tutor didn't answer: ${e.message}`))
      .finally(() => setTyping(false));
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  }

  const snapshot = file ? file.code.split("\n").slice(0, SNAPSHOT_LINES) : [];

  let tutorStatus: string | null = null;
  if (!isConnected) tutorStatus = "The AI tutor needs the server. Start Server/SocketServer.py.";
  else if (serverError) tutorStatus = `The server couldn't verify your sign in: ${serverError}`;
  else if (!serverUser || assignments === null) tutorStatus = "Connecting to the AI tutor…";
  else if (!assignments.length) tutorStatus = "You aren't enrolled in a course with assignments yet, so the AI tutor isn't available.";

  return (
    <div className="chatbox-page">
      <SiteNav />
      <div className="app">
        <header>
          <h1 className="title">AI chat — talk about your assignment</h1>
          <p className="subtitle">Work you upload on your Dashboard shows up here, and the AI tutor talks it through with you.</p>
        </header>

        <div className="work">
          {!file ? (
            <div className="empty">
              <strong>No assignment selected yet</strong>
              Upload your work on your <Link to="/dashboard">Dashboard</Link> and press "Chat about this assignment".
              The checks and a snapshot of your code will show up here.
            </div>
          ) : (
            <>
              <div className="filebar">
                <div>
                  <span className="name">{file.name}</span>
                  <span className="meta">{file.lines} lines · {(file.size / 1024).toFixed(1)} KB</span>
                </div>
                <Link className="link-btn" to="/dashboard">Back to dashboard</Link>
              </div>

              <div className="tutorbar">
                <strong>AI tutor</strong>
                {tutorStatus ? (
                  <span className="meta">{tutorStatus}</span>
                ) : tutor ? (
                  <span className="meta">Talking about {tutor.fileName}</span>
                ) : tutorBusy ? (
                  <span className="meta">Starting the AI tutor…</span>
                ) : (
                  <>
                    <select aria-label="Assignment" value={assignmentId}
                      onChange={(e) => setAssignmentId(e.target.value ? Number(e.target.value) : "")}>
                      <option value="">Choose the assignment…</option>
                      {assignments!.map((a) => <option key={a.id} value={a.id}>{assignmentLabel(a)}</option>)}
                    </select>
                    <button className="btn" onClick={startTutor} disabled={assignmentId === "" || typing}>
                      Start AI tutor on this file
                    </button>
                  </>
                )}
              </div>

              <div className="results">
                <div className="card">
                  <h2>Code checks</h2>
                  <ul className="checks">
                    {checks.map((c) => {
                      const cls = c.state === "done" ? (c.pass ? "pass" : "fail") : c.state;
                      return (
                        <li key={c.label} className={cls}>
                          <span className="status">{c.state === "done" ? (c.pass ? "✓" : "✕") : ""}</span>
                          <div>
                            <div className="label">{c.label}</div>
                            <div className="detail">
                              {c.state === "done" ? c.detail : c.state === "running" ? "Checking…" : "Waiting"}
                            </div>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                  <div className="score">
                    <span className="detail" style={{ color: "var(--muted)", fontSize: 12 }}>
                      {analysisDone ? "Check complete" : `Checking ${doneCount} of ${checks.length}…`}
                    </span>
                    <span className="big">{passedCount}/{checks.length}</span>
                  </div>
                  <div className="bar">
                    <div className="fill" style={{ width: `${checks.length ? (doneCount / checks.length) * 100 : 0}%` }} />
                  </div>
                </div>

                <div className="code-card">
                  <div className="code-head">
                    <span>{file.name}</span>
                    <span>snapshot</span>
                  </div>
                  <pre className="code">
                    {snapshot.map((line, i) => (
                      <div key={i} className="line">
                        <span className="ln">{i + 1}</span>
                        <span>{line || " "}</span>
                      </div>
                    ))}
                  </pre>
                  {file.lines > SNAPSHOT_LINES && (
                    <div className="more">… {file.lines - SNAPSHOT_LINES} more lines</div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        <section className="chat">
          <div className="chat-head">
            <strong>AI chat</strong>
            <span className="pill">
              {file ? `Using ${file.name}` : "No work selected"}
              {tutor ? " · AI tutor" : ""}
            </span>
          </div>
          <div className="messages">
            {messages.map((m) => (
              <div key={m.id} className={`msg ${m.from}`}>
                {m.from === "bot" && <span className="avatar">AI</span>}
                {m.file ? (
                  <div className="bubble attach">
                    <span className="fname">📄 {m.file.name}</span>
                    <span className="fmeta">{m.file.lines} lines · {(m.file.size / 1024).toFixed(1)} KB</span>
                    <span className="actions">
                      <button className="link-btn" onClick={() => { setTutor(null); loadSubmission(m.file!); }}>Check this file</button>
                    </span>
                  </div>
                ) : (
                  <div className="bubble">{m.text}</div>
                )}
              </div>
            ))}
            {typing && (
              <div className="msg bot">
                <span className="avatar">AI</span>
                <div className="bubble typing"><span></span><span></span><span></span></div>
              </div>
            )}
            <div ref={endRef} />
          </div>
          <div className="composer">
            <label className="clip" title="Attach a file" aria-label="Attach a file">
              📎
              <input
                type="file"
                accept=".py,.js,.jsx,.ts,.java,.c,.cpp,.cs,.html,.css,.txt,.md,.json,.csv"
                onChange={(e) => { attachFile(e.target.files?.[0]); e.target.value = ""; }}
              />
            </label>
            <textarea
              placeholder={tutor ? "Ask the AI tutor anything…" : "Ask the AI anything…"}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
            />
            <button className="btn" onClick={send} disabled={!input.trim() || typing}>Send</button>
          </div>
        </section>
      </div>
    </div>
  );
}

export default ChatBox;
