import telnetlib
from flask import Flask, request
import datetime
#from pytz import timezone
#import time
import sqlite3

app = Flask(__name__)

@app.route('/')
def index():
    return '<h2>Hello Flask+uWSGI+Nginx</h2>'

@app.route('/api/post', methods=["POST"])
def post_data():
    place = request.args.get("place")
    temperature = request.args.get("temperature")
    humidity = request.args.get("humidity")

    now = datetime.datetime.utcnow()
    tm = now.strftime('%Y/%m/%d %H:%M:%S')

    conn = sqlite3.connect('temperature.sqlite3')
    conn.execute("CREATE TABLE IF NOT EXISTS data(id INTEGER PRIMARY KEY AUTOINCREMENT, time STRING, place STRING, temperature REAL, humidity REAL)")
    cur = conn.cursor()
    sql = 'INSERT INTO data(time, place, temperature, humidity) values(?, ?, ?, ?)'
    data = [tm, place, temperature, humidity]
    cur.execute(sql, data)
    conn.commit()
    conn.close()

    return "time:" + tm + ", place:" + place + ", temperature:" + temperature + ", humidity:" + humidity

if __name__ == "__main__":
    # app.run(host='0.0.0.0')
    app.run(debug=True)
