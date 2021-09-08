## 					stein安装magnum



### 依赖环境

安装环境centos7

magnum相关的密码都是comleader123



### 控制节点

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

```
openstack endpoint create --region RegionOne container-infra public http://controller:9511/v1
openstack endpoint create --region RegionOne container-infra internal http://controller:9511/v1
openstack endpoint create --region RegionOne container-infra admin http://controller:9511/v1
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

如果没有外部网络，创建一个外部网络

创建密钥对，magnum集群需要

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

```


openstack coe cluster template create kubernetes-cluster-template --image fedora_atomic_for_magnum_k8s  --external-network provider --dns-nameserver 8.8.8.8 --master-flavor m1.small --docker-volume-size 5 --flavor m1.small --coe kubernetes
                     
                     
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
       # import pdb; pdb.set_trace()
        cluster_template = args[1]
        cluster_distro = cluster_template.cluster_distro
      #  if str(cluster_distro) ==  "Unset":
      #      cluster_distro == None
        cluster_distro == None
        if not cluster_distro:
            try:
                cli = clients
此处对镜像设置cluster_distro后，cluster_template.cluster_distro得到的是unsetType类
临时处理，强制用image里的cluster_distro
```

















##### 用秘钥创建master和node节点

```
openstack coe cluster create kubernetes-cluster \
                        --cluster-template kubernetes-cluster-template \
                        --master-count 1 \
                        --node-count 1 \
                        --keypair keyparitestmagnumcluster
```



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

