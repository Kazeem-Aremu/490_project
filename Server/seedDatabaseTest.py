"""
Create (and remove) a small set of TEST rows in Supabase so the getters and the
server tests have real data to read.

    python seed_database.py            insert test rows, save their IDs to seed_ids.json
    python seed_database.py --check    call every DataBaseHandler getter directly (no server)
                                       and print the full error if one fails
    python seed_database.py --clean    delete exactly the rows this script inserted

test_server.py reads seed_ids.json automatically, so after seeding, its "valid" tests
require REAL data back (not just "no error").

Rows are inserted in foreign-key order (USER -> COURSE -> ENROLLMENT/ASSIGNMENT ->
Submission -> AI_Conversations) and deleted in the reverse order.
Uses the secret key from your .env, which bypasses Row Level Security.
"""
import json
import os
import sys
import traceback

from DataBaseHandler import (
    DataBaseHandler,
    USER, USER_ID, USER_NAME, USER_ROLE,
    COURSE, COURSE_ID, COURSE_NAME, COURSE_TEACHER_ID,
    ENROLLMENT, ENROLL_COURSE_ID, ENROLL_STUDENT_ID,
    ASSIGNMENT, ASSIGNMENT_ID, ASSIGNMENT_COURSE_ID, ASSIGNMENT_TEACHER_ID,
    ASSIGNMENT_RESOURCE_LINK, ASSIGNMENT_RUBRIK, ASSIGNMENT_DESCRIPTION,
    SUBMISSION, SUB_ID, SUB_ASSIGN_ID, SUB_STUDENT_ID, SUB_SUBMISSION_LINK,
    AI_CONVOS, AI_CONVO_ID, AI_CONVO_SUBMISSION, AI_CONVO_RESPONSES,
    AI_CONVO_TOKENS_USED, AI_CONVO_EVAL_SCORE, AI_CONVO_AI_SCORE,
)

IDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_ids.json")

def save_ids(ids):
    with open(IDS_FILE, "w") as f:
        json.dump(ids, f, indent=2)


def load_ids():
    if not os.path.exists(IDS_FILE):
        return None
    with open(IDS_FILE) as f:
        return json.load(f)


def insert(db, table, rows):
    """Insert rows, return the saved rows (with their database-generated ids)."""
    return db.supabase.table(table).insert(rows).execute().data


# ------------------------------------------------------------------ seed
def seed():
    if load_ids() is not None:
        print("seed_ids.json already exists. Run with --clean first to avoid duplicates.")
        return 1

    db = DataBaseHandler()
    ids = {}
    try:
        users = insert(db, USER, [
            {USER_NAME: "TEST Teacher One", USER_ROLE: "teacher"},
            {USER_NAME: "TEST Student A",   USER_ROLE: "student"},
            {USER_NAME: "TEST Student B",   USER_ROLE: "student"},
        ])
        ids["teacher"], ids["student_a"], ids["student_b"] = [u[USER_ID] for u in users]
        save_ids(ids)
        print(f"users          teacher={ids['teacher']} student_a={ids['student_a']} student_b={ids['student_b']}")

        course = insert(db, COURSE, [
            {COURSE_NAME: "TEST Intro to Programming", COURSE_TEACHER_ID: ids["teacher"]},
        ])[0]
        ids["course"] = course[COURSE_ID]
        save_ids(ids)
        print(f"course         {ids['course']}")

        insert(db, ENROLLMENT, [
            {ENROLL_COURSE_ID: ids["course"], ENROLL_STUDENT_ID: ids["student_a"]},
            {ENROLL_COURSE_ID: ids["course"], ENROLL_STUDENT_ID: ids["student_b"]},
        ])
        ids["enrolled"] = True
        save_ids(ids)
        print("enrollments    2 rows (student_a, student_b in the course)")

        assignment = insert(db, ASSIGNMENT, [{
            ASSIGNMENT_COURSE_ID: ids["course"],
            ASSIGNMENT_TEACHER_ID: ids["teacher"],
            ASSIGNMENT_RESOURCE_LINK: "https://example.com/resources/hw1",
            ASSIGNMENT_RUBRIK: "https://example.com/rubrics/hw1",
            ASSIGNMENT_DESCRIPTION: "TEST Homework 1: write a hello-world program",
        }])[0]
        ids["assignment"] = assignment[ASSIGNMENT_ID]
        save_ids(ids)
        print(f"assignment     {ids['assignment']}")

        submission = insert(db, SUBMISSION, [{
            SUB_ASSIGN_ID: ids["assignment"],
            SUB_STUDENT_ID: ids["student_a"],
            SUB_SUBMISSION_LINK: "https://example.com/submissions/student_a_hw1",
        }])[0]
        ids["submission"] = submission[SUB_ID]
        save_ids(ids)
        print(f"submission     {ids['submission']}")

        convo = insert(db, AI_CONVOS, [{
            AI_CONVO_ID: ids["submission"],
            AI_CONVO_RESPONSES: "TEST AI feedback: good structure, add comments.",
            AI_CONVO_TOKENS_USED: 123,
            AI_CONVO_EVAL_SCORE: 8,
            AI_CONVO_AI_SCORE: 9,
        }])[0]
        ids["ai_conversation"] = convo[AI_CONVO_ID]
        save_ids(ids)
        print(f"ai_conversation {ids['ai_conversation']}")

    except Exception as e:
        traceback.print_exc()
        print(f"\nSeeding stopped: {e}")
        print("What was inserted so far is saved in seed_ids.json. Fix the problem, then run --clean and try again.")
        print("Common causes: a column name that doesn't match the table, a NOT NULL column "
              "I didn't fill, a CHECK constraint on ROLE, or an identity column set to GENERATED ALWAYS.")
        return 1

    print(f"\nDone. IDs saved to {IDS_FILE}")
    print("Next: python seed_database.py --check   then   python testClient.py")
    return 0


