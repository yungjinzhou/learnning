## todo





### 本季度（第一季度）任务


- 调度器对左括号协程的处理（健康状态上报）

- 调度器多应用的支持（是否做）

- 裁决日志负反馈（自学习后作用于左右括

- 对于一个应用多个容器的情况调研

- <font color=red>跟进超融合项目</font>

- - 跟进进度
  - 审计材料撰写
  - 

- 调度器

- - <font color=red>清理执行体时会重置字段，放到待清洗执行体后，如何确定是哪个机器上的哪个容器（todo）清洗逻辑</font>
  - 存储在redis中的key，增加app_name (todo)
  - 调度器黑白名单设置
  - 调度器控制左、右括号状态、服务
- 待清洗列表开发测试
  - <font color=red>一个镜像，暴露多个端口，有多个服务的场景</font>
  - <font color=red>调度器dockerfile构建优化</font>
  - <font color=red>调度器基础镜像dockerfile构建优化</font>
  - <font color=red>调度器镜像构建脚本优化</font>
  - 调度器接口逻辑优化，下线逻辑优化
  - <font color=red>调度器日志配置优化，数据分离优化</font>
- <font color=red>日志结构优化，输出日志格式</font>
  
  - <font color=red>调研兼容性：运行执行体命令，可以调用虚拟机</font>
- 官网应用调试

