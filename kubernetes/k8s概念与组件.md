# 概念、组件、架构

## 重要概念

Kubernetes 中的绝大部分概念都抽象成 Kubernetes 管理的一种资源对象，下面我们一起复习一下我们上节课遇到的一些资源对象：

### cluster（集群）

Cluster 是计算、存储和网络资源的集合，Kubernetes 利用这些资源运行各种基于容器的应用。

### master（主节点）

Master 节点是 Kubernetes 集群的控制节点，负责整个集群的管理和控制。

Master节点主要有一下组件：

### node(minion节点)

Node 节点是 Kubernetes 集群中的工作节点，Node 上的工作负载由 Master 节点分配，工作负载主要是运行容器应用。Node 节点上包含以下组件：
### Pod

Pod 是 Kubernetes 最基本的部署调度单元。每个 Pod 可以由一个或多个业务容器和一个根容器(Pause 容器)组成。一个 Pod 表示某个应用的一个实例，一个 Pod 具有一个 IP，该 IP 在其容器之间共享。

#### 引入pod的目的

1. 可管理性。
   有些容器天生就是需要紧密联系，一起工作。Pod 提供了比容器更高层次的抽象，将它们封装到一个部署单元中。Kubernetes 以 Pod 为最小单位进行调度、扩展、共享资源、管理生命周期。
2. 通信和资源共享。
   Pod 中的所有容器使用同一个网络 namespace，即相同的 IP 地址和 Port 空间。它们可以直接用 localhost 通信。同样的，这些容器可以共享存储，当 Kubernetes 挂载 volume 到 Pod，本质上是将 volume 挂载到 Pod 中的每一个容器。

#### pod使用方式

1. 运行单一容器。
   `one-container-per-Pod` 是 Kubernetes 最常见的模型，这种情况下，只是将单个容器简单封装成 Pod。即便是只有一个容器，Kubernetes 管理的也是 Pod 而不是直接管理容器。
2. 运行多个容器。
   条件是这些容器联系必须 非常紧密，而且需要 直接共享资源。



### Controller（控制器）

Kubernetes 通常不会直接创建 Pod，而是通过 Controller 来管理 Pod 的。Controller 中定义了 Pod 的部署特性，比如有几个副本，在什么样的 Node 上运行等。为了满足不同的业务场景，Kubernetes 提供了多种 Controller，包括 Deployment、ReplicaSet、DaemonSet、StatefuleSet、Job 等。

#### Deployment（部署控制器）

**是最常用的 Controller**、。Deployment 可以管理 Pod 的多个副本，并确保 Pod 按照期望的状态运行。

Deployment在内部使用ReplicaSet 来实现。可以通过 Deployment 来生成相应的 ReplicaSet 完成 Pod 副本的创建。

