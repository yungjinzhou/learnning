# K8s部署

##  基本概念与组件

### 基本概念

Kubernetes 中的绝大部分概念都抽象成 Kubernetes 管理的一种资源对象，下面我们一起复习一下我们上节课遇到的一些资源对象：

- Master：Master 节点是 Kubernetes 集群的控制节点，负责整个集群的管理和控制。Master 节点上包含以下组件：

- kube-apiserver：集群控制的入口，提供 HTTP REST 服务

- kube-controller-manager：Kubernetes 集群中所有资源对象的自动化控制中心

- kube-scheduler：负责 Pod 的调度

- Node：Node 节点是 Kubernetes 集群中的工作节点，Node 上的工作负载由 Master 节点分配，工作负载主要是运行容器应用。Node 节点上包含以下组件：
  - kubelet：负责 Pod 的创建、启动、监控、重启、销毁等工作，同时与 Master 节点协作，实现集群管理的基本功能。
  - kube-proxy：实现 Kubernetes Service 的通信和负载均衡
  - 运行容器化(Pod)应用
  
- Pod: Pod 是 Kubernetes 最基本的部署调度单元。每个 Pod 可以由一个或多个业务容器和一个根容器(Pause 容器)组成。一个 Pod 表示某个应用的一个实例，一个 Pod 具有一个 IP，该 IP 在其容器之间共享。

- Label(标签)：Label 是 Kubernetes 及其最终用户用于过滤系统中相似资源的方式，也是资源与资源相互“访问”或关联的粘合剂。比如说，为 Deployment 打开端口的 Service。不论是监控、日志、调试或是测试，任何 Kubernetes 资源都应打上标签以供后续查验。例如，给系统中所有 Worker Pod 打上标签：app=worker，之后即可在 kubectl 或 Kubernetes API 中使用 --selector 字段对其进行选择。

- Annotation(注解)：Annotation 与 Label 非常相似，但通常用于以自由的字符串形式保存不同对象的元数据，例如“更改原因: 安全补丁升级”。

- ReplicaSet：是 Pod 副本的抽象，用于解决 Pod 的扩容和伸缩

