import os
import json
import requests

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


# 调用函数
if __name__ == "__main__":
    print()