import pytest

import cc1101

# pylint: disable=protected-access


@pytest.mark.parametrize(
    ("rssi_index", "rssi_dbm"),
    [
        (128, -64 - 74),
        (204, -100),
        (255, -0.5 - 74),
        (0, -74),
        (64, 32 - 74),
        (127, 63.5 - 74),
    ],
)
def test_rss_dbm(rssi_index, rssi_dbm):
    packet = cc1101._ReceivedPacket(
        payload=b"\0",
        rssi_index=rssi_index,
        checksum_valid=True,
        link_quality_indicator=0,
    )
    assert packet.rssi_dbm == pytest.approx(rssi_dbm)


def test___str__():
    packet = cc1101._ReceivedPacket(
        payload=b"\0\x12\x34",
        rssi_index=204,
        checksum_valid=True,
        link_quality_indicator=0,
    )
    assert str(packet) == "_ReceivedPacket(RSSI -100dBm, 0x001234)"
