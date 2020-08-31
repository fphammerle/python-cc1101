import cc1101


with cc1101.CC1101() as transceiver:
    for register, value in transceiver.get_configuration_register_values().items():
        print(
            f"0x{register:02x}\t{register.name}\t=\t0x{value:02x}\t{value}\t0b{value:08b}"
        )
