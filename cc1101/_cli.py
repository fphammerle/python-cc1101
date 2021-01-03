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

import argparse
import logging
import sys

import cc1101
import cc1101.options

_LOGGER = logging.getLogger(__name__)


def _transmit():
    argparser = argparse.ArgumentParser(
        description="Transmits the payload provided via standard input (stdin)"
        " OOK-modulated in big-endian bit order.",
        allow_abbrev=False,
    )
    argparser.add_argument("-f", "--base-frequency-hertz", type=int)
    argparser.add_argument("-r", "--symbol-rate-baud", type=int)
    argparser.add_argument(
        "-s",
        "--sync-mode",
        type=str,
        choices=[m.name.lower().replace("_", "-") for m in cc1101.options.SyncMode],
    )
    argparser.add_argument(
        "-l",
        "--packet-length-mode",
        type=str,
        choices=[m.name.lower() for m in cc1101.options.PacketLengthMode],
    )
    argparser.add_argument("--disable-checksum", action="store_true")
    argparser.add_argument("-d", "--debug", action="store_true")
    args = argparser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s:%(levelname)s:%(name)s:%(funcName)s:%(message)s"
        if args.debug
        else "%(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    _LOGGER.debug("args=%r", args)
    payload = sys.stdin.buffer.read()
    # configure transceiver after reading from stdin
    # to avoid delay between configuration and transmission if pipe is slow
    with cc1101.CC1101(lock_spi_device=True) as transceiver:
        if args.base_frequency_hertz:
            transceiver.set_base_frequency_hertz(args.base_frequency_hertz)
        if args.symbol_rate_baud:
            transceiver.set_symbol_rate_baud(args.symbol_rate_baud)
        if args.sync_mode:
            transceiver.set_sync_mode(
                cc1101.options.SyncMode[args.sync_mode.upper().replace("-", "_")]
            )
        if args.packet_length_mode:
            packet_length_mode = cc1101.options.PacketLengthMode[
                args.packet_length_mode.upper()
            ]
            # default: variable length
            transceiver.set_packet_length_mode(packet_length_mode)
            # default: 255 (maximum)
            if packet_length_mode == cc1101.options.PacketLengthMode.FIXED:
                transceiver.set_packet_length_bytes(len(payload))
        if args.disable_checksum:
            transceiver.disable_checksum()
        _LOGGER.info("%s", transceiver)
        transceiver.transmit(payload)
