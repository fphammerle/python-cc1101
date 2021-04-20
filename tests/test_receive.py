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

import datetime
import unittest.mock

import gpiod
import pytest

# pylint: disable=protected-access


def test__enable_receive_mode(transceiver):
    transceiver._spi.xfer.return_value = [15]
    transceiver._enable_receive_mode()
    transceiver._spi.xfer.assert_called_once_with([0x34 | 0x00])


@pytest.mark.parametrize("payload", [b"\0", b"\x12\x45\x56"])
def test__get_received_packet(transceiver, payload):
    fifo_buffer = list(payload) + [128, (1 << 7) | 42]
    with unittest.mock.patch.object(
        transceiver, "_read_status_register", return_value=len(fifo_buffer)
    ) as read_status_register, unittest.mock.patch.object(
        transceiver, "_read_burst", return_value=fifo_buffer
    ) as read_burst_mock:
        received_packet = transceiver._get_received_packet()
    read_status_register.assert_called_once_with(0x3B)
    read_burst_mock.assert_called_once_with(
        start_register=0x3F, length=len(fifo_buffer)
    )
    assert received_packet.payload == payload
    assert received_packet._rssi_index == 128
    assert received_packet.checksum_valid
    assert received_packet.link_quality_indicator == 42


@pytest.mark.parametrize("gdo0_chip_selector", (0, "/dev/gpiochip1"))
@pytest.mark.parametrize("gdo0_line_name", ("GPIO24", "GPIO25"))
@pytest.mark.parametrize("reached_timeout", (True, False))
@pytest.mark.parametrize("timeout", (datetime.timedelta(seconds=1),))
def test__wait_for_packet(
    transceiver, gdo0_chip_selector, gdo0_line_name, timeout, reached_timeout
):
    line_mock = unittest.mock.MagicMock()
    line_mock.event_wait.return_value = not reached_timeout
    with unittest.mock.patch(
        "cc1101._gpio.get_line"
    ) as get_line_mock, unittest.mock.patch.object(
        transceiver, "_get_received_packet"
    ) as get_received_packet_mock, unittest.mock.patch.object(
        transceiver, "_enable_receive_mode"
    ) as enable_receive_mode_mock:
        get_line_mock.return_value = line_mock
        get_received_packet_mock.return_value = "packet-dummy"
        packet = transceiver._wait_for_packet(
            timeout=timeout,
            gdo0_chip=gdo0_chip_selector,
            gdo0_line_name=gdo0_line_name,
        )
    get_line_mock.assert_called_once_with(
        chip_selector=gdo0_chip_selector, line_name=gdo0_line_name
    )
    assert line_mock.request.call_count == 1
    (line_request,) = line_mock.request.call_args[0]
    assert vars(line_request) == {
        "consumer": "CC1101:GDO0",
        "flags": 0,
        "request_type": gpiod.line_request.EVENT_RISING_EDGE,
    }
    assert not line_mock.request.call_args[1]
    enable_receive_mode_mock.assert_called_once_with()
    line_mock.event_wait.assert_called_once_with(timeout=timeout)
    if reached_timeout:
        assert packet is None
        get_received_packet_mock.assert_not_called()
    else:
        get_received_packet_mock.assert_called_once_with()
        assert packet == "packet-dummy"
