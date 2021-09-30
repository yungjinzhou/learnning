# 深入剖析kubernetes





### k8s介绍

最具代表性的容器编排工具，当属 Docker 公司的 Compose+Swarm 组合，以及
Google 与 RedHat 公司共同主导的 Kubernetes 项目。



### kubenetes全局架构

**Kubernetes 项目确定了一个如下图所示的全局架构**

![img](.\企业微信截图_16325397933865.png)



- 控制节点，即 Master 节点，由三个紧密协作的独立组件组合而成，它们分别是负责 API 服务的 kube-apiserver、负责调度的 kube-scheduler，以及负责容器编排的 kube-controllermanager。整个集群的持久化数据，则由 kube-apiserver 处理后保存在 Ectd 中。

- 计算节点上最核心的部分，则是一个叫作 kubelet 的组件。

- 在 Kubernetes 项目中，kubelet 主要负责同容器运行时（比如 Docker 项目）打交道。而这个交互所依赖的，是一个称作 **CRI（Container Runtime Interface）**的远程调用接口，这个接口定义了容器运行时的各项核心操作，比如：启动一个容器需要的所有参数。

此外，kubelet 还通过 gRPC 协议同一个叫作 Device Plugin 的插件进行交互。这个插件，是Kubernetes 项目用来管理 GPU 等宿主机物理设备的主要组件，也是基于 Kubernetes 项目进行机器学习训练、高性能作业支持等工作必须关注的功能。

而kubelet 的另一个重要功能，则是调用网络插件和存储插件为容器配置网络和持久化存储。这两个插件与 kubelet 进行交互的接口，分别是 **CNI（Container Networking Interface）**和**CSI（Container Storage Interface）**。



围绕着容器和 Pod 不断向真实的技术场景扩展，我们就能够摸索出一幅如下所示的**Kubernetes 项目核心功能的“全景图”**。

![img](.\企业微信截图_16325401794689.png)



- 按照这幅图的线索，我们从容器这个最基础的概念出发，首先遇到了容器间“紧密协作”关系的难
  题，于是就扩展到了 Pod；有了 Pod 之后，我们希望能一次启动多个应用的实例，这样就需要
  Deployment 这个 Pod 的多实例管理器；而有了这样一组相同的 Pod 后，我们又需要通过一个固
  定的 IP 地址和端口以负载均衡的方式访问它，于是就有了 Service。
  可





### 基本概念与组件

#### 基本概念

Kubernetes 中的绝大部分概念都抽象成 Kubernetes 管理的一种资源对象，下面我们一起复习一下我们上节课遇到的一些资源对象：

- Master：Master 节点是 Kubernetes 集群的控制节点，负责整个集群的管理和控制。Master 节点上包含以下组件：
- kube-apiserver：集群控制的入口，提供 HTTP REST 服务
- kube-controller-manager：Kubernetes 集群中所有资源对象的自动化控制中心
- kube-scheduler：负责 Pod 的调度
- Node：Node 节点是 Kubernetes 集群中的工作节点，Node 上的工作负载由 Master 节点分配，工作负载主要是运行容器应用。Node 节点上包含以下组件：
  - kubelet：负责 Pod 的创建、启动、监控、重启、销毁等工作，同时与 Master 节点协作，实现集群管理的基本功能。
  - kube-proxy：实现 Kubernetes Service 的通信和负载均衡
  - 运行容器化(Pod)应用
- Pod: Pod 是 Kubernetes 最基本的部署调度单元。每个 Pod 可以由一个或多个业务容器和一个根容器(Pause 容器)组成。一个 Pod 表示某个应用的一个实例
- ReplicaSet：是 Pod 副本的抽象，用于解决 Pod 的扩容和伸缩
- Deployment：Deployment 表示部署，在内部使用ReplicaSet 来实现。可以通过 Deployment 来生成相应的 ReplicaSet 完成 Pod 副本的创建
- Service：Service 是 Kubernetes 最重要的资源对象。Kubernetes 中的 Service 对象可以对应微服务架构中的微服务。Service 定义了服务的访问入口，服务的调用者通过这个地址访问 Service 后端的 Pod 副本实例。Service 通过 Label Selector 同后端的 Pod 副本建立关系，Deployment 保证后端Pod 副本的数量，也就是保证服务的伸缩性。

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

