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
    ("mdmcfg3", "symbol_rate_mantissa"), [(0b00100010, 34), (0b10101010, 170)]
)
def test__get_symbol_rate_mantissa(transceiver, mdmcfg3, symbol_rate_mantissa):
    transceiver._spi.xfer.return_value = [15, mdmcfg3]
    assert transceiver._get_symbol_rate_mantissa() == symbol_rate_mantissa
    transceiver._spi.xfer.assert_called_once_with([0x11 | 0x80, 0])


@pytest.mark.parametrize(("mantissa"), (0, 0xFF, 0b10100101))
def test__set_symbol_rate_mantissa(transceiver, mantissa):
    transceiver._spi.xfer.return_value = [15, 15]
    transceiver._set_symbol_rate_mantissa(mantissa)
    transceiver._spi.xfer.assert_called_once_with([0x11 | 0x40, mantissa])
