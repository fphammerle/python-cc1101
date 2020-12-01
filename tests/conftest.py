import unittest.mock

import pytest

import cc1101


@pytest.fixture
def transceiver():
    with unittest.mock.patch("spidev.SpiDev"):
        return cc1101.CC1101()
