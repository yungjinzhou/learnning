## todo





### 本季度（第四季度）任务


- 调度器对左括号协程的处理（健康状态上报）
- 调度器多应用的支持（是否做）
- 调度器针对执行体宿主机异常宕机等情况，进行开发与优化
- 裁决日志负反馈（自学习后作用于左右括
- 对于一个应用多个容器的情况调研
- 
- 
- 



```
第四季度调度器组（杨金周、杨曦）的规划
超融合项目评审材料撰写、环境部署、验收等工作
长沙质控项目支持，容器云版本调度器与左右括号、应用联调、代码优化
调度器功能验证（异常调度、定时调度、执行体状态切换等）
调度器组件联动
4.1 调度器左括号联动，左括号联调，左括号分发控制、左括号健康状态控制
4.2 调度器右括号联动，
4.3 调度器执行体联动，保留脏执行体分析功能，执行体待清洗功能验证、执行体状态维护验证
4.4 调度器waf联动，配合 waf 对非正常情况下异常执行体进行清洗
4.5 调度器防火墙联动，配合防火墙接收异常消息，对异常可疑执行体进行清洗
4.6 调度器日志系统联动，
调度器优化
5.1 并发性能测试
5.2 策略开发与优化
5.3 异常情况下比如执行体宿主机异常对调度器各个服务以及应用的影响，开发与优化
5.4 白名单、黑名单功能开发
5.5 调度器对复杂应用的处理
鹤壁好差评服务项目支撑
```





### 本周任务

- 开发环境部署（执行体是什么，一个容器？一组容器？）
- 跟进超融合项目
- 调研调度器遇到多应用场景的方案(todo)
  - 方案一：根据应用启动多个scheduler容器，可行性调研中
  - - 配置文件yaml中增加appname字段
    - docker-compose的yaml文件中，针对每个应用，修改外部映射配置文件名称、位置和监听端口（如此会导致左右括号根据应用个数部署多个）
    - 代码中，修改相应的key(redis的key)，改动未知
  - 方案二：一个scheduler进程，管理多个应用，可行性调研中
  - - 代码改动量未知
    - 性能问题未测试
    - 
  - 方案三：监听是单独进程，每个应用占用一个进程进行处理，可行性调研中
  - - 代码改动量未知，
    - 开发难度未知，调研中
    - yaml文件和redis db如何拆分？
    - 
  - 方案四：插件化服务
  - 方案五：看左右括号针对多应用，如何处理
  - 
- 考虑调度器运行过程中，执行体宿主机宕机对调度器、服务的影响(doing)
- - 初始化过程中服务器宕机（处理优先级低）
  - 正常运行中时服务器宕机
  - - 宕机对在线执行体的影响(利用在线检查处理，但是会有异常执行体没有记录到数据库，需要手动删除)
    - 对备用执行体列表的影响及处理（清理掉所在异常宿主机的执行体信息）
    - 被初始化执行体列表的影响及处理（清理掉所在异常宿主机的执行体信息）
    - 对定时调度的影响（不做处理）
    - 对离线执行体的影响（将所在异常宿主机的执行体信息记录后，exec_id放入离线列表中）
    - 检测宿主机node服务
  - 考虑调度器运行过程中，redis服务异常对调度器的影响(todo)
  - 
- 联调环境，东区，东区调度器代码更新(todo)
- 存储在redis中的key，增加app_name (todo)
- 一个应用，多个部分，每个部分有镜像的问题（todo）
- 



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





### centos配置代理



```
export proxy="http://192.168.66.77:3128"
export http_proxy=$proxy
export https_proxy=$proxy
export ftp_proxy=$proxy
export no_proxy="localhost, 127.0.0.1, ::1"
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
```







```
ALTER USER 'root'@'localhost' IDENTIFIED BY 'mymysql';
flush privileges;

ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'mymysql';
flush privileges;

update mysql.user set host = '%',plugin='mysql_native_password' where user='root';
flush privileges;
```







项目进度

```
主题：超融合项目项目进展汇报

尊敬的校辉总，
   我想向您汇报一下我跟进的项目目前的进展情况。

1. 项目概述：
   超融合项目包含异构资源管理平台和网络加速平台两块内容，我们拆分成三个合同模块(裸金属管理组件、云原生管理组件和DPDK协议加速组件授权)，提供给余超，由余超撰写合同及后续跟供应商对接。
   现在项目处于项目交付、验收材料同时进行的状态。原定于9月15号完成验收材料，跟供应商公司多次沟通，供应商公司以没有签订合同为由，迟迟没有提供材料和软件环境，导致验收材料无法完成。本周三（9.20号）供应商跟山海源沟通，软件开发未完成，资料没有准备。
2. 已完成工作：
	 - 对提供的项目技术方案分析，拆分模块；（杨金周）
	 - 根据模块拆分功能点（杨金周、杨曦、桑帅东）
   - 完成供应商协调人对接，跟李总对接项目相关事宜。（杨金周）
3. 当前状态：
   - 跟供应商要签订的合同已提交高凌信息同事余超，由余超和供应商进行合同签订事宜，目前未完成合同签订；
   - 供应商软件处于开发中；
   - 验收所需资料供应商未提供（系统设计说明书、产品使用说明书、测试用例文档、测试报告、性能测试报告、源代码、安装包、其他相关软件包、部署文档、 授权情况）。
4. 下一步计划：
   - 催促对方尽快完成开发工作；
   - 催促同步进行资料撰写，及时发送给我们。
   - 立项准备
5. 问题和风险：
   - 对方估算开发时间是1个月，实际完成时间不可控。
如果您有任何问题或需要更多信息，请随时与我联系。感谢您对此进展汇报的关注，并期待您的反馈。

```





```
第三季度总结
研发方面：
1. 完成调度器方案设计及技术方案撰写
2. 完成调度器初版框架整体设计和初始化等开发任务，实现执行体应用安全平稳运行、实现节点资源合理利用，同时可以根据记录识别攻击，为分析潜在的漏洞及安全威胁提供数据支持
3. 实现调度器容器化，解决了环境依赖等问题，大大简化了部署步骤
4. 完成容器云版调度器设计与开发，解决由于执行体状态问题频繁调度导致的应用请求卡死等问题，同时解决环境依赖问题，简化部署
项目方面：
1. 长沙质控项目支持，使项目通过预言评审
2. 容器云环境部署，包括离线源、云平台以及质控项目的应用上云部署
3. 超融合项目功能点拆分、项目跟进；



第四季度规划
1. 超融合项目评审材料撰写、环境部署、验收等工作
2. 长沙质控项目支持，容器云版本调度器与左右括号、应用联调、代码优化
3. 调度器继续开发：
  - 对于一个应用多个容器的情况调研调度器如何兼容
  - 调度器针对执行体状态维护的处理
  - 调度器策略开发与优化
  - 调度器联调测试
  - 并发量等性能测试
  - 调度器针对执行体宿主机异常宕机等情况，进行开发与优化
  
  - 调度器对左括号协程的处理（健康状态上报）（需要讨论）
  - 调度器多应用的支持（是否做，需要讨论）
  - 执行体态势感知功能开发（需要讨论）
  - 订阅黑/白名单url消息（需要讨论）
  - 裁决日志负反馈（自学习后作用于左右括号，需要讨论）
  - 手动上下线功能（需要讨论）
  - 对于一个应用多个容器的情况调研（需要讨论）

```











