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

import re
import unittest.mock

import pytest

import cc1101
import cc1101.addresses
import cc1101.options

# pylint: disable=protected-access


@pytest.mark.parametrize("bus", [0, 1])
@pytest.mark.parametrize("chip_select", [0, 2])
def test___init__select_device(bus, chip_select):
    with unittest.mock.patch("spidev.SpiDev"):
        transceiver = cc1101.CC1101(spi_bus=bus, spi_chip_select=chip_select)
    assert transceiver._spi_bus == bus
    assert transceiver._spi_chip_select == chip_select
    assert transceiver._spi_device_path == "/dev/spidev{}.{}".format(bus, chip_select)
    transceiver._spi.open.side_effect = SystemExit
    with pytest.raises(SystemExit):
        with transceiver:
            pass
    transceiver._spi.open.assert_called_once_with(bus, chip_select)


def test__read_status_register(transceiver):
    transceiver._spi.xfer.return_value = [0, 20]
    transceiver._read_status_register(cc1101.addresses.StatusRegisterAddress.VERSION)
    transceiver._spi.xfer.assert_called_once_with([0x31 | 0xC0, 0])


def test__command_strobe(transceiver):
    transceiver._spi.xfer.return_value = [15]
    transceiver._command_strobe(cc1101.addresses.StrobeAddress.STX)
    transceiver._spi.xfer.assert_called_once_with([0x35 | 0x00])


def test__reset(transceiver):
    transceiver._spi.xfer.return_value = [15]
    transceiver._reset()
    transceiver._spi.xfer.assert_called_once_with([0x30 | 0x00])


@pytest.mark.parametrize("chip_version", [0x14, 0x04])
def test___enter__(transceiver, chip_version):
    with unittest.mock.patch.object(
        transceiver, "_read_status_register"
    ) as read_status_register_mock, unittest.mock.patch.object(
        transceiver, "_reset"
    ) as reset_mock, unittest.mock.patch.object(
        transceiver, "_set_modulation_format"
    ) as set_modulation_format_mock, unittest.mock.patch.object(
        transceiver, "_set_power_amplifier_setting_index"
    ) as set_pa_setting_mock, unittest.mock.patch.object(
        transceiver, "_disable_data_whitening"
    ) as disable_whitening_mock, unittest.mock.patch.object(
        transceiver, "_write_burst"
    ) as write_burst_mock, unittest.mock.patch.object(
        transceiver,
        "get_main_radio_control_state_machine_state",
        return_value=cc1101.MainRadioControlStateMachineState.IDLE,
    ):
        read_status_register_mock.side_effect = lambda r: {
            cc1101.addresses.StatusRegisterAddress.PARTNUM: 0,
            cc1101.addresses.StatusRegisterAddress.VERSION: chip_version,
        }[r]
        with transceiver as transceiver_context:
            assert transceiver == transceiver_context
            transceiver._spi.open.assert_called_once_with(0, 0)
            assert transceiver._spi.max_speed_hz == 55700
            reset_mock.assert_called_once_with()
            set_modulation_format_mock.assert_called_once_with(
                cc1101.options.ModulationFormat.ASK_OOK
            )
            set_pa_setting_mock.assert_called_once_with(1)
            disable_whitening_mock.assert_called_once_with()
            write_burst_mock.assert_called_once_with(0x18, [0b010100])


def test___enter___unsupported_partnum(transceiver):
    with unittest.mock.patch.object(
        transceiver, "_read_status_register"
    ) as read_status_register_mock, unittest.mock.patch.object(transceiver, "_reset"):
        read_status_register_mock.side_effect = lambda r: {
            cc1101.addresses.StatusRegisterAddress.PARTNUM: 21
        }[r]
        with pytest.raises(ValueError, match=r"^unexpected chip part number "):
            with transceiver:
                pass


def test___enter___unsupported_chip_version(transceiver):
    with unittest.mock.patch.object(
        transceiver, "_read_status_register"
    ) as read_status_register_mock, unittest.mock.patch.object(transceiver, "_reset"):
        read_status_register_mock.side_effect = lambda r: {
            cc1101.addresses.StatusRegisterAddress.PARTNUM: 0,
            cc1101.addresses.StatusRegisterAddress.VERSION: 0x15,
        }[r]
        with pytest.raises(
            ValueError,
            match=r"^{}$".format(
                re.escape(
                    "unsupported chip version 0x15 (expected one of [0x04, 0x14])"
                )
            ),
        ):
            with transceiver:
                pass


@pytest.mark.parametrize("bus", [0, 1])
@pytest.mark.parametrize("chip_select", [0, 2])
def test___enter__permission_error(transceiver, bus, chip_select):
    transceiver._spi.open.side_effect = PermissionError("[Errno 13] Permission denied")
    transceiver._spi_bus = bus
    transceiver._spi_chip_select = chip_select
    with pytest.raises(
        PermissionError, match=r"\s/dev/spidev{}.{}\s".format(bus, chip_select)
    ):
        with transceiver:
            pass


def test___enter__non_idle(transceiver):
    with unittest.mock.patch.object(
        transceiver,
        "get_main_radio_control_state_machine_state",
        return_value=cc1101.MainRadioControlStateMachineState.TX,
    ), unittest.mock.patch.object(transceiver, "_reset"), unittest.mock.patch.object(
        transceiver, "_verify_chip"
    ), unittest.mock.patch.object(
        transceiver, "_configure_defaults"
    ):
        with pytest.raises(
            ValueError, match=r"^expected marcstate idle \(actual: TX\)$"
        ):
            with transceiver:
                pass
