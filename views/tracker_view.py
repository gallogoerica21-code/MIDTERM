import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, ttk

from controller.hardware_controller import HardwareController
from logger import logger
from views.account_view import AdminApprovalsWindow, ProfileWindow


COLORS = {
    "navy": "#172554",
    "navy_2": "#1E3A8A",
    "blue": "#2563EB",
    "blue_hover": "#1D4ED8",
    "green": "#16A34A",
    "orange": "#EA580C",
    "red": "#DC2626",
    "purple": "#7C3AED",
    "bg": "#F4F7FB",
    "card": "#FFFFFF",
    "text": "#111827",
    "muted": "#64748B",
    "border": "#E2E8F0",
}


class HardwareTrackerWindow:
    """Professional campus inventory dashboard."""

    def __init__(self, root, username="Unknown", role="USER", on_logout=None):
        self.root = root
        self.username = username
        self.role = str(role or "USER").upper()
        self.on_logout = on_logout
        self.controller = HardwareController()
        self.selected_item_id = None

        self.root.title("Campus Hardware & Asset Management Dashboard")
        self.root.geometry("1400x850")
        self.root.minsize(1120, 700)
        self.root.configure(bg=COLORS["bg"])

        self._configure_styles()
        self._build_layout()
        self.load_data()
        self.auto_refresh()

    def _configure_styles(self):
        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Campus.Treeview",
            background="white",
            foreground=COLORS["text"],
            fieldbackground="white",
            rowheight=42,
            font=("Segoe UI", 10),
            borderwidth=0,
        )

        style.configure(
            "Campus.Treeview.Heading",
            background="#F8FAFC",
            foreground=COLORS["muted"],
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padding=(10, 10),
        )

        style.map(
            "Campus.Treeview",
            background=[("selected", "#DBEAFE")],
            foreground=[("selected", COLORS["text"])],
        )

    def _build_layout(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_main()

    def _build_sidebar(self):
        self.sidebar = tk.Frame(
            self.root,
            bg=COLORS["navy"],
            width=245,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        tk.Label(
            self.sidebar,
            text="🎓",
            font=("Segoe UI Emoji", 32),
            bg=COLORS["navy"],
            fg="white",
        ).pack(pady=(24, 2))

        tk.Label(
            self.sidebar,
            text="CAMPUS ASSET",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS["navy"],
            fg="white",
        ).pack()

        tk.Label(
            self.sidebar,
            text="MANAGEMENT SYSTEM",
            font=("Segoe UI", 8, "bold"),
            bg=COLORS["navy"],
            fg="#93C5FD",
        ).pack(pady=(0, 24))

        self._nav_button("▣   Dashboard", self._go_dashboard, active=True)
        self._nav_button("▤   Equipment Inventory", self._focus_inventory)
        self._nav_button("↻   Refresh Data", self.load_data)
        self._nav_button("⇩   Export CSV Report", self.handle_export)

        tk.Frame(
            self.sidebar,
            bg="#334155",
            height=1,
        ).pack(fill="x", padx=20, pady=20)

        tk.Label(
            self.sidebar,
            text="ACCOUNT",
            font=("Segoe UI", 8, "bold"),
            bg=COLORS["navy"],
            fg="#94A3B8",
        ).pack(anchor="w", padx=24)

        self._nav_button("◉   My Profile", self.open_profile)

        if self.role == "ADMIN":
            self._nav_button(
                "✓   Admin Approvals",
                self.open_approvals,
            )

        tk.Frame(
            self.sidebar,
            bg="#334155",
            height=1,
        ).pack(fill="x", padx=20, pady=20)

        tk.Label(
            self.sidebar,
            text=f"Signed in as\n{self.username}\n\nRole: {self.role}",
            font=("Segoe UI", 9),
            justify="left",
            bg=COLORS["navy"],
            fg="#CBD5E1",
        ).pack(anchor="w", padx=24)

        tk.Label(
            self.sidebar,
            text="●  SYSTEM ONLINE",
            font=("Segoe UI", 8, "bold"),
            bg=COLORS["navy"],
            fg="#86EFAC",
        ).pack(side="bottom", anchor="w", padx=24, pady=(0, 7))

        tk.Button(
            self.sidebar,
            text="↪   LOG OUT",
            command=self.handle_logout,
            anchor="w",
            padx=22,
            pady=10,
            bg=COLORS["red"],
            fg="white",
            activebackground="#B91C1C",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
        ).pack(
            side="bottom",
            fill="x",
            padx=12,
            pady=15,
        )

    def _nav_button(self, text, command, active=False):
        tk.Button(
            self.sidebar,
            text=text,
            command=command,
            anchor="w",
            padx=20,
            pady=10,
            bg=COLORS["navy_2"] if active else COLORS["navy"],
            fg="white",
            activebackground=COLORS["navy_2"],
            activeforeground="white",
            font=("Segoe UI", 9, "bold" if active else "normal"),
            relief="flat",
            bd=0,
            cursor="hand2",
        ).pack(fill="x", padx=12, pady=2)

    def _build_main(self):
        self.main = tk.Frame(self.root, bg=COLORS["bg"])
        self.main.grid(row=0, column=1, sticky="nsew")

        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        header = tk.Frame(
            self.main,
            bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            height=78,
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        title_box = tk.Frame(header, bg="white")
        title_box.pack(side="left", padx=28, pady=12)

        tk.Label(
            title_box,
            text="Dashboard",
            font=("Segoe UI", 20, "bold"),
            bg="white",
            fg=COLORS["text"],
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Equipment inventory overview and resource management",
            font=("Segoe UI", 9),
            bg="white",
            fg=COLORS["muted"],
        ).pack(anchor="w")

        tk.Label(
            header,
            text=f"●  {self.role} ACCESS",
            font=("Segoe UI", 9, "bold"),
            bg="white",
            fg=COLORS["green"] if self.role == "ADMIN" else COLORS["blue"],
        ).pack(side="right", padx=28)

        self.content_canvas = tk.Canvas(
            self.main,
            bg=COLORS["bg"],
            highlightthickness=0,
        )
        self.content_canvas.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        scroll = ttk.Scrollbar(
            self.main,
            orient="vertical",
            command=self.content_canvas.yview,
        )
        scroll.grid(row=1, column=1, sticky="ns")

        self.content_canvas.configure(
            yscrollcommand=scroll.set
        )

        self.content = tk.Frame(
            self.content_canvas,
            bg=COLORS["bg"],
        )

        window_id = self.content_canvas.create_window(
            (0, 0),
            window=self.content,
            anchor="nw",
        )

        self.content_canvas.bind(
            "<Configure>",
            lambda event: self.content_canvas.itemconfigure(
                window_id,
                width=event.width,
            ),
        )

        self.content.bind(
            "<Configure>",
            lambda event: self.content_canvas.configure(
                scrollregion=self.content_canvas.bbox("all")
            ),
        )

        self._build_dashboard_content()

    def _build_dashboard_content(self):
        body = tk.Frame(
            self.content,
            bg=COLORS["bg"],
        )
        body.pack(
            fill="both",
            expand=True,
            padx=26,
            pady=22,
        )

        cards = tk.Frame(body, bg=COLORS["bg"])
        cards.pack(fill="x")

        for index in range(4):
            cards.grid_columnconfigure(index, weight=1)

        self.card_values = {}

        card_data = [
            ("TOTAL ITEMS", "0", "▣", COLORS["blue"], "total"),
            ("AVAILABLE UNITS", "0", "✓", COLORS["green"], "available"),
            ("LOW STOCK", "0", "!", COLORS["orange"], "low"),
            ("INVENTORY VALUE", "₱0.00", "₱", COLORS["purple"], "value"),
        ]

        for index, (title, value, icon, accent, key) in enumerate(card_data):
            card = tk.Frame(
                cards,
                bg="white",
                highlightbackground=COLORS["border"],
                highlightthickness=1,
            )
            card.grid(
                row=0,
                column=index,
                sticky="ew",
                padx=(0, 9) if index < 3 else 0,
            )

            tk.Frame(
                card,
                bg=accent,
                width=5,
            ).pack(side="left", fill="y")

            inside = tk.Frame(card, bg="white")
            inside.pack(
                fill="both",
                expand=True,
                padx=14,
                pady=12,
            )

            tk.Label(
                inside,
                text=icon,
                font=("Segoe UI", 18, "bold"),
                bg="white",
                fg=accent,
            ).pack(anchor="w")

            label = tk.Label(
                inside,
                text=value,
                font=("Segoe UI", 19, "bold"),
                bg="white",
                fg=COLORS["text"],
            )
            label.pack(anchor="w")

            self.card_values[key] = label

            tk.Label(
                inside,
                text=title,
                font=("Segoe UI", 8, "bold"),
                bg="white",
                fg=COLORS["muted"],
            ).pack(anchor="w")

        toolbar = tk.Frame(
            body,
            bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        toolbar.pack(fill="x", pady=18)

        self.search_var = tk.StringVar()

        self.search_entry = tk.Entry(
            toolbar,
            textvariable=self.search_var,
            font=("Segoe UI", 10),
            relief="flat",
            bg="#F8FAFC",
            fg=COLORS["text"],
        )
        self.search_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(14, 5),
            pady=10,
            ipady=8,
        )

        self.category_var = tk.StringVar(value="All")

        self.category_combo = ttk.Combobox(
            toolbar,
            textvariable=self.category_var,
            state="readonly",
            width=17,
        )
        self.category_combo.pack(
            side="left",
            padx=5,
            pady=10,
            ipady=6,
        )

        self._action_button(
            toolbar,
            "SEARCH",
            self.load_data,
            COLORS["blue"],
        )

        self._action_button(
            toolbar,
            "CLEAR",
            self.clear_filter,
            "#64748B",
        )

        self.btn_add = self._action_button(
            toolbar,
            "+ ADD",
            self.add_item,
            COLORS["green"],
        )

        self.btn_update = self._action_button(
            toolbar,
            "EDIT",
            self.update_item,
            COLORS["blue"],
        )

        self.btn_delete = self._action_button(
            toolbar,
            "DELETE",
            self.delete_item,
            COLORS["red"],
        )

        if self.role != "ADMIN":
            for button in (
                self.btn_add,
                self.btn_update,
                self.btn_delete,
            ):
                button.config(state="disabled")

        borrow_toolbar = tk.Frame(
            body,
            bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        borrow_toolbar.pack(fill="x", pady=(0, 18))

        self.btn_borrow = self._action_button(
            borrow_toolbar,
            "BORROW",
            self.borrow_item,
            COLORS["purple"],
        )

        self.btn_borrow_history = self._action_button(
            borrow_toolbar,
            "BORROW HISTORY",
            self.open_borrow_history,
            "#9333EA",
        )

        table_card = tk.Frame(
            body,
            bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        table_card.pack(
            fill="both",
            expand=True,
        )

        table_head = tk.Frame(
            table_card,
            bg="white",
        )
        table_head.pack(
            fill="x",
            padx=18,
            pady=(15, 7),
        )

        tk.Label(
            table_head,
            text="Equipment Inventory",
            font=("Segoe UI", 13, "bold"),
            bg="white",
            fg=COLORS["text"],
        ).pack(side="left")

        self.inventory_count = tk.Label(
            table_head,
            text="0 records",
            font=("Segoe UI", 8, "bold"),
            bg="#EFF6FF",
            fg=COLORS["blue"],
        )
        self.inventory_count.pack(
            side="right",
            padx=5,
            ipadx=8,
            ipady=4,
        )

        table_frame = tk.Frame(
            table_card,
            bg="white",
        )
        table_frame.pack(
            fill="both",
            expand=True,
            padx=14,
            pady=(0, 14),
        )

        columns = (
            "ID",
            "Name",
            "Category",
            "Qty",
            "Price (₱)",
            "Status",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Campus.Treeview",
            selectmode="browse",
        )

        widths = {
            "ID": 90,
            "Name": 340,
            "Category": 220,
            "Qty": 110,
            "Price (₱)": 170,
            "Status": 180,
        }

        for column in columns:
            self.tree.heading(
                column,
                text=column.upper(),
            )
            self.tree.column(
                column,
                width=widths[column],
                anchor=(
                    "w"
                    if column in {"Name", "Category"}
                    else "center"
                ),
            )

        scroll_y = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        scroll_x = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview,
        )
        self.tree.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True,
        )
        scroll_y.pack(
            side="right",
            fill="y",
        )
        scroll_x.pack(
            side="bottom",
            fill="x",
        )

        self.tree.tag_configure(
            "out_of_stock",
            foreground=COLORS["red"],
        )
        self.tree.tag_configure(
            "low_stock",
            foreground=COLORS["orange"],
        )
        self.tree.tag_configure(
            "in_stock",
            foreground=COLORS["green"],
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.on_row_select,
        )

        footer = tk.Frame(
            body,
            bg=COLORS["bg"],
        )
        footer.pack(
            fill="x",
            pady=(12, 0),
        )

        self.label_total = tk.Label(
            footer,
            text="Total Inventory Value: ₱0.00",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["muted"],
        )
        self.label_total.pack(side="left")

        tk.Label(
            footer,
            text="Auto-refresh: every 5 seconds",
            font=("Segoe UI", 8),
            bg=COLORS["bg"],
            fg=COLORS["muted"],
        ).pack(side="right")

        self.search_entry.bind(
            "<Return>",
            lambda event: self.load_data(),
        )

        self.root.bind(
            "<Control-f>",
            lambda event: self.search_entry.focus_set(),
        )

    @staticmethod
    def _action_button(parent, text, command, color):
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="white",
            activebackground=color,
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
        )
        button.pack(
            side="left",
            padx=3,
            pady=10,
            ipadx=8,
            ipady=8,
        )
        return button

    def _go_dashboard(self):
        self.content_canvas.yview_moveto(0)

    def _focus_inventory(self):
        self.content_canvas.yview_moveto(0)
        self.search_entry.focus_set()

    @staticmethod
    def _row_tag(status):
        return {
            "Out of Stock": "out_of_stock",
            "Low Stock": "low_stock",
            "In Stock": "in_stock",
        }.get(status, "")

    def load_data(self):
        try:
            rows = self.controller.fetch_all_items(
                self.search_var.get().strip(),
                self.category_var.get(),
            )

            for item in self.tree.get_children():
                self.tree.delete(item)

            categories = ["All"] + self.controller.fetch_categories()
            self.category_combo["values"] = categories

            if self.category_var.get() not in categories:
                self.category_var.set("All")

            for row in rows:
                item_id, name, category, qty, price, status = row

                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        item_id,
                        name,
                        category,
                        qty,
                        f"{price:,.2f}",
                        status,
                    ),
                    tags=(self._row_tag(status),),
                )

            total_value = self.controller.get_total_value()

            self.inventory_count.config(
                text=f"{len(rows)} records"
            )

            self.label_total.config(
                text=f"Total Inventory Value: ₱{total_value:,.2f}"
            )

            total_items = len(rows)
            available_units = sum(
                max(0, int(row[3]))
                for row in rows
            )
            low_stock = sum(
                1
                for row in rows
                if row[5] == "Low Stock"
            )

            self.card_values["total"].config(
                text=str(total_items)
            )
            self.card_values["available"].config(
                text=str(available_units)
            )
            self.card_values["low"].config(
                text=str(low_stock)
            )
            self.card_values["value"].config(
                text=f"₱{total_value:,.2f}"
            )

        except Exception as exc:
            logger.exception("Dashboard refresh error: %s", exc)

    def clear_filter(self):
        self.search_var.set("")
        self.category_var.set("All")
        self.load_data()

    def open_profile(self):
        ProfileWindow(
            self.root,
            self.username,
        )

    def open_approvals(self):
        if self.role == "ADMIN":
            AdminApprovalsWindow(
                self.root,
                self.username,
            )

    def open_borrow_history(self):
        from views.account_view import BorrowHistoryWindow
        BorrowHistoryWindow(self.root)

    def on_row_select(self, event=None):
        selected = self.tree.selection()

        if selected:
            values = self.tree.item(selected[0])["values"]
            self.selected_item_id = values[0]

    def _item_dialog(self, title, existing=None):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("510x420")
        dialog.configure(bg=COLORS["bg"])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text=title,
            font=("Segoe UI", 18, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(anchor="w", padx=30, pady=(25, 2))

        tk.Label(
            dialog,
            text="Enter accurate equipment information for the inventory database.",
            font=("Segoe UI", 9),
            bg=COLORS["bg"],
            fg=COLORS["muted"],
        ).pack(anchor="w", padx=30, pady=(0, 14))

        values = existing or ("", "", "", "")
        fields = {}

        for label, value in zip(
            ("Item Name", "Category", "Quantity", "Unit Price"),
            values,
        ):
            tk.Label(
                dialog,
                text=label.upper(),
                font=("Segoe UI", 8, "bold"),
                bg=COLORS["bg"],
                fg=COLORS["muted"],
            ).pack(anchor="w", padx=30, pady=(6, 3))

            entry = tk.Entry(
                dialog,
                font=("Segoe UI", 10),
                relief="solid",
                bd=1,
            )
            entry.insert(0, str(value))
            entry.pack(
                fill="x",
                padx=30,
                ipady=8,
            )

            fields[label] = entry

        def save():
            item_values = (
                fields["Item Name"].get().strip(),
                fields["Category"].get().strip(),
                fields["Quantity"].get().strip(),
                fields["Unit Price"].get().strip(),
            )

            if existing:
                success, msg = self.controller.update_item(
                    self.selected_item_id,
                    *item_values,
                )
            else:
                success, msg = self.controller.add_item(
                    *item_values,
                )

            if success:
                messagebox.showinfo(
                    "Success",
                    msg,
                    parent=dialog,
                )
                dialog.destroy()
                self.load_data()
            else:
                messagebox.showerror(
                    "Unable to Save",
                    msg,
                    parent=dialog,
                )

        tk.Button(
            dialog,
            text=(
                "SAVE CHANGES"
                if existing
                else "ADD EQUIPMENT"
            ),
            command=save,
            bg=COLORS["blue"] if existing else COLORS["green"],
            fg="white",
            activebackground=(
                COLORS["blue_hover"]
                if existing
                else "#15803D"
            ),
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
        ).pack(
            fill="x",
            padx=30,
            pady=18,
            ipady=10,
        )

    def add_item(self):
        if self.role != "ADMIN":
            return
        self._item_dialog("＋  ADD EQUIPMENT")

    def update_item(self):
        if self.role != "ADMIN":
            return

        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "Edit Equipment",
                "Select an equipment item from the table first.",
            )
            return

        values = self.tree.item(selected[0])["values"]

        self.selected_item_id = values[0]

        self._item_dialog(
            "✎  EDIT EQUIPMENT",
            existing=(
                values[1],
                values[2],
                values[3],
                values[4],
            ),
        )

    def delete_item(self):
        if self.role != "ADMIN":
            return

        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "Delete Equipment",
                "Select an equipment item from the table first.",
            )
            return

        selected_item = self.tree.item(selected[0])
        values = selected_item["values"]

        item_id = values[0]
        item_name = values[1]

        if not messagebox.askyesno(
            "Confirm Delete",
            (
                f"Delete '{item_name}' (ID {item_id})?\n\n"
                "This action cannot be undone."
            ),
        ):
            return

        success, msg = self.controller.delete_item(item_id)

        if success:
            messagebox.showinfo("Deleted", msg)
            self.selected_item_id = None
            self.load_data()
        else:
            messagebox.showerror(
                "Delete Failed",
                msg,
            )

    def borrow_item(self):
        selected = self.tree.selection()
        default_item_id = self.tree.item(selected[0])["values"][0] if selected else ""

        dialog = tk.Toplevel(self.root)
        dialog.title("Borrow Equipment")
        dialog.geometry("480x520")
        dialog.configure(bg=COLORS["bg"])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="Borrow Item",
            font=("Segoe UI", 18, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(anchor="w", padx=28, pady=(22, 2))

        tk.Label(
            dialog,
            text="Record student borrow details for equipment checkout.",
            font=("Segoe UI", 9),
            bg=COLORS["bg"],
            fg=COLORS["muted"],
        ).pack(anchor="w", padx=28, pady=(0, 12))

        fields = {}
        default_due_date = (date.today() + timedelta(days=14)).strftime("%Y-%m-%d")

        labels = (
            ("Student Name", ""),
            ("Student ID", ""),
            ("Item ID", str(default_item_id)),
            ("Quantity", "1"),
            ("Pay by Date", default_due_date),
        )

        for label, value in labels:
            tk.Label(
                dialog,
                text=label.upper(),
                font=("Segoe UI", 8, "bold"),
                bg=COLORS["bg"],
                fg=COLORS["muted"],
            ).pack(anchor="w", padx=28, pady=(8, 3))

            entry = tk.Entry(
                dialog,
                font=("Segoe UI", 10),
                relief="solid",
                bd=1,
            )
            entry.insert(0, value)
            entry.pack(fill="x", padx=28, ipady=8)
            fields[label] = entry

        def save_borrow():
            student_name = fields["Student Name"].get().strip()
            student_id = fields["Student ID"].get().strip()
            item_id = fields["Item ID"].get().strip()
            quantity = fields["Quantity"].get().strip()
            pay_by_date = fields["Pay by Date"].get().strip()

            success, msg = self.controller.borrow_item(
                student_name,
                student_id,
                item_id,
                quantity,
                pay_by_date,
            )

            if success:
                messagebox.showinfo("Borrow Request Sent", msg, parent=dialog)
                dialog.destroy()
                self.load_data()
            else:
                messagebox.showerror("Borrow Failed", msg, parent=dialog)

        tk.Button(
            dialog,
            text="SAVE BORROW RECORD",
            command=save_borrow,
            bg=COLORS["purple"],
            fg="white",
            activebackground="#6D28D9",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
        ).pack(fill="x", padx=28, pady=(20, 18), ipady=10)

    def handle_export(self):
        success, msg = self.controller.export_to_csv()

        if success:
            messagebox.showinfo(
                "Export Complete",
                msg,
            )
        else:
            messagebox.showerror(
                "Export Failed",
                msg,
            )

    def handle_logout(self):
        if not messagebox.askyesno(
            "Confirm Logout",
            f"Are you sure you want to log out, {self.username}?",
        ):
            return

        logger.info(
            "User Logged Out: '%s'",
            self.username,
        )

        if callable(self.on_logout):
            self.on_logout()

    def auto_refresh(self):
        try:
            self.load_data()
        except Exception as exc:
            logger.exception(
                "Auto-refresh error: %s",
                exc,
            )

        self.root.after(
            5000,
            self.auto_refresh,
        )
