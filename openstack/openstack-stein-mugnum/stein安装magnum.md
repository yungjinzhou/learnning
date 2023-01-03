## 					一、stein安装magnum



### 依赖环境

- 安装环境centos7

- magnum相关的密码都是comleader123
- 需要有基本openstack环境，且已经安装了heat服务



### 安装步骤

> 均在控制节点安装

#### 创建magnum数据库

```
mysql -uroot -p

create database magnum;
GRANT ALL PRIVILEGES ON magnum.* TO 'magnum'@'localhost' IDENTIFIED BY 'comleader123';
GRANT ALL PRIVILEGES ON magnum.* TO 'magnum'@'%' IDENTIFIED BY 'comleader123';
```



登录

```
$ . admin-openrc
# 此处使用密码comleader123
openstack user create --domain default --password-prompt magnum

# magnum用户添加admin角色
openstack role add --project service --user magnum admin

```

#### 创建magnum服务

```
openstack service create --name magnum --description "OpenStack Container Infrastructure Management Service" container-infra

```



#### 创建容器管理服务 API endpoints

controller替换为控制节点的ip地址

```
openstack endpoint create --region RegionOne container-infra public http://192.168.232.107:9511/v1
openstack endpoint create --region RegionOne container-infra internal http://192.168.232.107:9511/v1
openstack endpoint create --region RegionOne container-infra admin http://192.168.232.107:9511/v1
```



magnum在管理coe集群时需要其他认证服务

#### 创建magnum包含项目和用户的域

```
openstack domain create --description "Owns users and projects created by magnum" magnum
openstack user create --domain magnum --password-prompt magnum_domain_admin
openstack role add --domain magnum --user-domain magnum --user magnum_domain_admin admin
```





#### 安装和配置组件

安装包

```
yum install openstack-magnum-api openstack-magnum-conductor python-magnumclient
```

配置magnum.conf

```
sed -i.default -e "/^#/d" -e "/^$/d" /etc/magnum/magnum.conf
```

vim /etc/magnum/magnum.conf

>In the `[certificates]` section, select `barbican` (or `x509keypair` if you don’t have barbican installed):

```
[DEFAULT]
transport_url = rabbit://openstack:openstack@192.168.204.173
host = 192.168.204.173
[api]
host = 192.168.204.173
port = 9511
[certificates]
cert_manager_type = x509keypair

[cinder_client]
region_name = RegionOne

[database]
connection = mysql+pymysql://magnum:comleader123@192.168.204.173/magnum
[keystone_authtoken]
memcached_servers = 192.168.204.173:11211
auth_version = v3
www_authenticate_uri = http://192.168.204.173:5000/v3
project_domain_id = default
project_name = service
user_domain_id = default
password = comleader123
username = magnum
auth_url = http://192.168.204.173:5000/v3
auth_type = password
admin_user = magnum
admin_password = comleader123
admin_tenant_name = service
service_token_roles_required = True

[keystone_auth]
memcached_servers = 192.168.204.173:11211
auth_version = v3
www_authenticate_uri = http://192.168.204.173:5000/v3
project_domain_id = default
project_name = service
user_domain_id = default
password = comleader123
username = magnum
auth_url = http://192.168.204.173:5000/v3
auth_type = password
admin_user = magnum
admin_password = comleader123
admin_tenant_name = service
service_token_roles_required = True

[trust]
trustee_domain_name = magnum
trustee_domain_admin_name = magnum_domain_admin
trustee_domain_admin_password = comleader123
trustee_keystone_interface = internal
auth_url = http://192.168.204.173:5000/v3
[oslo_messaging_notifications]
driver = messaging
[oslo_concurrency]
lock_path = /var/lib/magnum/tmp

```



##### 安装barbican(optional，可以不安装)

###### 创建数据库

```
mysql -uroot -p

CREATE DATABASE barbican;

GRANT ALL PRIVILEGES ON barbican.* TO 'barbican'@'localhost' IDENTIFIED BY 'comleader123';
GRANT ALL PRIVILEGES ON barbican.* TO 'barbican'@'%' IDENTIFIED BY 'comleader123';
```

###### 创建用户和角色

```
source admin-openrc
openstack user create --domain default --password-prompt barbican
openstack role add --project service --user barbican admin

openstack role create creator
openstack role add --project service --user barbican creator
```

###### 创建服务与endpoint

controller替换为ip地址

```
openstack service create --name barbican --description "Key Manager" key-manager

openstack endpoint create --region RegionOne key-manager public http://192.168.230.104:9311
openstack endpoint create --region RegionOne key-manager internal http://192.168.230.104:9311
openstack endpoint create --region RegionOne key-manager admin http://192.168.230.104:9311
```

###### 安装

```
yum install openstack-barbican-api -y
```

###### 修改配置



sed -i.default -e "/^#/d" -e "/^$/d" /etc/barbican/barbican.conf



```
[DEFAULT]
sql_connection = mysql+pymysql://barbican:comleader123@controller/barbican
transport_url = rabbit://openstack:openstack@controller
db_auto_create = false

[keystone_authtoken]
www_authenticate_uri = http://192.168.230.104:5000
auth_url = http://192.168.230.104:5000
memcached_servers = 192.168.230.104:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = barbican
password = comleader123

```



###### 同步数据库

```
su -s /bin/sh -c "barbican-manage db upgrade" barbican
```

###### 最终安装、配置httpd

 创建 /etc/httpd/conf.d/wsgi-barbican.conf

```
<VirtualHost [::1]:9311>
    ServerName controller

    ## Logging
    ErrorLog "/var/log/httpd/barbican_wsgi_main_error_ssl.log"
    LogLevel debug
    ServerSignature Off
    CustomLog "/var/log/httpd/barbican_wsgi_main_access_ssl.log" combined

    WSGIApplicationGroup %{GLOBAL}
    WSGIDaemonProcess barbican-api display-name=barbican-api group=barbican processes=2 threads=8 user=barbican
    WSGIProcessGroup barbican-api
    WSGIScriptAlias / "/usr/lib/python2.7/site-packages/barbican/api/app.wsgi"
    WSGIPassAuthorization On
</VirtualHost>
```

###### 重启服务

```
systemctl enable httpd.service
systemctl start httpd.service
```



#### 更新数据库

```
su -s /bin/sh -c "magnum-db-manage upgrade" magnum
```



#### 启动服务

```
systemctl enable openstack-magnum-api.service openstack-magnum-conductor.service
systemctl start openstack-magnum-api.service openstack-magnum-conductor.service
systemctl status openstack-magnum-api.service openstack-magnum-conductor.service
```



默认启动没有配置日志文件

可以修改openstack-magnum-api.service openstack-magnum-conductor.service

```
vim /usr/lib/systemd/system/openstack-magnum-api.service

ExecStart=/usr/bin/magnum-api
修改为
ExecStart=/usr/bin/magnum-api --config-file=/etc/magnum/magnum.conf --log-file=/var/log/magnum/magnum-api.log

```



#### 验证服务状态

状态是up

```
openstack coe service list
```





### 创建集群实例

- 如果没有外部网络，创建一个外部网络
- 创建密钥对，magnum集群需要
- 创建规格
- 创建符合条件的镜像（修改os_distro属性为可匹配的（fedora-atomic））
- <font color=red>**内网环境下要搭建本地etcd集群及discovery ，参考三**</font>

#### 上传集群需要的镜像

此处用k8s和swarm驱动需要的

>The VM versions of Kubernetes and Docker Swarm drivers require a Fedora Atomic image. The following is stock Fedora Atomic image, built by the Atomic team and tested by the Magnum team.

```
$ wget https://download.fedoraproject.org/pub/alt/atomic/stable/Fedora-Atomic-27-20180419.0/CloudImages/x86_64/images/Fedora-Atomic-27-20180419.0.x86_64.qcow2
```

#### 注册到镜像服务器

