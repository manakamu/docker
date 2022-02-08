from pyexpat.errors import XML_ERROR_FEATURE_REQUIRES_XML_DTD
from flask import Flask, request, render_template
import datetime
import sqlite3

app = Flask(__name__)

# デーブル作成クエリ
SQL_CREATE_T_DHT11 = 'CREATE TABLE IF NOT EXISTS \
    T_DHT11(recordId INTEGER PRIMARY KEY AUTOINCREMENT, \
    temperature REAL, humidity REAL)'
SQL_CREATE_T_SENSOR = 'CREATE TABLE IF NOT EXISTS \
    T_Sensor(sensorId INTEGER PRIMARY KEY AUTOINCREMENT, sensor STRING)'
SQL_CREATE_T_PLACE = 'CREATE TABLE IF NOT EXISTS \
    T_Place(placeId INTEGER PRIMARY KEY AUTOINCREMENT, place STRING)'
SQL_CREATE_T_MASTER = 'CREATE TABLE IF NOT EXISTS \
    T_Master(id INTEGER PRIMARY KEY AUTOINCREMENT, time STRING, \
    sensorId INTEGER, placeId INTEGER, recordId INTEGER, \
    FOREIGN KEY(sensorId) REFERENCES T_Sensor (sensorId), \
    FOREIGN KEY(placeId) REFERENCES T_Place (placeId), \
    FOREIGN KEY(recordId) REFERENCES T_Record (recordId))'

# T_Placeに関するクエリ
SQL_INSERT_T_PLACE = 'INSERT INTO T_Place(place) \
    SELECT ? WHERE NOT EXISTS (SELECT 1 FROM T_Place WHERE place=?)'
SQL_SELECT_PLACE_ID = 'SELECT placeId FROM T_Place WHERE place=?'

# T_Sensorに関するクエリ
SQL_INSERT_T_SENSOR = 'INSERT INTO T_Sensor(sensor) \
    SELECT ? WHERE NOT EXISTS (SELECT 1 FROM T_Sensor WHERE sensor=?)'
SQL_SELECT_SENSOR_ID = 'SELECT sensorId FROM T_Sensor WHERE sensor=?'

# T_DHT11に関するクエリ
SQL_INSERT_T_DHT11_RECORD = 'INSERT INTO T_DHT11(temperature, humidity) \
    VALUES(?, ?)'
SQL_SELECT_T_DHT11_RECOED ='SELECT LAST_INSERT_ROWID() FROM T_DHT11'

# T_Masterに関するクエリ
SQL_SELECT_T_MASTER = 'SELECT recordId FROM T_Master WHERE time=?'
SQL_INSERT_T_MASTER = 'INSERT INTO T_Master(time, sensorId, placeId, recordId) VALUES(?, ?, ?, ?)'

# グラフを描くためのSQL
SQL_SELECT_DAILY_DATE = "SELECT datetime(time, 'localtime') FROM T_Master \
    WHERE datetime(time, 'localtime') > datetime('now', 'localtime', '-24 hours') \
    GROUP BY datetime(time, 'localtime')"
SQL_SELECT_DAILY_DATA = "WITH RECURSIVE split(KEY,idx,fld,remain) AS \
        (SELECT time, instr(recordId,',') AS idx, \
            substr(recordId,1,instr(recordId,',')-1) AS fld, \
            substr(recordId, instr(recordId,',')+1)||',' AS remain \
        FROM T_Master UNION ALL SELECT KEY, instr(remain,',') AS idx, \
                substr(remain,1,instr(remain,',')-1) AS fld, \
                substr(remain, instr(remain,',')+1) AS remain \
        FROM split WHERE remain != '') \
    SELECT datetime(KEY, 'localtime') AS time, \
        T_Record.placeId, T_Place.place, temperature, humidity FROM split \
    INNER JOIN T_Record ON split.fld = T_Record.recordId \
    INNER JOIN T_Place ON T_Record.placeId = T_Place.placeId \
    WHERE fld != '' AND datetime(KEY, 'localtime') > datetime('now', 'localtime', '-24 hours') \
    ORDER BY T_Record.placeId ASC, KEY ASC"
SQL_SELECT_WEEKLY_DATE = "SELECT datetime(time, 'localtime') FROM T_Master \
    WHERE datetime(time, 'localtime') > datetime('now', 'localtime', '-7 days') \
    GROUP BY datetime(time, 'localtime')"
