from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def get_data():
    conn = sqlite3.connect('main.sqlite')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    data = c.fetchall()
    conn.close()
    return data

@app.route('/Sites/websites/thanos/thanos.html')
def index():
    data = get_data()
    return render_template('thanos.html', data=data)

if __name__ == "__main__":
    app.run()