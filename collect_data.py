import csv
import os
import time
from datetime import datetime

from pynput import keyboard, mouse


# ==============================
# SETTINGS
# ==============================

DATASET_FOLDER = "dataset/user_002"

os.makedirs(DATASET_FOLDER, exist_ok=True)

session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = os.path.join(
    DATASET_FOLDER,
    f"session_{session_id}.csv"
)

start_time = time.perf_counter()

events = []

pressed_keys = {}
last_key_time = None
last_mouse_time = None
last_mouse_x = None
last_mouse_y = None


# ==============================
# HELPER
# ==============================

def get_time():
    return time.perf_counter() - start_time


# ==============================
# KEYBOARD
# ==============================

def on_key_press(key):
    global last_key_time

    timestamp = get_time()

    # Do NOT store the actual key.
    key_name = "key"

    # Ignore duplicate press events while the key is already held
    if key in pressed_keys:
        return

    hold_start = timestamp
    pressed_keys[key] = hold_start

    if last_key_time is None:
        flight_time = ""
    else:
        flight_time = timestamp - last_key_time

    events.append({
        "timestamp": timestamp,
        "device": "keyboard",
        "event": "key_press",
        "x": "",
        "y": "",
        "dx": "",
        "dy": "",
        "distance": "",
        "velocity": "",
        "hold_time": "",
        "flight_time": flight_time
    })

    last_key_time = timestamp


def on_key_release(key):
    timestamp = get_time()

    if key in pressed_keys:
        hold_time = timestamp - pressed_keys[key]
        del pressed_keys[key]
    else:
        hold_time = ""

    events.append({
        "timestamp": timestamp,
        "device": "keyboard",
        "event": "key_release",
        "x": "",
        "y": "",
        "dx": "",
        "dy": "",
        "distance": "",
        "velocity": "",
        "hold_time": hold_time,
        "flight_time": ""
    })

    # ESC stops the collection
    if key == keyboard.Key.esc:
        return False


# ==============================
# MOUSE MOVEMENT
# ==============================

def on_move(x, y):
    global last_mouse_time
    global last_mouse_x
    global last_mouse_y

    timestamp = get_time()

    if last_mouse_x is None:
        dx = 0
        dy = 0
        distance = 0
        velocity = 0
    else:
        dx = x - last_mouse_x
        dy = y - last_mouse_y

        distance = (dx ** 2 + dy ** 2) ** 0.5

        time_difference = timestamp - last_mouse_time

        if time_difference > 0:
            velocity = distance / time_difference
        else:
            velocity = 0

    events.append({
        "timestamp": timestamp,
        "device": "mouse",
        "event": "move",
        "x": x,
        "y": y,
        "dx": dx,
        "dy": dy,
        "distance": distance,
        "velocity": velocity,
        "hold_time": "",
        "flight_time": ""
    })

    last_mouse_x = x
    last_mouse_y = y
    last_mouse_time = timestamp


# ==============================
# MOUSE CLICK
# ==============================

def on_click(x, y, button, pressed):

    timestamp = get_time()

    events.append({
        "timestamp": timestamp,
        "device": "mouse",
        "event": f"click_{'press' if pressed else 'release'}",
        "x": x,
        "y": y,
        "dx": "",
        "dy": "",
        "distance": "",
        "velocity": "",
        "hold_time": "",
        "flight_time": ""
    })


# ==============================
# MOUSE SCROLL
# ==============================

def on_scroll(x, y, dx, dy):

    timestamp = get_time()

    events.append({
        "timestamp": timestamp,
        "device": "mouse",
        "event": "scroll",
        "x": x,
        "y": y,
        "dx": dx,
        "dy": dy,
        "distance": "",
        "velocity": "",
        "hold_time": "",
        "flight_time": ""
    })


# ==============================
# START
# ==============================

print("=" * 50)
print("CONTINUOUS AUTHENTICATION DATA COLLECTOR")
print("=" * 50)

print("\nSession ID:", session_id)

print("\nData being collected:")
print("✓ Keyboard timing")
print("✓ Key hold duration")
print("✓ Time between keystrokes")
print("✓ Mouse movement")
print("✓ Mouse speed")
print("✓ Mouse clicks")
print("✓ Mouse scrolling")

print("\nActual typed characters are NOT stored.")
print("\nStart using your laptop normally.")
print("Press ESC to stop collection.\n")


keyboard_listener = keyboard.Listener(
    on_press=on_key_press,
    on_release=on_key_release
)

mouse_listener = mouse.Listener(
    on_move=on_move,
    on_click=on_click,
    on_scroll=on_scroll
)

keyboard_listener.start()
mouse_listener.start()

keyboard_listener.join()
mouse_listener.stop()
mouse_listener.join()


# ==============================
# SAVE DATA
# ==============================

fieldnames = [
    "timestamp",
    "device",
    "event",
    "x",
    "y",
    "dx",
    "dy",
    "distance",
    "velocity",
    "hold_time",
    "flight_time"
]

with open(output_file, "w", newline="", encoding="utf-8") as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(events)


print("\n" + "=" * 50)
print("DATA COLLECTION FINISHED")
print("=" * 50)

print("\nTotal events collected:", len(events))
print("Dataset saved at:")
print(output_file)