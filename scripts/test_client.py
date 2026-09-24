from web_app import app

with app.test_client() as c:
    rv = c.get('/login')
    print('STATUS', rv.status_code)
    data = rv.get_data(as_text=True)
    print('LENGTH', len(data))
    print(data[:400])
