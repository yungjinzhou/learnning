## todo





### 本季度（第四季度）任务


- 调度器对左括号协程的处理（健康状态上报）
- 调度器多应用的支持（是否做）
- 调度器针对执行体宿主机异常宕机等情况，进行开发与优化
- 裁决日志负反馈（自学习后作用于左右括
- 对于一个应用多个容器的情况调研
- 





### 本周任务

- 跟进超融合项目
- - 
  - 
- 
- 调度器，清理执行体时会重置字段，放到待清洗执行体后，如何确定是哪个机器上的哪个容器（todo）
- 存储在redis中的key，增加app_name (todo)
- 官网应用调试
- 调度器黑白名单设置
- 一个镜像，暴露多个端口，有多个服务的场景
- 调研兼容性
- - 运行执行体命令
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







```
3、能够独立部署和集成深度学习算法、熟悉至少一种深度学习框架（如TensorFlow、PyTorch等）；
C++开发（Linux）


OpenCV,Pytorch;


pytorch机器学习框架
go语言 + k8s部署运维
java语言
c语言
c++语言


```





```
1. 调试科技部项目；
2. 调试调度脚本；
3. 超融合环境，应用环境配合调试；
4. 
```





```
docker run -d --name registry-web --restart=always -p 8000:8080 
-v /root/docker-registry/registry-web.yml:/conf/config.yml 
hyper/docker-registry-web
```

