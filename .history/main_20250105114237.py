import os
import json
import threading
import traceback
from PIL import Image
import requests
import re
import sched
import time
import logging
from datetime import datetime

import bypy_tools
from cache_tools import FileCache

"""
@description 全局变量定义
"""
# 当前正在处理的任务ID
cur_task_id = ""
# 存储任务ID与对应文件夹名称的映射关系
task_folder = {}
# 存储任务ID与对应lora模型名称的映射关系
task_lora = {}
url = ""
cookie = ""
pan = bypy_tools.Pan()
finished_cache = None
download_cache = None

"""
@description 读取并解析JSON配置文件
@param {str} json_path - JSON文件路径
@param {dict} configReplace - 需要替换的配置键值对
@return {dict} 解析后的JSON数据
"""
def load_json(json_path, configReplace=None):
    with open(json_path, 'r', encoding='utf-8') as f:
        reqJsonRead = f.read()
        if configReplace:
            # 遍历字典中的键值对，将 {key} 替换为 value
            for key, value in configReplace.items():
                reqJsonRead = reqJsonRead.replace(f"{{{key}}}", f"{value}")
        jsonData = json.loads(reqJsonRead)
        return jsonData

"""
@description 获取指定文件夹中图片的最大分辨率
@param {str} folder_path - 文件夹路径
@return {tuple} 最大宽度和高度的元组
"""
def get_max_resolution(folder_path):
    max_width = 0
    max_height = 0
    max_resolution = (0, 0)  # (width, height)

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')):
            # 拼接完整的文件路径
            file_path = os.path.join(folder_path, filename)
            # 打开图片文件
            with Image.open(file_path) as img:
                # 获取图片的宽度和高度
                width, height = img.size
                # 检查是否是最大的分辨率
                if width * height > max_width * max_height:
                    max_width = width
                    max_height = height
                    max_resolution = (width, height)

    return max_resolution

"""
@description 获取文件夹中第一个txt文件的内容作为提示词
@param {str} folder_path - 文件夹路径
@return {str} 提示词文本内容
"""
def get_first_prompt(folder_path):
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            # 使用with语句打开文件，确保文件会被正确关闭
            with open(file_path, 'r', encoding='utf-8') as file:
                # 读取并返回文件内容
                return file.read()
    return ""

"""
@description 替换文件夹路径到模板中
@param {dict} request_json - 请求配置JSON对象
@param {str} folder_path - 文件夹路径
@param {str} folder_name - 文件夹名称
@return {dict} 替换后的请求配置JSON对象
"""
def replace_folder_in_request(request_json, folder_path, folder_name):
    repeat = 0
    epoch = 0
    width = 0
    height = 0
    first_prompt = ""
    print("folder_path", folder_path)
    print("folder_name", folder_name)
    for folder in os.listdir(folder_path):
        split = folder.split("_")
        if len(split) > 2:
            repeat = split[0]
            epoch = split[1]
            print("repeat", repeat)
            print("epoch", epoch)
            request_json['payload']['max_train_epochs'] = int(epoch)
        # 获取素材集中分辨率最大的
        resolution = get_max_resolution(os.path.join(folder_path, folder))
        # 获取素材集第一个提示词
        first_prompt = get_first_prompt(os.path.join(folder_path, folder))
        width, height = resolution
        print("最大分辨率：", width, height)
        break

    request_json['payload']['resolution'] = f"{width},{height}"
    request_json['payload']['train_data_dir'] = folder_path
    request_json['payload']['sample_prompts'].replace("{prompt}", f"{first_prompt}")
    request_json['payload']['output_name'] = folder_name
    request_json['payload']['output_dir'] = os.path.join("./output", folder_name)
    print("Lora输出路径", request_json['payload']['output_name'])
    return request_json

"""
@description 提交请求
@param {dict} request_json - 请求配置JSON对象
@return {dict} 响应数据
"""
def submit_request(request_json):
    try:
        url = request_json['url']
        headers = request_json['headers']
        payload = request_json['payload']
        response = requests.post(url, json=payload, headers=headers)
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

