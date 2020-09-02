# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2020-09-02
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

[Unreleased]: https://github.com/fphammerle/python-cc1101/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/fphammerle/python-cc1101/releases/tag/v0.1.0
