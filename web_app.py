from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
    flash,
)
from controller.tracker_controller import HardwareAuthController
from controller.hardware_controller import HardwareController
from models.database import init_hardware_db
import io
import csv
import os
import shutil


app = Flask(__name__)
app.secret_key = "replace-with-a-secure-random-key"

# Initialize the database at import time (compatible with Flask 3)
db_name = "hardware_inventory.db"
init_hardware_db(db_name=db_name)
if os.path.exists(db_name):
    bak = f"{db_name}.bak"
    try:
        shutil.copyfile(db_name, bak)
    except Exception:
        pass


def current_user():
    return session.get("user")


@app.route("/")
def index():
    if current_user():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    auth = HardwareAuthController()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        selected_role = request.form.get("role", "USER").upper()
        success, result = auth.login(username, password)
        if success:
            # Verify that the account's role matches the selected login role
            account_role = str(result.get("role", "USER")).upper()
            if account_role != selected_role:
                flash("Selected role does not match this account's role.", "danger")
                return render_template("login.html")

            session["user"] = result
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))
        flash(result, "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    auth = HardwareAuthController()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        success, msg = auth.register(username, password, email=email, role="USER")
        flash(msg, "success" if success else "danger")
        if success:
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/reset", methods=["GET", "POST"])
def reset_unlock():
    auth = HardwareAuthController()
    # Determine if this is an unlock-only request (admins will use this)
    unlock = request.args.get("unlock") in ("1", "true", "True")

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if unlock:
            success, msg = auth.request_password_reset(email, None)
        else:
            new_password = request.form.get("new_password", "")
            success, msg = auth.request_password_reset(email, new_password)

        flash(msg, "success" if success else "danger")
        if success:
            return redirect(url_for("login"))

    return render_template("reset.html", unlock=unlock)


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    hc = HardwareController()
    search = request.args.get("search", "")
    category = request.args.get("category", "All")
    items = hc.fetch_all_items(search=search, category=category)
    categories = ["All"] + hc.fetch_categories()
    # Replace total asset valuation with total stocks (sum of quantities)
    total_stocks = sum(int(row[3]) for row in items)

    # Borrowed items: show all for admin, otherwise show items matching username
    borrow_rows = hc.fetch_borrowed_items()
    if user.get("role") != "ADMIN":
        borrow_rows = [r for r in borrow_rows if str(r[2]) == str(user.get("username")) or str(r[1]) == str(user.get("username"))]

    return render_template(
        "dashboard.html",
        user=user,
        items=items,
        categories=categories,
        selected_category=category,
        total_stocks=total_stocks,
        borrow_rows=borrow_rows,
    )


@app.route("/borrow", methods=["POST"])
def borrow():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    hc = HardwareController()
    student_name = request.form.get("student_name")
    student_id = request.form.get("student_id")
    item_id = request.form.get("item_id")
    quantity = request.form.get("quantity")
    pay_by = request.form.get("repayment_due_date")

    success, msg = hc.borrow_item(student_name, student_id, item_id, quantity, pay_by)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("dashboard"))


@app.route("/borrow/request_return", methods=["POST"])
def request_return():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    borrow_id = request.form.get("borrow_id")
    qty = request.form.get("return_quantity")
    hc = HardwareController()
    success, msg = hc.request_return(borrow_id, qty)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("dashboard"))


@app.route("/export")
def export():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    hc = HardwareController()
    rows = hc.fetch_all_items()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Category", "Quantity", "Unit Price", "Status"])
    writer.writerows(rows)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="hardware_inventory_report.csv",
    )


@app.route("/admin/approvals")
def admin_approvals():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if user.get("role") != "ADMIN":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    auth = HardwareAuthController()
    requests = auth.get_reset_requests()
    borrow_rows = auth.get_borrow_requests()
    hc = HardwareController()
    return_rows = hc.get_return_requests()

    # Summary metrics for admin dashboard
    hc = HardwareController()
    items = hc.fetch_all_items()
    total_stocks = sum(int(row[3]) for row in items)
    total_borrowed = len([b for b in auth.get_borrow_requests() if b[8] == 'APPROVED'])

    return render_template(
        "admin.html",
        requests=requests,
        borrow_rows=borrow_rows,
        total_stocks=total_stocks,
        total_borrowed=total_borrowed,
        return_rows=return_rows,
    )


@app.route("/admin/review/<int:request_id>", methods=["POST"])
def admin_review(request_id):
    user = current_user()
    if not user or user.get("role") != "ADMIN":
        return redirect(url_for("login"))
    approve = request.form.get("action") == "approve"
    auth = HardwareAuthController()
    success, msg = auth.review_reset_request(request_id, user.get("username"), approve)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("admin_approvals"))


