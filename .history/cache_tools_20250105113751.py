"""
@description 文件缓存工具类
"""
class FileCache:
    """
    @description 文件缓存类，用于管理 JSON 格式的缓存文件
    @param {str} cache_file_path - 缓存文件路径
    """
    def __init__(self, cache_file_path):
        self.cache_file_path = cache_file_path
        self._ensure_cache_file()
        self.cache_data = self._load_cache()

    """
    @description 确保缓存文件存在
    """
    def _ensure_cache_file(self):
        try:
            with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                pass
        except FileNotFoundError:
            with open(self.cache_file_path, 'w', encoding='utf-8') as f:
                f.write('{"items": []}')

    """
    @description 加载缓存文件内容
    @return {dict} 缓存数据
    """
    def _load_cache(self):
        with open(self.cache_file_path, 'r', encoding='utf-8') as f:
            try:
                return json.loads(f.read())
            except json.JSONDecodeError:
                return {"items": []}

    """
    @description 保存缓存数据到文件
    """
    def _save_cache(self):
        with open(self.cache_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.cache_data, f, ensure_ascii=False, indent=2)

    """
    @description 添加项目到缓存
    @param {str} item_name - 项目名称
    @param {dict} metadata - 相关元数据
    """
    def add_item(self, item_name, metadata=None):
        if not self.has_item(item_name):
            cache_item = {
                "name": item_name,
                "timestamp": time.time(),
                "metadata": metadata or {}
            }
            self.cache_data["items"].append(cache_item)
            self._save_cache()

    """
    @description 检查项目是否存在
    @param {str} item_name - 项目名称
    @return {bool} 是否存在
    """
    def has_item(self, item_name):
        return any(item["name"] == item_name for item in self.cache_data["items"])

    """
    @description 获取所有项目名称
    @return {list} 项目名称列表
    """
    def get_all_items(self):
        return [item["name"] for item in self.cache_data["items"]]

    """
    @description 获取项目的完整信息
    @param {str} item_name - 项目名称
    @return {dict|None} 项目信息
    """
    def get_item_info(self, item_name):
        for item in self.cache_data["items"]:
            if item["name"] == item_name:
                return item
        return None 