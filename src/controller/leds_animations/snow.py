from random import randint
from time import sleep
from modules.leds import LedsModule
import threading
import time

def snow(leds: LedsModule, stop_event: threading.Event, duration: float = None):
    """Snow animation migrated from unicorn-hat example."""
    width, height = leds.width, leds.height
    rows = []
    row_pointer = 0
    def get_blank_row():
        return [0] * width
    def get_new_row():
        row = get_blank_row()
        row[randint(0, width - 1)] = 50 + randint(0, 155)
        return row
    def update_display():
        c = row_pointer
        for h in range(height):
            for w in range(width):
                val = rows[c][w]
                leds.set_pixel((width - 1) - w, (height - 1) - h, val, val, val)
            c += 1
            if c > height - 1:
                c = 0
        leds.show()
    def step():
        nonlocal row_pointer
        rows[row_pointer] = get_new_row()
        update_display()
        row_pointer -= 1
        if row_pointer < 0:
            row_pointer = height - 1
    for _ in range(height):
        rows.append(get_blank_row())
    start_time = time.time()
    while not stop_event.is_set():
        if duration is not None and (time.time() - start_time) > duration:
            break
        step()
        sleep(0.3)
