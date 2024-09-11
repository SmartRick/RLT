# 运行命令：
nohup python main.py > output.log 2>&1 &

# 查看日志：
tail -500f output.log

# finished_cache
finished_cache里面存放的是已经训练完的资源文件夹，如果是第一次运行脚本清空里面的内容或者直接删除该文件

# config.json
config.json存放的是配置文件，需要根据自己的需求进行修改配置
![img.png](img.png)
如我这里放了两个需要训练的资源文件夹，就指定到它的上级就行了
![img_1.png](img_1.png)
![img_2.png](img_2.png)

# request.json
请求参数，其他内容都不需要关注
将**payload**部分通过配置文件toml译成json即可
将**header**部分的Cookie部分建议换成实际请求里的，推测不同容器里面的token不一样，混入了容器id

**ps: 我未对比过json是否和toml完全一致，为了确定稳定性建议直接复制请求接口里的请求体内容**

