from cProfile import label
from itertools import count
from pickletools import read_unicodestringnl
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

    date = u"{0:%Y-%m-%d %H:%M}".format(datetime.datetime.utcnow())

    conn = sqlite3.connect('temperature.sqlite3')

    # テーブルがなければ作成する
    conn.execute("CREATE TABLE IF NOT EXISTS \
        T_Manage(id INTEGER PRIMARY KEY AUTOINCREMENT, time STRING, recordId INTEGER, \
        FOREIGN KEY(recordId) REFERENCES T_Record (recordId))")
    cur = conn.cursor()
    conn.execute("CREATE TABLE IF NOT EXISTS \
        T_Record(recordId INTEGER PRIMARY KEY AUTOINCREMENT, \
        placeId INTEGER, \
        temperature REAL, humidity REAL, \
        FOREIGN KEY(placeId) REFERENCES T_Place (placeId))")
    cur = conn.cursor()
    conn.execute("CREATE TABLE IF NOT EXISTS \
        T_Place(placeId INTEGER PRIMARY KEY AUTOINCREMENT, place STRING)")
    cur = conn.cursor()

    sql = 'INSERT INTO T_Place(place) SELECT ? WHERE NOT EXISTS (SELECT 1 FROM T_Place WHERE place=?)'
    cur.execute(sql, [place, place])

    # placeIdを取得
    sql = 'SELECT placeId FROM T_Place WHERE place=?'
    cur.execute(sql, [place])
    placeId = ''
    for element in cur:
        placeId = element[0]

    # T_Recordにデータを追加
    sql = 'INSERT INTO T_Record(placeId, temperature, humidity) VALUES(?, ?, ?)'
    data = [placeId, temperature, humidity]
    cur.execute(sql, data)

    # T_Recordに追加したレコードのrecordIdを取得する
    sql = 'select LAST_INSERT_ROWID() FROM T_Record'
    cur.execute(sql)
    recordId = 0
    for element in cur:
        recordId = element[0]

    # 既にあるrecordIdを取得する
    sql = 'SELECT recordId FROM T_Manage WHERE time=?'
    cur.execute(sql, [date])
    recordIds = ''
    for element in cur:
        recordIds = element[0]

    if len(str(recordIds)) == 0:
        # 同じ時刻のレコードがない場合はINSERTする
        sql = 'INSERT INTO T_Manage(time, recordId) VALUES(?, ?)'
        cur.execute(sql, [date, recordId])
    else:
        # recordIdはカンマ区切りで追加する
        data = '{},{}'.format(recordIds, recordId)
        sql = 'UPDATE T_Manage SET recordId=? WHERE time=?'
        cur.execute(sql, [data, date])

    conn.commit()
    conn.close()

    return "time:" + date + ", place:" + place + ", temperature:" + temperature + ", humidity:" + humidity

def create_data_list(cur, label_sql, sql, x_axis_format):
    labels = list()
    for element in cur.execute(label_sql):
        labels.append(element[0])

    placeId = -1
    label_list = list()
    temperature_list = list()
    humidity_list = list()
    temperatures = list()
    humidities = list()
    place_list = list()
    counter = 0
    for element in cur.execute(sql):
        if element[1] != placeId:
            counter = 0
            placeId = element[1]
            temperatures = list()
            humidities = list()
            temperature_list.append(temperatures)
            humidity_list.append(humidities)
            place_list.append(element[2])
            
        if len(label_list) < len(labels) - 1:
            timestamp = datetime.datetime.strptime(element[0], '%Y-%m-%d %H:%M:%S')
            label_list.append(timestamp.strftime(x_axis_format))
        
        if len(labels) > counter:
            if datetime.datetime.strptime(labels[counter], '%Y-%m-%d %H:%M:%S') == \
                datetime.datetime.strptime(element[0], '%Y-%m-%d %H:%M:%S'):
                temperatures.append(element[3])
                humidities.append(element[4])
            else:
                skip = 0
                for i, time in enumerate(labels, counter):
                    if len(labels) > i:
                        if datetime.datetime.strptime(labels[i], '%Y-%m-%d %H:%M:%S') == \
                            datetime.datetime.strptime(element[0], '%Y-%m-%d %H:%M:%S'):
                            temperatures.append(element[3])
                            humidities.append(element[4])
                            break
                        else:
                            # データが欠落しているため、同じデータで埋める
                            temperatures.append(element[3])
                            humidities.append(element[4])
                            skip += 1
                counter += skip
            counter += 1
    return label_list, temperature_list, humidity_list, place_list

