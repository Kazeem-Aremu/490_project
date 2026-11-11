import { useState } from "react";
import { useWebSocket } from "../contexts/ClientContextProvider";
import { type Assignment, type FileKind, openAssignmentFile } from "../api/assignments";

// "View assignment" / "View rubric" buttons for an assignment (teacher and student dashboards)
export default function FileLinks({ a }: { a: Assignment }) {
  const { request } = useWebSocket();
  const [error, setError] = useState("");
  if (!a.hasFile && !a.hasRubric) return null;
  const view = (kind: FileKind) => { setError(""); openAssignmentFile(request, a.id, kind).catch((e: Error) => setError(e.message)); };
  return (
    <span className="row" style={{ gap: 6 }}>
      {a.hasFile && <button type="button" className="btn sec sm" onClick={() => view("assignment")}>View assignment</button>}
      {a.hasRubric && <button type="button" className="btn sec sm" onClick={() => view("rubric")}>View rubric</button>}
      {error && <span className="muted" role="alert">{error}</span>}
    </span>
  );
}
