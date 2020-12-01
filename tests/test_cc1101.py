# python-cc1101 - Python Library to Transmit RF Signals via C1101 Transceivers
#
# Copyright (C) 2020 Fabian Peter Hammerle <fabian@hammerle.me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import unittest.mock

import pytest

import cc1101
import cc1101.options

# pylint: disable=protected-access

_FREQUENCY_CONTROL_WORD_HERTZ_PARAMS = [
    ([0x10, 0xA7, 0x62], 433000000),
    ([0x10, 0xAB, 0x85], 433420000),
    ([0x10, 0xB1, 0x3B], 434000000),
    ([0x21, 0x62, 0x76], 868000000),
]


@pytest.mark.parametrize(
    ("control_word", "hertz"), _FREQUENCY_CONTROL_WORD_HERTZ_PARAMS
)
def test__frequency_control_word_to_hertz(control_word, hertz):
    assert cc1101.CC1101._frequency_control_word_to_hertz(
        control_word
    ) == pytest.approx(hertz, abs=200)


@pytest.mark.parametrize(
    ("control_word", "hertz"), _FREQUENCY_CONTROL_WORD_HERTZ_PARAMS
)
def test__hertz_to_frequency_control_word(control_word, hertz):
    assert cc1101.CC1101._hertz_to_frequency_control_word(hertz) == control_word


_SYMBOL_RATE_MANTISSA_EXPONENT_REAL_PARAMS = [
    # > The default values give a data rate of 115.051 kBaud
    # > (closest setting to 115.2 kBaud), assuming a 26.0 MHz crystal.
    (34, 12, 115051),
    (34, 12 + 1, 115051 * 2),
    (34, 12 - 1, 115051 / 2),
]


@pytest.mark.parametrize(
    ("mantissa", "exponent", "real"), _SYMBOL_RATE_MANTISSA_EXPONENT_REAL_PARAMS
)
def test__symbol_rate_floating_point_to_real(mantissa, exponent, real):
    assert cc1101.CC1101._symbol_rate_floating_point_to_real(
        mantissa=mantissa, exponent=exponent
    ) == pytest.approx(real, rel=1e-5)


@pytest.mark.parametrize(
    ("mantissa", "exponent", "real"), _SYMBOL_RATE_MANTISSA_EXPONENT_REAL_PARAMS
)
def test__symbol_rate_real_to_floating_point(mantissa, exponent, real):
    assert cc1101.CC1101._symbol_rate_real_to_floating_point(real) == (
        mantissa,
        exponent,
    )


def test_get_packet_length_bytes(transceiver):
    xfer_mock = transceiver._spi.xfer
    xfer_mock.return_value = [0, 8]
    assert transceiver.get_packet_length_bytes() == 8
    xfer_mock.assert_called_once_with([0x06 | 0x80, 0])


@pytest.mark.parametrize("packet_length", [21])
def test_set_packet_length_bytes(transceiver, packet_length):
    xfer_mock = transceiver._spi.xfer
    xfer_mock.return_value = [15, 15]
    transceiver.set_packet_length_bytes(packet_length)
    xfer_mock.assert_called_once_with([0x06 | 0x40, packet_length])


@pytest.mark.parametrize("packet_length", [-21, 0, 256, 1024])
def test_set_packet_length_bytes_fail(transceiver, packet_length):
    with pytest.raises(Exception):
        transceiver.set_packet_length_bytes(packet_length)
    transceiver._spi.xfer.assert_not_called()


@pytest.mark.parametrize(
    ("pktctrl0_before", "pktctrl0_after"),
    (
        # unchanged
        (0b00000000, 0b00000000),
        (0b00010000, 0b00010000),
        (0b00010001, 0b00010001),
        (0b01000000, 0b01000000),
        (0b01000010, 0b01000010),
        (0b01110000, 0b01110000),
        (0b01110010, 0b01110010),
        # disabled
        (0b00010100, 0b00010000),
        (0b01000100, 0b01000000),
        (0b01000110, 0b01000010),
        (0b01110110, 0b01110010),
    ),
)
def test_disable_checksum(transceiver, pktctrl0_before, pktctrl0_after):
    xfer_mock = transceiver._spi.xfer
    xfer_mock.return_value = [15, 15]
    with unittest.mock.patch.object(
        transceiver, "_read_single_byte", return_value=pktctrl0_before
    ):
        transceiver.disable_checksum()
    xfer_mock.assert_called_once_with([0x08 | 0x40, pktctrl0_after])


@pytest.mark.parametrize(
    ("pktctrl0", "expected_mode"),
    (
        (0b00000000, cc1101.options.PacketLengthMode.FIXED),
        (0b00000001, cc1101.options.PacketLengthMode.VARIABLE),
        (0b01000100, cc1101.options.PacketLengthMode.FIXED),
        (0b01000101, cc1101.options.PacketLengthMode.VARIABLE),
    ),
)
def test_get_packet_length_mode(transceiver, pktctrl0, expected_mode):
    xfer_mock = transceiver._spi.xfer
    xfer_mock.return_value = [0, pktctrl0]
    assert transceiver.get_packet_length_mode() == expected_mode
    xfer_mock.assert_called_once_with([0x08 | 0x80, 0])


@pytest.mark.parametrize(
    ("pktctrl0_before", "pktctrl0_after", "mode"),
    (
        (0b00000000, 0b00000000, cc1101.options.PacketLengthMode.FIXED),
        (0b00000001, 0b00000000, cc1101.options.PacketLengthMode.FIXED),
        (0b00000001, 0b00000001, cc1101.options.PacketLengthMode.VARIABLE),
        (0b00000010, 0b00000000, cc1101.options.PacketLengthMode.FIXED),
        (0b00000010, 0b00000001, cc1101.options.PacketLengthMode.VARIABLE),
        (0b01000100, 0b01000100, cc1101.options.PacketLengthMode.FIXED),
        (0b01000100, 0b01000101, cc1101.options.PacketLengthMode.VARIABLE),
        (0b01000101, 0b01000100, cc1101.options.PacketLengthMode.FIXED),
        (0b01000101, 0b01000101, cc1101.options.PacketLengthMode.VARIABLE),
    ),
)
def test_set_packet_length_mode(transceiver, pktctrl0_before, pktctrl0_after, mode):
    xfer_mock = transceiver._spi.xfer
    xfer_mock.return_value = [15, 15]
    with unittest.mock.patch.object(
        transceiver, "_read_single_byte", return_value=pktctrl0_before
    ):
        transceiver.set_packet_length_mode(mode)
    xfer_mock.assert_called_once_with([0x08 | 0x40, pktctrl0_after])
