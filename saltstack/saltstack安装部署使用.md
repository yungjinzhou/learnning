# saltstack安装部署使用



2023.05.08测试可行

## 一、centos7安装saltstack

环境：centos7 x86_64，对应aarch64架构，可以下载对应的key和repo，导入后安装使用

### 1、基础安装

安装saltstack存储库和密钥(master和minion节点)

```
sudo rpm --import https://repo.saltproject.io/salt/py3/redhat/7/x86_64/SALT-PROJECT-GPG-PUBKEY-2023.pub
curl -fsSL https://repo.saltproject.io/salt/py3/redhat/7/x86_64/latest.repo | sudo tee /etc/yum.repos.d/salt.repo
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



## 二、saltstack使用

### 1、Salt-key使用

```
# salt-key常用选项
    -L             列出所有公钥信息
    -a minion      接受指定minion等待认证的key
    -A             接受所有minion等待认证的key
    -r minion      拒绝指定minion等待认证的key
    -R             拒绝所有minion等待认证的key
    -f minion      显示指定key的指纹信息
    -F             显示所有key的指纹信息
    -d minion      删除指定minion的key
    -D             删除所有minion的key
    -y             自动回答yes

salt-key -L   # 列出所有keys
salt-key -y -A # 接受所有minion的新证书
salt-key -a  ‘minion’ # 接受指定的minion证书

```



### 2、cmd.run模块

```
# 万能模块cmd.run 执行命令
[root@master ~]# salt 'node1' cmd.run 'hostname'
```



### 3、test.ping模块

```
# 测试所有受控端主机是否存活
# '*'表示所有目标机器 test.ping 只是模块里的一个功能，用来测试连通性
[root@master ~]# salt "*" test.ping  
node1:
```



### 4、salt-run模块

```
# 3.常用命令
# salt-run
# 该命令执行runner(salt带的或者自定义的，runner以后会讲)，通常在master端执行，比如经常用到的manage
salt-run [options] [runner.func]
salt-run manage.status   ##查看所有minion状态
salt-run manage.down     ##查看所有没在线minion
salt-run manged.up       ##查看所有在线minion
```



### 5、pkg安装卸载

```
# 4 安装软件
salt 'node1' pkg.install httpd
# 卸载软件
salt 'node1' pkg.remove httpd
```



### 6、network网络测试

```
salt '*' test.echo 'hello'
salt '*' network.ping baidu.com        # 使用ping命令测试到某主机的连通性
salt '*' network.connect baidu.com 80  # #测试minion至某一台服务器的网络是否连通
salt '*' network.get_hostname  # 获取主机名
salt '*' network.active_tcp    # 返回所有活动的tcp连接
salt '*' network.ip_addrs      # 返回一个IPv4的地址列表
salt '*' network.get_fqdn       # 查看主机的fqdn(完全限定域名)
```



### 7、salt-call

```
# salt-call
# 该命令通常在minion上执行，minion自己执行可执行模块，不是通过master下发job
salt-call [options] <function> [arguments]
salt-call test.ping           ##自己执行test.ping命令
salt-call cmd.run 'ifconfig'  ##自己执行cmd.run函数


```



### 8、salt-cp

```
# salt-cp
# 分发文件到minion上,不支持目录分发，通常在master运行
salt-cp [options] '<target>' SOURCE DEST
salt-cp '*' testfile.html /tmp
salt-cp 'node*' /opt/index.html /tmp/a.html


```

### 9、service操作

```
salt '*' service.available sshd  # 查看ssh服务是否可达
salt '*' service.get_all         # 查看所有启动的服务
salt '*' service.status nginx    # 查看指定服务是否在线
```



### 10、state操作



state.sls SLS（代表SaLt State文件）是Salt State系统的核心。SLS描述了系统的目标状态，由格式简单的数据构成。这经常被称作配置管理。首先，在master上面定义salt的主目录，默认是在/srv/salt/下面。

```
salt '*' state.show_top          # 查看top_file情况
salt '*' state.single pkg.installed name=lsof  # 安装lsof


sls文件命名：
sls文件以”.sls”后缀结尾，但在调用时是不需要写后缀的。
使用子目录来做组织是个很好的选择。  
init.sls 在一个子目录里面表示引导文件，也就表示子目录本身， 所以``apache/init.sls`` 就是表示``apache``. 如果同时存在apache.sls 和 apache/init.sls，则 apache/init.sls 被忽略，apache.sls将被用来表示apache.
# 编辑master节点配置文件  vim  /etc/salt/master   
# 修改配置如下  注意空格缩进
file_roots:
  base:
    - /srv/salt
# 重启salt-master
systemctl restart salt-master

# 创建目录
mkdir -p /srv/salt

# cd /srv/salt/
```



### 11、sys模块操作

```
# 查看模块文档
salt '*' sys.doc pkg           #查看pkg模块文档 
```



### 12、更多模块参考

```
# salt内置的执行模块列表
http://docs.saltstack.cn/ref/modules/all/index.html
```







