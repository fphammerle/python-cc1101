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

import pytest

# pylint: disable=protected-access


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