```
openstack image create \
                      --disk-format=qcow2 \
                      --container-format=bare \
                      --file=Fedora-Atomic-27-20180419.0.x86_64.qcow2\
                      --property os_distro='fedora-atomic' \
                      -latest
                      
                      
openstack image create --disk-format=qcow2 --container-format=bare --file=fedora-coreos-34.qcow2 --property os_distro='coreos' fedora-coreos-34latest       


openstack image create --disk-format=qcow2 --container-format=bare --file=fedora-coreos-34.qcow2 --property os_distro='fedora-atomic' fedora-atomic20180212    



openstack image create --disk-format=qcow2 --container-format=bare --file=centos7-20210422.qcow2 --property os_distro='centos' centos7-20210422-raw
```

#### 配置k8s集群，然后部署

##### 创建集群模板

- 注意要配置docker_volume_type，即volume_type，heat会调用cinder找对应的backend_driver，如果没有配置ceph、swift等，默认是lvm；
- 不配置doker-volume-size同样报错
- 创建前镜像、规格都要创建好，镜像选择适合magnum使用的几种对应的镜像，具体参考官网

```

openstack coe cluster template create kubernetes-cluster-template --image atomichostv3  --external-network for_magnum --dns-nameserver 8.8.8.8 --master-flavor m1.small --docker-volume-size 10 --flavor m1.small --labels docker_volume_type=lvm --coe kubernetes
 
openstack coe cluster template create kubernetes-cluster-template --image fedora-coreos-34latest  --external-network for_magnum --dns-nameserver 8.8.8.8 --master-flavor m1.small --docker-volume-size 10 --flavor m1.small --labels docker_volume_type=lvm --coe kubernetes
 
openstack coe cluster template create atomic-ussuritest --image e0b3a591-e3fa-4240-8339-5dd93c3ed7e0  --external-network for_magnum --dns-nameserver 8.8.8.8 --master-flavor m1.small --docker-volume-size 10 --flavor m1.small --labels docker_volume_type=lvm --coe kubernetes
 
```



报错

```
Cluster type (vm, Unset, kubernetes) not supported (HTTP 400) (Request-ID: req-7b41061d-5ea8-43f3-9bf1-0723c1e86871)


# magnum/api/validation.py
# 代码位置        cluster_type = (server_type, os, coe)
```



pdb定位代码

```
# magnum/drivers/common/driver.py

(Pdb) p definition_map
{
('bm', 'fedora', 'kubernetes'): {'class': <class 'magnum.drivers.k8s_fedora_ironic_v1.driver.Driver'>, 'entry_point_name': 'k8s_fedora_ironic_v1'}, 
('vm', 'ubuntu', 'mesos'): {'class': <class 'magnum.drivers.mesos_ubuntu_v1.driver.Driver'>, 'entry_point_name': 'mesos_ubuntu_v1'}, 
('vm', 'coreos', 'kubernetes'): {'class': <class 'magnum.drivers.k8s_coreos_v1.driver.Driver'>, 'entry_point_name': 'k8s_coreos_v1'}, ('vm', 'fedora-atomic', 'swarm-mode'): {'class': <class 'magnum.drivers.swarm_fedora_atomic_v2.driver.Driver'>, 'entry_point_name': 'swarm_fedora_atomic_v2'}, 
('vm', 'fedora-atomic', 'kubernetes'): {'class': <class 'magnum.drivers.k8s_fedora_atomic_v1.driver.Driver'>, 'entry_point_name': 'k8s_fedora_atomic_v1'}, 
('vm', 'fedora-atomic', 'swarm'): {'class': <class 'magnum.drivers.swarm_fedora_atomic_v1.driver.Driver'>, 'entry_point_name': 'swarm_fedora_atomic_v1'}}
(Pdb) 

由此可见，只有
('vm', 'coreos', 'kubernetes')
('vm', 'fedora-atomic', 'kubernetes')
才能符合
```



修改源码

```
def enforce_driver_supported():
    @decorator.decorator
    def wrapper(func, *args, **kwargs):
        cluster_template = args[1]
        cluster_distro = cluster_template.cluster_distro
        if str(cluster_distro) == "Unset":
            cluster_distro = None
        if not cluster_distro:
            try:
                cli = clients
```



##### 用秘钥创建master和node节点

```
openstack coe cluster create kubernetes-cluster \
                        --cluster-template kubernetes-cluster-template \
                        --master-count 1 \
                        --node-count 1 \
                        --docker-volume-size 5 \
                        --master-flavor m1.small \
                        --flavor m1.small \
                        --keypair keyparitestmagnumcluster
                        
                        
openstack coe cluster create ussuri-test --cluster-template atomic-ussuritest --master-count 1 --node-count 1 --docker-volume-size 10 --master-flavor m1.small --flavor m1.small  --keypair copmute01keypair --timeout 180
```

- 遇到创建失败，提示` reason: Resource CREATE failed: ResourceInError: resources.kube_masters.resources[0].resources.kube-master: Went to status ERROR due to "Message: No valid host was found. , Code: 500"`，扩展了计算节点的资源，删除无用实例后问题解决

- 创建失败提示`Cluster error, stack status: CREATE_FAILED, stack_id: 3802e51a-d30b-4a5b-bf15-f344ebfc0729, reason: Resource CREATE failed: ResourceInError: resources.kube_masters.resources[0].resources.docker_volume: Went to status error due to "Unknown"`查看卷scheduler日志，无法找到默认驱动，修改可用域x86_cinder为nova，并在cinder-api节点cinder-volume节点修改配置文件cinder.conf，增加

  ```
  [lvm]
  volume_driver = cinder.volume.drivers.lvm.LVMVolumeDriver
  volume_group = cinder-volumes
  target_protocol = iscsi
  target_helper = lioadm
  volume_backend_name = lvm
  ```

- 创建失败，修改模板中的heat_wait_condition参数改为10800，参考链接：https://bugs.launchpad.net/kolla-ansible/+bug/1842449；
- 创建模板时优化参数，参考链接https://lingxiankong.github.io/2018-02-15-magnum-note.html；
- 创建卡住，卡到kube_minions可能原因是minion发送请求到控制节点，但是endpoints配置的是controller，无法识别，需要在master  minion节点修改/etc/hosts配置 controller到ip的映射。参考链接：https://bugs.launchpad.net/kolla-ansible/+bug/1762754
- 配置文件修改，参考链接：https://bugs.launchpad.net/kolla-ansible/+bug/1885420





##### 查看状态

```
openstack coe cluster list
openstack coe cluster show kubernetes-cluster
```



##### 在环境中添加集群认证信息，

```
mkdir -p ~/clusters/kubernetes-cluster
 $(openstack coe cluster config kubernetes-cluster --dir ~/clusters/kubernetes-cluster)
 
```

##### 导出环境变量

```
export KUBECONFIG=/home/user/clusters/kubernetes-cluster/config
```

##### 列出k8s组件，查看状态


```
kubectl -n kube-system get po
```

##### 可以创建nginx然后验证是否运行

```
$ kubectl run nginx --image=nginx --replicas=5
deployment "nginx" created
$ kubectl get po
NAME                    READY     STATUS    RESTARTS   AGE
nginx-701339712-2ngt8   1/1       Running   0          15s
nginx-701339712-j8r3d   1/1       Running   0          15s
nginx-701339712-mb6jb   1/1       Running   0          15s
nginx-701339712-q115k   1/1       Running   0          15s
nginx-701339712-tb5lp   1/1       Running   0          15s
```







## 二、magnum-ui安装



### 安装 

控制节点安装

```
yum install -y openstack-magnum-ui
```

### 拷贝magnum-ui文件

到openstack-dashboard下

```
cp /usr/lib/python2.7/site-packages/magnum_ui/enabled/_1370_project_container_infra_panel_group.py /usr/share/openstack-dashboard/openstack_dashboard/local/enabled/
cp /usr/lib/python2.7/site-packages/magnum_ui/enabled/_1371_project_container_infra_clusters_panel.py /usr/share/openstack-dashboard/openstack_dashboard/local/enabled/
cp /usr/lib/python2.7/site-packages/magnum_ui/enabled/_1372_project_container_infra_cluster_templates_panel.py /usr/share/openstack-dashboard/openstack_dashboard/local/enabled/

```

