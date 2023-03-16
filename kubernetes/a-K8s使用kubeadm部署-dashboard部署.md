# K8s部署



##  一、用 kubeadm 搭建集群环境

### 1.1 架构

上节课我们给大家讲解了 k8s 的基本概念与几个主要的组件，我们在了解了 k8s 的基本概念过后，实际上就可以去正式使用了，但是我们前面的课程都是在 katacoda 上面进行的演示，只提供给我们15分钟左右的使用时间，所以最好的方式还是我们自己来手动搭建一套 k8s 的环境，在搭建环境之前，我们再来看一张更丰富的k8s的架构图。![k8s 架构](.\k8s-structure.jpeg)

- 核心层：Kubernetes 最核心的功能，对外提供 API 构建高层的应用，对内提供插件式应用执行环境
- 应用层：部署（无状态应用、有状态应用、批处理任务、集群应用等）和路由（服务发现、DNS 解析等）
- 管理层：系统度量（如基础设施、容器和网络的度量），自动化（如自动扩展、动态 Provision 等）以及策略管理（RBAC、Quota、PSP、NetworkPolicy 等）
- 接口层：kubectl 命令行工具、客户端 SDK 以及集群联邦
- 生态系统：在接口层之上的庞大容器集群管理调度的生态系统，可以划分为两个范畴
  - Kubernetes 外部：日志、监控、配置管理、CI、CD、Workflow等
  - Kubernetes 内部：CRI、CNI、CVI、镜像仓库、Cloud Provider、集群自身的配置和管理等

我们这里使用的是`kubeadm`工具来进行集群的搭建。

