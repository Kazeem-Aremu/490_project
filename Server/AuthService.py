"""
Ties a Supabase Auth login (the student-portal sign in page) to a row in our USER table.

The browser signs in with Supabase Auth and sends its access token to the server.
We ask Supabase who that token belongs to, so USERID is never trusted from the client.

The USER table uses integer ids and has no email/auth column, so the link is stored in the
auth user's app_metadata as "user_row_id" (only the service key can write app_metadata,
so a student cannot change it). First login creates the USER row from the signup names and the role chosen on sign up
(student or teacher).
To link an auth account to an existing USER row (e.g. seeded test data) use linkAuthUser.py.
"""
import threading
import traceback

from DataBaseHandler import USER, USER_ID, USER_NAME, USER_ROLE

USER_ROW_KEY = "user_row_id"
DEFAULT_ROLE = "student"
SIGNUP_ROLES = {"student", "teacher"}  # what the sign up page may choose


def err(code, text):
    return {"Response Code": code, "MESSAGE": {"ERROR": text}}


class AuthService:
    def __init__(self, database):
        self.db = database
        self._locks = {}
        self._locks_guard = threading.Lock()

    def _lock_for(self, key):
        with self._locks_guard:
            return self._locks.setdefault(key, threading.Lock())

    def login(self, token):
        """Returns (user_row, None) on success or (None, error_response)."""
        if not isinstance(token, str) or not token.strip():
            return None, err("400", "PARAMS needs TOKEN")
        try:
            auth_user = self.db.supabase.auth.get_user(token.strip()).user
        except Exception:
            traceback.print_exc()
            auth_user = None
        if auth_user is None:
            return None, err("401", "Your session is not valid. Please sign in again.")

        with self._lock_for(auth_user.id):
            try:
                row = self._find_or_create(auth_user)
            except Exception as e:
                traceback.print_exc()
                return None, err("500", f"Could not load your account: {e}")
        row = dict(row)
        row["AUTH_ID"] = auth_user.id
        row["EMAIL"] = auth_user.email
        return row, None

    def _find_or_create(self, auth_user):
        app_meta = auth_user.app_metadata or {}
        row_id = app_meta.get(USER_ROW_KEY)
        if row_id is not None:
            row = self.db.one(self.db.getUser(int(row_id)))
            if row is not None:
                return row

        meta = auth_user.user_metadata or {}
        name = " ".join(p for p in (meta.get("first_name"), meta.get("last_name")) if p).strip()
        role = str(meta.get("role") or "").lower()
        if role not in SIGNUP_ROLES:
            role = DEFAULT_ROLE
        row = self.db.one(self.db.supabase.table(USER).insert([{
            USER_NAME: name or auth_user.email or role.title(),
            USER_ROLE: role,
        }]).execute().data)

        self.db.supabase.auth.admin.update_user_by_id(
            auth_user.id, {"app_metadata": {**app_meta, USER_ROW_KEY: row[USER_ID]}})
        print(f"Linked auth user {auth_user.id} to USER {row[USER_ID]}")
        return row
