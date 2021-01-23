import logging

import cc1101


logging.basicConfig(level=logging.INFO)

with cc1101.CC1101() as transceiver:
    transceiver.set_base_frequency_hertz(433.5e6)
    transceiver.set_symbol_rate_baud(600)
    transceiver.set_sync_mode(cc1101.SyncMode.NO_PREAMBLE_AND_SYNC_WORD)
    transceiver.set_packet_length_mode(cc1101.PacketLengthMode.FIXED)
    transceiver.set_packet_length_bytes(4)
    transceiver.disable_checksum()
    transceiver.set_output_power((0, 0xC0))  # OOK modulation: (off, on)
    print(transceiver)
    transceiver.transmit(b"\xff\x00\xaa\xff")
