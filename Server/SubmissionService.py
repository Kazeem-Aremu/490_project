"""
UploadSubmission (Interface Description) for the AI chat box.

The browser sends the file text it already has open; the server stores it in a private
Supabase Storage bucket with the service key and saves a Submission row whose
Submission_link points at that object. AIService then reads the file through the same
link when the tutor conversation starts (see make_submission_fetcher's auth headers).
Doing the upload here means no Storage RLS policies are needed for students.
"""
import re
import threading
import time
import traceback

from DataBaseHandler import ASSIGNMENT_COURSE_ID, ENROLL_COURSE_ID, SUB_ID
from AIService import MAX_FILE_BYTES

BUCKET = "submissions"


def ok(message):
    return {"Response Code": "200", "MESSAGE": message}


def err(code, text):
    return {"Response Code": code, "MESSAGE": {"ERROR": text}}


def safe_name(name):
    return re.sub(r"[^\w.\-]+", "_", str(name or ""))[:120] or "file"


class SubmissionService:
    def __init__(self, database, supabase_url):
        self.db = database
        self.supabase_url = (supabase_url or "").rstrip("/")
        self._bucket_ready = False
        self._bucket_lock = threading.Lock()

    def _ensure_bucket(self):
        with self._bucket_lock:
            if self._bucket_ready:
                return
            storage = self.db.supabase.storage
            try:
                storage.get_bucket(BUCKET)
            except Exception:
                storage.create_bucket(BUCKET, options={"public": False})
                print(f"Created private storage bucket '{BUCKET}'")
            self._bucket_ready = True

    def create_submission(self, user_id, assignment_id, name, code):
        if not isinstance(code, str) or not code.strip():
            return err("400", "The file is empty")
        data = code.encode("utf-8")
        if len(data) > MAX_FILE_BYTES:
            return err("400", f"The file is too large (max {MAX_FILE_BYTES // 1000} KB)")

        db = self.db
        assignment = db.one(db.getAssignment(assignment_id))
        if assignment is None:
            return err("404", f"Assignment {assignment_id} not found")
        enrollments = db.getEnrollmentByUser(user_id)
        if not any(e[ENROLL_COURSE_ID] == assignment[ASSIGNMENT_COURSE_ID] for e in enrollments):
            return err("403", "Student is not enrolled in this course")

        path = f"{user_id}/{assignment_id}/{int(time.time() * 1000)}-{safe_name(name)}"
        try:
            self._ensure_bucket()
            db.supabase.storage.from_(BUCKET).upload(
                path, data, {"content-type": "text/plain; charset=utf-8"})
        except Exception as e:
            traceback.print_exc()
            return err("502", f"Could not store the file: {e}")

        link = f"{self.supabase_url}/storage/v1/object/authenticated/{BUCKET}/{path}"
        row = db.one(db.createSubmission(assignment_id, user_id, link))
        if row is None:
            return err("500", "Could not save the submission")
        return ok({"SUBMISSIONID": row[SUB_ID], "ASSIGNMENTID": assignment_id, "NAME": name})
