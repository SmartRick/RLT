import os
import json
import subprocess

import bypy.const
import requests
from bypy import ByPy

import main


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




if __name__ == "__main__":
    # print()
    # meta = bp.list("/ByPy-test",fmt="$f")
    # 执行bypy list命令并捕获输出
    # exec_bypy = execBypy(['bypy', 'meta', "/ByPy-test/config.jsoan"])
    # ok = Pan.isExist("/ByPy-test/config.jsoan")
    # print(ok)
    lora = main.upload_lora('/root/lora-scripts/output/证件照')
    # print(lora)
    # prompt = main.get_first_prompt("G:/project/project/python/automatic-mark-comfyui/mark/证件照/15_证件照")
    # print(prompt)
    # mark_downloads = main.read_from_file_to_list("./mark_folder_download")
    # if "熊猫花花" not in mark_downloads:
    #     print("不在")
    # else:
    #     print("在")
