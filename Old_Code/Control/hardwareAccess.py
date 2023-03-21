from ast import Pass
import numpy as np
from collections import namedtuple
import serial
import RPi.GPIO as GPIO
import threading
import time
from queue import Queue

PIN_HEATER = 8
PIN_VOLETS_OUVRE = 3
PIN_VOLETS_FERME = 5
PIN_VENT = 10
PIN_WATER_PUMP = 11
PIN_LIGHTS = 12
PIN_VALVE_1 = 13
PIN_VALVE_2 = 15
PIN_VALVE_3 = 16
PIN_VALVE_4 = 18
# FREQ_PWM = 0.0083333  # dure 2 minute
# FREQ_PWM = 2
# DUTY_CYCLE = 50
PWM_DURATION = 0.5
BIAIS_TEMP = 2.0

CONNECTION_ATTEMPTS = 20

WATER_DURATION = 5

LIST_PORTS = ["/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyACM2"]


complete_readings = namedtuple(
    "complete_readings",
    "temp_int_1 temp_int_2 temp_ext hum_int_1 hum_int_2 hum_ext CO2_int_1 CO2_int_2",
)
station_reading = namedtuple("station_reading", "temp hum CO2")


class HardwareAccess:
    def __init__(self):

        """Initialize les variables communes aux différentes fonctions
           de la classe"""
        self.list_serials = []
        self.heat_on = False
        self.lights_on = False
        self.volet_opened = False
        self.fan_on = False
        self.pulse_on = False
        self.test_file_temp_line = 0
        self.test_file_hum_line = 0
        self.test_file_co2_line = 0
        self.temp_ouverture_total_volets = 5
        self.current_ouverture_volets = 0
        self.queue_pwm = None
        self.thread_pwm = None

    def __del__(self):

        """Garbage collector; réinitialise les variables une fois qu'elles
           lorsque leur utilisation n'est plus nécessaire."""
        self.list_serials = None
        self.heat_on = None
        self.lights_on = None
        self.volet_opened = None
        self.fan_on = None
        self.pulse_on = None
        self.test_file_temp_line = None
        self.test_file_hum_line = None
        self.test_file_co2_line = None
        self.temp_ouverture_total_volets = None
        self.current_ouverture_volets = None
        self.queue_pwm.join()
        self.thread_pwm.join()
        self.queue_pwm = None
        self.thread_pwm = None

    def setup_hardware_access(self):
        self._key_lock = threading.Lock() 
        self.setup_gpios()
        self.setup_pwm()
        self.setup_serials()

    def setup_gpios(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(PIN_HEATER, GPIO.OUT)
        GPIO.setup(PIN_VOLETS_OUVRE, GPIO.OUT)
        GPIO.setup(PIN_VOLETS_FERME, GPIO.OUT)
        GPIO.setup(PIN_VENT, GPIO.OUT)
        GPIO.setup(PIN_WATER_PUMP, GPIO.OUT)
        GPIO.setup(PIN_LIGHTS, GPIO.OUT)
        GPIO.setup(PIN_VALVE_1, GPIO.OUT)
        GPIO.setup(PIN_VALVE_2, GPIO.OUT)
        GPIO.setup(PIN_VALVE_3, GPIO.OUT)
        GPIO.setup(PIN_VALVE_4, GPIO.OUT)
        GPIO.output(PIN_HEATER, GPIO.LOW)
        GPIO.output(PIN_VOLETS_OUVRE, GPIO.LOW)
        GPIO.output(PIN_VOLETS_FERME, GPIO.LOW)
        GPIO.output(PIN_VENT, GPIO.LOW)
        GPIO.output(PIN_WATER_PUMP, GPIO.LOW)
        GPIO.output(PIN_LIGHTS, GPIO.LOW)
        GPIO.output(PIN_VALVE_1, GPIO.LOW)
        GPIO.output(PIN_VALVE_2, GPIO.LOW)
        GPIO.output(PIN_VALVE_3, GPIO.LOW)
        GPIO.output(PIN_VALVE_4, GPIO.LOW)

    def setup_serials(self):
        for port in LIST_PORTS:
            connected = False
            n_tries = 0
            while not connected and n_tries < CONNECTION_ATTEMPTS:
                try:
                    ser = serial.Serial(
                        port=port,
                        baudrate=9600,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS,
                        timeout=10,
                    )
                    connected = True
                    self.list_serials.append(ser)
                except serial.serialutil.SerialException:
                    n_tries = n_tries + 1
                    time.sleep(1)

    def setup_pwm(self):
        self.queue_pwm = Queue(maxsize=0)
        self.thread_pwm = threading.Thread(target=self.pwm)
        self.thread_pwm.setDaemon(True)
        self.thread_pwm.start()

    def traitement_actions(self, actions, voletOuvertManuel):
        self.control_lights(actions.lights_turn_on)

        if actions.heat_pulse_on and not self.pulse_on:
            self.control_pwm(True)
            self.pulse_on = True
        elif not actions.heat_pulse_on and self.pulse_on:
            self.control_pwm(False)
            self.pulse_on = False

        if actions.heat_turn_on:
            self.control_heat(True)
        if actions.heat_turn_off:
            self.control_heat(False)

        if actions.vent_turn_on or voletOuvertManuel:
            self.control_fan(True)
            self.open_volets()
        if actions.vent_turn_off or not voletOuvertManuel:
            self.control_fan(False)
            self.close_volet()

        water_ids = []
        if actions.water_1_on:
            water_ids.append(1)
        if actions.water_2_on:
            water_ids.append(2)
        if actions.water_3_on:
            water_ids.append(3)
        if actions.water_4_on:
            water_ids.append(4)

        if len(water_ids) != 0:
            self.watering(water_ids)

    def watering(self, section_ids):
        t = threading.Thread(target=self.watering_thread, args=(section_ids,))
        t.start()

    def watering_thread(self, section_ids):
        self.turn_on_water_pump(True)
        for id in section_ids:
            self.turn_on_water_valve(id)
        self.turn_on_water_pump(False)

    def turn_on_water_pump(self, on):
        if on:
            GPIO.output(PIN_WATER_PUMP, GPIO.HIGH)
        else:
            GPIO.output(PIN_WATER_PUMP, GPIO.LOW)

    def turn_on_water_valve(self, section_id):
        pin = 0
        if section_id == 1:
            pin = PIN_VALVE_1
        elif section_id == 2:
            pin = PIN_VALVE_2
        elif section_id == 3:
            pin = PIN_VALVE_3
        elif section_id == 4:
            pin = PIN_VALVE_4

        # pour l'instant j'assume que les valves sont on/off
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(WATER_DURATION)
        GPIO.output(pin, GPIO.LOW)

    def control_fan(self, on):
        if on:
            GPIO.output(PIN_VENT, GPIO.HIGH)
            self.fan_on = True
        else:
            GPIO.output(PIN_VENT, GPIO.LOW)
            self.fan_on = False

    def open_volets(self):
        if not self.volet_opened:
            self.volet_opened = True
            t = threading.Thread(target=self.open_volets_thread, args=(100,))
            t.start()

    # pas certain qu'on ait besoin de faire 2 fonctions differentes pour l'ouverture et la fermeture
    def open_volets_thread(self, pourcentageOuverture):
        time_ouverture = pourcentageOuverture / 100 * self.temp_ouverture_total_volets
        GPIO.output(PIN_VOLETS_OUVRE, GPIO.HIGH)
        time.sleep(time_ouverture)
        GPIO.output(PIN_VOLETS_OUVRE, GPIO.LOW)
        self.current_ouverture_volets = time_ouverture

    def close_volet(self):
        if self.volet_opened:
            self.volet_opened = False
            t = threading.Thread(target=self.close_volets_thread)
            t.start()

    def close_volets_thread(self):
        GPIO.output(PIN_VOLETS_FERME, GPIO.HIGH)
        time.sleep(self.current_ouverture_volets)
        GPIO.output(PIN_VOLETS_FERME, GPIO.LOW)

    def control_lights(self, on):
        if on:
            GPIO.output(PIN_LIGHTS, GPIO.HIGH)
            self.lights_on = True
        else:
            GPIO.output(PIN_LIGHTS, GPIO.LOW)
            self.lights_on = False

    def control_heat(self, on):
        if on:
            GPIO.output(PIN_HEATER, GPIO.HIGH)
            self.heat_on = True
        else:
            GPIO.output(PIN_HEATER, GPIO.LOW)
            self.heat_on = False

    def control_pwm(self, start):
        if start:
            self.queue_pwm.put(True)
        else:
            GPIO.output(PIN_HEATER, GPIO.LOW)
            self.queue_pwm.put(False)

    def pwm(self):
        working = False
        while True:
            if not self.queue_pwm.empty():
                working = self.queue_pwm.get()
                self.queue_pwm.task_done()

            if working:
                GPIO.output(PIN_HEATER, GPIO.HIGH)
                time.sleep(PWM_DURATION)
                if not self.queue_pwm.empty():
                    working = self.queue_pwm.get()
                    self.queue_pwm.task_done()
                if working:
                    GPIO.output(PIN_HEATER, GPIO.LOW)
                    time.sleep(PWM_DURATION)
            else:
                time.sleep(0.5)

    def get_lecture_sensors(self):
        results_int = []
        result_ext = []
        for ser in self.list_serials:
            ser.write(b"run\n")
            reading = ser.readline()
            if reading == b"":
                print("couldn't not contact one station")
                # results_int.append(None)
            else:
                splits = reading.decode("utf-8").split(":")
                # if splits[2] == -1:
                #    result_ext = splits
                # else:
                #    results_int.append(splits)
                results_int.append(splits)

        # return complete_readings(
        #    float(results_int[0][0]),
        #    float(results_int[1][0]),
        #    float(result_ext[0]),
        #    float(results_int[0][1]),
        #    float(results_int[1][1]),
        #    float(result_ext[1]),
        #    float(results_int[0][2]),
        #    float(results_int[1][2]),
        # )

        return complete_readings(
            float(results_int[0][0]),
            float(results_int[1][0]),
            float(result_ext[2][2]),
            float(results_int[0][1]),
            float(results_int[1][1]),
            float(result_ext[2][2]),
            float(results_int[0][2]),
            float(results_int[1][2]),
        )

    def get_lecture_sensors_threaded(self):
        print("callings sensors")
        results_int = []
        result_ext = []
        threads = []
        for ser in self.list_serials:
            t = threading.Thread(
                target=self.contact_sensor, args=(ser, results_int, result_ext)
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        print(results_int)
        print(result_ext)

        if not len(result_ext) == 1:
            return None

        return complete_readings(
            float(results_int[0][0]) - BIAIS_TEMP,
            float(results_int[1][0]) - BIAIS_TEMP,
            float(result_ext[0][0]) - BIAIS_TEMP,
            float(results_int[0][1]),
            float(results_int[1][1]),
            float(result_ext[0][1]),
            float(results_int[0][2]),
            float(results_int[1][2]),
        )

    # return complete_readings(
    #     float(results_int[0][0]) - BIAIS_TEMP,
    #     float(results_int[1][0]) - BIAIS_TEMP,
    #     float(results_int[2][0]) - BIAIS_TEMP,
    #     float(results_int[0][1]),
    #     float(results_int[1][1]),
    #     float(results_int[2][1]),
    #     float(results_int[0][2]),
    #     float(results_int[1][2]),
    # )

    def contact_sensor(self, serial, output_int, output_ext):
        print("calling sensor one of sensors")
        serial.write(b"run\n")
        reading = serial.readline()
        # print(reading)
        if reading == b"":
            print("couldn't contact one station")
            # results_int.append(None)
        else:
            splits = reading.decode("utf-8").split(":")
            # if splits[2] == -1:
            if splits[2] == "-1":
                output_ext.append(splits)
            else:
                self._key_lock.acquire()
                output_int.append(splits)
                self._key_lock.release()
        print("sensor done")

    def get_lecture_sensors_test_random(self):
        if self.heat_on or np.random.random_integers(0, 10) <= 8:
            temp_int = np.random.normal(23, 2)
        else:
            temp_int = np.random.normal(18, 2)

        readings = complete_readings(temp_int, temp_int, 0, 0, 0, 0, 0, 0)
        return readings

    def get_lecture_sensors_test_simulated(self, directory):
        f_temp = open("test_lecture_files/" + directory + "/temp.txt")
        lines = f_temp.readlines()
        f_temp.close()
        if self.test_file_temp_line >= len(lines):
            self.test_file_temp_line = 0
        line_temp = lines[self.test_file_temp_line]
        self.test_file_temp_line += 1

        f_hum = open("test_lecture_files/" + directory + "/hum.txt")
        lines = f_hum.readlines()
        f_hum.close()
        if self.test_file_hum_line >= len(lines):
            self.test_file_hum_line = 0
        line_hum = lines[self.test_file_hum_line]
        self.test_file_hum_line += 1

        f_co2 = open("test_lecture_files/" + directory + "/CO2.txt")
        lines = f_co2.readlines()
        f_co2.close()
        if self.test_file_co2_line >= len(lines):
            self.test_file_co2_line = 0
        line_co2 = lines[self.test_file_co2_line]
        self.test_file_co2_line += 1

        splits_temp = line_temp.split(":")
        splits_hum = line_hum.split(":")
        splits_co2 = line_co2.split(":")

        readings = complete_readings(
            float(splits_temp[0]),
            float(splits_temp[1]),
            float(splits_temp[2]),
            float(splits_hum[0]),
            float(splits_hum[1]),
            float(splits_hum[2]),
            float(splits_co2[0]),
            float(splits_co2[1]),
        )
        time.sleep(5)
        return readings
