# saltstack安装部署使用



2023.05.08测试可行

## 一、centos7安装saltstack

环境：centos7 x86_64

### 1、基础安装

安装saltstack存储库和密钥(master和minion节点)

```
yum install -y https://repo.saltstack.com/py3/redhat/salt-py3-repo-latest.el7.noarch.rpm
```



清楚失效缓存(master和minion节点)

```
yum clean expire-cache
```



### 2、安装master

```
[root@master ~]# yum -y install salt salt-cloud salt-master salt-minion salt-ssh salt-syndic salt-api

```



修改master配置

```
# 修改主控端的minion配置文件  修改 #id和#master:salt 这两行 (注意书写规范：每个冒号后面都要跟一个空格)
# #master:salt  指向管理端地址，这里是指向salt-master服务器，可以是IP、域名或主机名
# #id           minion主机标识必须唯一
[root@master ~]# sed -i 's/^#master: salt/master: 10.0.0.20/g' /etc/salt/minion   #注意master:后的空格
[root@master ~]# sed -n '/^master:/p'  /etc/salt/minion
master: 10.0.0.20
[root@master ~]# sed -i 's/^#id:/id: master/g'  /etc/salt/minion   #注意id:后的空格
[root@master ~]# sed -n '/^id:/p'  /etc/salt/minion
id: master

# 启动salt-master与salt-minion
[root@master ~]# systemctl enable --now salt-master
[root@master ~]# systemctl enable --now salt-minion

#4505和4506都是salt-master的端口号，4505是publish_port    4506是ret_port
[root@master ~]# netstat -tlnp
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name    
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      1024/sshd           
tcp        0      0 0.0.0.0:4505            0.0.0.0:*               LISTEN      1286/python3        
tcp        0      0 0.0.0.0:4506            0.0.0.0:*               LISTEN      1298/python3

```



### 3、安装minion

```
root@node1 ~]# yum install -y salt-minion
```

minion配置文件

```
[root@node1 ~]# sed -i 's/^#master: salt/master: 10.0.0.20/g' /etc/salt/minion   #注意master:后有空格
[root@node1 ~]# sed -n '/^master:/p'  /etc/salt/minion
master: 10.0.0.20
[root@node1 ~]# sed -i 's/^#id:/id: master/g'  /etc/salt/minion   #注意id:后的空格
[root@node1 ~]# sed -n '/^id:/p'  /etc/salt/minion
id: node1
# 启动salt-minion
[root@node1 ~]# systemctl enable --now salt-minion
[root@node1 ~]# systemctl status salt-minion
● salt-minion.service - The Salt Minion
   Loaded: loaded (/usr/lib/systemd/system/salt-minion.service; enabled; vendor preset: disabled)
   Active: active (running) since 三 2021-08-18 09:46:58 CST; 2h 5min ago

```













参考链接：

https://www.cnblogs.com/zxjcwang/p/14332941.html

https://zhuanlan.zhihu.com/p/433968130