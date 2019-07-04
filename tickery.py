from sense_hat import SenseHat, ACTION_PRESSED
from enum import Enum
import bluetooth
import harvest
import time
import os


class OrientationAngles(Enum):
    DEGREE_0 = 0
    DEGREE_90 = 90
    DEGREE_180 = 180
    DEGREE_270 = 270
    DEGREE_STOP = -1
    DEGREE_CHARGE = -2


# configurations
bluetooth_address = '<ENTER_PHONE_BLUETOOTH_ADDRESS_HERE>'


shutting_down = False
sense = SenseHat()
sense.low_light = True
sense.clear()
COLOR_ORANGE = [255, 140, 0]
COLOR_YELLOW = [255, 255, 102]
COLOR_PINK = [255, 20, 147]
COLOR_GREEN = [50, 205, 50]
COLOR_RED = [255, 0, 0]

colors = {0: COLOR_ORANGE,
          90: COLOR_YELLOW,
          180: COLOR_PINK,
          270: COLOR_GREEN}


def show_message(message, color=[255, 0, 0]):
    # print("showing message" + message)
    global sense
    sense.show_message(message, text_colour=color, scroll_speed=0.04)


def initiate_shutdown(event):
    global shutting_down
    if event.action != ACTION_PRESSED:
        return
    shutting_down = True


def get_orientation_angle(coordinates):
    switcher = {
        (1, 0, 0): OrientationAngles.DEGREE_0,
        (0, 0, 1): OrientationAngles.DEGREE_STOP,
        (0, 0, -1): OrientationAngles.DEGREE_STOP,
        (0, 1, 0): OrientationAngles.DEGREE_270,
        (0, -1, 0): OrientationAngles.DEGREE_90,
        (-1, 0, 0): OrientationAngles.DEGREE_180,
        (-1, 0, 1): OrientationAngles.DEGREE_STOP,
    }
    angle = switcher.get(coordinates, OrientationAngles.DEGREE_STOP)
    print("angle, coordinates, {0}, {1}".format(angle.value, coordinates))
    return angle


def get_coordinates():
    x, y, z = sense.get_accelerometer_raw().values()
    x = int(round(x, 0))
    y = int(round(y, 0))
    z = int(round(z, 0))
    return (x, y, z)


def orient_display():
    x, y, z = get_coordinates()
    print("orienting display")
    angle = get_orientation_angle((x, y, z))
    sense.set_rotation(angle.value if angle.value >= 0 else 0)


def display_project_name():
    angle = get_orientation_angle((get_coordinates())).value
    if angle >= 0:
        sense.set_rotation(angle)
    show_message(harvest.get_project_name(angle))


sense.stick.direction_middle = initiate_shutdown
sense.stick.direction_up = display_project_name
sense.stick.direction_down = display_project_name
sense.stick.direction_left = display_project_name
sense.stick.direction_right = display_project_name

last_motion = (0, 0, 0)
iteration_count = 0
last_project_name = ""
color = [0, 0, 0]
timer_stopped = True
while not shutting_down:
    x, y, z = get_coordinates()
    if (x, y, z) != last_motion:
        if abs(x) > 1 or abs(y) > 1 or abs(z) > 1:
            sense.show_letter("!", text_colour=COLOR_PINK)
            time.sleep(2)
            sense.clear()
            continue
        angle = get_orientation_angle((x, y, z)).value
        if angle >= 0:
            color = colors[angle]
            harvest.get_side_mapping()
            sense.set_rotation(angle)
            harvest.start_timer(harvest.get_project_from_angle(angle))
            timer_stopped = False
            last_project_name = harvest.get_project_name(angle)
            show_message(last_project_name, color)
        elif angle == -1:
            harvest.stop_timers()
            timer_stopped = True
            show_message('X', COLOR_PINK)
        last_motion = (x, y, z)
    else:
        iteration_count += 1
        if (iteration_count > 30 and angle >= 0):
            iteration_count = 0
            sense.set_rotation(angle)
            result = bluetooth.lookup_name(bluetooth_address, timeout=2)
            if (result != None):
                if (timer_stopped):
                    harvest.start_timer(harvest.get_project_from_angle(angle))
                    timer_stopped = False
                else:
                    try:
                        time_entries = harvest.get_running_time_entries().json()[
                            'time_entries'][0]
                        timerStr = str(time_entries['hours'])
                        show_message("Time spent: {}h".format(timerStr), color)
                    except IndexError:
                        print("indexError")
            else:
                harvest.stop_timers()
                timer_stopped = True
                show_message("TIME IS PAUSED", COLOR_RED)

    time.sleep(1)


if shutting_down:
    sense.clear()
    orient_display()
    show_message("Powering off now...")
    for i in reversed(range(1, 4)):
        sense.show_letter(str(i))
        time.sleep(1)
    sense.clear()
    os.system("sudo poweroff")
