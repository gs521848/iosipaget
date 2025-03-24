from keystone import *
import lief


# 读取offset的byte
def read_bytes_at_offset(file_path, offset, length):
    try:
        with open(file_path, 'rb') as file:  # 以二进制模式打开文件
            file.seek(offset)  # 跳转到指定偏移地址
            data = file.read(length)  # 读取指定长度的字节
            return data
    except Exception as e:
        print(f"读取文件失败: {e}")
        return None


# 找到hex的offset的地址
def find_hex_offset(file_path, hex_str):
    # 将十六进制字符串转换为字节序列
    hex_bytes = bytes.fromhex(hex_str)

    # 打开文件并读取内容
    with open(file_path, 'rb') as file:
        data = file.read()

    # 搜索字节序列
    offset = data.find(hex_bytes)

    if offset != -1:
        return offset
    else:
        return None


def write_value_to_offset(file_path, offset, value, byteorder='big'):
    """
    将指定值写入文件的指定偏移量。

    :param file_path: 文件路径
    :param offset: 文件偏移量
    :param value: 要写入的值（十六进制字符串，如 "0x12345678"）
    :param byteorder: 字节序（'big' 或 'little'，默认为 'big'）
    """
    # 将十六进制字符串转换为整数
    value_int = int(value, 16)

    # 计算需要的字节数
    num_bytes = (value_int.bit_length() + 7) // 8  # 计算最小需要的字节数
    if num_bytes == 0:
        num_bytes = 1  # 至少写入 1 个字节

    # 将值转换为字节序列
    value_bytes = value_int.to_bytes(num_bytes, byteorder=byteorder)
    print(f"Bytes to write: {value_bytes}")

    # 打开文件并写入字节
    with open(file_path, 'r+b') as file:
        file.seek(offset)  # 跳转到指定偏移量
        file.write(value_bytes)  # 写入字节
    print(f"Successfully wrote {num_bytes} bytes to offset 0x{offset:x}")


# 计算64位的补位代码
def to_64bit_signed_hex(value):
    # 如果 value 是字符串，先转换为整数
    if isinstance(value, str):
        if value.startswith("-"):
            # 处理负数字符串
            value = -int(value[1:], 16)
        else:
            # 处理正数字符串
            value = int(value, 16)
    # 将负数转换为 64 位补码
    if value < 0:
        value = (1 << 64) + value
    return f"{value:016X}"


def assemble_to_hex(asm_code):
    ks = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)

    # 将汇编代码转换为机器码
    encoding, count = ks.asm(asm_code)
    print("Encoding:", encoding)
    # 将机器码转换为 4 字节的十六进制码
    hex_code = ''.join(f"{byte:02X}" for byte in encoding)
    return hex_code[:8]


def find_string_offset(file_path, target_string, encoding='utf-8'):
    # 将目标字符串转换为字节序列
    target_bytes = target_string.encode(encoding)

    # 打开文件并搜索字符串
    with open(file_path, 'rb') as file:
        data = file.read()
        offset = data.find(target_bytes)

        if offset != -1:
            return offset
        else:
            return None


import lief


def find_string_and_caller(macho_path, target_string):
    # 加载 Mach-O 文件
    file_addr = 0
    binary = lief.parse(macho_path)
    if binary is None:
        raise ValueError("Failed to parse Mach-O file")

    # 查找 __TEXT 段
    text_segment = None
    for segment in binary.segments:

        if segment.name == "__TEXT":
            text_segment = segment

    if text_segment is None:
        raise ValueError("__TEXT segment not found")

    # 查找 __cstring 节
    cstring_section = None
    for section in text_segment.sections:
        if section.name == "__cstring":
            cstring_section = section
            break

    if cstring_section is None:
        raise ValueError("__cstring section not found")

    # 获取 __cstring 节的内容
    cstring_data = bytes(cstring_section.content)

    # 提取所有字符串
    strings = []
    current_string = ""
    for byte in cstring_data:
        if byte == 0:  # 字符串以 null 结尾
            if current_string:
                strings.append(current_string)
                current_string = ""
        else:
            current_string += chr(byte)
    # 查找目标字符串
    target_address = None
    for idx, string in enumerate(strings):
        if target_string in string:
            # 计算目标字符串的地址
            target_address = cstring_section.virtual_address + cstring_data.find(string.encode('utf-8'))
            print(target_address)
            break

    if target_address is None:
        raise ValueError(f"Target string '{target_string}' not found in __cstring section")

    print(f"Found target string at address: 0x{target_address:x}")

    # 查找 __DATA 段
    data_segment = None
    for segment in binary.segments:
        if segment.name == "__DATA":
            data_segment = segment
            break

    if data_segment is None:
        raise ValueError("__DATA segment not found")

    # 查找 __cfstring 节
    cfstring_section = None
    for section in data_segment.sections:
        if section.name == "__cfstring":
            cfstring_section = section
            break

    if cfstring_section is None:
        raise ValueError("__cfstring section not found")

    # 获取 __cfstring 节的内容
    cfstring_data = cfstring_section.content

    cfstring_size = 32
    num_cfstrings = len(cfstring_data) // cfstring_size

    # 查找引用目标字符串的 CFString 结构体
    cfstring_address = None
    for i in range(num_cfstrings):
        offset = i * cfstring_size
        cfstring_entry = cfstring_data[offset:offset + cfstring_size]

        # 解析 data_ptr 字段
        data_ptr = int.from_bytes(cfstring_entry[16:24], byteorder='little')
        # print(f"{data_ptr}=====")
        # 检查 data_ptr 是否指向目标字符串的地址
        if data_ptr == target_address:
            cfstring_address = cfstring_section.virtual_address + offset
            file_addr = cfstring_address - segment.virtual_address + segment.file_offset
            print(f"Found CFString referencing target string at address: 0x{cfstring_address:x}")
            break

    if cfstring_address is None:
        raise ValueError(f"CFString referencing target string not found in __cfstring section")

    return file_addr


