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

import pytest

import cc1101

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