### 更改权限，重启服务


```
chown -R apache:apache /usr/share/openstack-dashboard/
systemctl restart httpd.service memcached.service

$ ./manage.py collectstatic
$ ./manage.py compress

systemctl restart nginx.service uwsgi.service
```

如果界面显示异常

```
yum reinstall -y openstack-dashboard
chown -R apache:apache /usr/share/openstack-dashboard/
systemctl restart httpd.service memcached.service
```





horizon安装参考链接：https://support.huaweicloud.com/dpmg-kunpengcpfs/kunpengopenstackstein_04_0015.html

magnum-ui安装参考链接：https://github.com/openstack/magnum-ui







## 三、搭建etcd discovery

参考链接： http://zengxiaoran.com/2020/12/04/etcd_cluster_discovery/

### 1搭建etcd集群（物理主机节点）

（构建discory url的话，可以直接参考2，不用搭建宿主机集群）

#### 1.1安装etcd

`yum install etcd -y`



#### 1.2修改配置文件

##### 1.2.1 修改配置etcd文件

> 这里的集群模式是指完全集群模式，当然也可以在单机上通过不同的端口，部署伪集群模式，只是那样做只适合测试环境，生产环境考虑到可用性的话需要将etcd实例分布到不同的主机上，这里集群搭建有三种方式，分布是静态配置，etcd发现，dns发现。默认配置运行etcd，监听本地的2379端口，用于与client端交互，监听2380用于etcd内部交互。etcd启动时，集群模式下会用到的参数如下：
>
> 1. –name
> 2. etcd集群中的节点名，这里可以随意，可区分且不重复就行
> 3. –listen-peer-urls
> 4. 监听的用于节点之间通信的url，可监听多个，集群内部将通过这些url进行数据交互(如选举，数据同步等)
> 5. –initial-advertise-peer-urls
> 6. 建议用于节点之间通信的url，节点间将以该值进行通信。
> 7. –listen-client-urls
> 8. 监听的用于客户端通信的url,同样可以监听多个。
> 9. –advertise-client-urls
> 10. 建议使用的客户端通信url,该值用于etcd代理或etcd成员与etcd节点通信。
> 11. –initial-cluster-token etcd-cluster-1
> 12. 节点的token值，设置该值后集群将生成唯一id,并为每个节点也生成唯一id,当使用相同配置文件再启动一个集群时，只要该token值不一样，etcd集群就不会相互影响。
> 13. –initial-cluster
> 14. 也就是集群中所有的initial-advertise-peer-urls 的合集
> 15. –initial-cluster-state new
> 16. 新建集群的标志，初始化状态使用 new，建立之后改此值为 existing





[root@etcd1 /]# vim /etc/etcd/etcd.conf

```javascript
[root@compute-intel ~]# cat /etc/etcd/etcd.conf
#[Member]
#ETCD_CORS=""
ETCD_DATA_DIR="/var/lib/etcd/default.etcd"
#ETCD_WAL_DIR=""
ETCD_LISTEN_PEER_URLS="http://192.168.230.106:2380"
ETCD_LISTEN_CLIENT_URLS="http://192.168.230.106:2379,http://127.0.0.1:2379"
#ETCD_MAX_SNAPSHOTS="5"
#ETCD_MAX_WALS="5"
ETCD_NAME="Master"
#ETCD_SNAPSHOT_COUNT="100000"
#ETCD_HEARTBEAT_INTERVAL="100"
#ETCD_ELECTION_TIMEOUT="1000"
#ETCD_QUOTA_BACKEND_BYTES="0"
#ETCD_MAX_REQUEST_BYTES="1572864"
#ETCD_GRPC_KEEPALIVE_MIN_TIME="5s"
#ETCD_GRPC_KEEPALIVE_INTERVAL="2h0m0s"
#ETCD_GRPC_KEEPALIVE_TIMEOUT="20s"
#
#[Clustering]
ETCD_INITIAL_ADVERTISE_PEER_URLS="http://192.168.230.106:2380"
ETCD_ADVERTISE_CLIENT_URLS="http://192.168.230.106:2379"
#ETCD_DISCOVERY=""
#ETCD_DISCOVERY_FALLBACK="proxy"
#ETCD_DISCOVERY_PROXY=""
#ETCD_DISCOVERY_SRV=""
ETCD_INITIAL_CLUSTER="Master=http://192.168.230.106:2380,Slave01=http://192.168.230.101:2380,Slave02=http://192.168.230.102:2380"
ETCD_INITIAL_CLUSTER_TOKEN="etcd-cluster"
ETCD_INITIAL_CLUSTER_STATE="new"
#ETCD_STRICT_RECONFIG_CHECK="true"
#ETCD_ENABLE_V2="true"
#
#[Proxy]
#ETCD_PROXY="off"
#ETCD_PROXY_FAILURE_WAIT="5000"
#ETCD_PROXY_REFRESH_INTERVAL="30000"
#ETCD_PROXY_DIAL_TIMEOUT="1000"
#ETCD_PROXY_WRITE_TIMEOUT="5000"
#ETCD_PROXY_READ_TIMEOUT="0"
#
#[Security]
#ETCD_CERT_FILE=""
#ETCD_KEY_FILE=""
#ETCD_CLIENT_CERT_AUTH="false"
#ETCD_TRUSTED_CA_FILE=""
#ETCD_AUTO_TLS="false"
#ETCD_PEER_CERT_FILE=""
#ETCD_PEER_KEY_FILE=""
#ETCD_PEER_CLIENT_CERT_AUTH="false"
#ETCD_PEER_TRUSTED_CA_FILE=""
#ETCD_PEER_AUTO_TLS="false"
#
#[Logging]
#ETCD_DEBUG="false"
#ETCD_LOG_PACKAGE_LEVELS=""
#ETCD_LOG_OUTPUT="default"
#
#[Unsafe]
#ETCD_FORCE_NEW_CLUSTER="false"
#
#[Version]
#ETCD_VERSION="false"
#ETCD_AUTO_COMPACTION_RETENTION="0"
#
#[Profiling]
#ETCD_ENABLE_PPROF="false"
#ETCD_METRICS="basic"
#
#[Auth]
#ETCD_AUTH_TOKEN="simple"

```





以上是yum安装etcd集群的配置模板，待理解下面所用的二进制包etcd discovery方法后再自行实验。

**推荐二进制包安装etcd*（option）**

**yum虽然也能用，还是二进制包的方法操作简单些。**

下载稳定版本的etcd二进制包

```
mkdir /var/lib/etcd;mkdir /etc/etcd; groupadd -r etcd; useradd -r -g etcd -d /var/lib/etcd -s /sbin/nologin -c "etcd user" etcd;chown -R etcd:etcd /var/lib/etcd`
ETCD_VERSION=`curl -s -L https://github.com/coreos/etcd/releases/latest | grep linux-amd64\.tar\.gz | grep href | cut -f 6 -d '/' | sort -u`; ETCD_DIR=/opt/etcd-$ETCD_VERSION; mkdir $ETCD_DIR;curl -L https://github.com/coreos/etcd/releases/download/$ETCD_VERSION/etcd-$ETCD_VERSION-linux-amd64.tar.gz | tar xz --strip-components=1 -C $ETCD_DIR; ln -sf $ETCD_DIR/etcd /usr/bin/etcd && ln -sf $ETCD_DIR/etcdctl /usr/bin/etcdctl; etcd --version
```

##### 1.2.2 修改配置service文件

新建etcd服务启动脚本

```
[root@etcd1 /]# vim /usr/lib/systemd/system/etcd.service
[Unit]
Description=Etcd Server
After=network.target
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
WorkingDirectory=/var/lib/etcd/
EnvironmentFile=-/etc/etcd/etcd.conf
User=etcd
# set GOMAXPROCS to number of processors
ExecStart=/bin/bash -c "GOMAXPROCS=$(nproc) /usr/bin/etcd --name=\"${ETCD_NAME}\" --data-dir=\"${ETCD_DATA_DIR}\" --listen-client-urls=\"${ETCD_LISTEN_CLIENT_URLS}\""
Restart=on-failure
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target

