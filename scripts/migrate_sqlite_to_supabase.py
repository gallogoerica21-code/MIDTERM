import argparse
import os
import sqlite3

from models.database import (
    connect_db,
    init_hardware_db,
    init_sqlite_hardware_db,
)


TABLE_COLUMNS = {
    "users": (
        "id, username, email, password_hash, role, failed_attempts, locked",
        "id",
    ),
    "hardware": (
        "item_id, item_name, category, quantity, unit_price, status",
        "item_id",
    ),
    "borrowed_items": (
        "borrow_id, student_name, student_id, item_id, quantity, "
        "repayment_due_date, status, borrowed_at, requested_by, approved_by, "
        "approved_at, rejected_by, rejected_at",
        "borrow_id",
    ),
    "return_requests": (
        "return_id, borrow_id, quantity, status, requested_at, reviewed_at, "
        "reviewed_by",
        "return_id",
    ),
    "password_reset_requests": (
        "request_id, user_id, email, requested_password_hash, status, "
        "requested_at, reviewed_at, reviewed_by",
        "request_id",
    ),
}


def migrate(source_path):
    if not os.environ.get("SUPABASE_DB_URL"):
        raise RuntimeError("Set SUPABASE_DB_URL before running this migration.")

    init_sqlite_hardware_db(source_path)
    init_hardware_db()

    with sqlite3.connect(source_path) as source, connect_db() as destination:
        existing_rows = {
            table: destination.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            for table in TABLE_COLUMNS
        }
        populated_tables = [table for table, count in existing_rows.items() if count]
        if populated_tables:
            raise RuntimeError(
                "Migration stopped to avoid duplicate or overwritten data. "
                "These Supabase tables already contain rows: "
                + ", ".join(populated_tables)
            )

        for table, (columns, id_column) in TABLE_COLUMNS.items():
            rows = source.execute(
                f"SELECT {columns} FROM {table} ORDER BY {id_column}"
            ).fetchall()
            placeholders = ", ".join("?" for _ in columns.split(","))
            for row in rows:
                destination.execute(
                    f"INSERT INTO {table} ({columns}) "
                    f"VALUES ({placeholders})",
                    row,
                )

        for table, (_, id_column) in TABLE_COLUMNS.items():
            destination.execute(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{table}', '{id_column}'),
                    COALESCE(MAX({id_column}), 1),
                    COUNT(*) > 0
                )
                FROM {table}
                """
            )

    print("SQLite data migrated to Supabase successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Copy existing inventory data to an empty Supabase database."
    )
    parser.add_argument(
        "--source",
        default="hardware_inventory.db",
        help="SQLite database file to migrate (default: hardware_inventory.db)",
    )
    args = parser.parse_args()
    migrate(args.source)
