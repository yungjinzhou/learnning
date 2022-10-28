# Kubernetes学习之路（十三）之Pod控制器--DaemonSet



## 一、什么是DaemonSet？

DaemonSet 确保全部（或者一些）Node 上运行一个 Pod 的副本。当有 Node 加入集群时，也会为他们新增一个 Pod 。当有 Node 从集群移除时，这些 Pod 也会被回收。删除 DaemonSet 将会删除它创建的所有 Pod。

使用 DaemonSet 的一些典型用法：

- 运行集群存储 daemon，例如在每个 Node 上运行 `glusterd`、`ceph`。
- 在每个 Node 上运行日志收集 daemon，例如`fluentd`、`logstash`。
- 在每个 Node 上运行监控 daemon，例如 [Prometheus Node Exporter](https://github.com/prometheus/node_exporter)、`collectd`、Datadog 代理、New Relic 代理，或 Ganglia `gmond`。

一个简单的用法是，在所有的 Node 上都存在一个 DaemonSet，将被作为每种类型的 daemon 使用。 一个稍微复杂的用法可能是，对单独的每种类型的 daemon 使用多个 DaemonSet，但具有不同的标志，和/或对不同硬件类型具有不同的内存、CPU要求。

## 二、编写DaemonSet Spec

**（1）必需字段**

和其它所有 Kubernetes 配置一样，DaemonSet 需要 `apiVersion`、`kind` 和 `metadata`字段。

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master ~]# kubectl explain daemonset
KIND:     DaemonSet
VERSION:  extensions/v1beta1

DESCRIPTION:
     DEPRECATED - This group version of DaemonSet is deprecated by
     apps/v1beta2/DaemonSet. See the release notes for more information.
     DaemonSet represents the configuration of a daemon set.

FIELDS:
   apiVersion    <string>
     APIVersion defines the versioned schema of this representation of an
     object. Servers should convert recognized schemas to the latest internal
     value, and may reject unrecognized values. More info:
     https://git.k8s.io/community/contributors/devel/api-conventions.md#resources

   kind    <string>
     Kind is a string value representing the REST resource this object
     represents. Servers may infer this from the endpoint the client submits
     requests to. Cannot be updated. In CamelCase. More info:
     https://git.k8s.io/community/contributors/devel/api-conventions.md#types-kinds

   metadata    <Object>
     Standard object's metadata. More info:
     https://git.k8s.io/community/contributors/devel/api-conventions.md#metadata

   spec    <Object>
     The desired behavior of this daemon set. More info:
     https://git.k8s.io/community/contributors/devel/api-conventions.md#spec-and-status

   status    <Object>
     The current status of this daemon set. This data may be out of date by some
     window of time. Populated by the system. Read-only. More info:
     https://git.k8s.io/community/contributors/devel/api-conventions.md#spec-and-status
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

**（2）Pod模板**

`.spec` 唯一必需的字段是 `.spec.template`。

