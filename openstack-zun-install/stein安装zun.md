## zun安装与配置

环境：centos7

opentack-zun版本stein

python2.7.5



### controller节点

#### 创建数据库

`mysql -uroot -pcomleader@123`

```
MariaDB [（none）] CREATE DATABASE zun;

MariaDB [(none)]> GRANT ALL PRIVILEGES ON zun.* TO 'zun'@'localhost' IDENTIFIED BY 'comleader123';

MariaDB [(none)]> GRANT ALL PRIVILEGES ON zun.* TO 'zun'@'%' IDENTIFIED BY 'comleader123';
```



#### 创建openstack用户、服务、端点



```
# . admin-openrc
# password: comleader123

# openstack user create --domain default --password-prompt zun

# openstack role add --project service --user zun admin

openstack service create --name zun --description "Container Service" container

openstack endpoint create --region RegionOne container public http://controller:9517/v1

openstack endpoint create --region RegionOne container internal http://controller:9517/v1

openstack endpoint create --region RegionOne container admin http://controller:9517/v1

```





#### 安装、启动zun服务

3.1 创建用户、组



```
groupadd --system zun
useradd --home-dir "/var/lib/zun" --create-home --system --shell /bin/false -g zun zun
```



3.2 创建目录


```
mkdir -p /etc/zun
chown zun:zun /etc/zun
```





3.3 安装zun



```
yum install epel-release python-pip git python-devel libffi-devel gcc openssl-devel -y
cd /var/lib/zun
git clone -b stable/stein https://git.openstack.org/openstack/zun.git
chown -R zun:zun zun
cd zun
pip install -r requirements.txt
python setup.py install


```



3.4 生成示例配置文件

```
su -s /bin/sh -c "oslo-config-generator --config-file etc/zun/zun-config-generator.conf" zun

su -s /bin/sh -c "cp etc/zun/zun.conf.sample /etc/zun/zun.conf" zun
```



3.5 复制api-paste.ini配置文件

```
su -s /bin/sh -c "cp etc/zun/api-paste.ini /etc/zun" zun
```



3.6 编辑配置文件,在合适位置添加以下内容

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
iauth_version = v3
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
iauth_version = v3
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

3.7 填充数据库
`su -s /bin/sh -c "zun-db-manage upgrade" zun`

 

3.8 创建启动文件

vim /usr/lib/systemd/system/zun-api.service(暂时不用)

vim /etc/systemd/system/zun-api.service

```
[Unit]
Description = OpenStack Container Service API


[Service]
ExecStart = /usr/bin/zun-api
User = zun

[Install]
WantedBy = multi-user.target
```

vim /usr/lib/systemd/system/zun-wsproxy.service(暂时不用)

vim /etc/systemd/system/zun-wsproxy.service

```
[Unit]
Description = OpenStack Container Service Websocket Proxy

[Service]
ExecStart = /usr/bin/zun-wsproxy
User = zun

[Install]

WantedBy = multi-user.target

```





3.9 启动服务

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
pip install websocket
```



#### etcd安装

```
yum install -y etcd
```



配置etcd

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
# systemctl enable etcd
# systemctl start etcd
```







### 计算节点



> **在计算节点安装zun-compute服务前，需要在计算节点安装docker和kuryr-libnetwork**
> **在控制节点安装etcd**









时间同步

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







#### docker安装



卸载旧版本的docker

> ```
> yum remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine
> ```

### 

安装一点必备的依赖

```
yum -y upgrade # 只更新包，不更新内核和系统
```



`yum install -y epel-release yum-utils device-mapper-persistent-data lvm2 python-pip git python-devel libffi-devel gcc openssl-devel wget vim net-tools` 

配置仓库

`yum-config-manager --add-repo http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo`

好像最近的docker版本升级了，变成了20版本，然后kuryr就用不成了。之前用的19.03没问题，就换成这个，安装这个版本的。

查询docker版本

```
yum list containerd.io --showduplicates | sort -r
yum list docker-ce --showduplicates | sort -r
yum install docker-ce-<VERSION_STRING> docker-ce-cli-<VERSION_STRING> containerd.io
# for example docker-ce-18.09.1
```





通过本地包安装

```
wget https://download.docker.com/linux/centos/7/x86_64/stable/Packages/docker-ce-18.09.6-3.el7.x86_64.rpm
wget https://download.docker.com/linux/centos/7/x86_64/stable/Packages/docker-ce-cli-18.09.6-3.el7.x86_64.rpm
wget https://download.docker.com/linux/centos/7/x86_64/stable/Packages/containerd.io-1.3.9-3.1.el7.x86_64.rpm

yum localinstall  -y  docker-ce-cli-18.09.6-3.el7.x86_64.rpm
yum localinstall  -y  containerd.io-1.3.9-3.1.el7.x86_64.rpm
yum localinstall  -y  docker-ce-18.09.6-3.el7.x86_64.rpm
```