#### 组件通信

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





### Kubernetes一键部署利器：kubeadm

#### 简单使用

```
# 创建一个 Master 节点
$ kubeadm init
# 将一个 Node 节点加入到当前集群中
$ kubeadm join <Master 节点的 IP 和端口 >
```

把 kubelet 直接运行在宿主机上，然后使用容器部署其他的 Kubernetes 组件。

使用 kubeadm 的第一步，是在机器上手动安装 kubeadm、kubelet 和 kubectl 这三个二进制文件。

#### kubeadm-init 的工作流程

- 当你**执行 kubeadm init 指令后**，kubeadm 首先要做的，是一系列的**检查**工作，以确定这台机器可以用来部署 Kubernetes。这一步检查，我们称为“Preflight Checks”，它可以为你省掉很多后续的麻烦。

- 在**通过了 Preflight Checks 之后**，kubeadm 要为你做的，是**生成** Kubernetes 对外提供服务所需的**各种证书和对应的目录**。Kubernetes 对外提供服务时，除非专门开启“不安全模式”，否则都要通过 HTTPS 才能访问kube-apiserver。这就需要为 Kubernetes 集群配置好证书文件。

  kubeadm 为 Kubernetes 项目生成的**证书文件**都放在 Master 节点的 **/etc/kubernetes/pki** 目录下。在这个目录下，最主要的证书文件是 ca.crt 和对应的私钥 ca.key。
  此外，用户使用 kubectl 获取容器日志等 streaming 操作时，需要通过 kube-apiserver 向kubelet 发起请求，这个连接也必须是安全的。kubeadm 为这一步生成的是 apiserver-kubeletclient.crt 文件，对应的私钥是 apiserver-kubelet-client.key。

- **证书生成后**，kubeadm 接下来会为其他组件**生成访问 kube-apiserver 所需的配置文件**。这些文件的路径是：/etc/kubernetes/xxx.conf（admin.conf controller-manager.conf kubelet.conf scheduler.conf）。

- 接下来，kubeadm 会为 Master 组件**生成 Pod 配置文件**。

  我已经在上一篇文章中和你介绍过Kubernetes 有三个 Master 组件 kube-apiserver、kube-controller-manager、kube-scheduler，而它们都会被使用 Pod 的方式部署起来。

  在 Kubernetes 中，有一种特殊的容器启动方法叫做“Static Pod”。它允许你把要部署的 Pod 的YAML 文件放在一个指定的目录里。这样，当这台机器上的 kubelet 启动时，它会自动检查这个目录，加载所有的 Pod YAML 文件，然后在这台机器上启动它们。在 kubeadm 中，**Master 组件的 YAML 文件会被生成在 /etc/kubernetes/manifests 路径**下（比如，etcd.yaml kube-apiserver.yaml kube-controller-manager.yaml kube-scheduler.yaml）。

  1. 这个 Pod 里只定义了一个容器，它使用的镜像是：k8s.gcr.io/kube-apiserveramd64:v1.11.1 。这个镜像是 Kubernetes 官方维护的一个组件镜像。
  2. 这个容器的启动命令（commands）是 kube-apiserver --authorization-mode=Node,RBAC…，这样一句非常长的命令。其实，它就是容器里 kube-apiserver 这个二进制文件再加上指定的配置参数而已。
  3. 如果你要修改一个已有集群的 kube-apiserver 的配置，需要修改这个 YAML 文件。
  4. 这些组件的参数也可以在部署时指定。

- kubeadm 还会再**生成**一个 **Etcd 的 Pod YAML** 文件，用来通过同样的 Static Pod 的方式启动 Etcd。

  一旦这些 **YAML 文件出现在**被 **kubelet 监视的** /etc/kubernetes/manifests **目录下**，**kubelet 就会自动创建**这些 YAML 文件中定义的 **Pod**，即 Master 组件的容器。

