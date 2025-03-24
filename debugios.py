from SpeedUpUtils import *

# print(find_string_offset("output/Payload/com.egsdk.hywgldyz.app/hyrz","Error setting audio session active!"))


# find_cfstr_error_setting_au_address("output/Payload/com.egsdk.hywgldyz.app/hyrz2")


if __name__ == "__main__":
    offset = 0xF59C18
    subtract_value = 0x2000
    integer_part, difference = calculate_offset_and_difference(offset, subtract_value)
    print(f"Original Offset: 0x{offset:x}")
    print(f"After Subtracting 0x{subtract_value:x}: 0x{offset - subtract_value:x}")
    print(f"Integer Part: 0x{integer_part:x}")
    print(f"Difference: 0x{difference:x}")