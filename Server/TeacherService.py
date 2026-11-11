"""
Teacher actions for the student-portal dashboard: create a class, list the students who can
be added to a class, and add / remove a student from one of the teacher's own classes.

Every call takes the caller's USERID (filled in by WebSocketServer from the signed-in
session, never trusted from the page) and checks that the caller is a teacher and owns
the course before changing anything.
"""
import traceback

from DataBaseHandler import (
    USER, USER_ID, USER_NAME, USER_ROLE,
    ENROLLMENT, ENROLL_COURSE_ID, ENROLL_STUDENT_ID,
    COURSE, COURSE_ID, COURSE_NAME, COURSE_TEACHER_ID,
)

MAX_COURSE_NAME = 120

TEACHER_ROLE = "teacher"
STUDENT_ROLE = "student"


def ok(message):
    return {"Response Code": "200", "MESSAGE": message}


def err(code, text):
    return {"Response Code": code, "MESSAGE": {"ERROR": text}}


class TeacherService:
    def __init__(self, database):
        self.db = database

    def _teacher(self, user_id):
        user = self.db.one(self.db.getUser(user_id))
        if user is None:
            return None, err("404", f"User {user_id} not found")
        if str(user.get(USER_ROLE, "")).lower() != TEACHER_ROLE:
            return None, err("403", "Only teachers can do this")
        return user, None

    def _own_course(self, user_id, course_id):
        """Returns an error response unless user_id is a teacher who owns course_id."""
        _, problem = self._teacher(user_id)
        if problem:
            return problem
        course = self.db.one(self.db.getCoursebyId(course_id))
        if course is None:
            return err("404", f"Course {course_id} not found")
        if course.get(COURSE_TEACHER_ID) != user_id:
            return err("403", "You can only manage your own classes")
        return None

    def create_course(self, user_id, name):
        """A new class owned by the calling teacher."""
        _, problem = self._teacher(user_id)
        if problem:
            return problem
        name = " ".join(str(name or "").split())
        if not name:
            return err("400", "The class needs a name")
        if len(name) > MAX_COURSE_NAME:
            return err("400", f"The class name is too long (max {MAX_COURSE_NAME} characters)")
        try:
            row = self.db.one(self.db.supabase.table(COURSE).insert([{
                COURSE_NAME: name, COURSE_TEACHER_ID: user_id,
            }]).execute().data)
        except Exception as e:
            traceback.print_exc()
            return err("500", f"Could not create the class: {e}")
        if row is None:
            return err("500", "Could not create the class")
        return ok({"COURSEID": row[COURSE_ID], "NAME": row[COURSE_NAME]})

    def list_students(self, user_id):
        """Every USER with the student role: [{id, NAME}, ...]."""
        _, problem = self._teacher(user_id)
        if problem:
            return problem
        rows = (self.db.supabase.table(USER).select(f"{USER_ID},{USER_NAME},{USER_ROLE}")
                .ilike(USER_ROLE, STUDENT_ROLE).order(USER_NAME).execute().data)
        return ok([{USER_ID: r[USER_ID], USER_NAME: r[USER_NAME]} for r in rows])

    def enroll(self, user_id, course_id, student_id):
        problem = self._own_course(user_id, course_id)
        if problem:
            return problem
        student = self.db.one(self.db.getUser(student_id))
        if student is None or str(student.get(USER_ROLE, "")).lower() != STUDENT_ROLE:
            return err("404", f"Student {student_id} not found")
        if any(e[ENROLL_STUDENT_ID] == student_id for e in self.db.getEnrollmentByCourse(course_id)):
            return ok({"COURSEID": course_id, "STUDENTID": student_id, "ALREADY": True})
        try:
            self.db.supabase.table(ENROLLMENT).insert([{
                ENROLL_COURSE_ID: course_id, ENROLL_STUDENT_ID: student_id,
            }]).execute()
        except Exception as e:
            traceback.print_exc()
            return err("500", f"Could not add the student: {e}")
        return ok({"COURSEID": course_id, "STUDENTID": student_id})

    def unenroll(self, user_id, course_id, student_id):
        problem = self._own_course(user_id, course_id)
        if problem:
            return problem
        try:
            (self.db.supabase.table(ENROLLMENT).delete()
             .eq(ENROLL_COURSE_ID, course_id).eq(ENROLL_STUDENT_ID, student_id).execute())
        except Exception as e:
            traceback.print_exc()
            return err("500", f"Could not remove the student: {e}")
        return ok({"COURSEID": course_id, "STUDENTID": student_id})
