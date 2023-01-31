import time
import serial

time.sleep(30)


def lecture():
    time.sleep(3)
    return "THIS IS A TEST\n"


ser = serial.Serial(
    port="/dev/ttyGS0",
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=None,
)

while 1:
    x = ser.readline()
    print(x)
    if x == b"run\n":
        ser.write(bytes(lecture(), "UTF-8"))
    time.sleep(0.1)
