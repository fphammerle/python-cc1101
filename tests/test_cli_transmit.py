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

import io
import logging
import unittest.mock

import pytest

import cc1101._cli
from cc1101.options import PacketLengthMode, SyncMode

# pylint: disable=protected-access


@pytest.mark.parametrize(
    (
        "args",
        "base_frequency_hertz",
        "symbol_rate_baud",
        "sync_mode",
        "packet_length_mode",
        "checksum_disabled",
    ),
    (
        ([""], None, None, None, None, False),
        (["", "-f", "433920000"], 433920000, None, None, None, False),
        (
            ["", "--base-frequency-hertz", "868000000"],
            868000000,
            None,
            None,
            None,
            False,
        ),
        (["", "-r", "10000"], None, 10000, None, None, False),
        (["", "--symbol-rate-baud", "12345"], None, 12345, None, None, False),
        (
            ["", "-s", "no-preamble-and-sync-word"],
            None,
            None,
            SyncMode.NO_PREAMBLE_AND_SYNC_WORD,
            None,
            False,
        ),
        (
            ["", "--sync-mode", "no-preamble-and-sync-word"],
            None,
            None,
            SyncMode.NO_PREAMBLE_AND_SYNC_WORD,
            None,
            False,
        ),
        (
            ["", "--sync-mode", "transmit-16-match-15-bits"],
            None,
            None,
            SyncMode.TRANSMIT_16_MATCH_15_BITS,
            None,
            False,
        ),
        (["", "-l", "fixed"], None, None, None, PacketLengthMode.FIXED, False),
        (
            ["", "--packet-length-mode", "fixed"],
            None,
            None,
            None,
            PacketLengthMode.FIXED,
            False,
        ),
        (
            ["", "--packet-length-mode", "variable"],
            None,
            None,
            None,
            PacketLengthMode.VARIABLE,
            False,
        ),
        (["", "--disable-checksum"], None, None, None, None, True),
    ),
)
@pytest.mark.parametrize("payload", (b"", b"message"))
def test_configure_device(
    args,
    base_frequency_hertz,
    symbol_rate_baud,
    sync_mode,
    packet_length_mode,
    checksum_disabled,
    payload,
):
    # pylint: disable=too-many-arguments
    with unittest.mock.patch("cc1101.CC1101") as transceiver_mock:
        stdin_mock = unittest.mock.MagicMock()
        stdin_mock.buffer = io.BytesIO(payload)
        with unittest.mock.patch("sys.stdin", stdin_mock):
            with unittest.mock.patch("sys.argv", args):
                cc1101._cli._transmit()
    transceiver_mock.assert_called_once_with(lock_spi_device=True)
    if base_frequency_hertz is None:
        transceiver_mock().__enter__().set_base_frequency_hertz.assert_not_called()
    else:
        transceiver_mock().__enter__().set_base_frequency_hertz.assert_called_once_with(
            base_frequency_hertz
        )
    if symbol_rate_baud is None:
        transceiver_mock().__enter__().set_symbol_rate_baud.assert_not_called()
    else:
        transceiver_mock().__enter__().set_symbol_rate_baud.assert_called_once_with(
            symbol_rate_baud
        )
    if sync_mode is None:
        transceiver_mock().__enter__().set_sync_mode.assert_not_called()
    else:
        transceiver_mock().__enter__().set_sync_mode.assert_called_once_with(sync_mode)
    if packet_length_mode is None:
        transceiver_mock().__enter__().set_packet_length_mode.assert_not_called()
    else:
        transceiver_mock().__enter__().set_packet_length_mode.assert_called_once_with(
            packet_length_mode
        )
    if packet_length_mode == PacketLengthMode.FIXED:
        transceiver_mock().__enter__().set_packet_length_bytes.assert_called_with(
            len(payload)
        )
    else:
        transceiver_mock().__enter__().set_packet_length_bytes.assert_not_called()
    if checksum_disabled:
        transceiver_mock().__enter__().disable_checksum.assert_called_once_with()
    else:
        transceiver_mock().__enter__().disable_checksum.assert_not_called()


@pytest.mark.parametrize(
    ("args", "output_power_settings"),
    (
        ([""], None),
        (["", "-p", "198"], [198]),  # default
        (["", "--output-power", "198"], [198]),
        (["", "-p", "0", "198"], [0, 198]),  # OOK
        (
            ["", "-p", "18", "14", "29", "52", "96", "132", "200", "192"],
            [18, 14, 29, 52, 96, 132, 200, 192],
        ),
    ),
)
def test_configure_device_output_power(args, output_power_settings):
    with unittest.mock.patch("cc1101.CC1101") as transceiver_mock:
        stdin_mock = unittest.mock.MagicMock()
        stdin_mock.buffer = io.BytesIO(b"message")
        with unittest.mock.patch("sys.stdin", stdin_mock):
            with unittest.mock.patch("sys.argv", args):
                cc1101._cli._transmit()
    transceiver_mock.assert_called_once_with(lock_spi_device=True)
    if output_power_settings:
        transceiver_mock().__enter__().set_output_power.assert_called_with(
            output_power_settings
        )
    else:
        transceiver_mock().__enter__().set_output_power.assert_not_called()


@pytest.mark.parametrize(
    ("args", "root_log_level", "log_format"),
    (
        ([""], logging.INFO, "%(message)s"),
        (
            ["", "--debug"],
            logging.DEBUG,
            "%(asctime)s:%(levelname)s:%(name)s:%(funcName)s:%(message)s",
        ),
    ),
)
def test_root_log_level(args, root_log_level, log_format):
    stdin_mock = unittest.mock.MagicMock()
    stdin_mock.buffer = io.BytesIO(b"")
    with unittest.mock.patch("cc1101.CC1101"), unittest.mock.patch(
        "sys.stdin", stdin_mock
    ), unittest.mock.patch("sys.argv", args), unittest.mock.patch(
        "logging.basicConfig"
    ) as logging_basic_config_mock:
        cc1101._cli._transmit()
    assert logging_basic_config_mock.call_count == 1
    assert logging_basic_config_mock.call_args[1]["level"] == root_log_level
    assert logging_basic_config_mock.call_args[1]["format"] == log_format


@pytest.mark.parametrize("payload", (b"", b"message"))
def test_logging(caplog, payload):
    # pylint: disable=too-many-arguments
    stdin_mock = unittest.mock.MagicMock()
    stdin_mock.buffer = io.BytesIO(payload)
    with unittest.mock.patch("sys.stdin", stdin_mock), unittest.mock.patch(
        "sys.argv", [""]
    ), unittest.mock.patch("cc1101.CC1101") as transceiver_mock, caplog.at_level(
        logging.DEBUG
    ):
        transceiver_mock().__enter__().__str__.return_value = "dummy"
        cc1101._cli._transmit()
    assert caplog.record_tuples == [
        (
            "cc1101._cli",
            logging.DEBUG,
            "args=Namespace(base_frequency_hertz=None, debug=False, "
            "disable_checksum=False, output_power_settings=None, packet_length_mode=None, "
            "symbol_rate_baud=None, sync_mode=None)",
        ),
        ("cc1101._cli", logging.INFO, "dummy"),
    ]
