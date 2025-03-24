import json
import os
import subprocess
import SpeedUpUtils


def unity_get_addr(macho, unity_file, metadata_file):
    try:
        file_path = os.path.join('il2CppDumper', 'script.json')
        if os.path.exists(file_path):
            print("已经删除了script.json")
            os.remove(file_path)
        il2cpp_path = "./Il2CppDumper/Il2CppDumper"
        print(f"执行代码：{il2cpp_path} {unity_file} {metadata_file}")
        print("Current Working Directory:", os.getcwd())
        if not os.path.exists(metadata_file):
            raise FileNotFoundError(f"File not found: {metadata_file}")

        command = [il2cpp_path, unity_file, metadata_file, "./Unity_Output"]
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()

        # 检查返回码
        if process.returncode != 0:
            raise RuntimeError(f"Failed to run Il2CppDumper: {stderr}")
        else:
            print("==========开始处理json文件============")
            if os.path.exists(file_path):
                print("找到了script文件")
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                # 提取ScriptMethod中的Address和Name
                for method in data.get("ScriptMethod", []):
                    address = method.get("Address")
                    name = method.get("Name")
                    if name == "UnityEngine.Time$$set_timeScale":
                        print(f"Find Address: {address}")
                        # SpeedUpUtils.find_string_and_caller(unity_file, "Error decoding %@")
                        # target_address=SpeedUpUtils.find_time_scale_setter(unity_file,"UnityEngine.Time::set_timeScale")
                        return address, 0

            else:
                print(f"文件 {file_path} 不存在,需要联系技术处理")
                return 0, 0
    except subprocess.CalledProcessError as e:
        # 如果命令执行失败，抛出异常
        print(f"Failed to run Il2CppDumper: {e.stderr} ,需要人工处理")
        return 0, 0
    except Exception as e:
        print(f"An error occurred: {e},需要人工处理")
        return 0, 0
