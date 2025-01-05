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
from task_queue import TaskQueue, TaskStatus

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
task_queue = None

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
    
    # 扫描并添加新任务到队列
    for folder in os.listdir(scan_dir):
        if finished_cache.has_item(folder):
            logging.debug(f"跳过已完成的任务: {folder}")
            continue
        if not download_cache.has_item(folder):
            logging.debug(f"跳过未下载完成的素材: {folder}")
            continue
            
        folder_path = os.path.join(scan_dir, folder)
        if os.path.isdir(folder_path):
            # 将任务信息添加到队列
            task_info = {
                "folder_name": folder,
                "folder_path": folder_path,
                "status": "pending"
            }
            task_queue.add_task(task_info)
            logging.info(f"已将任务添加到队列 - {folder}")
    
    # 尝试提交下一个任务
    submit_next_task(request_json)

def submit_next_task(request_json):
    """
    @description 提交队列中的下一个任务
    @param {dict} request_json - 请求配置JSON对象
    @return {bool} 是否成功提交任务
    """
    next_task = task_queue.peek_next_task()
    if not next_task:
        logging.info("任务队列为空")
        return False

    folder = next_task["folder_name"]
    folder_path = next_task["folder_path"]
    
    try:
        config = load_json("./config.json")
        updated_template = replace_folder_in_request(request_json, folder_path, folder)
        logging.debug(f"提交配置：{json.dumps(updated_template, indent=2, ensure_ascii=False)}")
        
        response_data = submit_request(updated_template)
        if response_data and response_data['status'] == "success":
            task_id = get_task_id(response_data)
            if not task_id:
                raise Exception("无法获取任务ID")
                
            global cur_task_id, task_folder
            cur_task_id = task_id
            task_folder[task_id] = folder
            task_lora[task_id] = os.path.join(config.get("lora_output_path"), folder)
            
            # 更新任务状态并移除
            task_queue.update_task_status(folder, "running")
            task_queue.get_next_task()
            
            logging.info(f'任务提交成功 - 任务名称: "{folder}" - 任务ID: {task_id}')
            return True
        else:
            raise Exception(f"API返回错误: {response_data.get('message', '未知错误')}")
            
    except Exception as e:
        logging.error(f"任务提交失败 - 文件夹: {folder_path} - 错误: {str(e)}")
        task_queue.update_task_status(folder, "failed")
        return False

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
    try:
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
            
            try:
                logging.info("开始上传Lora到云盘...")
                upload_lora(lora_path)
                finished_cache.add_item(folder, {
                    "lora_path": lora_path,
                    "task_id": cur_task_id
                })
                
                cur_task_id = ""
                logging.info("重置当前任务ID，准备提交新任务...")
                config = load_json("./config.json")
                request_json = load_json(request_json_path, config)
                submit_next_task(request_json)
            except Exception as e:
                logging.error(f"处理完成任务时发生错误: {str(e)}")
                
    except Exception as e:
        logging.error(f"调度过程发生错误: {str(e)}")

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

