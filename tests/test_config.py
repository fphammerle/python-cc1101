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
import warnings

import pytest

import cc1101
from cc1101.options import PacketLengthMode

# pylint: disable=protected-access


@pytest.mark.parametrize(
    ("xfer_return_value", "sync_word"),
    [([64, 211, 145], b"\xd3\x91"), ([64, 0, 0], b"\0\0")],
)
def test_get_sync_word(transceiver, xfer_return_value, sync_word):
    transceiver._spi.xfer.return_value = xfer_return_value
    assert transceiver.get_sync_word() == sync_word
    transceiver._spi.xfer.assert_called_once_with([0x04 | 0xC0, 0, 0])


def test_set_sync_word(transceiver):
    transceiver._spi.xfer.return_value = [15, 15, 15]
    transceiver.set_sync_word(b"\x12\x34")
    transceiver._spi.xfer.assert_called_once_with([0x04 | 0x40, 0x12, 0x34])


@pytest.mark.parametrize("sync_word", [b"", b"\0", "\x12\x34\x56"])
def test_set_sync_word_invalid_length(transceiver, sync_word):
    with pytest.raises(ValueError, match=r"\bexpected two bytes\b"):
        transceiver.set_sync_word(sync_word)


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


_FILTER_BANDWIDTH_MANTISSA_EXPONENT_REAL_PARAMS = [
    # > The default values give 203 kHz channel filter bandwidth,
    # > assuming a 26.0 MHz crystal.
    (0, 2, 203e3),
    # "Table 26: Channel Filter Bandwidths [kHz] (assuming a 26 MHz crystal)"
    (0, 0, 812e3),
    (0, 1, 406e3),
    (0, 2, 203e3),
    (1, 0, 650e3),
    (1, 1, 325e3),
    (3, 0, 464e3),
    (3, 1, 232e3),
    (3, 2, 116e3),
    (3, 3, 58e3),
]


@pytest.mark.parametrize(
    ("mantissa", "exponent", "real"), _FILTER_BANDWIDTH_MANTISSA_EXPONENT_REAL_PARAMS
)
def test__filter_bandwidth_floating_point_to_real(mantissa, exponent, real):
    assert cc1101.CC1101._filter_bandwidth_floating_point_to_real(
        mantissa=mantissa, exponent=exponent
    ) == pytest.approx(real, rel=1e-3)


@pytest.mark.parametrize(
    ("mdmcfg4", "real"),
    [
        (0b10001100, 203e3),
        (0b10001010, 203e3),
        (0b10001110, 203e3),
        (0b11111100, 58e3),
        (0b01011100, 325e3),
    ],
)
def test__get_filter_bandwidth_hertz(transceiver, mdmcfg4, real):
    transceiver._spi.xfer.return_value = [15, mdmcfg4]
    assert transceiver._get_filter_bandwidth_hertz() == pytest.approx(real, rel=1e-3)
    transceiver._spi.xfer.assert_called_once_with([0x10 | 0x80, 0])


@pytest.mark.parametrize(
    ("mdmcfg4_before", "mdmcfg4_after", "exponent", "mantissa"),
    [
        (0b00001010, 0b10111010, 0b10, 0b11),
        (0b00001100, 0b01001100, 0b01, 0b00),
        (0b00001100, 0b10111100, 0b10, 0b11),
        (0b00001100, 0b11011100, 0b11, 0b01),
        (0b01011100, 0b11011100, 0b11, 0b01),
        (0b11111100, 0b11011100, 0b11, 0b01),
    ],
)
def test__set_filter_bandwidth(
    transceiver, mdmcfg4_before, mdmcfg4_after, exponent, mantissa
):
    transceiver._spi.xfer.return_value = [15, 15]
    with unittest.mock.patch.object(
        transceiver, "_read_single_byte", return_value=mdmcfg4_before
    ):
        transceiver._set_filter_bandwidth(mantissa=mantissa, exponent=exponent)
    transceiver._spi.xfer.assert_called_once_with([0x10 | 0x40, mdmcfg4_after])


@pytest.mark.parametrize(
    ("mdmcfg4", "symbol_rate_exponent"), [(0b1001100, 12), (0b10011001, 9)]
)
def test__get_symbol_rate_exponent(transceiver, mdmcfg4, symbol_rate_exponent):
    transceiver._spi.xfer.return_value = [15, mdmcfg4]
    assert transceiver._get_symbol_rate_exponent() == symbol_rate_exponent
    transceiver._spi.xfer.assert_called_once_with([0x10 | 0x80, 0])


