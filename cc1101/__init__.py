import enum
import logging
import typing

import spidev


_LOGGER = logging.getLogger(__name__)


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
        # see "Table 45: SPI Address Space"
        # > The configuration registers on the CC1101 are
        # > located on SPI addresses from 0x00 to 0x2E.
        PKTLEN = 0x06
        FREQ2 = 0x0D
        FREQ1 = 0x0E
        FREQ0 = 0x0F
        MDMCFG4 = 0x10
        MDMCFG3 = 0x11
        MDMCFG2 = 0x12
        MCSM0 = 0x18
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
        STX = 0x35
        SFTX = 0x3B
        PARTNUM = 0x30
        VERSION = 0x31
        MARCSTATE = 0x35
        # see "10.5 FIFO Access"
        # > When the R/W-bit is zero, the TX FIFO is
        # > accessed, and the RX FIFO is accessed when
        # > the R/W-bit is one.
        TXFIFO = 0x3F

    class ModulationFormat(enum.IntEnum):
        """
        MDMCFG2.MOD_FORMAT
        """

        FSK2 = 0b000
        GFSK = 0b001
        ASK_OOK = 0b011
        FSK4 = 0b100
        MSK = 0b111

    class MainRadioControlStateMachineState(enum.IntEnum):
        """
        MARCSTATE - Main Radio Control State Machine State
        """

        # see "Figure 13: Simplified State Diagram"
        # and "Figure 25: Complete Radio Control State Diagram"
        IDLE = 0x01
        STARTCAL = 0x08  # after IDLE
        BWBOOST = 0x09  # after STARTCAL
        FS_LOCK = 0x0A
        TX = 0x13

    # 29.3 Status Register Details
    _SUPPORTED_PARTNUM = 0
    _SUPPORTED_VERSION = 0x14

    _CRYSTAL_OSCILLATOR_FREQUENCY_HERTZ = 26e6
    # see "21 Frequency Programming"
    # > f_carrier = f_XOSC / 2**16 * (FREQ + CHAN * ((256 + CHANSPC_M) * 2**CHANSPC_E-2))
    _FREQUENCY_CONTROL_WORD_HERTZ_FACTOR = _CRYSTAL_OSCILLATOR_FREQUENCY_HERTZ / 2 ** 16

    def __init__(self) -> None:
        self._spi = spidev.SpiDev()

    @staticmethod
    def _log_chip_status_byte(chip_status: int) -> None:
        # see "10.1 Chip Status Byte" & "Table 23: Status Byte Summary"
        _LOGGER.debug(
            "chip status byte: CHIP_RDYn=%d STATE=%s FIFO_BYTES_AVAILBLE=%d",
            chip_status >> 7,
            bin((chip_status >> 4) & 0b111),
            chip_status & 0b1111,
        )

    def _read_single_byte(self, register: _SPIAddress) -> int:
        response = self._spi.xfer([register | self._READ_SINGLE_BYTE, 0])
        assert len(response) == 2, response
        self._log_chip_status_byte(response[0])
        return response[1]

    def _read_burst(self, start_register: _SPIAddress, length: int) -> typing.List[int]:
        response = self._spi.xfer([start_register | self._READ_BURST] + [0] * length)
        assert len(response) == length + 1, response
        self._log_chip_status_byte(response[0])
        return response[1:]

    def _read_status_register(self, register: _SPIAddress) -> int:
        _LOGGER.debug("reading status register 0x%02x", register)
        values = self._read_burst(start_register=register, length=1)
        assert len(values) == 1, values
        return values[0]

    def _command_strobe(self, register: _SPIAddress) -> None:
        # see "10.4 Command Strobes"
        _LOGGER.debug("sending command strobe 0x%02x", register)
        response = self._spi.xfer([register | self._WRITE_SINGLE_BYTE])
        assert len(response) == 1, response
        self._log_chip_status_byte(response[0])

    def _write_burst(
        self, start_register: _SPIAddress, values: typing.List[int]
    ) -> None:
        _LOGGER.debug(
            "writing burst: start_register=0x%02x values=%s", start_register, values
        )
        response = self._spi.xfer([start_register | self._WRITE_BURST] + values)
        assert len(response) == len(values) + 1, response
        self._log_chip_status_byte(response[0])
        assert all(v == 0x0F for v in response[1:]), response  # TODO why?

    def _reset(self) -> None:
        self._command_strobe(self._SPIAddress.SRES)

    def _get_symbol_rate_exponent(self) -> int:
        """
        MDMCFG4.DRATE_E
        """
        return self._read_single_byte(self._SPIAddress.MDMCFG4) & 0b00001111

    def _get_symbol_rate_mantissa(self) -> int:
        """
        MDMCFG3.DRATE_M
        """
        return self._read_single_byte(self._SPIAddress.MDMCFG3)

    def get_symbol_rate_baud(self) -> float:
        # see "12 Data Rate Programming"
        return (
            (256 + self._get_symbol_rate_mantissa())
            * (2 ** self._get_symbol_rate_exponent())
            * self._CRYSTAL_OSCILLATOR_FREQUENCY_HERTZ
            / (2 ** 28)
        )

    def get_modulation_format(self) -> ModulationFormat:
        mdmcfg2 = self._read_single_byte(self._SPIAddress.MDMCFG2)
        return self.ModulationFormat((mdmcfg2 >> 4) & 0b111)

    def _set_modulation_format(self, modulation_format: ModulationFormat) -> None:
        mdmcfg2 = self._read_single_byte(self._SPIAddress.MDMCFG2)
        mdmcfg2 &= ~(modulation_format << 4)
        mdmcfg2 |= modulation_format << 4
        self._write_burst(self._SPIAddress.MDMCFG2, [mdmcfg2])

    def __enter__(self) -> "CC1101":
        # https://docs.python.org/3/reference/datamodel.html#object.__enter__
        self._spi.open(0, 0)
        self._spi.max_speed_hz = 55700  # empirical
        self._reset()
        partnum = self._read_status_register(self._SPIAddress.PARTNUM)
        if partnum != self._SUPPORTED_PARTNUM:
            raise ValueError(
                "unexpected chip part number {} (expected: {})".format(
                    partnum, self._SUPPORTED_PARTNUM
                )
            )
        version = self._read_status_register(self._SPIAddress.VERSION)
        if version != self._SUPPORTED_VERSION:
            raise ValueError(
                "unexpected chip version number {} (expected: {})".format(
                    version, self._SUPPORTED_VERSION
                )
            )
        # 6:4 MOD_FORMAT: OOK (default: 2-FSK)
        self._set_modulation_format(self.ModulationFormat.ASK_OOK)
        # 7:6 unused
        # 5:4 FS_AUTOCAL: calibrate when going from IDLE to RX or TX
        # 3:2 PO_TIMEOUT: default
        # 1 PIN_CTRL_EN: default
        # 0 XOSC_FORCE_ON: default
        self._write_burst(self._SPIAddress.MCSM0, [0b010100])
        marcstate = self.get_main_radio_control_state_machine_state()
        if marcstate != self.MainRadioControlStateMachineState.IDLE:
            raise ValueError("expected marcstate idle (actual: {})".format(marcstate))
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        # https://docs.python.org/3/reference/datamodel.html#object.__exit__
        self._spi.close()
        return False

    def get_main_radio_control_state_machine_state(
        self
    ) -> MainRadioControlStateMachineState:
        return self.MainRadioControlStateMachineState(
            self._read_status_register(self._SPIAddress.MARCSTATE)
        )

    def get_marc_state(self) -> MainRadioControlStateMachineState:
        """
        alias for get_main_radio_control_state_machine_state()
        """
        return self.get_main_radio_control_state_machine_state()

    @classmethod
    def _frequency_control_word_to_hertz(cls, control_word: typing.List[int]) -> float:
        return (
            int.from_bytes(control_word, byteorder="big", signed=False)
            * cls._FREQUENCY_CONTROL_WORD_HERTZ_FACTOR
        )

    @classmethod
    def _hertz_to_frequency_control_word(cls, hertz: float) -> typing.List[int]:
        return list(
            round(hertz / cls._FREQUENCY_CONTROL_WORD_HERTZ_FACTOR).to_bytes(
                length=3, byteorder="big", signed=False
            )
        )

    def _get_base_frequency_control_word(self) -> typing.List[int]:
        # > The base or start frequency is set by the 24 bitfrequency
        # > word located in the FREQ2, FREQ1, FREQ0 registers.
        return self._read_burst(start_register=self._SPIAddress.FREQ2, length=3)

    def _set_base_frequency_control_word(self, control_word: typing.List[int]) -> None:
        self._write_burst(start_register=self._SPIAddress.FREQ2, values=control_word)

    def get_base_frequency_hertz(self) -> float:
        return self._frequency_control_word_to_hertz(
            self._get_base_frequency_control_word()
        )

    def set_base_frequency_hertz(self, freq: float) -> None:
        self._set_base_frequency_control_word(
            self._hertz_to_frequency_control_word(freq)
        )

    def __str__(self) -> str:
        return "CC1101(marcstate={}, base_frequency={:.2f}MHz, symbol_rate={:.2f}kBaud, modulation_format={})".format(
            self.get_main_radio_control_state_machine_state().name.lower(),
            self.get_base_frequency_hertz() / 10 ** 6,
            self.get_symbol_rate_baud() / 1000,
            self.get_modulation_format().name,
        )

    def _get_packet_length(self) -> int:
        """
        packet length in fixed packet length mode,
        maximum packet length in variable packet length mode.
        """
        return self._read_burst(start_register=self._SPIAddress.PKTLEN, length=1)[0]

    def _flush_tx_fifo_buffer(self) -> str:
        # > Only issue SFTX in IDLE or TXFIFO_UNDERFLOW states.
        _LOGGER.debug("flushing tx fifo buffer")
        self._command_strobe(self._SPIAddress.SFTX)

    def transmit(self, payload: typing.List[int]) -> None:
        # see "15.2 Packet Format"
        # > In variable packet length mode, [...]
        # > The first byte written to the TXFIFO must be different from 0.
        if payload[0] == 0:
            raise ValueError(
                "in variable packet length mode the first byte of payload must not be null"
                + "\npayload: {}".format(payload)
            )
        marcstate = self.get_main_radio_control_state_machine_state()
        if marcstate != self.MainRadioControlStateMachineState.IDLE:
            raise Exception(
                "device must be idle before transmission (current marcstate: {})".format(
                    marcstate.name
                )
            )
        max_packet_length = self._get_packet_length()
        if len(payload) > max_packet_length:
            raise ValueError(
                "payload exceeds maximum payload length of {} bytes".format(
                    max_packet_length
                )
                + "\npayload: {}".format(payload)
            )
        self._flush_tx_fifo_buffer()
        self._write_burst(self._SPIAddress.TXFIFO, payload)
        _LOGGER.info("transmitting %s", payload)
        self._command_strobe(self._SPIAddress.STX)
