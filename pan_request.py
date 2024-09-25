import json

import requests
import util

class RequestHandler:
    def __init__(self):
        self.config = self.load_config()
        self.request_json = self.load_request_json()

    @staticmethod
    def load_config():
        return util.load_json("./config.json")

    @staticmethod
    def load_request_json():
        return util.load_json("./pan_request.json", RequestHandler.load_config())

    def dir_list(self, type_: str) -> dict:
        file_dict = {}
        config = self.config
        request_json = self.request_json
        # 下载路径指定为配置的云盘打标文件夹
        dir = config.get("mark_pan_dir")

        url = request_json.get("list_url") + dir
        headers = request_json['headers']
        response = requests.get(url, headers=headers)
        response_data = json.loads(response.text)

        if not response_data or response_data.get("code") != 0:
            print("云盘查询文件列表响应数据为空或无效")
            return file_dict

        # 获取文件列表
        file_list_data = response_data.get("data", {}).get("list", [])

        # 遍历文件列表，提取 fileName
        for file_info in file_list_data:
            file_name = file_info.get("fileName")
            if file_name:
                file_dict[file_name] = file_info.get("fileId")

        return file_dict

    def download(self, is_dir: bool, dst_path: str, src_path: str, file_id: str) -> bool:
        request_json = self.request_json
        url = request_json.get("download_url")
        payload = request_json.get("download_payload")
        headers = request_json['headers']
        payload["file_id"] = file_id
        payload["is_dir"] = is_dir
        payload["src_path"] = src_path
        payload["dstPath"] = dst_path
        response = requests.post(url, json=payload, headers=headers)
        print("百度云盘下载响应：", response.__dict__)
        response_data = json.loads(response.text)
        return response_data.get("code", "") == 0

    def upload(self, is_dir: bool, dst_path: str, src_path: str) -> bool:
        request_json = self.request_json
        url = request_json.get("upload_url")
        payload = request_json.get("upload_payload")
        headers = request_json['headers']
        payload["is_dir"] = is_dir
        payload["src_path"] = src_path
        payload["dstPath"] = dst_path
        response = requests.post(url, json=payload, headers=headers)
        print("百度云盘上传响应：", response.__dict__)
        response_data = json.loads(response.text)
        return response_data.get("code", "") == 0

