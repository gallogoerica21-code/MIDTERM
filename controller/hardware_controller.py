import csv
import sqlite3
from datetime import datetime

from pydantic import ValidationError

from logger import logger
from models.schemas import BorrowedItemSchema


class HardwareController:
    def __init__(self, db_name="hardware_inventory.db"):
        self.db_name = db_name

    def _connect(self):
        return sqlite3.connect(self.db_name)

    @staticmethod
    def _status_from_quantity(quantity: int) -> str:
        if quantity <= 0:
            return "Out of Stock"
        if quantity <= 5:
            return "Low Stock"
        return "In Stock"

    def fetch_all_items(self, search="", category="All"):
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE hardware
                SET status = CASE
                    WHEN quantity <= 0 THEN 'Out of Stock'
                    WHEN quantity <= 5 THEN 'Low Stock'
                    ELSE 'In Stock'
                END
                """
            )

            query = """
                SELECT item_id, item_name, category,
                       quantity, unit_price, status
                FROM hardware
                WHERE 1=1
            """
            params = []

            if search:
                query += """
                    AND (
                        item_name LIKE ?
                        OR category LIKE ?
                        OR status LIKE ?
                    )
                """
                term = f"%{search}%"
                params.extend([term, term, term])

            if category and category != "All":
                query += " AND category = ?"
                params.append(category)

            query += " ORDER BY item_id"

            return conn.execute(query, params).fetchall()

    def fetch_categories(self):
        with self._connect() as conn:
            return [
                row[0]
                for row in conn.execute(
                    """
                    SELECT DISTINCT category
                    FROM hardware
                    ORDER BY category
                    """
                )
            ]

    def get_total_value(self):
        with self._connect() as conn:
            result = conn.execute(
                "SELECT SUM(quantity * unit_price) FROM hardware"
            ).fetchone()
        return result[0] or 0.0

    def add_item(self, name, category, quantity, price):
        name = str(name).strip()
        category = str(category).strip()

        if not name:
            return False, "Item name is required."
        if not category:
            return False, "Category is required."

        try:
            quantity = int(quantity)
            if quantity < 0:
                return False, "Quantity must be a non-negative integer."
        except (ValueError, TypeError):
            return False, "Quantity must be a valid whole number."

        try:
            price = float(price)
            if price < 0:
                return False, "Unit price must be a non-negative number."
        except (ValueError, TypeError):
            return False, "Unit price must be a valid number."

        status = self._status_from_quantity(quantity)

        try:
            with self._connect() as conn:
                duplicate = conn.execute(
                    """
                    SELECT 1
                    FROM hardware
                    WHERE item_name = ?
                      AND category = ?
                      AND quantity = ?
                      AND unit_price = ?
                    """,
                    (name, category, quantity, price),
                ).fetchone()

                if duplicate:
                    return False, (
                        "An item with the same name, category, "
                        "quantity, and price already exists."
                    )

                conn.execute(
                    """
                    INSERT INTO hardware
                    (item_name, category, quantity, unit_price, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, category, quantity, price, status),
                )

            logger.info("Hardware item added: %s (%s) x%s", name, category, quantity)
            return True, "Equipment added successfully."

        except sqlite3.Error as exc:
            logger.exception("Error adding hardware item: %s", exc)
            return False, "Failed to add equipment to the database."

    def update_item(self, item_id, name, category, quantity, price):
        name = str(name).strip()
        category = str(category).strip()

        if not name:
            return False, "Item name is required."
        if not category:
            return False, "Category is required."

        try:
            quantity = int(quantity)
            if quantity < 0:
                return False, "Quantity must be a non-negative integer."
        except (ValueError, TypeError):
            return False, "Quantity must be a valid whole number."

        try:
            price = float(price)
            if price < 0:
                return False, "Unit price must be a non-negative number."
        except (ValueError, TypeError):
            return False, "Unit price must be a valid number."

        status = self._status_from_quantity(quantity)

        try:
            with self._connect() as conn:
                duplicate = conn.execute(
                    """
                    SELECT 1
                    FROM hardware
                    WHERE item_name = ?
                      AND category = ?
                      AND quantity = ?
                      AND unit_price = ?
                      AND item_id != ?
                    """,
                    (name, category, quantity, price, item_id),
                ).fetchone()

                if duplicate:
                    return False, "A duplicate equipment record already exists."

                updated = conn.execute(
                    """
                    UPDATE hardware
                    SET item_name = ?,
                        category = ?,
                        quantity = ?,
                        unit_price = ?,
                        status = ?
                    WHERE item_id = ?
                    """,
                    (name, category, quantity, price, status, item_id),
                ).rowcount

            if updated:
                logger.info("Hardware item updated: ID %s", item_id)
                return True, "Equipment updated successfully."

            return False, "Equipment record not found."

        except sqlite3.Error as exc:
            logger.exception("Error updating hardware item: %s", exc)
            return False, "Failed to update equipment."

    def delete_item(self, item_id):
        try:
            with self._connect() as conn:
                deleted = conn.execute(
                    "DELETE FROM hardware WHERE item_id = ?",
                    (item_id,),
                ).rowcount

            if deleted:
                logger.info("Hardware item deleted: ID %s", item_id)
                return True, "Equipment deleted successfully."

            return False, "Equipment record not found."

        except sqlite3.Error as exc:
            logger.exception("Error deleting hardware item: %s", exc)
            return False, "Failed to delete equipment."

    def borrow_item(self, student_name, student_id, item_id, quantity, repayment_due_date):
        try:
            validated = BorrowedItemSchema(
                student_name=student_name,
                student_id=student_id,
                item_id=item_id,
                quantity=quantity,
                repayment_due_date=repayment_due_date,
            )
        except ValidationError as exc:
            return False, exc.errors()[0]["msg"]

        try:
            with self._connect() as conn:
                item = conn.execute(
                    "SELECT item_name, quantity FROM hardware WHERE item_id = ?",
                    (validated.item_id,),
                ).fetchone()

                if not item:
                    return False, "Item ID not found."

                item_name, available = item
                if validated.quantity > available:
                    return False, (
                        f"Only {available} unit(s) available for '{item_name}'."
                    )

                conn.execute(
                    """
                    INSERT INTO borrowed_items
                    (student_name, student_id, item_id, quantity, repayment_due_date, status)
                    VALUES (?, ?, ?, ?, ?, 'PENDING')
                    """,
                    (
                        validated.student_name,
                        validated.student_id,
                        validated.item_id,
                        validated.quantity,
                        validated.repayment_due_date,
                    ),
                )

            logger.info(
                "Borrow request created pending admin approval: student=%s, student_id=%s, item_id=%s, quantity=%s, pay_by=%s",
                validated.student_name,
                validated.student_id,
                validated.item_id,
                validated.quantity,
                validated.repayment_due_date,
            )
            return True, "Borrow request submitted successfully. It is waiting for admin approval."

        except sqlite3.Error as exc:
            logger.exception("Error recording borrowed item request: %s", exc)
            return False, "Failed to submit borrow request."

    def fetch_borrowed_items(self):
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT b.borrow_id, b.student_name, b.student_id,
                       b.item_id, h.item_name, b.quantity,
                       b.repayment_due_date, b.status, b.borrowed_at
                FROM borrowed_items b
                JOIN hardware h ON h.item_id = b.item_id
                ORDER BY b.borrow_id DESC
                """
            ).fetchall()

    def fetch_pending_borrow_requests(self):
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT b.borrow_id, b.student_name, b.student_id,
                       b.item_id, h.item_name, b.quantity, b.repayment_due_date,
                       b.borrowed_at, b.status
                FROM borrowed_items b
                JOIN hardware h ON h.item_id = b.item_id
                WHERE b.status = 'PENDING'
                ORDER BY b.borrow_id DESC
                """
            ).fetchall()

    def request_return(self, borrow_id, quantity):
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return False, "Return quantity must be positive."
        except (ValueError, TypeError):
            return False, "Return quantity must be a valid integer."

        try:
            with self._connect() as conn:
                borrow = conn.execute(
                    "SELECT borrow_id, item_id, quantity, status FROM borrowed_items WHERE borrow_id = ?",
                    (borrow_id,),
                ).fetchone()
                if not borrow:
                    return False, "Borrow record not found."

                _, item_id, borrowed_qty, status = borrow
                if status != "APPROVED":
                    return False, "Only approved borrows can be returned."

                if quantity > borrowed_qty:
                    return False, "Return quantity cannot exceed borrowed quantity."

                # Ensure return_requests table exists and has expected columns
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS return_requests (
                        return_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        borrow_id INTEGER NOT NULL,
                        quantity INTEGER NOT NULL,
                        status TEXT NOT NULL DEFAULT 'PENDING',
                        requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        reviewed_at TEXT,
                        reviewed_by TEXT,
                        FOREIGN KEY(borrow_id) REFERENCES borrowed_items(borrow_id)
                    )
                    """
                )

                # Ensure schema variations are handled (some DBs use return_quantity)
                cols = [r[1] for r in conn.execute("PRAGMA table_info(return_requests)").fetchall()]
                if "item_id" not in cols:
                    try:
                        conn.execute("ALTER TABLE return_requests ADD COLUMN item_id INTEGER")
                        cols.append("item_id")
                    except sqlite3.Error:
                        pass

                # support both 'quantity' and 'return_quantity' column names
                qty_col = "quantity" if "quantity" in cols else ("return_quantity" if "return_quantity" in cols else None)
                if qty_col is None:
                    # create a compatible column name if nothing present
                    try:
                        conn.execute("ALTER TABLE return_requests ADD COLUMN quantity INTEGER DEFAULT 0")
                        qty_col = "quantity"
                        cols.append("quantity")
                    except sqlite3.Error:
                        return False, "Return requests schema incompatible."

                insert_cols = ["borrow_id", qty_col]
                insert_vals = [borrow_id, quantity]
                if "item_id" in cols:
                    insert_cols.insert(1, "item_id")
                    insert_vals.insert(1, item_id)

                placeholders = ",".join(["?" for _ in insert_cols])
                col_list = ",".join(insert_cols)
                conn.execute(f"INSERT INTO return_requests ({col_list}, status) VALUES ({placeholders}, 'PENDING')", tuple(insert_vals))

            logger.info("Return requested: borrow_id=%s qty=%s", borrow_id, quantity)
            return True, "Return request submitted for admin approval."

        except sqlite3.Error as exc:
            logger.exception("Error creating return request: %s", exc)
            return False, "Failed to submit return request."

    def get_return_requests(self, status=None):
        with self._connect() as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(return_requests)").fetchall()]
            qty_col = "quantity" if "quantity" in cols else ("return_quantity" if "return_quantity" in cols else None)
            select_cols = ["r.return_id", "r.borrow_id"]
            if "item_id" in cols:
                select_cols.append("r.item_id")
            # include quantity column using whichever exists and alias to quantity
            if qty_col:
                select_cols.append(f"r.{qty_col} as quantity")
            select_cols += ["r.requested_at", "r.status", "r.reviewed_at", "r.reviewed_by"]

            query = f"SELECT {', '.join(select_cols)} FROM return_requests r"
            params = ()
            if status:
                query += " WHERE r.status = ?"
                params = (status.upper(),)

            query += " ORDER BY r.return_id DESC"
            return conn.execute(query, params).fetchall()

    def review_return_request(self, return_id, admin_username, approve: bool):
        try:
            with self._connect() as conn:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(return_requests)").fetchall()]
                qty_col = "quantity" if "quantity" in cols else ("return_quantity" if "return_quantity" in cols else None)
                if qty_col is None:
                    return False, "Return request schema invalid."

                select_clause = f"borrow_id, {qty_col} as qty, status"
                if "item_id" in cols:
                    select_clause = f"borrow_id, item_id, {qty_col} as qty, status"

                row = conn.execute(f"SELECT {select_clause} FROM return_requests WHERE return_id = ?", (return_id,)).fetchone()
                if not row:
                    return False, "Return request not found."

                if "item_id" in cols:
                    borrow_id, item_id, qty, status = row
                else:
                    borrow_id, qty, status = row
                    b = conn.execute("SELECT item_id FROM borrowed_items WHERE borrow_id = ?", (borrow_id,)).fetchone()
                    if not b:
                        return False, "Related borrow record not found."
                    item_id = b[0]

                if status != "PENDING":
                    return False, "Return request is no longer pending."

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_status = "APPROVED" if approve else "REJECTED"

                if approve:
                    conn.execute(
                        "UPDATE hardware SET quantity = quantity + ? WHERE item_id = ?",
                        (qty, item_id),
                    )

                conn.execute(
                    "UPDATE return_requests SET status = ?, reviewed_at = ?, reviewed_by = ? WHERE return_id = ?",
                    (new_status, now, admin_username, return_id),
                )

            logger.info("Return request %s %s by %s", return_id, new_status, admin_username)
            return True, f"Return request {new_status.lower()}."

        except sqlite3.Error as exc:
            logger.exception("Error reviewing return request: %s", exc)
            return False, "Failed to review return request."

    def approve_borrow_request(self, borrow_id, admin_username):
        try:
            with self._connect() as conn:
                request = conn.execute(
                    """
                    SELECT item_id, quantity, status
                    FROM borrowed_items
                    WHERE borrow_id = ?
                    """,
                    (borrow_id,),
                ).fetchone()

                if not request:
                    return False, "Borrow request not found."

                item_id, quantity, status = request
                if status != "PENDING":
                    return False, "This borrow request is no longer pending."

                available = conn.execute(
                    "SELECT quantity FROM hardware WHERE item_id = ?",
                    (item_id,),
                ).fetchone()
                if not available:
                    return False, "Item no longer exists."

                if quantity > available[0]:
                    return False, "Not enough stock available to approve this request."

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute(
                    """
                    UPDATE borrowed_items
                    SET status = 'APPROVED',
                        approved_by = ?,
                        approved_at = ?
                    WHERE borrow_id = ?
                    """,
                    (admin_username, now, borrow_id),
                )
                conn.execute(
                    """
                    UPDATE hardware
                    SET quantity = quantity - ?,
                        status = CASE
                            WHEN quantity - ? <= 0 THEN 'Out of Stock'
                            WHEN quantity - ? <= 5 THEN 'Low Stock'
                            ELSE 'In Stock'
                        END
                    WHERE item_id = ?
                    """,
                    (quantity, quantity, quantity, item_id),
                )

            logger.info(
                "Borrow request approved: borrow_id=%s by=%s",
                borrow_id,
                admin_username,
            )
            return True, "Borrow request approved and stock updated."
        except sqlite3.Error as exc:
            logger.exception("Error approving borrow request: %s", exc)
            return False, "Failed to approve borrow request."

    def reject_borrow_request(self, borrow_id, admin_username):
        try:
            with self._connect() as conn:
                request = conn.execute(
                    "SELECT status FROM borrowed_items WHERE borrow_id = ?",
                    (borrow_id,),
                ).fetchone()
                if not request:
                    return False, "Borrow request not found."
                if request[0] != "PENDING":
                    return False, "This request is no longer pending."

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute(
                    """
                    UPDATE borrowed_items
                    SET status = 'REJECTED',
                        rejected_by = ?,
                        rejected_at = ?
                    WHERE borrow_id = ?
                    """,
                    (admin_username, now, borrow_id),
                )

            logger.info(
                "Borrow request rejected: borrow_id=%s by=%s",
                borrow_id,
                admin_username,
            )
            return True, "Borrow request rejected."
        except sqlite3.Error as exc:
            logger.exception("Error rejecting borrow request: %s", exc)
            return False, "Failed to reject borrow request."

    def export_to_csv(self, filename="hardware_inventory_report.csv"):
        try:
            rows = self.fetch_all_items()

            with open(
                filename,
                mode="w",
                newline="",
                encoding="utf-8",
            ) as file:
                writer = csv.writer(file)
                writer.writerow(
                    ["ID", "Name", "Category", "Quantity", "Unit Price", "Status"]
                )
                writer.writerows(rows)

            logger.info("Inventory exported to CSV: %s", filename)
            return True, f"Inventory exported to {filename}."

        except (OSError, sqlite3.Error) as exc:
            logger.exception("Error exporting inventory: %s", exc)
            return False, "Failed to export inventory to CSV."
