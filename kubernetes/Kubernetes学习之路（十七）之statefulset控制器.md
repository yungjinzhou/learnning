# Kubernetes学习之路（十七）之statefulset控制器

目录

- [一、statefulset简介](https://www.cnblogs.com/linuxk/p/9767736.html#一statefulset简介)
- [二、为什么要有headless？？](https://www.cnblogs.com/linuxk/p/9767736.html#二为什么要有headless)
- [三、为什么要 有volumeClainTemplate？？](https://www.cnblogs.com/linuxk/p/9767736.html#三为什么要-有volumeclaintemplate)
- 四、statefulSet使用演示
  - [（1）查看statefulset的定义](https://www.cnblogs.com/linuxk/p/9767736.html#1查看statefulset的定义)
  - [（2）清单定义StatefulSet](https://www.cnblogs.com/linuxk/p/9767736.html#2清单定义statefulset)
  - [（3）删除前期的操作](https://www.cnblogs.com/linuxk/p/9767736.html#3删除前期的操作)
  - [（4）修改pv的大小为2Gi](https://www.cnblogs.com/linuxk/p/9767736.html#4修改pv的大小为2gi)
  - [（5）创建statefulset](https://www.cnblogs.com/linuxk/p/9767736.html#5创建statefulset)
- 五、滚动更新、扩展伸缩、版本升级、修改更新策略
  - [1、滚动更新](https://www.cnblogs.com/linuxk/p/9767736.html#1滚动更新)
  - [2、扩展伸缩](https://www.cnblogs.com/linuxk/p/9767736.html#2扩展伸缩)
  - [3、更新策略和版本升级](https://www.cnblogs.com/linuxk/p/9767736.html#3更新策略和版本升级)



# 一、statefulset简介

>     从前面的学习我们知道使用Deployment创建的pod是无状态的，当挂载了Volume之后，如果该pod挂了，Replication Controller会再启动一个pod来保证可用性，但是由于pod是无状态的，pod挂了就会和之前的Volume的关系断开，新创建的Pod无法找到之前的Pod。但是对于用户而言，他们对底层的Pod挂了是没有感知的，但是当Pod挂了之后就无法再使用之前挂载的存储卷。
>
>     为了解决这一问题，就引入了StatefulSet用于保留Pod的状态信息。
>
>     StatefulSet是为了解决有状态服务的问题（对应Deployments和ReplicaSets是为无状态服务而设计），其应用场景包括：

- 1、稳定的持久化存储，即Pod重新调度后还是能访问到相同的持久化数据，基于PVC来实现
- 2、稳定的网络标志，即Pod重新调度后其PodName和HostName不变，基于Headless Service（即没有Cluster IP的Service）来实现
- 3、有序部署，有序扩展，即Pod是有顺序的，在部署或者扩展的时候要依据定义的顺序依次依次进行（即从0到N-1，在下一个Pod运行之前所有之前的Pod必须都是Running和Ready状态），基于init containers来实现
- 4、有序收缩，有序删除（即从N-1到0）
- 5、有序的滚动更新

> 从上面的应用场景可以发现，StatefulSet由以下几个部分组成：
>
> - Headless Service（无头服务）用于为Pod资源标识符生成可解析的DNS记录。
> - volumeClaimTemplates （存储卷申请模板）基于静态或动态PV供给方式为Pod资源提供专有的固定存储。
> - StatefulSet，用于管控Pod资源。

# 二、为什么要有headless？？

>     在deployment中，每一个pod是没有名称，是随机字符串，是无序的。而statefulset中是要求有序的，每一个pod的名称必须是固定的。当节点挂了，重建之后的标识符是不变的，每一个节点的节点名称是不能改变的。pod名称是作为pod识别的唯一标识符，必须保证其标识符的稳定并且唯一。
>     为了实现标识符的稳定，这时候就需要一个headless service 解析直达到pod，还需要给pod配置一个唯一的名称。

# 三、为什么要 有volumeClainTemplate？？

>     大部分有状态副本集都会用到持久存储，比如分布式系统来说，由于数据是不一样的，每个节点都需要自己专用的存储节点。而在deployment中pod模板中创建的存储卷是一个共享的存储卷，多个pod使用同一个存储卷，而statefulset定义中的每一个pod都不能使用同一个存储卷，由此基于pod模板创建pod是不适应的，这就需要引入volumeClainTemplate，当在使用statefulset创建pod时，会自动生成一个PVC，从而请求绑定一个PV，从而有自己专用的存储卷。Pod名称、PVC和PV关系图如下：
> ![img](https://img2018.cnblogs.com/blog/1349539/201903/1349539-20190307152625497-1629030475.png)

# 四、statefulSet使用演示

> 在创建StatefulSet之前需要准备的东西，值得注意的是创建顺序非常关键，创建顺序如下：
> 1、Volume
> 2、Persistent Volume
> 3、Persistent Volume Claim
> 4、Service
> 5、StatefulSet
> Volume可以有很多种类型，比如nfs、glusterfs等，我们这里使用的ceph RBD来创建。

## （1）查看statefulset的定义

```vbnet
[root@k8s-master ~]# kubectl explain statefulset
KIND:     StatefulSet
VERSION:  apps/v1
 
DESCRIPTION:
     StatefulSet represents a set of pods with consistent identities. Identities
     are defined as: - Network: A single stable DNS and hostname. - Storage: As
     many VolumeClaims as requested. The StatefulSet guarantees that a given
     network identity will always map to the same storage identity.
 
FIELDS:
   apiVersion	<string>
   kind	<string>
   metadata	<Object>
   spec	<Object>
   status	<Object>
[root@k8s-master ~]# kubectl explain statefulset.spec
KIND:     StatefulSet
VERSION:  apps/v1
 
RESOURCE: spec <Object>
 
DESCRIPTION:
     Spec defines the desired identities of pods in this set.
 
     A StatefulSetSpec is the specification of a StatefulSet.
 
FIELDS:
   podManagementPolicy	<string>  #Pod管理策略
   replicas	<integer>    #副本数量
   revisionHistoryLimit	<integer>   #历史版本限制
   selector	<Object> -required-    #选择器，必选项
   serviceName	<string> -required-  #服务名称，必选项
   template	<Object> -required-    #模板，必选项
   updateStrategy	<Object>       #更新策略
   volumeClaimTemplates	<[]Object>   #存储卷申请模板，列表对象形式
```

## （2）清单定义StatefulSet

> 如上所述，一个完整的StatefulSet控制器由一个Headless Service、一个StatefulSet和一个volumeClaimTemplate组成。如下资源清单中的定义：

```yaml
[root@k8s-master mainfests]# vim stateful-demo.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-svc
  labels:
    app: myapp-svc
spec:
  ports:
  - port: 80
    name: web
  clusterIP: None
  selector:
    app: myapp-pod
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: myapp
spec:
  serviceName: myapp-svc
  replicas: 3
  selector:
    matchLabels:
      app: myapp-pod
  template:
    metadata:
      labels:
        app: myapp-pod
    spec:
      containers:
      - name: myapp
        image: ikubernetes/myapp:v1
        ports:
        - containerPort: 80
          name: web
        volumeMounts:
        - name: myappdata
          mountPath: /usr/share/nginx/html
  volumeClaimTemplates:
  - metadata:
      name: myappdata
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 2Gi
```

> 解析上例：由于StatefulSet资源依赖于一个实现存在的Headless类型的Service资源，所以需要先定义一个名为myapp-svc的Headless Service资源，用于为关联到每个Pod资源创建DNS资源记录。接着定义了一个名为myapp的StatefulSet资源，它通过Pod模板创建了3个Pod资源副本，并基于volumeClaimTemplates向前面创建的PV进行了请求大小为2Gi的专用存储卷。

## （3）删除前期的操作

```perl
[root@k8s-master mainfests]# kubectl get pv
NAME      CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM           STORAGECLASS   REASON    AGE
pv001     1Gi        RWO,RWX        Retain           Available                                            23h
pv002     2Gi        RWO            Retain           Available                                            23h
pv003     2Gi        RWO,RWX        Retain           Bound       default/mypvc                            23h
pv004     4Gi        RWO,RWX        Retain           Available                                            23h
pv005     5Gi        RWO,RWX        Retain           Available                                            23h
[root@k8s-master mainfests]# kubectl delete pods pod-vol-pvc
pod "pod-vol-pvc" deleted
[root@k8s-master mainfests]# kubectl delete pods/pod-cm-3 pods/pod-secret-env pods/pod-vol-hostpath
pod "pod-cm-3" deleted
pod "pod-secret-env" deleted
pod "pod-vol-hostpath" deleted
 
[root@k8s-master mainfests]# kubectl delete deploy/myapp-backend-pod deploy/tomcat-deploy
deployment.extensions "myapp-backend-pod" deleted
deployment.extensions "tomcat-deploy" deleted
 
[root@k8s-master mainfests]# kubectl delete pods pod-vol-pvc
pod "pod-vol-pvc" deleted
[root@k8s-master mainfests]# kubectl delete pods/pod-cm-3 pods/pod-secret-env pods/pod-vol-hostpath
pod "pod-cm-3" deleted
pod "pod-secret-env" deleted
pod "pod-vol-hostpath" deleted
 
[root@k8s-master mainfests]# kubectl delete deploy/myapp-backend-pod deploy/tomcat-deploy
deployment.extensions "myapp-backend-pod" deleted
deployment.extensions "tomcat-deploy" deleted
 
persistentvolumeclaim "mypvc" deleted
[root@k8s-master mainfests]# kubectl delete pv --all
persistentvolume "pv001" deleted
persistentvolume "pv002" deleted
persistentvolume "pv003" deleted
persistentvolume "pv004" deleted
persistentvolume "pv005" deleted
```

## （4）修改pv的大小为2Gi

```bash
[root@k8s-master ~]# cd mainfests/volumes
[root@k8s-master volumes]# vim pv-demo.yaml 
[root@k8s-master volumes]# kubectl apply -f pv-demo.yaml 
persistentvolume/pv001 created
persistentvolume/pv002 created
persistentvolume/pv003 created
persistentvolume/pv004 created
persistentvolume/pv005 created
[root@k8s-master volumes]# kubectl get pv
NAME      CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM     STORAGECLASS   REASON    AGE
pv001     1Gi        RWO,RWX        Retain           Available                                      5s
pv002     2Gi        RWO            Retain           Available                                      5s
pv003     2Gi        RWO,RWX        Retain           Available                                      5s
pv004     2Gi        RWO,RWX        Retain           Available                                      5s
pv005     2Gi        RWO,RWX        Retain           Available                                      5s
```

## （5）创建statefulset

```sql
[root@k8s-master mainfests]# kubectl apply -f stateful-demo.yaml 
service/myapp-svc created
statefulset.apps/myapp created
[root@k8s-master mainfests]# kubectl get svc  #查看创建的无头服务myapp-svc
NAME         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)             AGE
kubernetes   ClusterIP   10.96.0.1        <none>        443/TCP             50d
myapp-svc    ClusterIP   None             <none>        80/TCP              38s
[root@k8s-master mainfests]# kubectl get sts    #查看statefulset
NAME      DESIRED   CURRENT   AGE
myapp     3         3         55s
[root@k8s-master mainfests]# kubectl get pvc    #查看pvc绑定
NAME                STATUS    VOLUME    CAPACITY   ACCESS MODES   STORAGECLASS   AGE
myappdata-myapp-0   Bound     pv002     2Gi        RWO                           1m
myappdata-myapp-1   Bound     pv003     2Gi        RWO,RWX                       1m
myappdata-myapp-2   Bound     pv004     2Gi        RWO,RWX                       1m
[root@k8s-master mainfests]# kubectl get pv    #查看pv绑定
NAME      CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM                       STORAGECLASS   REASON    AGE
pv001     1Gi        RWO,RWX        Retain           Available                                                        6m
pv002     2Gi        RWO            Retain           Bound       default/myappdata-myapp-0                            6m
pv003     2Gi        RWO,RWX        Retain           Bound       default/myappdata-myapp-1                            6m
pv004     2Gi        RWO,RWX        Retain           Bound       default/myappdata-myapp-2                            6m
pv005     2Gi        RWO,RWX        Retain           Available                                                        6m
 
[root@k8s-master mainfests]# kubectl get pods   #查看Pod信息
NAME                     READY     STATUS    RESTARTS   AGE
myapp-0                  1/1       Running   0          2m
myapp-1                  1/1       Running   0          2m
myapp-2                  1/1       Running   0          2m
pod-vol-demo             2/2       Running   0          1d
redis-5b5d6fbbbd-q8ppz   1/1       Running   1          2d
```

> 当删除的时候是从myapp-2开始进行删除的，关闭是逆向关闭

```sql
[root@k8s-master mainfests]# kubectl delete -f stateful-demo.yaml 
service "myapp-svc" deleted
statefulset.apps "myapp" deleted
 
[root@k8s-master ~]# kubectl get pods -w
NAME                     READY     STATUS    RESTARTS   AGE
filebeat-ds-hxgdx        1/1       Running   1          33d
filebeat-ds-s466l        1/1       Running   2          33d
myapp-0                  1/1       Running   0          3m
myapp-1                  1/1       Running   0          3m
myapp-2                  1/1       Running   0          3m
pod-vol-demo             2/2       Running   0          1d
redis-5b5d6fbbbd-q8ppz   1/1       Running   1          2d
myapp-0   1/1       Terminating   0         3m
myapp-2   1/1       Terminating   0         3m
myapp-1   1/1       Terminating   0         3m
myapp-1   0/1       Terminating   0         3m
myapp-0   0/1       Terminating   0         3m
myapp-2   0/1       Terminating   0         3m
myapp-1   0/1       Terminating   0         3m
myapp-1   0/1       Terminating   0         3m
myapp-0   0/1       Terminating   0         4m
myapp-0   0/1       Terminating   0         4m
myapp-2   0/1       Terminating   0         3m
myapp-2   0/1       Terminating   0         3m
 
此时PVC依旧存在的，再重新创建pod时，依旧会重新去绑定原来的pvc
[root@k8s-master mainfests]# kubectl apply -f stateful-demo.yaml 
service/myapp-svc created
statefulset.apps/myapp created
 
[root@k8s-master mainfests]# kubectl get pvc
NAME                STATUS    VOLUME    CAPACITY   ACCESS MODES   STORAGECLASS   AGE
myappdata-myapp-0   Bound     pv002     2Gi        RWO                           5m
myappdata-myapp-1   Bound     pv003     2Gi        RWO,RWX                       5m
myappdata-myapp-2   Bound     pv004     2Gi        RWO,RWX                       5m
[root@k8s-master mainfests]# kubectl delete -f stateful-demo.yaml 
service "myapp-svc" deleted
statefulset.apps "myapp" deleted
 
[root@k8s-master ~]# kubectl get pods -w
NAME                     READY     STATUS    RESTARTS   AGE
filebeat-ds-hxgdx        1/1       Running   1          33d
filebeat-ds-s466l        1/1       Running   2          33d
myapp-0                  1/1       Running   0          3m
myapp-1                  1/1       Running   0          3m
myapp-2                  1/1       Running   0          3m
pod-vol-demo             2/2       Running   0          1d
redis-5b5d6fbbbd-q8ppz   1/1       Running   1          2d
myapp-0   1/1       Terminating   0         3m
myapp-2   1/1       Terminating   0         3m
myapp-1   1/1       Terminating   0         3m
myapp-1   0/1       Terminating   0         3m
myapp-0   0/1       Terminating   0         3m
myapp-2   0/1       Terminating   0         3m
myapp-1   0/1       Terminating   0         3m
myapp-1   0/1       Terminating   0         3m
myapp-0   0/1       Terminating   0         4m
myapp-0   0/1       Terminating   0         4m
myapp-2   0/1       Terminating   0         3m
myapp-2   0/1       Terminating   0         3m
 
此时PVC依旧存在的，再重新创建pod时，依旧会重新去绑定原来的pvc
[root@k8s-master mainfests]# kubectl apply -f stateful-demo.yaml 
service/myapp-svc created
statefulset.apps/myapp created
 
[root@k8s-master mainfests]# kubectl get pvc
NAME                STATUS    VOLUME    CAPACITY   ACCESS MODES   STORAGECLASS   AGE
myappdata-myapp-0   Bound     pv002     2Gi        RWO                           5m
myappdata-myapp-1   Bound     pv003     2Gi        RWO,RWX                       5m
myappdata-myapp-2   Bound     pv004     2Gi        RWO,RWX                       5m
```

# 五、滚动更新、扩展伸缩、版本升级、修改更新策略

## 1、滚动更新

> RollingUpdate 更新策略在 StatefulSet 中实现 Pod 的自动滚动更新。 当StatefulSet的 .spec.updateStrategy.type 设置为 RollingUpdate 时，默认为：RollingUpdate。StatefulSet 控制器将在 StatefulSet 中删除并重新创建每个 Pod。 它将以与 Pod 终止相同的顺序进行（从最大的序数到最小的序数），每次更新一个 Pod。 在更新其前身之前，它将等待正在更新的 Pod 状态变成正在运行并就绪。如下操作的滚动更新是有2-0的顺序更新。

```sql
[root@k8s-master mainfests]# vim stateful-demo.yaml  #修改image版本为v2
.....
image: ikubernetes/myapp:v2
....
[root@k8s-master mainfests]# kubectl apply -f stateful-demo.yaml 
service/myapp-svc unchanged
statefulset.apps/myapp configured
[root@k8s-master ~]# kubectl get pods -w   #查看滚动更新的过程
NAME                     READY     STATUS    RESTARTS   AGE
myapp-0                  1/1       Running   0          36m
myapp-1                  1/1       Running   0          36m
myapp-2                  1/1       Running   0          36m
 
myapp-2   1/1       Terminating   0         36m
myapp-2   0/1       Terminating   0         36m
myapp-2   0/1       Terminating   0         36m
myapp-2   0/1       Terminating   0         36m
myapp-2   0/1       Pending   0         0s
myapp-2   0/1       Pending   0         0s
myapp-2   0/1       ContainerCreating   0         0s
myapp-2   1/1       Running   0         2s
myapp-1   1/1       Terminating   0         36m
myapp-1   0/1       Terminating   0         36m
myapp-1   0/1       Terminating   0         36m
myapp-1   0/1       Terminating   0         36m
myapp-1   0/1       Pending   0         0s
myapp-1   0/1       Pending   0         0s
myapp-1   0/1       ContainerCreating   0         0s
myapp-1   1/1       Running   0         1s
myapp-0   1/1       Terminating   0         37m
myapp-0   0/1       Terminating   0         37m
myapp-0   0/1       Terminating   0         37m
myapp-0   0/1       Terminating   0         37m
```

> 在创建的每一个Pod中，每一个pod自己的名称都是可以被解析的，如下：

```vbnet
[root@k8s-master ~]# kubectl get pods -o wide
NAME                     READY     STATUS    RESTARTS   AGE       IP            NODE
myapp-0                  1/1       Running   0          8m        10.244.1.62   k8s-node01
myapp-1                  1/1       Running   0          8m        10.244.2.49   k8s-node02
myapp-2                  1/1       Running   0          8m        10.244.1.61   k8s-node01
 
[root@k8s-master mainfests]# kubectl exec -it myapp-0 -- /bin/sh
/ # nslookup myapp-0.myapp-svc.default.svc.cluster.local
nslookup: can't resolve '(null)': Name does not resolve
 
Name:      myapp-0.myapp-svc.default.svc.cluster.local
Address 1: 10.244.1.62 myapp-0.myapp-svc.default.svc.cluster.local
/ # nslookup myapp-1.myapp-svc.default.svc.cluster.local
nslookup: can't resolve '(null)': Name does not resolve
 
Name:      myapp-1.myapp-svc.default.svc.cluster.local
Address 1: 10.244.2.49 myapp-1.myapp-svc.default.svc.cluster.local
/ # nslookup myapp-2.myapp-svc.default.svc.cluster.local
nslookup: can't resolve '(null)': Name does not resolve
 
Name:      myapp-2.myapp-svc.default.svc.cluster.local
Address 1: 10.244.1.61 myapp-2.myapp-svc.default.svc.cluster.local
 
从上面的解析，我们可以看到在容器当中可以通过对Pod的名称进行解析到ip。其解析的域名格式如下：
pod_name.service_name.ns_name.svc.cluster.local
eg: myapp-0.myapp.default.svc.cluster.local
```

## 2、扩展伸缩

```sql
[root@k8s-master mainfests]# kubectl scale sts myapp --replicas=4  #扩容副本增加到4个
statefulset.apps/myapp scaled
[root@k8s-master ~]# kubectl get pods -w  #动态查看扩容
NAME                     READY     STATUS    RESTARTS   AGE
myapp-0                  1/1       Running   0          23m
myapp-1                  1/1       Running   0          23m
myapp-2                  1/1       Running   0          23m
 
myapp-3   0/1       Pending   0         0s
myapp-3   0/1       Pending   0         0s
myapp-3   0/1       ContainerCreating   0         0s
myapp-3   1/1       Running   0         1s
[root@k8s-master mainfests]# kubectl get pv  #查看pv绑定
NAME      CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM                       STORAGECLASS   REASON    AGE
pv001     1Gi        RWO,RWX        Retain           Available                                                        1h
pv002     2Gi        RWO            Retain           Bound       default/myappdata-myapp-0                            1h
pv003     2Gi        RWO,RWX        Retain           Bound       default/myappdata-myapp-1                            1h
pv004     2Gi        RWO,RWX        Retain           Bound       default/myappdata-myapp-2                            1h
pv005     2Gi        RWO,RWX        Retain           Bound       default/myappdata-myapp-3                            1h
 
[root@k8s-master mainfests]# kubectl patch sts myapp -p '{"spec":{"replicas":2}}'  #打补丁方式缩容
statefulset.apps/myapp patched
[root@k8s-master ~]# kubectl get pods -w  #动态查看缩容
NAME                     READY     STATUS    RESTARTS   AGE
myapp-0                  1/1       Running   0          25m
myapp-1                  1/1       Running   0          25m
myapp-2                  1/1       Running   0          25m
myapp-3                  1/1       Running   0          1m
myapp-3   1/1       Terminating   0         2m
myapp-3   0/1       Terminating   0         2m
myapp-3   0/1       Terminating   0         2m
myapp-3   0/1       Terminating   0         2m
myapp-2   1/1       Terminating   0         26m
myapp-2   0/1       Terminating   0         26m
myapp-2   0/1       Terminating   0         27m
myapp-2   0/1       Terminating   0         27m
```

## 3、更新策略和版本升级

> 修改更新策略，以partition方式进行更新，更新值为2，只有myapp编号大于等于2的才会进行更新。类似于金丝雀部署方式。

```perl
[root@k8s-master mainfests]# kubectl patch sts myapp -p '{"spec":{"updateStrategy":{"rollingUpdate":{"partition":2}}}}'
statefulset.apps/myapp patched
[root@k8s-master ~]# kubectl get sts myapp
NAME      DESIRED   CURRENT   AGE
myapp     4         4         1h
[root@k8s-master ~]# kubectl describe sts myapp
Name:               myapp
Namespace:          default
CreationTimestamp:  Wed, 10 Oct 2018 21:58:24 -0400
Selector:           app=myapp-pod
Labels:             <none>
Annotations:        kubectl.kubernetes.io/last-applied-configuration={"apiVersion":"apps/v1","kind":"StatefulSet","metadata":{"annotations":{},"name":"myapp","namespace":"default"},"spec":{"replicas":3,"selector":{"match...
Replicas:           4 desired | 4 total
Update Strategy:    RollingUpdate
  Partition:        2
......
 
```

> 版本升级，将image的版本升级为v3，升级后对比myapp-2和myapp-1的image版本是不同的。这样就实现了金丝雀发布的效果。

```ruby
[root@k8s-master mainfests]# kubectl set image sts/myapp myapp=ikubernetes/myapp:v3
statefulset.apps/myapp image updated
[root@k8s-master ~]# kubectl get sts -o wide
NAME      DESIRED   CURRENT   AGE       CONTAINERS   IMAGES
myapp     4         4         1h        myapp        ikubernetes/myapp:v3
[root@k8s-master ~]# kubectl get pods myapp-2 -o yaml |grep image
  - image: ikubernetes/myapp:v3
    imagePullPolicy: IfNotPresent
    image: ikubernetes/myapp:v3
    imageID: docker-pullable://ikubernetes/myapp@sha256:b8d74db2515d3c1391c78c5768272b9344428035ef6d72158fd9f6c4239b2c69
 
[root@k8s-master ~]# kubectl get pods myapp-1 -o yaml |grep image
  - image: ikubernetes/myapp:v2
    imagePullPolicy: IfNotPresent
    image: ikubernetes/myapp:v2
    imageID: docker-pullable://ikubernetes/myapp@sha256:85a2b81a62f09a414ea33b74fb8aa686ed9b168294b26b4c819df0be0712d358
```

> 将剩余的Pod也更新版本，只需要将更新策略的partition值改为0即可，如下：

```sql
[root@k8s-master mainfests]#  kubectl patch sts myapp -p '{"spec":{"updateStrategy":{"rollingUpdate":{"partition":0}}}}'
statefulset.apps/myapp patched
 
[root@k8s-master ~]# kubectl get pods -w
NAME                     READY     STATUS    RESTARTS   AGE
myapp-0                  1/1       Running   0          58m
myapp-1                  1/1       Running   0          58m
myapp-2                  1/1       Running   0          13m
myapp-3                  1/1       Running   0          13m
myapp-1   1/1       Terminating   0         58m
myapp-1   0/1       Terminating   0         58m
myapp-1   0/1       Terminating   0         58m
myapp-1   0/1       Terminating   0         58m
myapp-1   0/1       Pending   0         0s
myapp-1   0/1       Pending   0         0s
myapp-1   0/1       ContainerCreating   0         0s
myapp-1   1/1       Running   0         2s
myapp-0   1/1       Terminating   0         58m
myapp-0   0/1       Terminating   0         58m
myapp-0   0/1       Terminating   0         58m
myapp-0   0/1       Terminating   0         58m
myapp-0   0/1       Pending   0         0s
myapp-0   0/1       Pending   0         0s
myapp-0   0/1       ContainerCreating   0         0s
myapp-0   1/1       Running   0         2s
```

