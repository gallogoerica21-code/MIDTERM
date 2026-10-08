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
- Supabase PostgreSQL support for shared web-app data
- Application logging
- Dashboard and approval pages refresh when shared data changes (checked every 5 seconds)

## Role access

- Regular users can browse inventory and submit borrow and return requests.
- Regular users can view only borrow records submitted through their own account; inventory prices, aggregate totals, and CSV export are reserved for administrators.
- Administrators can review requests, manage inventory, view all borrow records, and export inventory data.
- Borrow records created before account ownership tracking was added remain visible to administrators only.

Set `FLASK_SECRET_KEY` to a persistent random value if login sessions should survive web-server restarts. Without it, a fresh random session key is generated when the server starts.

## Supabase setup

The Flask app can use a shared Supabase PostgreSQL database. **If a database password has been shared in chat, reset it in Supabase before connecting.** Never commit or share the connection string. Keep the database connection string server-side; never expose it in browser code. App tables have row-level security enabled so the public Supabase API cannot read them without an explicit policy.

1. Install the project dependencies with `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env` and set `SUPABASE_DB_URL` using the newly reset password. URL-encode any reserved characters in the password. `.env` is ignored by Git.
3. To copy the existing local SQLite users, inventory, borrow/return requests, and password-reset requests, run `python -m scripts.migrate_sqlite_to_supabase`. The migration stops if any destination table already contains data.
4. Run the Flask app with `python web_app.py`. When `SUPABASE_DB_URL` is set, the web app and controllers use Supabase; without it, they continue to use the local SQLite database.

The dashboard and admin approvals page check for shared database changes every five seconds and reload when displayed data changes. This is near-real-time polling, not a Supabase Realtime WebSocket subscription.

## Deploy to Render

This repository includes a Render Blueprint (`render.yaml`) for the Flask web app. In Render, create a new Blueprint and select this GitHub repository and the `master` branch. Before deploying, set the `SUPABASE_DB_URL` secret environment variable on the Render service to the Supabase Session pooler URL; do not commit `.env` or paste database credentials into chat. The Blueprint generates a persistent `FLASK_SECRET_KEY`, installs `requirements.txt`, starts Gunicorn on Render's assigned port, and uses `/_ping` as its health check. Automatic deploys are enabled for new commits to `master`.

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
