# Kubernetes学习之路（十四）之服务发现Service



## 一、Service的概念

　　运行在Pod中的应用是向客户端提供服务的守护进程，比如，nginx、tomcat、etcd等等，它们都是受控于控制器的资源对象，存在生命周期，我们知道Pod资源对象在自愿或非自愿终端后，只能被重构的Pod对象所替代，属于不可再生类组件。而在动态和弹性的管理模式下，Service为该类Pod对象提供了一个固定、统一的访问接口和负载均衡能力。是不是觉得一堆话都没听明白呢？？？？

　　其实，就是说Pod存在生命周期，有销毁，有重建，无法提供一个固定的访问接口给客户端。并且为了同类的Pod都能够实现工作负载的价值，由此Service资源出现了，可以为一类Pod资源对象提供一个固定的访问接口和负载均衡，类似于阿里云的负载均衡或者是LVS的功能。

　　但是要知道的是，Service和Pod对象的IP地址，一个是虚拟地址，一个是Pod IP地址，都仅仅在集群内部可以进行访问，无法接入集群外部流量。而为了解决该类问题的办法可以是在单一的节点上做端口暴露（hostPort）以及让Pod资源共享工作节点的网络名称空间（hostNetwork）以外，还可以使用NodePort或者是LoadBalancer类型的Service资源，或者是有7层负载均衡能力的Ingress资源。

　　Service是Kubernetes的核心资源类型之一，Service资源基于标签选择器将一组Pod定义成一个逻辑组合，并通过自己的IP地址和端口调度代理请求到组内的Pod对象，如下图所示，它向客户端隐藏了真是的，处理用户请求的Pod资源，使得从客户端上看，就像是由Service直接处理并响应一样，是不是很像负载均衡器呢！

