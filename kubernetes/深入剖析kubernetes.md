# 深入剖析kubernetes





### k8s介绍

最具代表性的容器编排工具，当属 Docker 公司的 Compose+Swarm 组合，以及
Google 与 RedHat 公司共同主导的 Kubernetes 项目。



### kubenetes全局架构

**Kubernetes 项目确定了一个如下图所示的全局架构**

![img](E:\code\learnning\kubernetes\企业微信截图_16325397933865.png)



- 控制节点，即 Master 节点，由三个紧密协作的独立组件组合而成，它们分别是负责 API 服务的 kube-apiserver、负责调度的 kube-scheduler，以及负责容器编排的 kube-controllermanager。整个集群的持久化数据，则由 kube-apiserver 处理后保存在 Ectd 中。

- 计算节点上最核心的部分，则是一个叫作 kubelet 的组件。

- 在 Kubernetes 项目中，kubelet 主要负责同容器运行时（比如 Docker 项目）打交道。而这个交互所依赖的，是一个称作 **CRI（Container Runtime Interface）**的远程调用接口，这个接口定义了容器运行时的各项核心操作，比如：启动一个容器需要的所有参数。

此外，kubelet 还通过 gRPC 协议同一个叫作 Device Plugin 的插件进行交互。这个插件，是Kubernetes 项目用来管理 GPU 等宿主机物理设备的主要组件，也是基于 Kubernetes 项目进行机器学习训练、高性能作业支持等工作必须关注的功能。

而kubelet 的另一个重要功能，则是调用网络插件和存储插件为容器配置网络和持久化存储。这两个插件与 kubelet 进行交互的接口，分别是 **CNI（Container Networking Interface）**和**CSI（Container Storage Interface）**。



围绕着容器和 Pod 不断向真实的技术场景扩展，我们就能够摸索出一幅如下所示的**Kubernetes 项目核心功能的“全景图”**。

![img](E:\code\learnning\kubernetes\企业微信截图_16325401794689.png)



- 按照这幅图的线索，我们从容器这个最基础的概念出发，首先遇到了容器间“紧密协作”关系的难
  题，于是就扩展到了 Pod；有了 Pod 之后，我们希望能一次启动多个应用的实例，这样就需要
  Deployment 这个 Pod 的多实例管理器；而有了这样一组相同的 Pod 后，我们又需要通过一个固
  定的 IP 地址和端口以负载均衡的方式访问它，于是就有了 Service。
  可



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
apiVersion: kubeadm.k8s.io/v1alpha2
kind: MasterConfiguration
kubernetesVersion: v1.11.0
api:
  advertiseAddress: 192.168.0.102

  bindPort: 6443
...
  etcd:
    local:
    dataDir: /var/lib/etcd
    image: ""
imageRepository: k8s.gcr.io
kubeProxy:
  config:
  bindAddress: 0.0.0.0
...
  kubeletConfiguration:
    baseConfig:
    address: 0.0.0.0
...
networking:
  dnsDomain: cluster.local
  podSubnet: ""
  serviceSubnet: 10.96.0.0/12
nodeRegistration:
  criSocket: /var/run/dockershim.sock
apiServerExtraArgs:
  advertise-address: 192.168.0.103
  anonymous-auth: false
  enable-admission-plugins: AlwaysPullImages,DefaultStorageClass
  audit-log-path: /home/johndoe/audit.log
  runtime-config: "api/all=true"
  kubernetesVersion: "stable-1.11"
  
controllerManagerExtraArgs:
  horizontal-pod-autoscaler-use-rest-clients: "true"
  horizontal-pod-autoscaler-sync-period: "10s"
  node-monitor-grace-period: "10s"
```







