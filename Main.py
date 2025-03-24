import argparse
import glob
import shutil
import zipfile
import json
import os
import Cocos
import Unity
import SpeedUpUtils

"""
解压 IPA 文件到指定目录
"""


def extract_ipa(ipa_path, output_dir):
    if not os.path.isfile(ipa_path):
        raise FileNotFoundError(f"IPA 文件不存在: {ipa_path}")
    os.makedirs(output_dir, exist_ok=True)
    try:
        with zipfile.ZipFile(ipa_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        print(f"✅ 解压成功！文件已保存至: {os.path.abspath(output_dir)}")
        filenames, source_path = get_filenames_in_payload_subdir()
        if filenames is not None:
            expected_header = b'\xCF\xFA\xED\xFE\x0C\x00\x00\x01'
            for file_path in filenames:

                print(f"文件路径是{file_path}")
                try:
                    with open(file_path, 'rb') as file:  # 以二进制模式打开文件
                        file_header = file.read(8)  # 读取前八个字节
                        if file_header == expected_header:
                            print(f"mother fucking file is {file_path}")
                            return file_path, source_path
                except Exception as e:
                    print(f"读取文件失败: {e}")

    except zipfile.BadZipFile:
        raise ValueError("无效的 ZIP 文件，请确认输入文件是合法的 IPA 文件")


def get_filenames_in_payload_subdir():
    # 定义目标路径
    target_path = "./output/Payload/*/"  # 匹配任意名字的文件夹

    # 获取所有符合条件的目录
    subdirs = glob.glob(target_path)

    # 如果没有找到符合条件的目录
    if not subdirs:
        print("未找到符合条件的目录")
        return []
    print(f"在目录{subdirs[0]}下的文件")
    # 遍历所有符合条件的目录，获取文件名
    filenames = []
    # for subdir in subdirs:
    #     for root, dirs, files in os.walk(subdir):
    #         filenames.extend(files)
    #         print(f"在目录 '{root}' 中找到文件: {files}")
    for file in get_files_in_current_dir(subdirs[0]):
        filenames.append(subdirs[0] + file)
    return filenames, subdirs[0]


def get_files_in_current_dir(directory):
    # 获取当前目录下的所有文件和文件夹
    items = os.listdir(directory)
    # 过滤出文件
    files = [item for item in items if os.path.isfile(os.path.join(directory, item))]
    return files


def clear_output(directory):
    # 检查目录是否存在
    if not os.path.exists(directory):
        print(f"目录 '{directory}' 不存在")
        return

    # 遍历目录并删除所有内容
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)  # 删除文件或符号链接
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # 删除子目录
            print(f"已删除: {item_path}")
        except Exception as e:
            print(f"删除 {item_path} 失败: {e}")


def main():
    engine_name = ""
    Speedup_Address = ""
    Jump_Address = ""
    parser = argparse.ArgumentParser(
        description='IPA 文件解压工具',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'ipa_file',
        help='需要解压的 IPA 文件路径\n示例: /path/to/app.ipa'
    )
    # parser.add_argument(
    #     '-o', '--output',
    #     default='./ipa_extracted',
    #     help='输出目录 (默认: ./ipa_extracted)'
    # )

    args = parser.parse_args()

    try:
        machofile, resource_file = extract_ipa(args.ipa_file, "./output")
        print(f"需要修改的mach-o文件路径是{machofile}")
        if ((SpeedUpUtils.find_hex_offset(machofile, Cocos.cocos_hex_str1) is not None) or (
                SpeedUpUtils.find_hex_offset(machofile, Cocos.cocos_hex_str2) is not None)):
            engine_name = "cocos"
            print("=========检测到该游戏是Cocos游戏===========")
            Speedup_Address,Jump_Address=Cocos.cocos_modify(machofile)
        elif (os.path.isfile(f"{resource_file}FrameWorks/UnityFramework.framework/UnityFramework")):
            print("=========检测到该游戏是Unity游戏===========")
            engine_name = "unity"
            Speedup_Address, Jump_Address= Unity.unity_get_addr(machofile, f"{resource_file}FrameWorks/UnityFramework.framework/UnityFramework",
                                 f"{resource_file}Data/Managed/Metadata/global-metadata.dat")
        elif (SpeedUpUtils.find_string_offset(machofile, "webView:didFinishNavigation") is not None):
            engine_name = "web"
            Speedup_Address, Jump_Address=0,0
            print("=======检测到该游戏是Web游戏=============")
        else:
            print("其他引擎,人工处理")

        # 输出的参数输出成json
        print("开始输出成json格式")
        data = {
            "engine": engine_name,
            "Speedup_Address": Speedup_Address,
            "Jump_Address": Jump_Address
        }
        with open('result.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"{data}已经成功生成到当前json格式下")
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        # exit(1)


if __name__ == '__main__':
    clear_output("./output")
    main()
