# python-cc1101 - Python Library to Transmit RF Signals via CC1101 Transceivers
#
# Copyright (C) 2024 Fabian Peter Hammerle <fabian@hammerle.me>
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

import cc1101

# pylint: disable=protected-access


@pytest.mark.parametrize(
    ("freq210", "frequency_hertz"),
    [((0x10, 0xB0, 0x71), 433920000), ((0x21, 0x62, 0x76), 868000000)],
)
def test_get_base_frequency_hertz(
    transceiver: cc1101.CC1101,
    freq210: tuple[int, int, int],
    frequency_hertz: int,
) -> None:
    transceiver._spi.xfer.return_value = [0] + list(freq210)
    assert transceiver.get_base_frequency_hertz() == pytest.approx(
        frequency_hertz, abs=170
    )
    transceiver._spi.xfer.assert_called_once_with([0x0D | 0xC0, 0, 0, 0])


@pytest.mark.parametrize(
    ("freq210", "frequency_hertz"),
    [((0x10, 0xB0, 0x71), 433920000), ((0x21, 0x62, 0x76), 868000000)],
)
def test_set_base_frequency_hertz(
    transceiver: cc1101.CC1101,
    freq210: tuple[int, int, int],
    frequency_hertz: int,
) -> None:
    transceiver._spi.xfer.return_value = [15] * (1 + 3)
    transceiver.set_base_frequency_hertz(frequency_hertz)
    transceiver._spi.xfer.assert_called_once_with([0x0D | 0x40] + list(freq210))
