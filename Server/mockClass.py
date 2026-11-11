"""
Create one mock class with one mock assignment so the portal has something to show.

    py mockClass.py teacher@umes.edu     create the mock class owned by that portal teacher
                                         (or hand an existing mock class over to them)
    py mockClass.py                      create it with a placeholder "Mock Teacher" owner
    py mockClass.py --clean              delete everything this script created

The teacher must have signed up on the portal as a Teacher and signed in once (that
creates their USER row). Students are NOT added here: the teacher adds them from the
portal dashboard ("Add students"). IDs are saved to mock_ids.json, like seed_ids.json.
"""
import json
import os
import sys
import traceback

from DataBaseHandler import (
    DataBaseHandler,
    USER, USER_ID, USER_NAME, USER_ROLE,
    COURSE, COURSE_ID, COURSE_NAME, COURSE_TEACHER_ID,
    ENROLLMENT, ENROLL_COURSE_ID,
    ASSIGNMENT, ASSIGNMENT_ID, ASSIGNMENT_COURSE_ID, ASSIGNMENT_TEACHER_ID,
    ASSIGNMENT_RESOURCE_LINK, ASSIGNMENT_RUBRIK, ASSIGNMENT_DESCRIPTION,
    SUBMISSION, SUB_ID, SUB_ASSIGN_ID, AI_CONVOS, AI_CONVO_ID,
)
from AuthService import USER_ROW_KEY
from linkAuthUser import find_auth_user

IDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_ids.json")

CLASS_NAME = "Mock Class: Intro to Programming"
ASSIGNMENT_TEXT = ("Mock Assignment 1: Sum of Even Numbers. Write a Python function sum_even(nums) "
                   "that returns the sum of the even numbers in a list. It should return 0 for an empty list.")


def load_ids():
    if not os.path.exists(IDS_FILE):
        return None
    with open(IDS_FILE) as f:
        return json.load(f)


def save_ids(ids):
    with open(IDS_FILE, "w") as f:
        json.dump(ids, f, indent=2)


def teacher_row_for(db, email):
    """The USER row of a portal teacher account, or None (with a message printed)."""
    auth_user = find_auth_user(db, email)
    if auth_user is None:
        print(f"No portal account with email {email}. Sign up on the portal as a Teacher first.")
        return None
    row_id = (auth_user.app_metadata or {}).get(USER_ROW_KEY)
    row = db.one(db.getUser(int(row_id))) if row_id is not None else None
    if row is None:
        print(f"{email} has not signed in yet. Sign in once on the portal, then run this again.")
        return None
    if str(row.get(USER_ROLE, "")).lower() != "teacher":
        print(f"{email} is a {row.get(USER_ROLE)!r} account, not a teacher.")
        return None
    return row


def create(email):
    db = DataBaseHandler()
    ids = load_ids()

    if email:
        teacher = teacher_row_for(db, email)
        if teacher is None:
            return 1
        teacher_id = teacher[USER_ID]
    else:
        teacher = None

    try:
        if ids is not None:
            # The mock class exists already: just hand it to this teacher
            if teacher is None:
                print(f"The mock class already exists (course {ids['course']}). "
                      "Give a teacher email to hand it over, or run --clean first.")
                return 1
            db.supabase.table(COURSE).update({COURSE_TEACHER_ID: teacher_id}).eq(COURSE_ID, ids["course"]).execute()
            db.supabase.table(ASSIGNMENT).update({ASSIGNMENT_TEACHER_ID: teacher_id}).eq(ASSIGNMENT_ID, ids["assignment"]).execute()
            print(f"Mock class {ids['course']} now belongs to {teacher[USER_NAME]} (USER {teacher_id}).")
            return 0

        ids = {}
        if teacher is None:
            row = db.supabase.table(USER).insert([{USER_NAME: "Mock Teacher", USER_ROLE: "teacher"}]).execute().data[0]
            teacher_id = ids["placeholder_teacher"] = row[USER_ID]
            save_ids(ids)
            print(f"teacher     placeholder USER {teacher_id}")
        else:
            print(f"teacher     {teacher[USER_NAME]} (USER {teacher_id})")

        course = db.supabase.table(COURSE).insert([{COURSE_NAME: CLASS_NAME, COURSE_TEACHER_ID: teacher_id}]).execute().data[0]
        ids["course"] = course[COURSE_ID]
        save_ids(ids)
        print(f"class       {ids['course']}  {CLASS_NAME}")

        assignment = db.supabase.table(ASSIGNMENT).insert([{
            ASSIGNMENT_COURSE_ID: ids["course"],
            ASSIGNMENT_TEACHER_ID: teacher_id,
            ASSIGNMENT_RESOURCE_LINK: "https://example.com/mock/sum_even",
            ASSIGNMENT_RUBRIK: "https://example.com/mock/sum_even_rubric",
            ASSIGNMENT_DESCRIPTION: ASSIGNMENT_TEXT,
        }]).execute().data[0]
        ids["assignment"] = assignment[ASSIGNMENT_ID]
        save_ids(ids)
        print(f"assignment  {ids['assignment']}")
    except Exception as e:
        traceback.print_exc()
        print(f"\nStopped: {e}\nWhat was created so far is in mock_ids.json; run --clean to remove it.")
        return 1

    print("\nDone. Sign in as the teacher and use \"Add students\" on the dashboard.")
    return 0


def clean():
    ids = load_ids()
    if ids is None:
        print("No mock_ids.json - nothing to clean.")
        return 0
    db = DataBaseHandler()
    try:
        if "assignment" in ids:
            subs = db.supabase.table(SUBMISSION).select(SUB_ID).eq(SUB_ASSIGN_ID, ids["assignment"]).execute().data
            sub_ids = [s[SUB_ID] for s in subs]
            if sub_ids:
                db.supabase.table(AI_CONVOS).delete().in_(AI_CONVO_ID, sub_ids).execute()
                db.supabase.table(SUBMISSION).delete().in_(SUB_ID, sub_ids).execute()
                print(f"deleted {len(sub_ids)} submission(s) and their AI conversations")
            db.supabase.table(ASSIGNMENT).delete().eq(ASSIGNMENT_ID, ids["assignment"]).execute()
            print(f"deleted assignment {ids['assignment']}")
        if "course" in ids:
            db.supabase.table(ENROLLMENT).delete().eq(ENROLL_COURSE_ID, ids["course"]).execute()
            db.supabase.table(COURSE).delete().eq(COURSE_ID, ids["course"]).execute()
            print(f"deleted class {ids['course']} and its enrollments")
        if "placeholder_teacher" in ids:
            db.supabase.table(USER).delete().eq(USER_ID, ids["placeholder_teacher"]).execute()
            print(f"deleted placeholder teacher {ids['placeholder_teacher']}")
    except Exception as e:
        traceback.print_exc()
        print(f"\nClean stopped: {e}. mock_ids.json was kept; fix the cause and run --clean again.")
        return 1
    os.remove(IDS_FILE)
    print("Clean. mock_ids.json removed.")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--clean"]:
        sys.exit(clean())
    if len(args) <= 1 and not (args and args[0].startswith("-")):
        sys.exit(create(args[0] if args else None))
    print(__doc__)
    sys.exit(1)