`kubeadm`是`Kubernetes`官方提供的用于快速安装`Kubernetes`集群的工具，通过将集群的各个组件进行容器化安装管理，通过`kubeadm`的方式安装集群比二进制的方式安装要方便不少，但是目录`kubeadm`还处于 beta 状态，还不能用于生产环境，[Using kubeadm to Create a Cluster文档](https://kubernetes.io/docs/setup/independent/create-cluster-kubeadm/)中已经说明 kubeadm 将会很快能够用于生产环境了。对于现阶段想要用于生产环境的，建议还是参考我们前面的文章：[手动搭建高可用的 kubernetes 集群](https://blog.qikqiak.com/post/manual-install-high-available-kubernetes-cluster/)或者[视频教程](https://www.haimaxy.com/course/pjrqxm/?utm_source=k8s)。

### 1.2 基本环境

我们这里准备两台`Centos7`的主机用于安装，后续节点可以根究需要添加即可：

```shell
$ cat /etc/hosts
10.0.0.7 master
10.0.0.8 node01
```

配置nds

/etc/resolve.conf

```
cat > /etc/resolve.conf << EOF
nameserver 8.8.8.8
nameserver 114.114.114.114
EOF
```







禁用防火墙：

```shell
systemctl stop firewalld
systemctl disable firewalld
```

禁用SELINUX：

```shell
# 永久
sed -i 's/enforcing/disabled/' /etc/selinux/config 

# 临时
setenforce 0
```

关闭swap

```
# 临时
swapoff -a  

# 永久
sed -ri 's/.*swap.*/#&/' /etc/fstab
```



创建`/etc/sysctl.d/k8s.conf`文件，添加如下内容：

```shell
cat > /etc/sysctl.d/k8s.conf << EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF

```

执行如下命令使修改生效：

```shell
modprobe br_netfilter
sysctl -p /etc/sysctl.d/k8s.conf
```



配置yum源

```
cp /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.bak
vim  /etc/yum.repos.d/CentOS-Base.repo
```

配置成aliyun的源

```
# CentOS-Base.repo
#
# The mirror system uses the connecting IP address of the client and the
# update status of each mirror to pick mirrors that are updated to and
# geographically close to the client.  You should use this for CentOS updates
# unless you are manually picking other mirrors.
#
# If the mirrorlist= does not work for you, as a fall back you can try the 
# remarked out baseurl= line instead.
#
#
 
[base]
name=CentOS-$releasever - Base - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/os/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/os/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/$releasever/os/$basearch/
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
 
#released updates 
[updates]
name=CentOS-$releasever - Updates - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/updates/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/updates/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/$releasever/updates/$basearch/
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
 
#additional packages that may be useful
[extras]
name=CentOS-$releasever - Extras - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/extras/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/extras/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/$releasever/extras/$basearch/
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
 
#additional packages that extend functionality of existing packages
[centosplus]
name=CentOS-$releasever - Plus - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/centosplus/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/centosplus/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/$releasever/centosplus/$basearch/
gpgcheck=1
enabled=0
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
 
#contrib - packages by Centos Users
[contrib]
name=CentOS-$releasever - Contrib - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/contrib/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/contrib/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/$releasever/contrib/$basearch/
gpgcheck=1
enabled=0
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7

```



```
yum install -y vim wget curl net-tools epel-rel
ease

```











时间同步

```
yum install ntpdate -y
ntpdate time.windows.com
```







### 1.3 安装Docker

安装docker

```awk
wget https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo -O /etc/yum.repos.d/docker-ce.repo 

yum -y install docker-ce-18.06.1.ce-3.el7 

systemctl enable docker && systemctl start docker 

docker --version
```

添加阿里云YUM源

设置仓库地址：[https://help.aliyun.com/docum...](https://link.segmentfault.com/?enc=I4FOWk77s%2Bj9vM%2B6dL5UWQ%3D%3D.EFn2hCzotXO61c1A59Drpmw0Z1CeF0kw483rXGDsbO0vUGhg1eKrGtUefI%2BJ7ChWpQFCrvO%2BRq%2FSjrWQpzOwsA%3D%3D)

```bash
cat > /etc/docker/daemon.json << EOF
{ 
  "registry-mirrors": ["https://xxx.mirror.aliyuncs.com"] 
}
EOF
```

添加 kubernetes.repo 源

```awk
cat > /etc/yum.repos.d/kubernetes.repo << EOF 
[kubernetes] 
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64 
enabled=1 
gpgcheck=0 
epo_gpgcheck=0 
gpgkey=https://mirrors.aliyun.com/kubernetes/yum/doc/yum-key.gpg 
https://mirrors.aliyun.com/kubernetes/yum/doc/rpm-package-key.gpg 
EOF
```

### 1.4 安装kubelet kubeadm kubectl

```apache
yum install -y kubelet-1.18.0 kubeadm-1.18.0 kubectl-1.18.0


systemctl enable kubelet
```

配置swap禁用

```
 cat /etc/sysconfig/kubelet
 
 KUBELET_EXTRA_ARGS="--fail-swap-on=false"
 
 
 
 sudo swapoff -a
```





### 1.5 部署Kubenetes Master

在Master节点执行

```apache
kubeadm init --apiserver-advertise-address=10.0.0.9 --kubernetes-version v1.18.0 --service-cidr=10.96.0.0/12 --pod-network-cidr=10.244.0.0/16


# 未替换image repostory或者image镜像没有在本地时，可以用aliyun仓库

kubeadm init --apiserver-advertise-address=10.0.0.9 --image-repository registry.aliyuncs.com/google_containers --kubernetes-version v1.18.0 --service-cidr=10.96.0.0/12 --pod-network-cidr=10.244.0.0/16

```

得到返回值，其中有如下内容token

```mipsasm
kubeadm join 10.206.0.15:6443 --token iv8baz.f2yagtk257ilmanr 
    --discovery-token-ca-cert-hash sha256:b43a11c9feeab057ee3d6ee91fd7e96dfc75859911f96ff1e89e9578d0801c23 
```

提示使用kubectl工具

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

kubectl get nodes  # (未部署cni时候，节点都是NotReady的状态)
```

### 1.6 安装Node节点

执行kubeadm join

```mipsasm
kubeadm join 10.206.0.15:6443 --token iv8baz.f2yagtk257ilmanr \
    --discovery-token-ca-cert-hash sha256:b43a11c9feeab057ee3d6ee91fd7e96dfc75859911f96ff1e89e9578d0801c23 
```

### 1.7 部署CNI网络插件

在master节点测试

```awk
# 在线方式
wget https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml

#手动拉取镜像
docker pull quay.io/coreos/flannel:v0.14.0

kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
```

本地方式

<a href="#cni-flannel">kube-flannel.yaml文件内容</a> <a name="cni-flannel1">.</a>

```
#手动拉取镜像
docker pull quay.io/coreos/flannel:v0.14.0
kubectl apply -f kube-flannel.yml
```



查看coredns，状态一直ContainerCreating或者，可能是flannel没有配置好

查看/etc/cni/net.d/10-flannel.conflist

```
{
  "name": "cbr0",
  "cniVersion": "0.3.1",
  "plugins": [
    {
      "type": "flannel",
      "delegate": {
        "hairpinMode": true,
        "isDefaultGateway": true
      }
    },
    {
      "type": "portmap",
      "capabilities": {
        "portMappings": true
      }
    }
  ]
}

```











#### 1.7.1 注意

查看flannel 的pod，如果启动失败，后面 nodes节点的状态是NotReady，
需要看coredns是否是pending的状态，如果是，那么flannel部署的有问题。

可能报错1

```
kubectl describe pod coredns-xxxx -n kube-system查看原因

下面错误信息
cni config uninitialized KubeletNotReady runtime network not ready: NetworkReady=false reason:NetworkPluginNotReady message:docker: network plugin is not ready: cni config uninitialized

```

可能报错2

```
kubectl describe node

错误信息
NetworkPluginNotReady message:docker: network plugin is not ready: cni config uninitialized
```

这个时候也许是因为你的node节点中没有安装相应的cni模块。这个时候需要做如下操作:

```
sudo mkdir -p /opt/cni/bin
cd /opt/cni/bin
然后接下来去下载相应的压缩包
https://github.com/containernetworking/plugins/releases/tag/v0.3.0
下载一个cni-plugins-linux-amd64-v0.3.0.tgz
然后将其解压在/opt/cni/bin下就可以了。
```







部署成功

```apache
kubectl get pods -n kube-system

NAME                                 READY   STATUS     RESTARTS   AGE
kube-flannel-ds-2lzv7                0/1     Init:0/1   0          3m9s
kube-flannel-ds-2qh8t                0/1     Init:0/1   0          3m9s
kube-flannel-ds-72fb7                0/1     Init:0/1   0          3m9s
```

节点运行成功

```apache
kubectl get nodes

NAME         STATUS   ROLES    AGE   VERSION
k8s-master   Ready    master   54m   v1.18.0
k8s-node1    Ready    <none>   44m   v1.18.0
k8s-node2    Ready    <none>   44m   v1.18.0
```

### 1.8 测试kubernetes集群

创建一个pod

```pgsql
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80 --type=NodePort
kubectl get pod,svc

NAME                 TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/kubernetes   ClusterIP   10.96.0.1       <none>        443/TCP        148m
service/nginx        NodePort    10.97.184.183   <none>        80:31312/TCP   4s
```

测试访问

```awk
curl http://公网IP:31312
```

![image.png](https://segmentfault.com/img/bVcT9p8)

参考链接：https://segmentfault.com/a/1190000040512911







## 二、搭建 Kubernetes 集群 Dashboard 2.0+ 可视化插件

2022-01-15 141

**简介：** Kubernetes 还开发了一个基于 Web 的 Dashboard，用户可以用 Kubernetes Dashboard 部署容器化的应用、监控应用的状态、执行故障排查任务以及管理 Kubernetes 各种资源。

### 2.1 概述

Kubernetes 还开发了一个基于 Web 的 Dashboard，用户可以用 Kubernetes Dashboard 部署容器化的应用、监控应用的状态、执行故障排查任务以及管理 Kubernetes 各种资源。

Dashboard 的 GitHub 地址：https://github.com/kubernetes/dashboard

### 2.2 系统环境

- Kubernetes 版本：1.18.0
- kubernetes-dashboard 版本：v2.0.2

### 2.3 兼容性

| Kubernetes版本 | 1.13 | 1.14 | 1.15 | 1.16 | 1.17 | 1.18 |
| :------------- | :--- | :--- | :--- | :--- | :--- | :--- |
| 兼容性         | ？   | ？   | ？   | ？   | ?    | ✓    |

- ✕ 不支持的版本范围。
- ✓ 完全支持的版本范围。
- ? 由于Kubernetes API版本之间的重大更改，某些功能可能无法在仪表板中正常运行。

### 2.4 下载安装

#### 2.4.1 在线执行安装recommended

```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.2/aio/deploy/recommended.yaml


以下是console日志
namespace/kubernetes-dashboard created
serviceaccount/kubernetes-dashboard created
service/kubernetes-dashboard created
secret/kubernetes-dashboard-certs created
secret/kubernetes-dashboard-csrf created
secret/kubernetes-dashboard-key-holder created
configmap/kubernetes-dashboard-settings created
role.rbac.authorization.k8s.io/kubernetes-dashboard created
clusterrole.rbac.authorization.k8s.io/kubernetes-dashboard created
rolebinding.rbac.authorization.k8s.io/kubernetes-dashboard created
clusterrolebinding.rbac.authorization.k8s.io/kubernetes-dashboard created
deployment.apps/kubernetes-dashboard created
service/dashboard-metrics-scraper created
deployment.apps/dashboard-metrics-scraper created
```



#### 2.4.2 本地执行安装

（下载yaml文件后编辑后执行）

此种方式可以直接通过修改recommended.yaml配置拉取镜像策略、token有效期、访问方式NodePort及端口，用户密码登录等

- <a href="#recommended">1. 原始recommended.yaml</a> <a name="recommended1">.</a>
- <a href="#nodeport-recommended">2. 修改为NodePort方式并指定端口的recommended.yaml</a> <a name="nodeport-recommended1">.</a>
- <a href="#username-passwd">3. 修改可以用户名密码登录以及token有效期的recommended.yaml</a> <a name="username-passwd1">.</a>



可以看到新版本 Dashboard 集成了一个` metrics-scraper` 的组件，可以通过 Kubernetes 的 Metrics API 收集一些基础资源的监控信息，并在 web 页面上展示，所以要想在页面上展示监控信息就需要提供 Metrics API，前提需要安装 Metrics Server。

新版本的 Dashboard 会被默认安装在 kubernetes-dashboard 这个命名空间下面，查看 pod 名称：

```
$ kubectl get pods --namespace=kubernetes-dashboard -o wide
NAME                                         READY   STATUS    RESTARTS   AGE     IP           NODE        NOMINATED NODE   READINESS GATES
dashboard-metrics-scraper-6b4884c9d5-jdw22   1/1     Running   0          7h42m   10.244.3.3   k8s-node2   <none>           <none>
kubernetes-dashboard-7bfbb48676-l28c9        1/1     Running   0          7h38m   10.244.2.6   k8s-node3   <none>           <none>
```

### 2.5 修改为 NodePort 访问

#### 2.5.1 命令行执行方式

将 dashboard 改为 NodePort 方式访问，不使用 API Server 访问。因为 API Server 访问特别麻烦，一大串，比如：`http://172.16.106.226:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/`

如果是 NodePort 方式访问，就比较简单了，比如：`https://172.16.106.209:32027/`

查看 kubernetes-dashboard：

```
kubectl --namespace=kubernetes-dashboard get service kubernetes-dashboard
$ kubectl --namespace=kubernetes-dashboard get service kubernetes-dashboard
NAME                   TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)         AGE
kubernetes-dashboard   ClusterIP  10.98.194.221   <none>        443/TCP   7h45m
```

编辑 kubernetes-dashboard

```
kubectl --namespace=kubernetes-dashboard edit service kubernetes-dashboard
```

将里面的`type: ClusterIP`改为`type: NodePort`即可。
保存等一会儿，重新查看，就变为 NodePort 了。

```
$ kubectl --namespace=kubernetes-dashboard get service kubernetes-dashboard
NAME                   TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)         AGE
kubernetes-dashboard   NodePort   10.98.194.221   <none>        443:32027/TCP   7h45m
```



#### 2.5.2 配置文件修改方式

要修改的文件及内容参考

<a href="#nodeport-recommended">修改为NodePort方式并指定端口的recommended.yaml</a> <a name="nodeport-recommended1">.</a>





### 2.6 证书管理

Dashboard 安装完成，改为 NodePort 形式之后，通过 `https://172.16.106.209:32027/` 访问，会提示安全信息如下：

![在这里插入图片描述](https://img-blog.csdnimg.cn/e49e9f937949428c9349269d92af03b6.png?x-oss-process=image/watermark,type_d3F5LXplbmhlaQ,shadow_50,text_Q1NETiBAenVvemV3ZWk=,size_20,color_FFFFFF,t_70,g_se,x_16)

这就无法访问了，需要生成证书，这个比较简单，照着下面来就行：

```
#Step 1: 新建目录：
mkdir key && cd key

#Step 2: 生成 SSL 证书
openssl genrsa -out dashboard.key 2048

#Step 3: 我这里写的自己的 node1 节点，因为我是通过 nodeport 访问的；如果通过 apiserver 访问，可以写成自己的 master 节点 ip
openssl req -new -out dashboard.csr -key dashboard.key -subj '/CN=10.0.0.8'
openssl x509 -req -in dashboard.csr -signkey dashboard.key -out dashboard.crt

#Step 4: 删除原有的证书 secret
kubectl delete secret kubernetes-dashboard-certs -n kubernetes-dashboard

#Step 5: 创建新的证书 secret
kubectl create secret generic kubernetes-dashboard-certs --from-file=dashboard.key --from-file=dashboard.crt -n kubernetes-dashboard

#Step 6: 查看 pod
kubectl get pod -n kubernetes-dashboard

#Step 7: 重启 pod
kubectl delete pod kubernetes-dashboard-7b5bf5d559-gn4ls  -n kubernetes-dashboard





sudo kubectl apply -f /home/deploy/recommended.yaml
local_ip=`ifconfig -a|grep inet|grep -v 127.0.0.1 | grep -v 172.17.0.1  |grep -v inet6|awk '{print $2}'|tr -d "addr:"`
sudo mkdir key && cd key
sudo openssl genrsa -out dashboard.key 2048
sudo openssl req -new -out dashboard.csr -key dashboard.key -subj '/CN=$local_ip'
sudo openssl x509 -req -in dashboard.csr -signkey dashboard.key -out dashboard.crt
sudo kubectl delete secret kubernetes-dashboard-certs -n kubernetes-dashboard
sudo kubectl create secret generic kubernetes-dashboard-certs --from-file=dashboard.key --from-file=dashboard.crt -n kubernetes-dashboard
sudo kubectl get pod -n kubernetes-dashboard | grep "kubernetes-dashboard" | awk '{print $1}' | xargs kubectl delete pod  -n kubernetes-dashboard
sudo kubectl create -f /home/deploy/admin-user.yaml
sudo kubectl create -f /home/deploy/admin-user-role-binding.yaml

```

执行完成之后，再次访问点开高级之后，有个继续前往的链接，点击即可：

![图片](https://imgconvert.csdnimg.cn/aHR0cHM6Ly91cGxvYWRlci5zaGltby5pbS9mL1RTYW9LZzA0T3dMQURITU8hdGh1bWJuYWls?x-oss-process=image/format,png)

### 2.7 创建访问的 ServiceAccount

最后需要创建一个绑定 admin 权限的 ServiceAccount，获取其 Token 用于访问看板。

#### 2.7.1 创建用户

新建文件名`admin-user.yaml`，复制下面一段：

```
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kubernetes-dashboard
```

复制到`admin-user.yaml`文件后，执行：`kubectl create -f admin-user.yaml`

#### 2.7.2 绑定用户关系

新建文件`admin-user-role-binding.yaml`：

```
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kubernetes-dashboard
```

复制到 `admin-user-role-binding.yaml` 文件后，执行：`kubectl create -f admin-user-role-binding.yaml`

> 如果过程中提示存在或者需要删除，只需要 `kubectl delete -f` 相应的 yaml 文件即可。

### 2.8 获取令牌

按照官网提示的获取 token 方法：

```
kubectl -n kubernetes-dashboard describe secret $(kubectl -n kubernetes-dashboard get secret | grep admin-user | awk '{print $1}')



Name:         admin-user-token-dzkcw
Namespace:    kubernetes-dashboard
Labels:       <none>
Annotations:  kubernetes.io/service-account.name: admin-user
              kubernetes.io/service-account.uid: 33ae3374-b566-4125-a458-9700a56c205c

Type:  kubernetes.io/service-account-token

Data
====
namespace:  20 bytes
token:      eyJhbGciOiJSUzI1NiIsImtpZCI6IjBhdldZVTdiN3JweVVVUGk2WENETXJRbUFpZEZQSXhwdUV0UFotbnNIVUUifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlcm5ldGVzLWRhc2hib2FyZCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi11c2VyLXRva2VuLWR6a2N3Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImFkbWluLXVzZXIiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiIzM2FlMzM3NC1iNTY2LTQxMjUtYTQ1OC05NzAwYTU2YzIwNWMiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZXJuZXRlcy1kYXNoYm9hcmQ6YWRtaW4tdXNlciJ9.fdR0vrEOk6UQSw9o27ivwEUM7xyz0xHkU8RcgGeBub6ooUnd22dxLxbCwluQIWF6wnABnPp1qeq7ChmLcrQV_yoVDKRQQ4xeL5xFEo_4aPK9x3JIC2AxwsvWD_2UnuoWUdcWo6kryX323LpwHuRGwIp92tTL6rQ8mCZVnZGkP-oiLOA5-2XuP8DsuLPz7EteOg0lAm8ZE_oenDJgYKqHi5wKHZU8RaechyXr4v8WIx-QWoatI6lZfwRWuvctVpjcOh_KOidG3jRZ7PBHlQrw2oxYEl3dkKL28m39H7JzPSTopX-7zE0gRoFt3oZ5flwVwGDp9czMCq2vY1auP62IBQ
ca.crt:     1025 bytes

```

### 2.9 登录新版本 Dashboard 查看

本人的 Kubernetes 集群地址为”10.0.0.7”并且在 Service 中设置了 NodePort 端口为 30022和类型为 NodePort 方式访问 Dashboard ，所以访问地址：`https://10.0.0.8:30022` 进入 Kubernetes Dashboard 页面，然后输入上一步中创建的 ServiceAccount 的 Token 进入 Dashboard，可以看到新的 Dashboard。





### 2.10 配置用户名密码登录

#### 2.10.1 备份

备份kube-apiserver.yaml（重要）

```
cp /etc/kubernetes/manifests/kube-apiserver.yaml  /etc/kubernetes/manifests/kube-apiserver.yaml-bak
```



#### 2.10.2 新增密码

账户admin密码admin，唯一id是1

```
echo "admin,admin,1" > /etc/kubernetes/pki/basic_auth_file

echo "feng.yuqing,fyq@123,2" >> /etc/kubernetes/pki/basic_auth_file
```

每行写一个账号，id不能重复 



#### 2.10.3 修改apiserver.yaml

```
vim /etc/kubernetes/manifests/kube-apiserver.yaml``#加入这一行``- --token-auth-file=/etc/kubernetes/pki/basic_auth_file``#保存退出



具体位置：

spec:
  containers:
  - command:
    - kube-apiserver
    - --advertise-address=192.168.230.41
    - -- .......
    省略......
    - --tls-cert-file=/etc/kubernetes/pki/apiserver.key
    - --token-auth-file=/etc/kubernetes/basic_auth_file # 新增内容
    image: k8s.gcr.io/kube-apiserver:v1.22.4  
    ......
```



#### 2.10.4 查看状态

apiserver.yaml被修改后会自动重启（十秒左右），查看状态有报错

 重启apiserver

```
kubectl apply -f /etc/kubernetes/manifests/kube-apiserver.yaml
 
# 查看
$ kubectl get pod -n kube-system | grep apiserver
kube-apiserver-k8s-01            1/1     Running   0          24s
kube-apiserver-k8s-02            1/1     Running   0          44s
kube-apiserver-k8s-03            1/1     Running   0          50
```



#### 2.10.5 为用户绑定权限

admin绑定权限

```
kubectl create clusterrolebinding login-on-dashboard-with-cluster-admin --clusterrole=cluster-admin --user=admin
```



查看绑定结果

``````
kubectl get clusterrolebinding login-on-dashboard-with-cluster-admin
``````

#### 2.10.6 修改并更新recommended.yaml

参考

<a href="#username-passwd">3. 修改可以用户名密码登录以及token有效期的recommended.yaml</a>

更新

```
kubectl apply -f recommended.yaml
```









### 2.11 使用localhost proxy访问方式



使用原生recommend.yaml文件，不用修改

部署步骤

```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.2/aio/deploy/recommended.yaml

local_ip=`ifconfig -a|grep inet|grep -v 127.0.0.1 | grep -v 172.17.0.1  |grep -v inet6|awk '{print $2}'|tr -d "addr:"`
sudo mkdir key && cd key
sudo openssl genrsa -out dashboard.key 2048
sudo openssl req -new -out dashboard.csr -key dashboard.key -subj '/CN=$local_ip'
sudo openssl x509 -req -in dashboard.csr -signkey dashboard.key -out dashboard.crt
sudo kubectl delete secret kubernetes-dashboard-certs -n kubernetes-dashboard
sudo kubectl create secret generic kubernetes-dashboard-certs --from-file=dashboard.key --from-file=dashboard.crt -n kubernetes-dashboard
sudo kubectl get pod -n kubernetes-dashboard | grep "kubernetes-dashboard" | awk '{print $1}' | xargs kubectl delete pod  -n kubernetes-dashboard
sudo kubectl create -f /home/deploy/admin-user.yaml
sudo kubectl create -f /home/deploy/admin-user-role-binding.yaml


在代理节点命令行执行 
kubectl proxy

在代理节点浏览器(用的火狐浏览器)访问
http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/

获取token进入访问即可
```







### 2.12 使用apiserver方式访问





```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.2/aio/deploy/recommended.yaml

local_ip=`ifconfig -a|grep inet|grep -v 127.0.0.1 | grep -v 172.17.0.1  |grep -v inet6|awk '{print $2}'|tr -d "addr:"`
sudo mkdir key && cd key
sudo openssl genrsa -out dashboard.key 2048
sudo openssl req -new -out dashboard.csr -key dashboard.key -subj '/CN=$local_ip'
sudo openssl x509 -req -in dashboard.csr -signkey dashboard.key -out dashboard.crt
sudo kubectl delete secret kubernetes-dashboard-certs -n kubernetes-dashboard
sudo kubectl create secret generic kubernetes-dashboard-certs --from-file=dashboard.key --from-file=dashboard.crt -n kubernetes-dashboard
sudo kubectl get pod -n kubernetes-dashboard | grep "kubernetes-dashboard" | awk '{print $1}' | xargs kubectl delete pod  -n kubernetes-dashboard
sudo kubectl create -f /home/deploy/admin-user.yaml
sudo kubectl create -f /home/deploy/admin-user-role-binding.yaml



```



直接访问

```
https://masterip:6443/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```



会报错

```
{
  "kind": "Status",
  "apiVersion": "v1",
  "metadata": {

  },
  "status": "Failure",
  "message": "services \"https:kubernetes-dashboard:\" is forbidden: User \"system:anonymous\" cannot get services/proxy in the namespace \"kube-system\"",
  "reason": "Forbidden",
  "details": {
    "name": "https:kubernetes-dashboard:",
    "kind": "services"
  },
  "code": 403
}
```



可以通过以下两种方式解决



#### 2.12.1 用户名密码

```
修改/etc/kubernetes/manifests/kube-apiserver.yaml
增加anonymous-auth=false
  --authorization-mode=Node,RBAC \
  --anonymous-auth=false \

kubectl appy -f /etc/kubernetes/manifests/kube-apiserver.yaml

然后参考配置用户名、密码的部分，配置好后，用用户名密码登录


参考链接：
https://cloud.tencent.com/developer/article/1140064
通过链接中皮质
```



#### 2.12.2 放开anonymous用户权限

```
绑定一个 cluster-admin 的权限

kubectl create clusterrolebinding system:anonymous –clusterrole=cluster-admin –user=system:anonymous

```

直接访问就行





### 2.13 ingress访问方式(nodePort方式)

要求ingress-nginx-controller 的pod所在节点可以直接被访问到

安装ingress-nginx-controller-0.29.0

```
## kubernetes node 上拉取镜像
# docker pull quay.io/kubernetes-ingress-controller/nginx-ingress-controller:0.29.0
# docker pull mirrorgooglecontainers/defaultbackend-amd64:1.5
-    repository: k8s.gcr.io/defaultbackend-amd64

修改ingress-nginx配置
-  hostNetwork: false
+  hostNetwork: true


kubectl apply -f /home/deploy/ingress-nginx-0.29.0.yaml
# ingress-nginx-0.29.0.yaml见附件
```

部署websocket资源，建立后端转发长链接

kubectl apply -f /home/deploy/ingress-websocket.yaml

```
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: websocket
  namespace: default
  annotations:
    nginx.ingress.kuberntetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kuberntetes.io/proxy-rend-timeout: "3600"
    nginx.ingress.kuberntetes.io/proxy-connect-timeout: "3600"
    nginx.ingress.kuberntetes.io/upstream-hash-by: "$http_x_forwarded_for"
spec:
  rules:
    - host: testvipk8s.com
      http:
        paths:
          - backend:
              serviceName: websocket
              servicePort: 8080
            path: /websoket

```





#### 2.13.1 后端dashboard 80端口改动

##### 2.13.1.1 修改/home/deploy/recommended.yaml文件

```
-- a/aio/deploy/recommended.yaml
+++ b/aio/deploy/recommended.yaml
@@ -38,8 +38,12 @@ metadata:
   namespace: kubernetes-dashboard
 spec:
   ports:
-    - port: 443
+    - name: https
+      port: 443
       targetPort: 8443
+    - name: http
+      port: 80
+      targetPort: 9090
   selector:
     k8s-app: kubernetes-dashboard


+ #apiVersion: v1
+ #kind: Secret
+ #metadata:
+ #  labels:
+ #    k8s-app: kubernetes-dashboard
+ #  name: kubernetes-dashboard-certs
+ #  namespace: kubernetes-dashboard
+ #type: Opaque


@@ -188,13 +192,21 @@ spec:
       containers:
         - name: kubernetes-dashboard
-          imagePullPolicy: Always
+          imagePullPolicy: IfNotPresent
           ports:
             - containerPort: 8443
               protocol: TCP
+              name: https
+            - containerPort: 9090
+              protocol: TCP
+              name: http
           args:
-            - --auto-generate-certificates
+            # - --auto-generate-certificates
             - --namespace=kubernetes-dashboard
+            # - --insecure-port=9090
+            # - --port=8443
+            # - --insecure-bind-address=0.0.0.0
+            - --enable-insecure-login
             # Uncomment the following line to manually specify Kubernetes API server Host
             # If not specified, Dashboard will attempt to auto discover the API server and connect
             # to it. Uncomment only if the default does not work.
@@ -207,9 +219,12 @@ spec:
               name: tmp-volume
           livenessProbe:
             httpGet:
-              scheme: HTTPS
+              # scheme: HTTPS
+              # path: /
+              # port: 8443
+              scheme: HTTP
               path: /
-              port: 8443
+              port: 9090
             initialDelaySeconds: 30
             timeoutSeconds: 30
           securityContext:
@@ -272,6 +287,7 @@ spec:
       containers:
         - name: dashboard-metrics-scraper
           image: kubernetesui/metrics-scraper:v1.0.3
+          imagePullPolicy: IfNotPresent
           ports:
             - containerPort: 8000
               protocol: TCP
## 按照上述git对比出来的变化进行修改

```



##### 2.13.1.2 生成自定义域名的自签名证书

```
sudo mkdir $HOME/certs && cd $HOME/certs
sudo openssl genrsa -out dashboard.key 2048
sudo openssl req -new -out dashboard.csr -key dashboard.key -subj '/C=CN/ST=HN/L=ZZ/O=XDWY/OU=zh/CN=testvipk8s.com/emailAddress=yjz01@ieucd.com.cn'
sudo openssl x509 -req -in dashboard.csr -signkey dashboard.key -out dashboard.crt -days 3650
```

##### 2.13.1.3 部署dashboard

```
kubectl create namespace kubernetes-dashboard
sudo kubectl create secret generic kubernetes-dashboard-certs --from-file=$HOME/certs -n kubernetes-dashboard

kubectl apply -f /home/deploy/recommended.yaml
sudo kubectl create -f /home/deploy/admin-user.yaml
sudo kubectl create -f /home/deploy/admin-user-role-binding.yaml

cd $HOME/certs
sudo kubectl create secret tls k8svip --key dashboard.key --cert dashboard.crt -n kubernetes-dashboard
```



##### 2.13.1.4 创建ingress对象到k8s-cluster上

注意backend-protocol使用的是http因为后端服务暴露的是80端口，不是https

```
cat <<EOF > /home/deploy/dashbaord-ingress.yaml
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  name: kubernetes-dashboard
  namespace: kubernetes-dashboard
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTP"
spec:
  tls:
  - hosts:
    - testvipk8s.com
    secretName: kubernetes-dashboard-secret
  rules:
    - host: testvipk8s.com
      http:
        paths:
        - path: /
          backend:
            serviceName: kubernetes-dashboard
            servicePort: 80
EOF


kubectl apply -f /home/deploy/dashbaord-ingress.yaml
```



##### 2.13.1.5 域名映射处理

**本机访问**



```
# kubectl get ingress -n kubernetes-dashboard -o wide
NAME                    CLASS    HOSTS            ADDRESS         PORTS     AGE
k8s-dashboard-ingress   <none>   testvipk8s.com   10.109.236.60   80, 443   49m

## 访问端或者访问端的DNS中配置域名 testvipk8s.com 解析为地址 10.109.236.60 

```



**节点访问**

访问端或者访问端的DNS中配置域名 testvipk8s.com 解析为

将https://testvipk8s.com域名在本地做hosts解析，解析的ip为ingress-controller这个pod所在的node机器外网地址，

##### 2.13.1.6 域名访问

将dashboard.crt导入浏览器

访问域名https://testvipk8s.com，获取token登录







#### 2.13.2 后端dashboard 443端口 

##### 2.13.2.1 修改/home/deploy/recommended.yaml文件

```
在原始2.0.2 recommended.yaml文件基础（已修改镜像下载地址或者本地已有镜像）上，修改内容如下


#apiVersion: v1
#kind: Secret
#metadata:
#  labels:
#    k8s-app: kubernetes-dashboard
#  name: kubernetes-dashboard-certs
#  namespace: kubernetes-dashboard
#type: Opaque


。。。。。。。。
            - name: ACCEPT_LANGUAGE
              value: zh-CN
          args:
            - --auto-generate-certificates
            - --namespace=kubernetes-dashboard
            
            - --tls-cert-file=dashboard.crt
            - --tls-key-file=dashboard.key
            - --token-ttl=43200
。。。。。。。
```



##### 2.13.2.2 生成自定义域名的自签名证书

```
sudo mkdir $HOME/certs && cd $HOME/certs
sudo openssl genrsa -out dashboard.key 2048
sudo openssl req -new -out dashboard.csr -key dashboard.key -subj '/C=CN/ST=HN/L=ZZ/O=XDWY/OU=zh/CN=testvipk8s.com/emailAddress=yjz01@ieucd.com.cn'
sudo openssl x509 -req -in dashboard.csr -signkey dashboard.key -out dashboard.crt -days 3650
```

##### 2.13.2.3 部署dashboard443

```
kubectl create namespace kubernetes-dashboard
sudo kubectl create secret generic kubernetes-dashboard-certs --from-file=$HOME/certs -n kubernetes-dashboard

kubectl apply -f /home/deploy/recommended.yaml
sudo kubectl create -f /home/deploy/admin-user.yaml
sudo kubectl create -f /home/deploy/admin-user-role-binding.yaml

cd $HOME/certs
sudo kubectl create secret tls k8svip --key dashboard.key --cert dashboard.crt -n kubernetes-dashboard
```



##### 2.13.2.4 创建ingress对象到k8s-cluster上

注意backend-protocol使用的是http因为后端服务暴露的是80端口，不是https

```
cat <<EOF > /home/deploy/dashbaord-ingress.yaml
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  name: kubernetes-dashboard
  namespace: kubernetes-dashboard
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
spec:
  tls:
  - hosts:
    - testvipk8s.com
    secretName: kubernetes-dashboard-secret
  rules:
    - host: testvipk8s.com
      http:
        paths:
        - path: /
          backend:
            serviceName: kubernetes-dashboard
            servicePort: 443
EOF

kubectl apply -f /home/deploy/dashbaord-ingress.yaml
```



##### 2.13.2.5 域名映射处理

```
# kubectl get ingress -n kubernetes-dashboard -o wide
NAME                    CLASS    HOSTS            ADDRESS         PORTS     AGE
k8s-dashboard-ingress   <none>   testvipk8s.com   10.109.236.60   80, 443   49m

## 访问端或者访问端的DNS中配置域名 testvipk8s.com 解析为地址 10.109.236.60 

```

##### 2.13.2.6 域名访问

将dashboard.crt导入浏览器

访问域名https://testvipk8s.com，获取token登录



#### 2.13.3 给后端服务配置路径

以dashboard为例，修改ingress创建的dashboard资源

```
cat <<EOF > /home/deploy/dashbaord-ingress.yaml
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  name: kubernetes-dashboard
  namespace: kubernetes-dashboard
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
spec:
  tls:
  - hosts:
    - testvipk8s.com
    secretName: kubernetes-dashboard-secret
  rules:
    - host: testvipk8s.com
      http:
        paths:
        - path: /dashboard(/|$)(.*)
          backend:
            serviceName: kubernetes-dashboard
            servicePort: 443
EOF
```

重新更新kubectl apply -f /home/deploy/dashbaord-ingress.yaml



访问端或者访问端的DNS中配置域名 testvipk8s.com 解析为

将https://testvipk8s.com域名在本地做hosts解析，解析的ip为ingress-controller这个pod所在的node机器外网地址，

访问https://testvipk8s.com/dashboard/即可



### 2.14 ingress访问方式(Daemon方式)

#### 4. DaemonSet+HostNetwork+nodeSelector模式

参考链接：

https://www.cnblogs.com/baoshu/p/13255909.html

要求ingress-nginx-controller 的pod所在节点可以直接被访问到



### 2.15 涉及到的docker镜像

```
registry.aliyuncs.com/google_containers/pause:3.2
registry.aliyuncs.com/google_containers/coredns:1.6.7

quay.io/coreos/flannel:v0.14.0
flannel/flannel-cni-plugin:v1.1.2
flannel/flannel:v0.20.2

registry.aliyuncs.com/google_containers/etcd:3.4.3-0

k8s.gcr.io/kube-scheduler-amd64:v1.10.0
registry.aliyuncs.com/google_containers/kube-scheduler:v1.18.0

k8s.gcr.io/kube-controller-manager-amd64:v1.10.0
registry.aliyuncs.com/google_containers/kube-controller-manager:v1.18.0

k8s.gcr.io/kube-apiserver-amd64:v1.10.0
registry.aliyuncs.com/google_containers/kube-apiserver:v1.18.0

k8s.gcr.io/kube-proxy-amd64:v1.10.0
registry.aliyuncs.com/google_containers/kube-proxy:v1.18.0

kubernetesui/dashboard:v2.0.2
kubernetesui/metrics-scraper:v1.0.4

k8s.gcr.io/heapster-amd64:v1.4.2
k8s.gcr.io/heapster-grafana-amd64:v4.4.3
k8s.gcr.io/heapster-influxdb-amd64:v1.3.3


```







## 三、dashboard-amd:v1.10.0中文部署步骤

>搭建kubeadm1.13版本的k8s和 dashboard-amd64:v1.10.0（中文页面测试）

### 3.1 基本环境

我们这里准备两台`Centos7`的主机用于安装，后续节点可以根究需要添加即可：

```shell
$ cat /etc/hosts
10.0.0.7 master
10.0.0.8 node01
```

配置nds

/etc/resolve.conf

```
cat > /etc/resolve.conf << EOF
nameserver 8.8.8.8
nameserver 114.114.114.114
EOF
```



禁用防火墙：

```shell
systemctl stop firewalld
systemctl disable firewalld
```

禁用SELINUX：

```shell
# 永久
sed -i 's/enforcing/disabled/' /etc/selinux/config 

# 临时
setenforce 0
```

关闭swap

```
# 临时
swapoff -a  

# 永久
sed -ri 's/.*swap.*/#&/' /etc/fstab
```



创建`/etc/sysctl.d/k8s.conf`文件，添加如下内容：

```shell
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
```

执行如下命令使修改生效：

```shell
modprobe br_netfilter
sysctl -p /etc/sysctl.d/k8s.conf
```



配置yum源

```
cp /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.bak
vim  /etc/yum.repos.d/CentOS-Base.repo
```

配置成aliyun的源

```
# CentOS-Base.repo
#
# The mirror system uses the connecting IP address of the client and the
# update status of each mirror to pick mirrors that are updated to and
# geographically close to the client.  You should use this for CentOS updates
# unless you are manually picking other mirrors.
#
# If the mirrorlist= does not work for you, as a fall back you can try the 
# remarked out baseurl= line instead.
#
#
 
[base]
name=CentOS-$releasever - Base - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/os/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/os/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/$releasever/os/$basearch/
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
 
#released updates 
[updates]
name=CentOS-$releasever - Updates - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/updates/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/updates/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/$releasever/updates/$basearch/
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
 
#additional packages that may be useful
[extras]
name=CentOS-$releasever - Extras - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/extras/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/extras/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/$releasever/extras/$basearch/
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
 
#additional packages that extend functionality of existing packages
[centosplus]
name=CentOS-$releasever - Plus - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/centosplus/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/centosplus/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/$releasever/centosplus/$basearch/
gpgcheck=1
enabled=0
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
 
#contrib - packages by Centos Users
[contrib]
name=CentOS-$releasever - Contrib - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/contrib/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/contrib/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/$releasever/contrib/$basearch/
gpgcheck=1
enabled=0
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7

```





时间同步

```
yum install ntpdate -y
ntpdate time.windows.com
```

安装redis

```javascript
yum install epel-release vim gcc curl wget net-tools
yum install -y redis.x86_64
```



### 3.2 安装Docker

安装docker

```awk
wget https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo -O /etc/yum.repos.d/docker-ce.repo 

yum -y install docker-ce-18.06.1.ce-3.el7 

systemctl enable docker && systemctl start docker 

docker --version
```

添加阿里云YUM源

设置仓库地址：[https://help.aliyun.com/docum...](https://link.segmentfault.com/?enc=I4FOWk77s%2Bj9vM%2B6dL5UWQ%3D%3D.EFn2hCzotXO61c1A59Drpmw0Z1CeF0kw483rXGDsbO0vUGhg1eKrGtUefI%2BJ7ChWpQFCrvO%2BRq%2FSjrWQpzOwsA%3D%3D)

```bash
cat > /etc/docker/daemon.json << EOF
{ 
  "registry-mirrors": ["https://xxx.mirror.aliyuncs.com"] 
}
EOF

```

添加 kubernetes.repo 源

```awk
cat > /etc/yum.repos.d/kubernetes.repo << EOF 
[kubernetes] 
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64 
enabled=1 
gpgcheck=0 
epo_gpgcheck=0 
gpgkey=https://mirrors.aliyun.com/kubernetes/yum/doc/yum-key.gpg 
https://mirrors.aliyun.com/kubernetes/yum/doc/rpm-package-key.gpg 
EOF

```

### 3.3 安装kubelet kubeadm kubectl

```
yum install -y kubelet-1.13.1-0 kubectl-1.13.1-0  kubeadm-1.13.1-0

```



### 3.4下载docker镜像

```
docker pull mirrorgooglecontainers/kube-apiserver:v1.13.1
docker pull mirrorgooglecontainers/kube-controller-manager:v1.13.1
docker pull mirrorgooglecontainers/kube-scheduler:v1.13.1
docker pull mirrorgooglecontainers/kube-proxy:v1.13.1
docker pull mirrorgooglecontainers/pause:3.1
docker pull mirrorgooglecontainers/etcd:3.2.24
docker pull coredns/coredns:1.2.6
docker pull registry.cn-shenzhen.aliyuncs.com/cp_m/flannel:v0.10.0-amd64

docker tag mirrorgooglecontainers/kube-apiserver:v1.13.1 k8s.gcr.io/kube-apiserver:v1.13.1
docker tag mirrorgooglecontainers/kube-controller-manager:v1.13.1 k8s.gcr.io/kube-controller-manager:v1.13.1
docker tag mirrorgooglecontainers/kube-scheduler:v1.13.1 k8s.gcr.io/kube-scheduler:v1.13.1
docker tag mirrorgooglecontainers/kube-proxy:v1.13.1 k8s.gcr.io/kube-proxy:v1.13.1
docker tag mirrorgooglecontainers/pause:3.1 k8s.gcr.io/pause:3.1
docker tag mirrorgooglecontainers/etcd:3.2.24 k8s.gcr.io/etcd:3.2.24
docker tag coredns/coredns:1.2.6 k8s.gcr.io/coredns:1.2.6
docker tag registry.cn-shenzhen.aliyuncs.com/cp_m/flannel:v0.10.0-amd64 quay.io/coreos/flannel:v0.10.0-amd64

docker rmi mirrorgooglecontainers/kube-apiserver:v1.13.1           
docker rmi mirrorgooglecontainers/kube-controller-manager:v1.13.1  
docker rmi mirrorgooglecontainers/kube-scheduler:v1.13.1           
docker rmi mirrorgooglecontainers/kube-proxy:v1.13.1               
docker rmi mirrorgooglecontainers/pause:3.1                        
docker rmi mirrorgooglecontainers/etcd:3.2.24                      
docker rmi coredns/coredns:1.2.6
docker rmi registry.cn-shenzhen.aliyuncs.com/cp_m/flannel:v0.10.0-amd64
docker pull registry.cn-qingdao.aliyuncs.com/wangxiaoke/kubernetes-dashboard-amd64:v1.10.0
docker tag registry.cn-qingdao.aliyuncs.com/wangxiaoke/kubernetes-dashboard-amd64:v1.10.0 k8s.gcr.io/kubernetes-dashboard-amd64:v1.10.0
docker image rm registry.cn-qingdao.aliyuncs.com/wangxiaoke/kubernetes-dashboard-amd64:v1.10.0







以下是传到harbor处理过程
# 在外网机上执行
docker tag k8s.gcr.io/kubernetes-dashboard-amd64:v1.10.0 192.168.66.29:80/google_containers/kubernetes-dashboard-amd64:v1.10.0
docker tag k8s.gcr.io/kube-proxy:v1.13.1 192.168.66.29:80/google_containers/kube-proxy:v1.13.1
docker tag k8s.gcr.io/kube-scheduler:v1.13.1 192.168.66.29:80/google_containers/kube-scheduler:v1.13.1
docker tag k8s.gcr.io/kube-apiserver:v1.13.1 192.168.66.29:80/google_containers/kube-apiserver:v1.13.1
docker tag k8s.gcr.io/kube-controller-manager:v1.13.1 192.168.66.29:80/google_containers/kube-controller-manager:v1.13.1
docker tag k8s.gcr.io/coredns:1.2.6 192.168.66.29:80/google_containers/coredns:1.2.6
docker tag k8s.gcr.io/etcd:3.2.24 192.168.66.29:80/google_containers/etcd:3.2.24
docker tag quay.io/coreos/flannel:v0.10.0-amd64 192.168.66.29:80/google_containers/flannel:v0.10.0-amd64
docker tag k8s.gcr.io/pause:3.1 192.168.66.29:80/google_containers/pause:3.1



docker push 192.168.66.29:80/google_containers/kubernetes-dashboard-amd64:v1.10.0
docker push 192.168.66.29:80/google_containers/kube-proxy:v1.13.1
docker push 192.168.66.29:80/google_containers/kube-scheduler:v1.13.1
docker push 192.168.66.29:80/google_containers/kube-apiserver:v1.13.1
docker push 192.168.66.29:80/google_containers/kube-controller-manager:v1.13.1
docker push 192.168.66.29:80/google_containers/coredns:1.2.6
docker push 192.168.66.29:80/google_containers/etcd:3.2.24
docker push 192.168.66.29:80/google_containers/flannel:v0.10.0-amd64
docker push 192.168.66.29:80/google_containers/pause:3.1



# 在虚拟机上执行
docker pull 192.168.66.29:80/google_containers/kubernetes-dashboard-amd64:v1.10.0
docker pull 192.168.66.29:80/google_containers/kube-proxy:v1.13.1
docker pull 192.168.66.29:80/google_containers/kube-scheduler:v1.13.1
docker pull 192.168.66.29:80/google_containers/kube-apiserver:v1.13.1
docker pull 192.168.66.29:80/google_containers/kube-controller-manager:v1.13.1
docker pull 192.168.66.29:80/google_containers/coredns:1.2.6
docker pull 192.168.66.29:80/google_containers/etcd:3.2.24
docker pull 192.168.66.29:80/google_containers/flannel:v0.10.0-amd64
docker pull 192.168.66.29:80/google_containers/pause:3.1


docker tag 192.168.66.29:80/google_containers/kubernetes-dashboard-amd64:v1.10.0  k8s.gcr.io/kubernetes-dashboard-amd64:v1.10.0
docker tag 192.168.66.29:80/google_containers/kube-proxy:v1.13.1 k8s.gcr.io/kube-proxy:v1.13.1
docker tag 192.168.66.29:80/google_containers/kube-scheduler:v1.13.1 k8s.gcr.io/kube-scheduler:v1.13.1
docker tag 192.168.66.29:80/google_containers/kube-apiserver:v1.13.1 k8s.gcr.io/kube-apiserver:v1.13.1
docker tag 192.168.66.29:80/google_containers/kube-controller-manager:v1.13.1 k8s.gcr.io/kube-controller-manager:v1.13.1
docker tag 192.168.66.29:80/google_containers/coredns:1.2.6 k8s.gcr.io/coredns:1.2.6
docker tag 192.168.66.29:80/google_containers/etcd:3.2.24 k8s.gcr.io/etcd:3.2.24
docker tag 192.168.66.29:80/google_containers/flannel:v0.10.0-amd64  quay.io/coreos/flannel:v0.10.0-amd64
docker tag 192.168.66.29:80/google_containers/pause:3.1  k8s.gcr.io/pause:3.1




docker rmi 192.168.66.29:80/google_containers/kubernetes-dashboard-amd64:v1.10.0
docker rmi 192.168.66.29:80/google_containers/kube-proxy:v1.13.1
docker rmi 192.168.66.29:80/google_containers/kube-scheduler:v1.13.1
docker rmi 192.168.66.29:80/google_containers/kube-apiserver:v1.13.1
docker rmi 192.168.66.29:80/google_containers/kube-controller-manager:v1.13.1
docker rmi 192.168.66.29:80/google_containers/coredns:1.2.6
docker rmi 192.168.66.29:80/google_containers/etcd:3.2.24
docker rmi 192.168.66.29:80/google_containers/flannel:v0.10.0-amd64
docker rmi 192.168.66.29:80/google_containers/pause:3.1


```



### 3.5初始化k8s集群(master节点执行)

```
kubeadm init --kubernetes-version=v1.13.1 --apiserver-advertise-address 192.168.230.41 --pod-network-cidr=10.244.0.0/16

```



### 3.6配置kubectl 命令行（master节点执行）

```
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

```

### 3.7 配置flannel

kubectl apply -f kube-flannel.yaml

如果/etc/cni/net.d/10-flannel.conflist没有，需要配置下(所有节点)

```
# kube-flannel.yaml
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: flannel
rules:
  - apiGroups:
      - ""
    resources:
      - pods
    verbs:
      - get
  - apiGroups:
      - ""
    resources:
      - nodes
    verbs:
      - list
      - watch
  - apiGroups:
      - ""
    resources:
      - nodes/status
    verbs:
      - patch
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: flannel
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: flannel
subjects:
- kind: ServiceAccount
  name: flannel
  namespace: kube-system
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: flannel
  namespace: kube-system
---
kind: ConfigMap
apiVersion: v1
metadata:
  name: kube-flannel-cfg
  namespace: kube-system
  labels:
    tier: node
    app: flannel
data:
  cni-conf.json: |
    {
      "name": "cbr0",
      "plugins": [
        {
          "type": "flannel",
          "delegate": {
            "hairpinMode": true,
            "isDefaultGateway": true
          }
        },
        {
          "type": "portmap",
          "capabilities": {
            "portMappings": true
          }
        }
      ]
    }
  net-conf.json: |
    {
      "Network": "10.244.0.0/16",
      "Backend": {
        "Type": "vxlan"
      }
    }
---
apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
  name: kube-flannel-ds-amd64
  namespace: kube-system
  labels:
    tier: node
    app: flannel
spec:
  template:
    metadata:
      labels:
        tier: node
        app: flannel
    spec:
      hostNetwork: true
      nodeSelector:
        beta.kubernetes.io/arch: amd64
      tolerations:
      - operator: Exists
        effect: NoSchedule
      serviceAccountName: flannel
      initContainers:
      - name: install-cni
        image: quay.io/coreos/flannel:v0.10.0-amd64
        command:
        - cp
        args:
        - -f
        - /etc/kube-flannel/cni-conf.json
        - /etc/cni/net.d/10-flannel.conflist
        volumeMounts:
        - name: cni
          mountPath: /etc/cni/net.d
        - name: flannel-cfg
          mountPath: /etc/kube-flannel/
      containers:
      - name: kube-flannel
        image: quay.io/coreos/flannel:v0.10.0-amd64
        command:
        - /opt/bin/flanneld
        args:
        - --ip-masq
        - --kube-subnet-mgr
        resources:
          requests:
            cpu: "100m"
            memory: "50Mi"
          limits:
            cpu: "100m"
            memory: "50Mi"
        securityContext:
          privileged: true
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        volumeMounts:
        - name: run
          mountPath: /run
        - name: flannel-cfg
          mountPath: /etc/kube-flannel/
      volumes:
        - name: run
          hostPath:
            path: /run
        - name: cni
          hostPath:
            path: /etc/cni/net.d
        - name: flannel-cfg
          configMap:
            name: kube-flannel-cfg
---
apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
  name: kube-flannel-ds-arm64
  namespace: kube-system
  labels:
    tier: node
    app: flannel
spec:
  template:
    metadata:
      labels:
        tier: node
        app: flannel
    spec:
      hostNetwork: true
      nodeSelector:
        beta.kubernetes.io/arch: arm64
      tolerations:
      - operator: Exists
        effect: NoSchedule
      serviceAccountName: flannel
      initContainers:
      - name: install-cni
        image: quay.io/coreos/flannel:v0.10.0-arm64
        command:
        - cp
        args:
        - -f
        - /etc/kube-flannel/cni-conf.json
        - /etc/cni/net.d/10-flannel.conflist
        volumeMounts:
        - name: cni
          mountPath: /etc/cni/net.d
        - name: flannel-cfg
          mountPath: /etc/kube-flannel/
      containers:
      - name: kube-flannel
        image: quay.io/coreos/flannel:v0.10.0-arm64
        command:
        - /opt/bin/flanneld
        args:
        - --ip-masq
        - --kube-subnet-mgr
        resources:
          requests:
            cpu: "100m"
            memory: "50Mi"
          limits:
            cpu: "100m"
            memory: "50Mi"
        securityContext:
          privileged: true
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        volumeMounts:
        - name: run
          mountPath: /run
        - name: flannel-cfg
          mountPath: /etc/kube-flannel/
      volumes:
        - name: run
          hostPath:
            path: /run
        - name: cni
          hostPath:
            path: /etc/cni/net.d
        - name: flannel-cfg
          configMap:
            name: kube-flannel-cfg
---
apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
  name: kube-flannel-ds-arm
  namespace: kube-system
  labels:
    tier: node
    app: flannel
spec:
  template:
    metadata:
      labels:
        tier: node
        app: flannel
    spec:
      hostNetwork: true
      nodeSelector:
        beta.kubernetes.io/arch: arm
      tolerations:
      - operator: Exists
        effect: NoSchedule
      serviceAccountName: flannel
      initContainers:
      - name: install-cni
        image: quay.io/coreos/flannel:v0.10.0-arm
        command:
        - cp
        args:
        - -f
        - /etc/kube-flannel/cni-conf.json
        - /etc/cni/net.d/10-flannel.conflist
        volumeMounts:
        - name: cni
          mountPath: /etc/cni/net.d
        - name: flannel-cfg
          mountPath: /etc/kube-flannel/
      containers:
      - name: kube-flannel
        image: quay.io/coreos/flannel:v0.10.0-arm
        command:
        - /opt/bin/flanneld
        args:
        - --ip-masq
        - --kube-subnet-mgr
        resources:
          requests:
            cpu: "100m"
            memory: "50Mi"
          limits:
            cpu: "100m"
            memory: "50Mi"
        securityContext:
          privileged: true
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        volumeMounts:
        - name: run
          mountPath: /run
        - name: flannel-cfg
          mountPath: /etc/kube-flannel/
      volumes:
        - name: run
          hostPath:
            path: /run
        - name: cni
          hostPath:
            path: /etc/cni/net.d
        - name: flannel-cfg
          configMap:
            name: kube-flannel-cfg
---
apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
  name: kube-flannel-ds-ppc64le
  namespace: kube-system
  labels:
    tier: node
    app: flannel
spec:
  template:
    metadata:
      labels:
        tier: node
        app: flannel
    spec:
      hostNetwork: true
      nodeSelector:
        beta.kubernetes.io/arch: ppc64le
      tolerations:
      - operator: Exists
        effect: NoSchedule
      serviceAccountName: flannel
      initContainers:
      - name: install-cni
        image: quay.io/coreos/flannel:v0.10.0-ppc64le
        command:
        - cp
        args:
        - -f
        - /etc/kube-flannel/cni-conf.json
        - /etc/cni/net.d/10-flannel.conflist
        volumeMounts:
        - name: cni
          mountPath: /etc/cni/net.d
        - name: flannel-cfg
          mountPath: /etc/kube-flannel/
      containers:
      - name: kube-flannel
        image: quay.io/coreos/flannel:v0.10.0-ppc64le
        command:
        - /opt/bin/flanneld
        args:
        - --ip-masq
        - --kube-subnet-mgr
        resources:
          requests:
            cpu: "100m"
            memory: "50Mi"
          limits:
            cpu: "100m"
            memory: "50Mi"
        securityContext:
          privileged: true
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        volumeMounts:
        - name: run
          mountPath: /run
        - name: flannel-cfg
          mountPath: /etc/kube-flannel/
      volumes:
        - name: run
          hostPath:
            path: /run
        - name: cni
          hostPath:
            path: /etc/cni/net.d
        - name: flannel-cfg
          configMap:
            name: kube-flannel-cfg
---
apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
  name: kube-flannel-ds-s390x
  namespace: kube-system
  labels:
    tier: node
    app: flannel
spec:
  template:
    metadata:
      labels:
        tier: node
        app: flannel
    spec:
      hostNetwork: true
      nodeSelector:
        beta.kubernetes.io/arch: s390x
      tolerations:
      - operator: Exists
        effect: NoSchedule
      serviceAccountName: flannel
      initContainers:
      - name: install-cni
        image: quay.io/coreos/flannel:v0.10.0-s390x
        command:
        - cp
        args:
        - -f
        - /etc/kube-flannel/cni-conf.json
        - /etc/cni/net.d/10-flannel.conflist
        volumeMounts:
        - name: cni
          mountPath: /etc/cni/net.d
        - name: flannel-cfg
          mountPath: /etc/kube-flannel/
      containers:
      - name: kube-flannel
        image: quay.io/coreos/flannel:v0.10.0-s390x
        command:
        - /opt/bin/flanneld
        args:
        - --ip-masq
        - --kube-subnet-mgr
        resources:
          requests:
            cpu: "100m"
            memory: "50Mi"
          limits:
            cpu: "100m"
            memory: "50Mi"
        securityContext:
          privileged: true
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        volumeMounts:
        - name: run
          mountPath: /run
        - name: flannel-cfg
          mountPath: /etc/kube-flannel/
      volumes:
        - name: run
          hostPath:
            path: /run
        - name: cni
          hostPath:
            path: /etc/cni/net.d
        - name: flannel-cfg
          configMap:
            name: kube-flannel-cfg
```





### 3.8 加入集群（node节点执行）

```
kubeadm join 10.0.0.5:6443 --token ku4h8g.yb3rdsk68jqmzf67 --discovery-token-ca-cert-hash sha256:dcb4516a99c0d5eaae7be5a5e8a9f189e46119e9d9e39aafbee8bfe03a7e86a2

```



### 3.9 配置dashboard-amd64:v1.10.0



kubernetes-dashboard.yaml配置文件如下

kubectl apply -f /home/deploy/kubernetes-dashboard.yaml

```
# Copyright 2017 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# ------------------- Dashboard Secret ------------------- #

apiVersion: v1
kind: Secret
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard-certs
  namespace: kube-system
type: Opaque

---
# ------------------- Dashboard Service Account ------------------- #

apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kube-system

---
# ------------------- Dashboard Role & Role Binding ------------------- #

kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: kubernetes-dashboard-minimal
  namespace: kube-system
rules:
  # Allow Dashboard to create 'kubernetes-dashboard-key-holder' secret.
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["create"]
  # Allow Dashboard to create 'kubernetes-dashboard-settings' config map.
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["create"]
  # Allow Dashboard to get, update and delete Dashboard exclusive secrets.
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["kubernetes-dashboard-key-holder", "kubernetes-dashboard-certs"]
  verbs: ["get", "update", "delete"]
  # Allow Dashboard to get and update 'kubernetes-dashboard-settings' config map.
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["kubernetes-dashboard-settings"]
  verbs: ["get", "update"]
  # Allow Dashboard to get metrics from heapster.
- apiGroups: [""]
  resources: ["services"]
  resourceNames: ["heapster"]
  verbs: ["proxy"]
- apiGroups: [""]
  resources: ["services/proxy"]
  resourceNames: ["heapster", "http:heapster:", "https:heapster:"]
  verbs: ["get"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: kubernetes-dashboard-minimal
  namespace: kube-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: kubernetes-dashboard-minimal
subjects:
- kind: ServiceAccount
  name: kubernetes-dashboard
  namespace: kube-system

---
# ------------------- Dashboard Deployment ------------------- #

kind: Deployment
apiVersion: apps/v1beta2
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kube-system
spec:
  replicas: 1
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      k8s-app: kubernetes-dashboard
  template:
    metadata:
      labels:
        k8s-app: kubernetes-dashboard
    spec:
      containers:
      - name: kubernetes-dashboard
        image: k8s.gcr.io/kubernetes-dashboard-amd64:v1.10.0
        ports:
        - containerPort: 8443
          protocol: TCP
        args:
          - --auto-generate-certificates
          # Uncomment the following line to manually specify Kubernetes API server Host
          # If not specified, Dashboard will attempt to auto discover the API server and connect
          # to it. Uncomment only if the default does not work.
          # - --apiserver-host=http://my-address:port
        volumeMounts:
        - name: kubernetes-dashboard-certs
          mountPath: /certs
          # Create on-disk volume to store exec logs
        - mountPath: /tmp
          name: tmp-volume
        livenessProbe:
          httpGet:
            scheme: HTTPS
            path: /
            port: 8443
          initialDelaySeconds: 30
          timeoutSeconds: 30
      volumes:
      - name: kubernetes-dashboard-certs
        secret:
          secretName: kubernetes-dashboard-certs
      - name: tmp-volume
        emptyDir: {}
      serviceAccountName: kubernetes-dashboard
      # Comment the following tolerations if Dashboard must not be deployed on master
      tolerations:
      - key: node-role.kubernetes.io/master
        effect: NoSchedule

---
# ------------------- Dashboard Service ------------------- #

kind: Service
apiVersion: v1
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kube-system
spec:
  ports:
    - port: 443
      nodePort: 30001
      targetPort: 8443
  type: NodePort
  selector:
    k8s-app: kubernetes-dashboard

```



查看是否创建成功

```
kubectl get pods --namespace=kube-system
```



创建kubernetes-dashboard用户

```
 kubectl create -f admin-user.yaml 
```

```
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: admin
  annotations:
    rbac.authorization.kubernetes.io/autoupdate: "true"
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
subjects:
- kind: ServiceAccount
  name: admin
  namespace: kube-system
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin
  namespace: kube-system
  labels:
    kubernetes.io/cluster-service: "true"
    addonmanager.kubernetes.io/mode: Reconcile
    
```



### 3.10获取token/登录

```
kubectl describe secret $(kubectl get secret -n kube-system |grep admin|awk '{print $1}') -n kube-system|grep '^token'|awk '{print $2}'

```







## 注意事项



### 1. 节点 NotReady

1.1 kubectl describe node 查看信息

参考链接：https://komodor.com/learn/how-to-fix-kubernetes-node-not-ready-error/

发现有报错

```
  Ready            False   Sat, 08 Oct 2022 17:00:01 +0800   Sat, 08 Oct 2022 17:0ady=false reason:NetworkPluginNotReady message:docker: network plugin is not ready

```

参考了这个博客说要关闭 Swap 的限制，链接：https://blog.csdn.net/wzygis/article/details/91366441

具体配置添加如下：

```
[root@k8s-master01 ~]# cat /etc/sysconfig/kubelet  KUBELET_EXTRA_ARGS="--fail-swap-on=false"

```

查看coredns，状态一直ContainerCreating或者，可能是flannel没有配置好

查看/etc/cni/net.d/10-flannel.conflist

```
{
  "name": "cbr0",
  "cniVersion": "0.3.1",
  "plugins": [
    {
      "type": "flannel",
      "delegate": {
        "hairpinMode": true,
        "isDefaultGateway": true
      }
    },
    {
      "type": "portmap",
      "capabilities": {
        "portMappings": true
      }
    }
  ]
}

```









## 四、高可用集群搭建



### 4.1. 配置hostname

除了hostname，还需要准备vip

```
hostnamectl set-hostname k8s-master01

hostnamectl set-hostname k8s-master02

hostnamectl set-hostname k8s-master03

hostnamectl set-hostname  k8s-node01

```



### 4.2.配置hosts

```
cat > /etc/hosts << EOF
10.22.10.199 k8s-master01
10.22.10.80 k8s-master02
10.22.10.86 k8s-master03
10.22.10.137 k8s-node01
127.0.0.1   localhost
EOF

```

### 4.3.配置网络

```
export proxy="http://192.168.66.77:3128"
export http_proxy=$proxy
export https_proxy=$proxy
export ftp_proxy=$proxy
export no_proxy="localhost, 127.0.0.1, ::1"
```



**以下设置参考单节点集群配置**

禁用防火墙

关闭selinux

关闭swap分区

时间同步

**配置ulimt**

```
ulimit -SHn 65535
```

### 4.4. 配置内核参数

```
[root@localhost ~]# cat >> /etc/sysctl.d/k8s.conf << EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
vm.swappiness=0
EOF
[root@localhost ~]# sysctl -p
```





### 4.5. 内核升级

```
wget https://cbs.centos.org/kojifiles/packages/kernel/4.9.220/37.el7/x86_64/kernel-4.9.220-37.el7.x86_64.rpm

yum install -y linux-firmware(>=20140911)
实际安装linux-firmware-20200421
rpm -ivh kernel-4.9.220-37.el7.x86_64.rpm


reboot

uname -r
```





### 4.6 安装ipvs

```
yum install ipvsadm ipset sysstat conntrack libseccomp -y
```

加载模块

```
cat > /etc/sysconfig/modules/ipvs.modules <<EOF
#!/bin/bash
modprobe -- ip_vs
modprobe -- ip_vs_rr
modprobe -- ip_vs_wrr
modprobe -- ip_vs_sh
modprobe -- nf_conntrack_ipv4
modprobe -- ip_tables
modprobe -- ip_set
modprobe -- xt_set
modprobe -- ipt_set
modprobe -- ipt_rpfilter
modprobe -- ipt_REJECT
modprobe -- ipip
EOF

```



注意：在内核4.19版本nf_conntrack_ipv4已经改为nf_conntrack

配置重启自动加载

```
chmod 755 /etc/sysconfig/modules/ipvs.modules && bash /etc/sysconfig/modules/ipvs.modules && lsmod | grep -e ip_vs -e nf_conntrack
```





安装doker-ce



安装kubernetes



### 4.7集群高可用

```
yum install keepalived haproxy -y
```





#### 4.7.1 配置haproxy.cfg

```
#---------------------------------------------------------------------
# Global settings
#---------------------------------------------------------------------
global
    # to have these messages end up in /var/log/haproxy.log you will
    # need to:
    #
    # 1) configure syslog to accept network log events.  This is done
    #    by adding the '-r' option to the SYSLOGD_OPTIONS in
    #    /etc/sysconfig/syslog
    #
    # 2) configure local2 events to go to the /var/log/haproxy.log
    #   file. A line like the following can be added to
    #   /etc/sysconfig/syslog
    #
    #    local2.*                       /var/log/haproxy.log
    #
    log         127.0.0.1 local2
    chroot      /var/lib/haproxy
    pidfile     /var/run/haproxy.pid
    maxconn     4000
    user        haproxy
    group       haproxy
    daemon
    # turn on stats unix socket
    stats socket /var/lib/haproxy/stats
#---------------------------------------------------------------------
# common defaults that all the 'listen' and 'backend' sections will
# use if not designated in their block
#---------------------------------------------------------------------
defaults
    mode                    http
    log                     global
    option                  httplog
    option                  dontlognull
    option http-server-close
    option                  redispatch
    retries                 3
    timeout http-request    10s
    timeout queue           1m
    timeout connect         10s
    timeout client          1m
    timeout server          1m
    timeout http-keep-alive 10s
    timeout check           10s
    maxconn                 3000
#---------------------------------------------------------------------
# kubernetes apiserver frontend which proxys to the backends
#---------------------------------------------------------------------
frontend kubernetes
    mode                 tcp
    bind                 *:16443
    option               tcplog
    default_backend      kubernetes-apiserver
#---------------------------------------------------------------------
# round robin balancing between the various backends
#---------------------------------------------------------------------
backend kubernetes-apiserver
    mode        tcp
    balance     roundrobin
    server  k8s-master01 10.22.10.199:6443 check
    server  k8s-master02 10.22.10.80:6443 check
    server  k8s-master03 10.22.10.86:6443 check

```



#### 4.7.2配置keepalived.conf

master01

```
[root@k8s-master01 ~]# vim /etc/keepalived/keepalived.conf
! Configuration File for keepalived
global_defs {
   notification_email {
     acassen@firewall.loc
     failover@firewall.loc
     sysadmin@firewall.loc
   }
   notification_email_from Alexandre.Cassen@firewall.loc
   smtp_server 127.0.0.1
   smtp_connect_timeout 30
   router_id LVS_DEVEL
   vrrp_skip_check_adv_addr
   vrrp_garp_interval 0
   vrrp_gna_interval 0
}
# 定义脚本
vrrp_script check_apiserver {
    script "/etc/keepalived/check_apiserver.sh"
    interval 2
    weight -5
    fall 3
    rise 2
}
vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 100
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass comleader@123
    }
    virtual_ipaddress {
    10.22.10.254
    }
    # 调用脚本
    #track_script {
    #    check_apiserver
    #}
}
```



master2

```
[root@k8s-master01 ~]# vim /etc/keepalived/keepalived.conf
! Configuration File for keepalived
global_defs {
   notification_email {
     acassen@firewall.loc
     failover@firewall.loc
     sysadmin@firewall.loc
   }
   notification_email_from Alexandre.Cassen@firewall.loc
   smtp_server 127.0.0.1
   smtp_connect_timeout 30
   router_id LVS_DEVEL
   vrrp_skip_check_adv_addr
   vrrp_garp_interval 0
   vrrp_gna_interval 0
}
# 定义脚本
vrrp_script check_apiserver {
    script "/etc/keepalived/check_apiserver.sh"
    interval 2
    weight -5
    fall 3
    rise 2
}
vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 99
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass comleader@123
    }
    virtual_ipaddress {
    10.22.10.254
    }
    # 调用脚本
    #track_script {
    #    check_apiserver
    #}
}
```



master3

```
[root@k8s-master01 ~]# vim /etc/keepalived/keepalived.conf
! Configuration File for keepalived
global_defs {
   notification_email {
     acassen@firewall.loc
     failover@firewall.loc
     sysadmin@firewall.loc
   }
   notification_email_from Alexandre.Cassen@firewall.loc
   smtp_server 127.0.0.1
   smtp_connect_timeout 30
   router_id LVS_DEVEL
   vrrp_skip_check_adv_addr
   vrrp_garp_interval 0
   vrrp_gna_interval 0
}
# 定义脚本
vrrp_script check_apiserver {
    script "/etc/keepalived/check_apiserver.sh"
    interval 2
    weight -5
    fall 3
    rise 2
}
vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 98
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass comleader@123
    }
    virtual_ipaddress {
    10.22.10.254
    }
    # 调用脚本
    #track_script {
    #    check_apiserver
    #}
}

```



健康检查脚本

```
[root@k8s-master01 ~]# vim /etc/keepalived/check-apiserver.sh
#!/bin/bash
function check_apiserver(){
 for ((i=0;i<5;i++))
 do
  apiserver_job_id=${pgrep kube-apiserver}
  if [[ ! -z ${apiserver_job_id} ]];then
   return
  else
   sleep 2
  fi
  apiserver_job_id=0
 done
}
# 1->running    0->stopped
check_apiserver
if [[ $apiserver_job_id -eq 0 ]];then
 /usr/bin/systemctl stop keepalived
 exit 1
else
 exit 0
fi
```



#### 4.7.3 启动

```
systemctl enable --now keepalived haproxy
systemctl start keepalived haproxy
systemctl status keepalived haproxy

```



```
cat >> kubeadm.yaml <<EOF
apiVersion: kubeadm.k8s.io/v1beta2
kind: ClusterConfiguration
kubernetesVersion: v1.18.0
imageRepository: k8s.gcr.io
controlPlaneEndpoint: "10.22.10.254:16443"
networking:
  dnsDomain: cluster.local
  podSubnet: 10.244.0.0/16
  serviceSubnet: 10.96.0.0/12
---
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
featureGates:
  SupportIPVSProxyMode: true
mode: ipvs
EOF
```





### 4.8 启动k8s服务

```
kubeadm init --config kubeadm.yaml --upload-certs
```



kubeadm.yaml配置如下

```
apiVersion: kubeadm.k8s.io/v1beta2
kind: ClusterConfiguration
kubernetesVersion: v1.18.0
imageRepository: k8s.gcr.io
controlPlaneEndpoint: "vip:16443"
networking:
  dnsDomain: cluster.local
  podSubnet: 10.244.0.0/16
  serviceSubnet: 10.96.0.0/12
---
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
featureGates:
  SupportIPVSProxyMode: true
mode: ipvs

```











```
# master加入cluster
kubeadm join 10.22.10.254:16443 --token q1242k.7udwnyy7pk8zyljr --discovery-token-ca-cert-hash sha256:3130fea56b3ab36ea8bb606a26da6d049c51226a1e862ce59ff9d0ab0f61960b --control-plane --certificate-key fb90dca1614c9483aeb962de3972bc3ffae6b1d472eabc640ca1bf94f7d9a17d

    
    
# worker 加入master 
kubeadm join 10.22.10.254:16443 --token q1242k.7udwnyy7pk8zyljr --discovery-token-ca-cert-hash sha256:3130fea56b3ab36ea8bb606a26da6d049c51226a1e862ce59ff9d0ab0f61960b




如果token 和cert过期，重新生成后，组合使用

在master1上重新生成token和cert：
# kubeadm init phase upload-certs --upload-certs
W0514 13:22:23.433664     656 configset.go:202] WARNING: kubeadm cannot validate component configs for API groups [kubelet.config.k8s.io kubeproxy.config.k8s.io]
[upload-certs] Storing the certificates in Secret "kubeadm-certs" in the "kube-system" Namespace
[upload-certs] Using certificate key:
b55acff8cd105fe152c7de6e49372f9ccde71fc74bdf6ec22a08feaf9f00eba4

# kubeadm token create --print-join-command
W0514 13:22:41.748101     955 configset.go:202] WARNING: kubeadm cannot validate component configs for API groups [kubelet.config.k8s.io kubeproxy.config.k8s.io]
kubeadm join apiserver-lb:6443 --token 1iznqy.ulvp986lej4zcace     --discovery-token-ca-

```



### 4.9测试集群

```
curl  https://masterip:6443/version -k
{
  "major": "1",
  "minor": "18",
  "gitVersion": "v1.18.0",
  "gitCommit": "52c56ce7a8272c798dbc29846288d7cd9fbae032",
  "gitTreeState": "clean",
  "buildDate": "2020-04-16T11:48:36Z",
  "goVersion": "go1.13.9",
  "compiler": "gc",
  "platform": "linux/amd64"
```







## 末、附录及配置文件



### 1.原始recommended文件

<a name="recommended"> 原始recommended.yaml文件</a> <a href="#recommended1">返回2.4.2章节</a>

修改了kubernetes-dashboard拉取镜像的方式（原始是always），

改成imagePullPolicy: IfNotPresent

```
# Copyright 2017 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

apiVersion: v1
kind: Namespace
metadata:
  name: kubernetes-dashboard

---

apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kubernetes-dashboard

---

kind: Service
apiVersion: v1
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kubernetes-dashboard
spec:
  ports:
    - port: 443
      targetPort: 8443
  selector:
    k8s-app: kubernetes-dashboard

---

apiVersion: v1
kind: Secret
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard-certs
  namespace: kubernetes-dashboard
type: Opaque

---

apiVersion: v1
kind: Secret
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard-csrf
  namespace: kubernetes-dashboard
type: Opaque
data:
  csrf: ""

---

apiVersion: v1
kind: Secret
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard-key-holder
  namespace: kubernetes-dashboard
type: Opaque

---

kind: ConfigMap
apiVersion: v1
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard-settings
  namespace: kubernetes-dashboard

---

kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kubernetes-dashboard
rules:
  # Allow Dashboard to get, update and delete Dashboard exclusive secrets.
  - apiGroups: [""]
    resources: ["secrets"]
    resourceNames: ["kubernetes-dashboard-key-holder", "kubernetes-dashboard-certs", "kubernetes-dashboard-csrf"]
    verbs: ["get", "update", "delete"]
    # Allow Dashboard to get and update 'kubernetes-dashboard-settings' config map.
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["kubernetes-dashboard-settings"]
    verbs: ["get", "update"]
    # Allow Dashboard to get metrics.
  - apiGroups: [""]
    resources: ["services"]
    resourceNames: ["heapster", "dashboard-metrics-scraper"]
    verbs: ["proxy"]
  - apiGroups: [""]
    resources: ["services/proxy"]
    resourceNames: ["heapster", "http:heapster:", "https:heapster:", "dashboard-metrics-scraper", "http:dashboard-metrics-scraper"]
    verbs: ["get"]

---

kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
rules:
  # Allow Metrics Scraper to get metrics from the Metrics server
  - apiGroups: ["metrics.k8s.io"]
    resources: ["pods", "nodes"]
    verbs: ["get", "list", "watch"]

---

apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kubernetes-dashboard
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: kubernetes-dashboard
subjects:
  - kind: ServiceAccount
    name: kubernetes-dashboard
    namespace: kubernetes-dashboard

---

apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: kubernetes-dashboard
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: kubernetes-dashboard
subjects:
  - kind: ServiceAccount
    name: kubernetes-dashboard
    namespace: kubernetes-dashboard

---

kind: Deployment
apiVersion: apps/v1
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kubernetes-dashboard
spec:
  replicas: 1
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      k8s-app: kubernetes-dashboard
  template:
    metadata:
      labels:
        k8s-app: kubernetes-dashboard
    spec:
      containers:
        - name: kubernetes-dashboard
          image: kubernetesui/dashboard:v2.0.2
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8443
              protocol: TCP
          args:
            - --auto-generate-certificates
            - --namespace=kubernetes-dashboard
            - --token-ttl=43200
            # Uncomment the following line to manually specify Kubernetes API server Host
            # If not specified, Dashboard will attempt to auto discover the API server and connect
            # to it. Uncomment only if the default does not work.
            # - --apiserver-host=http://my-address:port
          volumeMounts:
            - name: kubernetes-dashboard-certs
              mountPath: /certs
              # Create on-disk volume to store exec logs
            - mountPath: /tmp
              name: tmp-volume
          livenessProbe:
            httpGet:
              scheme: HTTPS
              path: /
              port: 8443
            initialDelaySeconds: 30
            timeoutSeconds: 30
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            runAsUser: 1001
            runAsGroup: 2001
      volumes:
        - name: kubernetes-dashboard-certs
          secret:
            secretName: kubernetes-dashboard-certs
        - name: tmp-volume
          emptyDir: {}
      serviceAccountName: kubernetes-dashboard
      nodeSelector:
        "kubernetes.io/os": linux
      # Comment the following tolerations if Dashboard must not be deployed on master
      tolerations:
        - key: node-role.kubernetes.io/master
          effect: NoSchedule

---

kind: Service
apiVersion: v1
metadata:
  labels:
    k8s-app: dashboard-metrics-scraper
  name: dashboard-metrics-scraper
  namespace: kubernetes-dashboard
spec:
  ports:
    - port: 8000
      targetPort: 8000
  selector:
    k8s-app: dashboard-metrics-scraper

---

kind: Deployment
apiVersion: apps/v1
metadata:
  labels:
    k8s-app: dashboard-metrics-scraper
  name: dashboard-metrics-scraper
  namespace: kubernetes-dashboard
spec:
  replicas: 1
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      k8s-app: dashboard-metrics-scraper
  template:
    metadata:
      labels:
        k8s-app: dashboard-metrics-scraper
      annotations:
        seccomp.security.alpha.kubernetes.io/pod: 'runtime/default'
    spec:
      containers:
        - name: dashboard-metrics-scraper
          image: kubernetesui/metrics-scraper:v1.0.4
          ports:
            - containerPort: 8000
              protocol: TCP
          livenessProbe:
            httpGet:
              scheme: HTTP
              path: /
              port: 8000
            initialDelaySeconds: 30
            timeoutSeconds: 30
          volumeMounts:
          - mountPath: /tmp
            name: tmp-volume
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            runAsUser: 1001
            runAsGroup: 2001
      serviceAccountName: kubernetes-dashboard
      nodeSelector:
        "kubernetes.io/os": linux
      # Comment the following tolerations if Dashboard must not be deployed on master
      tolerations:
        - key: node-role.kubernetes.io/master
          effect: NoSchedule
      volumes:
        - name: tmp-volume
          emptyDir: {}

```





### 2.修改为NodePort方式

<a name="nodeport-recommended"> 修改为NodePort方式并指定端口的recommended.yaml</a> <a href="#nodeport-recommended1">返回2.4.2章节</a>

```
# 下面展示的是主要区别，不是全部文件内容


上面省略
.......
kind: Service
apiVersion: v1
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kubernetes-dashboard
spec:
  type: NodePort  # 新增类型
  ports:
    - port: 443
      nodeport: 30001  # 新增端口
      targetPort: 8443
  selector:
    k8s-app: kubernetes-dashboard

下面省略
.......
```



### 3.修改登录方式及token有效期(用户密码)

<a name="username-passwd"> 修改用户名密码登录的recommended.yaml</a> <a href="#username-passwd1">返回2.4.2章节</a>

```
# 下面展示的是主要区别，不是全部文件内容


上面省略
.......

    spec:
      containers:
        - name: kubernetes-dashboard
          image: kubernetesui/dashboard:v2.0.2
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8443
              protocol: TCP
          args:
            - --auto-generate-certificates
            - --namespace=kubernetes-dashboard
            - --token-ttl=43200   # 新增token有效期
            - --authentication-mode=basic   # 配置用户名密码登录


下面省略
.......
```



### 4.flannel配置

<a name="cni-flannel"> kube-flannel.yaml文件内容</a> <a href="#cni-flannel1">返回1.7章节</a>

```
---
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: psp.flannel.unprivileged
  annotations:
    seccomp.security.alpha.kubernetes.io/allowedProfileNames: docker/default
    seccomp.security.alpha.kubernetes.io/defaultProfileName: docker/default
    apparmor.security.beta.kubernetes.io/allowedProfileNames: runtime/default
    apparmor.security.beta.kubernetes.io/defaultProfileName: runtime/default
spec:
  privileged: false
  volumes:
  - configMap
  - secret
  - emptyDir
  - hostPath
  allowedHostPaths:
  - pathPrefix: "/etc/cni/net.d"
  - pathPrefix: "/etc/kube-flannel"
  - pathPrefix: "/run/flannel"
  readOnlyRootFilesystem: false
  # Users and groups
  runAsUser:
    rule: RunAsAny
  supplementalGroups:
    rule: RunAsAny
  fsGroup:
    rule: RunAsAny
  # Privilege Escalation
  allowPrivilegeEscalation: false
  defaultAllowPrivilegeEscalation: false
  # Capabilities
  allowedCapabilities: ['NET_ADMIN', 'NET_RAW']
  defaultAddCapabilities: []
  requiredDropCapabilities: []
  # Host namespaces
  hostPID: false
  hostIPC: false
  hostNetwork: true
  hostPorts:
  - min: 0
    max: 65535
  # SELinux
  seLinux:
    # SELinux is unused in CaaSP
    rule: 'RunAsAny'
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: flannel
rules:
- apiGroups: ['extensions']
  resources: ['podsecuritypolicies']
  verbs: ['use']
  resourceNames: ['psp.flannel.unprivileged']
- apiGroups:
  - ""
  resources:
  - pods
  verbs:
  - get
- apiGroups:
  - ""
  resources:
  - nodes
  verbs:
  - list
  - watch
- apiGroups:
  - ""
  resources:
  - nodes/status
  verbs:
  - patch
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: flannel
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: flannel
subjects:
- kind: ServiceAccount
  name: flannel
  namespace: kube-system
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: flannel
  namespace: kube-system
---
kind: ConfigMap
apiVersion: v1
metadata:
  name: kube-flannel-cfg
  namespace: kube-system
  labels:
    tier: node
    app: flannel
data:
  cni-conf.json: |
    {
      "name": "cbr0",
      "cniVersion": "0.3.1",
      "plugins": [
        {
          "type": "flannel",
          "delegate": {
            "hairpinMode": true,
            "isDefaultGateway": true
          }
        },
        {
          "type": "portmap",
          "capabilities": {
            "portMappings": true
          }
        }
      ]
    }
  net-conf.json: |
    {
      "Network": "10.244.0.0/16",
      "Backend": {
        "Type": "vxlan"
      }
    }
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: kube-flannel-ds
  namespace: kube-system
  labels:
    tier: node
    app: flannel
spec:
  selector:
    matchLabels:
      app: flannel
  template:
    metadata:
      labels:
        tier: node
        app: flannel
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/os
                operator: In
                values:
                - linux
      hostNetwork: true
      priorityClassName: system-node-critical
      tolerations:
      - operator: Exists
        effect: NoSchedule
      serviceAccountName: flannel
      initContainers:
      - name: install-cni
        image: quay.io/coreos/flannel:v0.14.0
        command:
        - cp
        args:
        - -f
        - /etc/kube-flannel/cni-conf.json
        - /etc/cni/net.d/10-flannel.conflist
        volumeMounts:
        - name: cni
          mountPath: /etc/cni/net.d
        - name: flannel-cfg
          mountPath: /etc/kube-flannel/
      containers:
      - name: kube-flannel
        image: quay.io/coreos/flannel:v0.14.0
        command:
        - /opt/bin/flanneld
        args:
        - --ip-masq
        - --kube-subnet-mgr
        resources:
          requests:
            cpu: "100m"
            memory: "50Mi"
          limits:
            cpu: "100m"
            memory: "50Mi"
        securityContext:
          privileged: false
          capabilities:
            add: ["NET_ADMIN", "NET_RAW"]
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        volumeMounts:
        - name: run
          mountPath: /run/flannel
        - name: flannel-cfg
          mountPath: /etc/kube-flannel/
      volumes:
      - name: run
        hostPath:
          path: /run/flannel
      - name: cni
        hostPath:
          path: /etc/cni/net.d
      - name: flannel-cfg
        configMap:
          name: kube-flannel-cfg

```





### 5. Ingress-nginx-0.29.0.yaml配置文件



```
apiVersion: v1
kind: Namespace
metadata:
  name: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
---
kind: ConfigMap
apiVersion: v1
metadata:
  name: nginx-configuration
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
---
kind: ConfigMap
apiVersion: v1
metadata:
  name: tcp-services
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
---
kind: ConfigMap
apiVersion: v1
metadata:
  name: udp-services
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
---
apiVersion: apps/v1
kind: Deployment
#kind: Daemonset
metadata:
  name: default-http-backend
  labels:
    app: default-http-backend
  namespace: ingress-nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app: default-http-backend
  template:
    metadata:
      labels:
       app: default-http-backend
    spec:
      terminationGracePeriodSeconds: 60
      containers:
      - name: default-http-backend
        image:  192.168.66.29:80/google_containers/defaultbackend-amd64:1.5      #建议提前在node节点下载镜像；
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 30
          timeoutSeconds: 5
        ports:
        - containerPort: 8080
        resources:
         # 这里调整了cpu和memory的大小，可能不同集群限制的最小值不同，看部署失败的原因就清楚
          limits:
            cpu: 100m
            memory: 100Mi
          requests:
            cpu: 100m
            memory: 100Mi
---
apiVersion: v1
kind: Service
metadata:
  name: default-http-backend
  # namespace: ingress-nginx
  namespace: ingress-nginx
  labels:
    app: default-http-backend
spec:
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: default-http-backend
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: nginx-ingress-serviceaccount
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRole
metadata:
  name: nginx-ingress-clusterrole
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
rules:
  - apiGroups:
      - ""
    resources:
      - configmaps
      - endpoints
      - nodes
      - pods
      - secrets
    verbs:
      - list
      - watch
  - apiGroups:
      - ""
    resources:
      - nodes
    verbs:
      - get
  - apiGroups:
      - ""
    resources:
      - services
    verbs:
      - get
      - list
      - watch
  - apiGroups:
      - ""
    resources:
      - events
    verbs:
      - create
      - patch
  - apiGroups:
      - "extensions"
      - "networking.k8s.io"
    resources:
      - ingresses
    verbs:
      - get
      - list
      - watch
  - apiGroups:
      - "extensions"
      - "networking.k8s.io"
    resources:
      - ingresses/status
    verbs:
      - update
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: Role
metadata:
  name: nginx-ingress-role
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
rules:
  - apiGroups:
      - ""
    resources:
      - configmaps
      - pods
      - secrets
      - namespaces
    verbs:
      - get
  - apiGroups:
      - ""
    resources:
      - configmaps
    resourceNames:
      # Defaults to "<election-id>-<ingress-class>"
      # Here: "<ingress-controller-leader>-<nginx>"
      # This has to be adapted if you change either parameter
      # when launching the nginx-ingress-controller.
      - "ingress-controller-leader-nginx"
    verbs:
      - get
      - update
  - apiGroups:
      - ""
    resources:
      - configmaps
    verbs:
      - create
  - apiGroups:
      - ""
    resources:
      - endpoints
    verbs:
      - get
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: RoleBinding
metadata:
  name: nginx-ingress-role-nisa-binding
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: nginx-ingress-role
subjects:
  - kind: ServiceAccount
    name: nginx-ingress-serviceaccount
    namespace: ingress-nginx
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: nginx-ingress-clusterrole-nisa-binding
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: nginx-ingress-clusterrole
subjects:
  - kind: ServiceAccount
    name: nginx-ingress-serviceaccount
    namespace: ingress-nginx
---
apiVersion: apps/v1
kind: Deployment
#kind: DaemonSet
metadata:
  name: nginx-ingress-controller
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: ingress-nginx
      app.kubernetes.io/part-of: ingress-nginx
  template:
    metadata:
      labels:
        app.kubernetes.io/name: ingress-nginx
        app.kubernetes.io/part-of: ingress-nginx
      annotations:
        prometheus.io/port: "10254"
        prometheus.io/scrape: "true"
    spec:
      # wait up to five minutes for the drain of connections
      hostNetwork: true
      terminationGracePeriodSeconds: 300
      serviceAccountName: nginx-ingress-serviceaccount
      nodeSelector:
        kubernetes.io/os: linux
      containers:
        - name: nginx-ingress-controller
          image: 192.168.66.29:80/google_containers/nginx-ingress-controller:0.29.0   #建议提前在node节点下载镜像；
          args:
            - /nginx-ingress-controller
            - --default-backend-service=$(POD_NAMESPACE)/default-http-backend
            - --configmap=$(POD_NAMESPACE)/nginx-configuration
            - --tcp-services-configmap=$(POD_NAMESPACE)/tcp-services
            - --udp-services-configmap=$(POD_NAMESPACE)/udp-services
            - --publish-service=$(POD_NAMESPACE)/ingress-nginx
            - --annotations-prefix=nginx.ingress.kubernetes.io
          securityContext:
            allowPrivilegeEscalation: true
            capabilities:
              drop:
                - ALL
              add:
                - NET_BIND_SERVICE
            # www-data -> 101
            runAsUser: 101
          env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: POD_NAMESPACE
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
          ports:
            - name: http
              containerPort: 80
              protocol: TCP
            - name: https
              containerPort: 443
              protocol: TCP
          livenessProbe:
            failureThreshold: 3
            httpGet:
              path: /healthz
              port: 10254
              scheme: HTTP
            initialDelaySeconds: 10
            periodSeconds: 10
            successThreshold: 1
            timeoutSeconds: 10
          readinessProbe:
            failureThreshold: 3
            httpGet:
              path: /healthz
              port: 10254
              scheme: HTTP
            periodSeconds: 10
            successThreshold: 1
            timeoutSeconds: 10
          lifecycle:
            preStop:
              exec:
                command:
                  - /wait-shutdown
---
apiVersion: v1
kind: LimitRange
metadata:
  name: ingress-nginx
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
spec:
  limits:
  - min:
      memory: 90Mi
      cpu: 100m
    type: Container
---
apiVersion: v1
kind: Service
metadata:
  name: ingress-nginx
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
spec:
  type: NodePort
  ports:
    - name: http
      port: 80
      targetPort: 80
      protocol: TCP
      nodePort: 32080
    - name: https
      port: 443
      targetPort: 443
      protocol: TCP
      nodePort: 32443
  selector:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx


```