SQL_SELECT_WEEKLY_DATA = "WITH RECURSIVE split(KEY,idx,fld,remain) AS \
        (SELECT time, instr(recordId,',') AS idx, \
            substr(recordId,1,instr(recordId,',')-1) AS fld, \
            substr(recordId, instr(recordId,',')+1)||',' AS remain \
        FROM T_Master UNION ALL SELECT KEY, instr(remain,',') AS idx, \
                substr(remain,1,instr(remain,',')-1) AS fld, \
                substr(remain, instr(remain,',')+1) AS remain \
        FROM split WHERE remain != '') \
    SELECT datetime(KEY, 'localtime') AS time, \
        T_Record.placeId, T_Place.place, temperature, humidity FROM split \
    INNER JOIN T_Record ON split.fld = T_Record.recordId \
    INNER JOIN T_Place ON T_Record.placeId = T_Place.placeId \
    WHERE fld != '' AND datetime(KEY, 'localtime') > datetime('now', 'localtime', '-7 days') \
    ORDER BY T_Record.placeId ASC, KEY ASC"
SQL_SELECT_MONTHLY_DATE = "SELECT datetime(time, 'localtime') FROM T_Master \
    WHERE datetime(time, 'localtime') > datetime('now', 'localtime', '-1 months') \
    GROUP BY datetime(time, 'localtime')"
SQL_SELECT_MONTHLY_DATA = "WITH RECURSIVE split(KEY,idx,fld,remain) AS \
        (SELECT time, instr(recordId,',') AS idx, \
            substr(recordId,1,instr(recordId,',')-1) AS fld, \
            substr(recordId, instr(recordId,',')+1)||',' AS remain \
        FROM T_Master UNION ALL SELECT KEY, instr(remain,',') AS idx, \
                substr(remain,1,instr(remain,',')-1) AS fld, \
                substr(remain, instr(remain,',')+1) AS remain \
        FROM split WHERE remain != '') \
    SELECT datetime(KEY, 'localtime') AS time, \
        T_Record.placeId, T_Place.place, temperature, humidity FROM split \
    INNER JOIN T_Record ON split.fld = T_Record.recordId \
    INNER JOIN T_Place ON T_Record.placeId = T_Place.placeId \
    WHERE fld != '' AND datetime(KEY, 'localtime') > datetime('now', 'localtime', '-1 months') \
    ORDER BY T_Record.placeId ASC, KEY ASC"

@app.route('/')
def index():
    return '<h2>Hello Flask+uWSGI+Nginx</h2>'

def create_dht11_table(conn):
    # テーブルがなければ作成する
    conn.execute(SQL_CREATE_T_DHT11)
    conn.execute(SQL_CREATE_T_SENSOR)
    conn.execute(SQL_CREATE_T_PLACE)
    conn.execute(SQL_CREATE_T_MASTER)

def insert_place(conn, place):
    cur = conn.cursor()

    cur.execute(SQL_INSERT_T_PLACE, [place, place])

    # 追加したplaceのplaceIdを取得
    cur.execute(SQL_SELECT_PLACE_ID, [place])
    placeId = None
    for element in cur:
        placeId = element[0]

    return placeId

def insert_sensor(conn, sensor):
    cur = conn.cursor()

    cur.execute(SQL_INSERT_T_SENSOR, [sensor, sensor])

    # 追加したT_sensorのplaceIdを取得
    cur.execute(SQL_SELECT_SENSOR_ID, [sensor])
    sensorId = None
    for element in cur:
        sensorId = element[0]

    return sensorId
    
def insert_dht11_record(conn, temperature, humidity):
    cur = conn.cursor()

    # T_DHT11にデータを追加
    data = [temperature, humidity]
    cur.execute(SQL_INSERT_T_DHT11_RECORD, data)

    # T_DHT11に追加したレコードのrecordIdを取得する
    cur.execute(SQL_SELECT_T_DHT11_RECOED)
    recordId = 0
    for element in cur:
        recordId = element[0]

    return recordId

def insert_master(conn, sensorId, placeId, date, recordId):
    cur = conn.cursor()
    cur.execute(SQL_INSERT_T_MASTER, [date, sensorId, placeId, recordId])