```





可能遇到的问题及其他使用方法（可跳过该步骤，直接看务三.2启动服务



正常情况可以查看到成员列表`etcdctl member list`

```
[root@etcd1 etcd]# etcdctl member list
5c5384ee2a68922d: name=etcd01 peerURLs=http://192.168.0.5:2380 clientURLs=http://etcd1:2379 isLeader=true
b22b4d8949724d9b: name=etcd04 peerURLs=http://etcd4:2380 clientURLs=http://etcd4:2379 isLeader=false
c373b2eb6d13eb35: name=etcd02 peerURLs=http://192.168.0.6:2380 clientURLs=http://etcd2:2379 isLeader=false
```



#### 1.3 启动服务

```
[root@etcd3 /]# systemctl start etcd
```



### 2. 搭建etcd集群（容器方式）

基本集群搭建

```
docker run -d -p 2479:2379 \
              -p 2480:2380 \
              -p 4401:4001 \
              -p 7401:7001 \
              --name etcd-discovery \
192.168.66.29:80/openstack_magnum/elcolio/etcd
```



### 3. 构建discovery

由于每次构建k8s集群需要不一样的token来区分，临时在代码中生成token（测试时使用etcd）

生成token的集群，等搭建完成时需要优化为自动生成token，此处手动生成



#### 3.1 搭建discovery服务

```
docker run -d -p 7890:8087 \
           -e DISC_ETCD=http://192.168.230.104:2379 \
           -e DISC_HOST=http://192.168.230.104:7890 \
           --name discovery 192.168.66.29:80/openstack_magnum/quay.io/coreos/discovery.etcd.io:latest
```

#### 3.2生成token

curl http://127.0.0.1:7890/new?size=1

http://192.168.232.107:7890/56adb00635311f5a48e8b198a2d6bc2a



#### 3.3修改value size

[root@etcd3 /]# curl -X PUT http://192.168.232.107:2379/v2/keys/discovery/56adb00635311f5a48e8b198a2d6bc2a/_config/size -d value=1

```
返回值
{"action":"set","node":{"key":"/discovery/56adb00635311f5a48e8b198a2d6bc2a/_config/size","value":"1","modifiedIndex":2704,"createdIndex":2704}}
```



#### 3.4 使用discovery

创建magnum  template时写入discovery_url: http://192.168.232.107:2379/v2/keys/discovery/56adb00635311f5a48e8b198a2d6bc2a/

（/_config/size，在magnum代码里有处理，所以在配置界面，不用加后缀）



## 四、搭建harbor内网仓库



登录harbor命令

```
docker login 192.168.66.29 -u admin -p comleader@123
```





如果拉harbor镜像，提示https报错，

```
报错信息
Unable to find image '192.168.66.29:80/openstack_magnum/elcolio/etcd:latest' locally
Trying to pull repository 192.168.66.29:80/openstack_magnum/elcolio/etcd ...
/usr/bin/docker-current: Get https://192.168.66.29:80/v1/_ping: http: server gave HTTP response to HTTPS client.
```



需要在/etc/docker/daemon.json修改

```
{
"registry-mirrors": ["http://hub-mirror.c.163.com", "https://registry.docker-cn.com"],
"insecure-registries":["192.168.66.29:80"]
}
```







### magnum需要的内网镜像下载及上传

```javascript
# from docker hub
docker pull docker.io/openstackmagnum/kubernetes-controller-manager:v1.11.6
docker pull docker.io/openstackmagnum/kubernetes-proxy:v1.11.6
docker pull docker.io/openstackmagnum/kubernetes-apiserver:v1.11.6
docker pull docker.io/openstackmagnum/kubernetes-scheduler:v1.11.6
docker pull docker.io/openstackmagnum/kubernetes-kubelet:v1.11.6
docker pull docker.io/openstackmagnum/etcd:v3.2.7
docker pull docker.io/openstackmagnum/cluster-autoscaler:v1.0
docker pull docker.io/openstackmagnum/heat-container-agent:stein-dev

docker pull docker.io/k8scloudprovider/octavia-ingress-controller:1.13.2-alpha
docker pull docker.io/k8scloudprovider/k8s-keystone-auth:1.13.0
docker pull docker.io/k8scloudprovider/openstack-cloud-controller-manager:v0.2.0



docker pull docker.io/prom/prometheus:v1.8.2
docker pull docker.io/prom/node-exporter:v0.15.2

docker pull docker.io/grafana/grafana:5.1.5

docker pull docker.io/coredns/coredns:1.3.0

docker pull quay.io/calico/node:v2.6.7
docker pull quay.io/calico/cni:v1.11.2
docker pull quay.io/calico/kube-controllers:v1.0.3

docker pull quay.io/coreos/flannel-cni:v0.3.0
docker pull quay.io/coreos/flannel:v0.9.0


docker pull quay.io/kubernetes-ingress-controller/nginx-ingress-controller:0.23.0
docker pull k8s.gcr.io/defaultbackend:1.4
docker pull docker.io/openstackmagnum/helm-client:dev
docker pull quay.io/prometheus/alertmanager
docker pull quay.io/coreos/prometheus-operator
docker pull quay.io/coreos/configmap-reload
docker pull quay.io/coreos/prometheus-config-reloader
docker pull gcr.io/google-containers/hyperkube
docker pull quay.io/prometheus/prometheus







# from aliyun
docker pull registry.aliyuncs.com/google_containers/pause:3.0



# from google
docker pull gcr.io/google_containers/pause:3.0

docker pull gcr.io/google_containers/cluster-proportional-autoscaler-amd64:1.1.2
docker pull k8s.gcr.io/node-problem-detector:v0.6.2
# 没有Project 'project:kubernetes-helm' not found or deleted
# docker pull gcr.io/kubernetes-helm/tiller:v2.12.3
docker pull gcr.io/google_containers/kubernetes-dashboard-amd64:v1.8.3
docker pull gcr.io/google_containers/heapster-amd64:v1.4.2
docker pull gcr.io/google_containers/heapster-influxdb-amd64:v1.3.3
docker pull gcr.io/google_containers/heapster-grafana-amd64:v4.4.3


```





上传到harbor步骤

```
# 从google或者dockerhub拉取镜像
docker pull xxxx
# 保存到本地
docker save image_id > kubernetes-kubelet.tar
# 上传到可以连接到harbor服务器的主机上
scp  kubernetes-kubelet.tar root@192.168.230.161:/home/
# 导入到docker image
docker load -i kubernetes-kubelet.tar
# 给镜像打tag
docker tag docker.io/openstackmagnum/kubernetes-kubelet:v1.11.6 192.168.66.29:80/openstack_magnum/kubernetes-kubelet:v1.11.6
# 推送到镜像服务器
docker push 192.168.66.29:80/openstack_magnum/kubernetes-kubelet:v1.11.6


```







## 部署k8s遇到的错误及解决方法



1、 安装mangum, heat，需要创建文档中的用户，否则会认证 失败

2、

















## 部署k8s错误日志





```
[clients_magnum]
#
# From heat.common.config
#
# Type of endpoint in Identity service catalog to use for communication with
# the OpenStack service. (string value)
#endpoint_type = <None>
# Optional CA cert file to use in SSL connections. (string value)
#ca_file = <None>
# Optional PEM-formatted certificate chain file. (string value)
#cert_file = <None>
# Optional PEM-formatted file that contains the private key. (string value)
#key_file = <None>
# If set, then the server's certificate will not be verified. (boolean value)
#insecure = <None>

