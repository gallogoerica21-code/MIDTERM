import sqlite3

from logger import logger


def init_hardware_db(db_name="hardware_inventory.db"):
    """Create the application's database and migrate older databases safely."""
    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'USER',
                    failed_attempts INTEGER NOT NULL DEFAULT 0,
                    locked INTEGER NOT NULL DEFAULT 0
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS hardware (
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS borrowed_items (
                    borrow_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_name TEXT NOT NULL,
                    student_id TEXT NOT NULL,
                    item_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    repayment_due_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    borrowed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    approved_by TEXT,
                    approved_at TEXT,
                    rejected_by TEXT,
                    rejected_at TEXT,
                    FOREIGN KEY (item_id) REFERENCES hardware(item_id)
                )
                """
            )

            # Migrate older users tables.
            cursor.execute("PRAGMA table_info(users)")
            cols = [row[1] for row in cursor.fetchall()]

            if "email" not in cols:
                cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
            if "role" not in cols:
                cursor.execute(
                    "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'USER'"
                )
            if "failed_attempts" not in cols:
                cursor.execute(
                    "ALTER TABLE users ADD COLUMN failed_attempts INTEGER NOT NULL DEFAULT 0"
                )
            if "locked" not in cols:
                cursor.execute(
                    "ALTER TABLE users ADD COLUMN locked INTEGER NOT NULL DEFAULT 0"
                )

            # A unique email index can fail if an old database contains duplicates.
            # In that case, keep the application usable and log the migration issue.
            try:
                cursor.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)"
                )
            except sqlite3.IntegrityError as exc:
                logger.warning("Could not create unique email index: %s", exc)

            cursor.execute("PRAGMA table_info(borrowed_items)")
            borrow_cols = [row[1] for row in cursor.fetchall()]
            for col_name, col_sql in {
                "repayment_due_date": "ALTER TABLE borrowed_items ADD COLUMN repayment_due_date TEXT",
                "status": "ALTER TABLE borrowed_items ADD COLUMN status TEXT NOT NULL DEFAULT 'PENDING'",
                "approved_by": "ALTER TABLE borrowed_items ADD COLUMN approved_by TEXT",
                "approved_at": "ALTER TABLE borrowed_items ADD COLUMN approved_at TEXT",
                "rejected_by": "ALTER TABLE borrowed_items ADD COLUMN rejected_by TEXT",
                "rejected_at": "ALTER TABLE borrowed_items ADD COLUMN rejected_at TEXT",
            }.items():
                if col_name not in borrow_cols:
                    try:
                        cursor.execute(col_sql)
                    except sqlite3.Error as exc:
                        logger.warning("Could not add borrowed_items column %s: %s", col_name, exc)

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS password_reset_requests (
                    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    email TEXT NOT NULL,
                    requested_password_hash TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TEXT,
                    reviewed_by TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
                """
            )

            conn.commit()

        logger.info("Hardware inventory database initialized successfully.")

    except sqlite3.Error as exc:
        logger.exception("Database initialization error: %s", exc)
        raise
