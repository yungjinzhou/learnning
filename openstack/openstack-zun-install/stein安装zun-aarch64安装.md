## stein版本zun在centos7环境下的安装与配置

### 一、基本环境参数

- 环境：centos7.6   mimic版本
- opentack-zun版本stein
- python2.7.5/python3.6，都是系统自带python环境
- **默认zun数据库及zun服务密码 password: comleader123，可根据需要更改，在此环境下发现密码中有@需要修改pymysql源码进行处理，否则不能识别**
- 设计到密码及ip地址及hostname的及
- 如需docker磁盘功能，需要开启磁盘配额的功能

### 二、controller节点zun安装

#### 2.1 创建数据库

`mysql -uroot -pcomleader@123`

```
MariaDB [（none）] CREATE DATABASE zun;

MariaDB [(none)]> GRANT ALL PRIVILEGES ON zun.* TO 'zun'@'localhost' IDENTIFIED BY 'comleader123';

MariaDB [(none)]> GRANT ALL PRIVILEGES ON zun.* TO 'zun'@'%' IDENTIFIED BY 'comleader123';
```

#### 2.2 创建openstack用户、服务、端点

```

. admin-openrc

# 默认zun数据库及zun服务密码 password: comleader123，可根据需要更改

openstack user create --domain default --password-prompt zun

openstack role add --project service --user zun admin

openstack service create --name zun --description "Container Service" container

openstack endpoint create --region RegionOne container public http://controller:9517/v1

openstack endpoint create --region RegionOne container internal http://controller:9517/v1

openstack endpoint create --region RegionOne container admin http://controller:9517/v1

```



#### 2.3 安装、启动zun服务

##### 2.3.1 创建用户、组

```
groupadd --system zun
useradd --home-dir "/var/lib/zun" --create-home --system --shell /bin/false -g zun zun

```

##### 2.3.2 创建目录


```
mkdir -p /etc/zun
chown zun:zun /etc/zun

```

##### 2.3.3 安装zun

```


yum install epel-release python-pip git python-devel libffi-devel gcc openssl-devel -y
cd /var/lib/zun
git clone -b stable/stein https://git.openstack.org/openstack/zun.git
chown -R zun:zun zun
cd zun
pip install -r requirements.txt
python setup.py install


```



##### 2.3.4生成配置文件并配置

```
pip install PyYAML==5.4.1# 提示yaml有错误，安装该版本

su -s /bin/sh -c "oslo-config-generator --config-file etc/zun/zun-config-generator.conf" zun
su -s /bin/sh -c "cp etc/zun/zun.conf.sample /etc/zun/zun.conf" zun

```

 复制api-paste.ini配置文件

```
su -s /bin/sh -c "cp etc/zun/api-paste.ini /etc/zun" zun

```

编辑配置文件,在合适位置添加以下内容

sed -i.default -e "/^#/d" -e "/^$/d" /etc/zun/zun.conf



vim /etc/zun/zun.conf



```
[DEFAULT]
transport_url = rabbit://openstack:openstack@controller
[api]
host_ip = 192.168.204.173
port = 9517
[cinder_client]
[compute]
[cors]
[database]
connection = mysql+pymysql://zun:comleader123@controller/zun
[docker]
[etcd]
[glance]
[glance_client]
[keystone_auth]
memcached_servers = controller:11211
www_authenticate_uri = http://controller:5000
auth_url = http://controller:5000
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = zun
password = comleader123
auth_protocol = http
auth_version = v3
service_token_roles_required = True
endpoint_type = internalURL
[keystone_authtoken]
memcached_servers = controller:11211
www_authenticate_uri = http://controller:5000
auth_url = http://controller:5000
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = zun
password = comleader123
auth_protocol = http
auth_version = v3
service_token_roles_required = True
endpoint_type = internalURL

[network]
[neutron_client]
[oslo_concurrency]
lock_path = /var/lib/zun/tmp
[oslo_messaging_amqp]
[oslo_messaging_kafka]
[oslo_messaging_notifications]
driver = messaging
[oslo_messaging_rabbit]
[oslo_policy]
[pci]
[privsep]
[profiler]
[quota]
[scheduler]
[ssl]
[volume]
[websocket_proxy]
wsproxy_host = 192.168.204.173
wsproxy_port = 6784
base_url = ws://controller:6784
[zun_client]

```