```









- 2021-09-13 16:51:33.708 64247 INFO heat.engine.scheduler [req-08854888-d52d-4808-88b6-b21fcd5f985d - admin - default default] Task create from SoftwareDeployment "kube_cluster_deploy" Stack "fedora-atomic-root-test-with-d-idlv2qepaqew" [73a2d6a9-f047-4139-9c7f-c5a5df906403] timed out



- 2021-09-13 16:51:34.080 64249 DEBUG heat.engine.scheduler [req-08854888-d52d-4808-88b6-b21fcd5f985d - admin - default default] Task create from HeatWaitCondition "minion_wait_condition" Stack "fedora-atomic-root-test-with-d-idlv2qepaqew-kube_minions-izcygqwk34gc-0-drtixczvrzar" [c8060190-102a-40c4-aab8-b3b78b410e3a] sleeping _sleep /usr/lib/python2.7/site-packages/heat/engine/scheduler.py:150











 `export KUBERNETES_MASTER=http://10.0.0.93:8080`





```
 对于非root用户 
mkdir -p $HOME/.kube

sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config 
sudo chown $(id -u):$(id -g) $HOME/.kube/config  


对于root用户 
export KUBECONFIG=/etc/kubernetes/admin.conf 
也可以直接放到~/.bash_profile 
echo "export KUBECONFIG=/etc/kubernetes/admin.conf" >> ~/.bash_profile 
```









[root@atomichostv1cluster-h5efkkibeh23-master-0 ~]# kubeadm init

I0917 00:34:39.938180   28691 version.go:93] could not fetch a Kubernetes version from the internet: unable to get URL "https://dl.k8s.io/release/stable-1.txt": Get https://storage.googleapis.com/kubernetes-release/release/stable-1.txt: net/http: request canceled while waiting for connection (Client.Timeout exceeded while awaiting headers)
I0917 00:34:40.012729   28691 version.go:94] falling back to the local client version: v1.12.5
[init] using Kubernetes version: v1.12.5
[preflight] running pre-flight checks
	[WARNING FileExisting-ethtool]: ethtool not found in system path
	[WARNING Hostname]: hostname "atomichostv1cluster-h5efkkibeh23-master-0.novalocal" could not be reached
	[WARNING Hostname]: hostname "atomichostv1cluster-h5efkkibeh23-master-0.novalocal" lookup atomichostv1cluster-h5efkkibeh23-master-0.novalocal on 8.8.8.8:53: no such host
[preflight] Some fatal errors occurred:
	[ERROR Port-10251]: Port 10251 is in use
	[ERROR Port-10252]: Port 10252 is in use
	[ERROR Port-2379]: Port 2379 is in use
	[ERROR DirAvailable--var-lib-etcd]: /var/lib/etcd is not empty
[preflight] If you know what you are doing, you can make a check non-fatal with `--ignore-preflight-errors=...`





2021-09-23 12:39:43.221 71521 INFO heat.engine.scheduler [req-5d63ee43-b892-4a51-9285-152ebc5e4fe6 - admin - default default] Task create from SoftwareDeployment "kube_cluster_deploy" Stack "atomichostv2cluster-b4vyomps5xay" [ea6069c8-f0a9-4f53-9c25-868daf09c7ff] timed out





cp RPM-GPG-KEY-fedora-29-x86_64   RPM-GPG-KEY-fedora-x86_64



http://mirrors.aliyun.com/fedora/releases/27/Everything/x86_64/os/ /repodata/repomd.xml

https://archives.fedoraproject.org/pub/archive/fedora/linux/releases/27/Everything/





```
[fedora] 
name=Fedora $releasever - $basearch - aliyun
#baseurl=https://archives.fedoraproject.org/pub/archive/fedora/releases/$releasever/Everything/$basearch/os/
baseurl=http://mirrors.aliyun.com/fedora/releases/$releasever/Everything/$basearch/os/ 
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=fedora-$releasever&arch=$basearch 
enabled=1 
metadata_0xpire=7d 
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-29-$basearch 
 
[fedora-debuginfo] 
name=Fedora $releasever - $basearch - Debug - aliyun
failovermethod=priority 

#baseurl=http://mirrors.aliyun.com/fedora/releases/$releasever/Everything/$basearch/debug/ 
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=fedora-debug-$releasever&arch=$basearch 
enabled=1 
metadata_expire=7d 
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-29-$basearch 
 
[fedora-source] 
name=Fedora $releasever - Source - aliyun
failovermethod=priority 
baseurl=https://archives.fedoraproject.org/pub/archive/fedora/releases/$releasever/Everything/source/SRPMS/ 
#mirrorli0t=https://mirrors.fedoraproject.org/metalink?repo=fedora-source-$releasever&arch=$basearch 
enabled=1 
metadata_expire=7d 
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-29-$basearch 

```



```

[updates]
name=Fedora $releasever - $basearch - Updates - aliyun
failovermethod=priority 
# baseurl=http://mirrors.aliyun.com/fedora/updates/$releasever/Everything/$basearch/ 
baseurl=https://archives.fedoraproject.org/pub/archive/fedora/updates/$releasever/Everything/$basearch/ 
#mirrorli0t=https://mirrors.fedoraproject.org/metalink?repo=updates-released-f$releasever&arch=$basearch 
enabled=1 
gpgcheck=0 
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-29-$basearch 
 
[updates-debuginfo] 
name=Fedora $releasever - $basearch - Updates - Debug -aliyun
failovermethod=priority 
#baseurl=http://mirrors.aliyun.com/fedora/updates/$releasever/Everything/$basearch/debug/ 
baseurl=https://archives.fedoraproject.org/pub/archive/fedora/updates/$releasever/Everything/$basearch/debug/ 
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=updates-released-debug-f$releasever&arch=$basearch 
enabled=0 
gpgcheck=0 
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-29-$basearch 
 
[updates-source] 
name=Fedora $releasever - Updates Source - aliyun
failovermethod=priority 
baseurl=https://archives.fedoraproject.org/pub/archive/fedora/updates/$releasever/Everything/SRPMS/ 
#baseurl=http://mirrors.aliyun.com/fedora/updates/$releasever/Everything/SRPMS/ 
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=updates-released-source-f$releasever&arch=$basearch 
enabled=0 
gpgcheck=0 
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-29-$basearch 



```









/var/lib/cloud/instance/scripts/part-010



/usr/bin/python3 -Es /usr/bin/atomic install  --storage ostredd --system --system-package=no --namea=kube-controller-manger docker.io/openstackmagnum/kubernetes-controller-manager:v1.11.6 





/var/lib/containers/atomic/kube-controller-manger.0





  cloud-init.target                                                                         loaded inactive   dead      start Cloud-init target                                                            



  cloud-config.target                                                                       loaded active     active          Cloud-config availability                                                    





atomic install  --storage ostredd --system --system-package no --set REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt --name heat-container-agent docker.io/openstackmagnum/kubernetes-controller-agent:stein-dev



atomic install --storage ostree --system '--set=ADDTL_MOUNTS=,{"type":"bind","source":"/opt/cni","destination":"/opt/cni","options":["bind","rw","slave","mode=777"]},{"type":"bind","source":"/var/lib/docker","destination":"/var/lib/docker","options":["bind","rw","slave","mode=755"]}' --system-package=no --name=kubelet docker.io/openstackmagnum/kubernetes-kubelet:v1.11.6

atomic install --storage ostree --system --system-package=no --name=kube-apiserver docker.io/openstackmagnum/kubernetes-apiserver:v1.11.6









