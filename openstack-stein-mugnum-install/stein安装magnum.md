## 					stein安装magnum



安装环境centos7

magnum相关的密码都是comleader123



控制节点

创建magnum数据库

```
mysql -uroot -p

create database magnum;
GRANT ALL PRIVILEGES ON magnum.* TO 'magnum'@'localhost' IDENTIFIED BY 'comleader123';
GRANT ALL PRIVILEGES ON magnum.* TO 'magnum'@'%' IDENTIFIED BY 'comleader123';
```



登陆

```
$ . admin-openrc
# 此处使用密码comleader123
openstack user create --domain default --password-prompt magnum

# magnum用户添加admin角色
openstack role add --project service --user magnum admin

```

创建magnum服务

```
openstack service create --name magnum --description "OpenStack Container Infrastructure Management Service" container-infra


```



创建容器管理服务 API endpoints:

```
openstack endpoint create --region RegionOne container-infra public http://controller:9511/v1
openstack endpoint create --region RegionOne container-infra internal http://controller:9511/v1
openstack endpoint create --region RegionOne container-infra admin http://controller:9511/v1
```



magnum在管理coe集群时需要其他认证服务

创建magnum包含项目和用户的域

```
openstack domain create --description "Owns users and projects created by magnum" magnum
openstack user create --domain magnum --password-prompt magnum_domain_admin
openstack role add --domain magnum --user-domain magnum --user magnum_domain_admin admin
```





安装和配置组件

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
...
transport_url = rabbit://openstack:openstack@controller
[api]
...
host = 192.168.204.173
[certificates]
...
cert_manager_type = x509keypair

[cinder_client]
...
region_name = RegionOne

[database]
...
connection = mysql+pymysql://magnum:comleader123@controller/magnum
[keystone_authtoken]
...
memcached_servers = controller:11211
auth_version = v3
auth_uri = http://controller:5000/v3
project_domain_id = default
project_name = service
user_domain_id = default
password = comleader123
username = magnum
auth_url = http://controller:35357
auth_type = password
admin_user = magnum
admin_password = comleader123
admin_tenant_name = service

[trust]
...
trustee_domain_name = magnum
trustee_domain_admin_name = magnum_domain_admin
trustee_domain_admin_password = comleader123
trustee_keystone_interface = KEYSTONE_INTERFACE
[oslo_messaging_notifications]
...
driver = messaging
[oslo_concurrency]
...
lock_path = /var/lib/magnum/tmp
```



更新数据库

```
su -s /bin/sh -c "magnum-db-manage upgrade" magnum
```



启动服务

```
systemctl enable openstack-magnum-api.service openstack-magnum-conductor.service
systemctl start openstack-magnum-api.service openstack-magnum-conductor.service
```



验证,状态是up

```
openstack coe service list
```



**<font color=red>验证失败</font>**



创建集群实例

如果没有外部网络，创建一个外部网络

创建密钥对，magnum集群需要

上传集群需要的镜像，此处用k8s和swarm驱动需要的

>The VM versions of Kubernetes and Docker Swarm drivers require a Fedora Atomic image. The following is stock Fedora Atomic image, built by the Atomic team and tested by the Magnum team.

```
$ wget https://download.fedoraproject.org/pub/alt/atomic/stable/Fedora-Atomic-27-20180419.0/CloudImages/x86_64/images/Fedora-Atomic-27-20180419.0.x86_64.qcow2
```

注册到镜像服务器

```
openstack image create \
                      --disk-format=qcow2 \
                      --container-format=bare \
                      --file=Fedora-Atomic-27-20180419.0.x86_64.qcow2\
                      --property os_distro='fedora-atomic' \
                      fedora-atomic-latest
```

配置k8s集群，然后部署

创建集群模板

```
openstack coe cluster template create kubernetes-cluster-template \
                     --image fedora-atomic-latest \
                     --external-network provider \
                     --dns-nameserver 8.8.8.8 \
                     --master-flavor m1.small \
                     --flavor m1.small \
                     --coe kubernetes
```

用秘钥创建master和node节点

```
openstack coe cluster create kubernetes-cluster \
                        --cluster-template kubernetes-cluster-template \
                        --master-count 1 \
                        --node-count 1 \
                        --keypair keyparitestmagnumcluster
```



查看状态

```
openstack coe cluster list
openstack coe cluster show kubernetes-cluster
```



在环境中添加集群认证信息，

```
mkdir -p ~/clusters/kubernetes-cluster
 $(openstack coe cluster config kubernetes-cluster --dir ~/clusters/kubernetes-cluster)
 
```

导出环境变量

```
export KUBECONFIG=/home/user/clusters/kubernetes-cluster/config
```

列出k8s组件，查看状态


```
kubectl -n kube-system get po
```

可以创建nginx然后验证是否运行

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









