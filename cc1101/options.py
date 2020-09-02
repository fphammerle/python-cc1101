import enum


class ModulationFormat(enum.IntEnum):
    """
    MDMCFG2.MOD_FORMAT
    """

    FSK2 = 0b000
    GFSK = 0b001
    ASK_OOK = 0b011
    FSK4 = 0b100
    MSK = 0b111


class SyncMode(enum.IntEnum):
    """
    MDMCFG2.SYNC_MODE

    see "14.3 Byte Synchronization"
    """

    NO_PREAMBLE_AND_SYNC_WORD = 0b00
    TRANSMIT_16_MATCH_15_BITS = 0b01
    TRANSMIT_16_MATCH_16_BITS = 0b10
    TRANSMIT_32_MATCH_30_BITS = 0b11
