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


@pytest.mark.parametrize(
    "patable",
    (
        (198, 0, 0, 0, 0, 0, 0, 0),  # default
        (0, 198, 0, 0, 0, 0, 0, 0),  # OOK
        (1, 2, 3, 4, 5, 6, 7, 8),
    ),
)
def test__get_patable(transceiver, patable):
    transceiver._spi.xfer.return_value = [0] + list(patable)
    assert transceiver._get_patable() == patable
    transceiver._spi.xfer.assert_called_once_with([0x3E | 0xC0] + [0] * 8)


@pytest.mark.parametrize(
    "patable",
    (
        (198, 0, 0, 0, 0, 0, 0, 0),  # default
        [198, 0, 0, 0, 0, 0, 0, 0],
        (0, 198, 0, 0, 0, 0, 0, 0),  # OOK
        (1, 2, 3, 4, 5, 6, 7, 8),
        (1, 2, 3),
        (1,),
    ),
)
def test__set_patable(transceiver, patable):
    transceiver._spi.xfer.return_value = [0b00000111] * (len(patable) + 1)
    transceiver._set_patable(patable)
    transceiver._spi.xfer.assert_called_once_with([0x3E | 0x40] + list(patable))


@pytest.mark.parametrize(
    "patable", ((21, -7), (0, 42, 256), (0, 1, 2, 3, 4, 5, 6, 7, 8))
)
def test__set_patable_invalid(transceiver, patable):
    with pytest.raises(Exception):
        transceiver._set_patable(patable)
    transceiver._spi.xfer.assert_not_called()
