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
import warnings

import pytest

import cc1101

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


_SYMBOL_RATE_MANTISSA_EXPONENT_REAL_PARAMS = [
    # > The default values give a data rate of 115.051 kBaud
    # > (closest setting to 115.2 kBaud), assuming a 26.0 MHz crystal.
    (34, 12, 115051),
    (34, 12 + 1, 115051 * 2),
    (34, 12 - 1, 115051 / 2),
    # > If DRATE_M is rounded to the nearest integer and becomes 256,
    # > increment DRATE_E and use DRATE_M = 0.
    (0, 13, 203124),
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
    ("mantissa", "exponent", "real"), _SYMBOL_RATE_MANTISSA_EXPONENT_REAL_PARAMS
)
def test_get_symbol_rate_baud(transceiver, mantissa, exponent, real):
    with unittest.mock.patch.object(
        transceiver, "_get_symbol_rate_mantissa", return_value=mantissa
    ), unittest.mock.patch.object(
        transceiver, "_get_symbol_rate_exponent", return_value=exponent
    ):
        assert transceiver.get_symbol_rate_baud() == pytest.approx(real, rel=1e-5)


@pytest.mark.parametrize(
    ("mantissa", "exponent", "real"), _SYMBOL_RATE_MANTISSA_EXPONENT_REAL_PARAMS
)
def test_set_symbol_rate_baud(transceiver, mantissa, exponent, real):
    with unittest.mock.patch.object(
        transceiver, "_set_symbol_rate_mantissa"
    ) as set_mantissa_mock, unittest.mock.patch.object(
        transceiver, "_set_symbol_rate_exponent"
    ) as set_exponent_mock:
        transceiver.set_symbol_rate_baud(real)
    set_mantissa_mock.assert_called_once_with(mantissa)
    set_exponent_mock.assert_called_once_with(exponent)


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


@pytest.mark.parametrize(
    ("patable", "patable_index", "power_levels"),
    (
        ((198, 0, 0, 0, 0, 0, 0, 0), 0, (198,)),  # CC1101's default
        ((198, 0, 0, 0, 0, 0, 0, 0), 1, (198, 0)),  # library's default
        ((0, 198, 0, 0, 0, 0, 0, 0), 1, (0, 198)),
        ((0, 1, 2, 3, 4, 5, 21, 42), 7, (0, 1, 2, 3, 4, 5, 21, 42)),
    ),
)
def test_get_output_power(transceiver, patable, patable_index, power_levels):
    with unittest.mock.patch.object(
        transceiver, "_get_patable", return_value=patable
    ), unittest.mock.patch.object(
        transceiver, "_get_power_amplifier_setting_index", return_value=patable_index
    ):
        assert transceiver.get_output_power() == power_levels


@pytest.mark.parametrize(
    ("patable_index", "power_levels"),
    (
        (0, (198,)),  # CC1101's default
        (1, (198, 0)),  # library's default
        (1, (0, 198)),
        (1, [0, 198]),
        (7, (0, 1, 2, 3, 4, 5, 21, 42)),
    ),
)
def test_set_output_power(transceiver, patable_index, power_levels):
    with unittest.mock.patch.object(
        transceiver, "_set_patable"
    ) as set_patable_mock, unittest.mock.patch.object(
        transceiver, "_set_power_amplifier_setting_index"
    ) as set_patable_index_mock:
        transceiver.set_output_power(power_levels)
    set_patable_mock.assert_called_once_with(list(power_levels))
    set_patable_index_mock.assert_called_once_with(patable_index)


@pytest.mark.parametrize(
    "power_levels", (tuple(), (21, 256), (0, 1, 2, 3, 4, 5, 6, 7, 8))
)
def test_set_output_power_invalid(transceiver, power_levels):
    with pytest.raises(Exception):
        transceiver.set_output_power(power_levels)
