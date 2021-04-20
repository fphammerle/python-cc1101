# python-cc1101 - Python Library to Transmit RF Signals via CC1101 Transceivers
#
# Copyright (C) 2021 Fabian Peter Hammerle <fabian@hammerle.me>
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

import ctypes
import ctypes.util
import datetime
import errno
import re
import unittest.mock

import pytest

import cc1101._gpio

# pylint: disable=protected-access


def test__load_libgpiod():
    with unittest.mock.patch(
        "ctypes.util.find_library", return_value=ctypes.util.find_library("c")
    ) as find_library_mock:
        assert isinstance(cc1101._gpio._load_libgpiod(), ctypes.CDLL)
    find_library_mock.assert_called_once_with("gpiod")


@pytest.mark.parametrize("name", ("GPIO24", "GPIO25"))
def test_line_find_permission_denied(libgpiod_mock, name):
    libgpiod_mock.gpiod_line_find.return_value = 0
    ctypes.set_errno(errno.EACCES)
    with pytest.raises(
        PermissionError,
        match=r"^Failed to access GPIO line {!r}\.\n".format(re.escape(name)),
    ):
        cc1101._gpio.GPIOLine.find(name.encode())


@pytest.mark.parametrize("name", ("GPIO24", "GPIO25"))
def test_line_find_non_existing(libgpiod_mock, name):
    libgpiod_mock.gpiod_line_find.return_value = 0
    ctypes.set_errno(errno.ENOENT)
    with pytest.raises(
        FileNotFoundError,
        match=r"^GPIO line {!r} does not exist\.\n".format(re.escape(name)),
    ):
        cc1101._gpio.GPIOLine.find(name.encode())


@pytest.mark.parametrize("name", ("GPIO24", "GPIO25"))
def test_line_find_unknown_error(libgpiod_mock, name):
    libgpiod_mock.gpiod_line_find.return_value = 0
    ctypes.set_errno(errno.ENOANO)
    with pytest.raises(
        OSError,
        match=r"^Failed to open GPIO line {!r}: ENOANO$".format(re.escape(name)),
    ):
        cc1101._gpio.GPIOLine.find(name.encode())


def test_line_find(libgpiod_mock):
    libgpiod_mock.gpiod_line_find.return_value = 21
    line = cc1101._gpio.GPIOLine.find(b"GPIO24")
    libgpiod_mock.gpiod_line_find.assert_called_once_with(b"GPIO24")
    assert isinstance(line, cc1101._gpio.GPIOLine)
    assert line._pointer.value == 21


def test_line_release(libgpiod_mock):
    line = cc1101._gpio.GPIOLine(42)
    del line
    libgpiod_mock.gpiod_line_close_chip.assert_called_once_with(42)


@pytest.mark.parametrize("consumer", (b"CC1101 GDO0", b"test"))
@pytest.mark.parametrize("timeout_seconds", (21.42, 0.1234))
@pytest.mark.parametrize("reached_timeout", (False, True))
def test_line_wait_for_rising_edge(
    libgpiod_mock, consumer: bytes, timeout_seconds: float, reached_timeout: bool
):
    pointer = ctypes.c_void_p(1234)
    line = cc1101._gpio.GPIOLine(pointer=pointer)
    libgpiod_mock.gpiod_line_request_rising_edge_events.return_value = 0
    libgpiod_mock.gpiod_line_event_wait.return_value = 0 if reached_timeout else 1
    event_occured = line.wait_for_rising_edge(
        consumer=consumer, timeout=datetime.timedelta(seconds=timeout_seconds)
    )
    assert event_occured is not reached_timeout
    libgpiod_mock.gpiod_line_request_rising_edge_events.assert_called_once_with(
        pointer, consumer
    )
    assert libgpiod_mock.gpiod_line_event_wait.call_count == 1
    wait_args, wait_kwargs = libgpiod_mock.gpiod_line_event_wait.call_args
    assert wait_args[0] == pointer
    assert (
        wait_args[1].contents.tv_sec + wait_args[1].contents.tv_nsec / 10 ** 9
    ) == pytest.approx(timeout_seconds, abs=1e-10)
    assert not wait_args[2:]
    assert not wait_kwargs
    libgpiod_mock.gpiod_line_release.assert_called_once_with(pointer)


@pytest.mark.parametrize("consumer", (b"CC1101 GDO0",))
@pytest.mark.parametrize("timeout_seconds", (21.42,))
def test_line_wait_for_rising_edge_busy(
    libgpiod_mock, consumer: bytes, timeout_seconds: float
):
    pointer = ctypes.c_void_p(1234)
    line = cc1101._gpio.GPIOLine(pointer=pointer)
    libgpiod_mock.gpiod_line_request_rising_edge_events.return_value = -1
    ctypes.set_errno(errno.EBUSY)
    with pytest.raises(
        OSError,
        match=r"^Request for rising edge event notifications failed \(EBUSY\)."
        r"\nBlocked by another process\?$",
    ):
        line.wait_for_rising_edge(
            consumer=consumer, timeout=datetime.timedelta(seconds=timeout_seconds)
        )
