# python-cc1101 - Python Library to Transmit RF Signals via CC1101 Transceivers
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

# pylint: disable=protected-access


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
