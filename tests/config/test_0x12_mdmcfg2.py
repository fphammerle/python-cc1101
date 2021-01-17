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

from cc1101.options import ModulationFormat, SyncMode

# pylint: disable=protected-access


@pytest.mark.parametrize(
    ("mdmcfg2", "mod_format"),
    (
        (0b00000010, ModulationFormat.FSK2),
        (0b10001110, ModulationFormat.FSK2),
        (0b10011110, ModulationFormat.GFSK),
        (0b10111110, ModulationFormat.ASK_OOK),
        (0b11001110, ModulationFormat.FSK4),
        (0b11001001, ModulationFormat.FSK4),
        (0b11111001, ModulationFormat.MSK),
    ),
)
def test_get_modulation_format(transceiver, mdmcfg2, mod_format):
    transceiver._spi.xfer.return_value = [15, mdmcfg2]
    assert transceiver.get_modulation_format() == mod_format
    transceiver._spi.xfer.assert_called_once_with([0x12 | 0x80, 0])


@pytest.mark.parametrize(
    ("mdmcfg2_before", "mdmcfg2_after", "mod_format"),
    [
        (0b00000010, 0b00000010, ModulationFormat.FSK2),
        (0b11111111, 0b10001111, ModulationFormat.FSK2),
        (0b00000010, 0b00010010, ModulationFormat.GFSK),
        (0b00000010, 0b00110010, ModulationFormat.ASK_OOK),
        (0b00000010, 0b01000010, ModulationFormat.FSK4),
        (0b01110101, 0b01000101, ModulationFormat.FSK4),
        (0b11111111, 0b11001111, ModulationFormat.FSK4),
        (0b00000010, 0b01110010, ModulationFormat.MSK),
        (0b11111111, 0b11111111, ModulationFormat.MSK),
    ],
)
def test__set_modulation_format(transceiver, mdmcfg2_before, mdmcfg2_after, mod_format):
    transceiver._spi.xfer.return_value = [15, 15]
    with unittest.mock.patch.object(
        transceiver, "_read_single_byte", return_value=mdmcfg2_before
    ):
        transceiver._set_modulation_format(mod_format)
    transceiver._spi.xfer.assert_called_once_with([0x12 | 0x40, mdmcfg2_after])


@pytest.mark.parametrize(
    ("mdmcfg2_before", "mdmcfg2_after"),
    [
        (0b00000010, 0b00001010),
        (0b00001010, 0b00001010),
        (0b11110111, 0b11111111),
        (0b11111111, 0b11111111),
    ],
)
def test_enable_manchester_code(transceiver, mdmcfg2_before, mdmcfg2_after):
    transceiver._spi.xfer.return_value = [15, 15]
    with unittest.mock.patch.object(
        transceiver, "_read_single_byte", return_value=mdmcfg2_before
    ):
        transceiver.enable_manchester_code()
    transceiver._spi.xfer.assert_called_once_with([0x12 | 0x40, mdmcfg2_after])


@pytest.mark.parametrize(
    ("mdmcfg2", "sync_mode"),
    [
        (0b00000000, SyncMode.NO_PREAMBLE_AND_SYNC_WORD),
        (0b00000001, SyncMode.TRANSMIT_16_MATCH_15_BITS),
        (0b00000010, SyncMode.TRANSMIT_16_MATCH_16_BITS),
        (0b00000011, SyncMode.TRANSMIT_32_MATCH_30_BITS),
        (0b00000110, SyncMode.TRANSMIT_16_MATCH_16_BITS),
        (0b00000111, SyncMode.TRANSMIT_32_MATCH_30_BITS),
        (0b00001100, SyncMode.NO_PREAMBLE_AND_SYNC_WORD),
        (0b01101011, SyncMode.TRANSMIT_32_MATCH_30_BITS),
        (0b01101111, SyncMode.TRANSMIT_32_MATCH_30_BITS),
    ],
)
def test_get_sync_mode(transceiver, mdmcfg2, sync_mode):
    transceiver._spi.xfer.return_value = [15, mdmcfg2]
    assert transceiver.get_sync_mode() == sync_mode
    transceiver._spi.xfer.assert_called_once_with([0x12 | 0x80, 0])


@pytest.mark.parametrize(
    ("mdmcfg2_before", "mdmcfg2_after", "sync_mode", "threshold_enabled"),
    [
        (0b00000010, 0b00000000, SyncMode.NO_PREAMBLE_AND_SYNC_WORD, None),
        (0b00000010, 0b00000001, SyncMode.TRANSMIT_16_MATCH_15_BITS, None),
        (0b00000010, 0b00000010, SyncMode.TRANSMIT_16_MATCH_16_BITS, None),
        (0b00000010, 0b00000011, SyncMode.TRANSMIT_32_MATCH_30_BITS, None),
        (0b01101110, 0b01101111, SyncMode.TRANSMIT_32_MATCH_30_BITS, None),
        (0b00000010, 0b00000110, SyncMode.TRANSMIT_16_MATCH_16_BITS, True),
        (0b00000010, 0b00000111, SyncMode.TRANSMIT_32_MATCH_30_BITS, True),
        (0b01101110, 0b01101111, SyncMode.TRANSMIT_32_MATCH_30_BITS, True),
        (0b00000010, 0b00000010, SyncMode.TRANSMIT_16_MATCH_16_BITS, False),
        (0b00000010, 0b00000011, SyncMode.TRANSMIT_32_MATCH_30_BITS, False),
        (0b01101110, 0b01101011, SyncMode.TRANSMIT_32_MATCH_30_BITS, False),
    ],
)
def test_set_sync_mode(
    transceiver, mdmcfg2_before, mdmcfg2_after, sync_mode, threshold_enabled
):
    transceiver._spi.xfer.return_value = [15, 15]
    with unittest.mock.patch.object(
        transceiver, "_read_single_byte", return_value=mdmcfg2_before
    ):
        transceiver.set_sync_mode(
            sync_mode, _carrier_sense_threshold_enabled=threshold_enabled
        )
    transceiver._spi.xfer.assert_called_once_with([0x12 | 0x40, mdmcfg2_after])