"""
@description 主程序：扫描目录、替换占位符、提交请求
@param {str} scan_dir - 需要扫描的目录
@param {str} request_json_path - 请求配置文件路径
"""
def submit_task(scan_dir, request_json_path):
    logging.info("=== 开始扫描新任务 ===")
    config = load_json("./config.json")
    request_json = load_json(request_json_path, config)
    finished_items = finished_cache.get_all_items()
    downloaded_items = download_cache.get_all_items()
    logging.info(f"当前已完成任务数: {len(finished_items)}")
    logging.info(f"当前已下载素材数: {len(downloaded_items)}")
    
    for folder in os.listdir(scan_dir):
        if finished_cache.has_item(folder):
            logging.debug(f"跳过已完成的任务: {folder}")
            continue
        if not download_cache.has_item(folder):
            logging.debug(f"跳过未下载完成的素材: {folder}")
            continue
            
        folder_path = os.path.join(scan_dir, folder)
        if os.path.isdir(folder_path):
            updated_template = replace_folder_in_request(request_json, folder_path, folder)
            logging.debug(f"提交配置：{json.dumps(updated_template, indent=2, ensure_ascii=False)}")
            response_data = submit_request(updated_template)
            if response_data and response_data['status'] == "success":
                task_id = get_task_id(response_data)
                global cur_task_id, task_folder
                cur_task_id = task_id
                task_folder[task_id] = folder
                task_lora[task_id] = os.path.join(config.get("lora_output_path"), folder)
                logging.info(f'任务提交成功 - 任务名称: "{folder}" - 任务ID: {task_id}')
                return
            else:
                finished_cache.add_item(folder, {
                    "lora_path": os.path.join(config.get("lora_output_path"), folder),
                    "task_id": task_id
                })
                logging.error(f"任务提交失败 - 文件夹: {folder_path}")

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
    config = load_json("./config.json")
    request_json = load_json("./request.json", config)
    # 获取任务请求结果列表
    task_map = get_task_map(request_json)
    return task_map

def current_task_finished():
    task_map = req_task_map()
    print("任务队列：", task_map)
    cur_task_status = task_map[cur_task_id]
    return cur_task_status == "FINISHED"

"""
@description 调度器主函数，负责任务的定期执行
@param {str} scan_dir - 需要扫描的目录
@param {str} request_json_path - 请求配置文件路径
@param {sched.scheduler} scheduler - 调度器实例
@param {dict} config - 配置信息
"""
def schedule_task(scan_dir, request_json_path, scheduler, config):
    try:
        scheduling(scan_dir, request_json_path)
    except Exception as e:
        print(f"任务调度异常: {e}")
        traceback.print_exc()

    interval = config["scheduling_minute"] * 60
    # 设置下一次执行的时间
    scheduler.enter(interval, 1, schedule_task, (scan_dir, request_json_path, scheduler, config))

"""
@description 下载任务的调度函数
@param {sched.scheduler} scheduler - 调度器实例
@param {dict} config - 配置信息
"""
def schedule_download_task(scheduler, config):
    try:
        download_job(config)
    except Exception as e:
        print(f"任务调度异常: {e}")
        # 打印完整的堆栈跟踪
        traceback.print_exc()

    interval = 60
    # 再次计划任务，每 60 s后执行
    scheduler.enter(interval, 1, schedule_download_task, (scheduler, config))

def download_job(config):
    logging.info("=== 检查新素材下载 ===")
    mark_dst_dir = config.get("source_dir")
    mark_src_dir = config.get("mark_pan_dir")
    downloaded_items = download_cache.get_all_items()
    logging.info(f"当前已下载素材数: {len(downloaded_items)}")
    
    pan_list, code = pan.list(mark_src_dir)
    if code == 0:
        logging.info(f"云盘待处理素材数: {len(pan_list)}")
        for dir_name in pan_list:
            if not download_cache.has_item(dir_name):
                logging.info(f"开始下载新素材: {dir_name}")
                success = pan.download(os.path.join(mark_src_dir, dir_name), os.path.join(mark_dst_dir, dir_name))
                if success == 0:
                    logging.info(f"素材下载成功 - {dir_name}")
                    download_cache.add_item(dir_name)
                else:
                    logging.error(f"素材下载失败 - {dir_name} - 错误码: {success}")
                break
    else:
        logging.error(f"获取云盘文件列表失败 - 错误码: {code}")

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
    loraUploadPath = config["lora_pan_upload_dir"] + "/" + os.path.basename(lora_path)
    if not pan.isExist(loraUploadPath):
        pan.mkdir(loraUploadPath)
    code = pan.upload(lora_path, loraUploadPath)
    if code != 0:
        print(f"lora:{lora_path}上传失败,code[{code}]")