如果需要安装最新的版本，命令是 yum install -y docker-ce docker-ce-cli containerd.io

启动服务，自启动

```
systemctl start docker containerd.service 
systemctl enable docker containerd.service
```



4.7 添加内核配置参数

cat /etc/sysctl.conf

```
net.bridge.bridge-nf-call-ip6tables = 1

net.bridge.bridge-nf-call-iptables = 1

net.ipv4.ip_forward = 1
```



​	`sysctl –p`

 



#### 安装kuryr-libnetwork

##### 控制节点

5 在controller节点上添加kuryr-libnetwork用户
5.1 创建kuryr用户

```
# . admin-openrc

# comleader123
# openstack user create --domain default --password-prompt kuryr

5.2 添加角色
# openstack role add --project service --user kuryr admin

```



##### 计算节点

6 在compute节点安装kuryr-libnetwork
6.1 创建用户



```
# groupadd --system kuryr

# useradd --home-dir "/var/lib/kuryr" --create-home --system --shell /bin/false -g kuryr kuryr

```





6.2 创建目录



```
# mkdir -p /etc/kuryr

# chown kuryr:kuryr /etc/kuryr

```





6.3 安装kuryr-libnetwork



```
yum install epel-release python-pip git python-devel libffi-devel gcc openssl-devel -y

# cd /var/lib/kuryr

# git clone -b stable/stein https://git.openstack.org/openstack/kuryr-libnetwork.git

# chown -R kuryr:kuryr kuryr-libnetwork

# cd kuryr-libnetwork


# 直接执行pip install --upgrade pip，如果报错，可能是py2.7版本问题，通过下面途径更新pip
wget https://bootstrap.pypa.io/pip/2.7/get-pip.py
sudo python get-pip.py
更新setuptools
pip install --upgrade setuptools

# 提示自带的python-ipaddress版本太旧(1.0.6)，pip直接安装失败
wget https://cbs.centos.org/kojifiles/packages/python-ipaddress/1.0.18/5.el7/noarch/python2-ipaddress-1.0.18-5.el7.noarch.rpm
yum install -y python2-ipaddress-1.0.18-5.el7.noarch.rpm

pip install pyroute2==0.5.10

# pip install -r requirements.txt
# python setup.py install
```









6.4 生成示例配置文件

```
# su -s /bin/sh -c "./tools/generate_config_file_samples.sh" kuryr

# su -s /bin/sh -c "cp etc/kuryr.conf.sample /etc/kuryr/kuryr.conf" kuryr
```





6.5 编辑配置文件，添加以下内容

vim /etc/kuryr/kuryr.conf

```
[DEFAULT]
bindir = /usr/libexec/kuryr
[binding]
[neutron]
www_authenticate_uri = http://controller:5000/v3
auth_url = http://controller:5000/v3
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = kuryr
password = comleader123

```



6.6 创建启动文件
 vim /etc/systemd/system/kuryr-libnetwork.service

```
[Unit]
Description = Kuryr-libnetwork - Docker network plugin for Neutron

[Service]
ExecStart = /usr/bin/kuryr-server --config-file /etc/kuryr/kuryr.conf
CapabilityBoundingSet = CAP_NET_ADMIN

[Install]
WantedBy = multi-user.target

```


6.7 启动服务

```
systemctl enable kuryr-libnetwork
systemctl start kuryr-libnetwork
systemctl restart docker
```



6.8 验证
6.8.1 创建kuryr网络



```
docker network create --driver kuryr --ipam-driver kuryr --subnet 173.19.12.0/24 --gateway=173.19.12.1 test_docker_net


```







6.8.2 查看网络

`docker network ls`

6.8.3 创建容器(网络连接失败)

`docker run --net test_net cirros ifconfig`



#### zun-compute服务安装与配置





7.1 创建用户

```
groupadd --system zun
useradd --home-dir "/var/lib/zun" --create-home --system --shell /bin/false -g zun zun
```

7.2 创建目录

```
mkdir -p /etc/zun
chown zun:zun /etc/zun
```



安装依赖

python2版本

```
yum install epel-release python-pip git python-devel libffi-devel gcc openssl-devel -y
```

python3版本

```
yum install python3-pip git python3-devel libffi-devel gcc openssl-devel numactl
```





7.3 安装zun

```
cd /var/lib/zun
git clone -b stable/stein https://git.openstack.org/openstack/zun.git

chown -R zun:zun zun

cd zun

# python2安装
pip install -r requirements.txt
python setup.py install


# python36安装
pip3 install --upgrade pip
pip3 install --upgrade setuptools
# pip3 install -r requirements.txt
# python3 setup.py install
```