class LoraTrainingSystem:
    """
    @description Lora训练系统管理器
    """
    def __init__(self, config_path="./config.json"):
        """
        @description 初始化系统
        @param {str} config_path - 配置文件路径
        """
        self.config = load_json(config_path)
        self.request_json_path = "./request.json"
        
        # 初始化组件
        self.finished_cache = FileCache("./finished_cache.json")
        self.download_cache = FileCache("./mark_folder_download.json")
        self.task_queue = TaskQueue()
        self.pan = bypy_tools.Pan()
        
        # 当前任务状态
        self.cur_task_id = ""
        self.task_folder = {}
        self.task_lora = {}

    def initialize(self):
        """
        @description 初始化系统
        """
        # 设置日志配置
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        logging.info("=== Lora训练自动化系统启动 ===")
        
        # 检查必要的配置
        if not self.config.get("source_dir"):
            raise ValueError("错误: 未配置扫描文件夹路径")
            
        self._start_schedulers()

    def _start_schedulers(self):
        """
        @description 启动调度器
        """
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.download_scheduler = sched.scheduler(time.time, time.sleep)

        # 配置调度任务
        self.scheduler.enter(0, 1, self._schedule_training_task, ())
        self.download_scheduler.enter(0, 1, self._schedule_download_task, ())
        
        # 启动调度器线程
        for scheduler, name in [(self.scheduler, "训练调度器"), 
                              (self.download_scheduler, "下载调度器")]:
            thread = threading.Thread(target=scheduler.run, name=name)
            thread.daemon = True
            thread.start()
            logging.info(f"- {name}已启动")
            
    def _schedule_training_task(self):
        """
        @description 训练任务调度循环
        """
        try:
            self._process_training_tasks()
        except Exception as e:
            logging.error(f"训练任务调度异常: {e}")
            logging.exception(e)
            
        # 设置下一次执行
        interval = self.config["scheduling_minute"] * 60
        self.scheduler.enter(interval, 1, self._schedule_training_task, ())
        
    def _schedule_download_task(self):
        """
        @description 下载任务调度循环
        """
        try:
            self._process_downloads()
        except Exception as e:
            logging.error(f"下载任务调度异常: {e}")
            logging.exception(e)
            
        self.download_scheduler.enter(60, 1, self._schedule_download_task, ())

    def _process_training_tasks(self):
        """
        @description 处理训练任务
        """
        logging.info("=== 任务调度检查 ===")
        task_map = self._get_task_map()
        
        if task_map:
            self._log_current_tasks(task_map)
            if self._has_running_task(task_map):
                return

        if not self.cur_task_id:
            logging.info("没有进行中的任务，扫描新任务...")
            self._scan_and_submit_tasks()
        elif self._is_current_task_finished(task_map):
            self._handle_finished_task()
            
    def _process_downloads(self):
        """
        @description 处理下载任务
        """
        logging.info("=== 检查新素材下载 ===")
        mark_src_dir = self.config.get("mark_pan_dir")
        mark_dst_dir = self.config.get("source_dir")
        
        # 获取云盘文件列表
        pan_list, code = self.pan.list(mark_src_dir)
        if code != 0:
            logging.error(f"获取云盘文件列表失败 - 错误码: {code}")
            return
            
        # 打印云盘文件列表
        logging.info(f"云盘文件列表 ({len(pan_list)} 个文件):")
        for idx, dir_name in enumerate(pan_list, 1):
            logging.info(f"  {idx}. {dir_name}")
            
        # 添加新的下载任务
        for dir_name in pan_list:
            # 检查是否已完成或已在队列中
            if not self.finished_cache.has_item(dir_name) and not self.task_queue.get_task_by_folder(dir_name):
                src_path = os.path.join(mark_src_dir, dir_name)
                self.task_queue.add_download_task(dir_name, src_path)
        
        # 处理下载任务
        downloading_tasks = self.task_queue.get_tasks_by_status(TaskStatus.DOWNLOADING)
        logging.info(f"当前下载任务数: {len(downloading_tasks)}")
        
        for task in downloading_tasks:
            folder_name = task["folder_name"]
            src_path = task["src_path"]
            dst_path = os.path.join(mark_dst_dir, folder_name)
            
            try:
                logging.info(f"开始下载素材: {folder_name}")
                success = self.pan.download(src_path, dst_path)
                
                if success == 0:
                    logging.info(f"素材下载成功 - {folder_name}")
                    self.task_queue.mark_download_complete(folder_name, dst_path)
                    # 下载完成后添加到下载缓存
                    self.download_cache.add_item(folder_name)
                else:
                    error_msg = f"下载失败 - 错误码: {success}"
                    self.task_queue.mark_download_failed(folder_name, error_msg)
                
            except Exception as e:
                error_msg = f"下载异常: {str(e)}"
                logging.error(f"素材下载失败 - {folder_name} - {error_msg}")
                self.task_queue.mark_download_failed(folder_name, error_msg)
            
            # 每次只处理一个下载任务
            break

    def _submit_task(self, folder, folder_path):
        """
        @description 提交单个训练任务
        """
        request_json = load_json(self.request_json_path, self.config)
        try:
            updated_template = replace_folder_in_request(request_json, folder_path, folder)
            response_data = submit_request(updated_template)
            
            if not response_data or response_data['status'] != "success":
                raise Exception(f"API返回错误: {response_data.get('message', '未知错误')}")
                
            task_id = self._extract_task_id(response_data)
            self._register_task(task_id, folder)
            return True
            
        except Exception as e:
            logging.error(f"任务提交失败 - 文件夹: {folder_path} - 错误: {str(e)}")
            self.task_queue.update_task_status(folder, "failed")
            return False

    def _log_current_tasks(self, task_map):
        """
        @description 记录当前任务状态
        """
        logging.info("当前任务状态:")
        for taskid, state in task_map.items():
            logging.info(f"任务ID: {taskid} - 状态: {state}")
            
    def _has_running_task(self, task_map):
        """
        @description 检查是否有正在运行的任务
        """
        for state in task_map.values():
            if state == "RUNNING":
                logging.info("发现正在执行的任务，等待完成...")
                return True
        return False
        
    def _register_task(self, task_id, folder):
        """
        @description 注册新任务
        """
        self.cur_task_id = task_id
        self.task_folder[task_id] = folder
        self.task_lora[task_id] = os.path.join(self.config.get("lora_output_path"), folder)
        logging.info(f'任务注册成功 - 任务名称: "{folder}" - 任务ID: {task_id}')
        
    def _handle_finished_task(self):
        """
        @description 处理已完成的任务
        """
        folder = self.task_folder[self.cur_task_id]
        lora_path = self.task_lora[self.cur_task_id]
        
        try:
            logging.info(f"任务完成: {folder}")
            logging.info(f"开始上传Lora到云盘: {lora_path}")
            
            self._upload_lora(lora_path)
            self._mark_task_finished(folder, self.cur_task_id, lora_path)
            
            self.cur_task_id = ""
            self._scan_and_submit_tasks()
            
        except Exception as e:
            logging.error(f"处理完成任务时发生错误: {str(e)}")

    def _process_download_list(self, pan_list, mark_src_dir, mark_dst_dir):
        """
        @description 处理下载列表
        @param {list} pan_list - 云盘文件列表
        @param {str} mark_src_dir - 云盘源目录
        @param {str} mark_dst_dir - 本地目标目录
        """
        logging.info(f"云盘待处理素材数: {len(pan_list)}")
        for dir_name in pan_list:
            if not self.download_cache.has_item(dir_name):
                logging.info(f"开始下载新素材: {dir_name}")
                success = self.pan.download(
                    os.path.join(mark_src_dir, dir_name), 
                    os.path.join(mark_dst_dir, dir_name)
                )
                if success == 0:
                    logging.info(f"素材下载成功 - {dir_name}")
                    self.download_cache.add_item(dir_name)
                else:
                    logging.error(f"素材下载失败 - {dir_name} - 错误码: {success}")
                break

    def _get_task_map(self):
        """
        @description 获取任务状态映射
        @return {dict} 任务ID到状态的映射
        """
        request_json = load_json(self.request_json_path, self.config)
        try:
            url = request_json['tasks_url']
            headers = request_json['headers']
            response = requests.get(url, headers=headers)
            response_data = json.loads(response.text)
            tasks = response_data['data']['tasks']
            return {item['id']: item['status'] for item in tasks}
        except Exception as e:
            logging.error(f"获取任务状态失败: {e}")
            return {}

    def _is_current_task_finished(self, task_map):
        """
        @description 检查当前任务是否完成
        @param {dict} task_map - 任务状态映射
        @return {bool} 是否完成
        """
        if not self.cur_task_id or self.cur_task_id not in task_map:
            return False
        return task_map[self.cur_task_id] == "FINISHED"

    def _scan_and_submit_tasks(self):
        """
        @description 扫描并提交新任务
        """
        logging.info("=== 开始扫描新任务 ===")
        finished_items = self.finished_cache.get_all_items()
        
        # 获取待训练的任务（下载完成的任务）
        pending_tasks = self.task_queue.get_tasks_by_status(TaskStatus.PENDING)
        
        logging.info(f"当前已完成任务数: {len(finished_items)}")
        logging.info(f"当前待训练任务数: {len(pending_tasks)}")
        
        # 如果有待训练的任务，尝试提交训练
        if pending_tasks:
            self._submit_next_task()

    def _submit_next_task(self):
        """
        @description 提交队列中的下一个待训练任务
        @return {bool} 是否成功提交任务
        """
        next_task = self.task_queue.get_next_pending_task()  # 获取下一个待训练任务
        if not next_task:
            logging.info("没有待训练的任务")
            return False

        folder = next_task["folder_name"]
        folder_path = next_task["folder_path"]
        
        try:
            request_json = load_json(self.request_json_path, self.config)
            updated_template = replace_folder_in_request(request_json, folder_path, folder)
            response_data = submit_request(updated_template)
            
            if not response_data or response_data['status'] != "success":
                error_msg = response_data.get('message', '未知错误') if response_data else "API请求失败"
                self.task_queue.mark_training_failed(folder, error_msg)
                return False
                
            task_id = self._extract_task_id(response_data)
            if not task_id:
                self.task_queue.mark_training_failed(folder, "无法获取任务ID")
                return False
            
            # 注册任务并更新状态
            self._register_task(task_id, folder)
            self.task_queue.mark_training_start(folder, task_id)
            self.task_queue.get_next_task()  # 从队列中移除任务
            
            logging.info(f'任务提交成功 - 任务名称: "{folder}" - 任务ID: {task_id}')
            return True
            
        except Exception as e:
            error_msg = f"任务提交失败: {str(e)}"
            logging.error(f"{error_msg} - 文件夹: {folder_path}")
            self.task_queue.mark_training_failed(folder, error_msg)
            return False

    def _extract_task_id(self, response_data):
        """
        @description 从响应数据中提取任务ID
        @param {dict} response_data - API响应数据
        @return {str|None} 任务ID或None
        """
        message = response_data['message']
        match = re.search(r'ID: ([a-f0-9-]+)', message)
        return match.group(1) if match else None

    def _upload_lora(self, lora_path):
        """
        @description 上传Lora模型到云盘
        @param {str} lora_path - Lora模型路径
        """
        upload_path = os.path.join(
            self.config["lora_pan_upload_dir"],
            os.path.basename(lora_path)
        )
        if not self.pan.isExist(upload_path):
            self.pan.mkdir(upload_path)
        
        code = self.pan.upload(lora_path, upload_path)
        if code != 0:
            raise Exception(f"Lora上传失败 - 路径: {lora_path} - 错误码: {code}")

    def _mark_task_finished(self, folder, task_id, lora_path):
        """
        @description 标记任务为已完成
        @param {str} folder - 文件夹名称
        @param {str} task_id - 任务ID
        @param {str} lora_path - Lora模型路径
        """
        self.finished_cache.add_item(folder, {
            "lora_path": lora_path,
            "task_id": task_id
        })

# 运行主程序
if __name__ == "__main__":
    try:
        system = LoraTrainingSystem()
        system.initialize()
        
        logging.info("\n=== 系统初始化完成 ===")
        logging.info("按 Ctrl+C 可以安全终止程序...")
        
        # 保持主线程运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logging.info("\n程序已终止")
        exit(0)
    except Exception as e:
        logging.exception("程序启动失败")
        exit(1)
