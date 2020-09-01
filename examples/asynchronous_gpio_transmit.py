import logging
import time

from RPi import GPIO

import cc1101

logging.basicConfig(level=logging.INFO)

_GDO0_PIN = 18  # GPIO24

GPIO.setmode(GPIO.BOARD)
GPIO.setup(_GDO0_PIN, GPIO.OUT, initial=GPIO.LOW)

with cc1101.CC1101() as transceiver:
    transceiver.set_base_frequency_hertz(433.92e6)
    transceiver.set_symbol_rate_baud(600)
    print(transceiver)
    print("starting transmission")
    with transceiver.asynchronous_transmission():
        while True:
            print(1, end="", flush=True)
            GPIO.output(_GDO0_PIN, GPIO.HIGH)
            time.sleep(1.0)
            print(0, end="", flush=True)
            GPIO.output(_GDO0_PIN, GPIO.LOW)
            time.sleep(1.0)
