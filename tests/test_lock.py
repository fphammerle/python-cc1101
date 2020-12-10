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

import unittest.mock

import pytest

import cc1101
import cc1101.addresses

# pylint: disable=protected-access


@pytest.fixture(scope="function")
def spidev_mock(tmp_path):
    class _SpiDevMock:
        def __init__(self):
            self._file = None

        def open(self, bus, select):
            path = tmp_path.joinpath("spidev{}.{}~".format(bus, select))
            self._file = path.open("w+")

        def fileno(self):
            return self._file.fileno()

        def close(self):
            self._file.close()

    return _SpiDevMock


# pylint: disable=redefined-outer-name; using fixture


def test___enter__locked(spidev_mock):
    with unittest.mock.patch.object(
        cc1101.CC1101, "_reset"
    ), unittest.mock.patch.object(
        cc1101.CC1101, "_verify_chip"
    ), unittest.mock.patch.object(
        cc1101.CC1101, "_configure_defaults"
    ), unittest.mock.patch.object(
        cc1101.CC1101,
        "get_main_radio_control_state_machine_state",
        return_value=cc1101.MainRadioControlStateMachineState.IDLE,
    ):
        with unittest.mock.patch("spidev.SpiDev", spidev_mock):
            transceiver = cc1101.CC1101(lock_spi_device=True)
        with transceiver:
            with unittest.mock.patch("spidev.SpiDev", spidev_mock):
                transceiver2 = cc1101.CC1101(lock_spi_device=True)
            with pytest.raises(BlockingIOError):
                with transceiver2:
                    pass
            with unittest.mock.patch("spidev.SpiDev", spidev_mock):
                transceiver3 = cc1101.CC1101(lock_spi_device=False)
            with transceiver3:
                pass
        with transceiver2:  # closing unlocks
            pass


def test___enter__not_locked(spidev_mock):
    with unittest.mock.patch.object(
        cc1101.CC1101, "_reset"
    ), unittest.mock.patch.object(
        cc1101.CC1101, "_verify_chip"
    ), unittest.mock.patch.object(
        cc1101.CC1101, "_configure_defaults"
    ), unittest.mock.patch.object(
        cc1101.CC1101,
        "get_main_radio_control_state_machine_state",
        return_value=cc1101.MainRadioControlStateMachineState.IDLE,
    ):
        with unittest.mock.patch("spidev.SpiDev", spidev_mock):
            transceiver = cc1101.CC1101(lock_spi_device=False)
        with transceiver:
            with unittest.mock.patch("spidev.SpiDev", spidev_mock):
                transceiver2 = cc1101.CC1101(lock_spi_device=True)
            with transceiver2:
                pass
