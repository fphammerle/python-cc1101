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
    with unittest.mock.patch.object(
        transceiver, "_read_status_register", return_value=0
    ):
        assert transceiver._get_received_packet() is None


@pytest.mark.parametrize("gdo0_gpio_line_name", (b"GPIO24", b"GPIO25"))
@pytest.mark.parametrize("reached_timeout", (True, False))
@pytest.mark.parametrize("timeout", (datetime.timedelta(seconds=4),))
def test__wait_for_packet(transceiver, gdo0_gpio_line_name, timeout, reached_timeout):
    line_mock = unittest.mock.MagicMock()
    line_mock.wait_for_rising_edge.return_value = not reached_timeout
    with unittest.mock.patch(
        "cc1101._gpio.GPIOLine.find", return_value=line_mock
    ) as find_line_mock, unittest.mock.patch.object(
        transceiver, "_get_received_packet", return_value="packet-dummy"
    ) as get_received_packet_mock, unittest.mock.patch.object(
        transceiver, "_enable_receive_mode"
    ) as enable_receive_mode_mock, unittest.mock.patch.object(
        transceiver, "_command_strobe"
    ) as command_strobe_mock:
        packet = transceiver._wait_for_packet(
            timeout=timeout,
            gdo0_gpio_line_name=gdo0_gpio_line_name,
        )
    find_line_mock.assert_called_once_with(name=gdo0_gpio_line_name)
    enable_receive_mode_mock.assert_called_once_with()
    line_mock.wait_for_rising_edge.assert_called_once_with(
        consumer=b"CC1101:GDO0", timeout=timeout
    )
    if reached_timeout:
        assert packet is None
        command_strobe_mock.assert_called_once_with(0x36)  # SIDLE
        get_received_packet_mock.assert_not_called()
    else:
        command_strobe_mock.assert_not_called()
        get_received_packet_mock.assert_called_once_with()
        assert packet == "packet-dummy"
