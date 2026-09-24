import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from web_app import app

with app.test_client() as c:
    r = c.get('/login')
    print('STATUS', r.status_code)
    txt = r.get_data(as_text=True)
    print('LENGTH', len(txt))
    print(txt[:2000])
