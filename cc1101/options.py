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

import enum


class PacketLengthMode(enum.IntEnum):
    """
    PKTCTRL0.LENGTH_CONFIG
    """

    FIXED = 0b00
    VARIABLE = 0b01
    # INFINITE = 0b10


class ModulationFormat(enum.IntEnum):
    """
    MDMCFG2.MOD_FORMAT
    """

    FSK2 = 0b000
    GFSK = 0b001
    ASK_OOK = 0b011
    FSK4 = 0b100
    MSK = 0b111


class SyncMode(enum.IntEnum):
    """
    MDMCFG2.SYNC_MODE

    see "14.3 Byte Synchronization"
    """

    NO_PREAMBLE_AND_SYNC_WORD = 0b00
    TRANSMIT_16_MATCH_15_BITS = 0b01
    TRANSMIT_16_MATCH_16_BITS = 0b10
    TRANSMIT_32_MATCH_30_BITS = 0b11
