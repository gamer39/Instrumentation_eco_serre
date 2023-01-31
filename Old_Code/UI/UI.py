import PySimpleGUI as sg
from UI import ComponentKeys, Combos


def Slider2button(
    text, keySub, keySlider, keyAdd, keyRange, minValue, maxValue, defaultValue
):
    return [
        sg.Text(text),
        sg.Button(
            "",
            key=keySub,
            button_color=(sg.theme_background_color(), sg.theme_background_color()),
            image_filename="/home/pi/Desktop/git/Design-IV/UI/minus_sign.png",
            image_size=(35, 35),
            image_subsample=2,
        ),
        sg.Slider(
            key=keySlider,
            range=(minValue, maxValue),
            default_value=defaultValue,
            size=(20, 5),
            orientation="horizontal",
            font=("Helvetica", 12),
            resolution=0.5,
            enable_events=True,
        ),
        sg.Button(
            "",
            key=keyAdd,
            button_color=(sg.theme_background_color(), sg.theme_background_color()),
            image_filename="/home/pi/Desktop/git/Design-IV/UI/plus_sign.png",
            image_size=(35, 35),
            image_subsample=2,
        ),
        sg.T("±"),
        sg.Combo(
            Combos.ranges,
            key=keyRange,
            default_value=10,
            enable_events=True,
            size=(10, 35),
        ),
    ]


def Slider2ButtonNoRange(
    text, keySub, keySlider, keyAdd, keyRange, minValue, maxValue, defaultValue
):
    return [
        sg.Text(text),
        sg.Button(
            "",
            key=keySub,
            button_color=(sg.theme_background_color(), sg.theme_background_color()),
            image_filename="/home/pi/Desktop/git/Design-IV/UI/minus_sign.png",
            image_size=(35, 35),
            image_subsample=2,
        ),
        sg.Slider(
            key=keySlider,
            range=(minValue, maxValue),
            default_value=defaultValue,
            size=(20, 5),
            orientation="horizontal",
            # font=("Helvetica", 12),
            resolution=0.5,
            enable_events=True,
        ),
        sg.Button(
            "",
            key=keyAdd,
            button_color=(sg.theme_background_color(), sg.theme_background_color()),
            image_filename="/home/pi/Desktop/git/Design-IV/UI/plus_sign.png",
            image_size=(35, 35),
            image_subsample=2,
        ),
    ]


def nouvelAppareilPopup():
    return [sg.OptionMenu(["Unité de chauffage", "Ventilateur", "Lumière"], s=(15, 2))]


def controleHeures(
    keyHeuresA, keyMinutesA, keyHeuresE, keyMinutesE, keyCheckBoxTimers, keyControlTimer
):
    return [
        [
            sg.Text("Heure d'allumage"),
            sg.Combo(Combos.hours, key=keyHeuresA, default_value=8, enable_events=True),
            sg.Combo(
                Combos.minutes, key=keyMinutesA, default_value=0, enable_events=True
            ),
            sg.Text("Heure d'éteignement"),
            sg.Combo(
                Combos.hours, key=keyHeuresE, default_value=16, enable_events=True
            ),
            sg.Combo(
                Combos.minutes, key=keyMinutesE, default_value=0, enable_events=True
            ),
        ]
    ]


def etatMachine(keyText, textDescription):
    return [
        sg.T(textDescription, key=keyText),
        sg.Image(
            key=ComponentKeys.allKeys[keyText]["StateImage"],
            filename="/home/pi/Desktop/git/Design-IV/UI/red_power_sign.png",
            background_color=sg.theme_background_color(),
        ),
    ]