kube      2981  2969 59 06:59 ?        00:00:20 /usr/local/bin/kube-apiserver --logtostderr=true --v=0 --etcd-servers=http://127.0.0.1:2379 --bind-address=0.0.0.0 --secure-port=6443 --insecure-bind-address=127.0.0.1 --insecure-port=8080 --allow-privileged=true --service-cluster-ip-range=10.254.0.0/16 --admission-control=NodeRestriction,NamespaceLifecycle,LimitRanger,ServiceAccount,DefaultStorageClass,DefaultTolerationSeconds,MutatingAdmissionWebhook,ValidatingAdmissionWebhook,ResourceQuota --runtime-config=api/all=true --allow-privileged=true --kubelet-preferred-address-types=InternalIP,Hostname,ExternalIP --authorization-mode=Node,Webhook,RBAC --tls-cert-file=/etc/kubernetes/certs/server.crt --tls-private-key-file=/etc/kubernetes/certs/server.key --client-ca-file=/etc/kubernetes/certs/ca.crt --service-account-key-file=/etc/kubernetes/certs/service_account.key --kubelet-certificate-authority=/etc/kubernetes/certs/ca.crt --kubelet-client-certificate=/etc/kubernetes/certs/server.crt --kubelet-client-key=/etc/kubernetes/certs/server.key --kubelet-https=true --proxy-client-cert-file=/etc/kubernetes/certs/server.crt --proxy-client-key-file=/etc/kubernetes/certs/server.key --requestheader-allowed-names=front-proxy-client,kube,kubernetes --requestheader-client-ca-file=/etc/kubernetes/certs/ca.crt --requestheader-extra-headers-prefix=X-Remote-Extra- --requestheader-group-headers=X-Remote-Group --requestheader-username-headers=X-Remote-User --cloud-provider=external --authentication-token-webhook-config-file=/etc/kubernetes/keystone_webhook_config.yaml --authorization-webhook-config-file=/etc/kubernetes/keystone_webhook_config.yaml









/sysroot/ostree/deploy/fedora-atomic/deploy/10b7d79eb645fcb1fd5f36c40ce3cc8c3269a89fe9c17f430dcc57e1641df492.0/usr/etc/systemd/system/kubelet.service.d/kubeadm.conf
/sysroot/ostree/deploy/fedora-atomic/deploy/10b7d79eb645fcb1fd5f36c40ce3cc8c3269a89fe9c17f430dcc57e1641df492.0/etc/systemd/system/kubelet.service.d/kubeadm.conf
/usr/etc/systemd/system/kubelet.service.d/kubeadm.conf
/etc/systemd/system/kubelet.service.d/kubeadm.conf







127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6
192.168.204.173  controller
10.0.0.59  atomichostv2cluster-gxwzlxwykemh-master-0.novalocal







kubeadm config print-defaults导出默认配置，并替换k8s.gcr.io为registry.aliyuncs.com/google_containers

```
apiEndpoint:
  advertiseAddress: 1.2.3.4
  bindPort: 6443
apiVersion: kubeadm.k8s.io/v1alpha3
bootstrapTokens:
- groups:
  - system:bootstrappers:kubeadm:default-node-token
  token: abcdef.0123456789abcdef
  ttl: 24h0m0s
  usages:
  - signing
  - authentication
kind: InitConfiguration
nodeRegistration:
  criSocket: /var/run/dockershim.sock
  name: atomichostv2cluster-gxwzlxwykemh-master-0.novalocal
  taints:
  - effect: NoSchedule
    key: node-role.kubernetes.io/master
---
apiVersion: kubeadm.k8s.io/v1alpha3
auditPolicy:
  logDir: /var/log/kubernetes/audit
  logMaxAge: 2
  path: ""
certificatesDir: /etc/kubernetes/pki
clusterName: kubernetes
controlPlaneEndpoint: ""
etcd:
  local:
    dataDir: /var/lib/etcd
    image: ""
imageRepository: registry.aliyuncs.com/google_containers
kind: ClusterConfiguration
kubernetesVersion: v1.12.0
networking:
  dnsDomain: cluster.local
  podSubnet: ""
  serviceSubnet: 10.96.0.0/12
unifiedControlPlaneImage: ""
---
apiEndpoint:
  advertiseAddress: 10.0.0.59
  bindPort: 6443
apiVersion: kubeadm.k8s.io/v1alpha3
caCertPath: /etc/kubernetes/pki/ca.crt
clusterName: kubernetes
discoveryFile: ""
discoveryTimeout: 5m0s
discoveryToken: abcdef.0123456789abcdef
discoveryTokenAPIServers:
- kube-apiserver:6443
discoveryTokenUnsafeSkipCAVerification: true
kind: JoinConfiguration
nodeRegistration:
  criSocket: /var/run/dockershim.sock
  name: atomichostv2cluster-gxwzlxwykemh-master-0.novalocal
tlsBootstrapToken: abcdef.0123456789abcdef
token: abcdef.0123456789abcdef
---
apiVersion: kubeproxy.config.k8s.io/v1alpha1
bindAddress: 0.0.0.0
clientConnection:
  acceptContentTypes: ""
  burst: 10
  contentType: application/vnd.kubernetes.protobuf
  kubeconfig: /var/lib/kube-proxy/kubeconfig.conf
  qps: 5
clusterCIDR: ""
configSyncPeriod: 15m0s
conntrack:
  max: null
  maxPerCore: 32768
  min: 131072
  tcpCloseWaitTimeout: 1h0m0s
  tcpEstablishedTimeout: 24h0m0s
enableProfiling: false
healthzBindAddress: 0.0.0.0:10256
hostnameOverride: ""
iptables:
  masqueradeAll: false
  masqueradeBit: 14
  minSyncPeriod: 0s
  syncPeriod: 30s
ipvs:
  excludeCIDRs: null
  minSyncPeriod: 0s
  scheduler: ""
  syncPeriod: 30s
kind: KubeProxyConfiguration
metricsBindAddress: 127.0.0.1:10249
mode: ""
nodePortAddresses: null
oomScoreAdj: -999
portRange: ""
resourceContainer: /kube-proxy
udpIdleTimeout: 250ms
---
address: 0.0.0.0
apiVersion: kubelet.config.k8s.io/v1beta1
authentication:
  anonymous:
    enabled: false
  webhook:
    cacheTTL: 2m0s
    enabled: true
  x509:
    clientCAFile: /etc/kubernetes/pki/ca.crt
authorization:
  mode: Webhook
  webhook:
    cacheAuthorizedTTL: 5m0s
    cacheUnauthorizedTTL: 30s
cgroupDriver: cgroupfs
cgroupsPerQOS: true
clusterDNS:
- 10.96.0.10
clusterDomain: cluster.local
configMapAndSecretChangeDetectionStrategy: Watch
containerLogMaxFiles: 5
containerLogMaxSize: 10Mi
contentType: application/vnd.kubernetes.protobuf
cpuCFSQuota: true
cpuCFSQuotaPeriod: 100ms
cpuManagerPolicy: none
cpuManagerReconcilePeriod: 10s
enableControllerAttachDetach: true
enableDebuggingHandlers: true
enforceNodeAllocatable:
- pods
eventBurst: 10
eventRecordQPS: 5
evictionHard:
  imagefs.available: 15%
  memory.available: 100Mi
  nodefs.available: 10%
  nodefs.inodesFree: 5%
evictionPressureTransitionPeriod: 5m0s
failSwapOn: true
fileCheckFrequency: 20s
hairpinMode: promiscuous-bridge
healthzBindAddress: 127.0.0.1
healthzPort: 10248
httpCheckFrequency: 20s
imageGCHighThresholdPercent: 85
imageGCLowThresholdPercent: 80
imageMinimumGCAge: 2m0s
iptablesDropBit: 15
iptablesMasqueradeBit: 14
kind: KubeletConfiguration
kubeAPIBurst: 10
kubeAPIQPS: 5
makeIPTablesUtilChains: true
maxOpenFiles: 1000000
maxPods: 110
nodeLeaseDurationSeconds: 40
nodeStatusUpdateFrequency: 10s
oomScoreAdj: -999
podPidsLimit: -1
port: 10250
registryBurst: 10
registryPullQPS: 5
resolvConf: /etc/resolv.conf
rotateCertificates: true
runtimeRequestTimeout: 2m0s
serializeImagePulls: true
staticPodPath: /etc/kubernetes/manifests
streamingConnectionIdleTimeout: 4h0m0s
syncFrequency: 1m0s
volumeStatsAggPeriod: 1m0s

```





