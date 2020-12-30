import unittest.mock

import pytest

# pylint: disable=protected-access


def test__enable_receive_mode(transceiver):
    transceiver._spi.xfer.return_value = [15]
    transceiver._enable_receive_mode()
    transceiver._spi.xfer.assert_called_once_with([0x34 | 0x00])


@pytest.mark.parametrize("payload", [b"\0", b"\x12\x45\x56"])
def test__get_received_packet(transceiver, payload):
    fifo_buffer = list(payload) + [128, (1 << 7) | 42]
    with unittest.mock.patch.object(
        transceiver, "_read_status_register", return_value=len(fifo_buffer)
    ) as read_status_register, unittest.mock.patch.object(
        transceiver, "_read_burst", return_value=fifo_buffer
    ) as read_burst_mock:
        received_packet = transceiver._get_received_packet()
    read_status_register.assert_called_once_with(0x3B)
    read_burst_mock.assert_called_once_with(
        start_register=0x3F, length=len(fifo_buffer)
    )
    assert received_packet.payload == payload
    assert received_packet._rssi_index == 128
    assert received_packet.checksum_valid
    assert received_packet.link_quality_indicator == 42
