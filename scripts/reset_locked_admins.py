import os
import sys
import sqlite3
import secrets
import string

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from controller.auth_controller import AuthController

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'hardware_inventory.db')


def generate_password(length=12):
    # Ensure complexity: at least one uppercase, one digit, one special from @#$%^&*
    specials = '@#$%^&*'
    while True:
        pwd = ''.join(secrets.choice(string.ascii_letters + string.digits + specials) for _ in range(length))
        if (any(c.isupper() for c in pwd)
                and any(c.isdigit() for c in pwd)
                and any(c in specials for c in pwd)):
            return pwd


def reset_locked_admins():
    auth = AuthController(DB)
    try:
        with sqlite3.connect(DB) as conn:
            rows = conn.execute("SELECT id, username, email, locked FROM users WHERE role='ADMIN'").fetchall()
            if not rows:
                print('NO_ADMINS')
                return 2

            locked = [r for r in rows if r[3]]
            if not locked:
                print('NO_LOCKED_ADMINS')
                # Optionally, we can still reset a named admin; leave for now
                return 0

            for user_id, username, email, locked_flag in locked:
                new_password = generate_password(12)
                # use AuthController's hashing
                new_hash = auth._hash_password(new_password)
                conn.execute(
                    "UPDATE users SET password_hash = ?, failed_attempts = 0, locked = 0 WHERE id = ?",
                    (new_hash, user_id),
                )
                print('RESET', username, email or '', new_password)
        return 0
    except Exception as exc:
        print('ERROR', exc)
        return 1


if __name__ == '__main__':
    sys.exit(reset_locked_admins())
