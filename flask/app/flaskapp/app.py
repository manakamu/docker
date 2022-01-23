import telnetlib
from flask import Flask, request, render_template
import datetime
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

    date = u"{0:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())

    conn = sqlite3.connect('temperature.sqlite3')
    conn.execute("CREATE TABLE IF NOT EXISTS data(id INTEGER PRIMARY KEY AUTOINCREMENT, time STRING, place STRING, temperature REAL, humidity REAL)")
    cur = conn.cursor()
    sql = 'INSERT INTO data(time, place, temperature, humidity) values(?, ?, ?, ?)'
    data = [date, place, temperature, humidity]
    cur.execute(sql, data)
    conn.commit()
    conn.close()

    return "time:" + date + ", place:" + place + ", temperature:" + temperature + ", humidity:" + humidity

@app.route('/dht11', methods=["GET"])
def get_dht11():
    conn = sqlite3.connect('temperature.sqlite3')
    cur = conn.cursor()
    sql = "SELECT datetime(time, 'localtime'), place, temperature, humidity FROM data WHERE datetime(time, 'localtime') > datetime('now', 'localtime', '-24 hour')"
    
    label_list = list()
    temperature_list = list()
    humidity_list = list()
    all = list()
    counter = 0    
    for element in cur.execute(sql):
        """
        if counter % 6 == 0:
            label_list.append(element[0])
        else:
            label_list.append('')
        """
        label_list.append(counter)
        temperature_list.append(element[2])
        humidity_list.append(element[3])
        counter += 1
        items = list()
        items.append(element[0])
        items.append(element[2])
        items.append(element[3])
        all.append(items)
        print(element)

    conn.close()

    return render_template('dht11.html', \
        all_list = all,
        label1 = '気温(℃）',
        label2 = '湿度(%)',
        labels = label_list,
        daily_data1 = temperature_list,
        daily_data2 = humidity_list,
        monthly_script = '',
        yearly_script = ''
        )

if __name__ == "__main__":
    app.run(debug=True)