@app.route('/dht11', methods=["GET"])
def get_dht11():
    conn = sqlite3.connect('temperature.sqlite3')
    cur = conn.cursor()

    label_sql = "SELECT datetime(time, 'localtime') FROM T_Manage \
        WHERE datetime(time, 'localtime') > datetime('now', 'localtime', '-24 hours') \
        GROUP BY datetime(time, 'localtime')"
    sql =   "WITH RECURSIVE split(KEY,idx,fld,remain) AS \
                (SELECT time, instr(recordId,',') AS idx, \
                    substr(recordId,1,instr(recordId,',')-1) AS fld, \
                    substr(recordId, instr(recordId,',')+1)||',' AS remain \
                FROM T_Manage UNION ALL SELECT KEY, instr(remain,',') AS idx, \
                        substr(remain,1,instr(remain,',')-1) AS fld, \
                        substr(remain, instr(remain,',')+1) AS remain \
                FROM split WHERE remain != '') \
            SELECT datetime(KEY, 'localtime') AS time, \
                T_Record.placeId, T_Place.place, temperature, humidity FROM split \
            INNER JOIN T_Record ON split.fld = T_Record.recordId \
            INNER JOIN T_Place ON T_Record.placeId = T_Place.placeId \
            WHERE fld != '' AND datetime(KEY, 'localtime') > datetime('now', 'localtime', '-24 hours') \
            ORDER BY T_Record.placeId ASC, KEY ASC"
    label_daily_list, temperature_daily_list, humidity_daily_list, place_dayly_list = \
        create_data_list(cur, label_sql, sql, '%H:%M')

    label_sql = "SELECT datetime(time, 'localtime') FROM T_Manage \
        WHERE datetime(time, 'localtime') > datetime('now', 'localtime', '-7 days') \
        GROUP BY datetime(time, 'localtime')"
    sql =   "WITH RECURSIVE split(KEY,idx,fld,remain) AS \
                (SELECT time, instr(recordId,',') AS idx, \
                    substr(recordId,1,instr(recordId,',')-1) AS fld, \
                    substr(recordId, instr(recordId,',')+1)||',' AS remain \
                FROM T_Manage UNION ALL SELECT KEY, instr(remain,',') AS idx, \
                        substr(remain,1,instr(remain,',')-1) AS fld, \
                        substr(remain, instr(remain,',')+1) AS remain \
                FROM split WHERE remain != '') \
            SELECT datetime(KEY, 'localtime') AS time, \
                T_Record.placeId, T_Place.place, temperature, humidity FROM split \
            INNER JOIN T_Record ON split.fld = T_Record.recordId \
            INNER JOIN T_Place ON T_Record.placeId = T_Place.placeId \
            WHERE fld != '' AND datetime(KEY, 'localtime') > datetime('now', 'localtime', '-7 days') \
            ORDER BY T_Record.placeId ASC, KEY ASC"
    label_weekly_list, temperature_weekly_list, humidity_weekly_list, place_weekly_list = \
        create_data_list(cur, label_sql, sql, '%Y/%m/%d %H:%M')

    label_sql = "SELECT datetime(time, 'localtime') FROM T_Manage \
        WHERE datetime(time, 'localtime') > datetime('now', 'localtime', '-1 months') \
        GROUP BY datetime(time, 'localtime')"
    sql =   "WITH RECURSIVE split(KEY,idx,fld,remain) AS \
                (SELECT time, instr(recordId,',') AS idx, \
                    substr(recordId,1,instr(recordId,',')-1) AS fld, \
                    substr(recordId, instr(recordId,',')+1)||',' AS remain \
                FROM T_Manage UNION ALL SELECT KEY, instr(remain,',') AS idx, \
                        substr(remain,1,instr(remain,',')-1) AS fld, \
                        substr(remain, instr(remain,',')+1) AS remain \
                FROM split WHERE remain != '') \
            SELECT datetime(KEY, 'localtime') AS time, \
                T_Record.placeId, T_Place.place, temperature, humidity FROM split \
            INNER JOIN T_Record ON split.fld = T_Record.recordId \
            INNER JOIN T_Place ON T_Record.placeId = T_Place.placeId \
            WHERE fld != '' AND datetime(KEY, 'localtime') > datetime('now', 'localtime', '-1 months') \
            ORDER BY T_Record.placeId ASC, KEY ASC"
    label_monthly_list, temperature_monthly_list, humidity_monthly_list, place_monthly_list = \
        create_data_list(cur, label_sql, sql, '%Y/%m/%d')

    conn.close()

    temperature_color = ['rgba(182, 15, 0, 0.5)', 'rgba(254, 78, 19, 0.5)', \
        'rgba(255, 159, 75, 0.5)', 'rgba(255, 220, 131, 0.5)', 'rgba(239, 255, 189, 0.5)']
    humidity_color = ['rgba(0, 67, 106, 0.5)', 'rgba(32, 125, 147, 0.5)', \
        'rgba(85, 186, 191, 0.5)', 'rgba(132, 236, 225, 0.5)', 'rgba(178, 255, 217, 0.5)']
    return render_template('dht11.html', \
        label_daily = label_daily_list,        
        temperature_daily = temperature_daily_list,
        humidity_daily = humidity_daily_list,
        place_daily = place_dayly_list,
        label_weekly = label_weekly_list,        
        temperature_weekly = temperature_weekly_list,
        humidity_weekly = humidity_weekly_list,
        place_weekly = place_weekly_list,
        label_monthly = label_monthly_list,
        temperature_monthly = temperature_monthly_list,
        humidity_monthly = humidity_monthly_list,
        place_monthly = place_monthly_list,
        temperature_color = temperature_color,
        humidity_color = humidity_color,
        )

if __name__ == "__main__":
    app.run(debug=True)