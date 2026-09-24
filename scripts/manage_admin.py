import os
import sys
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from controller.auth_controller import AuthController

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'hardware_inventory.db')

def list_admins():
    try:
        with sqlite3.connect(DB) as conn:
            rows = conn.execute("SELECT username, email, role, locked FROM users WHERE role = 'ADMIN'").fetchall()
            return rows
    except Exception as e:
        print('ERROR', e)
        return None

if __name__ == '__main__':
    auth = AuthController(DB)
    admins = list_admins()
    if admins is None:
        print('FAILED_TO_OPEN_DB')
        sys.exit(2)

    if len(admins) > 0:
        print('FOUND')
        for a in admins:
            print(a[0] or '', '|', a[1] or '', '|', a[2] or '', '|', 'Locked' if a[3] else 'Active')
        sys.exit(0)

    # No admins found; create a default admin
    username = 'admin'
    password = 'Admin@1234'
    email = 'admin@example.com'
    success, msg = auth.register(username, password, email=email, role='ADMIN')
    if success:
        print('CREATED')
        print(username, password, email)
        sys.exit(0)
    else:
        print('CREATE_FAILED')
        print(msg)
        sys.exit(1)
