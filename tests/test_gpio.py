import pathlib
import re
import unittest.mock

import pytest

import cc1101._gpio

# pylint: disable=protected-access


@pytest.mark.parametrize(
    ("chip_selector", "chip_selector_formatted"),
    (
        (0, "/dev/gpiochip0"),
        (1, "/dev/gpiochip1"),
        ("/dev/gpiochip0", "/dev/gpiochip0"),
        (pathlib.Path("/dev/gpiochip1"), "/dev/gpiochip1"),
    ),
)
def test_get_line_permission_error(chip_selector, chip_selector_formatted):
    with unittest.mock.patch(
        "gpiod.chip",
        side_effect=PermissionError("[Errno 13] Permission denied: '/dev/gpiochip0'"),
    ):
        with pytest.raises(
            PermissionError,
            match=r"^Failed to access GPIO chip {}\.".format(
                re.escape(chip_selector_formatted)
            ),
        ):
            cc1101._gpio.get_line(chip_selector=chip_selector, line_name="GPIO24")


def test_get_line_file_not_found():
    with unittest.mock.patch(
        "gpiod.chip",
        side_effect=FileNotFoundError(
            "[Errno 2] No such file or directory: 'cannot open GPIO device /dev/gpiochip21'"
        ),
    ):
        with pytest.raises(
            FileNotFoundError, match=r"^Failed to find GPIO chip /dev/gpiochip21\."
        ):
            cc1101._gpio.get_line(chip_selector=21, line_name="GPIO24")


def test_get_line_cannot_open():
    with unittest.mock.patch(
        "gpiod.chip",
        side_effect=OSError("[Errno 0] Success: 'cannot open GPIO device 42'"),
    ):
        with pytest.raises(
            FileNotFoundError, match=r"^Failed to find GPIO chip /dev/gpiochip42\."
        ):
            cc1101._gpio.get_line(chip_selector=42, line_name="GPIO24")


def test_get_line_type_error():
    with unittest.mock.patch(
        "gpiod.chip",
        side_effect=TypeError("iter() returned non-iterator of type 'NoneType'"),
    ):
        with pytest.raises(
            FileNotFoundError, match=r"^Failed to find GPIO chip /dev/gpiochip815\."
        ):
            cc1101._gpio.get_line(chip_selector="/dev/gpiochip815", line_name="GPIO24")


class _LineMock:

    # pylint: disable=too-few-public-methods

    def __init__(self, holding: bool):
        self._holding = holding

    @property
    def name(self) -> str:
        if not self._holding:
            raise RuntimeError("object not holding a GPIO line handle")
        return "dummy"


@pytest.mark.parametrize("chip_selector", ("/dev/gpiochip0",))
@pytest.mark.parametrize("line_name", ("GPIO24", "GPIO25"))
def test_get_line(chip_selector, line_name):
    with unittest.mock.patch("gpiod.chip") as chip_mock:
        chip_mock().find_line.return_value = _LineMock(holding=True)
        chip_mock.reset_mock()
        assert isinstance(
            cc1101._gpio.get_line(chip_selector=chip_selector, line_name=line_name),
            _LineMock,
        )
        chip_mock.assert_called_once_with(chip_selector)
        chip_mock().find_line.assert_called_once_with(name=line_name)


@pytest.mark.parametrize("chip_selector", ("/dev/gpiochip0",))
@pytest.mark.parametrize("line_name", ("GPIO24", "GPIO25"))
def test_get_line_unknown_line(chip_selector, line_name):
    with unittest.mock.patch("gpiod.chip") as chip_mock:
        chip_mock().find_line.return_value = _LineMock(holding=False)
        with pytest.raises(
            ValueError,
            match=r"Failed to find GPIO line with name {}\.".format(
                re.escape(repr(line_name))
            ),
        ):
            cc1101._gpio.get_line(chip_selector=chip_selector, line_name=line_name)
