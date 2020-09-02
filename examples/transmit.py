import logging
import time

import cc1101


logging.basicConfig(level=logging.INFO)

with cc1101.CC1101() as transceiver:
    print("defaults:", transceiver)
    transceiver.set_base_frequency_hertz(433.5e6)
    transceiver.set_symbol_rate_baud(600)
    # transceiver.set_sync_mode(cc1101.SyncMode.NO_PREAMBLE_AND_SYNC_WORD)
    print(transceiver)
    print("state", transceiver.get_marc_state().name)
    print("base frequency", transceiver.get_base_frequency_hertz(), "Hz")
    print("symbol rate", transceiver.get_symbol_rate_baud(), "Baud")
    print("modulation format", transceiver.get_modulation_format().name)
    print("starting transmission")
    transceiver.transmit(b"\x01\xff\x00 message")
    time.sleep(1.0)
    transceiver.transmit(bytes([0x01, 0b10101010, 0xFF]))
    while True:
        time.sleep(1.0)
        transceiver.transmit(bytes(range(1, 16)))
