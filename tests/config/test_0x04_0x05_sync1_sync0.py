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

# pylint: disable=protected-access


@pytest.mark.parametrize(
    ("xfer_return_value", "sync_word"),
    [([64, 211, 145], b"\xd3\x91"), ([64, 0, 0], b"\0\0")],
)
def test_get_sync_word(transceiver, xfer_return_value, sync_word):
    transceiver._spi.xfer.return_value = xfer_return_value
    assert transceiver.get_sync_word() == sync_word
    transceiver._spi.xfer.assert_called_once_with([0x04 | 0xC0, 0, 0])


def test_set_sync_word(transceiver):
    transceiver._spi.xfer.return_value = [15, 15, 15]
    transceiver.set_sync_word(b"\x12\x34")
    transceiver._spi.xfer.assert_called_once_with([0x04 | 0x40, 0x12, 0x34])


@pytest.mark.parametrize("sync_word", [b"", b"\0", "\x12\x34\x56"])
def test_set_sync_word_invalid_length(transceiver, sync_word):
    with pytest.raises(ValueError, match=r"\bexpected two bytes\b"):
        transceiver.set_sync_word(sync_word)
