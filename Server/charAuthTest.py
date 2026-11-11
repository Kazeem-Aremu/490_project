from DataBaseHandler import DataBaseHandler
db = DataBaseHandler()

print("ALL SUBMISSIONS:")
for r in db.supabase.table("Submission").select("*").execute().data:
    print(r, "| Student_id type:", type(r["Student_id"]).__name__)

def check(user_id, sub_id):
    s = db.one(db.getSubmission(sub_id))
    print("\nsubmission:", s)
    a = db.one(db.getAssignment(s["Assign_id"])) if s else None
    print("assignment:", a)
    print("enrollments:", db.getEnrollmentByUser(user_id))

check(20, 2)