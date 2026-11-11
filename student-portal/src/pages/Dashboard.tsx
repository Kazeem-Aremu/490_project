import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Dashboard.css";
import SiteNav from "../components/SiteNav";
import { useAuth } from "../contexts/AuthContext";
import { useWebSocket } from "../contexts/ClientContextProvider";
import { type Assignment, loadAssignments } from "../api/assignments";
import type { ChatHandoff } from "./ChatBox";
import TeacherDashboard from "./TeacherDashboard";
import FileLinks from "../components/FileLinks";

// Dashboard: teachers get their classes (TeacherDashboard.tsx); students get the view below.
// Student dashboard: the student's real assignments (from the server). Upload work for one,
// then open the chat to talk with the AI tutor about it.
const MAX_UPLOAD = 200_000; // bytes; same as the server's MAX_FILE_BYTES
const ACCEPT = ".py,.js,.jsx,.ts,.tsx,.java,.c,.cpp,.cs,.html,.css,.txt,.md,.json,.csv";

// The latest upload per assignment. The server keeps the file; the browser remembers which
// submission is the latest so "Chat about this assignment" still works after a reload.
type Upload = { submissionId: number; name: string; code: string; size: number; at: number };
type Uploads = Record<number, Upload>;

const storeKey = (userId: number) => `dashboard_uploads_${userId}`;
function readUploads(userId: number): Uploads {
  try { return JSON.parse(localStorage.getItem(storeKey(userId)) || "{}"); } catch { return {}; }
}
function writeUploads(userId: number, uploads: Uploads) {
  try { localStorage.setItem(storeKey(userId), JSON.stringify(uploads)); } catch { /* storage full or blocked */ }
}
const fmt = (t: number) => new Date(t).toLocaleString([], { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });

function StudentDashboard() {
  const { request, isConnected } = useWebSocket();
  const { serverUser, serverError } = useAuth();
  const navigate = useNavigate();
  const [assignments, setAssignments] = useState<Assignment[] | null>(null); // null = still loading
  const [loadError, setLoadError] = useState<string | null>(null);
  const [uploads, setUploads] = useState<Uploads>({});
  const [busyId, setBusyId] = useState<number | null>(null);
  const [errors, setErrors] = useState<Record<number, string>>({});

  useEffect(() => {
    if (!serverUser) { setAssignments(null); return; }
    setUploads(readUploads(serverUser.id));
    let alive = true;
    setLoadError(null);
    loadAssignments(request, serverUser.id)
      .then((a) => { if (alive) setAssignments(a); })
      .catch((e: Error) => { if (alive) { setAssignments([]); setLoadError(e.message); } });
    return () => { alive = false; };
  }, [serverUser, request]);

  function pickFile(a: Assignment) {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ACCEPT;
    input.onchange = () => upload(a, input.files?.[0]);
    input.click();
  }

  async function upload(a: Assignment, f: File | undefined) {
    if (!f || !serverUser) return;
    const userId = serverUser.id;
    setErrors((e) => ({ ...e, [a.id]: "" }));
    setBusyId(a.id);
    try {
      if (f.size > MAX_UPLOAD) throw new Error(`${f.name} is larger than ${MAX_UPLOAD / 1000} KB.`);
      const code = await f.text();
      if (!code.trim()) throw new Error(`${f.name} is empty.`);
      if (code.includes("\u0000")) throw new Error(`${f.name} isn't a text or code file.`);
      const res = await request<{ SUBMISSIONID: number }>({ MESSAGE: { METHOD: "POST", INFO: "createSubmission",
        PARAMS: { ASSIGNMENTID: a.id, NAME: f.name, CODE: code } } });
      const next = { ...readUploads(userId), [a.id]: { submissionId: res.SUBMISSIONID, name: f.name, code, size: f.size, at: Date.now() } };
      writeUploads(userId, next);
      setUploads(next);
    } catch (e) {
      setErrors((x) => ({ ...x, [a.id]: (e as Error).message }));
    } finally {
      setBusyId(null);
    }
  }

  function openChat(a: Assignment, up: Upload) {
    const state: ChatHandoff = {
      submission: { name: up.name, code: up.code, size: up.size, sentAt: up.submissionId },
      assignmentId: a.id,
      submissionId: up.submissionId,
    };
    navigate("/chat", { state });
  }

  let status: string | null = null;
  if (!isConnected) status = "The dashboard needs the server. Start Server/SocketServer.py.";
  else if (serverError) status = `The server couldn't verify your sign in: ${serverError}`;
  else if (!serverUser || assignments === null) status = "Loading your assignments…";
  else if (loadError) status = `Your assignments couldn't be loaded: ${loadError}`;
  else if (!assignments.length) status = "You aren't enrolled in a course with assignments yet.";

  const firstName = serverUser?.NAME?.split(" ")[0];

  return (
    <div className="ur-page">
      <SiteNav />
      {/* topbar + pill tab strip from the instructor dashboard redesign */}
      <div className="topbar">
        <div className="brand">Understanding Review</div>
        <div className="who">
          <span>{serverUser?.NAME}</span>
          <span className="pill p-info">student</span>
        </div>
      </div>
      <div className="shell">
      <nav className="rail" aria-label="Sections"><button className="on">My Assignments</button></nav>
      <main className="main">
        <div className="head">
          <div>
            <h1>My Assignments</h1>
            <p className="muted">
              {firstName ? `Welcome back, ${firstName}. ` : ""}
              Upload your work for an assignment, then chat with the AI tutor about it.
            </p>
          </div>
        </div>

        {status ? <div className="note">{status}</div> : assignments!.map((a) => {
          const up = uploads[a.id];
          const busy = busyId === a.id;
          return (
            <div className="card" key={a.id}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <h3>{a.courseName}</h3>
                <span className="muted">Assignment {a.id}</span>
              </div>
              {a.description && <p style={{ marginTop: 8 }}>{a.description}</p>}
              <FileLinks a={a} />
              <div className="row" style={{ margin: "10px 0 0" }}>
                Your work
                {up ? <>
                  <span className="pill p-ok">uploaded</span>
                  <span className="mono">{up.name}</span>
                  <span className="muted">{fmt(up.at)}</span>
                </> : <span className="pill p-mute">not uploaded</span>}
              </div>
              <div className="note">
                {up ? "Your work is uploaded. Chat with the AI tutor about it, or upload a new version."
                  : "Upload your solution to start. Then the AI tutor goes over it with you."}
              </div>
              {errors[a.id] && <div className="note bad" role="alert">{errors[a.id]}</div>}
              <div className="row" style={{ marginTop: 10 }}>
                <button className={"btn" + (up ? " sec" : "")} onClick={() => pickFile(a)} disabled={busyId !== null}>
                  {busy ? "Uploading…" : up ? "Upload a new version" : "Upload work"}
                </button>
                {up && <button className="btn" onClick={() => openChat(a, up)} disabled={busy}>Chat about this assignment</button>}
              </div>
            </div>
          );
        })}
      </main>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { serverUser } = useAuth();
  if (serverUser?.ROLE?.toLowerCase() === "teacher") {
    return (
      <div className="ur-page">
        <SiteNav />
        <TeacherDashboard />
      </div>
    );
  }
  return <StudentDashboard />;
}
