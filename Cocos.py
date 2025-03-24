import time
import SpeedUpUtils

cocos_hex_str1 = '22 08 20 1E 03 10 2E 1E'
cocos_hex_str2 = '28 08 20 1E  14 14 40 F9'
revive_hex_str1 = 'FF 83 01 d1'
revive_hex_str1 = 'FF c3 01 d1'


def cocos_modify(file_path,modify_address):
    text = "===== 开始进入 cocos 判断 ====="
    cocos_set = 0
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.05)  # 控制打印速度
    print()  # 换行
    update_offset1 = SpeedUpUtils.find_hex_offset(file_path, cocos_hex_str1)
    update_offset2 = SpeedUpUtils.find_hex_offset(file_path, cocos_hex_str2)
    if (update_offset1 is None and update_offset2 is None) or (
            update_offset1 is not None and update_offset2 is not None):
        update_offset = None
    else:
        update_offset = update_offset1 if update_offset1 is not None else update_offset2
        cocos_set = 40 if update_offset1 is not None else 44
    if update_offset is None:
        print("人工判断了,请联系技术处理")
        return 0, 0
    else:
        real_update_address = update_offset - cocos_set
        real_update_address_hex = hex(update_offset - cocos_set)
        jumpAddress = hex(real_update_address - int(modify_address, 16))
        backAddress_nohex=real_update_address + 4 - 8208
        backAddress = hex(real_update_address + 4 - 8208)
        print(
            f"找到地址Cocos加速Update特征地址：{hex(update_offset)},向上偏移{hex(cocos_set)},找到真实加速地址为{real_update_address_hex},返回的地址为{backAddress}")
        save_arm = SpeedUpUtils.read_four_bytes_at_offset(file_path, real_update_address_hex)
        print(f"保存当前加速hex码{save_arm}成功")
        assembly_code = f"B -{jumpAddress}"
        arm_code = SpeedUpUtils.assemble_to_hex(assembly_code)
        print(f"汇编代码是{assembly_code}")
        print(f"hex是{arm_code}")
        if SpeedUpUtils.write_value_to_offset(file_path, real_update_address, arm_code):
            print("修改汇编代码成功")

        cfString_addr = SpeedUpUtils.find_string_and_caller(file_path, "Error setting audio session active")
        print(f"获取到修改的cfString_addr为{cfString_addr}")
        cfs_integer, cfs_offset = SpeedUpUtils.calculate_offset_and_difference(cfString_addr, 0x2000)
        arm_modify = SpeedUpUtils.assemble_to_hex(f"adrp x16,#0x{cfs_integer:x}") + SpeedUpUtils.assemble_to_hex(
            f"ldr x16, [x16, #0x{cfs_offset:x}]") + SpeedUpUtils.assemble_to_hex(
            "br x16") + save_arm + SpeedUpUtils.assemble_to_hex(f"b #{backAddress}")
        print(arm_modify)
        if SpeedUpUtils.write_value_to_offset(file_path, 0x2000, arm_modify):
            print("修改0x2000汇编代码成功")
        return cfString_addr,backAddress_nohex