# ----------------------------------------------------------------- clean
def clean():
    ids = load_ids()
    if ids is None:
        print("No seed_ids.json - nothing to clean.")
        return 0
    db = DataBaseHandler()

    # reverse foreign-key order
    steps = []
    if "ai_conversation" in ids:
        steps.append((AI_CONVOS, AI_CONVO_ID, ids["ai_conversation"]))
    if "submission" in ids:
        steps.append((SUBMISSION, SUB_ID, ids["submission"]))
    if ids.get("enrolled"):
        steps.append((ENROLLMENT, ENROLL_COURSE_ID, ids["course"]))
    if "assignment" in ids:
        steps.append((ASSIGNMENT, ASSIGNMENT_ID, ids["assignment"]))
    if "course" in ids:
        steps.append((COURSE, COURSE_ID, ids["course"]))
    for key in ("student_a", "student_b", "teacher"):
        if key in ids:
            steps.append((USER, USER_ID, ids[key]))

    failed = False
    for table, column, value in steps:
        try:
            db.supabase.table(table).delete().eq(column, value).execute()
            print(f"deleted from {table} where {column} = {value}")
        except Exception as e:
            failed = True
            print(f"FAILED deleting from {table} where {column} = {value}: {e}")

    if failed:
        print("\nSome rows were not deleted, so seed_ids.json was kept. Fix the cause and run --clean again.")
        return 1
    os.remove(IDS_FILE)
    print("\nClean. seed_ids.json removed.")
    return 0


# ----------------------------------------------------------------- check
def check():
    """Call every getter directly. Prints the full traceback of any failure."""
    ids = load_ids()
    if ids is None:
        print("No seed_ids.json - run the seed first.")
        return 1
    db = DataBaseHandler()
    calls = [
        ("getUser",               ids.get("student_a")),
        ("getEnrollmentByUser",   ids.get("student_a")),
        ("getEnrollmentByCourse", ids.get("course")),
        ("getCourseByTeacher",    ids.get("teacher")),
        ("getCoursebyId",         ids.get("course")),
        ("getAssignmentByCourse", ids.get("course")),
        ("getAssignment",         ids.get("assignment")),
        ("getAiConversation",     ids.get("ai_conversation")),
    ]
    bad = 0
    for name, arg in calls:
        try:
            rows = getattr(db, name)(arg)
            status = f"OK    {len(rows)} row(s)" if rows else "EMPTY 0 rows (expected data!)"
            if not rows:
                bad += 1
            print(f"{name:24} ({arg}) -> {status}")
        except Exception:
            bad += 1
            print(f"{name:24} ({arg}) -> ERROR")
            traceback.print_exc()
    print(f"\n{len(calls) - bad}/{len(calls)} getters returned data")
    return 1 if bad else 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "--clean":
        sys.exit(clean())
    elif arg == "--check":
        sys.exit(check())
    elif arg in ("", "--seed"):
        sys.exit(seed())
    else:
        print(__doc__)
        sys.exit(2)