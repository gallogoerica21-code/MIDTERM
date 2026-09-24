import tkinter as tk
from tkinter import messagebox, ttk

from controller.tracker_controller import HardwareAuthController


COLORS = {
    "navy": "#172554",
    "blue": "#2563EB",
    "blue_hover": "#1D4ED8",
    "green": "#16A34A",
    "orange": "#EA580C",
    "bg": "#F4F7FB",
    "text": "#111827",
    "muted": "#64748B",
    "border": "#E2E8F0",
    "card": "#FFFFFF",
    "panel": "#F8FAFC",
    "brand": "#172554",
    "brand_text": "#CBD5E1",
    "brand_accent": "#93C5FD",
    "button_text": "#FFFFFF",
}

THEMES = {
    "light": {
        "navy": "#172554",
        "blue": "#2563EB",
        "blue_hover": "#1D4ED8",
        "green": "#16A34A",
        "orange": "#EA580C",
        "bg": "#F4F7FB",
        "text": "#111827",
        "muted": "#64748B",
        "border": "#E2E8F0",
        "card": "#FFFFFF",
        "panel": "#F8FAFC",
        "brand": "#172554",
        "brand_text": "#CBD5E1",
        "brand_accent": "#93C5FD",
        "button_text": "#FFFFFF",
    },
    "dark": {
        "navy": "#0F172A",
        "blue": "#60A5FA",
        "blue_hover": "#3B82F6",
        "green": "#34D399",
        "orange": "#F59E0B",
        "bg": "#0B1120",
        "text": "#E2E8F0",
        "muted": "#9CA3AF",
        "border": "#1F2937",
        "card": "#111827",
        "panel": "#0F172A",
        "brand": "#020817",
        "brand_text": "#E2E8F0",
        "brand_accent": "#93C5FD",
        "button_text": "#0F172A",
    },
}


