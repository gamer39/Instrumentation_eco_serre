from Control.hardwareAccess import HardwareAccess
from Control.DummyHardwareAccess import DummyHardwareAccess
import time
from threading import Thread
from UI.Interface import Interface
from UI.UI import Components
from Control.ControlLogic import ControlLogic
from Utils.ValuesSaver import ValuesSaver
from queue import Queue

# copier le cotenu de config_test dans config.json
config_file_path = "/home/pi/Desktop/git/Design-IV/Utils/config.json"
# config_file_path = "Utils/config_test.json"
hardware = HardwareAccess()
logic = None  # ControlLogic()
valuesSaver = ValuesSaver(config_file_path)
components = Components()
interface = Interface(components)


def main():
    q = Queue()
    config_file = setup()
    q = Queue()
    t_1 = Thread(target=interface.runInterface, args=(config_file, q, valuesSaver))
    t_2 = Thread(target=actionLoop, args=(q,))
    t_1.start()
    t_2.start()
    t_1.join()
    t_2.join()


def actionLoop(q):
    timeCount = 0
    while True:
        # ping_watchdog()
        if interface.window_down:
            break
        changements = interface.checkChangements()
        timeCount += 1
        if (
            changements or timeCount > 60
        ):  # on met un timecount pour saver les etats courant une fois de temps en temps
            valeurInterface = interface.getValues()
            if valeurInterface is not None:
                valuesSaver.updateValues(valeurInterface)
                logic.loadConfig(valuesSaver.getValues())
            # changements = False
            timeCount = 0

        # readings = hardware.get_lecture_sensors_test_simulated("test_winter_focus_temp")
        readings = hardware.get_lecture_sensors_threaded()

        if not readings == None:
            co2_level = round((readings.CO2_int_1 + readings.CO2_int_2) / 2, 2)
            if co2_level > valuesSaver.getValues()["SliderCO2"]:
                interface.CO2NiveauCritiquePopup(True)
            else:
                interface.CO2NiveauCritiquePopup(False)

            q.put(readings)
            q.join()
            actions = logic.logic_loop(readings)
            waterReadings = {
                "NextWater1": logic.next_water_1.strftime("%d/%m/%Y %H:%M"),
                "NextWater2": logic.next_water_2.strftime("%d/%m/%Y %H:%M"),
                "NextWater3": logic.next_water_3.strftime("%d/%m/%Y %H:%M"),
                "NextWater4": logic.next_water_4.strftime("%d/%m/%Y %H:%M"),
            }
            valuesSaver.updateValues(waterReadings)
            hardware.traitement_actions(actions)
            interface.updateStateValuesActionLoop(actions, hardware)
        time.sleep(0.5)


def setup():
    hardware.setup_hardware_access()
    return load_config()


def load_config():
    config = valuesSaver.getValues()
    global logic
    logic = ControlLogic(config)
    return config


def ping_watchdog():
    file_to_open = open("/dev/watchdog", "w")
    file_to_open.write("S")
    file_to_open.close()


if __name__ == "__main__":
    main()
