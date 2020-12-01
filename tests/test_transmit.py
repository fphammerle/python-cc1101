import unittest.mock

import pytest

import cc1101.options


def test_transmit_empty_payload(transceiver):
    with unittest.mock.patch.object(
        transceiver,
        "get_packet_length_mode",
        return_value=cc1101.options.PacketLengthMode.VARIABLE,
    ), unittest.mock.patch.object(
        transceiver, "get_packet_length_bytes", return_value=21
    ):
        with pytest.raises(ValueError, match=r"\bempty\b"):
            transceiver.transmit([])


@pytest.mark.parametrize("payload", (b"\0\x01\x02", [0, 127]))
def test_transmit_first_null(transceiver, payload):
    with unittest.mock.patch.object(
        transceiver,
        "get_packet_length_mode",
        return_value=cc1101.options.PacketLengthMode.VARIABLE,
    ), unittest.mock.patch.object(
        transceiver, "get_packet_length_bytes", return_value=21
    ):
        with pytest.raises(ValueError, match=r"\bfirst byte\b.*\bmust not be null\b"):
            transceiver.transmit(payload)


@pytest.mark.parametrize(
    ("max_packet_length", "payload"),
    ((3, "\x04\x01\x02\x03"), (4, [7, 21, 42, 0, 0, 1, 2, 3])),
)
def test_transmit_exceeding_max_length(transceiver, max_packet_length, payload):
    with unittest.mock.patch.object(
        transceiver,
        "get_packet_length_mode",
        return_value=cc1101.options.PacketLengthMode.VARIABLE,
    ), unittest.mock.patch.object(
        transceiver, "get_packet_length_bytes", return_value=max_packet_length
    ):
        with pytest.raises(
            ValueError, match=r"\bpayload exceeds maximum payload length\b"
        ):
            transceiver.transmit(payload)


@pytest.mark.parametrize(
    ("packet_length", "payload"),
    ((3, "\x04\x01\x02\x03"), (4, [7, 21, 42, 0, 0, 1, 2, 3])),
)
def test_transmit_unexpected_payload_len(transceiver, packet_length, payload):
    with unittest.mock.patch.object(
        transceiver,
        "get_packet_length_mode",
        return_value=cc1101.options.PacketLengthMode.FIXED,
    ), unittest.mock.patch.object(
        transceiver, "get_packet_length_bytes", return_value=packet_length
    ):
        with pytest.raises(ValueError, match=r"\bpayload length\b"):
            transceiver.transmit(payload)