`.spec.template` 是一个 [Pod 模板](https://kubernetes.io/docs/user-guide/replication-controller/#pod-template)。 它与 [Pod](https://kubernetes.io/docs/user-guide/pods) 具有相同的 schema，除了它是嵌套的，而且不具有 `apiVersion` 或 `kind` 字段。

Pod 除了必须字段外，在 DaemonSet 中的 Pod 模板必须指定合理的标签（查看 [pod selector](https://jimmysong.io/kubernetes-handbook/concepts/daemonset.html#pod-selector)）。

在 DaemonSet 中的 Pod 模板必需具有一个值为 `Always` 的 [`RestartPolicy`](https://kubernetes.io/docs/user-guide/pod-states)，或者未指定它的值，默认是 `Always`。

```
[root@k8s-master ~]# kubectl explain daemonset.spec.template.spec
```

 **（3）Pod Seletor**

`.spec.selector` 字段表示 Pod Selector，它与 [Job](https://kubernetes.io/docs/concepts/jobs/run-to-completion-finite-workloads/) 或其它资源的 `.sper.selector` 的原理是相同的。

`spec.selector` 表示一个对象，它由如下两个字段组成：

- `matchLabels` - 与 [ReplicationController](https://kubernetes.io/docs/concepts/workloads/controllers/replicationcontroller/) 的 `.spec.selector` 的原理相同。
- `matchExpressions` - 允许构建更加复杂的 Selector，可以通过指定 key、value 列表，以及与 key 和 value 列表的相关的操作符。

当上述两个字段都指定时，结果表示的是 AND 关系。

如果指定了 `.spec.selector`，必须与 `.spec.template.metadata.labels` 相匹配。如果没有指定，它们默认是等价的。如果与它们配置的不匹配，则会被 API 拒绝。

如果 Pod 的 label 与 selector 匹配，或者直接基于其它的 DaemonSet、或者 Controller（例如 ReplicationController），也不可以创建任何 Pod。 否则 DaemonSet Controller 将认为那些 Pod 是它创建的。Kubernetes 不会阻止这样做。一个场景是，可能希望在一个具有不同值的、用来测试用的 Node 上手动创建 Pod。

**（4）Daemon Pod通信**

与 DaemonSet 中的 Pod 进行通信，几种可能的模式如下：

- Push：配置 DaemonSet 中的 Pod 向其它 Service 发送更新，例如统计数据库。它们没有客户端。
- NodeIP 和已知端口：DaemonSet 中的 Pod 可以使用 `hostPort`，从而可以通过 Node IP 访问到 Pod。客户端能通过某种方法知道 Node IP 列表，并且基于此也可以知道端口。
- DNS：创建具有相同 Pod Selector 的 [Headless Service](https://kubernetes.io/docs/user-guide/services/#headless-services)，然后通过使用 `endpoints` 资源或从 DNS 检索到多个 A 记录来发现 DaemonSet。
- Service：创建具有相同 Pod Selector 的 Service，并使用该 Service 访问到某个随机 Node 上的 daemon。（没有办法访问到特定 Node）

##  三、创建redis-filebeat的DaemonSet演示

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
（1）编辑daemonSet的yaml文件
可以在同一个yaml文件中定义多个资源，这里将redis和filebeat定在一个文件当中

[root@k8s-master mainfests]# vim ds-demo.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
      role: logstor
  template:
    metadata:
      labels:
        app: redis
        role: logstor
    spec:
      containers:
      - name: redis
        image: redis:4.0-alpine
        ports:
        - name: redis
          containerPort: 6379
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: filebeat-ds
  namespace: default
spec:
  selector:
    matchLabels:
      app: filebeat
      release: stable
  template:
    metadata:
      labels: 
        app: filebeat
        release: stable
    spec:
      containers:
      - name: filebeat
        image: ikubernetes/filebeat:5.6.5-alpine
        env:
        - name: REDIS_HOST
          value: redis.default.svc.cluster.local
        - name: REDIS_LOG_LEVEL
          value: info

（2）创建pods                
[root@k8s-master mainfests]# kubectl apply -f ds-demo.yaml
deployment.apps/redis created
daemonset.apps/filebeat-ds created

（3）暴露端口
[root@k8s-master mainfests]# kubectl expose deployment redis --port=6379
service/redis exposed
[root@k8s-master mainfests]# kubectl get svc
NAME         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
kubernetes   ClusterIP   10.96.0.1        <none>        443/TCP        16d
myapp        NodePort    10.106.67.242    <none>        80:32432/TCP   13d
nginx        ClusterIP   10.106.162.254   <none>        80/TCP         14d
redis        ClusterIP   10.107.163.143   <none>        6379/TCP       4s

[root@k8s-master mainfests]# kubectl get pods
NAME                     READY     STATUS    RESTARTS   AGE
filebeat-ds-rpp9p        1/1       Running   0          5m
filebeat-ds-vwx7d        1/1       Running   0          5m
pod-demo                 2/2       Running   6          5d
redis-5b5d6fbbbd-v82pw   1/1       Running   0          36s

（4）测试redis是否收到日志
[root@k8s-master mainfests]# kubectl exec -it redis-5b5d6fbbbd-v82pw -- /bin/sh
/data # netstat -tnl
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       
tcp        0      0 0.0.0.0:6379            0.0.0.0:*               LISTEN      
tcp        0      0 :::6379                 :::*                    LISTEN      

/data # nslookup redis.default.svc.cluster.local
nslookup: can't resolve '(null)': Name does not resolve

Name:      redis.default.svc.cluster.local
Address 1: 10.107.163.143 redis.default.svc.cluster.local

/data # redis-cli -h redis.default.svc.cluster.local
redis.default.svc.cluster.local:6379> KEYS *　　#由于redis在filebeat后面才启动，日志可能已经发走了，所以查看key为空
(empty list or set)

[root@k8s-master mainfests]# kubectl get pods
NAME                     READY     STATUS    RESTARTS   AGE
filebeat-ds-rpp9p        1/1       Running   0          14m
filebeat-ds-vwx7d        1/1       Running   0          14m
pod-demo                 2/2       Running   6          5d
redis-5b5d6fbbbd-v82pw   1/1       Running   0          9m
[root@k8s-master mainfests]# kubectl exec -it filebeat-ds-rpp9p -- /bin/sh
/ # cat /etc/filebeat/filebeat.yml 
filebeat.registry_file: /var/log/containers/filebeat_registry
filebeat.idle_timeout: 5s
filebeat.spool_size: 2048

logging.level: info

filebeat.prospectors:
- input_type: log
  paths:
    - "/var/log/containers/*.log"
    - "/var/log/docker/containers/*.log"
    - "/var/log/startupscript.log"
    - "/var/log/kubelet.log"
    - "/var/log/kube-proxy.log"
    - "/var/log/kube-apiserver.log"
    - "/var/log/kube-controller-manager.log"
    - "/var/log/kube-scheduler.log"
    - "/var/log/rescheduler.log"
    - "/var/log/glbc.log"
    - "/var/log/cluster-autoscaler.log"
  symlinks: true
  json.message_key: log
  json.keys_under_root: true
  json.add_error_key: true
  multiline.pattern: '^\s'
  multiline.match: after
  document_type: kube-logs
  tail_files: true
  fields_under_root: true

output.redis:
  hosts: ${REDIS_HOST:?No Redis host configured. Use env var REDIS_HOST to set host.}
  key: "filebeat"

[root@k8s-master mainfests]# kubectl get pods -l app=filebeat -o wide
NAME                READY     STATUS    RESTARTS   AGE       IP            NODE
filebeat-ds-rpp9p   1/1       Running   0          16m       10.244.2.12   k8s-node02
filebeat-ds-vwx7d   1/1       Running   0          16m       10.244.1.15   k8s-node01
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

## 四、DaemonSet的滚动更新

DaemonSet有两种更新策略类型：

- OnDelete：这是向后兼容性的默认更新策略。使用 `OnDelete`更新策略，在更新DaemonSet模板后，只有在手动删除旧的DaemonSet pod时才会创建新的DaemonSet pod。这与Kubernetes 1.5或更早版本中DaemonSet的行为相同。
- RollingUpdate：使用`RollingUpdate`更新策略，在更新DaemonSet模板后，旧的DaemonSet pod将被终止，并且将以受控方式自动创建新的DaemonSet pod。

要启用DaemonSet的滚动更新功能，必须将其设置 `.spec.updateStrategy.type`为`RollingUpdate`。

（1）查看当前的更新策略：

```
[root@k8s-master mainfests]# kubectl get ds/filebeat-ds -o go-template='{{.spec.updateStrategy.type}}{{"\n"}}'
RollingUpdate
```

（2）更新DaemonSet模板

对`RollingUpdate`DaemonSet的任何更新都`.spec.template`将触发滚动更新。这可以通过几个不同的`kubectl`命令来完成。

声明式命令方式：

如果使用配置文件进行更新DaemonSet，可以使用kubectl aapply：

```
kubectl apply -f ds-demo.yaml
```

补丁式命令方式：

```
kubectl edit ds/filebeat-ds

kubectl patch ds/filebeat-ds -p=<strategic-merge-patch>
```

仅仅更新容器镜像还可以使用以下命令：

```
kubectl set image ds/<daemonset-name> <container-name>=<container-new-image>
```

下面对filebeat-ds的镜像进行版本更新，如下：

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master mainfests]# kubectl set image daemonsets filebeat-ds filebeat=ikubernetes/filebeat:5.6.6-alpine
daemonset.extensions/filebeat-ds image updated

[root@k8s-master mainfests]# kubectl get pods -w　　#观察滚动更新状态
NAME                     READY     STATUS        RESTARTS   AGE
filebeat-ds-rpp9p        1/1       Running       0          27m
filebeat-ds-vwx7d        0/1       Terminating   0          27m
pod-demo                 2/2       Running       6          5d
redis-5b5d6fbbbd-v82pw   1/1       Running       0          23m
filebeat-ds-vwx7d   0/1       Terminating   0         27m
filebeat-ds-vwx7d   0/1       Terminating   0         27m
filebeat-ds-s466l   0/1       Pending   0         0s
filebeat-ds-s466l   0/1       ContainerCreating   0         0s
filebeat-ds-s466l   1/1       Running   0         13s
filebeat-ds-rpp9p   1/1       Terminating   0         28m
filebeat-ds-rpp9p   0/1       Terminating   0         28m
filebeat-ds-rpp9p   0/1       Terminating   0         28m
filebeat-ds-rpp9p   0/1       Terminating   0         28m
filebeat-ds-hxgdx   0/1       Pending   0         0s
filebeat-ds-hxgdx   0/1       ContainerCreating   0         0s
filebeat-ds-hxgdx   1/1       Running   0         28s

[root@k8s-master mainfests]# kubectl get pods
NAME                     READY     STATUS    RESTARTS   AGE
filebeat-ds-hxgdx        1/1       Running   0          2m
filebeat-ds-s466l        1/1       Running   0          2m
pod-demo                 2/2       Running   6          5d
redis-5b5d6fbbbd-v82pw   1/1       Running   0          25m
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

从上面的滚动更新，可以看到在更新过程中，是先终止旧的pod，再创建一个新的pod，逐步进行替换的，这就是DaemonSet的滚动更新策略！