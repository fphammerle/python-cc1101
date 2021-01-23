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
    ("frend0", "setting_index"),
    [
        (0b01000, 0),
        (0b01001, 1),
        (0b01111, 7),
        (0b10000, 0),
        (0b10001, 1),
        (0b10111, 7),
        (0b10101, 5),
    ],
)
def test__get_power_amplifier_setting_index(transceiver, frend0, setting_index):
    transceiver._spi.xfer.return_value = [15, frend0]
    assert transceiver._get_power_amplifier_setting_index() == setting_index
    transceiver._spi.xfer.assert_called_once_with([0x22 | 0x80, 0])


@pytest.mark.parametrize(
    ("frend0_before", "frend0_after", "setting_index"),
    [
        (0b01000, 0b01000, 0),
        (0b01000, 0b01001, 1),
        (0b01000, 0b01111, 7),
        (0b10000, 0b10000, 0),
        (0b10000, 0b10001, 1),
        (0b10000, 0b10111, 7),
    ],
)
def test__set_power_amplifier_setting_index(
    transceiver, frend0_before, frend0_after, setting_index
):
    transceiver._spi.xfer.return_value = [15, 15]
    with unittest.mock.patch.object(
        transceiver, "_read_single_byte", return_value=frend0_before
    ):
        transceiver._set_power_amplifier_setting_index(setting_index)
    transceiver._spi.xfer.assert_called_once_with([0x22 | 0x40, frend0_after])


@pytest.mark.parametrize("setting_index", (-1, 8, 21))
def test__set_power_amplifier_setting_index_invalid(transceiver, setting_index):
    with pytest.raises(Exception):
        transceiver._set_power_amplifier_setting_index(setting_index)
    transceiver._spi.xfer.assert_not_called()
