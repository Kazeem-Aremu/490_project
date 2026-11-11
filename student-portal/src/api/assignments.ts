import type { useWebSocket } from "../contexts/ClientContextProvider";

// An assignment from a course. hasFile / hasRubric: the teacher uploaded a PDF or DOCX for it.
export type Assignment = { id: number; courseName: string; description: string; hasFile: boolean; hasRubric: boolean };
export type FileKind = "assignment" | "rubric";

type Request = ReturnType<typeof useWebSocket>["request"];
type Row = Record<string, unknown>;

// Only files stored by the server (AssignmentService) can be opened; older rows may hold placeholder links
const stored = (link: unknown) => typeof link === "string" && link.includes("/storage/v1/object/authenticated/assignments/");

export function toAssignment(a: Row, courseName: string): Assignment {
  return {
    id: Number(a.id),
    courseName,
    description: String(a.Description ?? "").trim(),
    hasFile: stored(a.resource_link),
    hasRubric: stored(a.rubrik_link),
  };
}

// Short label for dropdowns: "Course — first 60 characters of the description"
export function assignmentLabel(a: Assignment) {
  const d = a.description;
  return `${a.courseName} — ${d ? d.slice(0, 60) + (d.length > 60 ? "…" : "") : "Assignment " + a.id}`;
}

// Enrollement -> getCourseInfo -> AssignmentInfo (the server's existing GET routes)
export async function loadAssignments(request: Request, userId: number): Promise<Assignment[]> {
  const get = (INFO: string, BY: string, PARAMS: Row) => request<Row[]>({ MESSAGE: { METHOD: "GET", INFO, BY, PARAMS } });
  const enrollments = await get("Enrollement", "UserID", { userID: userId });
  const found: Assignment[] = [];
  for (const e of enrollments) {
    const courseId = e.Course_id;
    const course = await get("getCourseInfo", "CourseID", { CourseID: courseId }).catch(() => []);
    const courseName = String(course[0]?.Course_Name ?? `Course ${courseId}`);
    const rows = await get("AssignmentInfo", "CourseID", { COURSEID: courseId });
    for (const a of rows) found.push(toAssignment(a, courseName));
  }
  return found;
}

// Opens the assignment sheet or rubric in a new tab through a short-lived signed link.
// The tab is opened before the request so pop-up blockers allow it.
export async function openAssignmentFile(request: Request, assignmentId: number, kind: FileKind) {
  const tab = window.open("", "_blank");
  try {
    const res = await request<{ URL: string }>({ MESSAGE: { METHOD: "POST", INFO: "assignmentFile",
      PARAMS: { ASSIGNMENTID: assignmentId, KIND: kind } } });
    if (tab) { tab.opener = null; tab.location.href = res.URL; }
    else window.location.href = res.URL;
  } catch (e) {
    tab?.close();
    throw e;
  }
}

// A file as base64 (no "data:...;base64," prefix), for createAssignment
export function fileToBase64(f: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result).split(",", 2)[1] ?? "");
    r.onerror = () => reject(new Error(`Couldn't read ${f.name}`));
    r.readAsDataURL(f);
  });
}
