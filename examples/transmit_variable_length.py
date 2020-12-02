import logging
import time

import cc1101


logging.basicConfig(level=logging.INFO)

with cc1101.CC1101() as transceiver:
    print("defaults:", transceiver)
    transceiver.set_base_frequency_hertz(433.5e6)
    transceiver.set_symbol_rate_baud(600)
    # transceiver.set_sync_mode(cc1101.SyncMode.NO_PREAMBLE_AND_SYNC_WORD)
    # transceiver.disable_checksum()
    print(transceiver)
    print("state", transceiver.get_marc_state().name)
    print("base frequency", transceiver.get_base_frequency_hertz(), "Hz")
    print("symbol rate", transceiver.get_symbol_rate_baud(), "Baud")
    print("modulation format", transceiver.get_modulation_format().name)
    print("starting transmission")
    transceiver.transmit(b"\xff\xaa\x00 message")
    time.sleep(1.0)
    transceiver.transmit(bytes([0, 0b10101010, 0xFF]))
    for i in range(16):
        time.sleep(1.0)
        transceiver.transmit(bytes([i, i, i]))
