import time

temp = 15
count = 1
print("Enter your desired temperature : ")
desiredTemp = input()
print("Will try to reach " + desiredTemp)
while True:
    time.sleep(2)
    diff = abs(int(desiredTemp) - temp)
    count += 1
    temp += 0.1 * count
    print("Temperature is now : {:.2f}".format(temp))
    if diff < 1:
        print("Temp has been reached \n")
        break
