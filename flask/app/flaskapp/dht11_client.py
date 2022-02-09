import requests
import time
import board
import adafruit_dht

URL = 'http://indigoblue.ddns.net:5000/api/dht11'
PARAMS_FORMAT = '?sensor=DHT11&place={}&temperature={}&humidity={}'
PLACE = 'BedRoom'

dhtDevice = adafruit_dht.DHT11(board.D4)

try:
    temperature = dhtDevice.temperature
    humidity = dhtDevice.humidity
except:
    # 失敗した場合は、30秒待ってからもう１回実行する
    time.sleep(30)
    temperature = dhtDevice.temperature
    humidity = dhtDevice.humidity

dhtDevice.exit()

params = PARAMS_FORMAT.format(PLACE, temperature, humidity)

response = requests.post(URL + params)
print(response.status_code)    # HTTPのステータスコード取得
print(response.text)    # レスポンスのHTMLを文字列で取得
