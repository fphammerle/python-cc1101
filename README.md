# python-cc1101

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI Pipeline Status](https://github.com/fphammerle/python-cc1101/workflows/tests/badge.svg)](https://github.com/fphammerle/python-cc1101/actions)
[![Coverage Status](https://coveralls.io/repos/github/fphammerle/python-cc1101/badge.svg?branch=master)](https://coveralls.io/github/fphammerle/python-cc1101?branch=master)
[![Last Release](https://img.shields.io/pypi/v/cc1101.svg)](https://pypi.org/project/cc1101/#history)
[![Compatible Python Versions](https://img.shields.io/pypi/pyversions/cc1101.svg)](https://pypi.org/project/cc1101/)
[![DOI](https://zenodo.org/badge/292333844.svg)](https://zenodo.org/badge/latestdoi/292333844)

Python Library & Command Line Tool to Transmit RF Signals via [CC1101 Transceivers](https://www.ti.com/product/CC1101)

## Setup

```sh
$ pip3 install --user --upgrade cc1101
```

On Raspbian / Raspberry Pi OS, dependencies can optionally be installed via:
```sh
$ sudo apt-get install --no-install-recommends python3-spidev
```

### Wiring Raspberry Pi

Connect the following pins directly:

|C1101 |Raspberry Pi        |
|------|--------------------|
|VDD   | 3.3V (Pin 1 or 17) |
|SI    | MOSI (Pin 19)      |
|SO    | MISO (Pin 21)      |
|CSn   | CE0 (Pin 24)       |
|SCLK  | SCLK (Pin 23)      |
|GDO2\*| Any GPIO pin, commonly GPIO25 (Pin 22) \[[1](https://github.com/SpaceTeddy/CC1101/blob/0d0f011d3b808e36ad57fab596ed5e1db9516856/README.md#hardware-connection),[2](https://allgeek.de/2017/07/31/cc1101-spi-raspberry-adapter-fuer-homegear-homematicmax/),[3](https://securipi.co.uk/cc1101.pdf)\] |
|GDO0\*| Any GPIO pin, GPIO24 (Pin 18) recommended |
|GND   | Ground             |

No resistors required.
Connection of pins marked with \* is optional.
GDO2 stays "high until power and crystal have stabilized" (see `CHIP_RDYn` in docs).
GDO0 is used by `.asynchronous_transmission()` for data input.

If some of these pins are already in use,
select a different SPI bus or chip select:
https://www.raspberrypi.org/documentation/hardware/raspberrypi/spi/README.md
([permalink](https://github.com/raspberrypi/documentation/blob/d41d69f8efa3667b1a8b01a669238b8bd113edc1/hardware/raspberrypi/spi/README.md#hardware))

Raspberry Pi GPIO docs: https://www.raspberrypi.org/documentation/usage/gpio/

## Usage

### Library

See [examples](https://github.com/fphammerle/python-cc1101/blob/master/examples/).

```python
import cc1101

with cc1101.CC1101() as transceiver:
    transceiver.set_base_frequency_hertz(433.92e6)
    print(transceiver)
    transceiver.transmit(b"\x01\xff\x00 message")
```

In case CC1101 is connected to a different SPI bus or chip select line
than `/dev/spidev0.0`,
use `CC1101(spi_bus=?, spi_chip_select=?)`.

### Command Line

```sh
$ printf '\x01\x02\x03' | cc1101-transmit -f 433920000 -r 1000
```

See `cc1101-transmit --help`.

### Troubleshooting

In case a `PermissionError` gets raised,
check the permissions of `/dev/spidev*`.
You'll probably need `sudo usermod -a -G spi $USER`,
followed by a re-login.

Consult CC1101's offical docs for an in-depth explanation of all options:
https://www.ti.com/lit/ds/symlink/cc1101.pdf
