# openstack octavia 简介以及手工安装过程

2018-07-06阅读 2.7K0

openstack octavia 是 openstack lbaas的支持的一种后台程序，提供为虚拟机流量的[负载均衡](https://cloud.tencent.com/product/clb?from=10680)。实质是类似于trove，调用 nove 以及neutron的api生成一台安装好haproxy和keepalived软件的虚拟机，并连接到目标网路。octavia共有4个组件 housekeeping,worker,api,health-manager，octavia agent。api作用就不详细说了。worker：主要作用是和nova，neutron等组件通信，用于虚拟机调度以及把对于虚拟机操作的指令下发给octavia agent。housekeeping：查看octavia/controller/housekeeping/house_keeping.py得知其三个功能点：SpareAmphora,DatabaseCleanup,CertRotation。依次是清理虚拟机的池子，清理过期数据库，更新证书。health-manager：检查虚拟机状态，和虚拟机中的octavia agent通信，来更新各个组件的状态。octavia agent 位于虚拟机内部：对下是接受指令操作下层的haproxy软件，对上是和health-manager通信汇报各种情况。可以参考博文http://lingxiankong.github.io/blog/2016/03/30/octavia/?utm_source=tuicool&utm_medium=referral



一 安装

1、创建数据库

```javascript
mysql> CREATE DATABASE octavia;
mysql> GRANT ALL PRIVILEGES ON octavia.* TO 'octavia'@'localhost'  IDENTIFIED BY 'comleader@123';
mysql> GRANT ALL PRIVILEGES ON octavia.* TO 'octavia'@'%' \  IDENTIFIED BY 'comleader@123';
```

2 创建用户 角色 endpoint

```javascript
openstack user create --domain default --password-prompt octavia
openstack role add --project service --user octavia admin
openstack service create --name octavia --description "octavia API" load_balancer 
openstack endpoint create octavia public http://controller:9876/ --region RegionOne 
openstack endpoint create octavia admin http://controller:9876/ --region RegionOne 
openstack endpoint create octavia internal http://controller:9876/ --region RegionOne
```

3 安装软件包

```javascript
yum install openstack-octavia-worker openstack-octavia-api python2-octavia openstack-octavia-health-manager openstack-octavia-housekeeping python2-octaviaclient openstack-octavia-common openstack-octavia-diskimage-create net-tools bridge-utils -y

```

创建证书配置文件 openssl.cnf

```
mkdir -p /var/lib/octavia/
cd /var/lib/octavia/
git clone https://opendev.org/openstack/octavia.git -b stable/train


mkdir certs
chmod 700 certs
cd certs


cp /var/lib/octavia/etc/certificates/openssl.cnf certs/
修改openssl.cnf，有效期改为10年
```



创建认证密钥

```
mkdir -p /var/lib/octavia/
cd /var/lib/octavia/
git clone https://opendev.org/openstack/octavia.git -b stable/train
cd octavia/bin/
# 修改 create_dual_intermediate_CA.sh里所有密码pass:not-secure-passphrase ,为pass:foobar
source create_dual_intermediate_CA.sh
mkdir -p /etc/octavia/certs/private
chmod 755 /etc/octavia -R
cp -p etc/octavia/certs/server_ca.cert.pem /etc/octavia/certs
cp -p etc/octavia/certs/server_ca-chain.cert.pem /etc/octavia/certs
cp -p etc/octavia/certs/server_ca.key.pem /etc/octavia/certs/private
cp -p etc/octavia/certs/client_ca.cert.pem /etc/octavia/certs
cp -p etc/octavia/certs/client.cert-and-key.pem /etc/octavia/certs/private

mkdir -p /etc/octavia/.ssh
# 设置密码foobar(不能有@，否则解析错误)
@ ssh-keygen -b 2048 -t rsa -N "" -f /etc/octavia/.ssh/octavia_ssh_key
ssh-keygen -b 1024 -t rsa -N "" -f /etc/octavia/.ssh/octavia_ssh_key


openstack keypair create --public-key /etc/octavia/.ssh/octavia_ssh_key.pub octavia_ssh_key  --project service
chown -R octavia. /etc/octavia/.ssh/

```



4 导入镜像 镜像是从devstack 生成的系统中导出来的

```
参考：制作镜像
官方教程：Building Octavia Amphora Images — octavia 9.1.0.dev16 documentation (openstack.org)

```



```javascript
openstack image create --disk-format qcow2 --container-format bare  --private --tag amphora --file amphora-x64-haproxy.qcow2 amphora-x64-haproxy
# image_id: 8546902d-c84c-489d-a8bb-0d2235d3e187
```

5 创建管理网络，并在主机创建ovs端口，使octavia-worker，octavia-housekeeping，octavia-health-manager能和生成的虚拟机实例通讯

 5.1 生成管理网络，网段

```javascript
openstack network create lb-mgmt-net

openstack subnet create --subnet-range 19.178.0.0/24 --allocation-pool start=19.178.0.2,end=19.178.0.200 --network lb-mgmt-net lb-mgmt-subnet
# network_id: 552f64af-c7e6-4353-a404-de53fe2fd7f3
```

 5.2 生成管理端口防火墙规则 

5555端口是管理网络，考虑到octavia组件尚不成熟，开启了22端口，镜像本身也是开启了22端口。

```javascript

openstack security group create lb-mgmt-sec-grp  --project service # id: 47f73d34-321d-48b3-a995-bf554a16b6ca
openstack security group rule create --protocol udp --dst-port 5555 lb-mgmt-sec-grp
openstack security group rule create --protocol icmp lb-mgmt-sec-grp
openstack security group rule create --protocol tcp --dst-port 22 lb-mgmt-sec-grp
openstack security group rule create --protocol tcp --dst-port 9443 lb-mgmt-sec-grp

openstack security group create lb-health-mgr-sec-grp --project service
openstack security group rule create --protocol icmp lb-health-mgr-sec-grp
openstack security group rule create --protocol udp --dst-port 5555 lb-health-mgr-sec-grp
openstack security group rule create --protocol tcp --dst-port 22 lb-health-mgr-sec-grp
openstack security group rule create --protocol tcp --dst-port 9443 lb-health-mgr-sec-grp

```

 5.3 在管理网络创建一个端口用于连接[宿主机](https://cloud.tencent.com/product/cdh?from=10680)中的octavia health_manager

```javascript
neutron port-create --name octavia-health-manager-standalone-listen-port --security-group lb-health-mgr-sec-grp --device-owner Octavia:health-mgr --binding:host_id=controller lb-mgmt-net


# port_id: d8362f9b-c114-4df7-bc73-52beb570cd49	
# iface_id: port_id
#subnet_id: c57dab53-0993-4e82-b95d-7f7bbc435c43
# port_mac_address: fa:16:3e:77:87:9c
# port_ip : 19.178.0.127
```

 5.4 创建宿主机的ovs端口 并**连接至5.1生成的网络**

```javascript
ovs-vsctl --may-exist add-port br-int o-hm0 -- set Interface o-hm0 type=internal -- set Interface o-hm0 external-ids:iface-status=active -- set Interface o-hm0 external-ids:attached-mac=fa:16:3e:77:87:9c -- set Interface o-hm0 external-ids:iface-id=d8362f9b-c114-4df7-bc73-52beb570cd49
```

**其中iface-id 和attached-mac 为 5.3生成的port的属性**

```javascript
ip link set dev o-hm0 address fa:16:3e:77:87:9c
```

 5.5 在宿主机上创建dhcp 

```
mkdir -p /etc/octavia/dhcp/
cp /var/lib/octavia/octavia/etc/octavia/dhcp/dhclient.conf /etc/octavia/dhcp/dhclient.conf
dhclient -v o-hm0 -cf /etc/octavia/dhcp/dhclient.conf
```

设置后，可能dhclient会设置默认路由更改原来的路由，导致ssh链接不上或者与本机默认网关冲突，建议删除

```
route -n 
route del default gw 19.178.0.1
```

设置开机启动

```
$ vi /opt/octavia-interface-start.sh
#!/bin/bash

set -x

#MAC=$MGMT_PORT_MAC
#PORT_ID=$MGMT_PORT_ID

# MAC 为 $MGMT_PORT_MAC ，PORT_ID 为 $MGMT_PORT_ID，具体含义看前面
MAC="fa:16:3e:77:87:9c"
PORT_ID="d8362f9b-c114-4df7-bc73-52beb570cd49"

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
route del default gw 19.178.0.1

$ chmod +x /opt/octavia-interface-start.sh
$ echo 'nohup sh /opt/octavia-interface-start.sh > /var/log/octavia-interface-start.log 2>&1 &' >> /etc/rc.d/rc.local
$ chmod +x /etc/rc.d/rc.local

```

6 配置修改，和其他openstack组件设置差不多

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
bind_port = 5555
bind_ip = 19.178.0.127
controller_ip_port_list = 19.178.0.127:5555
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
ca_private_key = /etc/octavia/certs/private/server_ca.key.pem
ca_certificate = /etc/octavia/certs/server_ca.cert.pem
# ca_private_key = /etc/octavia/certs/private/cakey.pem
# ca_certificate = /etc/octavia/certs/ca_01.pem
[anchor]
[networking]
[haproxy_amphora]
server_ca = /etc/octavia/certs/server_ca-chain.cert.pem
client_cert = /etc/octavia/certs/private/client.cert-and-key.pem
# server_ca = /etc/octavia/certs/ca_01.pem
# client_cert = /etc/octavia/certs/client.pem
key_path = /etc/octavia/.ssh/octavia_ssh_key
base_cert_dir = /var/lib/octavia/certs
connection_max_retries = 1500
connection_retry_interval = 1
[controller_worker]
amp_image_owner_id = b5a1eb4ee8374fa1aa88cd4b59afda98  # image owner id
amp_image_id = 8546902d-c84c-489d-a8bb-0d2235d3e187 # image  amphora-x64-haproxy id
amp_image_tag = amphora
amp_ssh_key_name = octavia_ssh_key  # opesntack keypair
amp_active_wait_sec = 1
amp_active_retries = 100
amp_secgroup_list = 93b4ace2-00fe-4f64-893d-9f7a1d5c1b54 # 	lb-mgmt-sec-grp id
amp_boot_network_list = 552f64af-c7e6-4353-a404-de53fe2fd7f3 #lb-mgmt-net id
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

分解配置解释

 6.1 设置数据库

```javascript
[database]
connection = mysql+pymysql://octavia:comleader@123@controller/octavia
```

 6.2 设置[消息队列](https://cloud.tencent.com/product/cmq?from=10680)

```javascript
[oslo_messaging_rabbit]
rabbit_host = controller
rabbit_userid = openstack
rabbit_password = openstack
```

6.3 设置 keystone的认证信息

```javascript
[keystone_authtoken]
auth_version = 3
admin_password = comleader@123
admin_tenant_name = octavia
admin_user = octavia
auth_uri = http://controller:5000/v3
```

6.4 设置health_manager组件监听地址，此ip地址等于5.3中创建的ip地址

```javascript
[health_manager]
bind_port = 5555
bind_ip = 19.178.0.127
controller_ip_port_list = 19.178.0.127:5555
```

6.5 设置和虚拟机通信的 公钥私钥

```javascript
[haproxy_amphora]
server_ca = /etc/octavia/certs/ca_01.pem
client_cert = /etc/octavia/certs/client.pem
key_path = /etc/octavia/.ssh/octavia_ssh_key
base_path = /var/lib/octavia
base_cert_dir = /var/lib/octavia/certs
connection_max_retries = 1500
connection_retry_interval = 1
```

6.6 设置 用于开启虚拟机实例的信息

```javascript
[controller_worker]
amp_boot_network_list = 826be4f4-a23d-4c5c-bff5-7739936fac76 # 步骤5.1中生成的id
amp_image_tag = amphora # 步骤4 中已经定义这个metadata
amp_secgroup_list = d949202b-ba09-4003-962f-746ae75809f7 # 步骤5.2 生成的安全组id
amp_flavor_id = dd49b3d5-4693-4407-a76e-2ca95e00a9ec
amp_image_id = b23dda5f-210f-40e6-9c2c-c40e9daa661a #步骤4中生成的镜像id
amp_ssh_key_name = 155 #
amp_active_wait_sec = 1
amp_active_retries = 100
network_driver = allowed_address_pairs_driver
compute_driver = compute_nova_driver
amphora_driver = amphora_haproxy_rest_driver
```

7 修改neutron配置（暂时没有修改原有配置）

 7.1 修改 /etc/neutron/neutron.conf 增加lbaas服务（没有配置，配置后会有错误）

```javascript
service_plugins = [existing service plugins],neutron_lbaas.services.loadbalancer.plugin.LoadBalancerPluginv2
```

7.2 在[service_providers] 章节 设置lbaas 的服务提供者为octavia(没有配置)

```javascript
 service_provider = LOADBALANCERV2:Octavia:neutron_lbaas.drivers.octavia.driver.OctaviaDriver:default
```

8 启动服务

如果之前 开启了 LBaaS v2 with an agent 服务 请关闭，并清理下neutron数据库下 lbaas_loadbalancers lbaas_loadbalancer_statistics 不然会报错

同步数据库

```javascript
octavia-db-manage   upgrade head
```

重启neutron 

```javascript
systemctl restart neutron-server
```

启动octavia

```javascript
systemctl restart  octavia-housekeeping  octavia-worker octavia-api octavia-health-manager
```



参考安装，配置证书

https://www.cnblogs.com/leffss/p/15598094.html#could-not-sign-the-certificate-request-failed-to-load-ca-certificate







二 验证

9.1 创建loadbalancer

```javascript
[root@controller ~]# neutron lbaas-loadbalancer-create --name test-lb-1 lbtest
Created a new loadbalancer:
+---------------------+--------------------------------------+
| Field               | Value                                |
+---------------------+--------------------------------------+
| admin_state_up      | True                                 |
| description         |                                      |
| id                  | 5af472bb-2068-4b96-bcb3-bef7ff7abc56 |
| listeners           |                                      |
| name                | test-lb-1                            |
| operating_status    | OFFLINE                              |
| pools               |                                      |
| provider            | octavia                              |
| provisioning_status | PENDING_CREATE                       |
| tenant_id           | 9a4b2de78c2d45cfbf6880dd34877f7b     |
| vip_address         | 192.168.123.10                       |
| vip_port_id         | d163b73c-258a-4e03-90ad-5db31cfe23ac |
| vip_subnet_id       | 74aea53a-014a-4f9c-86f9-805a2a772a27 |
+---------------------+--------------------------------------+
```

 9.2 查看虚拟机，值得注意的地方，loadbalancer的地址是vip，和虚拟机的地址是不相同的

```javascript
[root@controller ~]# openstack server list |grep 82b59e85-29f2-46ce-ae0b-045b7fceb5ca
| 82b59e85-29f2-46ce-ae0b-045b7fceb5ca | amphora-734da57c-e444-4b8e-a706-455230ae0803 | ACTIVE  | lbtest=192.168.123.9; lb-mgmt-net=192.168.0.6        | amphora-x64-haproxy 201610131607    |
```

 9.3 创建linstener

```javascript
neutron lbaas-listener-create --name test-lb-tcp --loadbalancer test-lb-1 --protocol TCP  --protocol-port 22
```

 9.4 设置安全组

```javascript
 neutron port-update  --security-group default d163b73c-258a-4e03-90ad-5db31cfe23ac
```

 9.5 创建pool,新建三台虚拟机，并加入pool

```javascript
openstack server create  --flavor m1.small --nic net-id=22525640-297e-40eb-bd77-0a9afd861f8c --image "cirros for kvm raw"  --min 3 --max 3 test

[root@controller ~]# openstack server list |grep test-
| d8dc22d4-e657-4c54-96f9-3a53ca67533d | test-3                                       | ACTIVE  | lbtest=192.168.123.8                                 | cirros for kvm raw                  |
| c7926665-84c5-48a5-9de5-5e15e71baa5d | test-2                                       | ACTIVE  | lbtest=192.168.123.13                                | cirros for kvm raw                  |
| fcf60c23-b799-4d08-a5a7-2b0fc9f1905e | test-1                                       | ACTIVE  | lbtest=192.168.123.11                                | cirros for kvm raw                  |

neutron lbaas-pool-create   --name test-lb-pool-tcp  --lb-algorithm ROUND_ROBIN --listener test-lb-tcp --protocol TCP
 
for i in {8,13,11}
do
neutron lbaas-member-create --subnet lbtest  --address 192.168.123.${i}  --protocol-port 22  test-lb-pool-tcp
done
```

 9.6 验证

```javascript
[root@controller ~]# >/root/.ssh/known_hosts;ip netns exec qrouter-4718cc34-68cc-47a7-9201-405d1fc09213 ssh cirros@192.168.123.10 "hostname"
The authenticity of host '192.168.123.10 (192.168.123.10)' can't be established.
RSA key fingerprint is 72:c4:11:41:53:51:f2:1b:b5:e6:1b:69:a8:c2:5b:d4.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '192.168.123.10' (RSA) to the list of known hosts.
cirros@192.168.123.10's password: 
test-3
[root@controller ~]# >/root/.ssh/known_hosts;ip netns exec qrouter-4718cc34-68cc-47a7-9201-405d1fc09213 ssh cirros@192.168.123.10 "hostname"
The authenticity of host '192.168.123.10 (192.168.123.10)' can't be established.
RSA key fingerprint is 3d:88:0f:4a:b1:77:c9:6a:fd:82:4d:31:0c:ca:82:d8.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '192.168.123.10' (RSA) to the list of known hosts.
cirros@192.168.123.10's password: 
test-1
[root@controller ~]# >/root/.ssh/known_hosts;ip netns exec qrouter-4718cc34-68cc-47a7-9201-405d1fc09213 ssh cirros@192.168.123.10 "hostname"
The authenticity of host '192.168.123.10 (192.168.123.10)' can't be established.
RSA key fingerprint is 1c:03:f0:f9:92:a7:0f:5d:9d:09:22:14:94:62:e4:c4.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '192.168.123.10' (RSA) to the list of known hosts.
cirros@192.168.123.10's password: 
test-2
```

三 过程分析

10.1 worker的相关操作

 创建 云主机实例，关联到管理网络：

```javascript
REQ: curl -g -i -X POST http://controller:8774/v2.1/9a4b2de78c2d45cfbf6880dd34877f7b/servers -H "User-Agent: python-novaclient" -H "Content-Type: application/json" -H "Accept: application/json" -H "X-OpenStack-Nova-API-Version: 2.1" -H "X-Auth-Token: {SHA1}0f810ab0fdd5b92489f73a7f0988adfc9da4e517" -d '{"server": {"name": "amphora-4f22d55b-0680-4111-aef6-da98c9ccd1d4", "imageRef": "b23dda5f-210f-40e6-9c2c-c40e9daa661a", "key_name": "155", "flavorRef": "dd49b3d5-4693-4407-a76e-2ca95e00a9ec", "max_count": 1, "min_count": 1, "personality": [{"path": "/etc/octavia/amphora-agent.conf", "contents": ""}, {"path": "/etc/octavia/certs/client_ca.pem", "contents": "="}, {"path": "/etc/octavia/certs/server.pem", "contents": ""}], "networks": [{"uuid": "826be4f4-a23d-4c5c-bff5-7739936fac76"}], "security_groups": [{"name": "d949202b-ba09-4003-962f-746ae75809f7"}], "config_drive": true}}' _http_log_request /usr/lib/python2.7/site-packages/keystoneauth1/session.py:337
```

当检测到目标云主机的管理网络状态变为active后进行下一步

```javascript
REQ: curl -g -i -X GET http://controller:8774/v2.1/9a4b2de78c2d45cfbf6880dd34877f7b/servers/d3c97360-56b2-4f75-b905-2ef83870a342/os-interface -H "User-Agent: python-novaclient" -H "Accept: application/json" -H "X-OpenStack-Nova-API-Version: 2.1" -H "X-Auth-Token: {SHA1}3f6ccac4cb8b70b06fb5e62b9db2272702d8ec67" _http_log_request /usr/lib/python2.7/site-packages/keystoneauth1/session.py:337
2016-10-17 12:06:30.041 29993 DEBUG novaclient.v2.client [-] RESP: [200] Content-Length: 286 Content-Type: application/json Openstack-Api-Version: compute 2.1 X-Openstack-Nova-Api-Version: 2.1 Vary: OpenStack-API-Version, X-OpenStack-Nova-API-Version X-Compute-Request-Id: req-ccc07b37-e942-4a5b-a87a-b0e8d3887ba3 Date: Mon, 17 Oct 2016 04:06:30 GMT Connection: keep-alive
RESP BODY: {"interfaceAttachments": [{"port_state": "ACTIVE", "fixed_ips": [{"subnet_id": "4e3409e5-4e9a-4599-9b2e-f760b2fab380", "ip_address": "192.168.0.11"}], "port_id": "bbf99a69-0fb2-42a6-b7de-b7969bda9d73", "net_id": "826be4f4-a23d-4c5c-bff5-7739936fac76", "mac_addr": "fa:16:3e:01:04:2c"}]}
2016-10-17 12:06:30.078 29993 DEBUG octavia.controller.worker.tasks.amphora_driver_tasks [-] Finalized the amphora. execute /usr/lib/python2.7/site-packages/octavia/controller/worker/tasks/amphora_driver_tasks.py:164
```

创建对外服务的vip的端口

```javascript
2016-10-17 12:06:30.226 29993 DEBUG octavia.controller.worker.controller_worker [-] Task 'octavia.controller.worker.tasks.network_tasks.AllocateVIP' (af8ea5a0-42c8-4d30-9ffa-016668811fc8) transitioned into state 'RUNNING' from state 'PENDING' _task_receiver /usr/lib/python2.7/site-packages/taskflow/listeners/logging.py:189
2016-10-17 12:06:30.227 29993 DEBUG octavia.controller.worker.tasks.network_tasks [-] Allocate_vip port_id c7d7b552-83ac-4e0c-84bf-0b9cae661eab, subnet_id 74aea53a-014a-4f9c-86f9-805a2a772a27,ip_address 192.168.123.31 execute /usr/lib/python2.7/site-packages/octavia/controller/worker/tasks/network_tasks.py:328

```

在该vip下面创建一个实际的port 并把该port  attach至 云主机

```javascript
2016-10-17 12:06:32.662 29993 DEBUG octavia.network.drivers.neutron.allowed_address_pairs [-] Created vip port: 1627d28d-bf54-46eb-9d78-410c5d647bf4 for amphora: 3f6e22a1-e0b0-4098-ba20-daf47cfdae19 _plug_amphora_vip /usr/lib/python2.7/site-packages/octavia/network/drivers/neutron/allowed_address_pairs.py:97
2016-10-17 12:06:32.663 29993 DEBUG novaclient.v2.client [-] REQ: curl -g -i -X POST http://controller:8774/v2.1/9a4b2de78c2d45cfbf6880dd34877f7b/servers/d3c97360-56b2-4f75-b905-2ef83870a342/os-interface -H "User-Agent: python-novaclient" -H "Content-Type: application/json" -H "Accept: application/json" -H "X-OpenStack-Nova-API-Version: 2.1" -H "X-Auth-Token: {SHA1}3f6ccac4cb8b70b06fb5e62b9db2272702d8ec67" -d '{"interfaceAttachment": {"port_id": "1627d28d-bf54-46eb-9d78-410c5d647bf4"}}' _http_log_request /usr/lib/python2.7/site-packages/keystoneauth1/session.py:337
```

创建listener

```javascript
2016-10-17 19:01:09.384 29993 DEBUG octavia.amphorae.drivers.haproxy.rest_api_driver [-] request url https://192.168.0.9:9443/0.5/listeners/c3a1867c-b2e5-49a7-819b-7a7d39063dda/reload request /usr/lib/python2.7/site-packages/octavia/amphorae/drivers/haproxy/rest_api_driver.py:248
2016-10-17 19:01:09.412 29993 DEBUG octavia.amphorae.drivers.haproxy.rest_api_driver [-] Connected to amphora. Response: <Response [202]> request /usr/lib/python2.7/site-packages/octavia/amphorae/drivers/haproxy/rest_api_driver.py:270
2016-10-17 19:01:09.414 29993 DEBUG octavia.controller.worker.controller_worker [-] Task 'octavia.controller.worker.tasks.amphora_driver_tasks.ListenersUpdate' (0f588287-a383-4c70-9847-20187dd19f9f) transitioned into state 'SUCCESS' from state 'RUNNING' with result 'None' _task_receiver /usr/lib/python2.7/site-packages/taskflow/listeners/logging.py:178
```

10.2

octavia agent分析

在9443端口创建监听端口给worker和health-manager 访问

```javascript
2016-10-17 12:10:41.344 1043 INFO werkzeug [-]  * Running on https://0.0.0.0:9443/ (Press CTRL+C to quit)
```

octavia agent的似乎有bug，不显示debug信息。

11 高可用测试

将/etc/octavia/octavia.conf配置文件中的loadbalancer_topology = SINGLE 改成 ACTIVE_STANDBY 可以启用高可用模式，目前不持双ACTIVE

生成loadbalancer之后，可以看到生成两个虚拟机

[root@controller octavia]# neutron lbaas-loadbalancer-create --name test-lb1238 lbtest2 

```javascript
Created a new loadbalancer:
+---------------------+--------------------------------------+
| Field               | Value                                |
+---------------------+--------------------------------------+
| admin_state_up      | True                                 |
| description         |                                      |
| id                  | 4e43f3c7-c0f6-44c7-8dab-e2fc8ed16e0f |
| listeners           |                                      |
| name                | test-lb1238                          |
| operating_status    | OFFLINE                              |
| pools               |                                      |
| provider            | octavia                              |
| provisioning_status | PENDING_CREATE                       |
| tenant_id           | 9a4b2de78c2d45cfbf6880dd34877f7b     |
| vip_address         | 192.168.235.14                       |
| vip_port_id         | 42f72c9f-4623-4bf5-ae82-29f8cf588d2d |
| vip_subnet_id       | 52e93565-eab2-4316-a04c-3e554992c993 |
+---------------------+--------------------------------------+
[root@controller ~]# openstack server list |grep 192.168.235                 |
| 736b8b76-2918-49a7-8477-995a168709bd | amphora-5379f109-01fa-429c-860b-c739e0c5ad5e | ACTIVE  | lb-mgmt-net=192.168.0.8; lbtest2=192.168.235.10  | amphora-x64-haproxy 201610131607    |
| bd867667-b8d2-49c5-bb1e-54f0753d33a3 | amphora-23540889-b07e-4c0e-ab9b-df0075fbb9c3 | ACTIVE  | lb-mgmt-net=192.168.0.25; lbtest2=192.168.235.19 | amphora-x64-haproxy 201610131607
```

看到3个ip:vip是192.168.235.14,两台机器出口



ip是192.168.235.10和192.168.235.19

登陆虚拟机验证一下，注意登陆的ip是管理网络的ip：

```javascript
[root@controller ~]# ssh 192.168.0.8 "ps -ef |grep keepalived; cat  /var/lib/octavia/vrrp/octavia-keepalived.conf"
root      1868     1  0 04:40 ?        00:00:00 /usr/sbin/keepalived -D -d -f /var/lib/octavia/vrrp/octavia-keepalived.conf
root      1869  1868  0 04:40 ?        00:00:00 /usr/sbin/keepalived -D -d -f /var/lib/octavia/vrrp/octavia-keepalived.conf
root      1870  1868  0 04:40 ?        00:00:00 /usr/sbin/keepalived -D -d -f /var/lib/octavia/vrrp/octavia-keepalived.conf
root      5448  5377  0 05:00 ?        00:00:00 bash -c ps -ef |grep keepalived; cat  /var/lib/octavia/vrrp/octavia-keepalived.conf
root      5450  5448  0 05:00 ?        00:00:00 grep keepalived
vrrp_script check_script {
  script /var/lib/octavia/vrrp/check_script.sh
  interval 5
  fall 2
  rise 2
}
vrrp_instance 4e43f3c7c0f644c78dabe2fc8ed16e0f {
 state MASTER
 interface eth1
 virtual_router_id 1
 priority 100
 nopreempt
 garp_master_refresh 5
 garp_master_refresh_repeat 2
 advert_int 1
 authentication {
  auth_type PASS
  auth_pass ee46125
 }
 unicast_src_ip 192.168.235.10
 unicast_peer {
       192.168.235.19
 }
 virtual_ipaddress {
  192.168.235.14
 }
 track_script {
    check_script
 }
}
[root@controller ~]# ssh 192.168.0.8 "ps -ef |grep haproxy; cat  /var/lib/octavia/836053f0-ea72-46ae-9fae-8b80153ef593/haproxy.cfg"
nobody    2195     1  0 04:43 ?        00:00:00 /usr/sbin/haproxy -f /var/lib/octavia/836053f0-ea72-46ae-9fae-8b80153ef593/haproxy.cfg -L jrwLnRhlvXcPd21JhvXEMStRHh0 -p /var/lib/octavia/836053f0-ea72-46ae-9fae-8b80153ef593/836053f0-ea72-46ae-9fae-8b80153ef593.pid -sf 2154
root      6745  6676  0 05:06 ?        00:00:00 bash -c ps -ef |grep haproxy; cat  /var/lib/octavia/836053f0-ea72-46ae-9fae-8b80153ef593/haproxy.cfg
root      6747  6745  0 05:06 ?        00:00:00 grep haproxy
# Configuration for test-lb1238
global
    daemon
    user nobody
    group nogroup
    log /dev/log local0
    log /dev/log local1 notice
    stats socket /var/lib/octavia/836053f0-ea72-46ae-9fae-8b80153ef593.sock mode 0666 level user

defaults
    log global
    retries 3
    option redispatch
    timeout connect 5000
    timeout client 50000
    timeout server 50000

peers 836053f0ea7246ae9fae8b80153ef593_peers
    peer 3OduZJiPzm475Q7IgyshE5oq1Jk 192.168.235.19:1025
    peer jrwLnRhlvXcPd21JhvXEMStRHh0 192.168.235.10:1025


frontend 836053f0-ea72-46ae-9fae-8b80153ef593
    option tcplog
    bind 192.168.235.14:22
    mode tcp
    default_backend 457d4de5-3213-4969-8f20-1f2d3505ff1e

backend 457d4de5-3213-4969-8f20-1f2d3505ff1e
    mode tcp
    balance leastconn
    timeout check 5
    server fa28676f-a762-4a8e-91ab-7a83f071b62b 192.168.235.20:22 weight 1 check inter 5s fall 3 rise 3
    server 1ded44da-cba5-434c-8578-95153656c392 192.168.235.24:22 weight 1 check inter 5s fall 3 rise 3
```

另一台结果结果类似。

结论：octavia的高可用是通过haproxy加keepalived来完成的。

四、其他

1、在services_lbaas.conf下有个选项 

[octavia]

request_poll_timeout = 200

此选项的定义了，创建loadbalancer之后，当超过这个时间以后，如果octavia还没有的状态没有变成active，neutron就会把这个loadbalancer设置为error，默认值是100，在我的环境下高可用模式会来不及。日志如下：

```javascript
2016-10-19 09:38:26.392 6256 DEBUG neutron_lbaas.drivers.octavia.driver [req-bee3619a-f9d4-4463-adcd-3cb99826b600 - - - - -] Octavia reports load balancer 2676dac6-c41d-4501-9c41-781a176c6baf has provisioning status of PENDING_CREATE thread_op /usr/lib/python2.7/site-packages/neutron_lbaas/drivers/octavia/driver.py:75
2016-10-19 09:38:29.393 6256 DEBUG neutron_lbaas.drivers.octavia.driver [req-bee3619a-f9d4-4463-adcd-3cb99826b600 - - - - -] Timeout has expired for load balancer 2676dac6-c41d-4501-9c41-781a176c6baf to complete an operation.  The last reported status was PENDING_CREATE thread_op /usr/lib/python2.7/site-packages/neutron_lbaas/drivers/octavia/driver.py:94
```

2、源代码小修改例子：

 当neutron的loadbalancer状态发生变成active或者error时候时候推送到报警系统

 修改/usr/lib/python2.7/site-packages/neutron_lbaas/drivers/octavia/driver.py

```javascript
        if prov_status == 'ACTIVE' or prov_status == 'DELETED':
            kwargs = {'delete': delete}
            if manager.driver.allocates_vip and lb_create:
                kwargs['lb_create'] = lb_create
                # TODO(blogan): drop fk constraint on vip_port_id to ports
                # table because the port can't be removed unless the load
                # balancer has been deleted.  Until then we won't populate the
                # vip_port_id field.
                # entity.vip_port_id = octavia_lb.get('vip').get('port_id')
                entity.vip_address = octavia_lb.get('vip').get('ip_address')
            manager.successful_completion(context, entity, **kwargs)
            if prov_status == 'ACTIVE':
              urllib2.urlopen('http://********')
              LOG.debug("report  status to******* {0}{1}".format(entity.root_loadbalancer.id, prov_status))
            return
        elif prov_status == 'ERROR':
            manager.failed_completion(context, entity)
            urllib2.urlopen('http://*******')
            LOG.debug("report status to ******* {0}{1}".format(entity.root_loadbalancer.id, prov_status))
            return
```

3、octavia的数据库和neutron不是同一张表，但是里面有很多数据要求要保持一致，一定要保持两者相关数据的同步，不同步的话会带来很多问题，亲身经历。

本文参与[腾讯云自媒体分享计划](https://cloud.tencent.com/developer/support-plan)，欢迎正在阅读的你也加入，一起分享。