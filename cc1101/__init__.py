import enum

import spidev


class CC1101:

    # Table 45: SPI Address Space
    _READ_SINGLE_BYTE = 0x80

    class _Register(enum.IntEnum):
        SRES = 0x30
        # 29.3 Status Register Details
        PARTNUM = 0xF0
        VERSION = 0xF1

    # 29.3 Status Register Details
    _SUPPORTED_PARTNUM = 0
    _SUPPORTED_VERSION = 0x14

    def __init__(self) -> None:
        self._spi = spidev.SpiDev()

    def _reset(self) -> None:
        assert self._spi.xfer([self._Register.SRES, 0]) == [0x0F, 0x0F]

    def _read_single_byte(self, register: _Register) -> int:
        response = self._spi.xfer([self._READ_SINGLE_BYTE | register, 0])
        assert len(response) == 2, response
        assert response[0] == 0
        return response[1]

    def __enter__(self) -> "CC1101":
        # https://docs.python.org/3/reference/datamodel.html#object.__enter__
        self._spi.open(0, 0)
        self._spi.max_speed_hz = 55700  # empirical
        self._reset()
        partnum = self._read_single_byte(self._Register.PARTNUM)
        if partnum != self._SUPPORTED_PARTNUM:
            raise ValueError(
                "unexpected chip part number {} (expected: {})".format(
                    partnum, self._SUPPORTED_PARTNUM
                )
            )
        version = self._read_single_byte(self._Register.VERSION)
        if version != self._SUPPORTED_VERSION:
            raise ValueError(
                "unexpected chip version number {} (expected: {})".format(
                    version, self._SUPPORTED_VERSION
                )
            )
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        # https://docs.python.org/3/reference/datamodel.html#object.__exit__
        self._spi.close()
        return False
