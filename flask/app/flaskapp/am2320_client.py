import requests
import smbus
import time

URL = 'http://indigoblue.ddns.net:5000/api/am2320'
PARAMS_FORMAT = '?sensor=AM2320&place={}&temperature={}&humidity={}'
PLACE = 'BedRoom2'

i2c = smbus.SMBus(1)
address = 0x5c

try:
    i2c.write_i2c_block_data(address,0x00,[])
except:
    pass
time.sleep(0.003)
i2c.write_i2c_block_data(address,0x03,[0x00,0x04])

time.sleep(0.015)
block = i2c.read_i2c_block_data(address,0,6)
temperature = float(block[4] << 8 | block[5])/10
humidity = float(block[2] << 8 | block[3])/10

print('temperature:' + str(temperature))
print('humidity:' + str(humidity))

params = PARAMS_FORMAT.format(PLACE, temperature, humidity)

response = requests.post(URL + params)
print(response.status_code)    # HTTPのステータスコード取得
print(response.text)    # レスポンスのHTMLを文字列で取得

