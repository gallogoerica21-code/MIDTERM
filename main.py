import os
import sys
import tkinter as tk
import argparse
import subprocess
import webbrowser
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logger import logger
from models.database import init_hardware_db
from views.login_view import HardwareLoginWindow
from views.tracker_view import HardwareTrackerWindow


def launch_main_app(username="Unknown", role="USER"):
    """Replace the login screen with the authenticated dashboard."""
    for widget in root.winfo_children():
        widget.destroy()

    root.geometry("1400x850")
    root.minsize(1120, 700)
    root.resizable(True, True)

    HardwareTrackerWindow(
        root,
        username=username,
        role=role,
        on_logout=launch_login,
    )


def launch_login():
    """Return to the professional login screen."""
    for widget in root.winfo_children():
        widget.destroy()

    root.geometry("1000x620")
    root.minsize(900, 560)
    root.resizable(True, True)

    HardwareLoginWindow(
        root,
        on_login_success=launch_main_app,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--web", action="store_true", help="Run the Flask web UI instead of the Tkinter desktop UI")
    args = parser.parse_args()

    init_hardware_db()

    if args.web:
        # Launch the Flask helper as a subprocess so it runs in the project's venv
        python_exe = sys.executable
        run_script = os.path.join(os.path.dirname(__file__), "scripts", "run_flask.py")
        logger.info("Starting web server using %s %s", python_exe, run_script)
        proc = subprocess.Popen([python_exe, run_script], cwd=os.path.dirname(__file__))
        # give server a moment to start then open browser
        time.sleep(0.8)
        try:
            webbrowser.open("http://127.0.0.1:5000")
        except Exception:
            pass
        logger.info("Web UI started (pid=%s).", proc.pid)
        proc.wait()
    else:
        root = tk.Tk()
        root.title("Campus Hardware Inventory")
        root.protocol("WM_DELETE_WINDOW", root.destroy)

        logger.info("Campus Hardware Inventory application started (desktop).")
        launch_login()
        root.mainloop()
