## 					stein安装magnum



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
openstack endpoint create --region RegionOne container-infra public http://192.168.204.173:9511/v1
openstack endpoint create --region RegionOne container-infra internal http://192.168.204.173:9511/v1
openstack endpoint create --region RegionOne container-infra admin http://192.168.204.173:9511/v1
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



##### 安装barbican(optional)

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

openstack endpoint create --region RegionOne key-manager public http://192.168.204.173:9311
openstack endpoint create --region RegionOne key-manager internal http://192.168.204.173:9311
openstack endpoint create --region RegionOne key-manager admin http://192.168.204.173:9311
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
www_authenticate_uri = http://192.168.204.173:5000
auth_url = http://192.168.204.173:5000
memcached_servers = 192.168.204.173:11211
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
- 创建符合条件的镜像

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
                      fedora-atomic-latest
```

#### 配置k8s集群，然后部署

##### 创建集群模板

- 注意要配置docker_volume_type，即volume_type，heat会调用cinder找对应的backend_driver，如果没有配置ceph、swift等，默认是lvm；
- 不配置doker-volume-size同样报错
- 创建前镜像、规格都要创建好，镜像选择适合magnum使用的几种对应的镜像，具体参考官网

```

openstack coe cluster template create kubernetes-cluster-template --image fedora_atomic_for_magnum_k8s  --external-network provider --dns-nameserver 8.8.8.8 --master-flavor m1.small --docker-volume-size 5 --flavor m1.small --labels docker_volume_type=lvm --coe kubernetes
                     
```



报错

```
Cluster type (vm, Unset, kubernetes) not supported (HTTP 400) (Request-ID: req-7b41061d-5ea8-43f3-9bf1-0723c1e86871)


# magnum/api/validation.py
# 代码位置        cluster_type = (server_type, os, coe)
```



pdb定位代码

```
(Pdb) p definition_map
{
('bm', 'fedora', 'kubernetes'): {'class': <class 'magnum.drivers.k8s_fedora_ironic_v1.driver.Driver'>, 'entry_point_name': 'k8s_fedora_ironic_v1'}, 
('vm', 'ubuntu', 'mesos'): {'class': <class 'magnum.drivers.mesos_ubuntu_v1.driver.Driver'>, 'entry_point_name': 'mesos_ubuntu_v1'}, ('vm', 'coreos', 'kubernetes'): {'class': <class 'magnum.drivers.k8s_coreos_v1.driver.Driver'>, 'entry_point_name': 'k8s_coreos_v1'}, ('vm', 'fedora-atomic', 'swarm-mode'): {'class': <class 'magnum.drivers.swarm_fedora_atomic_v2.driver.Driver'>, 'entry_point_name': 'swarm_fedora_atomic_v2'}, 
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
        if str(cluster_distro) ==  "Unset":
            cluster_distro == None
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







## magnum-ui安装



### 安装 

控制节点安装

```
yum install -y openstack-magnum-ui
```

### 拷贝magnum-ui文件

到openstack-dashboard下

```
cp /usrlib/python2.7/site-packages/magnum_ui/enabled/_1370_project_container_infra_panel_group.py /usr/share/openstack-dashboard/openstack_dashboard/local/enabled
cp /usrlib/python2.7/site-packages/magnum_ui/enabled/_1371_project_container_infra_clusters_panel.py /usr/share/openstack-dashboard/openstack_dashboard/local/enabled
cp /usrlib/python2.7/site-packages/magnum_ui/enabled/_1372_project_container_infra_cluster_templates_panel.py /usr/share/openstack-dashboard/openstack_dashboard/local/enabled

```

### 更改权限，重启服务


```
chown -R apache:apache /usr/share/openstack-dashboard/
systemctl restart httpd.service memcached.service
```

如果界面显示异常

```
yum reinstall -y openstack-dashboard
chown -R apache:apache /usr/share/openstack-dashboard/
systemctl restart httpd.service memcached.service
```





horizon安装参考链接：https://support.huaweicloud.com/dpmg-kunpengcpfs/kunpengopenstackstein_04_0015.html

magnum-ui安装参考链接：https://github.com/openstack/magnum-ui









### 部署k8s错误日志



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





```
[fedora] 
name=Fedora $releasever - $basearch - aliyun
failovermethod=priority 
baseurl=http://mirrors.aliyun.com/fedora/releases/$releasever/Everything/$basearch/os/ 
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=fedora-$releasever&arch=$basearch 
enabled=1 
metadata_0xpire=7d 
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-29-$basearch 
 
[fedora-debuginfo] 
name=Fedora $releasever - $basearch - Debug - aliyun
failovermethod=priority 
baseurl=http://mirrors.aliyun.com/fedora/releases/$releasever/Everything/$basearch/debug/ 
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=fedora-debug-$releasever&arch=$basearch 
enabled=1 
metadata_expire=7d 
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-29-$basearch 
 
[fedora-source] 
name=Fedora $releasever - Source - aliyun
failovermethod=priority 
baseurl=http://mirrors.aliyun.com/fedora/releases/$releasever/Everything/source/SRPMS/ 
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
baseurl=http://mirrors.aliyun.com/fedora/updates/$releasever/Everything/$basearch/ 
#mirrorli0t=https://mirrors.fedoraproject.org/metalink?repo=updates-released-f$releasever&arch=$basearch 
enabled=1 
gpgcheck=0 
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-29-$basearch 
 
[updates-debuginfo] 
name=Fedora $releasever - $basearch - Updates - Debug -aliyun
failovermethod=priority 
baseurl=http://mirrors.aliyun.com/fedora/updates/$releasever/Everything/$basearch/debug/ 
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=updates-released-debug-f$releasever&arch=$basearch 
enabled=0 
gpgcheck=0 
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-29-$basearch 
 
[updates-source] 
name=Fedora $releasever - Updates Source - aliyun
failovermethod=priority 
baseurl=http://mirrors.aliyun.com/fedora/updates/$releasever/Everything/SRPMS/ 
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