```
/usr/local/bin/kube-apiserver --logtostderr=true --v=0 --etcd-servers=http://127.0.0.1:2379 --bind-address=0.0.0.0 --secure-port=6443 --insecure-bind-address=0.0.0.0 --insecure-port=8080 --allow-privileged=true --service-cluster-ip-range=10.254.0.0/16 --admission-control=NodeRestriction,NamespaceLifecycle,LimitRanger,ServiceAccount,DefaultStorageClass,DefaultTolerationSeconds,MutatingAdmissionWebhook,ValidatingAdmissionWebhook,ResourceQuota --runtime-config=api/all=true --allow-privileged=true --kubelet-preferred-address-types=InternalIP,Hostname,ExternalIP --authorization-mode=Node,Webhook,RBAC --tls-cert-file=/etc/kubernetes/certs/server.crt --tls-private-key-file=/etc/kubernetes/certs/server.key --client-ca-file=/etc/kubernetes/certs/ca.crt --service-account-key-file=/etc/kubernetes/certs/service_account.key --kubelet-certificate-authority=/etc/kubernetes/certs/ca.crt --kubelet-client-certificate=/etc/kubernetes/certs/server.crt --kubelet-client-key=/etc/kubernetes/certs/server.key --kubelet-https=true --proxy-client-cert-file=/etc/kubernetes/certs/server.crt --proxy-client-key-file=/etc/kubernetes/certs/server.key --requestheader-allowed-names=front-proxy-client,kube,kubernetes --requestheader-client-ca-file=/etc/kubernetes/certs/ca.crt --requestheader-extra-headers-prefix=X-Remote-Extra- --requestheader-group-headers=X-Remote-Group --requestheader-username-headers=X-Remote-User --cloud-provider=external --authentication-token-webhook-config-file=/etc/kubernetes/keystone_webhook_config.yaml --authorization-webhook-config-file=/etc/kubernetes/keystone_webhook_config.yaml
```







临时禁用ipv6

```
$ sudo sh -c 'echo 1 > /proc/sys/net/ipv6/conf/<interface-name>/disable_ipv6'

$ sudo sh -c 'echo 1 > /proc/sys/net/ipv6/conf/lo/disable_ipv6'

```





systemd-tmpfiles --create /etc/tmpfiles.d/heat-container-agent.conf



```
bash <(curl -L https://raw.githubusercontent.com/v2fly/fhs-install-v2ray/master/install-release.sh)
```









```
sed -i "s/#baseurl/baseurl/g" /etc/yum.repos.d/fedora.repo /etc/yum.repos.d/fedora-updates.repo
sed -i "s/metalink/#metalink/g" /etc/yum.repos.d/fedora.repo /etc/yum.repos.d/fedora-updates.repo
sed -i "s http://download.fedoraproject.org/pub/fedora/linux https://repo.huaweicloud.com/fedora g" /etc/yum.repos.d/fedora.repo /etc/yum.repos.d/fedora-updates.repo
```









```
###
# kubernetes system config
#
# The following values are used to configure the kube-apiserver
#

# The address on the local server to listen to.
#KUBE_API_ADDRESS="--bind-address=0.0.0.0 --secure-port=6443 --insecure-bind-address=127.0.0.1 --insecure-port=8080"
KUBE_API_ADDRESS="--bind-address=0.0.0.0 --secure-port=6443 --insecure-bind-address=127.0.0.1 --insecure-port=8080"

# The port on the local server to listen on.
# KUBE_API_PORT="--port=8080"

# Port minions listen on
# KUBELET_PORT="--kubelet-port=10250"

# Comma separated list of nodes in the etcd cluster
KUBE_ETCD_SERVERS="--etcd-servers=http://127.0.0.1:2379"

# Address range to use for services
KUBE_SERVICE_ADDRESSES="--service-cluster-ip-range=10.254.0.0/16"

# default admission control policies
KUBE_ADMISSION_CONTROL="--admission-control=NodeRestriction,NamespaceLifecycle,LimitRanger,ServiceAccount,DefaultStorageClass,DefaultTolerationSeconds,MutatingAdmissionWebhook,ValidatingAdmissionWebhook,ResourceQuota"

# Add your own!
KUBE_API_ARGS="--runtime-config=api/all=true --allow-privileged=true --kubelet-preferred-address-types=InternalIP,Hostname,ExternalIP  --authorization-mode=Node,Webhook,RBAC --tls-cert-file=/etc/kubernetes/certs/server.crt --tls-private-key-file=/etc/kubernetes/certs/server.key --client-ca-file=/etc/kubernetes/certs/ca.crt --service-account-key-file=/etc/kubernetes/certs/service_account.key --kubelet-certificate-authority=/etc/kubernetes/certs/ca.crt --kubelet-client-certificate=/etc/kubernetes/certs/server.crt --kubelet-client-key=/etc/kubernetes/certs/server.key --kubelet-https=true         --proxy-client-cert-file=/etc/kubernetes/certs/server.crt         --proxy-client-key-file=/etc/kubernetes/certs/server.key         --requestheader-allowed-names=front-proxy-client,kube,kubernetes         --requestheader-client-ca-file=/etc/kubernetes/certs/ca.crt         --requestheader-extra-headers-prefix=X-Remote-Extra-         --requestheader-group-headers=X-Remote-Group         --requestheader-username-headers=X-Remote-User --cloud-provider=external --authentication-token-webhook-config-file=/etc/kubernetes/keystone_webhook_config.yaml --authorization-webhook-config-file=/etc/kubernetes/keystone_webhook_config.yaml --log=/var/log/apiserver.log"

```



fedora atomic system   atomic usage



```
[root@huaweirepo1-rh7sb66kntau-master-0 ~]# atomic --help
usage: atomic [-h] [-v] [--debug] [-i] [-y]
              {containers,diff,help,images,host,info,install,mount,pull,push,upload,run,scan,sign,stop,storage,migrate,top,trust,uninstall,unmount,umount,update,verify,version}
              ...

Atomic Management Tool

positional arguments:
  {containers,diff,help,images,host,info,install,mount,pull,push,upload,run,scan,sign,stop,storage,migrate,top,trust,uninstall,unmount,umount,update,verify,version}
                        commands
    containers          operate on containers
    diff                Show differences between two container images, file
                        diff or RPMS.
    images              operate on images
    host                execute Atomic host commands
    install             execute container image install method
    mount               mount container image to a specified directory
    pull                pull latest image from a repository
    push (upload)       push latest image to repository
    run                 execute container image run method
    scan                scan an image or container for CVEs or configuration
                        compliance
    sign                Sign an image
    stop                execute container image stop method
    storage (migrate)   manage container storage
    top                 Show top-like stats about processes running in
                        containers
    trust               Manage system container trust policy
    uninstall           execute container image uninstall method
    unmount (umount)    unmount container image

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show atomic version and exit
  --debug               show debug messages
  -i, --ignore          ignore install-first requirement
  -y, --assumeyes       automatically answer yes for all questions
  
  
  
  
  
  
  
runc exec -t kube-apiserver /bin/sh
  
atomic run kube-apiserver

atomic pull quay.io/coreos/flannel:v0.10.0-amd64

rpm-ostree install kubernetes-kubeadm ethtool -r
 
```





kube-apiserver 启动命令