一切看起来都很美好，Pod 可以正常运行，如果上层有 ReplicaSet，还可以根据负载进行伸缩。不过，大家蜂拥而来，为的是能用新版本快速替换应用程序。我们想小规模地进行构建、测试和发布，以缩短反馈周期。使用 Deployments 即可持续地部署新软件，这是一组描述特定运行工作负载新需求的[元数据](https://www.zhihu.com/search?q=元数据&search_source=Entity&hybrid_search_source=Entity&hybrid_search_extra={"sourceType"%3A"answer"%2C"sourceId"%3A826736487})。举个例子，发布新版本、错误修复，甚至是回滚（这是 Kubernetes 的另一个内部选项）。

在 Kubernetes 中部署软件可使用 2 个主要策略：

- 替换——正如其名，使用新需求替换全部负载，自然会强制停机。对于快速替换非生产环境的资源，这很有帮助。
- 滚动升级——通过监听两个特定配置慢慢地将容器替换成新的：

#### ReplicaSet（副本集控制器）

实现了 Pod 的多副本管理。使用 Deployment 时会自动创建 ReplicaSet，也就是说 Deployment 是通过 ReplicaSet 来管理 Pod 的多个副本，我们通常不需要直接使用 ReplicaSet。

#### DaemonSet(守护进程集)

用于每个 Node 最多只运行一个 Pod 副本的场景。正如其名称所揭示的，DaemonSet 通常用于运行 daemon。

有时候，应用程序每个节点需要的实例不超过一个。比如 [FileBeat](https://link.zhihu.com/?target=https%3A//yq.aliyun.com/go/articleRenderRedirect%3Furl%3Dhttps%3A%2F%2Fwww.elastic.co%2Fproducts%2Fbeats%2Ffilebeat) 这类日志收集器就是个很好的例子。为了从各个节点收集日志，其代理需要运行在所有节点上，但每个节点只需要一个实例。Kubernetes 的 DaemonSet 即可用于创建这样的工作负载。

#### StatefulSet(有状态集)

能够保证 Pod 的每个副本在整个生命周期中名称是不变的。而其他 Controller 不提供这个功能，当某个 Pod 发生故障需要删除并重新启动时，Pod 的名称会发生变化。同时 StatefuleSet 会保证副本按照固定的顺序启动、更新或者删除。还负责管理 PersistentVolumeClaim（Pod 上连接的磁盘）。



#### Job(任务)

用于运行结束就删除的应用。而其他 Controller 中的 Pod 通常是长期持续运行。

为了在 Kubernetes 中实现这一点，可以使用 Job 资源。正如其名，Job 的工作是生成容器来完成特定的工作，并在成功完成时销毁。举个例子，一组 Worker 从待处理和存储的数据队列中读取作业。一旦队列空了，就不再需要这些 Worker 了，直到下个批次准备好。

cronjob

### Service

Kubernetes Service 定义了外界访问一组特定 Pod 的方式。Service 有自己的 IP 和端口，Service 为 Pod 提供了负载均衡。Kubernetes 运行容器（Pod）与访问容器（Pod）这两项任务分别由 Controller 和 Service 执行。 

Service 是 Kubernetes 最重要的资源对象。Kubernetes 中的 Service 对象可以对应微服务架构中的微服务。Service 定义了服务的访问入口，服务的调用者通过这个地址访问 Service 后端的 Pod 副本实例。Service 通过 Label Selector 同后端的 Pod 副本建立关系，Deployment 保证后端Pod 副本的数量，也就是保证服务的伸缩性。

### Namespace

Namespace 可以将一个物理的 Cluster 逻辑上划分成多个虚拟 Cluster，每个 Cluster 就是一个 Namespace。不同 Namespace 里的资源是完全隔离的。

Kubernetes 默认创建了两个 Namespace。

```
[root@linux-node1 ~]# kubectl get namespace
NAME          STATUS    AGE
default       Active    1d
kube-system   Active    1d
```

**`default`** -- 创建资源时如果不指定，将被放到这个 Namespace 中。

**`kube-system`** -- Kubernetes 自己创建的系统资源将放到这个 Namespace 中。





## 架构



**Kubernetes架构**

![img](.\k8s架构.png)



![k8s 架构](.\k8s-structure.jpeg)



**K8S架构拆解图**

![img](.\k8s架构拆解图.png)



### K8S Master节点

**从上图可以看到，Master是K8S集群的核心部分，主要运行着以下的服务：kube-apiserver、kube-scheduler、kube-controller-manager、etcd和Pod网络（如：flannel）**



```
API Server：K8S对外的唯一接口，提供HTTP/HTTPS RESTful API，即kubernetes API。所有的请求都需要经过这个接口进行通信。主要处理REST操作以及更新ETCD中的对象。是所有资源增删改查的唯一入口，并提供认证、授权、访问控制、API 注册和发现等机制。

Scheduler：资源调度，负责决定将Pod放到哪个Node上运行。Scheduler在调度时会对集群的结构进行分析，当前各个节点的负载，以及应用对高可用、性能等方面的需求。 

Controller Manager：负责管理集群各种资源，保证资源处于预期的状态。Controller Manager由多种controller组成，包括replication controller、endpoints controller、namespace controller、serviceaccounts controller等 

ETCD：负责保存k8s 集群的配置信息和各种资源的状态信息，当数据发生变化时，etcd会快速地通知k8s相关组件。Pod网络：Pod要能够相互间通信，K8S集群必须部署Pod网络，flannel是其中一种的可选方案。

```





### K8S Node节点

**Node是Pod运行的地方，Kubernetes支持Docker、rkt等容器Runtime。Node上运行的K8S组件包括kubelet、kube-proxy和Pod网络。**

```
Kubelet：负责 Pod 的创建、启动、监控、重启、销毁等工作，同时与 Master 节点协作，实现集群管理的基本功能。 kubelet 负责维护容器的生命周期，同时也负责 Volume（CSI）和网络（CNI）的管理；


Kube-proxy：实现 Kubernetes Service 的通信和负载均衡。
service在逻辑上代表了后端的多个Pod，外借通过service访问Pod。service接收到请求就需要kube-proxy完成转发到Pod的。每个Node都会运行kube-proxy服务，负责将访问的service的TCP/UDP数据流转发到后端的容器，如果有多个副本，kube-proxy会实现负载均衡，有2种方式：LVS或者Iptables 

Docker Engine：负责节点的容器的管理工作

```



### Kubernetes中pod创建流程

　　Pod是Kubernetes中最基本的部署调度单元，可以包含container，逻辑上表示某种应用的一个实例。例如一个web站点应用由前端、后端及数据库构建而成，这三个组件将运行在各自的容器中，那么我们可以创建包含三个container的pod。

![img](.\pod创建流程.png)

![k8s pod](.\k8s-pod-process.png)



**具体的创建步骤包括：**

（1）客户端提交创建请求，可以通过API Server的Restful API，也可以使用kubectl命令行工具。支持的数据类型包括JSON和YAML。

（2）API Server处理用户请求，存储Pod数据到etcd。

（3）调度器通过API Server查看未绑定的Pod。尝试为Pod分配主机。

（4）过滤主机 (调度预选)：调度器用一组规则过滤掉不符合要求的主机。比如Pod指定了所需要的资源量，那么可用资源比Pod需要的资源量少的主机会被过滤掉。

（5）主机打分(调度优选)：对第一步筛选出的符合要求的主机进行打分，在主机打分阶段，调度器会考虑一些整体优化策略，比如把容一个Replication Controller的副本分布到不同的主机上，使用最低负载的主机等。

（6）选择主机：选择打分最高的主机，进行binding操作，结果存储到etcd中。

（7）kubelet根据调度结果执行Pod创建操作： 绑定成功后，scheduler会调用APIServer的API在etcd中创建一个boundpod对象，描述在一个工作节点上绑定运行的所有pod信息。运行在每个工作节点上的kubelet也会定期与etcd同步boundpod信息，一旦发现应该在该工作节点上运行的boundpod对象没有更新，则调用Docker API创建并启动pod内的容器。



### 组件通信

#### 核心组件

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











# 未归类处理todo

- Label(标签)：Label 是 Kubernetes 及其最终用户用于过滤系统中相似资源的方式，也是资源与资源相互“访问”或关联的粘合剂。比如说，为 Deployment 打开端口的 Service。不论是监控、日志、调试或是测试，任何 Kubernetes 资源都应打上标签以供后续查验。例如，给系统中所有 Worker Pod 打上标签：app=worker，之后即可在 kubectl 或 Kubernetes API 中使用 --selector 字段对其进行选择。

- Annotation(注解)：Annotation 与 Label 非常相似，但通常用于以自由的字符串形式保存不同对象的元数据，例如“更改原因: 安全补丁升级”。

  MaxAvailable——设置在部署新版本时可用的工作负载比例（或具体数量），100% 表示“我有 2 个容器，在部署时要保持 2 个存活以服务请求”；
  b. MaxSurge——设置在当前存活容器的基础上部署的工作负载比例（或数量），100% 表示“我有 X 个容器，部署另外 X 个容器，然后开始滚动移除旧容器”。

- ConfigMap(配置映射)及Secret（机密配置）：如果你还不熟悉[十二要素应用清单](https://link.zhihu.com/?target=https%3A//yq.aliyun.com/go/articleRenderRedirect%3Furl%3Dhttps%3A%2F%2F12factor.net%2F)，请先行了解。现代应用程序的一个关键概念是无环境，并可通过注入的环境变量进行配置。应用程序应与其位置完全无关。为了在 Kubernetes 中实现这个重要的概念，就有了 ConfigMap。实际上这是一个环境变量键值列表，它们会被传递给正在运行的工作负载以确定不同的运行时行为。在同样的范畴下，Secret 与正常的配置条目类似，只是会进行加密以防类似密钥、密码、证书等敏感信息的泄漏。

  我个人认为 Hashicorp 的 Vault 是使用机密配置的最佳方案。请务必阅读一下我去年写的[有关文章](https://link.zhihu.com/?target=https%3A//yq.aliyun.com/go/articleRenderRedirect%3Furl%3Dhttps%3A%2F%2Fmedium.com%2Fprodopsio%2Fsecurity-for-dummies-protecting-application-secrets-made-easy-5ef3f8b748f7)，文章讲述了将 Vault 作为生产环境一部分的原因，以及我的一位同事写的[另一篇更技术性的文章](https://link.zhihu.com/?target=https%3A//yq.aliyun.com/go/articleRenderRedirect%3Furl%3Dhttps%3A%2F%2Fmedium.com%2Fprodopsio%2Ftaking-your-hashicorp-vault-to-the-next-level-8549e7988b24)。

- Storage(存储)：Kubernetes 在存储之上添加了一层抽象。工作负载可以为不同任务请求特定存储，甚至可以管理超过 Pod 生命周期的持久化。为简短起见，请阅读作者之前发布的[关于 Kubernetes 存储的文章](https://link.zhihu.com/?target=https%3A//yq.aliyun.com/go/articleRenderRedirect%3Furl%3Dhttps%3A%2F%2Fmedium.com%2Fprodopsio%2Fk8s-will-not-solve-your-storage-problems-5bda2e6180b5)，特别重点看看为什么它不能完全解决类似数据库部署这样的数据持久性要求。

- Service Discovery(服务发现)：作为编排系统，Kubernetes 控制着不同工作负载的众多资源，负责管理 Pod、作业及所有需要通信的物理资源的网络。为此，Kubernetes 使用了 ETCD。

  ETCD 是 Kubernetes 的“内部”数据库，Master 通过它来获取所有资源的位置。Kubernetes 还为服务提供了实际的“服务发现”——所有 Pod 使用了一个自定义的 DNS 服务器，通过解析其他服务的名称以获取其 IP 地址和端口。它在 Kubernetes 集群中“开箱即用”，无须进行设置


