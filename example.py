import logging
import time

import cc1101


logging.basicConfig(level=logging.INFO)

with cc1101.CC1101() as transceiver:
    print(transceiver)
    transceiver.set_base_frequency_hertz(433e6)
    print(transceiver)
    print("state", transceiver.get_marc_state().name)
    print("base frequency", transceiver.get_base_frequency_hertz(), "Hz")
    print("starting transmission")
    while True:
        transceiver.transmit(list(range(1, 32)))
        time.sleep(2.0)
