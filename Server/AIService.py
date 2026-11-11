import json
import threading
import traceback
import urllib.request
from urllib.parse import urlparse
from DataBaseHandler import DataBaseHandler
from AgentInterface import Teacher, build_kickoff, build_system_prompt, load_history, visible

MAX_USER_CHARS = 4000
MAX_FILE_CHARS = 20000
MAX_FILE_BYTES = 200_000
MAX_TOKENS_PER_CONVO = 50_000

def ok(message):
    return {"Response Code":"200", "MESSAGE":message}

def err(code, text):
    return {"Response Code": code, "MESSAGE":{"ERROR":text}}

def make_submission_fetcher(allowed_host, headers=None):
    ##returns fetch link/file text or nothing if it cant be read.
    ##headers (e.g. the Supabase key for private Storage files) are only ever sent to allowed_host
    def fetch (link):
        parsed = urlparse(link or "")
        if parsed.scheme != "https" or not allowed_host or parsed.hostname != allowed_host:
            return None

        try:
            request = urllib.request.Request(link, headers=headers or {})
            with urllib.request.urlopen(request, timeout=10) as resp:
                raw = resp.read(MAX_FILE_BYTES + 1)
        except Exception:
            traceback.print_exc()
            return None
        return raw[:MAX_FILE_BYTES].decode("utf-8", errors="replace")
    return fetch


class AIService:
    def __init__(self,database,fetch_text = None, assignment_texts = None):
        self.db:DataBaseHandler = database
        self.fetch_text = fetch_text
        ## (assignment) -> (assignment sheet text, rubric text); AssignmentService.assignment_texts
        self.assignment_texts = assignment_texts
        self._locks = {}
        self._locks_guard = threading.Lock()

    def _lock_for(self, key):
        with self._locks_guard:
            return self._locks.setdefault(key, threading.Lock())

    def _authorize(self, user_id, submission_id):
        db = self.db
        submission = db.one(db.getSubmission(submission_id))

        if submission is None:
            return None, None, err("404", f"Submission {submission_id} not found")
        if int(submission["Student_id"]) != user_id:
            return None, None, err("403", "this submission belongs to a different student ")
        assignment = db.one(db.getAssignment(submission["Assign_id"]))
        if assignment is None:
            return None, None, err("404", "Assignment for this submission not found")
        enrollments = db.getEnrollmentByUser(user_id)
        if not any(e["Course_id"] == assignment["Course_id"] for e in enrollments):
            return None, None, err("403", "Student is not enrolled in this course")

        return submission, assignment, None

    def _system_prompt(self, assignment):
        texts = (None, None)
        if self.assignment_texts is not None:
            try:
                texts = self.assignment_texts(assignment)
            except Exception:
                traceback.print_exc()
        return build_system_prompt(assignment, *texts)

    def _read_submission(self, submission):
        if self.fetch_text is None:
            return None
        try:
            text = self.fetch_text(submission.get("Submission_link"))
        except Exception:
            traceback.print_exc()
            return None

        if text is not None and len(text) > MAX_FILE_CHARS:
            text = text[:MAX_FILE_CHARS] + "\n..[file truncated]"

        return text


    def start_conversation(self, user_id, submission_id):
        submission, assignment, problem = self._authorize(user_id, submission_id)
        if problem:
            return problem

        with self._lock_for(submission_id):
            existing = self.db.one(self.db.getAiConversation(submission_id))
            if existing is not None:
                history = load_history(existing.get("Responses"))
                return ok({"CONVOID":submission_id, "RESUMED": True, "MESSAGES":visible(history)})

            kickoff = {"role":"user", "hidden":True, "content":build_kickoff(self._read_submission(submission))
                       }
            teacher = Teacher(self._system_prompt(assignment), [kickoff])
            try:
                teacher.respond()
            except Exception:
                traceback.print_exc()
                return err("502", "The AI service is unavailable right now. Please try again.")

            self.db.createAIConversation(submission_id, json.dumps(teacher.history), teacher.tokens_used)
            return ok({"CONVOID":submission_id, "RESUMED":False, "MESSAGES":visible(teacher.history)})


    def send_message(self, user_id, convo_id, text):
        text = text.strip() if isinstance(text,str) else ""
        if not text:
            return err("400", "Message is empty")
        if len(text) > MAX_USER_CHARS:
            return err("400", f"Message is too long (max {MAX_USER_CHARS} characters)")

        _, assignment, problem = self._authorize(user_id, convo_id)
        if problem:
            return problem

        with self._lock_for(convo_id):
            convo = self.db.one(self.db.getAiConversation(convo_id))
            if convo is None:
                return err("404", "No conversation yet. Start one first.")
            used = convo.get("Tokens_used") or 0
            if used >= MAX_TOKENS_PER_CONVO:
                return err("429", "This conversation has reached its limit")


            teacher = Teacher(self._system_prompt(assignment), load_history(convo.get("Responses")))

            try:
                reply = teacher.say(text)

            except Exception:
                traceback.print_exc()
                return err("502", "The Ai service is unavailable right now. Please try again.")

            self.db.updateAIConversation(convo_id, json.dumps(teacher.history), used + teacher.tokens_used)

            return ok({"CONVOID":convo_id, "REPLY":reply})