@app.route("/admin/borrow/<int:borrow_id>/approve", methods=["POST"])
def admin_approve_borrow(borrow_id):
    user = current_user()
    if not user or user.get("role") != "ADMIN":
        return redirect(url_for("login"))
    auth = HardwareAuthController()
    success, msg = auth.approve_borrow_request(borrow_id, user.get("username"))
    flash(msg, "success" if success else "danger")
    return redirect(url_for("admin_approvals"))


@app.route("/admin/borrow/<int:borrow_id>/reject", methods=["POST"])
def admin_reject_borrow(borrow_id):
    user = current_user()
    if not user or user.get("role") != "ADMIN":
        return redirect(url_for("login"))
    auth = HardwareAuthController()
    success, msg = auth.reject_borrow_request(borrow_id, user.get("username"))
    flash(msg, "success" if success else "danger")
    return redirect(url_for("admin_approvals"))


@app.route("/admin/return/<int:return_id>/approve", methods=["POST"])
def admin_approve_return(return_id):
    user = current_user()
    if not user or user.get("role") != "ADMIN":
        return redirect(url_for("login"))
    hc = HardwareController()
    success, msg = hc.review_return_request(return_id, user.get("username"), True)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("admin_approvals"))


@app.route("/admin/return/<int:return_id>/reject", methods=["POST"])
def admin_reject_return(return_id):
    user = current_user()
    if not user or user.get("role") != "ADMIN":
        return redirect(url_for("login"))
    hc = HardwareController()
    success, msg = hc.review_return_request(return_id, user.get("username"), False)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("admin_approvals"))


@app.route("/admin/return/mark/<int:borrow_id>", methods=["POST"])
def admin_mark_return(borrow_id):
    user = current_user()
    if not user or user.get("role") != "ADMIN":
        return redirect(url_for("login"))

    qty = request.form.get("return_quantity")
    hc = HardwareController()
    success, msg = hc.admin_mark_return(borrow_id, qty, user.get("username"))
    flash(msg, "success" if success else "danger")
    return redirect(url_for("admin_approvals"))


@app.route("/items/add", methods=["POST"])
def add_item():
    user = current_user()
    if not user or user.get("role") != "ADMIN":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))
    name = request.form.get("name")
    category = request.form.get("category")
    quantity = request.form.get("quantity")
    price = request.form.get("price")
    hc = HardwareController()
    success, msg = hc.add_item(name, category, quantity, price)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("dashboard"))


@app.route("/items/update/<int:item_id>", methods=["POST"])
def update_item(item_id):
    user = current_user()
    if not user or user.get("role") != "ADMIN":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))
    name = request.form.get("name")
    category = request.form.get("category")
    quantity = request.form.get("quantity")
    price = request.form.get("price")
    hc = HardwareController()
    success, msg = hc.update_item(item_id, name, category, quantity, price)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("dashboard"))


@app.route("/items/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    user = current_user()
    if not user or user.get("role") != "ADMIN":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))
    hc = HardwareController()
    success, msg = hc.delete_item(item_id)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("dashboard"))


@app.route("/borrow/history")
def borrow_history():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    hc = HardwareController()
    rows = hc.fetch_borrowed_items()
    return render_template("borrow_history.html", rows=rows, user=user)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    auth = HardwareAuthController()
    if request.method == "POST":
        current = request.form.get("current_password")
        new = request.form.get("new_password")
        success, msg = auth.change_password(user.get("username"), current, new)
        flash(msg, "success" if success else "danger")
        return redirect(url_for("profile"))

    profile = auth.get_profile(user.get("username"))
    return render_template("profile.html", profile=profile)


def run_flask(debug: bool = False, host: str = "127.0.0.1", port: int = 5000):
    """Run the Flask web server. Call explicitly if you want the web UI.

    The project primary entrypoint is `main.py` which launches the Tkinter
    desktop application. This helper lets you run the Flask server manually
    when needed (for the optional web interface).
    """
    # Configure simple file logging for diagnostics
    import logging
    from logging.handlers import RotatingFileHandler

    log_path = os.path.join(os.path.dirname(__file__), "logs")
    try:
        os.makedirs(log_path, exist_ok=True)
    except Exception:
        pass

    fh = RotatingFileHandler(os.path.join(log_path, "web_app.log"), maxBytes=5_000_000, backupCount=3)
    fh.setLevel(logging.DEBUG if debug else logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    fh.setFormatter(formatter)
    if not app.logger.handlers:
        app.logger.addHandler(fh)

    # Run without the reloader to avoid double-process issues in some environments
    app.run(host=host, port=port, debug=debug, use_reloader=False)


# simple health endpoint for diagnostics
@app.route('/_ping')
def _ping():
    return 'ok', 200
