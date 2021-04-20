import unittest.mock

import pytest

import cc1101


@pytest.fixture(scope="function")
def transceiver():
    with unittest.mock.patch("spidev.SpiDev"):
        return cc1101.CC1101()


@pytest.fixture(scope="function")
def libgpiod_mock():
    mock = unittest.mock.MagicMock()
    with unittest.mock.patch("cc1101._gpio._load_libgpiod", return_value=mock):
        yield mock