class Components:
    def __init__(self):
        self.frame_inputs_layout = [
            Slider2button(
                "Température (°C) ",
                ComponentKeys.allKeys["Temp"]["Sub"],
                ComponentKeys.allKeys["Temp"]["Slider"],
                ComponentKeys.allKeys["Temp"]["Add"],
                ComponentKeys.allKeys["Temp"]["Range"],
                0,
                35,
                20,
            ),
            Slider2button(
                "Humidité (%)",
                ComponentKeys.allKeys["Humidity"]["Sub"],
                ComponentKeys.allKeys["Humidity"]["Slider"],
                ComponentKeys.allKeys["Humidity"]["Add"],
                ComponentKeys.allKeys["Humidity"]["Range"],
                0,
                100,
                80,
            ),
            Slider2button(
                "Taux de CO2 (ppm)",
                ComponentKeys.allKeys["CO2"]["Sub"],
                ComponentKeys.allKeys["CO2"]["Slider"],
                ComponentKeys.allKeys["CO2"]["Add"],
                ComponentKeys.allKeys["CO2"]["Range"],
                400,
                1000,
                600,
            ),
        ]
        self.frame_hours_control_pompe = [
            [
                sg.T("Choix de la zone à controler :"),
                sg.Combo(
                    [1, 2, 3, 4],
                    key=ComponentKeys.allKeys["Pompe"]["Zone"],
                    default_value=1,
                    enable_events=True,
                ),
                sg.Checkbox(
                    "On/Off",
                    key=ComponentKeys.allKeys["Pompe"]["OnOffManual"],
                    default=False,
                    enable_events=True,
                ),
            ],
            Slider2ButtonNoRange(
                "Temps entre les arrosages(min)",
                ComponentKeys.allKeys["Pompe"]["Sub"],
                ComponentKeys.allKeys["Pompe"]["Slider"],
                ComponentKeys.allKeys["Pompe"]["Add"],
                ComponentKeys.allKeys["Pompe"]["Range"],
                0,
                120,
                10,
            ),
        ]
        self.frame_hours_control_moteur = [
            [
                sg.T("Temps d'ouverture des volets(s) : "),
                sg.Combo(Combos.minutes, key="VoletsTempsOuverture", default_value=10),
            ],
            [
                sg.Checkbox(
                    "Contrôle manuel",
                    key="MoteurControleManuel",
                    default=False,
                    enable_events=True,
                ),
                sg.Button("Ouvrir", key="MotorOnButton", button_color="grey"),
                sg.B("Fermer", key="MotorOffButton", button_color="red"),
            ],
        ]

        self.frame_hours_control_lumiere = controleHeures(
            ComponentKeys.allKeys["Lumiere"]["AllumeH"],
            ComponentKeys.allKeys["Lumiere"]["AllumeM"],
            ComponentKeys.allKeys["Lumiere"]["EteintH"],
            ComponentKeys.allKeys["Lumiere"]["EteintM"],
            ComponentKeys.allKeys["Lumiere"]["TimerUsed"],
            ComponentKeys.allKeys["Lumiere"]["OnOffManual"],
        )
        self.frame_machines_state = [
            etatMachine("Ventilateur", "Ventilation"),
            etatMachine("Moteur", "Moteur des volets"),
            etatMachine("Pompe", "Pompe"),
            etatMachine("Temp", "Chauffage"),
            etatMachine("Lumiere", "Lumière"),
        ]
        self.frame_capteurs_state = [
            [
                sg.T("Température ambiante : "),
                sg.T("20", key="TempMoy"),
                sg.T("Humidité moyenne : "),
                sg.T("", key="HumidMoy"),
            ],
            [
                sg.T("Température capteur 1 : "),
                sg.T("", key="temp_int_1"),
                sg.T("Humidité capteur 1 : "),
                sg.T("", key="hum_int_1"),
            ],
            [
                sg.T("Température capteur 2 : "),
                sg.T("", key="temp_int_2"),
                sg.T("Humidité capteur 2 : "),
                sg.T("", key="hum_int_2"),
            ],
            [
                sg.T("Température extérieure: "),
                sg.T("", key="temp_ext"),
                sg.T("Humidité extérieure: "),
                sg.T("", key="hum_ext"),
            ],
            [
                sg.T("CO2 capteur 1 : "),
                sg.T("", key="CO2_int_1"),
                sg.T("CO2 capteur 2 : "),
                sg.T("", key="CO2_int_2"),
            ],
        ]

        self.layout = [
            [
                sg.Frame(
                    "Consignes de contrôles",
                    self.frame_inputs_layout,
                    title_color="white",
                    element_justification="r",
                ),
                sg.Frame(
                    "État de la machinerie",
                    self.frame_machines_state,
                    title_color="white",
                    element_justification="right",
                ),
            ],
            [
                sg.Frame(
                    "Contrôle des Pompes",
                    self.frame_hours_control_pompe,
                    title_color="white",
                )
            ],
            [
                sg.Frame(
                    "Contrôle de la lumière",
                    self.frame_hours_control_lumiere,
                    title_color="white",
                )
            ],
            [
                sg.Frame(
                    "Valeurs des capteurs",
                    self.frame_capteurs_state,
                    title_color="white",
                ),
                sg.Frame(
                    "Contrôle des moteurs des volets",
                    self.frame_hours_control_moteur,
                    title_color="white",
                    element_justification="c",
                ),
            ],
            [sg.B("Minimiser"), sg.Cancel("Fermer")],
            [
                sg.T(
                    "ATTENTION LE NIVEAU DE CO2 EST TROP ÉLEVÉ!",
                    key="CO2WarningText",
                    visible=False,
                    font=("Helvetica bold", 20),
                    text_color="red",
                )
            ],
            [sg.B("Minimiser")],
        ]

    def __del__(self):
        self.layout = None
        self.frame_inputs_layout = None
        self.frame_hours_control_pompe = None
        self.frame_hours_control_moteur = None
        self.frame_hours_control_lumiere = None
        self.frame_machines_state = None
        self.frame_capteurs_state = None
