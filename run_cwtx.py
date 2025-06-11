import cc1101
import time
import RPi.GPIO as GPIO
import sys
from cc1101 import StrobeAddress, ConfigurationRegisterAddress

CSN_PIN = 23

FREQ = (
    float(sys.argv[1]) * 1e6 if len(sys.argv) > 1 else 433.92e6
)  # Default to 433.92 MHz

GPIO.setmode(GPIO.BCM)
GPIO.setup(CSN_PIN, GPIO.OUT)
GPIO.output(CSN_PIN, GPIO.HIGH)


def write_register(trx, reg, val):
    GPIO.output(CSN_PIN, GPIO.LOW)
    time.sleep(0.001)
    trx._spi.xfer([reg | 0x00, val])  # single write
    GPIO.output(CSN_PIN, GPIO.HIGH)


with cc1101.CC1101() as trx:
    trx.set_base_frequency_hertz(FREQ)
    trx.set_output_power([0xC0])  # 10 dBm

    # Enter CW mode
    write_register(trx, ConfigurationRegisterAddress.MDMCFG2, 0x30)  # unmodulated
    write_register(trx, ConfigurationRegisterAddress.FREND0, 0x11)
    write_register(trx, ConfigurationRegisterAddress.FSCAL2, 0x0A)
    write_register(
        trx, ConfigurationRegisterAddress.PKTCTRL0, 0x00
    )  # No packet handling
    write_register(
        trx, ConfigurationRegisterAddress.IOCFG0, 0x06
    )  # Optional: GDO0 to sync

    # STX to enter TX mode
    trx._command_strobe(StrobeAddress.SIDLE)  # Ensure idle first
    trx._command_strobe(StrobeAddress.SFTX)  # Flush TX FIFO
    trx._command_strobe(StrobeAddress.STX)

    print(f"Transmitting CW at {FREQ / 1e6} MHz. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping.")
        trx._command_strobe(StrobeAddress.SIDLE)
