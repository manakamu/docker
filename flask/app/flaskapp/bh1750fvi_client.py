#!/usr/bin/python

import smbus
import requests

URL = 'http://indigoblue.ddns.net:5000/api/sensors'
PARAMS_FORMAT = '?sensor=BH1750FVI&place={}&lux={}&luminance={}'
PLACE = 'DiningRoom'

def readLux():
    Bus = smbus.SMBus(1)
    Addr = 0x23

    LxRead = Bus.read_i2c_block_data(Addr,0x11)
    LxRead2 = Bus.read_i2c_block_data(Addr,0x10)

    lux = LxRead[1]* 10
    luminance = (LxRead2[0] * 256 + LxRead2[1]) / 1.2
    
    return lux, luminance

lux, luminance = readLux()

if lux == 0.0 and luminance == 0.0:
    # 0の場合は念のためもう一度取得する
    lux, luminance = readLux()

print("照度: "+str(lux)+" ルクス")
print("輝度: " + str(luminance))

params = PARAMS_FORMAT.format(PLACE, lux, luminance)

response = requests.post(URL + params)
print(response.status_code)    # HTTPのステータスコード取得
print(response.text)    # レスポンスのHTMLを文字列で取得
