from controller.tracker_controller import HardwareAuthController
import sqlite3
import sys

DB = "hardware_inventory.db"

def main():
    auth = HardwareAuthController()
    username = "admin"
    password = "Admin123@"
    email = "admin@example.com"

    success, msg = auth.register(username, password, email=email, role="ADMIN")
    if success:
        print("Admin account created:", username)
        return 0

    print("Register returned:", msg)

    # Fallback: if username exists, update role, password hash, and unlock
    try:
        with sqlite3.connect(DB) as conn:
            row = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            ).fetchone()
            if not row:
                print("No existing user found and registration failed.")
                return 2

            user_id = row[0]
            new_hash = auth._hash_password(password)
            conn.execute(
                "UPDATE users SET password_hash = ?, role = ?, failed_attempts = 0, locked = 0, email = ? WHERE id = ?",
                (new_hash, "ADMIN", email, user_id),
            )
            print("Existing user updated to admin and unlocked:", username)
            return 0

    except Exception as exc:
        print("Failed to create or update admin:", exc)
        return 3


if __name__ == "__main__":
    sys.exit(main())
