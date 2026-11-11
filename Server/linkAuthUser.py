"""
Link a student-portal login (Supabase Auth account) to an existing USER row.

New sign ups get their own USER row automatically on first login (see AuthService.py).
Use this when you want a login to act as a row that already exists, e.g. the seeded
"TEST Student A" who is enrolled in a course and has an assignment:

    py linkAuthUser.py someone@umes.edu 20
    py linkAuthUser.py someone@umes.edu            # show the current link
"""
import sys

from DataBaseHandler import DataBaseHandler
from AuthService import USER_ROW_KEY


def find_auth_user(db, email):
    page = 1
    while True:
        users = db.supabase.auth.admin.list_users(page=page, per_page=200)
        if not users:
            return None
        for u in users:
            if (u.email or "").lower() == email.lower():
                return u
        page += 1


def main():
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        return 1
    db = DataBaseHandler()
    auth_user = find_auth_user(db, sys.argv[1])
    if auth_user is None:
        print(f"No portal account with email {sys.argv[1]}. Sign up on the portal first.")
        return 1
    meta = auth_user.app_metadata or {}
    if len(sys.argv) == 2:
        print(f"{auth_user.email} -> USER {meta.get(USER_ROW_KEY)}")
        return 0

    row_id = int(sys.argv[2])
    row = db.one(db.getUser(row_id))
    if row is None:
        print(f"USER {row_id} does not exist")
        return 1
    db.supabase.auth.admin.update_user_by_id(auth_user.id, {"app_metadata": {**meta, USER_ROW_KEY: row_id}})
    print(f"{auth_user.email} -> USER {row_id} ({row.get('NAME')}, {row.get('ROLE')}). Sign in again on the portal.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