@pytest.mark.parametrize(
    ("mdmcfg3", "symbol_rate_mantissa"), [(0b00100010, 34), (0b10101010, 170)]
)
def test__get_symbol_rate_mantissa(transceiver, mdmcfg3, symbol_rate_mantissa):
    transceiver._spi.xfer.return_value = [15, mdmcfg3]
    assert transceiver._get_symbol_rate_mantissa() == symbol_rate_mantissa
    transceiver._spi.xfer.assert_called_once_with([0x11 | 0x80, 0])


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


@pytest.mark.parametrize(
    ("mdmcfg1", "length"),
    [
        (0b00000010, 2),
        (0b00010010, 3),
        (0b00100010, 4),
        (0b00110010, 6),
        (0b01000010, 8),
        (0b01010010, 12),
        (0b01100010, 16),
        (0b01110010, 24),
    ],
)
def test_get_preamble_length_bytes(transceiver, mdmcfg1, length):
    transceiver._spi.xfer.return_value = [0, mdmcfg1]
    assert transceiver.get_preamble_length_bytes() == length
    transceiver._spi.xfer.assert_called_once_with([0x13 | 0x80, 0])


@pytest.mark.parametrize(
    ("mdmcfg1_before", "mdmcfg1_after", "length"),
    [
        (0b00000010, 0b00000010, 2),
        (0b00000010, 0b00010010, 3),
        (0b00000010, 0b00100010, 4),
        (0b00000010, 0b00110010, 6),
        (0b00000010, 0b01000010, 8),
        (0b00000010, 0b01010010, 12),
        (0b00000010, 0b01100010, 16),
        (0b00000010, 0b01110010, 24),
        (0b01010010, 0b01100010, 16),
        (0b01110010, 0b00000010, 2),
        (0b01110010, 0b01000010, 8),
        (0b11011010, 0b11101010, 16),
        (0b11110111, 0b11000111, 8),
        (0b11111110, 0b10001110, 2),
    ],
)
def test_set_preamble_length_bytes(transceiver, mdmcfg1_before, mdmcfg1_after, length):
    transceiver._spi.xfer.return_value = [15, 15]
    with unittest.mock.patch.object(
        transceiver, "_read_single_byte", return_value=mdmcfg1_before
    ):
        transceiver.set_preamble_length_bytes(length)
    transceiver._spi.xfer.assert_called_once_with([0x13 | 0x40, mdmcfg1_after])


@pytest.mark.parametrize(
    "length", [-21, 0, 1, 5, 7, 9, 10, 11, 13, 14, 15, 17, 20, 23, 25, 32, 42]
)
def test_set_preamble_length_bytes_invalid(transceiver, length):
    with pytest.raises(ValueError, match=r"\bpreamble length\b"):
        transceiver.set_preamble_length_bytes(length)


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
        (0b00000000, PacketLengthMode.FIXED),
        (0b00000001, PacketLengthMode.VARIABLE),
        (0b01000100, PacketLengthMode.FIXED),
        (0b01000101, PacketLengthMode.VARIABLE),
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
        (0b00000000, 0b00000000, PacketLengthMode.FIXED),
        (0b00000001, 0b00000000, PacketLengthMode.FIXED),
        (0b00000001, 0b00000001, PacketLengthMode.VARIABLE),
        (0b00000010, 0b00000000, PacketLengthMode.FIXED),
        (0b00000010, 0b00000001, PacketLengthMode.VARIABLE),
        (0b01000100, 0b01000100, PacketLengthMode.FIXED),
        (0b01000100, 0b01000101, PacketLengthMode.VARIABLE),
        (0b01000101, 0b01000100, PacketLengthMode.FIXED),
        (0b01000101, 0b01000101, PacketLengthMode.VARIABLE),
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


@pytest.mark.parametrize(
    ("freq_hz", "warn"),
    (
        (100e6, True),
        (281.6e6, True),
        (281.65e6, False),  # within tolerance
        (281.7e6, False),
        (433.92e6, False),
    ),
)
def test_set_base_frequency_hertz_low_warning(transceiver, freq_hz, warn):
    with unittest.mock.patch.object(
        transceiver, "_set_base_frequency_control_word"
    ) as set_control_word_mock:
        with warnings.catch_warnings(record=True) as caught_warnings:
            transceiver.set_base_frequency_hertz(freq_hz)
    assert set_control_word_mock.call_count == 1
    if warn:
        assert len(caught_warnings) == 1
        assert (
            str(caught_warnings[0].message)
            == "CC1101 is unable to transmit at frequencies below 281.7 MHz"
        )
    else:
        assert not caught_warnings