##### 2.3.5 填充数据库

`su -s /bin/sh -c "zun-db-manage upgrade" zun`

##### 2.3.6 创建启动文件

vim /etc/systemd/system/zun-api.service



```
[Unit]
Description = OpenStack Container Service API

[Service]
ExecStart = /usr/bin/zun-api --config-file=/etc/zun/zun.conf --logfile=/var/log/zun/zun-api.log
User = zun

[Install]
WantedBy = multi-user.target
```



vim /etc/systemd/system/zun-wsproxy.service



```
[Unit]
Description = OpenStack Container Service Websocket Proxy

[Service]
ExecStart = /usr/bin/zun-wsproxy --config-file=/etc/zun/zun.conf --logfile=/var/log/zun/zun-wsproxy.log
User = zun

[Install]

WantedBy = multi-user.target

```

 创建目录  **mkdir /var/log/zun/**

更改权限 **chmod -R 777 /var/log/zun**

##### 2.3.7启动服务

先执行systemctl daemon-reload



```
systemctl enable zun-api  zun-wsproxy
systemctl start zun-api  zun-wsproxy
systemctl status zun-api  zun-wsproxy
```

如果启动报websocket或者selectors 报错

```
pip install docker==4.4.4
pip install websocket-client==0.32.0
pip install websocket==0.2.1

```

#### 2.4 etcd安装

```
yum install -y etcd

```



配置etcd

sed -i.default -e "/^#/d" -e "/^$/d" /etc/etcd/etcd.conf





```
#[Member]
ETCD_DATA_DIR="/var/lib/etcd/default.etcd"
ETCD_LISTEN_PEER_URLS="http://192.168.204.173:2380"
ETCD_LISTEN_CLIENT_URLS="http://192.168.204.173:2379"
ETCD_NAME="controller"
#[Clustering]
ETCD_INITIAL_ADVERTISE_PEER_URLS="http://192.168.204.173:2380"
ETCD_ADVERTISE_CLIENT_URLS="http://192.168.204.173:2379"
ETCD_INITIAL_CLUSTER="controller=http://192.168.204.173:2380"
ETCD_INITIAL_CLUSTER_TOKEN="etcd-cluster-01"
ETCD_INITIAL_CLUSTER_STATE="new"
```



启动

```
systemctl enable etcd
systemctl start etcd

```





### 三、计算节点zun安装

安装一点必备的依赖

```
# 以下是centos7安装方式，
yum install -y centos-release-openstack-stein
yum install -y python-openstackclient 

# neutron如果用的ovs，执行下面操作
yum install -y ebtables ipset
yum install -y openstack-neutron-openvswitch  
修改配置文件
安装依赖包
yum install libibverbs -y
yum install bridge-utils -y
systemctl start neutron-openvswitch-agent
systemctl enable neutron-openvswitch-agent

创建虚拟交换机（可不操作）
ovs-vsctl add-br br-provider
ovs-vsctl add-port br-provider ens36

# 后面kuryr会调用ovs-vsctl，赋予最大权限
chmod 777 /var/run/openvswitch/db.sock



# neutron如果用的linuxbridge，执行下面操作
yum install -y openstack-neutron-linuxbridge ebtables ipset  conntrack-tools bridge-utils
修改配置文件
启动代理
systemctl start neutron-linuxbridge-agent
systemctl enable neutron-linuxbridge-agent

```



安装后面步骤会用到的基础包

```
yum install -y epel-release yum-utils device-mapper-persistent-data lvm2 python-pip git python-devel libffi-devel gcc openssl-devel wget vim net-tools iscsi-initiator-utils nano
```

#### 3.1 时间同步

```
 1、安装软件包
yum install -y chrony

# 2、将时间同步服务器修改为controller节点
sed -i '/^server/d' /etc/chrony.conf 
sed -i '2aserver controller iburst' /etc/chrony.conf

# 3、启动 NTP 服务并将其配置为随系统启动
systemctl enable chronyd.service
systemctl start chronyd.service

# 4、设置时区
timedatectl set-timezone Asia/Shanghai

# 5、查看时间同步源
chronyc sources

# 6、查看时间是否正确
timedatectl status

```



#### 3.2 docker安装

参考链接：https://docs.docker.com/engine/install/ubuntu/

卸载旧版本的docker

> ```
> sudo apt-get remove docker docker-engine docker.io containerd runc
> 
> ```



配置仓库

```
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg lsb-release
    
```

Add Docker’s official GPG key:

```
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

```

Use the following command to set up the **stable** repository.

```
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```



查询docker版本

```
# 查看docker版本
apt-cache madison containerd
sudo apt-get update

# 安装 docker-ce、docker-ce-cli、containerd.io
apt install docker-ce=5:18.09.6~3-0~ubuntu-bionic
apt install docker-ce-cli=5:18.09.6~3-0~ubuntu-bionic
apt install containerd.io=1.3.9-1

```

启动服务

```
systemctl start docker containerd.service 
systemctl enable docker containerd.service
systemctl status docker containerd.service
```



添加内核配置参数

cat /etc/sysctl.conf



```
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
```

`sysctl -p`

 

#### 3.3 安装kuryr-libnetwork

##### 3.3.1 <font color=red>控制节点</font>

###### 3.3.1.1 创建kuryr用户

```
# comleader123
. admin-openrc
openstack user create --domain default --password-prompt kuryr

5.2 添加角色
openstack role add --project service --user kuryr admin

```



##### 3.3.2 计算节点

###### 3.3.2.1 创建用户

```
groupadd --system kuryr
useradd --home-dir "/var/lib/kuryr" --create-home --system --shell /bin/false -g kuryr kuryr

```

###### 3.3.2.2 创建目录

```
mkdir -p /etc/kuryr
chown kuryr:kuryr /etc/kuryr

```

###### 3.3.2.3 安装kuryr-libnetwork

```
cd /var/lib/kuryr
git clone -b stable/stein https://git.openstack.org/openstack/kuryr-libnetwork.git
chown -R kuryr:kuryr kuryr-libnetwork
cd kuryr-libnetwork

# yum install python3-pip git python3-devel libffi-devel gcc openssl-devel numactl -y

pip3 install --upgrade pip==21.3.1
pip3 install --upgrade setuptools==44.1.1
pip3 install -r requirements.txt
pip3 install -u pyrouter2==0.5.10
python3 setup.py install

```





###### 3.3.2.4 生成配置文件并配置

```
su -s /bin/sh -c "./tools/generate_config_file_samples.sh" kuryr

su -s /bin/sh -c "cp etc/kuryr.conf.sample /etc/kuryr/kuryr.conf" kuryr
```



编辑配置文件，添加以下内容

sed -i.default -e "/^#/d" -e "/^$/d" /etc/kuryr/kuryr.conf

vim /etc/kuryr/kuryr.conf



```
[DEFAULT]
# bindir = /usr/libexec/kuryr  # py2
bindir = /usr/local/libexec/kuryr  # py3
[binding]
[neutron]
www_authenticate_uri = http://controller:5000
auth_url = http://controller:5000
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = neutron
password = comleader@123
service_metadata_proxy = true
metadata_proxy_shared_secret = metadata_secret
#bility_scope = global
#process_external_connectivity = false

```



###### 3.3.2.5 创建启动文件

 vim /etc/systemd/system/kuryr-libnetwork.service



```
[Unit]
Description = Kuryr-libnetwork - Docker network plugin for Neutron

[Service]
ExecStart = /usr/bin/kuryr-server --config-file /etc/kuryr/kuryr.conf --log-file /var/log/kuryr/kuryr-server.log
# ExecStart = /usr/local/bin/kuryr-server --config-file /etc/kuryr/kuryr.conf --log-file /var/log/kuryr/kuryr-server.log 
CapabilityBoundingSet = CAP_NET_ADMIN

[Install]
WantedBy = multi-user.target

```

###### 3.3.2.6 启动服务

```
mkdir /var/log/kuryr/
chmod 777 /var/log/kuryr/
systemctl enable kuryr-libnetwork
systemctl start kuryr-libnetwork
systemctl restart docker
systemctl status docker kuryr-libnetwork

```

```
# python3安装方式，不用执行下面的操作
重新安装与配置linuxbridge
yum install -y openstack-neutron-linuxbridge ebtables ipset  conntrack-tools bridge-utils
修改配置文件
启动代理
systemctl start neutron-linuxbridge-agent
systemctl enable neutron-linuxbridge-agent
```





######  3.3.2.7 验证

 创建kuryr网络

```
docker network create --driver kuryr --ipam-driver kuryr --subnet 173.18.12.0/24 --gateway=173.18.12.1 test_net
```

有报错

```
Error response from daemon: This node is not a swarm manager. Use "docker swarm init" or "docker swarm join" to connect this node to swarm and try again.

```



查看网络

`docker network ls`

创建容器

`docker run --net test_net cirros /sbin/init`



#### 3.4 zun-compute服务安装与配置

##### 3.4.1 创建用户

```
groupadd --system zun
useradd --home-dir "/var/lib/zun" --create-home --system --shell /bin/false -g zun zun
```

##### 3.4.2 创建目录

```
mkdir -p /etc/zun
chown zun:zun /etc/zun
```



**下面安装py2、py3任选一种即可(建议用python3, 用py2可能导致安装kuryr的包变更导致kuryr网络有问题)**

##### 3.4.3 安装zun包依赖

python3版本

```
yum install python3-pip git python3-devel libffi-devel gcc openssl-devel numactl -y

```



##### 3.4.4 安装zun

```
cd /var/lib/zun
git clone -b stable/stein https://git.openstack.org/openstack/zun.git
chown -R zun:zun zun
cd zun


# python36安装
pip3 install --upgrade pip==21.3.1
pip3 install --upgrade setuptools==44.1.1
pip3 install -r requirements.txt
pip3 install websocket-client==1.2.3
pip3 install websockify==0.10.0
python3 setup.py install
```

##### 3.4.5 生成示例配置文件

```
su -s /bin/sh -c "oslo-config-generator --config-file etc/zun/zun-config-generator.conf" zun
su -s /bin/sh -c "cp etc/zun/zun.conf.sample /etc/zun/zun.conf" zun
su -s /bin/sh -c "cp etc/zun/rootwrap.conf /etc/zun/rootwrap.conf" zun
su -s /bin/sh -c "mkdir -p /etc/zun/rootwrap.d" zun
su -s /bin/sh -c "cp etc/zun/rootwrap.d/* /etc/zun/rootwrap.d/" zun

# su -s /bin/sh -c "cp etc/cni/net.d/* /etc/cni/net.d/" zun
```

##### 3.4.6 配置zun用户

```

python3
echo "zun ALL=(root) NOPASSWD: /usr/local/bin/zun-rootwrap /etc/zun/rootwrap.conf *" | sudo tee /etc/sudoers.d/zun-rootwrap
```



##### 3.4.7 编辑配置文件

vim /etc/zun/zun.conf

sed -i.default -e "/^$/d" -e "/^#/d" /etc/zun/zun.conf





```
[DEFAULT]

transport_url = rabbit://openstack:openstack@controller
state_path = /var/lib/zun

[database]
connection = mysql+pymysql://zun:comleader123@controller/zun

[keystone_auth]
memcached_servers = controller:11211
www_authenticate_uri = http://controller:5000
project_domain_name = default
project_name = service
user_domain_name = default
password = comleader123
username = zun
auth_url = http://controller:5000
auth_type = password
auth_version = v3
auth_protocol = http
service_token_roles_required = True
endpoint_type = internalURL

[keystone_authtoken]
memcached_servers = controller:11211
www_authenticate_uri= http://controller:5000
project_domain_name = default
project_name = service
user_domain_name = default
password = comleader123
username = zun
auth_url = http://controller:5000
auth_type = password

[websocket_proxy]
base_url = ws://controller:6784/
[oslo_concurrency]
lock_path = /var/lib/zun/tmp


[compute]
# If you want to run both containers and nova instances in this compute node, in the [compute] section, configure the host_shared_with_nova:
host_shared_with_nova = true
```



##### 3.4.8 配置docker和kuryr

###### 3.4.8.1 创建docker配置文件夹

```
mkdir -p /etc/systemd/system/docker.service.d
```

###### 3.4.8.2 创建docker配置文件

vim /etc/systemd/system/docker.service.d/docker.conf

**此处把zun:2375和controller:2379替换成对应的能解析到ip地址的host名称或者ip地址(比如zun2:2379, 1.1.1.1:2379)，group后根据前面配置的实际用户名修改**

```
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd --group zun -H tcp://zun:2375 -H unix:///var/run/docker.sock --cluster-store etcd://controller:2379
```

###### 3.4.8.3 重启docker

```
systemctl daemon-reload
systemctl restart docker
```

###### 3.4.8.4 编辑kuryr配置文件

vim  /etc/kuryr/kuryr.conf

可不修改改位置，测试修改后联网报错，如果没有报错，可以先不添加

```
[DEFAULT]
capability_scope = global
process_external_connectivity = False
```

优化kuryr创建网络时的等待时间（可不操作）

 ![img](H:\code\learnning\openstack-zun-install\企业微信截图_16390289337530.png) 

https://review.opendev.org/c/openstack/zun/+/679573/2/zun/network/kuryr_network.py

###### 3.4.8.5 重启kuryr

```
systemctl restart kuryr-libnetwork
```



##### 3.4.9 配置containerd

```
containerd config default > /etc/containerd/config.toml
```

 chown zun:zun /etc/containerd/config.toml 



```
[grpc]
  ...
  gid = ZUN_GROUP_ID
  
```

获取zun_group_id的方法如下

```
getent group zun | cut -d: -f3
```



```
systemctl restart containerd
```



##### 3.4.10 配置CNI（可选）

```
# mkdir -p /opt/cni/bin
# curl -L https://github.com/containernetworking/plugins/releases/download/v0.7.1/cni-plugins-amd64-v0.7.1.tgz \
      | tar -C /opt/cni/bin -xzvf - ./loopback
      
# install -o zun -m 0555 -D /usr/bin/zun-cni /opt/cni/bin/zun-cni


```



##### 3.4.11 创建启动文件

vim /etc/systemd/system/zun-compute.service



python3

```

[Unit]
Description = OpenStack Container Service Compute Agent

[Service]
ExecStart = /usr/local/bin/zun-compute --logfile /var/log/zun/zun-compute.log
User = zun

[Install]
WantedBy = multi-user.target

```

创建日志文件夹

```
mkdir /var/log/zun/
chown zun:zun /var/log/zun

```





##### 3.4.112 启动zun-compute

直接启动报错，需要安装

```
# python3
pip3 install pymysql==1.0.2
apt-get install -y numactl pciutils

```

同时修改

```

# python3
sed -i "s/with_lockmode('update')/with_for_update()/" /usr/local/lib/python3.6/dist-packages/zun/db/sqlalchemy/api.py
```







```
systemctl enable zun-compute
systemctl start zun-compute
systemctl status zun-compute
```





启动zun-cni-daemon(暂时不安装)

```
# systemctl enable zun-cni-daemon
# systemctl start zun-cni-daemon
# systemctl status zun-cni-daemon
```





##### 3.4.13 验证

控制节点

```
 pip install python-zunclient==3.3.0
 source /root/admin-openrc
 openstack appcontainer service list
```

##### 3.4.14 挂载卷权限修改

zun-compute挂载volume暂行方法

```
1. 安装
# yum install iscsi-initiator-utils -y
 apt-get install open-iscsi
2. 修改zun-compute.service ,更改User=root
3. 修改代码oslo_privsep/daemon.py (去掉sudo前缀)

            cmd = context.helper_command(sockpath)
            if "zun-rootwrap" in str(cmd) and "privsep-helper" in str(cmd):
                cmd = cmd[1:]
            LOG.info('Running privsep helper: %s', cmd)
4. 修改/etc/zun/rootwrap.conf，将/usr/local/bin/放在最前面
exec_dirs=/usr/local/bin/,/sbin,/usr/sbin,/bin,/usr/bin,/usr/local/sbin
```



尝试在非root情况下修改以下位置，没有成功

```

1. 修改/etc/sudoers.d/zun-rootwrap
[root@zun163 ~]# cat /etc/sudoers.d/zun-rootwrap 
zun ALL=(root) NOPASSWD: /usr/local/bin/zun-rootwrap /etc/zun/rootwrap.conf *
zun ALL=(root) NOPASSWD: /usr/local/bin/privsep-helper /etc/zun/rootwrap.conf *

2.修改代码
/etc/sudoers    zun ALL = (root) NOPASSWD: ALL
zun 
3.修改代码
vim zun/common/privileged.py
    capabilities=[c.CAP_SYS_ADMIN, c.CAP_DAC_READ_SEARCH],
4.修改配置文件zun.conf
[privsep]
#user = root
#helper_command = privsep-helper

```



##### 3.4.15 容器设置磁盘，做目录级别的磁盘配额功能

本地磁盘配额问题，导致设置disk大小后失败

```
（zun/container/docker/host.py）
mount |grep $(df /var/lib/docker |awk 'FNR==2 {print $1}') |grep -E 'pquota|prjquota'

解决办法
磁盘需要支持配额
https://blog.csdn.net/hanpengyu/article/details/7475645(vmware虚拟机添加磁盘)
https://www.cnblogs.com/yaokaka/p/14186153.html（目录级别磁盘配额）
```



**做支持目录级别的磁盘配额功能**

**docker images备份**

```
[root@node1 ~]# docker image save busybox > /tmp/busybox.tar
```

**第一步：添加一个新硬盘sdb**

```
[root@node1 ~]# fdisk -l

Disk /dev/sda: 21.5 GB, 21474836480 bytes, 41943040 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk label type: dos
Disk identifier: 0x0004ff38

   Device Boot      Start         End      Blocks   Id  System
/dev/sda1   *        2048     1026047      512000   83  Linux
/dev/sda2         1026048    41938943    20456448   83  Linux
/dev/sda3        41938944    41943039        2048   82  Linux swap / Solaris

Disk /dev/sdb: 21.5 GB, 21474836480 bytes, 41943040 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
```

**第二步：格式化硬盘为xfs文件系统格式**

```
[root@node1 ~]# mkfs.xfs -f /dev/sdb
meta-data=/dev/sdb               isize=512    agcount=4, agsize=1310720 blks
         =                       sectsz=512   attr=2, projid32bit=1
         =                       crc=1        finobt=0, sparse=0
data     =                       bsize=4096   blocks=5242880, imaxpct=25
         =                       sunit=0      swidth=0 blks
naming   =version 2              bsize=4096   ascii-ci=0 ftype=1
log      =internal log           bsize=4096   blocks=2560, version=2
         =                       sectsz=512   sunit=0 blks, lazy-count=1
realtime =none                   extsz=4096   blocks=0, rtextents=0
```

**第三步：创建data目录，后续将作为docker数据目录；**

```
[root@node1 ~]# mkdir /data/ -p
```

**第四步：挂载data目录，并且开启磁盘配额功能（默认xfs支持配额功能）**

```
[root@node1 ~]# mount -o uquota,prjquota /dev/sdb /data/
```

**第五步：查看配额-配置详情**

```
[root@node1 ~]# xfs_quota -x -c 'report' /data/
User quota on /data (/dev/sdb)
                               Blocks                     
User ID          Used       Soft       Hard    Warn/Grace     
---------- -------------------------------------------------- 
root                0          0          0     00 [--------]

Project quota on /data (/dev/sdb)
                               Blocks                     
Project ID       Used       Soft       Hard    Warn/Grace     
---------- -------------------------------------------------- 
#0                  0          0          0     00 [--------]
```

运行了xfs_quota这个命令后，显示如上，说明，/data/这个目录已经支持了目录配额功能

**第六步：从/data/docker/作软链接到/var/lib下**

把/var/lib目录下docker目录备份走，再重新做一个/data/docker的软连接到/var/lib下；

不支持目录级别的磁盘配额功能的源/var/lib/docker/目录移走，把支持目录级别的磁盘配额功能软链接到/data/docker/目录下的/var/lib/docker/目录

```
cd /var/lib
mv docker docker.bak
mkdir -p /data/docker
ln -s /data/docker/ /var/lib/
```

**第七步：重启docker服务**

```
systemctl restart docker 
```



### 四、zun-ui安装

https://docs.openstack.org/zun-ui/latest/install/index.html

horizon-dashboard安装配置

https://support.huaweicloud.com/dpmg-kunpengcpfs/kunpengopenstackstein_04_0015.html






