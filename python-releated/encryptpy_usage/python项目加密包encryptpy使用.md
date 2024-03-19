环境要求：

python3.8以上，基于fedora32上用调度器项目代码进行测试

```
docker pull fedora:32
docker run -itd --name test fedora:32 /bin/bash
docker cp scheduler.tar.gz test:/home/
docker exec -it test /bin/bash
yum install python3-pip  gcc  python3-devel git -y
mkdir  /home/test
cp scheduelr.tar.gz /home/test/
cd /home/test/
tar -zxvf scheduler.tar.gz
```







*scheduler_start.py 改为schedulerStart.py*

基础环境包安装

```
pip3.8 install encryptpy -i http://mirrors.aliyun.com/pypi/simple/ --extra-index-url https://pypi.python.org/simple --trusted-host mirrors.aliyun.com

```



创建目录

```
假设项目代码目录为scheduler
则目录结构为：
/home/test/scheduler/
/home/test/.encryptpy.cfg
```

.encryptpy.cfg具体内容如下

```
[encryptpy]
; 将被编译的文件
paths =
    scheduler
; 编译时忽略的文件，支持正则
ignores =
    schedulerStart.py
; 用于子命令`init`, 拷贝项目时会忽略的文件，Glob风格
copy_ignores =
    *.pyc
    *.md
    *.txt
; The build directory
build_dir = build
; 用于子命令`run` and `git-diff`, 编译后是否移除源.py文件
clean_py = 0

```



执行命令

```
encryptpy clean  #   会删除__pychache__目录和旧的build目录
encryptpy init .  #  执行生成二进制文件

```

