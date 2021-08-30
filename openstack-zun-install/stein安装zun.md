## zun安装与配置

环境：centos7

opentack-zun版本stein

python2.7.5



### controller节点

#### 创建数据库

`mysql -uroot -pcomleader@123`

```
MariaDB [（none）] CREATE DATABASE zun;

MariaDB [(none)]> GRANT ALL PRIVILEGES ON zun.* TO 'zun'@'localhost' IDENTIFIED BY 'comleader@123';

MariaDB [(none)]> GRANT ALL PRIVILEGES ON zun.* TO 'zun'@'%' IDENTIFIED BY 'comleader@123';
```



#### 创建openstack用户、服务、端点



```
# . admin-openrc

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
connection = mysql+pymysql://zun:comleader@123@controller/zun
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
password = comleader@123
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
password = comleader@123
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



#### docker安装



卸载旧版本的docker

> ```
> yum remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine
> ```

### 

安装一点必备的依赖

`yum install -y epel-release yum-utils device-mapper-persistent-data lvm2 python-pip git python-devel libffi-devel gcc openssl-devel`
配置仓库

`yum-config-manager --add-repo http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo`

好像最近的docker版本升级了，变成了20版本，然后kuryr就用不成了。之前用的19.03没问题，就换成这个，安装这个版本的。

通过本地包安装

```
wget https://download.docker.com/linux/centos/7/x86_64/stable/Packages/docker-ce-19.03.14-3.el7.x86_64.rpm
wget https://download.docker.com/linux/centos/7/x86_64/stable/Packages/docker-ce-cli-19.03.14-3.el7.x86_64.rpm
wget https://download.docker.com/linux/centos/7/x86_64/stable/Packages/containerd.io-1.3.9-3.1.el7.x86_64.rpm

yum localinstall  -y  docker-ce-cli-19.03.14-3.el7.x86_64.rpm
yum localinstall  -y  containerd.io-1.3.9-3.1.el7.x86_64.rpm
yum localinstall  -y  docker-ce-19.03.14-3.el7.x86_64.rpm
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
#yum install epel-release python-pip git python-devel libffi-devel gcc openssl-devel -y

# cd /var/lib/kuryr

# git clone -b stable/stein https://git.openstack.org/openstack/kuryr-libnetwork.git

# chown -R kuryr:kuryr kuryr-libnetwork

# cd kuryr-libnetwork

# 安装下一步时如果报错，看下面操作
# pip install -r requirements.txt

# python setup.py install
```



```
# 直接执行pip install --upgrade pip，如果报错，可能是py2.7版本问题，通过下面途径更新pip
wget https://bootstrap.pypa.io/pip/2.7/get-pip.py
sudo python get-pip.py
更新setuptools
pip install --upgrade setuptools

yum install python-devel  # 没有安装时提示gcc 失败， yappi失败，缺少python.h文件

更新后在执行pip install -r requirements.txt

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
password = comleader@123

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

启动遇到问题，可能跟pip和python2.7版本有关系

重新安装了pip install pyroute2==0.4.21

6.8 验证
6.8.1 创建kuryr网络



```
docker network create --driver kuryr --ipam-driver kuryr --subnet 10.10.0.0/16 --gateway=10.10.0.1 test_net


```



# 

6.8.2 查看网络

`docker network ls`

6.8.3 创建容器

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

```
yum install epel-release python-pip git python-devel libffi-devel gcc openssl-devel -y
```



7.3 安装zun

```
cd /var/lib/zun
git clone -b stable/stein https://git.openstack.org/openstack/zun.git

chown -R zun:zun zun

cd zun
pip install -r requirements.txt
python setup.py install
```





7.4 生成示例配置文件

```
# su -s /bin/sh -c "oslo-config-generator --config-file etc/zun/zun-config-generator.conf" zun

# su -s /bin/sh -c "cp etc/zun/zun.conf.sample /etc/zun/zun.conf" zun

# su -s /bin/sh -c "cp etc/zun/rootwrap.conf /etc/zun/rootwrap.conf" zun

# su -s /bin/sh -c "mkdir -p /etc/zun/rootwrap.d" zun

# su -s /bin/sh -c "cp etc/zun/rootwrap.d/* /etc/zun/rootwrap.d/" zun
```



7.5 配置zun用户

```
echo "zun ALL=(root) NOPASSWD: /usr/bin/zun-rootwrap /etc/zun/rootwrap.conf *" | sudo tee /etc/sudoers.d/zun-rootwrap

```



7.6 编辑配置文件，添加以下内容

vim /etc/zun/zun.conf

```
[DEFAULT]

transport_url = rabbit://openstack:openstack@controller
state_path = /var/lib/zun

[database]
connection = mysql+pymysql://zun:comleader@123@controller/zun

[keystone_auth]
memcached_servers = controller:11211
www_authenticate_uri = http://controller:5000
project_domain_name = default
project_name = service
user_domain_name = default
password = comleader@123
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
password = comleader@123
username = zun
auth_url = http://controller:5000
auth_type = password

[websocket_proxy]
base_url = ws://controller:6784/
[oslo_concurrency]
lock_path = /var/lib/zun/tmp
```



7.7 配置docker和kuryr
7.7.1 创建docker配置文件夹

`mkdir -p /etc/systemd/system/docker.service.d`

###### 7.7.2 创建docker配置文件--报错

vim /etc/systemd/system/docker.service.d/docker.conf

```
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd --group zun -H tcp://compute:2375 -H unix:///var/run/docker.sock --cluster-store etcd://controller:2379
```



7.7.3 重启docker

```
# systemctl daemon-reload

# systemctl restart docker
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

```
# systemctl enable zun-compute
# systemctl start zun-compute
# systemctl status zun-compute
```











##### 验证



```
 pip install python-zunclient==3.3.0
 source /root/admin-openrc
 openstack appcontainer service list
```



























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

























































 

7.10 验证

```
pip install python-zunclient==1.1.0
source admin-openrc
openstack appcontainer service list
```

















