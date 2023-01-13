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

禁用防火墙：

```shell
$ systemctl stop firewalld
$ systemctl disable firewalld
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
$ modprobe br_netfilter
$ sysctl -p /etc/sysctl.d/k8s.conf
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

添加 yum 源

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

### 1.5 部署Kubenetes Master

在Master节点执行

```apache
kubeadm init --apiserver-advertise-address=10.206.0.15 --image-repository registry.aliyuncs.com/google_containers --kubernetes-version v1.18.0 --service-cidr=10.96.0.0/12 --pod-network-cidr=10.244.0.0/16
```

得到token

```mipsasm
kubeadm join 10.206.0.15:6443 --token iv8baz.f2yagtk257ilmanr \
    --discovery-token-ca-cert-hash sha256:b43a11c9feeab057ee3d6ee91fd7e96dfc75859911f96ff1e89e9578d0801c23 
```

提示使用kubectl工具

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

kubectl get nodes
```

### 1.6 安装Node节点

执行kubeadm join

```mipsasm
kubeadm join 10.206.0.15:6443 --token iv8baz.f2yagtk257ilmanr \
    --discovery-token-ca-cert-hash sha256:b43a11c9feeab057ee3d6ee91fd7e96dfc75859911f96ff1e89e9578d0801c23 
```

### 1.7 部署CNI网络插件

```awk
wget https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml

#手动拉取镜像
docker pull quay.io/coreos/flannel:v0.14.0

kubectl apply -f kube-flannel.yml
```

**注意**

查看flannel 的pod，如果启动失败，后面 nodes的状态是NotReady

需要看











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

- Kubernetes 版本：1.18.5
- kubernetes-dashboard 版本：v2.0.3

### 2.3 兼容性

| Kubernetes版本 | 1.13 | 1.14 | 1.15 | 1.16 | 1.17 | 1.18 |
| :------------- | :--- | :--- | :--- | :--- | :--- | :--- |
| 兼容性         | ？   | ？   | ？   | ？   | ?    | ✓    |

- ✕ 不支持的版本范围。
- ✓ 完全支持的版本范围。
- ? 由于Kubernetes API版本之间的重大更改，某些功能可能无法在仪表板中正常运行。

### 2.4 下载安装

执行安装:（网上下载方式）

```
$ kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.2/aio/deploy/recommended.yaml


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



执行安装:（下载yaml文件后编辑后执行）

此种方式可以直接通过修改recommended.yaml配置NodePort，端口，用户密码登录等





可以看到新版本 Dashboard 集成了一个` metrics-scraper` 的组件，可以通过 Kubernetes 的 Metrics API 收集一些基础资源的监控信息，并在 web 页面上展示，所以要想在页面上展示监控信息就需要提供 Metrics API，前提需要安装 Metrics Server。

新版本的 Dashboard 会被默认安装在 kubernetes-dashboard 这个命名空间下面，查看 pod 名称：

```
$ kubectl get pods --namespace=kubernetes-dashboard -o wide
NAME                                         READY   STATUS    RESTARTS   AGE     IP           NODE        NOMINATED NODE   READINESS GATES
dashboard-metrics-scraper-6b4884c9d5-jdw22   1/1     Running   0          7h42m   10.244.3.3   k8s-node2   <none>           <none>
kubernetes-dashboard-7bfbb48676-l28c9        1/1     Running   0          7h38m   10.244.2.6   k8s-node3   <none>           <none>
```

### 2.5 修改为 NodePort 访问

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





### 2.10 配置用户名密码

A。备份kube-apiserver.yaml（重要）

```
cp /etc/kubernetes/manifests/kube-apiserver.yaml  /etc/kubernetes/manifests/kube-apiserver.yaml-bak
```



B。新增密码

账户admin密码admin，唯一id是1

```
echo "admin,admin,1" > /etc/kubernetes/pki/basic_auth_file

echo "feng.yuqing,fyq@123,2" >> /etc/kubernetes/pki/basic_auth_file
```

每行写一个账号，id不能重复 



修改apiserver.yaml



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
    - --token-auth-file=/etc/kubernetes/basic_auth_file
    image: k8s.gcr.io/kube-apiserver:v1.22.4
    ......
```



D。查看状态

apiserver.yaml被修改后会自动重启（十秒左右），查看状态有报错

 

E。为admin/fengyuqing用户绑定权限

# admin绑定权限

kubectl create clusterrolebinding login-on-dashboard-with-cluster-admin --clusterrole=cluster-admin --user=admin

# 查看绑定结果

kubectl get clusterrolebinding login-on-dashboard-with-cluster-admin

F。修改recommended.yaml

recommended.yaml 是dashboard相关部署文件。











## 注意事项



### 1. 节点 NotReady

kubectl describe node 查看信息

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



还有可能是flannel没有配置好，

提示

















