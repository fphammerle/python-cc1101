import enum

import spidev


class CC1101:

    # > All transfers on the SPI interface are done
    # > most significant bit first.
    # > All transactions on the SPI interface start with
    # > a header byte containing a R/W bit, a access bit (B),
    # > and a 6-bit address (A5 - A0).
    # > [...]
    # > Table 45: SPI Address Space
    _WRITE_SINGLE_BYTE = 0x00
    # > Registers with consecutive addresses can be
    # > accessed in an efficient way by setting the
    # > burst bit (B) in the header byte. The address
    # > bits (A5 - A0) set the start address in an
    # > internal address counter. This counter is
    # > incremented by one each new byte [...]
    _WRITE_BURST = 0x40
    _READ_SINGLE_BYTE = 0x80
    _READ_BURST = 0xC0

    class _SPIAddress(enum.IntEnum):
        # Table 45: SPI Address Space
        # > For register addresses in the range 0x30-0x3D,
        # > the burst bit is used to select between
        # > status registers when burst bit is one, and
        # > between command strobes when burst bit is
        # > zero. [...]
        # > Because of this, burst access is not available
        # > for status registers and they must be accessed
        # > one at a time. The status registers can only be
        # > read.
        SRES = 0x30
        PARTNUM = 0x30
        VERSION = 0x31
        MARCSTATE = 0x35

    class MainRadioControlStateMachineState(enum.IntEnum):
        """
        MARCSTATE - Main Radio Control State Machine State
        """

        IDLE = 0x01

    # 29.3 Status Register Details
    _SUPPORTED_PARTNUM = 0
    _SUPPORTED_VERSION = 0x14

    def __init__(self) -> None:
        self._spi = spidev.SpiDev()

    def _reset(self) -> None:
        assert self._spi.xfer([self._SPIAddress.SRES, 0]) == [0x0F, 0x0F]

    def _read_burst(self, register: _SPIAddress) -> int:
        response = self._spi.xfer([register | self._READ_BURST, 0])
        assert len(response) == 2, response
        assert response[0] == 0
        return response[1]

    def __enter__(self) -> "CC1101":
        # https://docs.python.org/3/reference/datamodel.html#object.__enter__
        self._spi.open(0, 0)
        self._spi.max_speed_hz = 55700  # empirical
        self._reset()
        partnum = self._read_burst(self._SPIAddress.PARTNUM)
        if partnum != self._SUPPORTED_PARTNUM:
            raise ValueError(
                "unexpected chip part number {} (expected: {})".format(
                    partnum, self._SUPPORTED_PARTNUM
                )
            )
        version = self._read_burst(self._SPIAddress.VERSION)
        if version != self._SUPPORTED_VERSION:
            raise ValueError(
                "unexpected chip version number {} (expected: {})".format(
                    version, self._SUPPORTED_VERSION
                )
            )
        marcstate = self.getMainRadioControlStateMachineState()
        if marcstate != self.MainRadioControlStateMachineState.IDLE:
            raise ValueError("expected marcstate idle (actual: {})".format(marcstate))
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        # https://docs.python.org/3/reference/datamodel.html#object.__exit__
        self._spi.close()
        return False

    def getMainRadioControlStateMachineState(self) -> MainRadioControlStateMachineState:
        return self.MainRadioControlStateMachineState(
            self._read_burst(self._SPIAddress.MARCSTATE)
        )

    def getMARCState(self) -> MainRadioControlStateMachineState:
        """
        alias for getMainRadioControlStateMachineState()
        """
        return self.getMainRadioControlStateMachineState()
