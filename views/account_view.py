import tkinter as tk
from tkinter import messagebox, ttk

from controller.tracker_controller import HardwareAuthController


COLORS = {
    "navy": "#172554",
    "blue": "#2563EB",
    "green": "#16A34A",
    "red": "#DC2626",
    "orange": "#EA580C",
    "bg": "#F4F7FB",
    "text": "#111827",
    "muted": "#64748B",
    "border": "#E2E8F0",
}


class ProfileWindow:
    def __init__(self, parent, username):
        self.auth = HardwareAuthController()

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("My Profile & Security")
        self.dialog.geometry("500x620")
        self.dialog.configure(bg=COLORS["bg"])
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        profile = self.auth.get_profile(username)

        if not profile:
            messagebox.showerror(
                "Profile",
                "Unable to load the user profile.",
                parent=self.dialog,
            )
            self.dialog.destroy()
            return

        self._build(profile)

    def _build(self, profile):
        username, email, role, locked = profile

        tk.Label(
            self.dialog,
            text="👤  MY PROFILE",
            font=("Segoe UI", 19, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(anchor="w", padx=30, pady=(25, 2))

        tk.Label(
            self.dialog,
            text="Account information and password security",
            font=("Segoe UI", 9),
            bg=COLORS["bg"],
            fg=COLORS["muted"],
        ).pack(anchor="w", padx=30, pady=(0, 20))

        card = tk.Frame(
            self.dialog,
            bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        card.pack(fill="x", padx=30)

        for label, value in (
            ("USERNAME", username),
            ("EMAIL", email or "Not provided"),
            ("ROLE", role),
            ("ACCOUNT STATUS", "Locked" if locked else "Active"),
        ):
            row = tk.Frame(card, bg="white")
            row.pack(fill="x", padx=18, pady=10)

            tk.Label(
                row,
                text=label,
                font=("Segoe UI", 8, "bold"),
                bg="white",
                fg=COLORS["muted"],
            ).pack(anchor="w")

            tk.Label(
                row,
                text=str(value),
                font=("Segoe UI", 10, "bold"),
                bg="white",
                fg=COLORS["text"],
            ).pack(anchor="w", pady=(2, 0))

        security = tk.Frame(self.dialog, bg=COLORS["bg"])
        security.pack(fill="x", padx=30, pady=18)

        tk.Label(
            security,
            text="CHANGE PASSWORD",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["muted"],
        ).pack(anchor="w")

        current = self._entry(security)
        new = self._entry(security)

        labels = [("Current password", current), ("New password", new)]
        for label, entry in labels:
            tk.Label(
                security,
                text=label,
                font=("Segoe UI", 8, "bold"),
                bg=COLORS["bg"],
                fg=COLORS["muted"],
            ).pack(anchor="w", pady=(8, 3))
            entry.pack(fill="x", ipady=7)

        tk.Button(
            security,
            text="SAVE NEW PASSWORD",
            command=lambda: self._change(
                username, current.get(), new.get()
            ),
            bg=COLORS["blue"],
            fg="white",
            activebackground="#1D4ED8",
            activeforeground="white",
            relief="flat",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        ).pack(fill="x", pady=16, ipady=9)

    @staticmethod
    def _entry(parent):
        return tk.Entry(
            parent,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
            show="*",
        )

    def _change(self, username, current, new):
        success, msg = self.auth.change_password(
            username, current, new
        )
        (messagebox.showinfo if success else messagebox.showerror)(
            "Password Change",
            msg,
            parent=self.dialog,
        )
        if success:
            self.dialog.destroy()


class AdminApprovalsWindow:
    def __init__(self, parent, admin_username):
        self.auth = HardwareAuthController()
        self.admin_username = admin_username

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Admin Approvals")
        self.dialog.geometry("980x760")
        self.dialog.minsize(980, 760)
        self.dialog.configure(bg=COLORS["bg"])
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._build()
        self.load()

    def _build(self):
        tk.Label(
            self.dialog,
            text="✓  ADMIN APPROVALS",
            font=("Segoe UI", 19, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(anchor="w", padx=25, pady=(22, 2))

        tk.Label(
            self.dialog,
            text="Admin approval is required before a password-reset request becomes active.",
            font=("Segoe UI", 9),
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=25, pady=(0, 15))

        table_card = tk.Frame(
            self.dialog,
            bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        table_card.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        columns = (
            "ID",
            "Username",
            "Email",
            "Status",
            "Requested",
            "Reviewed",
            "By",
        )

        self.tree = ttk.Treeview(
            table_card,
            columns=columns,
            show="headings",
            height=12,
        )

        widths = {
            "ID": 55,
            "Username": 110,
            "Email": 190,
            "Status": 95,
            "Requested": 145,
            "Reviewed": 145,
            "By": 110,
        }

        for column in columns:
            self.tree.heading(column, text=column.upper())
            self.tree.column(
                column,
                width=widths[column],
                anchor="center" if column in {"ID", "Status"} else "w",
            )

        self.tree.tag_configure(
            "pending",
            foreground=COLORS["orange"],
        )
        self.tree.tag_configure(
            "approved",
            foreground=COLORS["green"],
        )
        self.tree.tag_configure(
            "rejected",
            foreground=COLORS["red"],
        )

        scroll = ttk.Scrollbar(
            table_card,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scroll.pack(side="right", fill="y", pady=10)

        controls = tk.Frame(self.dialog, bg=COLORS["bg"])
        controls.pack(pady=(0, 20))

        self._button(
            controls,
            "✓  APPROVE SELECTED",
            lambda: self.review(True),
            COLORS["green"],
        ).pack(side="left", padx=5)

        self._button(
            controls,
            "✕  REJECT SELECTED",
            lambda: self.review(False),
            COLORS["red"],
        ).pack(side="left", padx=5)

        self._button(
            controls,
            "↻  REFRESH",
            self.load,
            COLORS["blue"],
        ).pack(side="left", padx=5)

        borrow_label = tk.Label(
            self.dialog,
            text="Borrow approval requests",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text"],
        )
        borrow_label.pack(anchor="w", padx=25, pady=(15, 8))

        borrow_table = tk.Frame(
            self.dialog,
            bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        borrow_table.pack(fill="x", padx=25, pady=(0, 10))

        borrow_columns = (
            "Borrow ID",
            "Student Name",
            "Student ID",
            "Item ID",
            "Item Name",
            "Quantity",
            "Pay By",
            "Requested",
            "Status",
        )
        self.borrow_tree = ttk.Treeview(
            borrow_table,
            columns=borrow_columns,
            show="headings",
            height=6,
        )

        borrow_widths = {
            "Borrow ID": 80,
            "Student Name": 150,
            "Student ID": 120,
            "Item ID": 80,
            "Item Name": 150,
            "Quantity": 80,
            "Pay By": 110,
            "Requested": 150,
            "Status": 90,
        }

        for column in borrow_columns:
            self.borrow_tree.heading(column, text=column.upper())
            self.borrow_tree.column(column, width=borrow_widths[column], anchor="w")

        self.borrow_tree.tag_configure("PENDING", foreground=COLORS["orange"])
        self.borrow_tree.tag_configure("APPROVED", foreground=COLORS["green"])
        self.borrow_tree.tag_configure("REJECTED", foreground=COLORS["red"])

        borrow_scroll = ttk.Scrollbar(
            borrow_table,
            orient="vertical",
            command=self.borrow_tree.yview,
        )
        self.borrow_tree.configure(yscrollcommand=borrow_scroll.set)

        self.borrow_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        borrow_scroll.pack(side="right", fill="y", pady=10)

        borrow_controls = tk.Frame(self.dialog, bg=COLORS["bg"])
        borrow_controls.pack(pady=(0, 20))

        self._button(
            borrow_controls,
            "✓  APPROVE BORROW",
            self.approve_borrow_request,
            COLORS["green"],
        ).pack(side="left", padx=5)

        self._button(
            borrow_controls,
            "✕  REJECT BORROW",
            self.reject_borrow_request,
            COLORS["red"],
        ).pack(side="left", padx=5)

        self._button(
            borrow_controls,
            "↻  REFRESH",
            self.load,
            COLORS["blue"],
        ).pack(side="left", padx=5)

    @staticmethod
    def _button(parent, text, command, color):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="white",
            activebackground=color,
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=12,
            pady=8,
        )

    def load(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in self.auth.get_reset_requests():
            status = str(row[3]).lower()
            self.tree.insert(
                "",
                tk.END,
                values=row,
                tags=(status,),
            )

        for item in self.borrow_tree.get_children():
            self.borrow_tree.delete(item)

        rows = self.auth.get_borrow_requests()
        if not rows:
            self.borrow_tree.insert(
                "",
                tk.END,
                values=("No borrow requests yet", "", "", "", "", "", "", "", ""),
            )
            return

        for row in rows:
            status = str(row[8]).upper()
            self.borrow_tree.insert("", tk.END, values=row, tags=(status,))

    def review(self, approve):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "Approval",
                "Select a reset request first.",
                parent=self.dialog,
            )
            return

        values = self.tree.item(selected[0])["values"]
        request_id = values[0]

        action = "approve" if approve else "reject"

        if not messagebox.askyesno(
            "Confirm Action",
            f"Are you sure you want to {action} request #{request_id}?",
            parent=self.dialog,
        ):
            return

        success, msg = self.auth.review_reset_request(
            int(request_id),
            self.admin_username,
            approve,
        )

        (messagebox.showinfo if success else messagebox.showerror)(
            "Approval",
            msg,
            parent=self.dialog,
        )

        if success:
            self.load()

    def approve_borrow_request(self):
        selected = self.borrow_tree.selection()
        if not selected:
            messagebox.showwarning(
                "Borrow Approval",
                "Select a borrow request first.",
                parent=self.dialog,
            )
            return

        values = self.borrow_tree.item(selected[0])["values"]
        borrow_id = values[0]

        if not messagebox.askyesno(
            "Confirm Approval",
            f"Approve borrow request #{borrow_id}?",
            parent=self.dialog,
        ):
            return

        success, msg = self.auth.approve_borrow_request(int(borrow_id), self.admin_username)
        (messagebox.showinfo if success else messagebox.showerror)(
            "Borrow Approval",
            msg,
            parent=self.dialog,
        )
        if success:
            self.load()
            messagebox.showinfo(
                "Borrow Request Updated",
                "The borrow request has been approved and the user will be notified.",
                parent=self.dialog,
            )

    def reject_borrow_request(self):
        selected = self.borrow_tree.selection()
        if not selected:
            messagebox.showwarning(
                "Borrow Approval",
                "Select a borrow request first.",
                parent=self.dialog,
            )
            return

        values = self.borrow_tree.item(selected[0])["values"]
        borrow_id = values[0]

        if not messagebox.askyesno(
            "Confirm Rejection",
            f"Reject borrow request #{borrow_id}?",
            parent=self.dialog,
        ):
            return

        success, msg = self.auth.reject_borrow_request(int(borrow_id), self.admin_username)
        (messagebox.showinfo if success else messagebox.showerror)(
            "Borrow Approval",
            msg,
            parent=self.dialog,
        )
        if success:
            self.load()
            messagebox.showinfo(
                "Borrow Request Updated",
                "The borrow request has been rejected and the user will be notified.",
                parent=self.dialog,
            )


class BorrowHistoryWindow:
    def __init__(self, parent):
        from controller.hardware_controller import HardwareController

        self.controller = HardwareController()

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Borrowed Items History")
        self.dialog.geometry("1240x620")
        self.dialog.minsize(1080, 500)
        self.dialog.configure(bg=COLORS["bg"])
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._build()
        self.load()

    def _build(self):
        tk.Label(
            self.dialog,
            text="📦  BORROWED ITEMS",
            font=("Segoe UI", 19, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(anchor="w", padx=25, pady=(22, 2))

        tk.Label(
            self.dialog,
            text="Borrow records appear here after a student or staff member checks out equipment.",
            font=("Segoe UI", 9),
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=25, pady=(0, 15))

        table_card = tk.Frame(
            self.dialog,
            bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        table_card.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        columns = (
            "Borrow ID",
            "Student Name",
            "Student ID",
            "Item ID",
            "Item Name",
            "Quantity",
            "Pay By",
            "Status",
            "Borrowed At",
        )

        self.tree = ttk.Treeview(
            table_card,
            columns=columns,
            show="headings",
            height=14,
        )

        self.tree.tag_configure("PENDING", foreground=COLORS["orange"])
        self.tree.tag_configure("APPROVED", foreground=COLORS["green"])
        self.tree.tag_configure("REJECTED", foreground=COLORS["red"])

        widths = {
            "Borrow ID": 90,
            "Student Name": 170,
            "Student ID": 130,
            "Item ID": 90,
            "Item Name": 190,
            "Quantity": 90,
            "Pay By": 110,
            "Status": 95,
            "Borrowed At": 170,
        }

        for column in columns:
            self.tree.heading(column, text=column.upper())
            self.tree.column(column, width=widths[column], anchor="w")

        scroll_y = ttk.Scrollbar(
            table_card,
            orient="vertical",
            command=self.tree.yview,
        )
        scroll_x = ttk.Scrollbar(
            table_card,
            orient="horizontal",
            command=self.tree.xview,
        )
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scroll_y.pack(side="right", fill="y", pady=10)
        scroll_x.pack(side="bottom", fill="x", padx=10)

    def load(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = self.controller.fetch_borrowed_items()
        if not rows:
            self.tree.insert(
                "",
                tk.END,
                values=("No borrow records yet", "", "", "", "", "", "", "", ""),
            )
            return

        for row in rows:
            status = str(row[7]).upper()
            self.tree.insert("", tk.END, values=row, tags=(status,))
