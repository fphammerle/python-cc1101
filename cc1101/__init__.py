import contextlib
import enum
import logging
import math
import typing

import spidev

from cc1101.addresses import (
    StrobeAddress,
    ConfigurationRegisterAddress,
    StatusRegisterAddress,
    FIFORegisterAddress,
)
from cc1101.options import SyncMode, ModulationFormat


_LOGGER = logging.getLogger(__name__)


class Pin(enum.Enum):
    GDO0 = "GDO0"


class _TransceiveMode(enum.IntEnum):
    """
    PKTCTRL0.PKT_FORMAT
    """

    FIFO = 0b00
    SYNCHRONOUS_SERIAL = 0b01
    RANDOM_TRANSMISSION = 0b10
    ASYNCHRONOUS_SERIAL = 0b11


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

    def _read_single_byte(
        self, register: typing.Union[ConfigurationRegisterAddress, FIFORegisterAddress]
    ) -> int:
        response = self._spi.xfer([register | self._READ_SINGLE_BYTE, 0])
        assert len(response) == 2, response
        self._log_chip_status_byte(response[0])
        return response[1]

    def _read_burst(
        self,
        start_register: typing.Union[ConfigurationRegisterAddress, FIFORegisterAddress],
        length: int,
    ) -> typing.List[int]:
        response = self._spi.xfer([start_register | self._READ_BURST] + [0] * length)
        assert len(response) == length + 1, response
        self._log_chip_status_byte(response[0])
        return response[1:]

    def _read_status_register(self, register: StatusRegisterAddress) -> int:
        # > For register addresses in the range 0x30-0x3D,
        # > the burst bit is used to select between
        # > status registers when burst bit is one, and
        # > between command strobes when burst bit is
        # > zero. [...]
        # > Because of this, burst access is not available
        # > for status registers and they must be accessed
        # > one at a time. The status registers can only be
        # > read.
        response = self._spi.xfer([register | self._READ_BURST, 0])
        assert len(response) == 2, response
        self._log_chip_status_byte(response[0])
        return response[1]

    def _command_strobe(self, register: StrobeAddress) -> None:
        # see "10.4 Command Strobes"
        _LOGGER.debug("sending command strobe 0x%02x", register)
        response = self._spi.xfer([register | self._WRITE_SINGLE_BYTE])
        assert len(response) == 1, response
        self._log_chip_status_byte(response[0])

    def _write_burst(
        self,
        start_register: typing.Union[ConfigurationRegisterAddress, FIFORegisterAddress],
        values: typing.List[int],
    ) -> None:
        _LOGGER.debug(
            "writing burst: start_register=0x%02x values=%s", start_register, values
        )
        response = self._spi.xfer([start_register | self._WRITE_BURST] + values)
        assert len(response) == len(values) + 1, response
        self._log_chip_status_byte(response[0])
        assert all(v == response[0] for v in response[1:]), response

    def _reset(self) -> None:
        self._command_strobe(StrobeAddress.SRES)

    def _get_symbol_rate_exponent(self) -> int:
        """
        MDMCFG4.DRATE_E
        """
        return self._read_single_byte(ConfigurationRegisterAddress.MDMCFG4) & 0b00001111

    def _set_symbol_rate_exponent(self, exponent: int):
        mdmcfg4 = self._read_single_byte(ConfigurationRegisterAddress.MDMCFG4)
        mdmcfg4 &= 0b11110000
        mdmcfg4 |= exponent
        self._write_burst(
            start_register=ConfigurationRegisterAddress.MDMCFG4, values=[mdmcfg4]
        )

    def _get_symbol_rate_mantissa(self) -> int:
        """
        MDMCFG3.DRATE_M
        """
        return self._read_single_byte(ConfigurationRegisterAddress.MDMCFG3)

    def _set_symbol_rate_mantissa(self, mantissa: int) -> None:
        self._write_burst(
            start_register=ConfigurationRegisterAddress.MDMCFG3, values=[mantissa]
        )

    @classmethod
    def _symbol_rate_floating_point_to_real(cls, mantissa: int, exponent: int) -> float:
        # see "12 Data Rate Programming"
        return (
            (256 + mantissa)
            * (2 ** exponent)
            * cls._CRYSTAL_OSCILLATOR_FREQUENCY_HERTZ
            / (2 ** 28)
        )

    @classmethod
    def _symbol_rate_real_to_floating_point(cls, real: float) -> typing.Tuple[int, int]:
        # see "12 Data Rate Programming"
        assert real > 0, real
        exponent = math.floor(
            math.log2(real / cls._CRYSTAL_OSCILLATOR_FREQUENCY_HERTZ) + 20
        )
        mantissa = round(
            real * 2 ** 28 / cls._CRYSTAL_OSCILLATOR_FREQUENCY_HERTZ / 2 ** exponent
            - 256
        )
        if mantissa == 256:
            exponent += 1
            mantissa = 0
        assert 0 < exponent <= 2 ** 4, exponent
        assert mantissa <= 2 ** 8, mantissa
        return mantissa, exponent

    def get_symbol_rate_baud(self) -> float:
        return self._symbol_rate_floating_point_to_real(
            mantissa=self._get_symbol_rate_mantissa(),
            exponent=self._get_symbol_rate_exponent(),
        )

    def set_symbol_rate_baud(self, real: float) -> None:
        # > The data rate can be set from 0.6 kBaud to 500 kBaud [...]
        mantissa, exponent = self._symbol_rate_real_to_floating_point(real)
        self._set_symbol_rate_mantissa(mantissa)
        self._set_symbol_rate_exponent(exponent)

    def get_modulation_format(self) -> ModulationFormat:
        mdmcfg2 = self._read_single_byte(ConfigurationRegisterAddress.MDMCFG2)
        return ModulationFormat((mdmcfg2 >> 4) & 0b111)

    def _set_modulation_format(self, modulation_format: ModulationFormat) -> None:
        mdmcfg2 = self._read_single_byte(ConfigurationRegisterAddress.MDMCFG2)
        mdmcfg2 &= ~(modulation_format << 4)
        mdmcfg2 |= modulation_format << 4
        self._write_burst(ConfigurationRegisterAddress.MDMCFG2, [mdmcfg2])

    def enable_manchester_code(self) -> None:
        """
        MDMCFG2.MANCHESTER_EN

        Enable manchester encoding & decoding.
        """
        mdmcfg2 = self._read_single_byte(ConfigurationRegisterAddress.MDMCFG2)
        mdmcfg2 |= 0b1000
        self._write_burst(ConfigurationRegisterAddress.MDMCFG2, [mdmcfg2])

    def get_sync_mode(self) -> SyncMode:
        mdmcfg2 = self._read_single_byte(ConfigurationRegisterAddress.MDMCFG2)
        return SyncMode(mdmcfg2 & 0b11)

    def set_sync_mode(self, mode: SyncMode) -> None:
        """
        MDMCFG2.SYNC_MODE

        see "14.3 Byte Synchronization"
        """
        mdmcfg2 = self._read_single_byte(ConfigurationRegisterAddress.MDMCFG2)
        mdmcfg2 &= 0b11111100
        mdmcfg2 |= mode
        self._write_burst(ConfigurationRegisterAddress.MDMCFG2, [mdmcfg2])

    def _set_power_amplifier_setting_index(self, setting_index: int) -> None:
        """
        FREND0.PA_POWER

        > This value is an index to the PATABLE,
        > which can be programmed with up to 8 different PA settings.

        > In OOK/ASK mode, this selects the PATABLE index to use
        > when transmitting a '1'.
        > PATABLE index zero is used in OOK/ASK when transmitting a '0'.
        > The PATABLE settings from index 0 to the PA_POWER value are
        > used for > ASK TX shaping, [...]

        see "Figure 32: Shaping of ASK Signal"

        > If OOK modulation is used, the logic 0 and logic 1 power levels
        > shall be programmed to index 0 and 1 respectively.
        """
        frend0 = self._read_single_byte(ConfigurationRegisterAddress.FREND0)
        frend0 &= 0b000
        frend0 |= setting_index
        self._write_burst(ConfigurationRegisterAddress.FREND0, [setting_index])

    def __enter__(self) -> "CC1101":
        # https://docs.python.org/3/reference/datamodel.html#object.__enter__
        self._spi.open(0, 0)
        self._spi.max_speed_hz = 55700  # empirical
        self._reset()
        partnum = self._read_status_register(StatusRegisterAddress.PARTNUM)
        if partnum != self._SUPPORTED_PARTNUM:
            raise ValueError(
                "unexpected chip part number {} (expected: {})".format(
                    partnum, self._SUPPORTED_PARTNUM
                )
            )
        version = self._read_status_register(StatusRegisterAddress.VERSION)
        if version != self._SUPPORTED_VERSION:
            raise ValueError(
                "unexpected chip version number {} (expected: {})".format(
                    version, self._SUPPORTED_VERSION
                )
            )
        # 6:4 MOD_FORMAT: OOK (default: 2-FSK)
        self._set_modulation_format(ModulationFormat.ASK_OOK)
        self._set_power_amplifier_setting_index(1)
        self._disable_data_whitening()
        # 7:6 unused
        # 5:4 FS_AUTOCAL: calibrate when going from IDLE to RX or TX
        # 3:2 PO_TIMEOUT: default
        # 1 PIN_CTRL_EN: default
        # 0 XOSC_FORCE_ON: default
        self._write_burst(ConfigurationRegisterAddress.MCSM0, [0b010100])
        marcstate = self.get_main_radio_control_state_machine_state()
        if marcstate != MainRadioControlStateMachineState.IDLE:
            raise ValueError("expected marcstate idle (actual: {})".format(marcstate))
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        # https://docs.python.org/3/reference/datamodel.html#object.__exit__
        self._spi.close()
        return False

    def get_main_radio_control_state_machine_state(
        self
    ) -> MainRadioControlStateMachineState:
        return MainRadioControlStateMachineState(
            self._read_status_register(StatusRegisterAddress.MARCSTATE)
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
        return self._read_burst(
            start_register=ConfigurationRegisterAddress.FREQ2, length=3
        )

    def _set_base_frequency_control_word(self, control_word: typing.List[int]) -> None:
        self._write_burst(
            start_register=ConfigurationRegisterAddress.FREQ2, values=control_word
        )

    def get_base_frequency_hertz(self) -> float:
        return self._frequency_control_word_to_hertz(
            self._get_base_frequency_control_word()
        )

    def set_base_frequency_hertz(self, freq: float) -> None:
        self._set_base_frequency_control_word(
            self._hertz_to_frequency_control_word(freq)
        )

    def __str__(self) -> str:
        attrs = (
            "marcstate={}".format(
                self.get_main_radio_control_state_machine_state().name.lower()
            ),
            "base_frequency={:.2f}MHz".format(
                self.get_base_frequency_hertz() / 10 ** 6
            ),
            "symbol_rate={:.2f}kBaud".format(self.get_symbol_rate_baud() / 1000),
            "modulation_format={}".format(self.get_modulation_format().name),
            "sync_mode={}".format(self.get_sync_mode().name),
        )
        return "CC1101({})".format(", ".join(attrs))

    def _get_packet_length(self) -> int:
        """
        packet length in fixed packet length mode,
        maximum packet length in variable packet length mode.
        """
        return self._read_single_byte(ConfigurationRegisterAddress.PKTLEN)

    def get_configuration_register_values(
        self,
        start_register: ConfigurationRegisterAddress = min(
            ConfigurationRegisterAddress
        ),
        end_register: ConfigurationRegisterAddress = max(ConfigurationRegisterAddress),
    ) -> typing.Dict[ConfigurationRegisterAddress, int]:
        assert start_register <= end_register, (start_register, end_register)
        values = self._read_burst(
            start_register=start_register, length=end_register - start_register + 1
        )
        return {
            ConfigurationRegisterAddress(start_register + i): v
            for i, v in enumerate(values)
        }

    def _disable_data_whitening(self):
        """
        PKTCTRL0.WHITE_DATA

        see "15.1 Data Whitening"

        > By setting PKTCTRL0.WHITE_DATA=1 [default],
        > all data, except the preamble and the sync word
        > will be XOR-ed with a 9-bit pseudo-random (PN9)
        > sequence before being transmitted.
        """
        pktctrl0 = self._read_single_byte(ConfigurationRegisterAddress.PKTCTRL0)
        pktctrl0 &= 0b10111111
        self._write_burst(
            start_register=ConfigurationRegisterAddress.PKTCTRL0, values=[pktctrl0]
        )

    def _get_transceive_mode(self) -> _TransceiveMode:
        pktctrl0 = self._read_single_byte(ConfigurationRegisterAddress.PKTCTRL0)
        return _TransceiveMode((pktctrl0 >> 4) & 0b11)

    def _set_transceive_mode(self, mode: _TransceiveMode) -> None:
        _LOGGER.info("changing transceive mode to %s", mode.name)
        pktctrl0 = self._read_single_byte(ConfigurationRegisterAddress.PKTCTRL0)
        pktctrl0 &= ~0b00110000
        pktctrl0 |= mode << 4
        self._write_burst(
            start_register=ConfigurationRegisterAddress.PKTCTRL0, values=[pktctrl0]
        )

    def _flush_tx_fifo_buffer(self) -> None:
        # > Only issue SFTX in IDLE or TXFIFO_UNDERFLOW states.
        _LOGGER.debug("flushing tx fifo buffer")
        self._command_strobe(StrobeAddress.SFTX)

    def transmit(self, payload: bytes) -> None:
        # see "15.2 Packet Format"
        # > In variable packet length mode, [...]
        # > The first byte written to the TXFIFO must be different from 0.
        if payload[0] == 0:
            raise ValueError(
                "in variable packet length mode the first byte of payload must not be null"
                + "\npayload: {!r}".format(payload)
            )
        marcstate = self.get_main_radio_control_state_machine_state()
        if marcstate != MainRadioControlStateMachineState.IDLE:
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
                + "\npayload: {!r}".format(payload)
            )
        self._flush_tx_fifo_buffer()
        self._write_burst(FIFORegisterAddress.TX, list(payload))
        _LOGGER.info(
            "transmitting 0x%s (%r)",
            "".join("{:02x}".format(b) for b in payload),
            payload,
        )
        self._command_strobe(StrobeAddress.STX)

    @contextlib.contextmanager
    def asynchronous_transmission(self) -> typing.Iterator[Pin]:
        """
        see "27.1 Asynchronous Serial Operation"

        >>> with cc1101.CC1101() as transceiver:
        >>>     transceiver.set_base_frequency_hertz(433.92e6)
        >>>     transceiver.set_symbol_rate_baud(600)
        >>>     print(transceiver)
        >>>     with transceiver.asynchronous_transmission():
        >>>         # send digital signal to GDO0 pin
        """
        self._set_transceive_mode(_TransceiveMode.ASYNCHRONOUS_SERIAL)
        self._command_strobe(StrobeAddress.STX)
        try:
            # > In TX, the GDO0 pin is used for data input (TX data).
            yield Pin.GDO0
        finally:
            self._command_strobe(StrobeAddress.SIDLE)
            self._set_transceive_mode(_TransceiveMode.FIFO)
