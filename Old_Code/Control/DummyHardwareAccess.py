from ast import Pass
import numpy as np
from collections import namedtuple
import serial
import threading
import time

PIN_HEATER = 0
PIN_VOLETS = 0
PIN_VENT = 0
PIN_WATER_PUMP = 0
PIN_LIGHTS = 0
PIN_VALVE_1 = 0
PIN_VALVE_2 = 0
PIN_VALVE_3 = 0
PIN_VALVE_4 = 0
FREQ_PWM = 0.0083333  # dure 2 minute
DUTY_CYCLE = 50
WATER_DURATION = 0

LIST_PORTS = ["/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyACM2"]


# pour fins de démonstrations


complete_readings = namedtuple(
    "complete_readings",
    "temp_int_1 temp_int_2 temp_ext hum_int_1 hum_int_2 hum_ext CO2_int_1 CO2_int_2",
)
station_reading = namedtuple("station_reading", "temp hum CO2")


class DummyHardwareAccess:
    def __init__(self):
        self.list_serials = []
        self.heat_on = False
        self.lights_on = False
        self.volet_opened = False
        self.fan_on = False
        self.pulse_on = False
        self.test_file_temp_line = 0
        self.test_file_hum_line = 0
        self.test_file_co2_line = 0

    def __del__(self):
        self.list_serials = None
        self.heat_on = None
        self.lights_on = None
        self.volet_opened = None
        self.fan_on = None
        self.pulse_on = None
        self.test_file_temp_line = None
        self.test_file_hum_line = None
        self.test_file_co2_line = None

    def setup_hardware_access(self):
        self._key_lock = threading.Lock()
        self.setup_gpios()
        self.setup_serials()

    def setup_gpios(self):
        pass

    def setup_serials(self):
        pass

    def traitement_actions(self, actions, voletOuvertManuel):
        self.control_lights(actions.lights_turn_on)

        if actions.heat_pulse_on and not self.pulse_on:
            print("heatpulse_on")
            self.pulse_on = True
        elif not actions.heat_pulse_on and self.pulse_on:
            print("heatpulse_off")
            self.pulse_on = False

        if actions.heat_turn_on:
            self.control_heat(True)
        if actions.heat_turn_off:
            self.control_heat(False)

        if actions.vent_turn_on or voletOuvertManuel:
            self.control_fan(True)
            self.open_volets()
        if actions.vent_turn_off:
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
            print("water_pump_on")
        else:
            print("water_pump_off")

    def turn_on_water_valve(self, section_id):
        # open valve
        time.sleep(WATER_DURATION)
        # close valve

    def control_fan(self, on):
        if on:
            print("fan_on")
            self.fan_on = True
        else:
            print("fan_off")
            self.fan_on = False

    def open_volets(self):
        if not self.volet_opened:
            self.volet_opened = True
            t = threading.Thread(target=self.open_volets_thread, args=(100,))
            t.start()

    # pas certain qu'on ait besoin de faire 2 fonctions differentes pour l'ouverture et la fermeture
    def open_volets_thread(self, pourcentageOuverture):
        print("opening volets")
        return True

    def close_volet(self):
        if self.volet_opened:
            self.volet_opened = False
            t = threading.Thread(target=self.close_volets_thread)
            t.start()

    def close_volets_thread(self):
        print("Closing volets")
        return True

    def control_lights(self, on):
        if on:
            print("lights_on")
            self.lights_on = True
        else:
            print("lights_off")
            self.lights_on = False

    def control_heat(self, on):
        if on:
            print("heat_on")
            self.heat_on = True
        else:
            print("heat_off")
            self.heat_on = False

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
                if splits[2] == -1:
                    result_ext = splits
                else:
                    results_int.append(splits)

        return complete_readings(
            float(results_int[0][0]),
            float(results_int[1][0]),
            float(result_ext[0]),
            float(results_int[0][1]),
            float(results_int[1][1]),
            float(result_ext[1]),
            float(results_int[0][2]),
            float(results_int[1][2]),
        )

    def get_lecture_sensors_threaded(self):
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

        return complete_readings(
            float(results_int[0][0]),
            float(results_int[1][0]),
            float(result_ext[0][0]),
            float(results_int[0][1]),
            float(results_int[1][1]),
            float(result_ext[1]),
            float(results_int[0][2]),
            float(results_int[1][2]),
        )

    def contact_sensor(self, serial, output_int, output_ext):
        serial.write(b"run\n")
        reading = serial.readline()
        if reading == b"":
            print("couldn't not contact one station")
            # results_int.append(None)
        else:
            splits = reading.decode("utf-8").split(":")
            if splits[2] == -1:
                output_ext.append(splits)
            else:
                self._key_lock.acquire()
                output_int.append(splits)
                self._key_lock.release()

    def get_lecture_sensors_test_random(self):
        if self.heat_on or np.random.random_integers(0, 10) <= 8:
            temp_int = np.random.normal(18, 2)
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
        print(readings)
        return readings
