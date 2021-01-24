# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.7.0] - 2021-01-24
### Added
- method `set/get_output_power` to configure/retrieve output power settings
  (`PATABLE` and `FREND0.PA_POWER`)
- all commands: added parameter `-p/--output-power`
- command `cc1101-export-config`: append values of `PATABLE` register as comment

### Fixed
- default config via private/unstable method `_set_power_amplifier_setting_index`:
  no longer set `FREND0.LODIV_BUF_CURRENT_TX` to `0` (default: `1`)

## [2.6.1] - 2021-01-16
### Fixed
- private/unstable method `_set_modulation_format`:
  fixed incorrect configuration of `MDMCFG2` register

## [2.6.0] - 2021-01-04
### Added
- command `cc1101-export-config` to export / inspect config register values
  after configuration via command-line arguments & options matching `cc1101-transmit`

### Fixed
- `cc1101-transmit` command:
  - set `flock` on SPI device file to avoid race conditions,
    if other processes attempt to use the same transceiver
  - configure transceiver after reading from stdin
    to avoid delay between configuration and transmission, if pipe is slow

## [2.5.0] - 2020-12-30
### Added
- added command `cc1101-transmit` to transmit via command-line interface
- warn when selecting frequency below supported range

## [2.4.0] - 2020-12-13
### Added
- support chip version `0x04`

## [2.3.0] - 2020-12-11
### Added
- option `CC1101(lock_spi_device=True)` sets an advisory, exclusive,
  non-blocking `flock` on the SPI device file `/dev/spidev?.?`
- method `.unlock_spi_device()` to release `flock` manually

## [2.2.0] - 2020-12-08
### Added
- select arbitrary device via `CC1101(spi_bus=?, spi_chip_select=?)`
- added explanation to `PermissionError` on `SpiDev.open()`

## [2.1.0] - 2020-12-04
### Added
- method `.get_sync_word()`
- method `.set_sync_word()`
- method `.get_preamble_length_bytes()`
- method `.set_preamble_length_bytes()`
- preamble length & sync word in string representation

## [2.0.0] - 2020-12-03
### Changed
- `transmit()`: prepend length byte in variable packet length mode internally
  to avoid accidental incomplete transmissions and TX FIFO underflows

## [1.2.0] - 2020-12-02
### Added
- support for fixed packet length mode
  via new method `set_packet_length_mode(PacketLengthMode.FIXED)`
- new enum `options.PacketLengthMode`
- new method `get_packet_length_mode()`
- method `get_packet_length_bytes()` is now public
- new method `set_packet_length_bytes()`
- added configured packet length to `CC1101`'s string representation
  (`≤n` indicates variable length mode, `=n` fixed length mode)

## [1.1.0] - 2020-12-01
### Added
- method `disable_checksum()` to disable automatic CRC sum
  appending in TX mode and checking in RX mode

## [1.0.0] - 2020-09-02
### Added
- `CC1101` class providing
  - context manager to open SPI port
  - `transmit()` for buffered transmission
  - context manager `asynchronous_transmission()` for manual signal generation
  - `get_configuration_register_values()` to read all configuration registers
- OOK modulation
- configurable symbol rate & sync mode
- optional manchester encoding
- disabled data whitening
- automatic calibration

[Unreleased]: https://github.com/fphammerle/python-cc1101/compare/v2.7.0...HEAD
[2.7.0]: https://github.com/fphammerle/python-cc1101/compare/v2.6.1...v2.7.0
[2.6.1]: https://github.com/fphammerle/python-cc1101/compare/v2.6.0...v2.6.1
[2.6.0]: https://github.com/fphammerle/python-cc1101/compare/v2.5.0...v2.6.0
[2.5.0]: https://github.com/fphammerle/python-cc1101/compare/v2.4.0...v2.5.0
[2.4.0]: https://github.com/fphammerle/python-cc1101/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/fphammerle/python-cc1101/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/fphammerle/python-cc1101/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/fphammerle/python-cc1101/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/fphammerle/python-cc1101/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/fphammerle/python-cc1101/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/fphammerle/python-cc1101/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/fphammerle/python-cc1101/releases/tag/v1.0.0
