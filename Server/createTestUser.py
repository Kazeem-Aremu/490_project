"""
Create a portal account WITHOUT sending a confirmation email.

Supabase's built-in email service only allows a few emails per hour ("email rate limit
exceeded" on sign up). This script uses the service key to create the account already
confirmed, with the role chosen, and links it to a new USER row right away, so:
  * a teacher can sign in immediately, and
  * a student shows up in a teacher's "Add students" list before ever signing in.

    py createTestUser.py <email> <student|teacher> <first name> <last name> [password]
    py createTestUser.py teacher1@umes.edu teacher Ada Lovelace
    py createTestUser.py student1@umes.edu student Alan Turing Passw0rd!

If no password is given you are asked for one (at least 6 characters, like the sign up page).
Uses SUPABASE_URL and SUPABASE_SECRET_KEY from Server/.env. Never ship this to the browser.
"""
import getpass
import sys
import traceback

from DataBaseHandler import DataBaseHandler, USER, USER_ID, USER_NAME, USER_ROLE
from AuthService import SIGNUP_ROLES, USER_ROW_KEY
from linkAuthUser import find_auth_user

MIN_PASSWORD = 6


def main():
    args = sys.argv[1:]
    if len(args) not in (4, 5) or args[1].lower() not in SIGNUP_ROLES:
        print(__doc__)
        return 1
    email, role, first, last = args[0].strip(), args[1].lower(), args[2].strip(), args[3].strip()
    password = args[4] if len(args) == 5 else getpass.getpass("Password for the new account: ")
    if len(password) < MIN_PASSWORD:
        print(f"The password must be at least {MIN_PASSWORD} characters.")
        return 1

    db = DataBaseHandler()
    if find_auth_user(db, email) is not None:
        print(f"{email} already has a portal account. Use linkAuthUser.py to check or change its USER row.")
        return 1

    # 1) the USER row the server uses (same as AuthService does on a first sign in)
    name = f"{first} {last}".strip() or email
    row = db.one(db.supabase.table(USER).insert([{USER_NAME: name, USER_ROLE: role}]).execute().data)
    if row is None:
        print("Could not create the USER row.")
        return 1

    # 2) the Supabase Auth account, already confirmed and already linked to that row
    try:
        db.supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"first_name": first, "last_name": last, "role": role},
            "app_metadata": {USER_ROW_KEY: row[USER_ID]},
        })
    except Exception as e:
        traceback.print_exc()
        db.supabase.table(USER).delete().eq(USER_ID, row[USER_ID]).execute()  # don't leave an orphan row
        print(f"\nCould not create the account: {e}")
        return 1

    print(f"Created {role} {name} <{email}> (USER {row[USER_ID]}). They can sign in on the portal now.")
    if role == "teacher":
        print(f"For the mock class: py mockClass.py {email}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