- Master 容器启动后，kubeadm 会通过检查 localhost:6443/healthz 这个 Master 组件的健康检查URL，等待 Master 组件完全运行起来。

- kubeadm 就会为**集群生成一个 bootstrap token**。在后面，只要持有这个 token，任何一个安装了 kubelet 和 kubadm 的节点，都可以通过 kubeadm join 加入到这个集群当中。

  这个 token 的值和使用方法会，会在 kubeadm init 结束后被打印出来。

- 在 token 生成之后，kubeadm 会**将 ca.crt 等** Master 节点的重要**信息**，通过 ConfigMap 的方式**保存在 Etcd** 当中，供后续部署 Node 节点使用。这个 ConfigMap 的名字是 cluster-info。

- kubeadm init 的最后一步，就是**安装默认插件**。

  Kubernetes 默认 kube-proxy 和 DNS 这两个插件是必须安装的。它们分别用来提供整个集群的服务发现和 DNS 功能。其实，这两个插件也只是两个容器镜像而已，所以 kubeadm 只要用 Kubernetes 客户端创建两个 Pod 就可以了。



#### kubeadm  join工作流程

这个流程其实非常简单，kubeadm init 生成 bootstrap token 之后，你就可以在任意一台安装了kubelet 和 kubeadm 的机器上执行 kubeadm join 了。

因为，任何一台机器想要成为 Kubernetes 集群中的一个节点，就必须在集群的 kube-apiserver 上注册。可是，要想跟 apiserver 打交道，这台机器就必须要获取到相应的证书文件（CA 文件）。可是，为了能够一键安装，我们就不能让用户去 Master 节点上手动拷贝这些文件。
所以，kubeadm 至少需要发起一次“不安全模式”的访问到 kube-apiserver，从而拿到保存在ConfigMap 中的 cluster-info（它保存了 APIServer 的授权信息）。而 bootstrap token，扮演的就是这个过程中的安全验证的角色。

只要有了 cluster-info 里的 kube-apiserver 的地址、端口、证书，kubelet 就可以以“安全模式”连接到 apiserver 上，这样一个新的节点就部署完成了。



#### 配置 kubeadm 的部署参数

```
$ kubeadm init --config kubeadm.yaml
```

例如这样的配置

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



#### 使用kubeadm搭建一个kubenetes

- centos7.6环境，4cpu, 4G内存，20G磁盘
- 更换阿里云镜像



##### master节点

配置ip地址

```]
vim /etc/sysconfig/network-scripts/ifcfg-eth0
YPE=Ethernet
BOOTPROTO=static
NAME=eth0
DEVICE=eth0
ONBOOT=yes
IPADDR=10.0.0.7
NETMASK=255.255.255.0
GATEWAY=10.0.0.2
DNS1=8.8.8.8
DNS2=114.114.114.114

```

配置hostname

```
hostnamectl set-hostname k8smaster
```

配置nameserver

```
vim /etc/resolv.conf

nameserver 8.8.8.8
nameserver 114.114.114.114
```

更换下载源

```
mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup

wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
yum makecache
```





关闭防火墙

```gauss
systemctl stop firewalld
systemctl disable firewalld

```

关闭selinux

```awk
# 永久
sed -i 's/enforcing/disabled/' /etc/selinux/config 

# 临时
setenforce 0
```

关闭 swap

```awk
# 临时
swapoff -a  

# 永久
sed -ri 's/.*swap.*/#&/' /etc/fstab

```



配置hosts

```accesslog
cat >> /etc/hosts << EOF 
10.0.0.7 k8s-master 
10.0.0.8 k8s-minion1
EOF

```

配置网络

```gauss
cat > /etc/sysctl.d/k8s.conf << EOF 
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1 
EOF

# 生效
sysctl --system 
```

时间同步

```stylus
yum install ntpdate -y
ntpdate time.windows.com
```



重启机器



安装docker

```awk
wget https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo -O /etc/yum.repos.d/docker-ce.repo 

yum -y install docker-ce-18.06.1.ce-3.el7 

systemctl enable docker && systemctl start docker 

docker --version
```

