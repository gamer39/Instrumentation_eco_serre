#!/usr/bin/env python
import time
import serial

list_ports = ["/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyACM2"]
# list_ports = ['/dev/ttyACM0']
list_serials = []

for port in list_ports:
    ser = serial.Serial(
        port=port,
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=10,
    )
    list_serials.append(ser)

while 1:
    print("nouvelles lectures: ")
    for ser in list_serials:
        ser.write(b"run\n")
        result = ser.readline()
        if result == b"":
            print("Read time out")
        else:
            splits = result.decode("utf-8").split(":")
            msg = "temp : " + splits[0] + " hum : " + splits[1] + " CO2 : " + splits[2]
            print(msg)
