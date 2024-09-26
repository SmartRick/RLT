import os
import json
import threading

import requests
import re
import sched
import time

import pan_request

# 当前任务id号
cur_task_id = ""
# 任务id-文件夹名称
task_folder = {}
# 任务id-lora名称
task_lora = {}
url = ""
cookie = ""

# 读取模板文件
def load_json(json_path,configReplace=None):
    with open(json_path, 'r', encoding='utf-8') as f:
        reqJsonRead = f.read()
        if configReplace:
            # 遍历字典中的键值对，将 {key} 替换为 value
            for key, value in configReplace.items():
                reqJsonRead = reqJsonRead.replace(f"{{{key}}}", f"{value}")
        jsonData = json.loads(reqJsonRead)
        return jsonData

# 替换文件夹路径到模板中
def replace_folder_in_request(request_json, folder_path, folder_name):
    repeat = 0
    epoch = 0
    width = 0
    height = 0
    for folder in os.listdir(folder_path):
        split = folder.split("_")
        repeat = split[0]
        epoch = split[1]
        width = split[2]
        height = split[3]
        # split__split = split[1].split(",")
        # epoch = split__split[0]
        # width = split__split[1]
        # height = split__split[2]
        break
    print("repeat",repeat)
    print("epoch",epoch)
    print("width",width)
    print("height",height)

    request_json['payload']['resolution'] = f"{width},{height}"
    request_json['payload']['max_train_epochs'] = int(epoch)

    request_json['payload']['train_data_dir'] = folder_path
    # request_json['payload']['train_data_dir'] = "./train/zbmt/月兔姑娘"
    request_json['payload']['output_name'] = folder_name + "_v1"
    return request_json

# 提交请求
def submit_request(request_json):
    try:
        url = request_json['url']
        headers = request_json['headers']
        payload = request_json['payload']
        print(f"payload: {payload}")
        response = requests.post(url, json=payload, headers=headers)
        print("响应：",response.__dict__)
        response_data = json.loads(response.text)
        status = response_data['status']
        # 输出状态码和返回内容，以便调试
        print(f"Status: {status}")
        print(f"Response message: {response_data['message']}")

        return response_data
    except Exception as e:
        # 输出异常信息，方便排查问题
        print(f"Error occurred: {e}")
        return False

# 主程序：扫描目录、替换占位符、提交请求
def submit_task(scan_dir, request_json_path):
    config = load_json("./config.json")
    request_json = load_json(request_json_path,config)
    finished_folder = read_from_file_to_list("./finished_cache")
    for folder in os.listdir(scan_dir):
        if folder in finished_folder:
            continue
        folder_path = os.path.join(scan_dir, folder)
        if os.path.isdir(folder_path):
            updated_template = replace_folder_in_request(request_json, folder_path, folder)
            response_data = submit_request(updated_template)
            if response_data:
                task_id = get_task_id(response_data)
                global cur_task_id, task_folder
                # 设置当前任务id
                cur_task_id = task_id
                # 设置全局的任务-文件夹
                task_folder[task_id] = folder
                task_lora[task_id] = config.get("lora_output_path") + updated_template.get("output_name") + "." + updated_template.get("save_model_as")
                print(f"任务提交成功，任务名称：“{folder}”，任务ID： {task_id}")
                return
            else:
                print(f"任务提交失败： {folder_path}")

def get_task_id(response_data):
    message = response_data['message']
    match = re.search(r'ID: ([a-f0-9-]+)', message)
    if match:
        return match.group(1)
    return None

def get_task_map(request_json):
    try:
        url = request_json['tasks_url']
        headers = request_json['headers']
        response = requests.get(url, headers=headers)

        response_data = json.loads(response.text)
        tasks = response_data['data']['tasks']
        result_map = {item['id']: item['status'] for item in tasks}
        return result_map
    except Exception as e:
        # 输出异常信息，方便排查问题
        print(f"Error occurred: {e}")
        return False

def req_task_map():
    global cur_task_id
    config = load_json("./config.json")
    request_json = load_json("./request.json",config)
    # 获取任务请求结果列表
    task_map = get_task_map(request_json)
    return task_map
def current_task_finished():
    task_map = req_task_map()
    print("任务队列：", task_map)
    cur_task_status = task_map[cur_task_id]
    return cur_task_status == "FINISHED"

