# openstack octavia 简介以及手工安装过程



**（stein版本对应4.1.4 octavia）**
**版本：stein版本，octavia_version==4.1.4**
**环境：centos7**

openstack octavia 是 openstack lbaas的支持的一种后台程序，提供为虚拟机流量的[负载均衡](https://cloud.tencent.com/product/clb?from=10680)。调用 nove 以及neutron的api生成一台安装好haproxy和keepalived软件的虚拟机，并连接到目标网路。octavia共有4个组件 housekeeping,worker,api,health-manager，octavia agent。api作用就不详细说了。worker：主要作用是和nova，neutron等组件通信，用于虚拟机调度以及把对于虚拟机操作的指令下发给octavia agent。housekeeping：查看octavia/controller/housekeeping/house_keeping.py得知其三个功能点：SpareAmphora,DatabaseCleanup,CertRotation。依次是清理虚拟机的池子，清理过期数据库，更新证书。health-manager：检查虚拟机状态，和虚拟机中的octavia agent通信，来更新各个组件的状态。octavia agent 位于虚拟机内部：对下是接受指令操作下层的haproxy软件，对上是和health-manager通信汇报各种情况。



### 1、创建数据库

```javascript
mysql> CREATE DATABASE octavia;
mysql> GRANT ALL PRIVILEGES ON octavia.* TO 'octavia'@'localhost'  IDENTIFIED BY 'comleader@123';
mysql> GRANT ALL PRIVILEGES ON octavia.* TO 'octavia'@'%'  IDENTIFIED BY 'comleader@123';
flush privileges;
```

### 2 创建用户 角色 endpoint

```javascript
openstack user create --domain default --password-prompt octavia
openstack role add --project service --user octavia admin
openstack service create --name octavia --description "octavia API" load_balancer 
openstack endpoint create octavia public http://controller:9876/ --region RegionOne 
openstack endpoint create octavia admin http://controller:9876/ --region RegionOne 
openstack endpoint create octavia internal http://controller:9876/ --region RegionOne
```

### 3 安装软件包

```javascript
yum install openstack-octavia-worker openstack-octavia-api python2-octavia openstack-octavia-health-manager openstack-octavia-housekeeping python2-octaviaclient openstack-octavia-common openstack-octavia-diskimage-create net-tools bridge-utils -y

```

### 4 导入镜像

是从devstack 生成的系统中导出来的

```
参考：制作镜像
官方教程：Building Octavia Amphora Images — octavia 9.1.0.dev16 documentation (openstack.org)

```



```javascript
openstack image create --disk-format qcow2 --container-format bare  --private --tag amphora --file amphora-x64-haproxy.qcow2 amphora-x64-haproxy
# image_id:  d6d3c84d-685f-4927-85ac-ce7594a14a20
# image_owner_id: 9b97026dba004226973f47c1a5565b63
```

### 5 创建管理网络

并在主机创建ovs端口，使octavia-worker，octavia-housekeeping，octavia-health-manager能和生成的虚拟机实例通讯

#### 创建证书并配置文件 

openssl.cnf

```
cd /var/lib/
git clone -b 4.1.4 https://opendev.org/openstack/octavia.git

mkdir -p /etc/octavia/certs
cd /etc/octavia/
chmod 700 certs

cp /var/lib/octavia/etc/certificates/openssl.cnf certs/
修改openssl.cnf，有效期改为10年
```

#### 创建认证密钥

```
# 证书相关的密码都改为或者设置为foobar

mkdir -p /etc/octavia/.ssh
ssh-keygen -b 2048 -t rsa -N "" -f /etc/octavia/.ssh/octavia_ssh_key
nova keypair-add --pub-key=/etc/octavia/.ssh/octavia_ssh_key.pub octavia_ssh_key --user <octavia的user id>


cd /var/lib/octavia/bin/
source create_certificates.sh /etc/octavia/certs/ /etc/octavia/certs/openssl.cnf
chown octavia:octavia /etc/octavia/certs -R
```



####  5.1 生成管理网络，网段

```javascript
openstack network create lb-mgmt-net 
openstack subnet create --subnet-range 19.178.0.0/24 --allocation-pool start=19.178.0.2,end=19.178.0.200 --network lb-mgmt-net lb-mgmt-subnet
# network_id: 7b42197a-97a9-4ad2-ae4c-82c3dfee0e3e

```

####  5.2 生成管理端口防火墙规则 

5555端口是管理网络，考虑到octavia组件尚不成熟，开启了22端口，镜像本身也是开启了22端口。

```javascript

openstack security group create lb-mgmt-sec-grp  --project service 
# security group id:  484e9029-fac6-458a-9f8e-75610948494f
# 把udp和tcp端口全部放开方便调试 
openstack security group rule create --protocol udp --dst-port 1:65535 lb-mgmt-sec-grp
openstack security group rule create --protocol icmp lb-mgmt-sec-grp
openstack security group rule create --protocol tcp --dst-port 1:65535 lb-mgmt-sec-grp


# openstack security group rule create --protocol udp --dst-port 5555 lb-mgmt-sec-grp
# openstack security group rule create --protocol icmp lb-mgmt-sec-grp
# openstack security group rule create --protocol tcp --dst-port 22 lb-mgmt-sec-grp
# openstack security group rule create --protocol tcp --dst-port 9443 lb-mgmt-sec-grp
```

####  5.3 在管理网络创建一个端口

用于连接[宿主机](https://cloud.tencent.com/product/cdh?from=10680)中的octavia health_manager

```javascript
neutron port-create --name octavia-health-manager-listen-port --security-group lb-mgmt-sec-grp --device-owner Octavia:health-mgr --binding:host_id=controller lb-mgmt-net --tenant-id 1e38230edf564bc3ad81b51f5c24f523 (项目名称为service的id)


# port_id: e51985e2-6030-4bab-a4b5-f203a0bb5b7e
# iface_id: port_id
#subnet_id: d125188e-78ae-416f-acbe-105758e16c92
# port_mac_address: fa:16:3e:99:c9:17
# port_ip : 19.178.0.178

```

####  5.4 创建宿主机的ovs端口

 并**连接至5.1生成的网络**

```javascript



# for ovs
ovs-vsctl --may-exist add-port br-int o-hm0 -- set Interface o-hm0 type=internal -- set Interface o-hm0 external-ids:iface-status=active -- set Interface o-hm0 external-ids:attached-mac=fa:16:3e:99:c9:17 -- set Interface o-hm0 external-ids:iface-id=e51985e2-6030-4bab-a4b5-f203a0bb5b7e



# for linuxbridge
ocatvia_mgmt_br=brq$(openstack network show lb-mgmt-net -c id -f value|cut -c 1-11)
 ip link add o-hm0 type veth peer name o-bhm0
 brctl addif $ocatvia_mgmt_br o-bhm0
 ip link set o-bhm0 up

```

**其中iface-id 和attached-mac 为 5.3生成的port的属性**

```javascript
ip link set dev o-hm0 address fa:16:3e:99:c9:17
```

####  5.5 在宿主机上创建dhcp 

```
mkdir -p /etc/octavia/dhcp/
cp /var/lib/octavia/etc/dhcp/dhclient.conf /etc/octavia/dhcp/dhclient.conf
dhclient -v o-hm0 -cf /etc/octavia/dhcp/dhclient.conf
```

设置后，**可能**dhclient会设置默认路由更改原来的路由，导致ssh链接不上或者与本机默认网关冲突，建议删除

```
route -n 
route del default gw 19.178.0.1
```

#### 5.6 设置开机启动

```
$ vi /opt/octavia-interface-start.sh
#!/bin/bash

set -x

#MAC=$MGMT_PORT_MAC
#PORT_ID=$MGMT_PORT_ID

# MAC 为 $MGMT_PORT_MAC ，PORT_ID 为 $MGMT_PORT_ID，具体含义看前面
MAC="fa:16:3e:5a:4b:c4"
PORT_ID="8bf3d486-77c8-46b8-9163-b19e383221db"

sleep 120s

ovs-vsctl --may-exist add-port br-int o-hm0 \
  -- set Interface o-hm0 type=internal \
  -- set Interface o-hm0 external-ids:iface-status=active \
  -- set Interface o-hm0 external-ids:attached-mac=$MAC \
  -- set Interface o-hm0 external-ids:iface-id=$PORT_ID

ip link set dev o-hm0 address $MAC
ip link set dev o-hm0 up
# iptables -I INPUT -i o-hm0 -p udp --dport 5555 -j ACCEPT
iptables -A INPUT -i o-hm0 -j ACCEPT # 完全放开，开发环境，方便调试
dhclient -v o-hm0 -cf /etc/dhcp/octavia

$ chmod +x /opt/octavia-interface-start.sh
$ echo 'nohup sh /opt/octavia-interface-start.sh > /var/log/octavia-interface-start.log 2>&1 &' >> /etc/rc.d/rc.local
$ chmod +x /etc/rc.d/rc.local
```

### 6 配置修改

和其他openstack组件设置差不多

sed  -i.default  -e '/^#/d'  -e '/^$/d' /etc/octavia/octavia.conf

总配置

```
[DEFAULT]
transport_url = rabbit://openstack:openstack@controller
[api_settings]
bind_host = 0.0.0.0
bind_port = 9876
[database]
connection = mysql+pymysql://octavia:comleader@123@controller/octavia
[health_manager]
# 设置health_manager组件监听地址，此ip地址等于5.3中创建的ip地址
bind_port = 5555
bind_ip = 19.178.0.194
controller_ip_port_list = 19.178.0.194:5555
heartbeat_key=insecure
[keystone_authtoken]
www_authenticate_uri = http://controller:5000
auth_url = http://controller:5000
memcached_servers = controller:11211
auth_type = password
project_domain_name = Default
user_domain_name = Default
project_name = service
username = octavia
password = comleader@123

[certificates] 
ca_private_key_passphrase = foobar  # 证书密码，建议所有都一致
ca_private_key = /etc/octavia/certs/private/cakey.pem
ca_certificate = /etc/octavia/certs/ca_01.pem
[anchor]
[networking]
[haproxy_amphora]
#  设置和虚拟机通信的 公钥私钥
server_ca = /etc/octavia/certs/ca_01.pem
client_cert = /etc/octavia/certs/client.pem
key_path = /etc/octavia/.ssh/octavia_ssh_key
base_path = /var/lib/octavia
base_cert_dir = /var/lib/octavia/certs
connection_max_retries = 1500
connection_retry_interval = 1
[controller_worker]
# 设置 用于开启虚拟机实例的信息
amp_image_owner_id = b5a1eb4ee8374fa1aa88cd4b59afda98  # image owner id
amp_image_id = 8546902d-c84c-489d-a8bb-0d2235d3e187 # image  amphora-x64-haproxy id
amp_image_tag = amphora
amp_ssh_key_name = octavia_ssh_key  # opesntack keypair
amp_active_wait_sec = 1
amp_active_retries = 100
amp_secgroup_list = 43416fd9-bf78-465c-8c4a-d03d2c908429 # 	lb-mgmt-sec-grp id
amp_boot_network_list = 7551834d-fbc9-45e6-833c-18aaa83dac41 #lb-mgmt-net id
amp_flavor_id = 1630128403613
network_driver = allowed_address_pairs_driver
compute_driver = compute_nova_driver
amphora_driver = amphora_haproxy_rest_driver
[task_flow]
[oslo_messaging]
topic = octavia_prov
[oslo_middleware]
[house_keeping]
[amphora_agent]
[keepalived_vrrp]
[service_auth]
auth_url = http://controller:5000
memcached_servers = controller:11211
auth_type = password
project_domain_name = Default
user_domain_name = Default
project_name = service
username = octavia
password = comleader@123
[nova]
[glance]
[neutron]
[quotas]
[audit]
[audit_middleware_notifications]
[driver_agent]
[oslo_messaging_rabbit]
rabbit_host = controller
rabbit_userid = openstack
rabbit_password = openstack

```

### 7 启动服务

如果之前 开启了 LBaaS v2 with an agent 服务 请关闭，并清理下neutron数据库下 lbaas_loadbalancers lbaas_loadbalancer_statistics 不然会报错

同步数据库

```javascript
octavia-db-manage  upgrade head
```

启动octavia

```javascript
systemctl enable  octavia-housekeeping  octavia-worker octavia-api octavia-health-manager
systemctl restart  octavia-housekeeping  octavia-worker octavia-api octavia-health-manager
systemctl status  octavia-housekeeping  octavia-worker octavia-api octavia-health-manager
```


