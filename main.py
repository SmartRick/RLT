import os
import json
import requests

# 读取模板文件
def load_json(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        jsonData = json.load(f)
        print(jsonData)
        return jsonData

# 替换文件夹路径到模板中
def replace_folder_in_request(request_json, folder_path, folder_name):
    # request_json['payload']['train_data_dir'] = folder_path
    request_json['payload']['train_data_dir'] = "./train/zbmt/月兔姑娘"
    request_json['payload']['output_name'] = folder_name + "_v1"
    return request_json

# 提交请求
def submit_request(request_json):
    try:
        url = request_json['url']
        headers = request_json['headers']
        payload = request_json['payload']  # 修改 body 为 payload
        response = requests.post(url, json=payload, headers=headers)

        response_data = json.loads(response.text)
        status = response_data['status']
        # 输出状态码和返回内容，以便调试
        print(f"Status: {status}")
        print(f"Response message: {response_data['message']}")

        return status == "success"
    except Exception as e:
        # 输出异常信息，方便排查问题
        print(f"Error occurred: {e}")
        return False

# 主程序：扫描目录、替换占位符、提交请求
def main(scan_dir, request_json_path):
    request_json = load_json(request_json_path)

    for folder in os.listdir(scan_dir):
        folder_path = os.path.join(scan_dir, folder)
        if os.path.isdir(folder_path):
            updated_template = replace_folder_in_request(request_json, folder_path, folder)
            success = submit_request(updated_template)
            if success:
                print(f"任务提交成功： {folder_path}")
            else:
                print(f"任务提交失败： {folder_path}")

# 运行主程序
if __name__ == "__main__":
    config = load_json("./config.json")
    scan_dir = config["source_dir"]
    request_json_path = "./request.json"
    main(scan_dir, request_json_path)

