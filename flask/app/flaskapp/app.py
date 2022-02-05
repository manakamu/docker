from flask import Flask, request, render_template
import datetime
import sqlite3

app = Flask(__name__)

# デーブル作成クエリ
SQL_CREATE_T_MANAGE = 'CREATE TABLE IF NOT EXISTS \
    T_Manage(id INTEGER PRIMARY KEY AUTOINCREMENT, time STRING, recordId INTEGER, \
    FOREIGN KEY(recordId) REFERENCES T_Record (recordId))'
SQL_CREATE_T_RECORD = 'CREATE TABLE IF NOT EXISTS \
    T_Record(recordId INTEGER PRIMARY KEY AUTOINCREMENT, \
    placeId INTEGER, \
    temperature REAL, humidity REAL, \
    FOREIGN KEY(placeId) REFERENCES T_Place (placeId))'
SQL_CREATE_T_PLACE = 'CREATE TABLE IF NOT EXISTS T_Place(placeId INTEGER PRIMARY KEY AUTOINCREMENT, place STRING)'

# T_Placeに関するクエリ
SQL_INSERT_T_PLACE = 'INSERT INTO T_Place(place) \
    SELECT ? WHERE NOT EXISTS (SELECT 1 FROM T_Place WHERE place=?)'
SQL_SELECT_PLACE_ID = 'SELECT placeId FROM T_Place WHERE place=?'

# T_Recordに関するクエリ
SQL_INSERT_T_RECORD = 'INSERT INTO T_Record(placeId, temperature, humidity) VALUES(?, ?, ?)'
SQL_SELECT_T_RECOED ='SELECT LAST_INSERT_ROWID() FROM T_Record'

# T_Manageに関するクエリ
SQL_SELECT_T_MANAGE = 'SELECT recordId FROM T_Manage WHERE time=?'
SQL_INSERT_T_MANAGE = 'INSERT INTO T_Manage(time, recordId) VALUES(?, ?)'
SQL_UPDATE_T_MANAGE = 'UPDATE T_Manage SET recordId=? WHERE time=?'

@app.route('/')
def index():
    return '<h2>Hello Flask+uWSGI+Nginx</h2>'

def create_table(conn):
    # テーブルがなければ作成する
    conn.execute(SQL_CREATE_T_MANAGE)
    conn.execute(SQL_CREATE_T_RECORD)
    conn.execute(SQL_CREATE_T_PLACE)

def insert_place(conn, place):
    cur = conn.cursor()

    cur.execute(SQL_INSERT_T_PLACE, [place, place])

    # 追加したplaceのplaceIdを取得
    cur.execute(SQL_SELECT_PLACE_ID, [place])
    placeId = None
    for element in cur:
        placeId = element[0]

    return placeId

def insert_record(conn, placeId, temperature, humidity):
    cur = conn.cursor()

    # T_Recordにデータを追加
    data = [placeId, temperature, humidity]
    cur.execute(SQL_INSERT_T_RECORD, data)

    # T_Recordに追加したレコードのrecordIdを取得する
    cur.execute(SQL_SELECT_T_RECOED)
    recordId = 0
    for element in cur:
        recordId = element[0]

    return recordId

def insert_manage(conn, date, recordId):
    cur = conn.cursor()

    # 既にあるrecordIdを取得する
    cur.execute(SQL_SELECT_T_MANAGE, [date])
    recordIds = None
    for element in cur:
        recordIds = element[0]

    if len(str(recordIds)) == 0:
        # 同じ時刻のレコードがない場合はINSERTする
        cur.execute(SQL_INSERT_T_MANAGE, [date, recordId])
    else:
        # recordIdはカンマ区切りで追加する
        data = '{},{}'.format(recordIds, recordId)
        cur.execute(SQL_UPDATE_T_MANAGE, [data, date])

@app.route('/api/post', methods=["POST"])
def post_data():
    date = u"{0:%Y-%m-%d %H:%M}".format(datetime.datetime.utcnow())
    place = request.args.get("place")
    temperature = request.args.get("temperature")
    humidity = request.args.get("humidity")
    conn = sqlite3.connect('temperature.sqlite3')

    create_table(conn)

    cur = conn.cursor()
    placeId = insert_place(conn, place)

    recordId = insert_record(conn, placeId, temperature, humidity)

    insert_manage(conn, date, recordId)

    conn.commit()
    conn.close()

    return "time:" + date + ", place:" + place + ", temperature:" + temperature + ", humidity:" + humidity

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
            
        if len(date_list) < len(dates_all) - 1:
            timestamp = datetime.datetime.strptime(element[0], '%Y-%m-%d %H:%M:%S')
            date_list.append(timestamp.strftime(x_axis_format))
        
        if len(dates_all) > counter:
            if datetime.datetime.strptime(dates_all[counter], '%Y-%m-%d %H:%M:%S') == \
                datetime.datetime.strptime(element[0], '%Y-%m-%d %H:%M:%S'):
                temperatures.append(element[3])
                humidities.append(element[4])
            else:
                skip = 0
                for i, time in enumerate(dates_all, counter):
                    if len(dates_all) > i:
                        if datetime.datetime.strptime(dates_all[i], '%Y-%m-%d %H:%M:%S') == \
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
    return date_list, temperature_list, humidity_list, place_list

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
