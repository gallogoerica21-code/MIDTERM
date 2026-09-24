# Campus Hardware Inventory Management System

## Project structure

```text
campus_hardware_complete/
├── main.py
├── logger.py
├── hardware_inventory.db       # created automatically
├── hardware_inventory_report.csv  # created when exporting
├── app_logging/
│   └── app.log                 # created automatically
├── controller/
│   ├── __init__.py
│   ├── auth_controller.py
│   ├── hardware_controller.py
│   └── tracker_controller.py
├── models/
│   ├── __init__.py
│   ├── database.py
│   └── schemas.py
└── views/
    ├── __init__.py
    ├── account_view.py
    ├── login_view.py
    └── tracker_view.py
```

## Requirements

Python 3.10+ recommended.

Install Pydantic:

```bash
pip install pydantic
```

## Run

Open this folder in VS Code, then open the VS Code terminal and run:

```bash
To run the original Tkinter desktop app:

```bash
python main.py
```

To run the new Flask web interface (keeps original code untouched):

```bash
pip install -r requirements.txt
python web_app.py
```

Example portal message printed by `web_app.py`:

```
=============================================================
CAMPUS HARDWARE INVENTORY - WEB PORTAL
=============================================================

Open Google Chrome and go to:
http://127.0.0.1:5000

Press CTRL+C to stop the server.
```

## Important

Run `main.py` from the project root. Do NOT open or run `views/tracker_view.py` by itself.

The professional interface includes:

- Two-panel secure login/register screen
- Sidebar navigation
- Dashboard summary cards
- Search and category filters
- Professional Treeview inventory table
- Admin-only Add/Edit/Delete controls
- User profile and password change
- Admin password-reset approvals
- CSV export
- Login lockout after three failed attempts
- Password hashing with PBKDF2-HMAC-SHA256
- SQLite database
- Application logging
- Automatic dashboard refresh

## Deliverables created by this conversion

- Original desktop Python source preserved (do not delete `views/` or `main.py`).
- A backup of the SQLite database is created at startup as `hardware_inventory.db.bak`.
- Flask bridge: `web_app.py` (new) — uses existing controllers and DB.
- HTML templates: `templates/` (login, dashboard, profile, admin, borrow_history).
- Static CSS: `static/styles.css`.
- `requirements.txt` updated for the web bridge.

## Testing checklist (quick)

- Application starts without syntax errors: `python web_app.py`.
- Open Chrome at: http://127.0.0.1:5000 and confirm pages load.
- Login works with existing users; invalid login displays messages.
- Users can submit borrow requests with quantities (must be whole number and <= available stock when approved by admin).
- Admin can view pending borrow requests and approve/reject them; approval reduces stock.
- Users can request returns; admin approval restores stock.
- CSV export available via the Export link.
