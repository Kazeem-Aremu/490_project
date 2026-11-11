import { type FormEvent, type ReactNode, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useWebSocket } from "../contexts/ClientContextProvider";
import { type Assignment, type FileKind, fileToBase64, toAssignment } from "../api/assignments";
import FileLinks from "../components/FileLinks";

// Teacher dashboard, laid out like the instructor dashboard redesign (instructor-dashboard-redesign
// branch: UMES topbar, pill tabs, stat cards, tables) but filled with real data from the server.
// Tabs: Overview (stats + roster), Classes and Students, Assignment Setup.
// "Add students" lets the teacher pick students (accounts that signed up as Student) to enroll.
// "New assignment" uploads an assignment sheet and rubric (PDF or DOCX) that students can open
// and that the AI tutor reads.
type Row = Record<string, unknown>;
type Student = { id: number; NAME: string };
type Course = { id: number; name: string; assignments: Assignment[]; roster: number[] };

type Tab = "overview" | "classes" | "setup";
const TABS: [Tab, string][] = [["overview", "Overview"], ["classes", "Classes and Students"], ["setup", "Assignment Setup"]];

const Head = ({ title, sub }: { title: ReactNode; sub?: ReactNode }) => (
  <div className="head"><div><h1>{title}</h1>{sub != null && <p className="muted">{sub}</p>}</div></div>
);

const MAX_FILE_MB = 10; // same as the server's AssignmentService.MAX_FILE_BYTES
const DOC_TYPES = ".pdf,.docx";

// The "New assignment" form inside one class card
function NewAssignment({ course, onCreated }: { course: Course; onCreated: (a: Assignment) => void }) {
  const { request } = useWebSocket();
  const [open, setOpen] = useState(false);
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState<Partial<Record<FileKind, File>>>({});
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [formKey, setFormKey] = useState(0); // remounts the file inputs to clear them

  function pick(kind: FileKind, f: File | undefined) {
    setMsg(null);
    if (f && !/\.(pdf|docx)$/i.test(f.name)) { setMsg({ ok: false, text: `${f.name} must be a PDF or DOCX.` }); return; }
    if (f && f.size > MAX_FILE_MB * 1024 * 1024) { setMsg({ ok: false, text: `${f.name} is larger than ${MAX_FILE_MB} MB.` }); return; }
    setFiles((x) => ({ ...x, [kind]: f }));
  }

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!description.trim() || saving) return;
    setSaving(true);
    setMsg(null);
    try {
      const FILES: Record<string, { NAME: string; DATA: string }> = {};
      for (const kind of ["assignment", "rubric"] as FileKind[]) {
        const f = files[kind];
        if (f) FILES[kind] = { NAME: f.name, DATA: await fileToBase64(f) };
      }
      const res = await request<{ ASSIGNMENTID: number; DESCRIPTION: string; HASFILE: boolean; HASRUBRIC: boolean; NOTEXT: string[] }>(
        { MESSAGE: { METHOD: "POST", INFO: "createAssignment", PARAMS: { COURSEID: course.id, DESCRIPTION: description.trim(), FILES } } },
        180_000);
      onCreated({ id: res.ASSIGNMENTID, courseName: course.name, description: res.DESCRIPTION, hasFile: res.HASFILE, hasRubric: res.HASRUBRIC });
      setDescription("");
      setFiles({});
      setFormKey((k) => k + 1);
      setOpen(false);
      setMsg({ ok: true, text: "Assignment created. Students in this class can see it now." + (res.NOTEXT.length
        ? ` The text of the ${res.NOTEXT.join(" and ")} file couldn't be read (a scanned PDF?), so the AI tutor won't see it.` : "") });
    } catch (err) {
      setMsg({ ok: false, text: `The assignment couldn't be created: ${(err as Error).message}` });
    } finally {
      setSaving(false);
    }
  }

  if (!open) {
    return <>
      <button className="btn sec sm" style={{ marginTop: 8 }} onClick={() => { setOpen(true); setMsg(null); }}>New assignment</button>
      {msg && <div className={"note " + (msg.ok ? "ok" : "bad")} role="status">{msg.text}</div>}
    </>;
  }
  return (
    <form className="new-asg" onSubmit={save} key={formKey}>
      <label htmlFor={`desc-${course.id}`}>Title and short description</label>
      <textarea id={`desc-${course.id}`} rows={3} maxLength={4000} required value={description}
        onChange={(e) => setDescription(e.target.value)} placeholder="e.g. Homework 2: Loops. Write sum_even(nums)…" />
      <label htmlFor={`asg-${course.id}`}>Assignment file (PDF or DOCX, optional)</label>
      <input id={`asg-${course.id}`} type="file" accept={DOC_TYPES} onChange={(e) => pick("assignment", e.target.files?.[0])} />
      <label htmlFor={`rub-${course.id}`}>Rubric (PDF or DOCX, optional)</label>
      <input id={`rub-${course.id}`} type="file" accept={DOC_TYPES} onChange={(e) => pick("rubric", e.target.files?.[0])} />
      <p className="muted" style={{ fontSize: ".8rem", margin: "6px 0 0" }}>Students can open both files. The AI tutor reads them to guide students, but never gives a grade.</p>
      {msg && <div className={"note " + (msg.ok ? "ok" : "bad")} role="status">{msg.text}</div>}
      <div className="row" style={{ marginTop: 10 }}>
        <button className="btn" type="submit" disabled={!description.trim() || saving}>{saving ? "Uploading…" : "Create assignment"}</button>
        <button className="btn sec" type="button" disabled={saving} onClick={() => { setOpen(false); setMsg(null); }}>Cancel</button>
      </div>
    </form>
  );
}

