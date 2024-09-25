import random
import os

# 随机生成指定长度的数字
def generate_random_number(length: int) -> int:
    # 生成一个指定长度的随机数字
    if length <= 0:
        raise ValueError("Length must be a positive integer.")

    # 确保第一个数字不为0，防止数字长度变短
    first_digit = random.randint(1, 9)
    # 剩余的位数可以是0-9
    remaining_digits = [random.randint(0, 9) for _ in range(length - 1)]
    # 将数字列表转成字符串并拼接，最后转成int
    return int(str(first_digit) + ''.join(map(str, remaining_digits)))


def is_download_complete(path: str, file_name: str = None) -> bool:
    # 检查路径是否存在
    if not os.path.exists(path):
        raise ValueError("文件路径不存在")
    # 检查路径是文件夹还是文件
    if os.path.isfile(path):
        # 如果是文件，直接检查文件后缀
        return not file_name or not path.endswith('.tmp')
    elif os.path.isdir(path):
        # 如果是文件夹，遍历文件夹中的文件
        for file_name in os.listdir(path):
            if file_name.endswith('.tmp'):
                return False
        # 如果没有找到.tmp文件，且指定了文件名，检查该文件是否存在
        if file_name:
            return os.path.isfile(os.path.join(path, file_name))
        return True
    else:
        raise ValueError("非法文件")


def load_json(json_path, configReplace=None):
    with open(json_path, 'r', encoding='utf-8') as f:
        reqJsonRead = f.read()
        if configReplace:
            # 遍历字典中的键值对，将 {key} 替换为 value
            for key, value in configReplace.items():
                reqJsonRead = reqJsonRead.replace(f"{{{key}}}", f"{value}")
        jsonData = json.loads(reqJsonRead)
        return jsonData
