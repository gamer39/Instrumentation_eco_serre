from datetime import datetime, timedelta
from collections import namedtuple
import numpy as np
from UI import ComponentKeys

TRESHOLD_TEMP_EXT = 15
TRESHOLD_TOO_HUM = 15

actions = namedtuple(
    "actions",
    "heat_turn_on heat_turn_off vent_turn_on vent_turn_off lights_turn_on water_1_on water_2_on water_3_on water_4_on heat_pulse_on",
)


class ControlLogic:
    def __init__(self, config):
        self.loadConfig(config)

    def __del__(self):
        self.target_temp = None
        self.range_temp = None
        self.target_hum = None
        self.range_hum = None
        self.time_light_open = None
        self.time_light_close = None
        self.freq_water_1 = None
        self.next_water_1 = None
        self.freq_water_2 = None
        self.next_water_2 = None
        self.freq_water_3 = None
        self.next_water_3 = None
        self.freq_water_4 = None
        self.next_water_4 = None
        self.free_hum = None

    def loadConfig(self, config):
        self.target_temp = config[ComponentKeys.allKeys["Temp"]["Slider"]]
        self.range_temp = config[ComponentKeys.allKeys["Temp"]["Range"]]
        self.target_hum = config[ComponentKeys.allKeys["Humidity"]["Slider"]]
        self.range_hum = config[ComponentKeys.allKeys["Humidity"]["Range"]]
        # create a time object
        self.time_light_open = datetime(
            datetime.now().year,
            datetime.now().month,
            datetime.now().day,
            hour=config[ComponentKeys.allKeys["Lumiere"]["AllumeH"]],
            minute=config[ComponentKeys.allKeys["Lumiere"]["AllumeM"]],
            second=0,
        )
        self.time_light_close = datetime(
            datetime.now().year,
            datetime.now().month,
            datetime.now().day,
            hour=config[ComponentKeys.allKeys["Lumiere"]["EteintH"]],
            minute=config[ComponentKeys.allKeys["Lumiere"]["EteintM"]],
            second=0,
        )

        self.freq_water_1 = config["FreqWater1"]
        self.freq_water_2 = config["FreqWater2"]
        self.freq_water_3 = config["FreqWater3"]
        self.freq_water_4 = config["FreqWater4"]
        self.next_water_1 = datetime.strptime(config["NextWater1"], "%d/%m/%Y %H:%M")
        self.next_water_2 = datetime.strptime(config["NextWater2"], "%d/%m/%Y %H:%M")
        self.next_water_3 = datetime.strptime(config["NextWater3"], "%d/%m/%Y %H:%M")
        self.next_water_4 = datetime.strptime(config["NextWater4"], "%d/%m/%Y %H:%M")
        self.free_hum = config["HumidFree"]

    def logic_loop(self, sensorReadings):
        mean_temp = np.mean([sensorReadings.temp_int_1, sensorReadings.temp_int_2])
        mean_hum = np.mean([sensorReadings.hum_int_1, sensorReadings.hum_int_2])
        retour_lights = self.check_lights()
        retour_water_1 = self.check_water(1)
        retour_water_2 = self.check_water(2)
        retour_water_3 = self.check_water(3)
        retour_water_4 = self.check_water(4)
        id_temp = self.check_temp(mean_temp, sensorReadings.temp_ext)
        id_hum = self.check_hum(mean_hum, sensorReadings.hum_ext)
        retour_heat_on = False
        retour_heat_off = False
        retour_vent_on = False
        retour_vent_off = False
        retour_pulse_on = False
        if id_temp == 1:
            retour_heat_on = True
            retour_vent_off = True
        elif id_temp == 2:
            retour_heat_off = True
        elif id_temp == 3:
            retour_vent_on = True

        if id_hum == 1:
            retour_vent_off = True
        elif id_hum == 2:
            retour_vent_on = True
        elif id_hum == 3:
            retour_vent_on = True
            retour_pulse_on = True

        return actions(
            retour_heat_on,
            retour_heat_off,
            retour_vent_on,
            retour_vent_off,
            retour_lights,
            retour_water_1,
            retour_water_2,
            retour_water_3,
            retour_water_4,
            retour_pulse_on,
        )

    def check_lights(self):
        open = False
        if (
            datetime.now().time() > self.time_light_open.time()
            or datetime.now().time() < self.time_light_close.time()
        ):
            open = True
        return open

    def check_water(self, id):
        now = datetime.now()
        retour = False

        if id == 1:
            if now > self.next_water_1:
                retour = True
                self.next_water_1 = now + timedelta(
                    # this should probably be minutes
                    minutes=self.freq_water_1
                )
        elif id == 2:
            if now > self.next_water_2:
                retour = True
                self.next_water_2 = now + timedelta(minutes=self.freq_water_2)
        elif id == 3:
            if now > self.next_water_3:
                retour = True
                self.next_water_3 = now + timedelta(minutes=self.freq_water_3)
        elif id == 4:
            if now > self.next_water_4:
                retour = True
                self.next_water_4 = now + timedelta(minutes=self.freq_water_4)
        return retour

    def check_temp(self, temp_int, temp_ext):
        retour = 0
        if temp_int < (self.target_temp - self.range_temp):
            # start_chauffage
            # stop_vent
            retour = 1
            self.free_hum = False
        elif temp_int > (self.target_temp + self.range_temp):
            if temp_ext < TRESHOLD_TEMP_EXT:
                # stop_chauffage
                retour = 2
                pass
            else:
                # start_vent
                retour = 3
                pass
            self.free_hum = False
        else:
            self.free_hum = True
        return retour

    def check_hum(self, hum_int, hum_ext):
        retour = 0
        if self.free_hum:
            if hum_int < (self.target_hum - self.range_hum):
                # stop_vent
                retour = 1
                pass
            elif hum_int > (self.target_hum + self.range_hum):
                # start_vent
                retour = 2
                if hum_int > (self.target_hum + self.range_hum + TRESHOLD_TOO_HUM):
                    # pulse_chauffage
                    retour = 3
                    pass
        return retour
