# python-cc1101

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI Pipeline Status](https://github.com/fphammerle/python-cc1101/workflows/tests/badge.svg)](https://github.com/fphammerle/python-cc1101/actions)
[![Last Release](https://img.shields.io/pypi/v/cc1101.svg)](https://pypi.org/project/cc1101/#history)
[![Compatible Python Versions](https://img.shields.io/pypi/pyversions/cc1101.svg)](https://pypi.org/project/cc1101/)
[![DOI](https://zenodo.org/badge/292333844.svg)](https://zenodo.org/badge/latestdoi/292333844)

Python Library to Transmit RF Signals via [CC1101 Transceivers](https://www.ti.com/product/CC1101)

## Setup

```sh
$ pip3 install --user --upgrade cc1101
```

On Raspbian / Raspberry Pi OS, dependencies can optionally be installed via:
```sh
$ sudo apt-get install --no-install-recommends python3-spidev
```

### Wiring Raspberry Pi

Directly connect the following pins:

|C1101|Raspberry Pi        |
|-----|--------------------|
|VDD  | 3.3V (Pin 1 or 17) |
|SI   | MOSI (Pin 19)      |
|SO   | MISO (Pin 21)      |
|CSn  | CE0 (Pin 24)       |
|SCLK | SCLK (Pin 23)      | 
|GND  | Ground             |

No resistors required. GDO0 & GDO2 are currently unused.

Raspberry Pi GPIO docs: https://www.raspberrypi.org/documentation/usage/gpio/

## Usage

See [examples](https://github.com/fphammerle/python-cc1101/blob/master/examples/).

```python
import cc1101

with cc1101.CC1101() as transceiver:
    transceiver.set_base_frequency_hertz(433.92e6)
    print(transceiver)
    transceiver.transmit(b"\x01\xff\x00 message")
```

In case a `PermissionError` gets raised,
check the permissions of `/dev/spidev*`.
You'll probably need `sudo usermod -a -G spi $USER`,
followed by a re-login.

CC1101's docs: https://www.ti.com/lit/ds/symlink/cc1101.pdf