@app.route('/api/dht11', methods=["POST"])
def post_data():
    date = u"{0:%Y-%m-%d %H:%M}".format(datetime.datetime.utcnow())
    sensor = request.args.get("sensor")
    place = request.args.get("place")
    temperature = request.args.get("temperature")
    humidity = request.args.get("humidity")
    conn = sqlite3.connect('sensors.sqlite3')

    create_dht11_table(conn)

    cur = conn.cursor()
    sensorId = insert_sensor(conn, sensor)
    placeId = insert_place(conn, place)
    recordId = insert_dht11_record(conn, temperature, humidity)

    insert_master(conn, date, sensorId, placeId, recordId)

    conn.commit()
    conn.close()

    return "time:" + date + ", sensor:" + sensor + ", place:" + place + ", \
        temperature:" + temperature + ", humidity:" + humidity

def create_data_list(cur, date_sql, sql, x_axis_format):
    dates_all = list()
    for element in cur.execute(date_sql):
        dates_all.append(element[0])

    placeId = -1
    date_list = list()
    temperature_list = list()
    humidity_list = list()
    temperatures = None
    humidities = None
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
            print(element[2])
        if counter >= len(dates_all):
            break
        current_date = datetime.datetime.strptime(dates_all[counter], '%Y-%m-%d %H:%M:%S')
        record_date = datetime.datetime.strptime(element[0], '%Y-%m-%d %H:%M:%S')
        if len(date_list) < len(dates_all):
            date_list.append(current_date.strftime(x_axis_format))
        if current_date == record_date:
            temperatures.append(element[3])
            humidities.append(element[4])
        else:
            skip = 0
            for i, time in enumerate(dates_all, counter):
                if len(dates_all) > i:
                    current_date = datetime.datetime.strptime( \
                        dates_all[i], '%Y-%m-%d %H:%M:%S')
                    if len(date_list) < len(dates_all):
                        date_list.append(current_date.strftime(x_axis_format))

                    if current_date == record_date:
                        temperatures.append(element[3])
                        humidities.append(element[4])
                        break
                    else:
                        # データが欠落しているため、同じデータで埋める
                        temperatures.append(element[3])
                        humidities.append(element[4])
                        skip += 1
                else:
                    break
            counter += skip
        counter += 1
    return date_list, temperature_list, humidity_list, place_list

@app.route('/dht11', methods=["GET"])
def get_dht11():
    conn = sqlite3.connect('temperature.sqlite3')
    cur = conn.cursor()

    label_daily, temperature_daily, humidity_daily, place_daily = \
        create_data_list(cur, SQL_SELECT_DAILY_DATE, SQL_SELECT_DAILY_DATA, '%H:%M')

    label_weekly, temperature_weekly, humidity_weekly, place_weekly = \
        create_data_list(cur, SQL_SELECT_WEEKLY_DATE, SQL_SELECT_WEEKLY_DATA, '%Y/%m/%d %H:%M')

    label_monthly, temperature_monthly, humidity_monthly, place_monthly = \
        create_data_list(cur, SQL_SELECT_MONTHLY_DATE, SQL_SELECT_MONTHLY_DATA, '%Y/%m/%d')

    conn.close()

    temperature_color = ['rgba(182, 15, 0, 0.5)', 'rgba(254, 78, 19, 0.5)', \
        'rgba(255, 159, 75, 0.5)', 'rgba(255, 220, 131, 0.5)', \
        'rgba(239, 255, 189, 0.5)']
    humidity_color = ['rgba(0, 67, 106, 0.5)', 'rgba(32, 125, 147, 0.5)', \
        'rgba(85, 186, 191, 0.5)', 'rgba(132, 236, 225, 0.5)', \
        'rgba(178, 255, 217, 0.5)']
    return render_template('dht11.html', \
        label_daily = label_daily,        
        temperature_daily = temperature_daily,
        humidity_daily = humidity_daily,
        place_daily = place_daily,
        label_weekly = label_weekly,        
        temperature_weekly = temperature_weekly,
        humidity_weekly = humidity_weekly,
        place_weekly = place_weekly,
        label_monthly = label_monthly,
        temperature_monthly = temperature_monthly,
        humidity_monthly = humidity_monthly,
        place_monthly = place_monthly,
        temperature_color = temperature_color,
        humidity_color = humidity_color,
        )

if __name__ == "__main__":
    app.run(debug=True)