class HardwareLoginWindow:
    """Professional login and registration screen."""

    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.auth = HardwareAuthController()
        self.theme = "light"

        self.root.title("Campus Hardware Inventory | Secure Access")
        self.root.geometry("1000x620")
        self.root.minsize(900, 560)
        self.root.configure(bg=COLORS["bg"])

        self._build()

    def _build(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # LEFT: Branding
        brand = tk.Canvas(self.root, highlightthickness=0, bg=COLORS["navy"], height=600)
        brand.grid(row=0, column=0, sticky="nsew")
        # subtle gradient-like accent using overlapping rectangles
        for i in range(6):
            color = COLORS["brand_accent"]
            brand.create_rectangle(0, i * 100, 500, (i + 1) * 100, fill=color, outline=color, stipple="gray12")

        brand_frame = tk.Frame(self.root, bg=COLORS["navy"]) 
        brand.create_window(250, 220, window=brand_frame, width=420, height=400)

        tk.Label(
            brand_frame,
            text="🎓",
            font=("Segoe UI Emoji", 56),
            bg=COLORS["navy"],
            fg="white",
        ).pack(pady=(10, 8))

        tk.Label(
            brand_frame,
            text="CAMPUS HARDWARE",
            font=("Segoe UI", 25, "bold"),
            bg=COLORS["navy"],
            fg="white",
        ).pack()

        tk.Label(
            brand_frame,
            text="INVENTORY MANAGEMENT SYSTEM",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["navy"],
            fg="#93C5FD",
        ).pack(pady=(4, 18))

        tk.Label(
            brand_frame,
            text=(
                "Track equipment, manage campus resources,\n"
                "and maintain a reliable inventory record."
            ),
            font=("Segoe UI", 11),
            justify="center",
            bg=COLORS["navy"],
            fg="#CBD5E1",
        ).pack()

        tk.Frame(
            brand_frame,
            bg="#334155",
            height=1,
        ).pack(fill="x", padx=40, pady=28)

        tk.Label(
            brand_frame,
            text="SECURE  •  ORGANIZED  •  ACCOUNTABLE",
            font=("Segoe UI", 8, "bold"),
            bg=COLORS["navy"],
            fg="#94A3B8",
        ).pack()

        # RIGHT: Authentication
        panel = tk.Frame(self.root, bg=COLORS["bg"])
        panel.grid(row=0, column=1, sticky="nsew")

        card = tk.Frame(
            panel,
            bg=COLORS["card"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            bd=0,
        )
        card.pack(fill="both", expand=True, padx=45, pady=38)

        # subtle drop shadow (simulate with border color)
        # removed stacked frame shadow which caused rendering artifacts

        tk.Label(
            card,
            text="Welcome back",
            font=("Segoe UI", 24, "bold"),
            bg=COLORS["card"],
            fg=COLORS["text"],
        ).pack(anchor="w", padx=35, pady=(30, 2))

        tk.Label(
            card,
            text="Sign in or create an account to continue.",
            font=("Segoe UI", 10),
            bg=COLORS["card"],
            fg=COLORS["muted"],
        ).pack(anchor="w", padx=35, pady=(0, 16))

        self._field(card, "USERNAME", "entry_user")
        self._field(card, "EMAIL", "entry_email")
        self._field(card, "PASSWORD", "entry_pass", secret=True)

        role_row = tk.Frame(card, bg=COLORS["card"])
        role_row.pack(fill="x", padx=35, pady=(12, 3))

        tk.Label(
            role_row,
            text="ACCOUNT ROLE",
            font=("Segoe UI", 8, "bold"),
            bg="white",
            fg=COLORS["muted"],
        ).pack(anchor="w")

        self.role_var = tk.StringVar(value="USER")
        role_buttons = tk.Frame(role_row, bg=COLORS["card"])
        role_buttons.pack(fill="x", pady=(6, 0))

        self.role_buttons = {}
        for role in ("USER", "ADMIN"):
            btn = tk.Button(
                role_buttons,
                text=role,
                width=12,
                relief="flat",
                bd=0,
                cursor="hand2",
                font=("Segoe UI", 9, "bold"),
                command=lambda selected=role: self.set_role(selected),
            )
            btn.pack(side="left", padx=(0, 8))
            self.role_buttons[role] = btn

        self.update_role_buttons()

        self.show_password_var = tk.BooleanVar(value=False)

        tk.Checkbutton(
            card,
            text="Show password",
            variable=self.show_password_var,
            command=self._toggle_password,
            bg=COLORS["card"],
            fg=COLORS["muted"],
            activebackground=COLORS["card"],
            selectcolor=COLORS["card"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=32, pady=(4, 7))

        buttons = tk.Frame(card, bg=COLORS["card"])
        buttons.pack(fill="x", padx=35, pady=(8, 5))

        tk.Button(
            buttons,
            text="SIGN IN  →",
            command=self.handle_login,
            bg=COLORS["blue"],
            fg="white",
            activebackground=COLORS["blue_hover"],
            activeforeground="white",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        )
        sign_in_btn = buttons.winfo_children()[-1]
        sign_in_btn.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=10,
            padx=(0, 5),
        )
        self._add_hover(sign_in_btn, enter_bg=COLORS["blue_hover"], leave_bg=COLORS["blue"], enter_fg="white", leave_fg="white")

        create_btn = tk.Button(
            buttons,
            text="CREATE ACCOUNT",
            command=self.handle_register,
            bg=COLORS["green"],
            fg="white",
            activebackground="#15803D",
            activeforeground="white",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        )
        create_btn.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=10,
            padx=(5, 0),
        )
        self._add_hover(create_btn, enter_bg="#15803D", leave_bg=COLORS["green"], enter_fg="white", leave_fg="white")

        reset_btn = tk.Button(
            card,
            text="Reset / Unlock Password",
            command=self.open_reset_dialog,
            bg=COLORS["card"],
            fg=COLORS["blue"],
            activebackground=COLORS["card"],
            activeforeground=COLORS["blue_hover"],
            relief="flat",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )
        reset_btn.pack(pady=(7, 8))
        self._add_hover(reset_btn, enter_bg=COLORS["panel"], leave_bg=COLORS["card"], enter_fg=COLORS["blue_hover"], leave_fg=COLORS["blue"]) 

        toggle_label = "🌙 DARK MODE" if self.theme == "light" else "☀️ LIGHT MODE"
        theme_btn = tk.Button(
            card,
            text=toggle_label,
            command=self.toggle_theme,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            activebackground=COLORS["border"],
            activeforeground=COLORS["text"],
            relief="flat",
            bd=1,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )
        theme_btn.pack(pady=(0, 22))
        self._add_hover(theme_btn, enter_bg=COLORS["border"], leave_bg=COLORS["panel"], enter_fg=COLORS["text"], leave_fg=COLORS["text"]) 

        self.entry_user.focus_set()
        self.entry_user.bind("<Return>", lambda event: self.handle_login())
        self.entry_pass.bind("<Return>", lambda event: self.handle_login())

    def _field(self, parent, label, attribute, secret=False):
        tk.Label(
            parent,
            text=label,
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["card"],
            fg=COLORS["muted"],
        ).pack(fill="x", padx=35, pady=(7, 3))

        entry = tk.Entry(
            parent,
            font=("Segoe UI", 11),
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            show="*" if secret else "",
        )
        entry.pack(fill="x", padx=35, ipady=10, pady=(0, 6))
        setattr(self, attribute, entry)

    def set_role(self, role):
        self.role_var.set(role)
        self.update_role_buttons()

    def update_role_buttons(self):
        selected = self.role_var.get()
        for role, button in self.role_buttons.items():
            is_selected = role == selected
            button.configure(
                bg=(COLORS["blue"] if is_selected else COLORS["panel"]),
                fg=(COLORS["button_text"] if is_selected else COLORS["text"]),
                activebackground=(COLORS["blue_hover"] if is_selected else COLORS["border"]),
                activeforeground=(COLORS["button_text"] if is_selected else COLORS["text"]),
            )
            # add hover feedback to role buttons
            self._add_hover(button, enter_bg=COLORS["blue_hover"] if is_selected else COLORS["border"], leave_bg=(COLORS["blue"] if is_selected else COLORS["panel"]), enter_fg=COLORS["button_text"], leave_fg=(COLORS["button_text"] if is_selected else COLORS["text"]))

    def toggle_theme(self):
        global COLORS
        self.theme = "dark" if self.theme == "light" else "light"
        COLORS = THEMES[self.theme]
        self.root.configure(bg=COLORS["bg"])
        self._build()

    def _add_hover(self, widget, enter_bg=None, leave_bg=None, enter_fg=None, leave_fg=None):
        def on_enter(e):
            try:
                if enter_bg:
                    widget.configure(bg=enter_bg)
                if enter_fg:
                    widget.configure(fg=enter_fg)
            except Exception:
                pass

        def on_leave(e):
            try:
                if leave_bg:
                    widget.configure(bg=leave_bg)
                if leave_fg:
                    widget.configure(fg=leave_fg)
            except Exception:
                pass

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def handle_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get()

        success, result = self.auth.login(username, password)

        if success:
            messagebox.showinfo(
                "Login Successful",
                f"Welcome, {result['username']}!",
            )
            self.on_login_success(
                result["username"],
                result["role"],
            )
        else:
            messagebox.showerror("Login Failed", result)

    def handle_register(self):
        success, msg = self.auth.register(
            self.entry_user.get().strip(),
            self.entry_pass.get(),
            self.entry_email.get().strip(),
            self.role_var.get(),
        )

        if success:
            messagebox.showinfo(
                "Registration Successful",
                msg,
            )
            self.entry_pass.delete(0, tk.END)
        else:
            messagebox.showerror(
                "Registration Alert",
                msg,
            )

    def open_reset_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Reset / Unlock Password")
        dialog.geometry("430x300")
        dialog.configure(bg=COLORS["bg"])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="🔑  RESET / UNLOCK",
            font=("Segoe UI", 17, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(anchor="w", padx=28, pady=(24, 2))

        tk.Label(
            dialog,
            text="Submit a new-password request for administrator approval.",
            font=("Segoe UI", 9),
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            wraplength=360,
            justify="left",
        ).pack(anchor="w", padx=28, pady=(0, 14))

        tk.Label(
            dialog,
            text="REGISTERED EMAIL",
            font=("Segoe UI", 8, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["muted"],
        ).pack(anchor="w", padx=28, pady=(4, 3))

        email = tk.Entry(
            dialog,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
        )
        email.pack(fill="x", padx=28, ipady=7)

        tk.Label(
            dialog,
            text="NEW PASSWORD",
            font=("Segoe UI", 8, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["muted"],
        ).pack(anchor="w", padx=28, pady=(9, 3))

        password = tk.Entry(
            dialog,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
            show="*",
        )
        password.pack(fill="x", padx=28, ipady=7)

        def submit():
            success, msg = self.auth.request_password_reset(
                email.get().strip(),
                password.get(),
            )

            (messagebox.showinfo if success else messagebox.showerror)(
                "Password Reset",
                msg,
                parent=dialog,
            )

            if success:
                dialog.destroy()

        tk.Button(
            dialog,
            text="SUBMIT REQUEST",
            command=submit,
            bg=COLORS["orange"],
            fg="white",
            activebackground="#C2410C",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
        ).pack(fill="x", padx=28, pady=17, ipady=9)

    def _toggle_password(self):
        self.entry_pass.config(
            show="" if self.show_password_var.get() else "*"
        )