```
/usr/local/bin/kube-apiserver --logtostderr=true --v=0 --etcd-servers=http://127.0.0.1:2379 --bind-address=0.0.0.0 --secure-port=6444 --insecure-bind-address=0.0.0.0 --insecure-port=8081 --allow-privileged=true --service-cluster-ip-range=10.254.0.0/16 --admission-control=NodeRestriction,NamespaceLifecycle,LimitRanger,ServiceAccount,DefaultStorageClass,DefaultTolerationSeconds,MutatingAdmissionWebhook,ValidatingAdmissionWebhook,ResourceQuota --runtime-config=api/all=true --allow-privileged=true --kubelet-preferred-address-types=InternalIP,Hostname,ExternalIP --authorization-mode=Node,Webhook,RBAC --tls-cert-file=/etc/kubernetes/certs/server.crt --tls-private-key-file=/etc/kubernetes/certs/server.key --client-ca-file=/etc/kubernetes/certs/ca.crt --service-account-key-file=/etc/kubernetes/certs/service_account.key --kubelet-certificate-authority=/etc/kubernetes/certs/ca.crt --kubelet-client-certificate=/etc/kubernetes/certs/server.crt --kubelet-client-key=/etc/kubernetes/certs/server.key --kubelet-https=true --proxy-client-cert-file=/etc/kubernetes/certs/server.crt --proxy-client-key-file=/etc/kubernetes/certs/server.key --requestheader-allowed-names=front-proxy-client,kube,kubernetes --requestheader-client-ca-file=/etc/kubernetes/certs/ca.crt --requestheader-extra-headers-prefix=X-Remote-Extra- --requestheader-group-headers=X-Remote-Group --requestheader-username-headers=X-Remote-User --cloud-provider=external --authentication-token-webhook-config-file=/etc/kubernetes/keystone_webhook_config.yaml --authorization-webhook-config-file=/etc/kubernetes/keystone_webhook_config.yaml
 
```







```
ETCD_NAME="10.0.0.246"
ETCD_DATA_DIR="/var/lib/etcd/default.etcd"
ETCD_LISTEN_CLIENT_URLS="https://10.0.0.246:2379,http://0.0.0.0:2379"
ETCD_LISTEN_PEER_URLS="https://10.0.0.246:2380"

ETCD_ADVERTISE_CLIENT_URLS="https://10.0.0.246:2379,http://0.0.0.0:2379"
ETCD_INITIAL_ADVERTISE_PEER_URLS="https://10.0.0.246:2380"
ETCD_DISCOVERY="https://discovery.etcd.io/c32a249f2ea0d73e31ebeafbbdd13f33"
ETCD_CA_FILE=/etc/etcd/certs/ca.crt
ETCD_TRUSTED_CA_FILE=/etc/etcd/certs/ca.crt
ETCD_CERT_FILE=/etc/etcd/certs/server.crt
ETCD_KEY_FILE=/etc/etcd/certs/server.key
ETCD_CLIENT_CERT_AUTH=true
ETCD_PEER_CA_FILE=/etc/etcd/certs/ca.crt
ETCD_PEER_TRUSTED_CA_FILE=/etc/etcd/certs/ca.crt
ETCD_PEER_CERT_FILE=/etc/etcd/certs/server.crt
ETCD_PEER_KEY_FILE=/etc/etcd/certs/server.key
ETCD_PEER_CLIENT_CERT_AUTH=true

```







```
###
# kubernetes system config
#
# The following values are used to configure the kube-apiserver
#

# The address on the local server to listen to.
KUBE_API_ADDRESS="--bind-address=0.0.0.0 --secure-port=6443 --insecure-bind-address=0.0.0.0 --insecure-port=8080"

# The port on the local server to listen on.
# KUBE_API_PORT="--port=8080"

# Port minions listen on
# KUBELET_PORT="--kubelet-port=10250"

# Comma separated list of nodes in the etcd cluster
KUBE_ETCD_SERVERS="--etcd-servers=http://127.0.0.1:2379"

# Address range to use for services
KUBE_SERVICE_ADDRESSES="--service-cluster-ip-range=10.254.0.0/16"

# default admission control policies
KUBE_ADMISSION_CONTROL="--admission-control=NodeRestriction,NamespaceLifecycle,LimitRanger,ServiceAccount,DefaultStorageClass,DefaultTolerationSeconds,MutatingAdmissionWebhook,ValidatingAdmissionWebhook,ResourceQuota"

# KUBE_ADMISSION_CONTROL="--admission-control=NodeRestriction,NamespaceLifecycle,LimitRanger,DefaultStorageClass,DefaultTolerationSeconds,MutatingAdmissionWebhook,ValidatingAdmissionWebhook,ResourceQuota"

# Add your own!
KUBE_API_ARGS="--runtime-config=api/all=true --allow-privileged=true --kubelet-preferred-address-types=InternalIP,Hostname,ExternalIP --authorization-mode=Node,Webhook,RBAC --tls-cert-file=/etc/kubernetes/certs/server.crt --tls-private-key-file=/etc/kubernetes/certs/server.key --client-ca-file=/etc/kubernetes/certs/ca.crt --service-account-key-file=/etc/kubernetes/certs/service_account.key --kubelet-certificate-authority=/etc/kubernetes/certs/ca.crt --kubelet-client-certificate=/etc/kubernetes/certs/server.crt --kubelet-client-key=/etc/kubernetes/certs/server.key --kubelet-https=true --proxy-client-cert-file=/etc/kubernetes/certs/server.crt --proxy-client-key-file=/etc/kubernetes/certs/server.key --requestheader-allowed-names=front-proxy-client,kube,kubernetes --requestheader-client-ca-file=/etc/kubernetes/certs/ca.crt --requestheader-extra-headers-prefix=X-Remote-Extra- --requestheader-group-headers=X-Remote-Group --requestheader-username-headers=X-Remote-User --cloud-provider=external --authentication-token-webhook-config-file=/etc/kubernetes/keystone_webhook_config.yaml --authorization-webhook-config-file=/etc/kubernetes/keystone_webhook_config.yaml"

```









```
atomic install --storage ostree --system --system-package=no --name=kube-apiserver docker.io/openstackmagnum/kubernetes-apiserver:v1.11.6


atomic install --storage ostree --system '--set=ADDTL_MOUNTS=,{"type":"bind","source":"/opt/cni","destination":"/opt/cni","options":["bind","rw","slave","mode=777"]},{"type":"bind","source":"/var/lib/docker","destination":"/var/lib/docker","options":["bind","rw","slave","mode=755"]}' --system-package=no --name=kubelet docker.io/openstackmagnum/kubernetes-kubelet:v1.11.6



atomic install --storage ostree --system --system-package=no --name=kube-controller-manager docker.io/openstackmagnum/kubernetes-controller-manager:v1.11.6


atomic install --storage ostree --system --system-package=no --name=kube-scheduler docker.io/openstackmagnum/kubernetes-scheduler:v1.11.6

atomic install --storage ostree --system --system-package=no --name=kube-proxy docker.io/openstackmagnum/kubernetes-proxy:v1.11.6

 atomic install --storage ostree --system --system-package no --set REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt --name heat-container-agent docker.io/openstackmagnum/heat-container-agent:stein-dev
 
 atomic install --system-package no --system --storage ostree --name=etcd docker.io/openstackmagnum/etcd:v3.2.7
 
 
```





```
kubeadm config print init-defaults > kubeadm.conf


```







| 脚本名称                 | ussuri                         | stein                          |
| ------------------------ | ------------------------------ | ------------------------------ |
| calico-service-v3.3-x.sh | 有                             | 无                             |
| calico-service.sh        | 没有ETCD相关配置<br />变更较多 | 有ETCD相关配置<br />不一致较多 |
| kubecluster.yaml         | api_lb<br />etcd_lb            |                                |
|                          |                                |                                |
|                          |                                |                                |
|                          |                                |                                |
|                          |                                |                                |
|                          |                                |                                |
|                          |                                |                                |
|                          |                                |                                |
|                          |                                |                                |
|                          |                                |                                |
|                          |                                |                                |
|                          |                                |                                |
|                          |                                |                                |
|                          |                                |                                |
|                          |                                |                                |
|                          |                                |                                |
|                          |                                |                                |

ussuri:



stein:





使用fedoro atomic部署k8s时，拉取harobor镜像报错，gave HTTP response to HTTPS client



更改docker.service ，防止报错： gave HTTP response to HTTPS client

修改/etc/systemd/system/multi-user.target.wants/docker.service；修改/etc/systemd/system/docker.service

systemctl status docker.service查看实际用的配置文件























