import cc1101

with cc1101.CC1101() as transceiver:
    print(transceiver)
    print("state", transceiver.getMARCState().name)
    print("base frequency", transceiver.get_base_frequency_hertz(), "Hz")
    transceiver.set_base_frequency_hertz(443e6)
    print(transceiver)
