# Kubernetes学习之路（十五）之Ingress和Ingress Controller

目录

- 一、什么是Ingress？
  - [1、Pod 漂移问题](https://www.cnblogs.com/linuxk/p/9706720.html#1pod-漂移问题)
  - [2、端口管理问题](https://www.cnblogs.com/linuxk/p/9706720.html#2端口管理问题)
  - [3、域名分配及动态更新问题](https://www.cnblogs.com/linuxk/p/9706720.html#3域名分配及动态更新问题)
- [二、如何创建Ingress资源](https://www.cnblogs.com/linuxk/p/9706720.html#二如何创建ingress资源)
- 三、Ingress资源类型
  - [1、单Service资源型Ingress](https://www.cnblogs.com/linuxk/p/9706720.html#1单service资源型ingress)
- 四、Ingress Nginx部署
  - [1、部署Ingress controller](https://www.cnblogs.com/linuxk/p/9706720.html#1部署ingress-controller)
  - [2、部署后端服务](https://www.cnblogs.com/linuxk/p/9706720.html#2部署后端服务)
  - [3、部署ingress-nginx service](https://www.cnblogs.com/linuxk/p/9706720.html#3部署ingress-nginx-service)
  - [4、部署ingress](https://www.cnblogs.com/linuxk/p/9706720.html#4部署ingress)
- [四、增加tomcat服务](https://www.cnblogs.com/linuxk/p/9706720.html#四增加tomcat服务)
- [四、构建TLS站点](https://www.cnblogs.com/linuxk/p/9706720.html#四构建tls站点)



### 一、什么是Ingress？

从前面的学习，我们可以了解到`Kubernetes`暴露服务的方式目前只有三种：`LoadBlancer Service、ExternalName、NodePort Service、Ingress`；而我们需要将集群内服务提供外界访问就会产生以下几个问题：

#### 1、Pod 漂移问题

Kubernetes 具有强大的副本控制能力，能保证在任意副本（Pod）挂掉时自动从其他机器启动一个新的，还可以动态扩容等，通俗地说，这个 Pod 可能在任何时刻出现在任何节点上，也可能在任何时刻死在任何节点上；那么自然随着 Pod 的创建和销毁，Pod IP 肯定会动态变化；那么如何把这个动态的 Pod IP 暴露出去？这里借助于 Kubernetes 的 Service 机制，Service 可以以标签的形式选定一组带有指定标签的 Pod，并监控和自动负载他们的 Pod IP，那么我们向外暴露只暴露 Service IP 就行了；这就是 NodePort 模式：即在每个节点上开起一个端口，然后转发到内部 Pod IP 上，如下图所示：
此时的访问方式：[http://nodeip](http://nodeip/):nodeport/
![img](https://img2018.cnblogs.com/blog/1349539/201809/1349539-20180929174515031-619898952.png)

#### 2、端口管理问题

采用 NodePort 方式暴露服务面临问题是，服务一旦多起来，NodePort 在每个节点上开启的端口会及其庞大，而且难以维护；这时，我们可以能否使用一个Nginx直接对内进行转发呢？众所周知的是，Pod与Pod之间是可以互相通信的，而Pod是可以共享宿主机的网络名称空间的，也就是说当在共享网络名称空间时，Pod上所监听的就是Node上的端口。那么这又该如何实现呢？简单的实现就是使用 DaemonSet 在每个 Node 上监听 80，然后写好规则，因为 Nginx 外面绑定了宿主机 80 端口（就像 NodePort），本身又在集群内，那么向后直接转发到相应 Service IP 就行了，如下图所示：
![img](https://img2018.cnblogs.com/blog/1349539/201809/1349539-20180929175905911-113975562.png)

#### 3、域名分配及动态更新问题

从上面的方法，采用 Nginx-Pod 似乎已经解决了问题，但是其实这里面有一个很大缺陷：当每次有新服务加入又该如何修改 Nginx 配置呢？？我们知道使用Nginx可以通过虚拟主机域名进行区分不同的服务，而每个服务通过upstream进行定义不同的负载均衡池，再加上location进行负载均衡的反向代理，在日常使用中只需要修改nginx.conf即可实现，那在K8S中又该如何实现这种方式的调度呢？？？

假设后端的服务初始服务只有ecshop，后面增加了bbs和member服务，那么又该如何将这2个服务加入到Nginx-Pod进行调度呢？总不能每次手动改或者Rolling Update 前端 Nginx Pod 吧！！此时 Ingress 出现了，如果不算上面的Nginx，Ingress 包含两大组件：Ingress Controller 和 Ingress。
![img](https://img2018.cnblogs.com/blog/1349539/201809/1349539-20180930094041632-683389969.png)

Ingress 简单的理解就是你原来需要改 Nginx 配置，然后配置各种域名对应哪个 Service，现在把这个动作抽象出来，变成一个 Ingress 对象，你可以用 yaml 创建，每次不要去改 Nginx 了，直接改 yaml 然后创建/更新就行了；那么问题来了：”Nginx 该怎么处理？”

Ingress Controller 这东西就是解决 “Nginx 的处理方式” 的；Ingress Controoler 通过与 Kubernetes API 交互，动态的去感知集群中 Ingress 规则变化，然后读取他，按照他自己模板生成一段 Nginx 配置，再写到 Nginx Pod 里，最后 reload 一下，工作流程如下图：
![img](https://img2018.cnblogs.com/blog/1349539/201809/1349539-20180930094200688-1480474925.png)

实际上Ingress也是Kubernetes API的标准资源类型之一，它其实就是一组基于DNS名称（host）或URL路径把请求转发到指定的Service资源的规则。用于将集群外部的请求流量转发到集群内部完成的服务发布。我们需要明白的是，Ingress资源自身不能进行“流量穿透”，仅仅是一组规则的集合，这些集合规则还需要其他功能的辅助，比如监听某套接字，然后根据这些规则的匹配进行路由转发，这些能够为Ingress资源监听套接字并将流量转发的组件就是Ingress Controller。

**PS：Ingress 控制器不同于Deployment 控制器的是，Ingress控制器不直接运行为kube-controller-manager的一部分，它仅仅是Kubernetes集群的一个附件，类似于CoreDNS，需要在集群上单独部署。**

### 二、如何创建Ingress资源

Ingress资源时基于HTTP虚拟主机或URL的转发规则，需要强调的是，**这是一条转发规则**。它在资源配置清单中的spec字段中嵌套了rules、backend和tls等字段进行定义。如下示例中定义了一个Ingress资源，其包含了一个转发规则：将发往myapp.magedu.com的请求，代理给一个名字为myapp的Service资源。

```yaml
apiVersion: extensions/v1beta1		
kind: Ingress		
metadata:			
  name: ingress-myapp   
  namespace: default     
  annotations:          
    kubernetes.io/ingress.class: "nginx"
spec:     
  rules:   
  - host: myapp.magedu.com   
    http:
      paths:       
      - path:       
        backend:    
          serviceName: myapp
          servicePort: 80
```

Ingress 中的spec字段是Ingress资源的核心组成部分，主要包含以下3个字段：

- rules：用于定义当前Ingress资源的转发规则列表；由rules定义规则，或没有匹配到规则时，所有的流量会转发到由backend定义的默认后端。
- backend：默认的后端用于服务那些没有匹配到任何规则的请求；定义Ingress资源时，必须要定义backend或rules两者之一，该字段用于让负载均衡器指定一个全局默认的后端。
- tls：TLS配置，目前仅支持通过默认端口443提供服务，如果要配置指定的列表成员指向不同的主机，则需要通过SNI TLS扩展机制来支持该功能。
  backend对象的定义由2个必要的字段组成：serviceName和servicePort，分别用于指定流量转发的后端目标Service资源名称和端口。
  rules对象由一系列的配置的Ingress资源的host规则组成，这些host规则用于将一个主机上的某个URL映射到相关后端Service对象，其定义格式如下：

```yaml
spec:
  rules:
  - hosts: <string>
    http:
      paths:
      - path:
        backend:
          serviceName: <string>
          servicePort: <string>
```

需要注意的是，.spec.rules.host属性值，目前暂不支持使用IP地址定义，也不支持IP:Port的格式，该字段留空，代表着通配所有主机名。
tls对象由2个内嵌的字段组成，仅在定义TLS主机的转发规则上使用。

- hosts： 包含 于 使用 的 TLS 证书 之内 的 主机 名称 字符串 列表， 因此， 此处 使用 的 主机 名 必须 匹配 tlsSecret 中的 名称。
- secretName： 用于 引用 SSL 会话 的 secret 对象 名称， 在 基于 SNI 实现 多 主机 路 由 的 场景 中， 此 字段 为 可选。

### 三、Ingress资源类型

Ingress的资源类型有以下4种：

- 1、单Service资源型Ingress
- 2、基于URL路径进行流量转发
- 3、基于主机名称的虚拟主机
- 4、TLS类型的Ingress资源

#### 1、单Service资源型Ingress

暴露单个服务的方法有多种，如NodePort、LoadBanlancer等等，当然也可以使用Ingress来进行暴露单个服务，只需要为Ingress指定default backend即可，如下示例：

```yaml
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: my-ingress
spec:
  backend:
    serviceName: my-svc
    servicePort: 80
```

Ingress控制器会为其分配一个IP地址接入请求流量，并将其转发至后端my-svc

### 四、Ingress Nginx部署

使用Ingress功能步骤：
1、安装部署ingress controller Pod
2、部署后端服务
3、部署ingress-nginx service
4、部署ingress

从前面的描述我们知道，Ingress 可以使用 yaml 的方式进行创建，从而得知 Ingress 也是标准的 K8S 资源，其定义的方式，也可以使用 explain 进行查看：

```delphi
[root@k8s-master ~]# kubectl explain ingress
KIND:     Ingress
VERSION:  extensions/v1beta1
 
DESCRIPTION:
     Ingress is a collection of rules that allow inbound connections to reach
     the endpoints defined by a backend. An Ingress can be configured to give
     services externally-reachable urls, load balance traffic, terminate SSL,
     offer name based virtual hosting etc.
 
FIELDS:
   apiVersion	<string>
     APIVersion defines the versioned schema of this representation of an
     object. Servers should convert recognized schemas to the latest internal
     value, and may reject unrecognized values. More info:
     https://git.k8s.io/community/contributors/devel/api-conventions.md#resources
 
   kind	<string>
     Kind is a string value representing the REST resource this object
     represents. Servers may infer this from the endpoint the client submits
     requests to. Cannot be updated. In CamelCase. More info:
     https://git.k8s.io/community/contributors/devel/api-conventions.md#types-kinds
 
   metadata	<Object>
     Standard object's metadata. More info:
     https://git.k8s.io/community/contributors/devel/api-conventions.md#metadata
 
   spec	<Object>
     Spec is the desired state of the Ingress. More info:
     https://git.k8s.io/community/contributors/devel/api-conventions.md#spec-and-status
 
   status	<Object>
     Status is the current state of the Ingress. More info:
     https://git.k8s.io/community/contributors/devel/api-conventions.md#spec-and-status
 
```

#### 1、部署Ingress controller

[ingress-nginx在github上的地址](https://github.com/kubernetes/ingress-nginx)
（1）下载ingress相关的yaml

```csharp
[root@k8s-master ~]# mkdir ingress-nginx
[root@k8s-master ~]# cd ingress-nginx/
[root@k8s-master ingress-nginx]# for file in namespace.yaml configmap.yaml rbac.yaml tcp-services-configmap.yaml with-rbac.yaml udp-services-configmap.yaml default-backend.yaml;do wget https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/$file;done
[root@k8s-master ingress-nginx]# ll
total 28
-rw-r--r-- 1 root root  199 Sep 29 22:45 configmap.yaml	#configmap用于为nginx从外部注入配置的
-rw-r--r-- 1 root root 1583 Sep 29 22:45 default-backend.yaml	#配置默认后端服务
-rw-r--r-- 1 root root   69 Sep 29 22:45 namespace.yaml	#创建独立的名称空间
-rw-r--r-- 1 root root 2866 Sep 29 22:45 rbac.yaml	#rbac用于集群角色授权
-rw-r--r-- 1 root root  192 Sep 29 22:45 tcp-services-configmap.yaml
-rw-r--r-- 1 root root  192 Sep 29 22:45 udp-services-configmap.yaml
-rw-r--r-- 1 root root 2409 Sep 29 22:45 with-rbac.yaml
```

（2）创建ingress-nginx名称空间

```yaml
[root@k8s-master ingress-nginx]# cat namespace.yaml 
apiVersion: v1
kind: Namespace
metadata:
  name: ingress-nginx
 
---
[root@k8s-master ingress-nginx]# kubectl apply -f namespace.yaml 
namespace/ingress-nginx created
```

（3）创建ingress controller的pod

```bash
[root@k8s-master ingress-nginx]#  kubectl apply -f ./
configmap/nginx-configuration created
deployment.extensions/default-http-backend created
service/default-http-backend created
namespace/ingress-nginx configured
serviceaccount/nginx-ingress-serviceaccount created
clusterrole.rbac.authorization.k8s.io/nginx-ingress-clusterrole created
role.rbac.authorization.k8s.io/nginx-ingress-role created
rolebinding.rbac.authorization.k8s.io/nginx-ingress-role-nisa-binding created
clusterrolebinding.rbac.authorization.k8s.io/nginx-ingress-clusterrole-nisa-binding created
configmap/tcp-services created
configmap/udp-services created
deployment.extensions/nginx-ingress-controller created
[root@k8s-master ingress-nginx]# kubectl get pod -n ingress-nginx -w
NAME                                        READY     STATUS              RESTARTS   AGE
default-http-backend-7db7c45b69-gjrnl       0/1       ContainerCreating   0          35s
nginx-ingress-controller-6bd7c597cb-6pchv   0/1       ContainerCreating   0          34s
```

此处遇到一个问题，新版本的Kubernetes在安装部署中，需要从k8s.grc.io仓库中拉取所需镜像文件，但由于国内网络防火墙问题导致无法正常拉取。
docker.io仓库对google的容器做了镜像，可以通过下列命令下拉取相关镜像：

```bash
[root@k8s-node01 ~]# docker pull mirrorgooglecontainers/defaultbackend-amd64:1.5
1.5: Pulling from mirrorgooglecontainers/defaultbackend-amd64
9ecb1e82bb4a: Pull complete 
Digest: sha256:d08e129315e2dd093abfc16283cee19eabc18ae6b7cb8c2e26cc26888c6fc56a
Status: Downloaded newer image for mirrorgooglecontainers/defaultbackend-amd64:1.5
 
[root@k8s-node01 ~]# docker tag mirrorgooglecontainers/defaultbackend-amd64:1.5 k8s.gcr.io/defaultbackend-amd64:1.5
[root@k8s-node01 ~]# docker image ls
REPOSITORY                                    TAG                 IMAGE ID            CREATED             SIZE
mirrorgooglecontainers/defaultbackend-amd64   1.5                 b5af743e5984        34 hours ago        5.13MB
k8s.gcr.io/defaultbackend-amd64               1.5                 b5af743e5984        34 hours ago        5.13MB
```

#### 2、部署后端服务

（1）查看ingress的配置清单选项

```vhdl
[root@k8s-master ingress-nginx]# kubectl explain ingress.spec
KIND:     Ingress
VERSION:  extensions/v1beta1
 
RESOURCE: spec <Object>
 
DESCRIPTION:
     Spec is the desired state of the Ingress. More info:
     https://git.k8s.io/community/contributors/devel/api-conventions.md#spec-and-status
 
     IngressSpec describes the Ingress the user wishes to exist.
 
FIELDS:
   backend	<Object>     #定义后端有哪几个主机
     A default backend capable of servicing requests that don't match any rule.
     At least one of 'backend' or 'rules' must be specified. This field is
     optional to allow the loadbalancer controller or defaulting logic to
     specify a global default.
 
   rules	<[]Object>    #定义规则
     A list of host rules used to configure the Ingress. If unspecified, or no
     rule matches, all traffic is sent to the default backend.
 
   tls	<[]Object>
     TLS configuration. Currently the Ingress only supports a single TLS port,
     443. If multiple members of this list specify different hosts, they will be
     multiplexed on the same port according to the hostname specified through
     the SNI TLS extension, if the ingress controller fulfilling the ingress
     supports SNI.
```

（2）部署后端服务

```yaml
[root@k8s-master ingress-nginx]# cd ../mainfests/
[root@k8s-master mainfests]# mkdir ingress && cd ingress
[root@k8s-master ingress]# cp ../deploy-demo.yaml .
[root@k8s-master ingress]# vim deploy-demo.yaml 
#创建service为myapp
apiVersion: v1
kind: Service
metadata:
  name: myapp
  namespace: default
spec:
  selector:
    app: myapp
    release: canary
  ports:
  - name: http
    targetPort: 80
    port: 80
---
#创建后端服务的pod
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-backend-pod
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
      release: canary
  template:
    metadata:
      labels:
        app: myapp
        release: canary
    spec:
      containers:
      - name: myapp
        image: ikubernetes/myapp:v2
        ports:
        - name: http
          containerPort: 80
[root@k8s-master ingress]# kubectl apply -f deploy-demo.yaml 
service/myapp created
deployment.apps/myapp-backend-pod unchanged
```

（3）查看新建的后端服务pod

```sql
[root@k8s-master ingress]# kubectl get pods
NAME                                 READY     STATUS    RESTARTS   AGE
myapp-backend-pod-67f6f6b4dc-9jl9q   1/1       Running   0          7m
myapp-backend-pod-67f6f6b4dc-x5jsb   1/1       Running   0          7m
myapp-backend-pod-67f6f6b4dc-xzxbj   1/1       Running   0          7m
```

#### 3、部署ingress-nginx service

通过ingress-controller对外提供服务，现在还需要手动给ingress-controller建立一个service，接收集群外部流量。方法如下：
（1）下载ingress-controller的yaml文件

```yaml
[root@k8s-master ingress]# wget https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/provider/baremetal/service-nodeport.yaml
[root@k8s-master ingress]# vim service-nodeport.yaml 
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
      nodePort: 30080
    - name: https
      port: 443
      targetPort: 443
      protocol: TCP
      nodePort: 30443
  selector:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
 
---

```

（2）创建ingress-controller的service，并测试访问

```sql
[root@k8s-master ingress]# kubectl apply -f service-nodeport.yaml 
service/ingress-nginx created
[root@k8s-master ingress]# kubectl get svc -n ingress-nginx
NAME                   TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
default-http-backend   ClusterIP   10.104.41.201   <none>        80/TCP                       45m
ingress-nginx          NodePort    10.96.135.79    <none>        80:30080/TCP,443:30443/TCP   11s
```

此时访问:192.168.56.12:30080
此时应该是404 ，调度器是正常工作的，但是后端服务没有关联
![img](https://img2018.cnblogs.com/blog/1349539/201809/1349539-20180930120624317-1402372112.png)

#### 4、部署ingress

（1）编写ingress的配置清单

```yaml
[root@k8s-master ingress]# vim ingress-myapp.yaml
apiVersion: extensions/v1beta1		#api版本
kind: Ingress		#清单类型
metadata:			#元数据
  name: ingress-myapp    #ingress的名称
  namespace: default     #所属名称空间
  annotations:           #注解信息
    kubernetes.io/ingress.class: "nginx"
spec:      #规格
  rules:   #定义后端转发的规则
  - host: myapp.magedu.com    #通过域名进行转发
    http:
      paths:       
      - path:       #配置访问路径，如果通过url进行转发，需要修改；空默认为访问的路径为"/"
        backend:    #配置后端服务
          serviceName: myapp
          servicePort: 80
[root@k8s-master ingress]# kubectl apply -f ingress-myapp.yaml
[root@k8s-master ingress]# kubectl get ingress
NAME            HOSTS              ADDRESS   PORTS     AGE
ingress-myapp   myapp.magedu.com             80        46s
```

（2）查看ingress-myapp的详细信息

```csharp
[root@k8s-master ingress]# kubectl describe ingress ingress-myapp
Name:             ingress-myapp
Namespace:        default
Address:          
Default backend:  default-http-backend:80 (<none>)
Rules:
  Host              Path  Backends
  ----              ----  --------
  myapp.magedu.com  
                       myapp:80 (<none>)
Annotations:
  kubectl.kubernetes.io/last-applied-configuration:  {"apiVersion":"extensions/v1beta1","kind":"Ingress","metadata":{"annotations":{"kubernetes.io/ingress.class":"nginx"},"name":"ingress-myapp","namespace":"default"},"spec":{"rules":[{"host":"myapp.magedu.com","http":{"paths":[{"backend":{"serviceName":"myapp","servicePort":80},"path":null}]}}]}}
 
  kubernetes.io/ingress.class:  nginx
Events:
  Type    Reason  Age   From                      Message
  ----    ------  ----  ----                      -------
  Normal  CREATE  1m    nginx-ingress-controller  Ingress default/ingress-myapp
 
[root@k8s-master ingress]# kubectl get pods -n ingress-nginx
NAME                                        READY     STATUS    RESTARTS   AGE
default-http-backend-7db7c45b69-fndwp       1/1       Running   0          31m
nginx-ingress-controller-6bd7c597cb-6pchv   1/1       Running   0          55m
```

（3）进入nginx-ingress-controller进行查看是否注入了nginx的配置

```bash
[root@k8s-master ingress]# kubectl exec -n ingress-nginx -it nginx-ingress-controller-6bd7c597cb-6pchv -- /bin/bash
www-data@nginx-ingress-controller-6bd7c597cb-6pchv:/etc/nginx$ cat nginx.conf
......
	## start server myapp.magedu.com
	server {
		server_name myapp.magedu.com ;
		
		listen 80;
		
		set $proxy_upstream_name "-";
		
		location / {
			
			set $namespace      "default";
			set $ingress_name   "ingress-myapp";
			set $service_name   "myapp";
			set $service_port   "80";
			set $location_path  "/";
			
			rewrite_by_lua_block {
				
				balancer.rewrite()
				
			}
			
			log_by_lua_block {
				
				balancer.log()
				
				monitor.call()
			}
......
```

（4）修改本地host文件，进行访问
192.168.56.12 myapp.magedu.com
192.168.56.13 myapp.magedu.com
![img](https://img2018.cnblogs.com/blog/1349539/201809/1349539-20180930120604221-1512400790.png)

### 四、增加tomcat服务

（1）编写tomcat的配置清单文件

```yaml
[root@k8s-master ingress]# cp deploy-demo.yaml tomcat-demo.yaml
[root@k8s-master ingress]# vim tomcat-demo.yaml 
apiVersion: v1
kind: Service
metadata:
  name: tomcat
  namespace: default
spec:
  selector:
    app: tomcat
    release: canary
  ports:
  - name: http
    targetPort: 8080
    port: 8080
  - name: ajp
    targetPort: 8009
    port: 8009
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tomcat-deploy
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tomcat
      release: canary
  template:
    metadata:
      labels:
        app: tomcat
        release: canary
    spec:
      containers:
      - name: tomcat
        image: tomcat:8.5.34-jre8-alpine   
        #此镜像在dockerhub上进行下载，需要查看版本是否有变化，hub.docker.com
        ports:
        - name: http
          containerPort: 8080
          name: ajp
          containerPort: 8009
[root@k8s-master ingress]# kubectl get pods
NAME                                 READY     STATUS    RESTARTS   AGE
tomcat-deploy-6dd558cd64-b4xbm       1/1       Running   0          3m
tomcat-deploy-6dd558cd64-qtwpx       1/1       Running   0          3m
tomcat-deploy-6dd558cd64-w7f9s       1/1       Running   0          5m
```

（2）进入tomcat的pod中进行查看是否监听8080和8009端口，并查看tomcat的svc

```sql
[root@k8s-master ingress]# kubectl exec tomcat-deploy-6dd558cd64-b4xbm -- netstat -tnl
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       
tcp        0      0 127.0.0.1:8005          0.0.0.0:*               LISTEN      
tcp        0      0 0.0.0.0:8009            0.0.0.0:*               LISTEN      
tcp        0      0 0.0.0.0:8080            0.0.0.0:*               LISTEN      
 
[root@k8s-master ingress]# kubectl get svc
NAME         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)             AGE
......
tomcat       ClusterIP   10.104.158.148   <none>        8080/TCP,8009/TCP   28m
```

（3）编写tomcat的ingress规则，并创建ingress资源

```yaml
[root@k8s-master ingress]# cp ingress-myapp.yaml ingress-tomcat.yaml
[root@k8s-master ingress]# vim ingress-tomcat.yaml 
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: tomcat
  namespace: default
  annotations:
    kubernetes.io/ingress.class: "nginx"
spec:
  rules:
  - host: tomcat.magedu.com    #主机域名
    http:
      paths:
      - path:
        backend:
          serviceName: tomcat
          servicePort: 8080
[root@k8s-master ingress]# kubectl apply -f ingress-tomcat.yaml 
ingress.extensions/tomcat created
```

（4）查看ingress具体信息

```makefile
[root@k8s-master ingress]# kubectl get ingress
NAME            HOSTS               ADDRESS   PORTS     AGE
ingress-myapp   myapp.magedu.com              80        3h
tomcat          tomcat.magedu.com             80        5s
[root@k8s-master ingress]# kubectl describe ingress
Name:             ingress-myapp
Namespace:        default
Address:          
Default backend:  default-http-backend:80 (<none>)
Rules:
  Host              Path  Backends
  ----              ----  --------
  myapp.magedu.com  
                       myapp:80 (<none>)
Annotations:
  kubectl.kubernetes.io/last-applied-configuration:  {"apiVersion":"extensions/v1beta1","kind":"Ingress","metadata":{"annotations":{"kubernetes.io/ingress.class":"nginx"},"name":"ingress-myapp","namespace":"default"},"spec":{"rules":[{"host":"myapp.magedu.com","http":{"paths":[{"backend":{"serviceName":"myapp","servicePort":80},"path":null}]}}]}}
 
  kubernetes.io/ingress.class:  nginx
Events:                         <none>
 
 
Name:             tomcat
Namespace:        default
Address:          
Default backend:  default-http-backend:80 (<none>)
Rules:
  Host               Path  Backends
  ----               ----  --------
  tomcat.magedu.com  
                        tomcat:8080 (<none>)
Annotations:
  kubectl.kubernetes.io/last-applied-configuration:  {"apiVersion":"extensions/v1beta1","kind":"Ingress","metadata":{"annotations":{"kubernetes.io/ingress.class":"nginx"},"name":"tomcat","namespace":"default"},"spec":{"rules":[{"host":"tomcat.magedu.com","http":{"paths":[{"backend":{"serviceName":"tomcat","servicePort":8080},"path":null}]}}]}}
 
  kubernetes.io/ingress.class:  nginx
Events:
  Type    Reason  Age   From                      Message
  ----    ------  ----  ----                      -------
  Normal  CREATE  2m    nginx-ingress-controller  Ingress default/tomcat
```

（5）测试访问：tomcat.mageud.com:30080
![img](https://img2018.cnblogs.com/blog/1349539/201809/1349539-20180930155902614-1149294054.png)

（6）总结
从前面的部署过程中，可以再次进行总结部署的流程如下：
①下载Ingress-controller相关的YAML文件，并给Ingress-controller创建独立的名称空间；
②部署后端的服务，如myapp，并通过service进行暴露；
③部署Ingress-controller的service，以实现接入集群外部流量；
④部署Ingress，进行定义规则，使Ingress-controller和后端服务的Pod组进行关联。
本次部署后的说明图如下：
![img](https://img2018.cnblogs.com/blog/1349539/201809/1349539-20180930160336958-1687092087.png)

### 四、构建TLS站点

（1）准备证书

```vbnet
[root@k8s-master ingress]# openssl genrsa -out tls.key 2048 
Generating RSA private key, 2048 bit long modulus
.......+++
.......................+++
e is 65537 (0x10001)
 
[root@k8s-master ingress]# openssl req -new -x509 -key tls.key -out tls.crt -subj /C=CN/ST=Beijing/L=Beijing/O=DevOps/CN=tomcat.magedu.com
```

（2）生成secret

```yaml
[root@k8s-master ingress]# kubectl create secret tls tomcat-ingress-secret --cert=tls.crt --key=tls.key
secret/tomcat-ingress-secret created
[root@k8s-master ingress]# kubectl get secret
NAME                    TYPE                                  DATA      AGE
default-token-j5pf5     kubernetes.io/service-account-token   3         39d
tomcat-ingress-secret   kubernetes.io/tls                     2         9s
[root@k8s-master ingress]# kubectl describe secret tomcat-ingress-secret
Name:         tomcat-ingress-secret
Namespace:    default
Labels:       <none>
Annotations:  <none>
 
Type:  kubernetes.io/tls
 
Data
====
tls.crt:  1294 bytes
tls.key:  1679 bytes
```

（3）创建ingress

```makefile
[root@k8s-master ingress]# kubectl explain ingress.spec
[root@k8s-master ingress]# kubectl explain ingress.spec.tls
[root@k8s-master ingress]# cp ingress-tomcat.yaml ingress-tomcat-tls.yaml
[root@k8s-master ingress]# vim ingress-tomcat-tls.yaml 
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: ingress-tomcat-tls
  namespace: default
  annotations:
    kubernetes.io/ingress.class: "nginx"
spec:
  tls:
  - hosts:
    - tomcat.magedu.com
    secretName: tomcat-ingress-secret
  rules:
  - host: tomcat.magedu.com
    http:
      paths:
      - path:
        backend:
          serviceName: tomcat
          servicePort: 8080
 
[root@k8s-master ingress]# kubectl apply -f ingress-tomcat-tls.yaml 
ingress.extensions/ingress-tomcat-tls created
[root@k8s-master ingress]# kubectl get ingress
NAME                 HOSTS               ADDRESS   PORTS     AGE
ingress-myapp        myapp.magedu.com              80        4h
ingress-tomcat-tls   tomcat.magedu.com             80, 443   5s
tomcat               tomcat.magedu.com             80        1h
[root@k8s-master ingress]# kubectl describe ingress ingress-tomcat-tls
Name:             ingress-tomcat-tls
Namespace:        default
Address:          
Default backend:  default-http-backend:80 (<none>)
TLS:
  tomcat-ingress-secret terminates tomcat.magedu.com
Rules:
  Host               Path  Backends
  ----               ----  --------
  tomcat.magedu.com  
                        tomcat:8080 (<none>)
Annotations:
  kubectl.kubernetes.io/last-applied-configuration:  {"apiVersion":"extensions/v1beta1","kind":"Ingress","metadata":{"annotations":{"kubernetes.io/ingress.class":"nginx"},"name":"ingress-tomcat-tls","namespace":"default"},"spec":{"rules":[{"host":"tomcat.magedu.com","http":{"paths":[{"backend":{"serviceName":"tomcat","servicePort":8080},"path":null}]}}],"tls":[{"hosts":["tomcat.magedu.com"],"secretName":"tomcat-ingress-secret"}]}}
 
  kubernetes.io/ingress.class:  nginx
Events:
  Type    Reason  Age   From                      Message
  ----    ------  ----  ----                      -------
  Normal  CREATE  20s   nginx-ingress-controller  Ingress default/ingress-tomcat-tls
```

（4）访问测试：[https://tomcat.magedu.com:30443](https://tomcat.magedu.com:30443/)

![img](https://img2018.cnblogs.com/blog/1349539/201809/1349539-20180930174510553-912620418.png)