![img](https://img2018.cnblogs.com/blog/1349539/201902/1349539-20190226153708890-1966593460.png)

　　Service对象的IP地址也称为Cluster IP，它位于为Kubernetes集群配置指定专用的IP地址范围之内，是一种虚拟的IP地址，它在Service对象创建之后保持不变，并且能够被同一集群中的Pod资源所访问。Service端口用于接受客户端请求，并将请求转发至后端的Pod应用的相应端口，这样的代理机制，也称为端口代理，它是基于TCP/IP 协议栈的传输层。

## 二、Service的实现模型

　　在 Kubernetes 集群中，每个 Node 运行一个 `kube-proxy` 进程。`kube-proxy` 负责为 `Service` 实现了一种 VIP（虚拟 IP）的形式，而不是 `ExternalName` 的形式。 在 Kubernetes v1.0 版本，代理完全在 userspace。在 Kubernetes v1.1 版本，新增了 iptables 代理，但并不是默认的运行模式。 从 Kubernetes v1.2 起，默认就是 iptables 代理。在Kubernetes v1.8.0-beta.0中，添加了ipvs代理。在 Kubernetes v1.0 版本，`Service` 是 “4层”（TCP/UDP over IP）概念。 在 Kubernetes v1.1 版本，新增了 `Ingress` API（beta 版），用来表示 “7层”（HTTP）服务。

kube-proxy 这个组件始终监视着apiserver中有关service的变动信息，获取任何一个与service资源相关的变动状态，通过watch监视，一旦有service资源相关的变动和创建，kube-proxy都要转换为当前节点上的能够实现资源调度规则（例如：iptables、ipvs）

![img](https://images2018.cnblogs.com/blog/1349539/201809/1349539-20180907165901269-453271720.png)

### 2.1、userspace代理模式

　　这种模式，当客户端Pod请求内核空间的service iptables后，把请求转到给用户空间监听的kube-proxy 的端口，由kube-proxy来处理后，再由kube-proxy将请求转给内核空间的 service ip，再由service iptalbes根据请求转给各节点中的的service pod。

　　由此可见这个模式有很大的问题，由客户端请求先进入内核空间的，又进去用户空间访问kube-proxy，由kube-proxy封装完成后再进去内核空间的iptables，再根据iptables的规则分发给各节点的用户空间的pod。这样流量从用户空间进出内核带来的性能损耗是不可接受的。在Kubernetes 1.1版本之前，userspace是默认的代理模型。

![img](https://images2018.cnblogs.com/blog/1349539/201809/1349539-20180907170415435-1497905641.png)

### 2.2、 iptables代理模式

　　客户端IP请求时，直接请求本地内核service ip，根据iptables的规则直接将请求转发到到各pod上，因为使用iptable NAT来完成转发，也存在不可忽视的性能损耗。另外，如果集群中存在上万的Service/Endpoint，那么Node上的iptables rules将会非常庞大，性能还会再打折扣。iptables代理模式由Kubernetes 1.1版本引入，自1.2版本开始成为默认类型。

![img](https://images2018.cnblogs.com/blog/1349539/201809/1349539-20180907171245389-9573372.png)

###  2.3、ipvs代理模式

　　Kubernetes自1.9-alpha版本引入了ipvs代理模式，自1.11版本开始成为默认设置。客户端IP请求时到达内核空间时，根据ipvs的规则直接分发到各pod上。kube-proxy会监视Kubernetes `Service`对象和`Endpoints`，调用`netlink`接口以相应地创建ipvs规则并定期与Kubernetes `Service`对象和`Endpoints`对象同步ipvs规则，以确保ipvs状态与期望一致。访问服务时，流量将被重定向到其中一个后端Pod。

与iptables类似，ipvs基于netfilter 的 hook 功能，但使用哈希表作为底层数据结构并在内核空间中工作。这意味着ipvs可以更快地重定向流量，并且在同步代理规则时具有更好的性能。此外，ipvs为负载均衡算法提供了更多选项，例如：

- rr：`轮询调度`
- lc：最小连接数
- `dh`：目标哈希
- `sh`：源哈希
- `sed`：最短期望延迟
- `nq`：不排队调度

**注意： ipvs模式假定在运行kube-proxy之前在节点上都已经安装了IPVS内核模块。当kube-proxy以ipvs代理模式启动时，kube-proxy将验证节点上是否安装了IPVS模块，如果未安装，则kube-proxy将回退到iptables代理模式。**

![img](https://images2018.cnblogs.com/blog/1349539/201809/1349539-20180907171512167-1381663777.png)

 如果某个服务后端pod发生变化，标签选择器适应的pod有多一个，适应的信息会立即反映到apiserver上,而kube-proxy一定可以watch到etc中的信息变化，而将它立即转为ipvs或者iptables中的规则，这一切都是动态和实时的，删除一个pod也是同样的原理。如图：

![img](https://img2018.cnblogs.com/blog/1349539/201809/1349539-20180927135812407-1162084485.png)

## 三、Service的定义

**3.1、清单创建Service**

![img](https://images.cnblogs.com/OutliningIndicators/ExpandedBlockStart.gif)

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
 1 [root@k8s-master ~]# kubectl explain svc
 2 KIND:     Service
 3 VERSION:  v1
 4 
 5 DESCRIPTION:
 6      Service is a named abstraction of software service (for example, mysql)
 7      consisting of local port (for example 3306) that the proxy listens on, and
 8      the selector that determines which pods will answer requests sent through
 9      the proxy.
10 
11 FIELDS:
12    apiVersion    <string>
13      APIVersion defines the versioned schema of this representation of an
14      object. Servers should convert recognized schemas to the latest internal
15      value, and may reject unrecognized values. More info:
16      https://git.k8s.io/community/contributors/devel/api-conventions.md#resources
17 
18    kind    <string>
19      Kind is a string value representing the REST resource this object
20      represents. Servers may infer this from the endpoint the client submits
21      requests to. Cannot be updated. In CamelCase. More info:
22      https://git.k8s.io/community/contributors/devel/api-conventions.md#types-kinds
23 
24    metadata    <Object>
25      Standard object's metadata. More info:
26      https://git.k8s.io/community/contributors/devel/api-conventions.md#metadata
27 
28    spec    <Object>
29      Spec defines the behavior of a service.
30      https://git.k8s.io/community/contributors/devel/api-conventions.md#spec-and-status
31 
32    status    <Object>
33      Most recently observed status of the service. Populated by the system.
34      Read-only. More info:
35      https://git.k8s.io/community/contributors/devel/api-conventions.md#spec-and-status
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

其中重要的4个字段：
apiVersion:
kind:
metadata:
spec:
　　clusterIP: 可以自定义，也可以动态分配
　　ports:（与后端容器端口关联）
　　selector:（关联到哪些pod资源上）
　　type：服务类型

**3.2、service的类型**

对一些应用（如 Frontend）的某些部分，可能希望通过外部（Kubernetes 集群外部）IP 地址暴露 Service。

Kubernetes `ServiceTypes` 允许指定一个需要的类型的 Service，默认是 `ClusterIP` 类型。

`Type` 的取值以及行为如下：

- **`ClusterIP`：**通过集群的内部 IP 暴露服务，选择该值，服务只能够在集群内部可以访问，这也是默认的 `ServiceType`。
- **`NodePort`：**通过每个 Node 上的 IP 和静态端口（`NodePort`）暴露服务。`NodePort` 服务会路由到 `ClusterIP` 服务，这个 `ClusterIP` 服务会自动创建。通过请求 `<NodeIP>:<NodePort>`，可以从集群的外部访问一个 `NodePort` 服务。
- **`LoadBalancer`：**使用云提供商的负载均衡器，可以向外部暴露服务。外部的负载均衡器可以路由到 `NodePort` 服务和 `ClusterIP` 服务。
- **`ExternalName`：**通过返回 `CNAME` 和它的值，可以将服务映射到 `externalName` 字段的内容（例如， `foo.bar.example.com`）。 没有任何类型代理被创建，这只有 Kubernetes 1.7 或更高版本的 `kube-dns` 才支持。

####  3.2.1、ClusterIP的service类型演示：

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master mainfests]# cat redis-svc.yaml 
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: default
spec:
  selector:　　#标签选择器，必须指定pod资源本身的标签
    app: redis
    role: logstor
  type: ClusterIP　　#指定服务类型为ClusterIP
  ports: 　　#指定端口
  - port: 6379　　#暴露给服务的端口
  - targetPort: 6379　　#容器的端口
[root@k8s-master mainfests]# kubectl apply -f redis-svc.yaml 
service/redis created
[root@k8s-master mainfests]# kubectl get svc
NAME         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
kubernetes   ClusterIP   10.96.0.1        <none>        443/TCP    36d
redis        ClusterIP   10.107.238.182   <none>        6379/TCP   1m

[root@k8s-master mainfests]# kubectl describe svc redis
Name:              redis
Namespace:         default
Labels:            <none>
Annotations:       kubectl.kubernetes.io/last-applied-configuration={"apiVersion":"v1","kind":"Service","metadata":{"annotations":{},"name":"redis","namespace":"default"},"spec":{"ports":[{"port":6379,"targetPort":6379}...
Selector:          app=redis,role=logstor
Type:              ClusterIP
IP:                10.107.238.182　　#service ip
Port:              <unset>  6379/TCP
TargetPort:        6379/TCP
Endpoints:         10.244.1.16:6379　　#此处的ip+端口就是pod的ip+端口
Session Affinity:  None
Events:            <none>

[root@k8s-master mainfests]# kubectl get pod redis-5b5d6fbbbd-v82pw -o wide
NAME                     READY     STATUS    RESTARTS   AGE       IP            NODE
redis-5b5d6fbbbd-v82pw   1/1       Running   0          20d       10.244.1.16   k8s-node01
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

从上演示可以总结出：service不会直接到pod，service是直接到endpoint资源，就是地址加端口，再由endpoint再关联到pod。

service只要创建完，就会在dns中添加一个资源记录进行解析，添加完成即可进行解析。资源记录的格式为：SVC_NAME.NS_NAME.DOMAIN.LTD.

默认的集群service 的A记录：svc.cluster.local.

redis服务创建的A记录：redis.default.svc.cluster.local.

#### 3.2.2、NodePort的service类型演示： 

　　NodePort即节点Port，通常在部署Kubernetes集群系统时会预留一个端口范围用于NodePort，其范围默认为：30000~32767之间的端口。定义NodePort类型的Service资源时，需要使用.spec.type进行明确指定。

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master mainfests]# kubectl get pods --show-labels |grep myapp-deploy
myapp-deploy-69b47bc96d-4hxxw   1/1       Running   0          12m       app=myapp,pod-template-hash=2560367528,release=canary
myapp-deploy-69b47bc96d-95bc4   1/1       Running   0          12m       app=myapp,pod-template-hash=2560367528,release=canary
myapp-deploy-69b47bc96d-hwbzt   1/1       Running   0          12m       app=myapp,pod-template-hash=2560367528,release=canary
myapp-deploy-69b47bc96d-pjv74   1/1       Running   0          12m       app=myapp,pod-template-hash=2560367528,release=canary
myapp-deploy-69b47bc96d-rf7bs   1/1       Running   0          12m       app=myapp,pod-template-hash=2560367528,release=canary

[root@k8s-master mainfests]# cat myapp-svc.yaml #为myapp创建service
apiVersion: v1
kind: Service
metadata:
  name: myapp
  namespace: default
spec:
  selector:
    app: myapp
    release: canary
  type: NodePort
  ports: 
  - port: 80
    targetPort: 80
    nodePort: 30080
[root@k8s-master mainfests]# kubectl apply -f myapp-svc.yaml 
service/myapp created
[root@k8s-master mainfests]# kubectl get svc
NAME         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
kubernetes   ClusterIP   10.96.0.1        <none>        443/TCP        36d
myapp        NodePort    10.101.245.119   <none>        80:30080/TCP   5s
redis        ClusterIP   10.107.238.182   <none>        6379/TCP       28m

[root@k8s-master mainfests]# while true;do curl http://192.168.56.11:30080/hostname.html;sleep 1;done
myapp-deploy-69b47bc96d-95bc4
myapp-deploy-69b47bc96d-4hxxw
myapp-deploy-69b47bc96d-pjv74
myapp-deploy-69b47bc96d-rf7bs
myapp-deploy-69b47bc96d-95bc4
myapp-deploy-69b47bc96d-rf7bs
myapp-deploy-69b47bc96d-95bc4
myapp-deploy-69b47bc96d-pjv74
myapp-deploy-69b47bc96d-4hxxw
myapp-deploy-69b47bc96d-pjv74
myapp-deploy-69b47bc96d-pjv74
myapp-deploy-69b47bc96d-4hxxw
myapp-deploy-69b47bc96d-pjv74
myapp-deploy-69b47bc96d-pjv74
myapp-deploy-69b47bc96d-pjv74
myapp-deploy-69b47bc96d-95bc4
myapp-deploy-69b47bc96d-hwbzt

[root@k8s-master mainfests]# while true;do curl http://192.168.56.11:30080/;sleep 1;done
```

 Hello MyApp | Version: v1 | <a href="hostname.html">Pod Name</a>
 Hello MyApp | Version: v1 | <a href="hostname.html">Pod Name</a>
 Hello MyApp | Version: v1 | <a href="hostname.html">Pod Name</a>
 Hello MyApp | Version: v1 | <a href="hostname.html">Pod Name</a>
 Hello MyApp | Version: v1 | <a href="hostname.html">Pod Name</a>
 Hello MyApp | Version: v1 | <a href="hostname.html">Pod Name</a>

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

从以上例子，可以看到通过NodePort方式已经实现了从集群外部端口进行访问，访问链接如下：http://192.168.56.11:30080/。实践中并不鼓励用户自定义使用节点的端口，因为容易和其他现存的Service冲突，建议留给系统自动配置。

####  3.2.3、Pod的会话保持

　　Service资源还支持Session affinity（粘性会话）机制，可以将来自同一个客户端的请求始终转发至同一个后端的Pod对象，这意味着它会影响调度算法的流量分发功用，进而降低其负载均衡的效果。因此，当客户端访问Pod中的应用程序时，如果有基于客户端身份保存某些私有信息，并基于这些私有信息追踪用户的活动等一类的需求时，那么应该启用session affinity机制。

　　Service affinity的效果仅仅在一段时间内生效，默认值为10800秒，超出时长，客户端再次访问会重新调度。该机制仅能基于客户端IP地址识别客户端身份，它会将经由同一个NAT服务器进行原地址转换的所有客户端识别为同一个客户端，由此可知，其调度的效果并不理想。Service 资源 通过. spec. sessionAffinity 和. spec. sessionAffinityConfig 两个字段配置粘性会话。 spec. sessionAffinity 字段用于定义要使用的粘性会话的类型，它仅支持使用“ None” 和“ ClientIP” 两种属性值。如下：

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master mainfests]# kubectl explain svc.spec.sessionAffinity
KIND:     Service
VERSION:  v1

FIELD:    sessionAffinity <string>

DESCRIPTION:
     Supports "ClientIP" and "None". Used to maintain session affinity. Enable
     client IP based session affinity. Must be ClientIP or None. Defaults to
     None. More info:
     https://kubernetes.io/docs/concepts/services-networking/service/#virtual-ips-and-service-proxies
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

sessionAffinity支持ClientIP和None 两种方式，默认是None（随机调度） ClientIP是来自于同一个客户端的请求调度到同一个pod中

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master mainfests]# vim myapp-svc.yaml 
apiVersion: v1
kind: Service
metadata:
  name: myapp
  namespace: default
spec:
  selector:
    app: myapp
    release: canary
  sessionAffinity: ClientIP
  type: NodePort
  ports: 
  - port: 80
    targetPort: 80
    nodePort: 30080
[root@k8s-master mainfests]# kubectl apply -f myapp-svc.yaml 
service/myapp configured
[root@k8s-master mainfests]# kubectl describe svc myapp
Name:                     myapp
Namespace:                default
Labels:                   <none>
Annotations:              kubectl.kubernetes.io/last-applied-configuration={"apiVersion":"v1","kind":"Service","metadata":{"annotations":{},"name":"myapp","namespace":"default"},"spec":{"ports":[{"nodePort":30080,"port":80,"ta...
Selector:                 app=myapp,release=canary
Type:                     NodePort
IP:                       10.101.245.119
Port:                     <unset>  80/TCP
TargetPort:               80/TCP
NodePort:                 <unset>  30080/TCP
Endpoints:                10.244.1.18:80,10.244.1.19:80,10.244.2.15:80 + 2 more...
Session Affinity:         ClientIP
External Traffic Policy:  Cluster
Events:                   <none>
[root@k8s-master mainfests]# while true;do curl http://192.168.56.11:30080/hostname.html;sleep 1;done
myapp-deploy-69b47bc96d-hwbzt
myapp-deploy-69b47bc96d-hwbzt
myapp-deploy-69b47bc96d-hwbzt
myapp-deploy-69b47bc96d-hwbzt
myapp-deploy-69b47bc96d-hwbzt
myapp-deploy-69b47bc96d-hwbzt
myapp-deploy-69b47bc96d-hwbzt
myapp-deploy-69b47bc96d-hwbzt
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

也可以使用打补丁的方式进行修改yaml内的内容，如下：

```
kubectl patch svc myapp -p '{"spec":{"sessionAffinity":"ClusterIP"}}'  #session保持，同一ip访问同一个pod

kubectl patch svc myapp -p '{"spec":{"sessionAffinity":"None"}}'    #取消session 
```

## 四、Headless Service 

有时不需要或不想要负载均衡，以及单独的 Service IP。 遇到这种情况，可以通过指定 Cluster IP（`spec.clusterIP`）的值为 `"None"` 来创建 `Headless` Service。

这个选项允许开发人员自由寻找他们自己的方式，从而降低与 Kubernetes 系统的耦合性。 应用仍然可以使用一种自注册的模式和适配器，对其它需要发现机制的系统能够很容易地基于这个 API 来构建。

对这类 `Service` 并不会分配 Cluster IP，kube-proxy 不会处理它们，而且平台也不会为它们进行负载均衡和路由。 DNS 如何实现自动配置，依赖于 `Service` 是否定义了 selector。

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
（1）编写headless service配置清单
[root@k8s-master mainfests]# cp myapp-svc.yaml myapp-svc-headless.yaml 
[root@k8s-master mainfests]# vim myapp-svc-headless.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-headless
  namespace: default
spec:
  selector:
    app: myapp
    release: canary
  clusterIP: "None"　　#headless的clusterIP值为None
  ports: 
  - port: 80
    targetPort: 80

（2）创建headless service 
[root@k8s-master mainfests]# kubectl apply -f myapp-svc-headless.yaml 
service/myapp-headless created
[root@k8s-master mainfests]# kubectl get svc
NAME             TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
kubernetes       ClusterIP   10.96.0.1        <none>        443/TCP        36d
myapp            NodePort    10.101.245.119   <none>        80:30080/TCP   1h
myapp-headless   ClusterIP   None             <none>        80/TCP         5s
redis            ClusterIP   10.107.238.182   <none>        6379/TCP       2h

（3）使用coredns进行解析验证
[root@k8s-master mainfests]# dig -t A myapp-headless.default.svc.cluster.local. @10.96.0.10

; <<>> DiG 9.9.4-RedHat-9.9.4-61.el7 <<>> -t A myapp-headless.default.svc.cluster.local. @10.96.0.10
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 62028
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 5, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
;; QUESTION SECTION:
;myapp-headless.default.svc.cluster.local. IN A

;; ANSWER SECTION:
myapp-headless.default.svc.cluster.local. 5 IN A 10.244.1.18
myapp-headless.default.svc.cluster.local. 5 IN A 10.244.1.19
myapp-headless.default.svc.cluster.local. 5 IN A 10.244.2.15
myapp-headless.default.svc.cluster.local. 5 IN A 10.244.2.16
myapp-headless.default.svc.cluster.local. 5 IN A 10.244.2.17

;; Query time: 4 msec
;; SERVER: 10.96.0.10#53(10.96.0.10)
;; WHEN: Thu Sep 27 04:27:15 EDT 2018
;; MSG SIZE  rcvd: 349

[root@k8s-master mainfests]# kubectl get svc -n kube-system
NAME       TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)         AGE
kube-dns   ClusterIP   10.96.0.10   <none>        53/UDP,53/TCP   36d

[root@k8s-master mainfests]# kubectl get pods -o wide -l app=myapp
NAME                            READY     STATUS    RESTARTS   AGE       IP            NODE
myapp-deploy-69b47bc96d-4hxxw   1/1       Running   0          1h        10.244.1.18   k8s-node01
myapp-deploy-69b47bc96d-95bc4   1/1       Running   0          1h        10.244.2.16   k8s-node02
myapp-deploy-69b47bc96d-hwbzt   1/1       Running   0          1h        10.244.1.19   k8s-node01
myapp-deploy-69b47bc96d-pjv74   1/1       Running   0          1h        10.244.2.15   k8s-node02
myapp-deploy-69b47bc96d-rf7bs   1/1       Running   0          1h        10.244.2.17   k8s-node02

（4）对比含有ClusterIP的service解析
[root@k8s-master mainfests]# dig -t A myapp.default.svc.cluster.local. @10.96.0.10

; <<>> DiG 9.9.4-RedHat-9.9.4-61.el7 <<>> -t A myapp.default.svc.cluster.local. @10.96.0.10
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 50445
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
;; QUESTION SECTION:
;myapp.default.svc.cluster.local. IN    A

;; ANSWER SECTION:
myapp.default.svc.cluster.local. 5 IN    A    10.101.245.119

;; Query time: 1 msec
;; SERVER: 10.96.0.10#53(10.96.0.10)
;; WHEN: Thu Sep 27 04:31:16 EDT 2018
;; MSG SIZE  rcvd: 107

[root@k8s-master mainfests]# kubectl get svc
NAME             TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
kubernetes       ClusterIP   10.96.0.1        <none>        443/TCP        36d
myapp            NodePort    10.101.245.119   <none>        80:30080/TCP   1h
myapp-headless   ClusterIP   None             <none>        80/TCP         11m
redis            ClusterIP   10.107.238.182   <none>        6379/TCP       2h
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

从以上的演示可以看到对比普通的service和headless service，headless service做dns解析是直接解析到pod的，而servcie是解析到ClusterIP的，那么headless有什么用呢？？？这将在statefulset中应用到，这里暂时仅仅做了解什么是headless service和创建方法。