def scheduling(scan_dir, request_json_path):
    global cur_task_id, task_folder
    task_map = req_task_map()
    for taskid,state in task_map.items():
        if state == "RUNNING":
            print(f"任务：{taskid}在执行中...")
            return

    if not cur_task_id:
        # 如果是第一次执行，直接提交任务
        submit_task(scan_dir, request_json_path)

    elif current_task_finished():
        # 获取完成任务的文件夹名称
        folder = task_folder[cur_task_id]
        # 获取完成任务的lora路径
        lora_path = task_lora[cur_task_id]
        # 任务完成，将文件夹名称写入完成文件缓存中
        write_to_file("./finished_cache", folder)
        # 上传lora到百度云盘中
        upload_lora(lora_path)
        # 再次请求提交新任务
        submit_task(scan_dir, request_json_path)

def write_to_file(file_path, text):
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(text + '\n')

def read_from_file_to_list(file_path):
    content_list = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            content_list.append(line.strip())
    return content_list

def upload_lora(lora_path):
    config = load_json("./config.json")
    pan_request_handler = pan_request.RequestHandler()
    result = pan_request_handler.upload(False, config.get("lora_pan_dst_dir"), lora_path)
    if not result:
        print(f"lora:{lora_path}上传失败")

def schedule_task(scan_dir, request_json_path, scheduler, config):
    try:
        scheduling(scan_dir, request_json_path)
    except Exception as e:
        print(f"任务调度异常: {e}")

    interval = config["scheduling_minute"] * 60
    # 再次计划任务，每 [scheduling_minute] 分钟后执行
    scheduler.enter(interval, 1, schedule_task, (scan_dir, request_json_path, scheduler, config))

def schedule_download_task(scheduler, config, pan_request_json):
    try:
        download_job(config)
    except Exception as e:
        print(f"任务调度异常: {e}")

    interval = 60
    # 再次计划任务，每 60 s后执行
    scheduler.enter(interval, 1, schedule_download_task, (scheduler, config, pan_request_json))

def download_job(config):
    mark_dst_dir = config.get("mark_dir")
    mark_src_dir = config.get("mark_pan_dir")
    download_mark_list = read_from_file_to_list("./mark_folder_download")
    pan_request_handle = pan_request.RequestHandler()
    # 扫描下载打标文件夹
    dir_dict = pan_request_handle.dir_list("mark")
    for dir_name, file_id in dir_dict:
        if dir_name not in download_mark_list:
            success = pan_request_handle.download(True, mark_dst_dir, mark_src_dir + "/" + dir_name, file_id)
            # 下载的素材文件夹名称·记录到缓存文件中
            write_to_file("./mark_folder_download", dir_name)
            if not success:
                print(f"{mark_src_dir + dir_name}下载失败")
            break

# 运行主程序
if __name__ == "__main__":
    config = load_json("./config.json")
    pan_request_json = load_json("./pan_request.json")
    scan_dir = config.get("source_dir")
    url = config.get("host")
    cookie = config.get("cookie")
    request_json_path = "./request.json"

    finished_cache_path = "./finished_cache"
    mark_folder_download = "./mark_folder_download"
    # 检查 finished_cache 文件是否存在，不存在则创建一个空文件
    if not os.path.exists(finished_cache_path):
        with open(finished_cache_path, 'w', encoding='utf-8') as f:
            pass
    if not os.path.exists(mark_folder_download):
        with open(mark_folder_download, 'w', encoding='utf-8') as f:
            pass

    if scan_dir is None:
        print("Error: 未配置扫描文件夹路径")
    else:
        scheduler = sched.scheduler(time.time, time.sleep)
        # 首次执行任务
        scheduler.enter(0, 1, schedule_task, (scan_dir, request_json_path, scheduler, config))
        print("启动完成")

        scheduler2 = sched.scheduler(time.time, time.sleep)
        # 首次执行任务
        scheduler2.enter(0, 1, schedule_download_task, (scheduler2, config, pan_request_json))
        print("下载调度器启动完成")

        # 使用线程启动两个调度器
        threading.Thread(target=scheduler.run).start()
        threading.Thread(target=scheduler2.run).start()

