import os
import subprocess

from bypy import ByPy


# 百度云存放文件的文件夹名
# dir_name = "ByPy-test"

# 获取一个bypy对象，封装了所有百度云文件操作的方法
# bp = ByPy()
# 百度网盘创建远程文件夹bypy-test
# bp.mkdir(remotepath = dir_name)


# 函数作用：文件中的 \ 改为 /
# 函数输入：文件绝对路径
# 输出：文件绝对路径添加转义符后的结果
def changePath(filePath):
    path = ""
    for i in range(len(filePath)):
        if filePath[i] != "\\":
            path += filePath[i]
        else:
            path += "/"
    return path


# 获取文件的大小,结果保留两位小数，单位为MB
def get_FileSize(filePath):
    fsize = os.path.getsize(filePath)
    fsize = fsize / float(1024 * 1024)
    return round(fsize, 2)


class Pan():
    def __init__(self):
        self.bp = ByPy()
        pass

    @staticmethod
    def execBypy(cmd) -> list:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, encoding="utf-8")

        # 获取命令行的输出
        output = result.stdout

        # 分行处理输出结果
        lines = output.split('\n')

        # 从后往前遍历，直到遇到以'<W>'开头的行
        collecting = True
        content = []
        for line in reversed(lines):
            if collecting:
                if line.startswith('<W>'):
                    collecting = False
                elif line:
                    content.append(line)

        # 反转收集到的内容
        content.reverse()
        return content

    @staticmethod
    def wapperExecBypy(cmd):
        bypyRes = Pan.execBypy(cmd)
        # print(bypyRes)
        if bypyRes[len(bypyRes) - 1].find("Error") != -1:
            return bypyRes, bypyRes[len(bypyRes) - 1].split("Error ")[1]
        else:
            return bypyRes[1:], 0

    @staticmethod
    def list(dir):
        return Pan.wapperExecBypy(['bypy', 'list', dir, "$f"])

    @staticmethod
    def isExist(dir):
        list, ok = Pan.wapperExecBypy(['bypy', 'meta', dir])
        return len(list) == 1 and ok == 0

    # 调用函数
    def download(self, rp, lp):
        rp = changePath(rp)
        lp = changePath(lp)
        return self.bp.download(rp, lp)

    def upload(self, lp, rp):
        lp = changePath(lp)
        rp = changePath(rp)
        return self.bp.upload(lp, rp)

    def mkdir(self, dir):
        return self.bp.mkdir(dir)
