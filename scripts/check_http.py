import sys
import requests

try:
    r = requests.get('http://127.0.0.1:5000', timeout=5)
    print('STATUS', r.status_code)
    txt = r.text
    print('LENGTH:', len(txt))
    print(txt[:2000])
except Exception as e:
    print('ERROR', repr(e))
    sys.exit(2)