- Deployment：Deployment 表示部署，在内部使用ReplicaSet 来实现。可以通过 Deployment 来生成相应的 ReplicaSet 完成 Pod 副本的创建。

  一切看起来都很美好，Pod 可以正常运行，如果上层有 ReplicaSet，还可以根据负载进行伸缩。不过，大家蜂拥而来，为的是能用新版本快速替换应用程序。我们想小规模地进行构建、测试和发布，以缩短反馈周期。使用 Deployments 即可持续地部署新软件，这是一组描述特定运行工作负载新需求的[元数据](https://www.zhihu.com/search?q=元数据&search_source=Entity&hybrid_search_source=Entity&hybrid_search_extra={"sourceType"%3A"answer"%2C"sourceId"%3A826736487})。举个例子，发布新版本、错误修复，甚至是回滚（这是 Kubernetes 的另一个内部选项）。

  在 Kubernetes 中部署软件可使用 2 个主要策略：

  - 替换——正如其名，使用新需求替换全部负载，自然会强制停机。对于快速替换非生产环境的资源，这很有帮助。
  - 滚动升级——通过监听两个特定配置慢慢地将容器替换成新的：

  MaxAvailable——设置在部署新版本时可用的工作负载比例（或具体数量），100% 表示“我有 2 个容器，在部署时要保持 2 个存活以服务请求”；
  b. MaxSurge——设置在当前存活容器的基础上部署的工作负载比例（或数量），100% 表示“我有 X 个容器，部署另外 X 个容器，然后开始滚动移除旧容器”。

- Job(任务)：Kubernetes 核心团队考虑了大部分使用编排系统的应用程序。虽然多数应用程序要求持续运行以同时处理服务器请求（比如 Web 服务器），但有时还是需要生成一批作业并在其完成后进行清理。比如，一个迷你的无服务器环境。

  为了在 Kubernetes 中实现这一点，可以使用 Job 资源。正如其名，Job 的工作是生成容器来完成特定的工作，并在成功完成时销毁。举个例子，一组 Worker 从待处理和存储的数据队列中读取作业。一旦队列空了，就不再需要这些 Worker 了，直到下个批次准备好。

- ConfigMap(配置映射)及Secret（机密配置）：如果你还不熟悉[十二要素应用清单](https://link.zhihu.com/?target=https%3A//yq.aliyun.com/go/articleRenderRedirect%3Furl%3Dhttps%3A%2F%2F12factor.net%2F)，请先行了解。现代应用程序的一个关键概念是无环境，并可通过注入的环境变量进行配置。应用程序应与其位置完全无关。为了在 Kubernetes 中实现这个重要的概念，就有了 ConfigMap。实际上这是一个环境变量键值列表，它们会被传递给正在运行的工作负载以确定不同的运行时行为。在同样的范畴下，Secret 与正常的配置条目类似，只是会进行加密以防类似密钥、密码、证书等敏感信息的泄漏。

  我个人认为 Hashicorp 的 Vault 是使用机密配置的最佳方案。请务必阅读一下我去年写的[有关文章](https://link.zhihu.com/?target=https%3A//yq.aliyun.com/go/articleRenderRedirect%3Furl%3Dhttps%3A%2F%2Fmedium.com%2Fprodopsio%2Fsecurity-for-dummies-protecting-application-secrets-made-easy-5ef3f8b748f7)，文章讲述了将 Vault 作为生产环境一部分的原因，以及我的一位同事写的[另一篇更技术性的文章](https://link.zhihu.com/?target=https%3A//yq.aliyun.com/go/articleRenderRedirect%3Furl%3Dhttps%3A%2F%2Fmedium.com%2Fprodopsio%2Ftaking-your-hashicorp-vault-to-the-next-level-8549e7988b24)。

- DaemonSet(守护进程集)：有时候，应用程序每个节点需要的实例不超过一个。比如 [FileBeat](https://link.zhihu.com/?target=https%3A//yq.aliyun.com/go/articleRenderRedirect%3Furl%3Dhttps%3A%2F%2Fwww.elastic.co%2Fproducts%2Fbeats%2Ffilebeat) 这类日志收集器就是个很好的例子。为了从各个节点收集日志，其代理需要运行在所有节点上，但每个节点只需要一个实例。Kubernetes 的 DaemonSet 即可用于创建这样的工作负载。

- Storage(存储)：Kubernetes 在存储之上添加了一层抽象。工作负载可以为不同任务请求特定存储，甚至可以管理超过 Pod 生命周期的持久化。为简短起见，请阅读作者之前发布的[关于 Kubernetes 存储的文章](https://link.zhihu.com/?target=https%3A//yq.aliyun.com/go/articleRenderRedirect%3Furl%3Dhttps%3A%2F%2Fmedium.com%2Fprodopsio%2Fk8s-will-not-solve-your-storage-problems-5bda2e6180b5)，特别重点看看为什么它不能完全解决类似数据库部署这样的数据持久性要求。

- Service：Service 是 Kubernetes 最重要的资源对象。Kubernetes 中的 Service 对象可以对应微服务架构中的微服务。Service 定义了服务的访问入口，服务的调用者通过这个地址访问 Service 后端的 Pod 副本实例。Service 通过 Label Selector 同后端的 Pod 副本建立关系，Deployment 保证后端Pod 副本的数量，也就是保证服务的伸缩性。

- StatefulSet(有状态集)：尽管多数微服务涉及的都是不可变的无状态应用程序，但也有例外。有状态的工作负载有赖于磁盘卷的可靠支持。虽然应用程序容器本身可以是不可变的，可以使用更新的版本或更健康的实例来替代，但是所有副本还是需要数据的持久化。StatefulSet 即是用于这类需要在整个生命周期内使用同一节点的应用程序的部署。

  它还保留了它的“名称”：容器内的 hostname 以及整个集群中服务发现的名称。3 个 ZooKeeper 构成的 StatefulSet 可以被命名 zk-1、zk-2 及 zk-3，也可以扩展到更多的成员 zk-4、zk-5 等等…… StatefulSets 还负责管理 PersistentVolumeClaim（Pod 上连接的磁盘）。

- Service Discovery(服务发现)：作为编排系统，Kubernetes 控制着不同工作负载的众多资源，负责管理 Pod、作业及所有需要通信的物理资源的网络。为此，Kubernetes 使用了 ETCD。

  ETCD 是 Kubernetes 的“内部”数据库，Master 通过它来获取所有资源的位置。Kubernetes 还为服务提供了实际的“服务发现”——所有 Pod 使用了一个自定义的 DNS 服务器，通过解析其他服务的名称以获取其 IP 地址和端口。它在 Kubernetes 集群中“开箱即用”，无须进行设置。

  

  ![k8s basic](.\k8s-basic.png)

Kubernetes 主要由以下几个核心组件组成:

- etcd 保存了整个集群的状态，就是一个数据库；
- apiserver 提供了资源操作的唯一入口，并提供认证、授权、访问控制、API 注册和发现等机制；
- controller manager 负责维护集群的状态，比如故障检测、自动扩展、滚动更新等；
- scheduler 负责资源的调度，按照预定的调度策略将 Pod 调度到相应的机器上；
- kubelet 负责维护容器的生命周期，同时也负责 Volume（CSI）和网络（CNI）的管理；
- Container runtime 负责镜像管理以及 Pod 和容器的真正运行（CRI）；
- kube-proxy 负责为 Service 提供 cluster 内部的服务发现和负载均衡；

当然了除了上面的这些核心组件，还有一些推荐的插件：

- kube-dns 负责为整个集群提供 DNS 服务
- Ingress Controller 为服务提供外网入口
- Heapster 提供资源监控
- Dashboard 提供 GUI

### 组件通信

Kubernetes 多组件之间的通信原理：

- apiserver 负责 etcd 存储的所有操作，且只有 apiserver 才直接操作 etcd 集群
- apiserver 对内（集群中的其他组件）和对外（用户）提供统一的 REST API，其他组件均通过 apiserver 进行通信
  - controller manager、scheduler、kube-proxy 和 kubelet 等均通过 apiserver watch API 监测资源变化情况，并对资源作相应的操作
  - 所有需要更新资源状态的操作均通过 apiserver 的 REST API 进行
- apiserver 也会直接调用 kubelet API（如 logs, exec, attach 等），默认不校验 kubelet 证书，但可以通过 `--kubelet-certificate-authority` 开启（而 GKE 通过 SSH 隧道保护它们之间的通信）

比如最典型的创建 Pod 的流程：![k8s pod](.\k8s-pod-process.png)

- 用户通过 REST API 创建一个 Pod
- apiserver 将其写入 etcd
- scheduluer 检测到未绑定 Node 的 Pod，开始调度并更新 Pod 的 Node 绑定
- kubelet 检测到有新的 Pod 调度过来，通过 container runtime 运行该 Pod
- kubelet 通过 container runtime 取到 Pod 状态，并更新到 apiserver 中





##  用 kubeadm 搭建集群环境

### 架构

上节课我们给大家讲解了 k8s 的基本概念与几个主要的组件，我们在了解了 k8s 的基本概念过后，实际上就可以去正式使用了，但是我们前面的课程都是在 katacoda 上面进行的演示，只提供给我们15分钟左右的使用时间，所以最好的方式还是我们自己来手动搭建一套 k8s 的环境，在搭建环境之前，我们再来看一张更丰富的k8s的架构图。![k8s 架构](.\k8s-structure.jpeg)

- 核心层：Kubernetes 最核心的功能，对外提供 API 构建高层的应用，对内提供插件式应用执行环境
- 应用层：部署（无状态应用、有状态应用、批处理任务、集群应用等）和路由（服务发现、DNS 解析等）
- 管理层：系统度量（如基础设施、容器和网络的度量），自动化（如自动扩展、动态 Provision 等）以及策略管理（RBAC、Quota、PSP、NetworkPolicy 等）
- 接口层：kubectl 命令行工具、客户端 SDK 以及集群联邦
- 生态系统：在接口层之上的庞大容器集群管理调度的生态系统，可以划分为两个范畴
  - Kubernetes 外部：日志、监控、配置管理、CI、CD、Workflow等
  - Kubernetes 内部：CRI、CNI、CVI、镜像仓库、Cloud Provider、集群自身的配置和管理等

在更进一步了解了 k8s 集群的架构后，我们就可以来正式的的安装我们的 k8s 集群环境了，我们这里使用的是`kubeadm`工具来进行集群的搭建。

`kubeadm`是`Kubernetes`官方提供的用于快速安装`Kubernetes`集群的工具，通过将集群的各个组件进行容器化安装管理，通过`kubeadm`的方式安装集群比二进制的方式安装要方便不少，但是目录`kubeadm`还处于 beta 状态，还不能用于生产环境，[Using kubeadm to Create a Cluster文档](https://kubernetes.io/docs/setup/independent/create-cluster-kubeadm/)中已经说明 kubeadm 将会很快能够用于生产环境了。对于现阶段想要用于生产环境的，建议还是参考我们前面的文章：[手动搭建高可用的 kubernetes 集群](https://blog.qikqiak.com/post/manual-install-high-available-kubernetes-cluster/)或者[视频教程](https://www.haimaxy.com/course/pjrqxm/?utm_source=k8s)。

### 环境

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







### 安装Docker

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

### 安装kubelet kubeadm kubectl

```apache
yum install -y kubelet-1.18.0 kubeadm-1.18.0 kubectl-1.18.0


systemctl enable kubelet
```

### 部署Kubenetes Master

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

### 安装Node节点

执行kubeadm join

```mipsasm
kubeadm join 10.206.0.15:6443 --token iv8baz.f2yagtk257ilmanr \
    --discovery-token-ca-cert-hash sha256:b43a11c9feeab057ee3d6ee91fd7e96dfc75859911f96ff1e89e9578d0801c23 
```

### 部署CNI网络插件

```awk
wget https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml

#手动拉取镜像
docker pull quay.io/coreos/flannel:v0.14.0

kubectl apply -f kube-flannel.yml
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

### 测试kubernetes集群

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













## 搭建 Kubernetes 集群 Dashboard 2.0+ 可视化插件

2022-01-15 141

**简介：** Kubernetes 还开发了一个基于 Web 的 Dashboard，用户可以用 Kubernetes Dashboard 部署容器化的应用、监控应用的状态、执行故障排查任务以及管理 Kubernetes 各种资源。

### 一、概述

Kubernetes 还开发了一个基于 Web 的 Dashboard，用户可以用 Kubernetes Dashboard 部署容器化的应用、监控应用的状态、执行故障排查任务以及管理 Kubernetes 各种资源。

Dashboard 的 GitHub 地址：https://github.com/kubernetes/dashboard

### 二、系统环境

- Kubernetes 版本：1.18.5
- kubernetes-dashboard 版本：v2.0.3

### 三、兼容性

| Kubernetes版本 | 1.13 | 1.14 | 1.15 | 1.16 | 1.17 | 1.18 |
| :------------- | :--- | :--- | :--- | :--- | :--- | :--- |
| 兼容性         | ？   | ？   | ？   | ？   | ?    | ✓    |

- ✕ 不支持的版本范围。
- ✓ 完全支持的版本范围。
- ? 由于Kubernetes API版本之间的重大更改，某些功能可能无法在仪表板中正常运行。

### 四、下载安装

执行安装:

```
$ kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.2/aio/deploy/recommended.yaml
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

可以看到新版本 Dashboard 集成了一个` metrics-scraper` 的组件，可以通过 Kubernetes 的 Metrics API 收集一些基础资源的监控信息，并在 web 页面上展示，所以要想在页面上展示监控信息就需要提供 Metrics API，前提需要安装 Metrics Server。

新版本的 Dashboard 会被默认安装在 kubernetes-dashboard 这个命名空间下面，查看 pod 名称：

```
$ kubectl get pods --namespace=kubernetes-dashboard -o wide
NAME                                         READY   STATUS    RESTARTS   AGE     IP           NODE        NOMINATED NODE   READINESS GATES
dashboard-metrics-scraper-6b4884c9d5-jdw22   1/1     Running   0          7h42m   10.244.3.3   k8s-node2   <none>           <none>
kubernetes-dashboard-7bfbb48676-l28c9        1/1     Running   0          7h38m   10.244.2.6   k8s-node3   <none>           <none>
```

### 五、修改为 NodePort 访问

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

### 六、证书管理

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

### 七、创建访问的 ServiceAccount

最后需要创建一个绑定 admin 权限的 ServiceAccount，获取其 Token 用于访问看板。

#### 1、创建用户

新建文件名`admin-user.yaml`，复制下面一段：

```
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kubernetes-dashboard
```

复制到`admin-user.yaml`文件后，执行：`kubectl create -f admin-user.yaml`

#### 2、绑定用户关系

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

### 八、获取令牌

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

### 九、登录新版本 Dashboard 查看

本人的 Kubernetes 集群地址为”10.0.0.7”并且在 Service 中设置了 NodePort 端口为 30022和类型为 NodePort 方式访问 Dashboard ，所以访问地址：`https://10.0.0.8:30022` 进入 Kubernetes Dashboard 页面，然后输入上一步中创建的 ServiceAccount 的 Token 进入 Dashboard，可以看到新的 Dashboard。





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





















