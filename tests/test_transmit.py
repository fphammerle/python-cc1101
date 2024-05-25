import logging
import unittest.mock

import pytest

import cc1101.addresses
import cc1101.options

# pylint: disable=protected-access


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


def test_transmit_not_idle(transceiver: cc1101.CC1101) -> None:
    with unittest.mock.patch.object(
        transceiver,
        "get_packet_length_mode",
        return_value=cc1101.options.PacketLengthMode.VARIABLE,
    ), unittest.mock.patch.object(
        transceiver, "get_packet_length_bytes", return_value=42 // 2
    ), unittest.mock.patch.object(
        transceiver,
        "get_main_radio_control_state_machine_state",
        return_value=cc1101.MainRadioControlStateMachineState.RX,
    ), pytest.raises(
        RuntimeError,
        match=r"^device must be idle before transmission \(current marcstate: RX\)$",
    ):
        transceiver.transmit(b"\x01\x02\x03")
    transceiver._spi.xfer.assert_not_called()


@pytest.mark.parametrize("payload", (b"\0", b"\xaa\xbb\xcc", bytes(range(42))))
def test_transmit_fixed(caplog, transceiver, payload):
    transceiver._spi.xfer.side_effect = lambda v: [15] * len(v)
    with unittest.mock.patch.object(
        transceiver,
        "get_packet_length_mode",
        return_value=cc1101.options.PacketLengthMode.FIXED,
    ), unittest.mock.patch.object(
        transceiver, "get_packet_length_bytes", return_value=len(payload)
    ), unittest.mock.patch.object(
        transceiver,
        "get_main_radio_control_state_machine_state",
        return_value=cc1101.MainRadioControlStateMachineState.IDLE,
    ), caplog.at_level(
        logging.INFO
    ):
        transceiver.transmit(payload)
    assert transceiver._spi.xfer.call_args_list == [
        unittest.mock.call([0x3B]),  # flush
        unittest.mock.call([0x3F | 0x40] + list(payload)),
        unittest.mock.call([0x35]),  # start transmission
    ]
    assert caplog.record_tuples == [
        (
            "cc1101",
            20,
            "transmitting 0x{} ({!r})".format(  # pylint: disable=consider-using-f-string
                "".join(f"{b:02x}" for b in payload), payload
            ),
        )
    ]


@pytest.mark.parametrize(
    "payload", (b"\x01\0", b"\x03\xaa\xbb\xcc", b"\x10" + bytes(range(16)))
)
def test_transmit_variable(transceiver, payload):
    transceiver._spi.xfer.side_effect = lambda v: [15] * len(v)
    with unittest.mock.patch.object(
        transceiver,
        "get_packet_length_mode",
        return_value=cc1101.options.PacketLengthMode.VARIABLE,
    ), unittest.mock.patch.object(
        transceiver, "get_packet_length_bytes", return_value=255
    ), unittest.mock.patch.object(
        transceiver,
        "get_main_radio_control_state_machine_state",
        return_value=cc1101.MainRadioControlStateMachineState.IDLE,
    ):
        transceiver.transmit(payload)
    assert transceiver._spi.xfer.call_args_list == [
        unittest.mock.call([0x3B]),  # flush
        unittest.mock.call([0x3F | 0x40] + [len(payload)] + list(payload)),
        unittest.mock.call([0x35]),  # start transmission
    ]


def test_asynchronous_transmission(transceiver: cc1101.CC1101) -> None:
    with unittest.mock.patch.object(
        transceiver, "_set_transceive_mode"
    ) as set_mode_mock, unittest.mock.patch.object(
        transceiver, "_command_strobe"
    ) as command_mock:
        with transceiver.asynchronous_transmission() as input_pin:
            set_mode_mock.assert_called_once_with(
                cc1101.options._TransceiveMode.ASYNCHRONOUS_SERIAL
            )
            set_mode_mock.reset_mock()
            command_mock.assert_called_once_with(cc1101.addresses.StrobeAddress.STX)
            command_mock.reset_mock()
            transceiver._spi.xfer.assert_not_called()
            assert input_pin == cc1101.Pin.GDO0
        set_mode_mock.assert_called_once_with(cc1101.options._TransceiveMode.FIFO)
        command_mock.assert_called_once_with(cc1101.addresses.StrobeAddress.SIDLE)
        transceiver._spi.xfer.assert_not_called()