def find_time_scale_setter(macho_path, target_string):
    # 加载 Mach-O 文件
    binary = lief.parse(macho_path)
    if binary is None:
        raise ValueError("Failed to parse Mach-O file")

    # 查找 __TEXT 段
    text_segment = None
    for segment in binary.segments:

        if segment.name == "__TEXT":
            text_segment = segment

    if text_segment is None:
        raise ValueError("__TEXT segment not found")

    # 查找 __cstring 节
    cstring_section = None
    for section in text_segment.sections:
        if section.name == "__cstring":
            cstring_section = section
            break

    if cstring_section is None:
        raise ValueError("__cstring section not found")

    # 获取 __cstring 节的内容
    cstring_data = bytes(cstring_section.content)

    # 提取所有字符串
    strings = []
    current_string = ""
    for byte in cstring_data:
        if byte == 0:  # 字符串以 null 结尾
            if current_string:
                strings.append(current_string)
                current_string = ""
        else:
            current_string += chr(byte)
    # 查找目标字符串
    target_address = None

    # print(cstring_data)
    for idx, string in enumerate(strings):

        if target_string in string:
            # 计算目标字符串的地址
            target_address = cstring_section.virtual_address + cstring_data.find(string.encode('utf-8'))
            for section in binary.sections:
                # 获取段的内容
                data = section.content

                # 遍历段内容，查找引用
                for i in range(len(data) - 4):  # 假设地址是 4 字节
                    # 检查是否引用了目标字符串的地址
                    address = int.from_bytes(data[i:i + 4], byteorder="big")
                    if address == target_address:
                        print(f"在地址 0x{section.virtual_address + i:X} 引用了字符串 '{target_string}'。")
            return target_address

    if target_address is None:
        raise ValueError(f"Target string '{target_string}' not found in __cstring section")

    print(f"Found target string at address: 0x{target_address:x}")


def calculate_offset_and_difference(offset, subtract_value):
    """
    计算文件偏移量的整数部分和差值部分。

    :param offset: 文件偏移量（如 0xF59C18）
    :param subtract_value: 需要减去的值（如 0x2000）
    :return: (整数部分, 差值部分)
    """
    # 减去指定值
    new_offset = offset - subtract_value

    # 获取整数部分（向下取整到最接近的 0x1000 的倍数）
    integer_part = (new_offset // 0x1000) * 0x1000

    # 获取差值部分
    difference = new_offset - integer_part

    return integer_part, difference


def read_four_bytes_at_offset(file_path, offset):
    try:
        # 将十六进制字符串转换为整数
        if isinstance(offset, str):
            if offset.startswith("0x"):
                offset_int = int(offset, 16)
            else:
                raise ValueError("Offset must be a hexadecimal string starting with '0x'")
        else:
            offset_int = int(offset)

        # 打开文件并读取 4 个字节
        with open(file_path, 'rb') as file:
            file.seek(offset_int)  # 移动文件指针到指定偏移量
            four_bytes = file.read(4)  # 读取 4 个字节
            if len(four_bytes) < 4:
                raise ValueError(f"Failed to read 4 bytes at offset {offset}: File is too short")

            return four_bytes.hex()
    except Exception as e:
        raise ValueError(f"Failed to read 4 bytes at offset {offset}: {e}")
