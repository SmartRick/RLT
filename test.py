def read_log_file(file_path):
    encodings = ['utf-8', 'gbk', 'iso-8859-1']  # 可能的编码列表
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
                # 检查是否能够正确解码
                if content:
                    print(f"成功使用 {encoding} 编码读取日志")
                    return content
        except UnicodeDecodeError:
            continue
    print("未能使用常见编码读取日志")
    return None

def read_log_file(file_path):
    try:
        with open(file_path, 'r', encoding='iso-8859-1') as file:
            content = file.read()
            print(content)  # 输出到控制台
            return content
    except UnicodeDecodeError:
        print("解码错误，尝试其他编码方式")
        return None
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None

# 调用函数
if __name__ == "__main__":
    read_log_file('./events.out.tfevents.1725977962.instance.8097.0')
