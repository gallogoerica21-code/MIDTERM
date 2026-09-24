import os
import sys

# Ensure project root is on sys.path so imports like `web_app` resolve
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from web_app import run_flask


if __name__ == "__main__":
    run_flask(debug=True, host="127.0.0.1", port=5000)
