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

import logging
import unittest.mock

import pytest

import cc1101._cli
from cc1101.options import PacketLengthMode

# pylint: disable=protected-access


@pytest.mark.parametrize(
    ("args", "packet_length_mode", "checksum_disabled"),
    (
        ([""], None, False),
        (["", "--packet-length-mode", "variable"], PacketLengthMode.VARIABLE, False),
        (["", "--disable-checksum"], None, True),
    ),
)
def test_configure_device(args, packet_length_mode, checksum_disabled):
    # pylint: disable=too-many-arguments
    with unittest.mock.patch("cc1101.CC1101") as transceiver_class_mock:
        with unittest.mock.patch("sys.argv", args):
            cc1101._cli._export_config()
    transceiver_class_mock.assert_called_once_with(lock_spi_device=True)
    transceiver_mock = transceiver_class_mock().__enter__()
    if packet_length_mode is None:
        transceiver_mock.__enter__().set_packet_length_mode.assert_not_called()
    else:
        transceiver_mock.set_packet_length_mode.assert_called_once_with(
            packet_length_mode
        )
    transceiver_mock.set_packet_length_bytes.assert_not_called()
    if checksum_disabled:
        transceiver_mock.disable_checksum.assert_called_once_with()
    else:
        transceiver_mock.disable_checksum.assert_not_called()


@pytest.mark.parametrize(
    ("args", "output_power_settings"),
    (
        ([""], None),
        (["", "-p", "192"], [192]),
        (["", "--output-power", "192"], [192]),
        (["", "-p", "0", "192"], [0, 192]),  # OOK
        (
            ["", "-p", "3", "15", "30", "39", "80", "129", "203", "194"],
            [3, 15, 30, 39, 80, 129, 203, 194],
        ),
    ),
)
def test_configure_device_output_power_settings(args, output_power_settings):
    with unittest.mock.patch("cc1101.CC1101") as transceiver_mock:
        with unittest.mock.patch("sys.argv", args):
            cc1101._cli._export_config()
    if output_power_settings is None:
        transceiver_mock().__enter__().set_output_power.assert_not_called()
    else:
        transceiver_mock().__enter__().set_output_power.assert_called_with(
            output_power_settings
        )


def test_export_python_list(capsys, caplog):
    with unittest.mock.patch("cc1101.CC1101") as transceiver_mock:
        transceiver_mock().__enter__().get_configuration_register_values.return_value = {
            cc1101.addresses.ConfigurationRegisterAddress.IOCFG2: 0x29,
            cc1101.addresses.ConfigurationRegisterAddress.IOCFG1: 0x2E,
        }
        transceiver_mock().__enter__()._get_patable.return_value = [0xC6] + [0] * 7
        with unittest.mock.patch("sys.argv", [""]):
            with caplog.at_level(logging.INFO):
                cc1101._cli._export_config()
    assert caplog.record_tuples == [
        ("cc1101._cli", 20, str(transceiver_mock().__enter__()))
    ]
    out, err = capsys.readouterr()
    assert not err
    assert (
        out
        == "[\n0b00101001, # 0x29 IOCFG2\n0b00101110, # 0x2e IOCFG1\n]\n"
        + "# PATABLE = (0xc6, 0, 0, 0, 0, 0, 0, 0)\n"
    )


@pytest.mark.parametrize(
    ("args", "root_log_level", "log_format"),
    (
        ([], logging.INFO, "%(message)s"),
        (
            ["--debug"],
            logging.DEBUG,
            "%(asctime)s:%(levelname)s:%(name)s:%(funcName)s:" + "%(message)s",
        ),
    ),
)
def test_root_log_level(args, root_log_level, log_format):
    with unittest.mock.patch("cc1101.CC1101"), unittest.mock.patch(
        "sys.argv", [""] + args
    ), unittest.mock.patch("logging.basicConfig") as logging_basic_config_mock:
        cc1101._cli._export_config()
    assert logging_basic_config_mock.call_count == 1
    assert logging_basic_config_mock.call_args[1]["level"] == root_log_level
    assert logging_basic_config_mock.call_args[1]["format"] == log_format


def test_logging(caplog):
    with unittest.mock.patch("sys.argv", [""]), unittest.mock.patch(
        "cc1101.CC1101"
    ) as transceiver_mock, caplog.at_level(logging.DEBUG):
        transceiver_mock().__enter__().__str__.return_value = "dummystr"
        cc1101._cli._export_config()
    assert caplog.record_tuples == [
        (
            "cc1101._cli",
            logging.DEBUG,
            "args=Namespace(base_frequency_hertz=None, debug=False, disable_checksum=False, "
            "format='python-list', output_power_settings=None, packet_length_mode=None, "
            "symbol_rate_baud=None, sync_mode=None)",
        ),
        ("cc1101._cli", logging.INFO, "dummystr"),
    ]
