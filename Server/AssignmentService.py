"""
Assignment files (the assignment sheet and its rubric) for the student-portal.

A teacher creates an assignment from the dashboard with a description and, optionally, a PDF
or DOCX for the assignment and one for the rubric. The browser sends each file base64 encoded;
the server stores it in the private Supabase Storage bucket "assignments" with the service key
(no Storage RLS policies needed, same as SubmissionService) and saves the links in the
ASSIGNMENT row's resource_link / rubrik_link columns.

At upload the text is pulled out of each file (pypdf / python-docx) and stored next to it as
"<path>.txt". The AI tutor reads those texts (assignment_texts) so it can review a student's
work against the real assignment and rubric. Students and the owning teacher can open the
original files through short-lived signed links (file_link).
"""
import base64
import binascii
import io
import threading
import time
import traceback

from DataBaseHandler import (
    ASSIGNMENT, ASSIGNMENT_ID, ASSIGNMENT_COURSE_ID, ASSIGNMENT_TEACHER_ID,
    ASSIGNMENT_RESOURCE_LINK, ASSIGNMENT_RUBRIK, ASSIGNMENT_DESCRIPTION,
    COURSE_TEACHER_ID, ENROLL_COURSE_ID,
)
from SubmissionService import safe_name

BUCKET = "assignments"
MAX_FILE_BYTES = 10 * 1024 * 1024       # per file, after base64 decoding
MAX_DESCRIPTION = 4000
MAX_TEXT_CHARS = 15_000                 # per file, what the AI tutor is given
SIGNED_LINK_SECONDS = 300
KINDS = {"assignment": ASSIGNMENT_RESOURCE_LINK, "rubric": ASSIGNMENT_RUBRIK}
CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def ok(message):
    return {"Response Code": "200", "MESSAGE": message}


def err(code, text):
    return {"Response Code": code, "MESSAGE": {"ERROR": text}}


def extension(name):
    name = str(name or "").lower()
    return next((ext for ext in CONTENT_TYPES if name.endswith(ext)), None)


def extract_text(data, ext):
    """Plain text of a PDF or DOCX, or None if nothing could be read (e.g. a scanned PDF)."""
    try:
        if ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
        else:
            from docx import Document
            doc = Document(io.BytesIO(data))
            parts = [p.text for p in doc.paragraphs]
            for table in doc.tables:
                for row in table.rows:
                    parts.append(" | ".join(cell.text.strip() for cell in row.cells))
            text = "\n".join(parts)
    except Exception:
        traceback.print_exc()
        return None
    text = text.strip()
    return text or None


