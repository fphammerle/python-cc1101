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

import pathlib
import typing

ChipSelector = typing.Union[pathlib.Path, str, int]


def _format_chip_selector(selector: ChipSelector) -> str:
    if isinstance(selector, int):
        return "/dev/gpiochip{}".format(selector)
    return str(selector)


def get_line(chip_selector: ChipSelector, line_name: str) -> "gpiod.line":  # type: ignore
    # lazy import to protect stable API against incompatilibities in hhk7734/python3-gpiod
    # e.g., incompatibility of v1.5.0 with python3.5&3.6 (python_requires not set)
    import gpiod  # pylint: disable=import-outside-toplevel

    try:
        chip = gpiod.chip(chip_selector)
    except PermissionError as exc:
        raise PermissionError(
            "Failed to access GPIO chip {}.".format(
                _format_chip_selector(chip_selector)
            )
            + "\nVerify that the current user has read and write access."
            + "\nOn some systems, like Raspberry Pi OS / Raspbian,"
            + "\n\tsudo usermod -a -G gpio $USER"
            + "\nfollowed by a re-login grants sufficient permissions."
        ) from exc
    except (FileNotFoundError, OSError, TypeError) as exc:
        raise FileNotFoundError(
            "Failed to find GPIO chip {}.".format(_format_chip_selector(chip_selector))
            + "\nRun command `gpiodetect` or `gpioinfo` to view available GPIO chips."
        ) from exc
    line = chip.find_line(name=line_name)
    try:
        line.name
    except RuntimeError as exc:
        raise ValueError(
            "Failed to find GPIO line with name {!r}.".format(line_name)
            + "\nRun command `gpioinfo` to view the names of all available GPIO lines."
        ) from exc
    return line