export default function TeacherDashboard() {
  const { request, isConnected } = useWebSocket();
  const { serverUser, serverError } = useAuth();
  const [courses, setCourses] = useState<Course[] | null>(null); // null = still loading
  const [students, setStudents] = useState<Student[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [picked, setPicked] = useState<Record<number, number[]>>({}); // course id -> student ids ticked
  const [busy, setBusy] = useState<number | null>(null); // course id being changed
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);
  const [createMsg, setCreateMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [params, setParams] = useSearchParams();
  const tab: Tab = TABS.some(([t]) => t === params.get("tab")) ? params.get("tab") as Tab : "overview";
  const go = (t: Tab) => setParams(t === "overview" ? {} : { tab: t }, { replace: true });

  const get = useCallback((INFO: string, BY: string | null, PARAMS: Row) =>
    request<Row[]>({ MESSAGE: { METHOD: "GET", INFO, ...(BY ? { BY } : {}), PARAMS } }), [request]);

  const rosterOf = useCallback(async (courseId: number) =>
    (await get("Enrollement", "Course", { CourseID: courseId })).map((e) => Number(e.Student_id)), [get]);

  useEffect(() => {
    if (!serverUser) { setCourses(null); return; }
    let alive = true;
    setLoadError(null);
    (async () => {
      const [rows, list] = await Promise.all([
        get("getCourseInfo", "teacherID", { teacherID: serverUser.id }),
        request<Student[]>({ MESSAGE: { METHOD: "GET", INFO: "StudentList", PARAMS: {} } }),
      ]);
      const found: Course[] = [];
      for (const c of rows) {
        const id = Number(c.id);
        const name = String(c.Course_Name ?? `Course ${id}`);
        const [asgs, roster] = await Promise.all([get("AssignmentInfo", "CourseID", { COURSEID: id }), rosterOf(id)]);
        found.push({ id, name, assignments: asgs.map((a) => toAssignment(a, name)), roster });
      }
      if (!alive) return;
      setStudents(list);
      setCourses(found);
    })().catch((e: Error) => { if (alive) { setCourses([]); setLoadError(e.message); } });
    return () => { alive = false; };
  }, [serverUser, get, request, rosterOf]);

  function toggle(courseId: number, studentId: number) {
    setPicked((p) => {
      const cur = p[courseId] ?? [];
      return { ...p, [courseId]: cur.includes(studentId) ? cur.filter((x) => x !== studentId) : [...cur, studentId] };
    });
  }

  // enrollStudent / unenrollStudent for each student, then reload the class list from the server
  async function change(course: Course, studentIds: number[], add: boolean) {
    if (!studentIds.length) return;
    setBusy(course.id);
    setNotes((n) => ({ ...n, [course.id]: "" }));
    const failed: string[] = [];
    for (const sid of studentIds) {
      try {
        await request({ MESSAGE: { METHOD: "POST", INFO: add ? "enrollStudent" : "unenrollStudent",
          PARAMS: { COURSEID: course.id, STUDENTID: sid } } });
      } catch (e) {
        failed.push(`${nameOf(sid)}: ${(e as Error).message}`);
      }
    }
    try {
      const roster = await rosterOf(course.id);
      setCourses((cs) => cs && cs.map((c) => (c.id === course.id ? { ...c, roster } : c)));
    } catch { /* keep the old list */ }
    if (add) setPicked((p) => ({ ...p, [course.id]: [] }));
    const done = studentIds.length - failed.length;
    setNotes((n) => ({ ...n, [course.id]: failed.length
      ? `Some changes failed. ${failed.join(" ")}`
      : add ? `Added ${done} student${done === 1 ? "" : "s"}.` : "Student removed." }));
    setBusy(null);
  }

  async function createClass(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const name = newName.trim();
    if (!name || creating) return;
    setCreating(true);
    setCreateMsg(null);
    try {
      const res = await request<{ COURSEID: number; NAME: string }>({ MESSAGE: { METHOD: "POST", INFO: "createCourse", PARAMS: { NAME: name } } });
      setCourses((cs) => [{ id: res.COURSEID, name: res.NAME, assignments: [], roster: [] }, ...(cs ?? [])]);
      setNewName("");
      setCreateMsg({ ok: true, text: `Created ${res.NAME}. Add students to it below.` });
    } catch (err) {
      setCreateMsg({ ok: false, text: `The class couldn't be created: ${(err as Error).message}` });
    } finally {
      setCreating(false);
    }
  }

  const nameOf = (id: number) => students.find((s) => s.id === id)?.NAME ?? `Student ${id}`;

  let status: string | null = null;
  if (!isConnected) status = "The dashboard needs the server. Start Server/SocketServer.py.";
  else if (serverError) status = `The server couldn't verify your sign in: ${serverError}`;
  else if (!serverUser || courses === null) status = "Loading your classes…";
  else if (loadError) status = `Your classes couldn't be loaded: ${loadError}`;

  const firstName = serverUser?.NAME?.split(" ")[0];
  const list = courses ?? [];
  const enrolled = new Set(list.flatMap((c) => c.roster));
  const allAssignments = list.flatMap((c) => c.assignments);
  const noClass = <div className="note">You don't have a class yet. Create one under <button className="btn sec sm" onClick={() => go("classes")}>Classes and Students</button></div>;

  /* ---------- Overview: stat cards + roster (like the redesign's Overview) ---------- */
  function Overview() {
    const stats: [string, number][] = [
      ["Classes", list.length],
      ["Students enrolled", enrolled.size],
      ["Assignments", allAssignments.length],
      ["Assignments with a rubric", allAssignments.filter((a) => a.hasRubric).length],
    ];
    return <>
      <Head title="Overview" sub={(firstName ? `Welcome back, ${firstName}. ` : "") + "Your classes at a glance."} />
      <div className="grid">
        {stats.map(([label, n]) => <div className="card" key={label}><div className="muted">{label}</div><div className="stat">{n}</div></div>)}
      </div>
      {!list.length ? noClass : <>
        <div className="card">
          <h3>Classes</h3>
          <div className="scroll"><table>
            <thead><tr><th>Class</th><th>Students</th><th>Assignments</th><th>Files</th></tr></thead>
            <tbody>{list.map((c) => (
              <tr key={c.id} className="click" onClick={() => go("classes")}>
                <td>{c.name}</td>
                <td className="mono">{c.roster.length}</td>
                <td className="mono">{c.assignments.length}</td>
                <td>{c.assignments.some((a) => a.hasFile || a.hasRubric)
                  ? <span className="pill p-ok">uploaded</span> : <span className="pill p-mute">none yet</span>}</td>
              </tr>
            ))}</tbody>
          </table></div>
        </div>
        <div className="card">
          <h3>Roster</h3>
          {enrolled.size ? <div className="scroll"><table>
            <thead><tr><th>Student</th><th>Classes</th></tr></thead>
            <tbody>{[...enrolled].sort((a, b) => nameOf(a).localeCompare(nameOf(b))).map((sid) => (
              <tr key={sid}>
                <td>{nameOf(sid)}</td>
                <td><span className="row" style={{ gap: 4 }}>{list.filter((c) => c.roster.includes(sid)).map((c) =>
                  <span key={c.id} className="pill p-info">{c.name}</span>)}</span></td>
              </tr>
            ))}</tbody>
          </table></div> : <p className="muted">No students enrolled yet. Add them under Classes and Students.</p>}
        </div>
      </>}
    </>;
  }

  /* ---------- Classes and Students: create a class, manage each roster ---------- */
  function Classes() {
    return <>
      <Head title="Classes and Students" sub="Create a class, then choose the students who belong in it. They'll see its assignments on their dashboard." />
      <form className="card" onSubmit={createClass}>
        <h3>Create a class</h3>
        <div className="row">
          <input aria-label="Class name" placeholder="e.g. CSDP 222: Intro to Programming" maxLength={120}
            value={newName} onChange={(e) => setNewName(e.target.value)} style={{ flex: "1 1 260px" }} />
          <button className="btn" type="submit" disabled={!newName.trim() || creating}>{creating ? "Creating…" : "Create class"}</button>
        </div>
        {createMsg && <div className={"note " + (createMsg.ok ? "ok" : "bad")} role="status">{createMsg.text}</div>}
      </form>
      {list.map((c) => {
        const available = students.filter((st) => !c.roster.includes(st.id));
        const ticked = picked[c.id] ?? [];
        const isBusy = busy === c.id;
        return (
          <div className="card" key={c.id}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <h3>{c.name}</h3>
              <span className="muted">{c.roster.length} student{c.roster.length === 1 ? "" : "s"} · {c.assignments.length} assignment{c.assignments.length === 1 ? "" : "s"}</span>
            </div>
            <div className="two" style={{ marginTop: 6 }}>
              <div>
                <h3 style={{ fontSize: ".9rem" }}>Students in this class</h3>
                {c.roster.length ? (
                  <ul className="roster">
                    {c.roster.map((sid) => (
                      <li key={sid}>
                        <span>{nameOf(sid)}</span>
                        <button className="btn sec sm" disabled={isBusy} onClick={() => change(c, [sid], false)}>Remove</button>
                      </li>
                    ))}
                  </ul>
                ) : <p className="muted">No students yet. Add some from the list.</p>}
              </div>
              <div>
                <h3 style={{ fontSize: ".9rem" }}>Add students</h3>
                {available.length ? (
                  <ul className="picker">
                    {available.map((st) => (
                      <li key={st.id}>
                        <label>
                          <input type="checkbox" checked={ticked.includes(st.id)} disabled={isBusy} onChange={() => toggle(c.id, st.id)} />
                          {st.NAME}
                        </label>
                      </li>
                    ))}
                  </ul>
                ) : <p className="muted">{students.length ? "Every student is already in this class." : "No student accounts yet. Students appear here after they sign up and sign in once."}</p>}
                <button className="btn" style={{ marginTop: 8 }} disabled={!ticked.length || isBusy} onClick={() => change(c, ticked, true)}>
                  {isBusy ? "Saving…" : ticked.length ? `Add ${ticked.length} selected` : "Add selected"}
                </button>
              </div>
            </div>
            {notes[c.id] && <div className={"note" + (notes[c.id].startsWith("Some") ? " bad" : " ok")} role="status">{notes[c.id]}</div>}
          </div>
        );
      })}
    </>;
  }

  /* ---------- Assignment Setup: assignments + their files, per class ---------- */
  function Setup() {
    return <>
      <Head title="Assignment Setup" sub="Add assignments with an assignment sheet and rubric (PDF or DOCX). Students can open them, and the AI tutor reads them." />
      {!list.length ? noClass : list.map((c) => (
        <div className="card" key={c.id}>
          <h3>{c.name}</h3>
          {c.assignments.length ? (
            <div className="scroll"><table>
              <thead><tr><th>Assignment</th><th>Assignment file</th><th>Rubric</th><th></th></tr></thead>
              <tbody>{c.assignments.map((a) => (
                <tr key={a.id}>
                  <td>{a.description || `Assignment ${a.id}`}</td>
                  <td>{a.hasFile ? <span className="pill p-ok">uploaded</span> : <span className="pill p-mute">none</span>}</td>
                  <td>{a.hasRubric ? <span className="pill p-ok">uploaded</span> : <span className="pill p-mute">none</span>}</td>
                  <td><FileLinks a={a} /></td>
                </tr>
              ))}</tbody>
            </table></div>
          ) : <p className="muted">No assignments yet.</p>}
          <NewAssignment course={c} onCreated={(a) =>
            setCourses((cs) => cs && cs.map((x) => (x.id === c.id ? { ...x, assignments: [...x.assignments, a] } : x)))} />
        </div>
      ))}
    </>;
  }

  // Called as plain functions (not <Overview />) so typing in a form doesn't remount it and lose focus
  const view = { overview: Overview, classes: Classes, setup: Setup }[tab];

  return (
    <>
      <div className="topbar">
        <div className="brand">Understanding Review</div>
        <div className="who">
          <span>{serverUser?.NAME}</span>
          <span className="pill p-info">teacher</span>
        </div>
      </div>
      <div className="shell">
        <nav className="rail" aria-label="Sections">
          {TABS.map(([id, label]) => <button key={id} className={tab === id ? "on" : ""} onClick={() => go(id)}>{label}</button>)}
        </nav>
        <main className="main">
          {status ? <div className="note">{status}</div> : view()}
        </main>
      </div>
    </>
  );
}