7.4 生成示例配置文件

```
# su -s /bin/sh -c "oslo-config-generator --config-file etc/zun/zun-config-generator.conf" zun
# su -s /bin/sh -c "cp etc/zun/zun.conf.sample /etc/zun/zun.conf" zun
# su -s /bin/sh -c "cp etc/zun/rootwrap.conf /etc/zun/rootwrap.conf" zun
# su -s /bin/sh -c "mkdir -p /etc/zun/rootwrap.d" zun
# su -s /bin/sh -c "cp etc/zun/rootwrap.d/* /etc/zun/rootwrap.d/" zun

# su -s /bin/sh -c "cp etc/cni/net.d/* /etc/cni/net.d/" zun

```



7.5 配置zun用户

```
echo "zun ALL=(root) NOPASSWD: /usr/bin/zun-rootwrap /etc/zun/rootwrap.conf *" | sudo tee /etc/sudoers.d/zun-rootwrap

python3
echo "zun ALL=(root) NOPASSWD: /usr/local/bin/zun-rootwrap /etc/zun/rootwrap.conf *" | sudo tee /etc/sudoers.d/zun-rootwrap
```



7.6 编辑配置文件，添加以下内容

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



7.7 配置docker和kuryr
7.7.1 创建docker配置文件夹

`mkdir -p /etc/systemd/system/docker.service.d`

###### 7.7.2 创建docker配置文件--报错

vim /etc/systemd/system/docker.service.d/docker.conf

**此处把compute和controller替换成对应的服务host名称或者ip地址**

```
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd --group zun -H tcp://compute:2375 -H unix:///var/run/docker.sock --cluster-store etcd://controller:2379
```





7.7.3 重启docker

```
systemctl daemon-reload
systemctl restart docker
```



7.7.4 编辑kuryr配置文件，添加以下内容

vim  /etc/kuryr/kuryr.conf

```
[DEFAULT]
capability_scope = global
process_external_connectivity = False
```



7.7.5 重启kuryr

```
systemctl restart kuryr-libnetwork
```







配置containerd

`containerd config default > /etc/containerd/config.toml`

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

配置CNI

```
# mkdir -p /opt/cni/bin
# curl -L https://github.com/containernetworking/plugins/releases/download/v0.7.1/cni-plugins-amd64-v0.7.1.tgz \
      | tar -C /opt/cni/bin -xzvf - ./loopback
      
   
   
# install -o zun -m 0555 -D /usr/bin/zun-cni /opt/cni/bin/zun-cni



```







7.8 创建启动文件

vim /etc/systemd/system/zun-compute.service

```
[Unit]
Description = OpenStack Container Service Compute Agent

[Service]
ExecStart = /usr/bin/zun-compute
User = zun

[Install]
WantedBy = multi-user.target
```



7.9 启动zun-compute

直接启动报错，需要安装

```
# python2
yum install mysql-devel python-devel
pip install Mysql-python

# python3
pip3 install pymysql
yum install pciutils
```

同时修改

```
# python2
sed -i "s/with_lockmode('update')/with_for_update()/" /usr/lib/python2.7/site-packages/zun/db/sqlalchemy/api.py



# python3
sed -i "s/with_lockmode('update')/with_for_update()/" /usr/local/lib/python3.6/site-packages/zun/db/sqlalchemy/api.py
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





##### 验证

控制节点

```
 pip install python-zunclient==3.3.0
 source /root/admin-openrc
 openstack appcontainer service list
```















zun-ui安装



https://docs.openstack.org/zun-ui/latest/install/index.html



horizon-dashboard安装配置

https://support.huaweicloud.com/dpmg-kunpengcpfs/kunpengopenstackstein_04_0015.html









### 安装过程中遇到的问题及解决



#### <font color=red>docker使用kuryr网络报错(先继续向下安装)</font>

Status: Downloaded newer image for cirros:latest
docker: Error response from daemon: failed to create endpoint great_colden on network test_net: NetworkDriver.CreateEndpoint: vif_type(binding_failed) is not supported. A binding script for this type can't be found.









#### 启动zun-compute报错

提示

```
2021-08-27 11:14:52.813 28753 ERROR oslo_service.periodic_task ImportError: No module named pymysql
```

安装pymysql(pip install pymysql)后，不能解析地址`comleader@123@controller`，手动pymysql源码修改，判断host，password后

运行`/usr/bin/zun-compute`

报错lspci命令

`yum install pciutils -y`

重新执行，依然报错

```
2021-08-27 15:36:52.711 30425 ERROR oslo_service.periodic_task AttributeError: 'Query' object has no attribute 'with_lockmode'
```






