import os
import sqlite3

from dotenv import load_dotenv

from logger import logger

load_dotenv()

def init_sqlite_hardware_db(db_name="hardware_inventory.db"):
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
                    requested_by TEXT,
                    approved_by TEXT,
                    approved_at TEXT,
                    rejected_by TEXT,
                    rejected_at TEXT,
                    FOREIGN KEY (item_id) REFERENCES hardware(item_id)
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS return_requests (
                    return_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    borrow_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TEXT,
                    reviewed_by TEXT,
                    FOREIGN KEY (borrow_id) REFERENCES borrowed_items(borrow_id)
                )
                """
            )

            cursor.execute("PRAGMA table_info(return_requests)")
            return_cols = [row[1] for row in cursor.fetchall()]
            if "quantity" not in return_cols:
                cursor.execute(
                    "ALTER TABLE return_requests ADD COLUMN quantity INTEGER NOT NULL DEFAULT 0"
                )
                if "return_quantity" in return_cols:
                    cursor.execute(
                        "UPDATE return_requests SET quantity = return_quantity"
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
                "requested_by": "ALTER TABLE borrowed_items ADD COLUMN requested_by TEXT",
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


def connect_db(db_name="hardware_inventory.db"):
    """Connect to Supabase PostgreSQL when configured, otherwise use SQLite."""
    database_url = os.environ.get("SUPABASE_DB_URL")
    if not database_url:
        return sqlite3.connect(db_name)

    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError(
            "Supabase is configured but psycopg is missing. "
            "Install the packages in requirements.txt."
        ) from exc

    try:
        connection = psycopg.connect(database_url, sslmode="require")
    except psycopg.Error as exc:
        logger.exception("Could not connect to Supabase PostgreSQL.")
        raise sqlite3.OperationalError("Could not connect to Supabase PostgreSQL.") from exc
    return _PostgresConnection(connection, psycopg)


class _PostgresConnection:
    def __init__(self, connection, psycopg):
        self._connection = connection
        self._psycopg = psycopg

    def execute(self, query, parameters=()):
        try:
            return self._connection.execute(query.replace("?", "%s"), parameters)
        except self._psycopg.IntegrityError as exc:
            raise sqlite3.IntegrityError(str(exc)) from exc
        except self._psycopg.Error as exc:
            raise sqlite3.OperationalError(str(exc)) from exc

    def commit(self):
        try:
            self._connection.commit()
        except self._psycopg.Error as exc:
            raise sqlite3.OperationalError(str(exc)) from exc

    def __enter__(self):
        self._connection.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return self._connection.__exit__(exc_type, exc_value, traceback)
        except self._psycopg.IntegrityError as exc:
            raise sqlite3.IntegrityError(str(exc)) from exc
        except self._psycopg.Error as exc:
            raise sqlite3.OperationalError(str(exc)) from exc


def init_postgres_hardware_db(database_url):
    """Create the shared Supabase schema used by the application."""
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError(
            "Supabase is configured but psycopg is missing. "
            "Install the packages in requirements.txt."
        ) from exc

    try:
        with psycopg.connect(database_url, sslmode="require") as conn:
            statements = (
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'USER',
                    failed_attempts INTEGER NOT NULL DEFAULT 0,
                    locked INTEGER NOT NULL DEFAULT 0
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS hardware (
                    item_id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    item_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price DOUBLE PRECISION NOT NULL,
                    status TEXT NOT NULL
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS borrowed_items (
                    borrow_id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    student_name TEXT NOT NULL,
                    student_id TEXT NOT NULL,
                    item_id BIGINT NOT NULL REFERENCES hardware(item_id),
                    quantity INTEGER NOT NULL,
                    repayment_due_date TEXT,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    borrowed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    requested_by TEXT,
                    approved_by TEXT,
                    approved_at TEXT,
                    rejected_by TEXT,
                    rejected_at TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS return_requests (
                    return_id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    borrow_id BIGINT NOT NULL REFERENCES borrowed_items(borrow_id),
                    quantity INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TEXT,
                    reviewed_by TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS password_reset_requests (
                    request_id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id),
                    email TEXT NOT NULL,
                    requested_password_hash TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TEXT,
                    reviewed_by TEXT
                )
                """,
            )
            for statement in statements:
                conn.execute(statement)
            conn.execute(
                """
                ALTER TABLE borrowed_items
                ALTER COLUMN repayment_due_date DROP NOT NULL
                """
            )
            for table in (
                "users",
                "hardware",
                "borrowed_items",
                "return_requests",
                "password_reset_requests",
            ):
                conn.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)"
            )
    except psycopg.Error:
        logger.exception("Supabase PostgreSQL database initialization failed.")
        raise

    logger.info("Supabase PostgreSQL database initialized successfully.")


def init_hardware_db(db_name="hardware_inventory.db"):
    database_url = os.environ.get("SUPABASE_DB_URL")
    if database_url:
        init_postgres_hardware_db(database_url)
    else:
        init_sqlite_hardware_db(db_name=db_name)