添加阿里云YUM源

设置仓库地址：[https://help.aliyun.com/docum...](https://link.segmentfault.com/?url=https%3A%2F%2Fhelp.aliyun.com%2Fdocument_detail%2F60750.html)

```arcade
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



安装kubelet kubeadm kubectl

```apache
yum install -y kubelet-1.18.0 kubeadm-1.18.0 kubectl-1.18.0


systemctl enable kubelet
```

部署Kubenetes Master

在Master节点执行

```apache
kubeadm init --apiserver-advertise-address=10.0.0.7 --image-repository registry.aliyuncs.com/google_containers --kubernetes-version v1.18.0 --service-cidr=10.96.0.0/12 --pod-network-cidr=10.244.0.0/16
```

得到token

```
kubeadm join 10.0.0.7:6443 --token lj8kxk.xs9oy9jj7x0vp0s0 \
    --discovery-token-ca-cert-hash sha256:4b958a86348e11904a74e4507dd3b076e58364a2caaccd07d96e04c55afd1eb2 
```



提示使用kubectl工具

```awk
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

kubectl get nodes
```



部署CNI网络插件

```awk
wget https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml

#手动拉取镜像
docker pull quay.io/coreos/flannel:v0.14.0

kubectl apply -f kube-flannel.yml
```



kube-flannel.yml

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





##### 安装Node节点

- docker和kubeadm安装和master节点相同

配置ip地址

```]
vim /etc/sysconfig/network-scripts/ifcfg-eth0
YPE=Ethernet
BOOTPROTO=static
NAME=eth0
DEVICE=eth0
ONBOOT=yes
IPADDR=10.0.0.7
NETMASK=255.255.255.0
GATEWAY=10.0.0.2
DNS1=8.8.8.8
DNS2=114.114.114.114

```

配置hostname

```
hostnamectl set-hostname k8sminion1
```

配置nameserver

```
vim /etc/resolv.conf

nameserver 8.8.8.8
nameserver 114.114.114.114
```

更换下载源

```
mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup

wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
yum makecache
```





关闭防火墙

```gauss
systemctl stop firewalld
systemctl disable firewalld

```

关闭selinux

```awk
# 永久
sed -i 's/enforcing/disabled/' /etc/selinux/config 

# 临时
setenforce 0
```

关闭 swap

```awk
# 临时
swapoff -a  

# 永久
sed -ri 's/.*swap.*/#&/' /etc/fstab

```



配置hosts

```accesslog
cat >> /etc/hosts << EOF 
10.0.0.7 k8s-master 
10.0.0.8 k8s-minion1
EOF

```

配置网络

```gauss
cat > /etc/sysctl.d/k8s.conf << EOF 
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1 
EOF

# 生效
sysctl --system 
```

时间同步

```stylus
yum install ntpdate -y
ntpdate time.windows.com
```



重启机器



安装docker

```awk
wget https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo -O /etc/yum.repos.d/docker-ce.repo 

yum -y install docker-ce-18.06.1.ce-3.el7 

systemctl enable docker && systemctl start docker 

docker --version
```

添加阿里云YUM源

设置仓库地址：[https://help.aliyun.com/docum...](https://link.segmentfault.com/?url=https%3A%2F%2Fhelp.aliyun.com%2Fdocument_detail%2F60750.html)

```arcade
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



安装kubeadm 

```apache
yum install -y kubeadm-1.18.0
```

在workerr节点执行

```
kubeadm join 10.0.0.7:6443 --token lj8kxk.xs9oy9jj7x0vp0s0 \
    --discovery-token-ca-cert-hash sha256:4b958a86348e11904a74e4507dd3b076e58364a2caaccd07d96e04c55afd1eb2 
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



测试kubernetes集群

创建一个pod

```pgsql
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80 --type=NodePort
kubectl get pod,svc

NAME                 TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/kubernetes   ClusterIP   10.0.0.7       <none>        443/TCP        148m
service/nginx        NodePort    10.0.0.7  <none>        80:31312/TCP   4s
```

测试访问

```awk
curl http://公网IP:31312
```

