class AssignmentService:
    def __init__(self, database, supabase_url, teachers):
        self.db = database
        self.teachers = teachers  # TeacherService, for the "is this the teacher's course" check
        self.supabase_url = (supabase_url or "").rstrip("/")
        self.link_prefix = f"{self.supabase_url}/storage/v1/object/authenticated/{BUCKET}/"
        self._bucket_ready = False
        self._bucket_lock = threading.Lock()
        self._text_cache = {}  # storage path -> extracted text (or None)

    def _storage(self):
        with self._bucket_lock:
            storage = self.db.supabase.storage
            if not self._bucket_ready:
                try:
                    storage.get_bucket(BUCKET)
                except Exception:
                    storage.create_bucket(BUCKET, options={"public": False})
                    print(f"Created private storage bucket '{BUCKET}'")
                self._bucket_ready = True
            return storage.from_(BUCKET)

    def _path_of(self, link):
        """Storage path for a link this service made; None for anything else (e.g. example.com)."""
        link = str(link or "")
        return link[len(self.link_prefix):] if self.supabase_url and link.startswith(self.link_prefix) else None

    # ------------------------------------------------------------------ create
    def create_assignment(self, user_id, course_id, description, files):
        problem = self.teachers._own_course(user_id, course_id)
        if problem:
            return problem
        description = str(description or "").strip()
        if not description:
            return err("400", "The assignment needs a description")
        if len(description) > MAX_DESCRIPTION:
            return err("400", f"The description is too long (max {MAX_DESCRIPTION} characters)")
        if files is not None and not isinstance(files, dict):
            return err("400", "FILES must be an object")

        # Check every file before storing any of them
        uploads = []
        for kind, f in (files or {}).items():
            if kind not in KINDS or f is None:
                continue
            if not isinstance(f, dict):
                return err("400", f"FILES.{kind} must be an object with NAME and DATA")
            name = str(f.get("NAME") or "")
            ext = extension(name)
            if ext is None:
                return err("400", f"{name or 'The ' + kind + ' file'} must be a PDF or DOCX")
            try:
                data = base64.b64decode(str(f.get("DATA") or ""), validate=True)
            except (binascii.Error, ValueError):
                return err("400", f"{name} could not be decoded")
            if not data:
                return err("400", f"{name} is empty")
            if len(data) > MAX_FILE_BYTES:
                return err("400", f"{name} is larger than {MAX_FILE_BYTES // (1024 * 1024)} MB")
            uploads.append((kind, name, ext, data))

        links, stored = {}, []
        try:
            bucket = self._storage() if uploads else None
            for kind, name, ext, data in uploads:
                path = f"{course_id}/{int(time.time() * 1000)}-{kind}-{safe_name(name)}"
                bucket.upload(path, data, {"content-type": CONTENT_TYPES[ext]})
                stored.append(path)
                text = extract_text(data, ext)
                if text is not None:
                    bucket.upload(path + ".txt", text.encode("utf-8"), {"content-type": "text/plain; charset=utf-8"})
                    stored.append(path + ".txt")
                self._text_cache[path] = text
                links[KINDS[kind]] = self.link_prefix + path

            row = self.db.one(self.db.supabase.table(ASSIGNMENT).insert([{
                ASSIGNMENT_COURSE_ID: course_id,
                ASSIGNMENT_TEACHER_ID: user_id,
                ASSIGNMENT_DESCRIPTION: description,
                ## "" rather than NULL when there is no file, in case the columns are NOT NULL
                ASSIGNMENT_RESOURCE_LINK: links.get(ASSIGNMENT_RESOURCE_LINK, ""),
                ASSIGNMENT_RUBRIK: links.get(ASSIGNMENT_RUBRIK, ""),
            }]).execute().data)
            if row is None:
                raise RuntimeError("no row returned")
        except Exception as e:
            traceback.print_exc()
            if stored:  # don't leave orphaned files behind
                try:
                    self._storage().remove(stored)
                except Exception:
                    traceback.print_exc()
            return err("502", f"Could not save the assignment: {e}")

        return ok({
            "ASSIGNMENTID": row[ASSIGNMENT_ID],
            "COURSEID": course_id,
            "DESCRIPTION": description,
            "HASFILE": ASSIGNMENT_RESOURCE_LINK in links,
            "HASRUBRIC": ASSIGNMENT_RUBRIK in links,
            # files whose text couldn't be read (e.g. scanned PDFs): the tutor won't see them
            "NOTEXT": [kind for kind, _, _, _ in uploads if self._text_cache.get(self._path_of(links[KINDS[kind]])) is None],
        })

    # ------------------------------------------------------------- view a file
    def file_link(self, user_id, assignment_id, kind):
        if kind not in KINDS:
            return err("400", "KIND must be 'assignment' or 'rubric'")
        db = self.db
        assignment = db.one(db.getAssignment(assignment_id))
        if assignment is None:
            return err("404", f"Assignment {assignment_id} not found")
        course_id = assignment[ASSIGNMENT_COURSE_ID]
        course = db.one(db.getCoursebyId(course_id))
        is_teacher = course is not None and course.get(COURSE_TEACHER_ID) == user_id
        enrolled = any(e[ENROLL_COURSE_ID] == course_id for e in db.getEnrollmentByUser(user_id))
        if not (is_teacher or enrolled):
            return err("403", "You are not in this class")
        path = self._path_of(assignment.get(KINDS[kind]))
        if path is None:
            return err("404", f"This assignment has no {kind} file")
        try:
            signed = self._storage().create_signed_url(path, SIGNED_LINK_SECONDS)
        except Exception as e:
            traceback.print_exc()
            return err("502", f"Could not open the file: {e}")
        url = (signed.get("signedURL") or signed.get("signedUrl")) if isinstance(signed, dict) else None
        if not url:
            return err("502", "Could not open the file")
        if url.startswith("/"):  # some client versions return a path relative to Storage
            url = f"{self.supabase_url}/storage/v1{url}"
        return ok({"URL": url, "NAME": path.rsplit("/", 1)[-1].split("-", 2)[-1]})

    # -------------------------------------------------------- text for the AI
    def _text(self, link):
        path = self._path_of(link)
        if path is None:
            return None
        if path not in self._text_cache:
            try:
                raw = self._storage().download(path + ".txt")
                self._text_cache[path] = raw.decode("utf-8", errors="replace")
            except Exception as e:
                # no .txt (nothing readable in the file) or Storage unreachable; remembered
                # until the server restarts so every chat message doesn't retry it
                print(f"No assignment text for {path}: {e}")
                self._text_cache[path] = None
        text = self._text_cache[path]
        if text is not None and len(text) > MAX_TEXT_CHARS:
            text = text[:MAX_TEXT_CHARS] + "\n..[truncated]"
        return text

    def assignment_texts(self, assignment):
        """(assignment file text, rubric text) for the AI tutor; either may be None."""
        return self._text(assignment.get(ASSIGNMENT_RESOURCE_LINK)), self._text(assignment.get(ASSIGNMENT_RUBRIK))
