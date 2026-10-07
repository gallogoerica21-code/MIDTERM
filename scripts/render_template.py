from web_app import app
from flask import render_template

with app.app_context():
    try:
        html = render_template('login.html')
        print('LENGTH', len(html))
        print(html[:2000])
    except Exception as e:
        print('ERROR', repr(e))