- Kjb-门户

  - 设计方案文档修改
  - 假设方案文档修改
  - 公司环境调度器部署及调试
  - 现场环境调度器部署及调试
  - 执行体打包环境构建，安装镜像仓库，并编写执行体宿主机配置
  - x86平台和arm平台两种构建环境搭建，容器基础环境安装
  - 原应用后台管理部署
  - 原应用数据库部署
  - 原应用前台部署
  - 原应用同步服务部署
  - 原应用功能测试
  - 原应用使用文档撰写
  - 应用单执行体系统容器化，在容器中安装原应用，保证容器内应用功能和原应用功能正常
  - 原应用信息、组件容器化对接
  - 配合应用改造执行体及修改应用更新包
  - 每个http请求左括号分发2次裁决，文件hash裁决、网页内容分发裁决；
  - 获取执行体信息脚本适配；
  - 执行体上下线脚本适配；
  - 执行体下线适配
  - <font color=red>左括号订阅黑白名单功能</font>
  - <font color=red>右括号订阅黑白名单功能</font>
  - 左括号健康状态检查
  - 调度器随机模式裁决策略适配
  - 调度器随机模式裁决策略测试
  - 调度器适配镜像安全度裁决策略测试
    调度器适配镜像安全度裁决策略适配
  - <font color=red>调度器权重模式裁决策略适配及测试</font>
  - <font color=red>调度器置信度模式裁决策略适配及测试</font>
  - 18个异构执行体构建dockerfiel编写
  - 适配web服务器和不同的操作系统进行异构
  - 适配不同的java版本和不同的web服务进行异构
    编写镜像更新脚本 
  - "1.编写自动化构建基础操作系统脚本
  - 2.编写自动化构建基础运行环境脚本
  - 3.编写自动构建应用执行体和更新、运行。脚本"
  - "1.执行体打包后上传到镜像仓库，完成版本更新，
  - 2.编写执行体运行脚本和命令，指明端口和映射文件"
  - https协议适配
  - 左括号对接日志组件调试
  - 左括号-调度器对接任务
  - 左括号性能优化(静态文件缓存、图片缓存）
  - 数据缓存与传输压缩加速功能调试
  - 裁决异常发现、黑白名单管理
  - 裁决上报接口适配&调度轮换清洗调试
  - <font color=red>裁决执行体清洗逻辑优化（一次三个还是一次1个）</font>
  - <font color=red>故障转移优化，平均分配，快速分配</font>
  - 左括号对接调度器健康状态检查
  - 左括号对接Waf防火墙
  - 左括号裁决上报接口联调
  - 调度器和左括号联动
  - 调度器和右括号联动
  - 调度器执行体+右括号放行联动
  - 裁决器+proxy调试及问题修改
  - 数据库jdbc+agent+proxy+执行体联调
  - 索引引擎lucene+agent+proxy+执行体联调
  - httpclient+agent+proxy+执行体联调
  - smtp邮件协议+agent+proxy+执行体联调
  - memcachedclient数据缓存+agent+proxy+执行体联调
  - 邮件收发mailapi+agent+proxy+执行体联调
  - 功能自测（前台页面功能、通信协议版本、首页功能、文章栏目管理）
  - 自测文件同步功能
  - 自测：角色管理、用户管理功能、维护功能
  - 验证异构的18个执行体，每个执行体的功能
  - 

- 一键部署方案

- - 配置、远程修改，有很多重复的字段，如果要实现，需要修改代码及现有的配置结构，比如先统一录入数据库，然后各个组件统一从数据库获取
  - 不同应用，镜像不同，配置镜像的参数不同，打镜像等存在问题，无法一键实现部署
  - 统一组件容器化
  - 现在的配置文件，比如yaml，比如镜像信息都是有结构的，不是单一的比如cfg的配置文件格式，修改或者添加有困难
  - 组件安装，需要搭建离线源，内网环境， 离线源搭建（不同架构、不同系统的源），时间评估，如果现场部署，离线源如何带过去问题
  - 固定执行体-镜像个数（不同架构个数）、固定执行体宿主机个数、固定架构信息（）
  - 各个组件，单独部署时的详细部署方案
  - x86环境、arm环境，要求可以联网
  - 可以部署整个组件的环境，虚拟机
  - 基础环境，比如docker/配置文件/docker-compose/repo部署，安装，ssh环境安装，远程
  - 
  - 

- kjb-门户建设方案修改

- - 部署方案
  - 设计方案
  - 虚拟机：是否异构，系统、架构等
  - 源系统需要3个虚拟机，右括号、左括号、调度器、3执行体宿主机、后台管理系统、后台数据库服务、镜像仓库、日志系统。。。

- 

- 

  





### 本周任务

- kjb项目-构建调度器x86、arm镜像，提供部署文档

- 在windows上安装arm虚拟机(done)

- 在arm机器上构建调度器镜像及测试(done)

- 调度器相关立项资料撰写

- 

- kjb项目-调度器配置文件说明

- 加密部分资料

- 超融合异构内生安全支撑平台-数据平面加速平台测试方案修改

- 裁决异常后执行体清洗逻辑开发（是否保留异常执行体，保留个数，保留时长等处理）

- 调度器重置时执行体被清理的代码逻辑测试

- kjb项目-解决初始化过程中执行体一直异常的情况

- 定时监测任务间隔时长优化，可配置

- 调研缩小scheduler调度器的镜像大小，尝试使用alpine镜像，测试安装问题较多，且安装后镜像大小没有显著减少

- 更新调度器代码打包成镜像进行测试

- 当故常节点异常或者恢复时，是否处理执行体，记录执行体

- 

- 

  













### mysql操作

```
# mysql 备份、导出
/usr/bin/mysqldump -uroot -pmymysql -P 3306 -h 10.21.16.43 --database cookck > cookck.sql


# mysql 导入



# 构建镜像
docker rmi cookck/mysql:v20240204
docker build -t cookck/mysql:v20240204  .
```





### docker配置代理

```
docker服务配代理的方法，配上代理后就可以下载dockerhub镜像：
mkdir -p /etc/systemd/system/docker.service.d
cat >   /etc/systemd/system/docker.service.d/http-proxy.conf << eof
[Service]
Environment="HTTP_PROXY=192.168.66.77:3128"
Environment="HTTPS_PROXY=192.168.66.77:3128"
Environment="NO_PROXY=192.168.*.*,*.local,localhost,127.0.0.1"
eof

systemctl daemon-reload
systemctl restart docker
```



```
docker run -itd --name cookck -p 8089:8089 -p 8088:8088 cookck:v1 /bin/bash
```





#### dockerfile

```
FROM mysql:5.7
COPY cookck.sql /docker-entrypoint-initdb.d/cookck.sql
ENV MYSQL_ROOT_PASSWORD=mymysql  MYSQL_DATABASE=cookck
EXPOSE 3306
```







### centos配置代理



```
export proxy="http://192.168.66.77:3128"
export http_proxy=$proxy
export https_proxy=$proxy
export ftp_proxy=$proxy
export no_proxy="localhost, 127.0.0.1, ::1"
```





### 批量处理容器镜像



```
docker image list | grep menhu | grep 2024 | grep -v php | awk '{print $1}' | xargs -d  '-' | awk '{print $5}' | xargs -I {} echo 'docker image save -o '{}'.tar' > image.txt

docker image list | grep menhu | grep 2024 | grep -v php | awk '{print $1":"$2}' > target.txt

paste -d ' ' image.txt target.txt > result.txt

cat result.txt | while read LINE; do echo $LINE; eval $LINE; done
```









### 镜像制作，处理



```
执行
dd if=/dev/zero of=/home/junk_files
， 把剩余空间全部占满之后
执行
rm -f /home/junk_files

关机

# 压缩镜像
qemu-img convert -c -O qcow2 CentOS-7-x86_64-GenericCloud.qcow2 CentOS7v6.qcow2
```



#### 配置免密

```
 su nova -s /bin/bash -c "ssh-keygen -m PEM -t rsa -b 2048 -N '' -q -f /var/lib/nova/.ssh/id_rsa"
    log_info "Put nova's public key to controller and compute node"
    for node in `cat /etc/hosts | grep -E "controller|compute" | awk '{print $1}'`
    do
        su nova -s /usr/bin/expect -c "spawn ssh-copy-id root@$node
            expect {
                \"*yes/no\" { send \"yes\r\"; exp_continue }
                \"*password:\" { send \"comleader@123\r\" }
            }
            expect eof"
    done
```





### 修改qcow2镜像密码

```
virt-sysprep --root-password password:comleader@123 -a CentOS-7-x86_64-GenericCloud1.qcow2
```



### mac网卡增加ip地址

```
sudo ifconfig en5 inet 192.168.100.49 netmask 255.255.255.0 alias
```



### 定位网络问题的命令

```javascript
tracert ip
route -n
ip netns 
ip route
ip  a
brctl show
ovs-vsctl
bridge fdb # bridge fdb展示的是隧道信息
bridge fdb shwo dev vxlan-3
tcpdump -i eth0 -nnvvv
tcpdump -i dev icmp -nnvvv
vrish edit domain-id  # 查看虚拟机xml信息，有网卡信息
virsh dumpxml domain-id
```











### 临时







harbor登录

```
docker login 192.168.66.29:80 -u admin -p comleader@123


docker run -d --name registry-web --restart=always -p 8000:8080 
-v /root/docker-registry/registry-web.yml:/conf/config.yml 
hyper/docker-registry-web



docker run -d -p 3000:3000  -e OPENAI_API_KEY="sess-dvGHJ2GxYuSgNslbyhKKeQCz3MMaeWGvjAFdddda" -e CODE="123456"  yidadaa/chatgpt-next-web

```