"""
@description 调度器主函数，负责任务的定期执行
@param {str} scan_dir - 需要扫描的目录
@param {str} request_json_path - 请求配置文件路径
@param {sched.scheduler} scheduler - 调度器实例
@param {dict} config - 配置信息
"""
def scheduling(scan_dir, request_json_path):
    logging.info("=== 任务调度检查 ===")
    global cur_task_id, task_folder
    task_map = req_task_map()
    
    if task_map:
        logging.info("当前任务状态:")
        for taskid, state in task_map.items():
            logging.info(f"任务ID: {taskid} - 状态: {state}")
            if state == "RUNNING":
                logging.info(f"发现正在执行的任务，等待完成...")
                return

    if not cur_task_id:
        logging.info("没有进行中的任务，准备提交新任务...")
        submit_task(scan_dir, request_json_path)
    elif current_task_finished():
        folder = task_folder[cur_task_id]
        lora_path = task_lora[cur_task_id]
        logging.info(f"任务完成:")
        logging.info(f"- 文件夹: {folder}")
        logging.info(f"- Lora路径: {lora_path}")
        
        logging.info("开始上传Lora到云盘...")
        upload_lora(lora_path)
        finished_cache.add_item(folder, {
            "lora_path": lora_path,
            "task_id": cur_task_id
        })
        
        cur_task_id = ""
        logging.info("重置当前任务ID，准备提交新任务...")
        submit_task(scan_dir, request_json_path)

# 在文件开头添加日志配置
def setup_logging():
    """
    @description 配置日志系统
    """
    # 创建logs目录（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 生成日志文件名（使用当前日期）
    log_filename = f"logs/lora_training_{datetime.now().strftime('%Y%m%d')}.log"
    
    # 配置日志格式
    log_format = '%(asctime)s [%(levelname)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logging.info("=== 日志系统初始化完成 ===")

# 运行主程序
if __name__ == "__main__":
    try:
        # 初始化日志系统
        setup_logging()
        
        logging.info("=== Lora训练自动化系统启动 ===")
        # 初始化缓存对象
        finished_cache = FileCache("./finished_cache.json")
        download_cache = FileCache("./mark_folder_download.json")
        
        config = load_json("./config.json")
        scan_dir = config.get("source_dir")
        url = config.get("host")
        cookie = config.get("cookie")
        request_json_path = "./request.json"

        if scan_dir is None:
            print("错误: 未配置扫描文件夹路径")
        else:
            scheduler = sched.scheduler(time.time, time.sleep)
            scheduler2 = sched.scheduler(time.time, time.sleep)

            # 首次执行任务
            scheduler.enter(0, 1, schedule_task, (scan_dir, request_json_path, scheduler, config))
            scheduler2.enter(0, 1, schedule_download_task, (scheduler2, config))
            print("\n=== 系统初始化完成 ===")
            print("- Lora训练调度器已启动")
            print("- 素材下载调度器已启动")
            print("\n按 Ctrl+C 可以安全终止程序...")

            # 使用线程启动两个调度器
            t1 = threading.Thread(target=scheduler.run)
            t2 = threading.Thread(target=scheduler2.run)
            
            # 设置为守护线程，这样主线程结束时它们会自动终止
            t1.daemon = True
            t2.daemon = True
            
            t1.start()
            t2.start()
            
            # 保持主线程运行
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        logging.info("\n程序已终止")
        exit(0)
    except Exception as e:
        logging.exception("程序发生异常")
        exit(1)
