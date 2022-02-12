#!/usr/bin/python

import smbus

Bus = smbus.SMBus(1)
Addr = 0x23

LxRead = Bus.read_i2c_block_data(Addr,0x11)
print("照度: "+str(LxRead[1]* 10)+" ルクス")

LxRead2 = Bus.read_i2c_block_data(Addr,0x10)
print("輝度: " + str((LxRead2[0] * 256 + LxRead2[1]) / 1.2))
