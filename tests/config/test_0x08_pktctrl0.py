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

from cc1101.options import PacketLengthMode

# pylint: disable=protected-access


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
