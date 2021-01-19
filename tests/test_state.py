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

import cc1101


# pylint: disable=protected-access


@pytest.mark.parametrize(
    "marcstate",
    (
        cc1101.MainRadioControlStateMachineState.IDLE,
        cc1101.MainRadioControlStateMachineState.RX,
    ),
)
def test_get_main_radio_control_state_machine_state(transceiver, marcstate):
    transceiver._spi.xfer.return_value = [
        0b0000111,  # chip status "idle", but irrelevant for retrieval of marcstate
        marcstate.value,
    ]
    assert transceiver.get_main_radio_control_state_machine_state() == marcstate
    transceiver._spi.xfer.assert_called_once_with([0x35 | 0xC0, 0])
    assert transceiver.get_marc_state() == marcstate
