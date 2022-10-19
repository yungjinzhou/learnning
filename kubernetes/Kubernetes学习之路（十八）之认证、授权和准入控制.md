# [Kubernetes学习之路（十八）之认证、授权和准入控制 ](https://www.cnblogs.com/linuxk/p/9772117.html)

API Server作为Kubernetes网关，是访问和管理资源对象的唯一入口，其各种集群组件访问资源都需要经过网关才能进行正常访问和管理。每一次的访问请求都需要进行合法性的检验，其中包括身份验证、操作权限验证以及操作规范验证等，需要通过一系列验证通过之后才能访问或者存储数据到etcd当中。如下图：

![img](https://img2018.cnblogs.com/blog/1349539/201903/1349539-20190307160125484-1365856991.png) 

## 一、ServiceAccount

Service account是为了方便Pod里面的进程调用Kubernetes API或其他外部服务而设计的。它与User account不同

- User account是为人设计的，而service account则是为Pod中的进程调用Kubernetes API而设计；
- User account是跨namespace的，而service account则是仅局限它所在的namespace；
- 每个namespace都会自动创建一个default service account
- Token controller检测service account的创建，并为它们创建[secret](https://www.kubernetes.org.cn/secret)
- 开启ServiceAccount Admission Controller后
  - 每个Pod在创建后都会自动设置spec.serviceAccount为default（除非指定了其他ServiceAccout）
  - 验证Pod引用的service account已经存在，否则拒绝创建
  - 如果Pod没有指定ImagePullSecrets，则把service account的ImagePullSecrets加到Pod中
  - 每个container启动后都会挂载该service account的token和ca.crt到/var/run/secrets/kubernetes.io/serviceaccount/

 当创建 pod 的时候，如果没有指定一个 service account，系统会自动在与该pod 相同的 namespace 下为其指派一个default service account。而pod和apiserver之间进行通信的账号，称为serviceAccountName。如下：

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master ~]# kubectl get pods
NAME                     READY     STATUS    RESTARTS   AGE
filebeat-ds-hxgdx        1/1       Running   1          34d
filebeat-ds-s466l        1/1       Running   2          34d
myapp-0                  1/1       Running   0          3h
myapp-1                  1/1       Running   0          3h
myapp-2                  1/1       Running   0          4h
myapp-3                  1/1       Running   0          4h
pod-vol-demo             2/2       Running   0          2d
redis-5b5d6fbbbd-q8ppz   1/1       Running   1          2d
[root@k8s-master ~]# kubectl get pods/myapp-0 -o yaml |grep "serviceAccountName"
  serviceAccountName: default
[root@k8s-master ~]# kubectl describe pods myapp-0
Name:               myapp-0
Namespace:          default
......
Volumes:
  ......
  default-token-j5pf5:
    Type:        Secret (a volume populated by a Secret)
    SecretName:  default-token-j5pf5
    Optional:    false
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

从上面可以看到每个Pod无论定义与否都会有个存储卷，这个存储卷为default-token-*** token令牌，这就是pod和serviceaccount认证信息。通过secret进行定义，由于认证信息属于敏感信息，所以需要保存在secret资源当中，并以存储卷的方式挂载到Pod当中。从而让Pod内运行的应用通过对应的secret中的信息来连接apiserver，并完成认证。每个 namespace 中都有一个默认的叫做 default 的 service account 资源。进行查看名称空间内的secret，也可以看到对应的default-token。让当前名称空间中所有的pod在连接apiserver时可以使用的预制认证信息，从而保证pod之间的通信。

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master ~]# kubectl get sa
NAME      SECRETS   AGE
default   1         50d
[root@k8s-master ~]# kubectl get sa -n ingress-nginx  #前期创建的ingress-nginx名称空间也存在这样的serviceaccount
NAME                           SECRETS   AGE
default                        1         11d
nginx-ingress-serviceaccount   1         11d
[root@k8s-master ~]# kubectl get secret
NAME                    TYPE                                  DATA      AGE
default-token-j5pf5     kubernetes.io/service-account-token   3         50d
mysecret                Opaque                                2         1d
tomcat-ingress-secret   kubernetes.io/tls                     2         10d
[root@k8s-master ~]# kubectl get secret -n ingress-nginx
NAME                                       TYPE                                  DATA      AGE
default-token-zl49j                        kubernetes.io/service-account-token   3         11d
nginx-ingress-serviceaccount-token-mcsf4   kubernetes.io/service-account-token   3         11d
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

而默认的service account 仅仅只能获取当前Pod自身的相关属性，无法观察到其他名称空间Pod的相关属性信息。如果想要扩展Pod，假设有一个Pod需要用于管理其他Pod或者是其他资源对象，是无法通过自身的名称空间的serviceaccount进行获取其他Pod的相关属性信息的，此时就需要进行手动创建一个serviceaccount，并在创建Pod时进行定义。那么serviceaccount该如何进行定义呢？？？实际上，service accout也属于一个k8s资源，如下查看service account的定义方式：

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master ~]# kubectl explain sa
KIND:     ServiceAccount
VERSION:  v1

DESCRIPTION:
     ServiceAccount binds together: * a name, understood by users, and perhaps
     by peripheral systems, for an identity * a principal that can be
     authenticated and authorized * a set of secrets

FIELDS:
   apiVersion    <string>
     APIVersion defines the versioned schema of this representation of an
     object. Servers should convert recognized schemas to the latest internal
     value, and may reject unrecognized values. More info:
     https://git.k8s.io/community/contributors/devel/api-conventions.md#resources

   automountServiceAccountToken    <boolean>
     AutomountServiceAccountToken indicates whether pods running as this service
     account should have an API token automatically mounted. Can be overridden
     at the pod level.

   imagePullSecrets    <[]Object>
     ImagePullSecrets is a list of references to secrets in the same namespace
     to use for pulling any images in pods that reference this ServiceAccount.
     ImagePullSecrets are distinct from Secrets because Secrets can be mounted
     in the pod, but ImagePullSecrets are only accessed by the kubelet. More
     info:
     https://kubernetes.io/docs/concepts/containers/images/#specifying-imagepullsecrets-on-a-pod

   kind    <string>
     Kind is a string value representing the REST resource this object
     represents. Servers may infer this from the endpoint the client submits
     requests to. Cannot be updated. In CamelCase. More info:
     https://git.k8s.io/community/contributors/devel/api-conventions.md#types-kinds

   metadata    <Object>
     Standard object's metadata. More info:
     https://git.k8s.io/community/contributors/devel/api-conventions.md#metadata

   secrets    <[]Object>
     Secrets is the list of secrets allowed to be used by pods running using
     this ServiceAccount. More info:
     https://kubernetes.io/docs/concepts/configuration/secret
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

### service account的创建

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master mainfests]# kubectl create serviceaccount mysa -o yaml --dry-run #不执行查看定义方式
apiVersion: v1
kind: ServiceAccount
metadata:
  creationTimestamp: null
  name: mysa

[root@k8s-master mainfests]# kubectl create serviceaccount mysa -o yaml --dry-run > serviceaccount.yaml  #直接导出为yaml定义文件，可以节省敲键盘的时间
[root@k8s-master mainfests]# kubectl apply -f serviceaccount.yaml 
serviceaccount/mysa created
[root@k8s-master mainfests]# kubectl get serviceaccount/mysa -o yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"v1","kind":"ServiceAccount","metadata":{"annotations":{},"creationTimestamp":null,"name":"mysa","namespace":"default"}}
  creationTimestamp: 2018-10-11T08:12:25Z
  name: mysa
  namespace: default
  resourceVersion: "432865"
  selfLink: /api/v1/namespaces/default/serviceaccounts/mysa
  uid: 62fc7782-cd2d-11e8-801a-000c2972dc1f
secrets:
- name: mysa-token-h2mgk
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

看到有一个 token 已经被自动创建，并被 service account 引用。设置非默认的 service account，只需要在 pod 的`spec.serviceAccountName` 字段中将name设置为您想要用的 service account 名字即可。在 pod 创建之初 service account 就必须已经存在，否则创建将被拒绝。需要注意的是不能更新已创建的 pod 的 service account。

###  serviceaccount的自定义使用

这里在default名称空间创建了一个sa为admin，可以看到已经自动生成了一个**Tokens：admin-token-7k5nr。**

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master mainfests]# kubectl create serviceaccount admin
serviceaccount/admin created
[root@k8s-master mainfests]# kubectl get sa
NAME      SECRETS   AGE
admin     1         3s
default   1         50d
[root@k8s-master mainfests]# kubectl describe sa/admin
Name:                admin
Namespace:           default
Labels:              <none>
Annotations:         <none>
Image pull secrets:  <none>
Mountable secrets:   admin-token-7k5nr
Tokens:              admin-token-7k5nr
Events:              <none>
[root@k8s-master mainfests]# kubectl get secret
NAME                    TYPE                                  DATA      AGE
admin-token-7k5nr       kubernetes.io/service-account-token   3         31s
default-token-j5pf5     kubernetes.io/service-account-token   3         50d
mysecret                Opaque                                2         1d
tomcat-ingress-secret   kubernetes.io/tls                     2         10d
[root@k8s-master mainfests]# vim pod-sa-demo.yaml　　#Pod中引用新建的serviceaccount
apiVersion: v1
kind: Pod
metadata:
  name: pod-sa-demo
  namespace: default
  labels:
    app: myapp
    tier: frontend
spec:
  containers:
  - name: myapp
    image: ikubernetes/myapp:v1
    ports:
    - name: http
      containerPort: 80
  serviceAccountName: admin
[root@k8s-master mainfests]# kubectl apply -f pod-sa-demo.yaml 
pod/pod-sa-demo created
[root@k8s-master mainfests]# kubectl describe pods pod-sa-demo
......
Volumes:
  admin-token-7k5nr:
    Type:        Secret (a volume populated by a Secret)
    SecretName:  admin-token-7k5nr
    Optional:    false
......
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

 在K8S集群当中，每一个用户对资源的访问都是需要通过apiserver进行通信认证才能进行访问的，那么在此机制当中，对资源的访问可以是token，也可以是通过配置文件的方式进行保存和使用认证信息，可以通过kubectl config进行查看配置，如下：

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master mainfests]# kubectl config view
apiVersion: v1
clusters:  #集群列表
- cluster:
    certificate-authority-data: REDACTED
    server: https://192.168.56.11:6443
  name: kubernetes
contexts:  #上下文列表
- context: #定义哪个集群被哪个用户访问
    cluster: kubernetes
    user: kubernetes-admin
  name: kubernetes-admin@kubernetes
current-context: kubernetes-admin@kubernetes  #当前上下文
kind: Config
preferences: {}
users:   #用户列表
- name: kubernetes-admin
  user:
    client-certificate-data: REDACTED
    client-key-data: REDACTED
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

在上面的配置文件当中，定义了集群、上下文以及用户。其中Config也是K8S的标准资源之一，在该配置文件当中定义了一个集群列表，指定的集群可以有多个；用户列表也可以有多个，指明集群中的用户；而在上下文列表当中，是进行定义可以使用哪个用户对哪个集群进行访问，以及当前使用的上下文是什么。如图：定义了用户kubernetes-admin可以对kubernetes该集群的访问，用户kubernetes-user1对Clluster1集群的访问

![img](https://img2018.cnblogs.com/blog/1349539/201810/1349539-20181013114713444-798210079.png)

###  自建证书和账号进行访问apiserver演示

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
（1）生成证书
[root@k8s-master pki]# (umask 077;openssl genrsa -out magedu.key 2048)
Generating RSA private key, 2048 bit long modulus
............................................................................................+++
...................................................................................+++
e is 65537 (0x10001)
[root@k8s-master pki]# ll magedu.key 
-rw------- 1 root root 1675 Oct 12 23:52 magedu.key

（2）使用ca.crt进行签署
[root@k8s-master pki]# openssl req -new -key magedu.key -out magedu.csr -subj "/CN=magedu"  证书签署请求

[root@k8s-master pki]# openssl x509 -req -in magedu.csr -CA ./ca.crt -CAkey ./ca.key -CAcreateserial -out magedu.crt -days 365  #证书签署
Signature ok
subject=/CN=magedu
Getting CA Private Key
[root@k8s-master pki]# openssl x509 -in magedu.crt -text -noout

（3）添加到用户认证
[root@k8s-master pki]# kubectl config set-credentials magedu --client-certificate=./magedu.crt --client-key=./magedu.key --embed-certs=true
User "magedu" set.

[root@k8s-master pki]# kubectl config set-context magedu@kubernetes --cluster=kubernetes --user=magedu
Context "magedu@kubernetes" created.

[root@k8s-master pki]# kubectl config view
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: REDACTED
    server: https://192.168.56.11:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: kubernetes-admin
  name: kubernetes-admin@kubernetes
- context:
    cluster: kubernetes
    user: magedu
  name: magedu@kubernetes
current-context: kubernetes-admin@kubernetes
kind: Config
preferences: {}
users:
- name: kubernetes-admin
  user:
    client-certificate-data: REDACTED
    client-key-data: REDACTED
- name: magedu
  user:
    client-certificate-data: REDACTED
    client-key-data: REDACTED

[root@k8s-master pki]# kubectl config use-context magedu@kubernetes
Switched to context "magedu@kubernetes".
[root@k8s-master pki]# kubectl get pods
No resources found.
Error from server (Forbidden): pods is forbidden: User "magedu" cannot list pods in the namespace "default"
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

从上面的演示，当切换成magedu用户进行访问集群时，由于magedu该账户没有管理集群的权限，所以在获取pods资源信息时，会提示Forrbidden。那么下面就再来了解一下怎么对账户进行授权！！！

## 二、RBAC----基于角色的访问控制

 Kubernetes的授权是基于插件形式的，其常用的授权插件有以下几种：

- Node（节点认证）
- ABAC(基于属性的访问控制)
- RBAC（基于角色的访问控制）
- Webhook（基于http回调机制的访问控制）

 让一个用户（Users）扮演一个角色（Role），角色拥有权限，从而让用户拥有这样的权限，随后在授权机制当中，只需要将权限授予某个角色，此时用户将获取对应角色的权限，从而实现角色的访问控制。如图：

![img](https://img2018.cnblogs.com/blog/1349539/201810/1349539-20181013104659832-1317864140.png)

 

基于角色的访问控制（Role-Based Access Control, 即”RBAC”）使用”rbac.authorization.k8s.io” API Group实现授权决策，允许管理员通过Kubernetes API动态配置策略。

在k8s的授权机制当中，采用RBAC的方式进行授权，其工作逻辑是　　把对对象的操作权限定义到一个角色当中，再将用户绑定到该角色，从而使用户得到对应角色的权限。此种方式仅作用于名称空间当中，这是什么意思呢？当User1绑定到Role角色当中，User1就获取了对该NamespaceA的操作权限，但是对NamespaceB是没有权限进行操作的，如get，list等操作。
另外，k8s为此还有一种集群级别的授权机制，就是定义一个集群角色（ClusterRole），对集群内的所有资源都有可操作的权限，从而将User2，User3通过ClusterRoleBinding到ClusterRole，从而使User2、User3拥有集群的操作权限。Role、RoleBinding、ClusterRole和ClusterRoleBinding的关系如下图：

![img](https://img2018.cnblogs.com/blog/1349539/201810/1349539-20181011164935788-596677596.png)

但是这里有2种绑定ClusterRoleBinding、RoleBinding。也可以使用RoleBinding去绑定ClusterRole。
当使用这种方式进行绑定时，用户仅能获取当前名称空间的所有权限。为什么这么绕呢？？举例有10个名称空间，每个名称空间都需要一个管理员，而该管理员的权限都是一致的。那么此时需要去定义这样的管理员，使用RoleBinding就需要创建10个Role，这样显得更加繁重。为此当使用RoleBinding去绑定一个ClusterRole时，该User仅仅拥有对当前名称空间的集群操作权限，换句话说，此时只需要创建一个ClusterRole就解决了以上的需求。

 **这里要注意的是：RoleBinding仅仅对当前名称空间有对应的权限。**

**在RBAC API中，一个角色包含了一套表示一组权限的规则。 权限以纯粹的累加形式累积（没有”否定”的规则）。 角色可以由命名空间（namespace）内的`Role`对象定义，而整个Kubernetes集群范围内有效的角色则通过`ClusterRole`对象实现。**

## 三、Kubernetes RBAC的演示

### **1、User --> Rolebinding --> Role**

####  **（1）角色的创建**

**一个`Role`对象只能用于授予对某一单一命名空间中资源的访问权限**

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master ~]# kubectl create role -h   #查看角色创建帮助
Create a role with single rule.

Examples:
  # Create a Role named "pod-reader" that allows user to perform "get", "watch" and "list" on pods
  kubectl create role pod-reader --verb=get --verb=list --verb=watch --resource=pods
  
  # Create a Role named "pod-reader" with ResourceName specified
  kubectl create role pod-reader --verb=get --resource=pods --resource-name=readablepod --resource-name=anotherpod
  
  # Create a Role named "foo" with API Group specified
  kubectl create role foo --verb=get,list,watch --resource=rs.extensions
  
  # Create a Role named "foo" with SubResource specified
  kubectl create role foo --verb=get,list,watch --resource=pods,pods/status

Options:
      --allow-missing-template-keys=true: If true, ignore any errors in templates when a field or map key is missing in
the template. Only applies to golang and jsonpath output formats.
      --dry-run=false: If true, only print the object that would be sent, without sending it.
  -o, --output='': Output format. One of:
json|yaml|name|go-template|go-template-file|templatefile|template|jsonpath|jsonpath-file.
      --resource=[]: Resource that the rule applies to
      --resource-name=[]: Resource in the white list that the rule applies to, repeat this flag for multiple items
      --save-config=false: If true, the configuration of current object will be saved in its annotation. Otherwise, the
annotation will be unchanged. This flag is useful when you want to perform kubectl apply on this object in the future.
      --template='': Template string or path to template file to use when -o=go-template, -o=go-template-file. The
template format is golang templates [http://golang.org/pkg/text/template/#pkg-overview].
      --validate=true: If true, use a schema to validate the input before sending it
      --verb=[]: Verb that applies to the resources contained in the rule

Usage:
  kubectl create role NAME --verb=verb --resource=resource.group/subresource [--resource-name=resourcename] [--dry-run]
[options]
使用kubectl create进行创建角色，指定角色名称，--verb指定权限，--resource指定资源或者资源组，--dry-run单跑模式并不会创建

Use "kubectl options" for a list of global command-line options (applies to all commands).

[root@k8s-master ~]# kubectl create role pods-reader --verb=get,list,watch --resource=pods --dry-run -o yaml #干跑模式查看role的定义

apiVersion: rbac.authorization.k8s.io/v1
kind: Role #资源类型
metadata:
  creationTimestamp: null
  name: pods-reader
rules:
- apiGroups:  #对那些api组内的资源进行操作
  - ""
  resources:  #对那些资源定义
  - pods
  verbs:      #操作权限定义
  - get
  - list
  - watch

[root@k8s-master ~]# cd mainfests/
[root@k8s-master mainfests]# kubectl create role pods-reader --verb=get,list,watch --resource=pods --dry-run -o yaml > role-demo.yaml

[root@k8s-master mainfests]# vim role-demo.yaml 
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pods-reader
  namespace: default
rules:
- apiGroups:
  - ""
  resources:
  - pods
  verbs:
  - get
  - list
  - watch

[root@k8s-master mainfests]# kubectl apply -f role-demo.yaml  #角色创建
role.rbac.authorization.k8s.io/pods-reader created
[root@k8s-master mainfests]# kubectl get role
NAME          AGE
pods-reader   3s
[root@k8s-master mainfests]# kubectl describe role pods-reader
Name:         pods-reader
Labels:       <none>
Annotations:  kubectl.kubernetes.io/last-applied-configuration={"apiVersion":"rbac.authorization.k8s.io/v1","kind":"Role","metadata":{"annotations":{},"name":"pods-reader","namespace":"default"},"rules":[{"apiGroup...
PolicyRule:
  Resources  Non-Resource URLs  Resource Names  Verbs
  ---------  -----------------  --------------  -----
  pods       []                 []              [get list watch]  #此处已经定义了pods-reader这个角色对pods资源拥有get、list、watch的权限
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

#### **（2）角色的绑定**

**`RoleBinding`可以引用在同一命名空间内定义的`Role`对象。**

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master ~]# kubectl create rolebinding -h  #角色绑定创建帮助
Create a RoleBinding for a particular Role or ClusterRole.

Examples:
  # Create a RoleBinding for user1, user2, and group1 using the admin ClusterRole
  kubectl create rolebinding admin --clusterrole=admin --user=user1 --user=user2 --group=group1

Options:
      --allow-missing-template-keys=true: If true, ignore any errors in templates when a field or map key is missing in
the template. Only applies to golang and jsonpath output formats.
      --clusterrole='': ClusterRole this RoleBinding should reference
      --dry-run=false: If true, only print the object that would be sent, without sending it.
      --generator='rolebinding.rbac.authorization.k8s.io/v1alpha1': The name of the API generator to use.
      --group=[]: Groups to bind to the role
  -o, --output='': Output format. One of:
json|yaml|name|templatefile|template|go-template|go-template-file|jsonpath-file|jsonpath.
      --role='': Role this RoleBinding should reference
      --save-config=false: If true, the configuration of current object will be saved in its annotation. Otherwise, the
annotation will be unchanged. This flag is useful when you want to perform kubectl apply on this object in the future.
      --serviceaccount=[]: Service accounts to bind to the role, in the format <namespace>:<name>
      --template='': Template string or path to template file to use when -o=go-template, -o=go-template-file. The
template format is golang templates [http://golang.org/pkg/text/template/#pkg-overview].
      --validate=true: If true, use a schema to validate the input before sending it

Usage:
  kubectl create rolebinding NAME --clusterrole=NAME|--role=NAME [--user=username] [--group=groupname]
[--serviceaccount=namespace:serviceaccountname] [--dry-run] [options]
使用kubectl create进行创建角色绑定，指定角色绑定的名称，--role|--clusterrole指定绑定哪个角色，--user指定哪个用户

Use "kubectl options" for a list of global command-line options (applies to all commands).

[root@k8s-master mainfests]# kubectl create rolebinding magedu-read-pods --role=pods-reader --user=magedu --dry-run -o yaml > rolebinding-demo.yaml
[root@k8s-master mainfests]# cat rolebinding-demo.yaml 
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  creationTimestamp: null
  name: magedu-read-pods
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: pods-reader
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: User
  name: magedu
[root@k8s-master mainfests]# kubectl apply -f rolebinding-demo.yaml  #创建角色绑定
rolebinding.rbac.authorization.k8s.io/magedu-read-pods created

[root@k8s-master mainfests]# kubectl describe rolebinding magedu-read-pods #查看角色绑定的信息，这里可以看到user：magedu绑定到了pods-reader这个角色上
Name:         magedu-read-pods
Labels:       <none>
Annotations:  kubectl.kubernetes.io/last-applied-configuration={"apiVersion":"rbac.authorization.k8s.io/v1","kind":"RoleBinding","metadata":{"annotations":{},"creationTimestamp":null,"name":"magedu-read-pods","name...
Role:
  Kind:  Role
  Name:  pods-reader
Subjects:
  Kind  Name    Namespace
  ----  ----    ---------
  User  magedu  

 [root@k8s-master ~]# kubectl config use-context magedu@kubernetes #切换magedu这个用户，并使用get获取pods资源信息
Switched to context "magedu@kubernetes".
[root@k8s-master ~]# kubectl get pods
NAME                     READY     STATUS    RESTARTS   AGE
filebeat-ds-hxgdx        1/1       Running   1          36d
filebeat-ds-s466l        1/1       Running   2          36d
myapp-0                  1/1       Running   0          2d
myapp-1                  1/1       Running   0          2d
myapp-2                  1/1       Running   0          2d
myapp-3                  1/1       Running   0          2d
pod-sa-demo              1/1       Running   0          1d
pod-vol-demo             2/2       Running   0          3d
redis-5b5d6fbbbd-q8ppz   1/1       Running   1          4d
[root@k8s-master ~]# kubectl get pods -n ingress-nginx  #测试获取ingress-nginx这个名称空间的pods信息
No resources found.
Error from server (Forbidden): pods is forbidden: User "magedu" cannot list pods in the namespace "ingress-nginx"
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

从上面的操作，可以总结出，role的定义和绑定，仅作用于当前名称空间，在获取ingress-nginx名称空间时，一样会出现Forbidden！！！

### 2、User --> Clusterrolebinding --> Clusterrole

####  **（1）clusterrole定义**

`ClusterRole`对象可以授予与`Role`对象相同的权限，但由于它们属于集群范围对象， 也可以使用它们授予对以下几种资源的访问权限：

- 集群范围资源（例如节点，即node）
- 非资源类型endpoint（例如”/healthz”）
- 跨所有命名空间的命名空间范围资源（例如pod，需要运行命令`kubectl get pods --all-namespaces`来查询集群中所有的pod）

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master mainfests]# kubectl config use-context kubernetes-admin@kubernetes  #切换会kubernetes-admin用户
Switched to context "kubernetes-admin@kubernetes".
[root@k8s-master mainfests]# kubectl create clusterrole cluster-read --verb=get,list,watch --resource=pods -o yaml > clusterrole-demo.yaml

[root@k8s-master mainfests]# vim clusterrole-demo.yaml #定义clusterrole和权限
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-read
rules:
- apiGroups:
  - ""
  resources:
  - pods
  verbs:
  - get
  - list
  - watch
[root@k8s-master mainfests]# kubectl apply -f clusterrole-demo.yaml  #创建clusterrole
clusterrole.rbac.authorization.k8s.io/cluster-read configured
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

这里我们需要切换回kubernetes-admin账户，是由于magedu账户不具备创建的权限，这也说明普通用户是无法进行创建K8S资源的，除非进行授权。如下，我们另开一个终端，将配置到一个普通用户ik8s上，使其使用magedu账户进行通信

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master ~]# useradd ik8s
[root@k8s-master ~]# cp -rp .kube/ /home/ik8s/
[root@k8s-master ~]# chown -R ik8s.ik8s /home/ik8s/
[root@k8s-master ~]# su - ik8s
[ik8s@k8s-master ~]$ kubectl config use-context magedu@kubernetes
Switched to context "magedu@kubernetes".
[ik8s@k8s-master ~]$ kubectl config view
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: REDACTED
    server: https://192.168.56.11:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: kubernetes-admin
  name: kubernetes-admin@kubernetes
- context:
    cluster: kubernetes
    user: magedu
  name: magedu@kubernetes
current-context: magedu@kubernetes
kind: Config
preferences: {}
users:
- name: kubernetes-admin
  user:
    client-certificate-data: REDACTED
    client-key-data: REDACTED
- name: magedu
  user:
    client-certificate-data: REDACTED
    client-key-data: REDACTED
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

#### **（2）clusterrolebinding定义**

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master mainfests]# kubectl get rolebinding  #获取角色绑定信息
NAME               AGE
magedu-read-pods   1h
[root@k8s-master mainfests]# kubectl delete rolebinding magedu-read-pods #删除前面的绑定
rolebinding.rbac.authorization.k8s.io "magedu-read-pods" deleted

[ik8s@k8s-master ~]$ kubectl get pods  #删除后，在ik8s普通用户上进行获取pods资源信息，就立马出现forbidden了
No resources found.
Error from server (Forbidden): pods is forbidden: User "magedu" cannot list pods in the namespace "default"

[root@k8s-master mainfests]# kubectl create clusterrolebinding magedu-read-all-pods --clusterrole=cluster-read --user=magedu --dry-run -o yaml > clusterrolebinding-demo.yaml
[root@k8s-master mainfests]# vim clusterrolebinding-demo.yaml  #创建角色绑定，将magedu绑定到clusterrole：magedu-read-all-pods上
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: magedu-read-all-pods
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-read
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: User
  name: magedu
  
[root@k8s-master mainfests]# kubectl get clusterrole
NAME                                                                   AGE
admin                                                                  52d
cluster-admin                                                          52d
cluster-read                                                           13m
......

[root@k8s-master mainfests]# kubectl apply -f clusterrolebinding-demo.yaml 
clusterrolebinding.rbac.authorization.k8s.io/magedu-read-all-pods created
[root@k8s-master mainfests]# kubectl get clusterrolebinding
NAME                                                   AGE
......
magedu-read-all-pods                                   10s

[root@k8s-master mainfests]# kubectl describe clusterrolebinding magedu-read-all-pods
Name:         magedu-read-all-pods
Labels:       <none>
Annotations:  kubectl.kubernetes.io/last-applied-configuration={"apiVersion":"rbac.authorization.k8s.io/v1beta1","kind":"ClusterRoleBinding","metadata":{"annotations":{},"name":"magedu-read-all-pods","namespace":""...
Role:
  Kind:  ClusterRole
  Name:  cluster-read
Subjects:
  Kind  Name    Namespace
  ----  ----    ---------
  User  magedu  

[ik8s@k8s-master ~]$ kubectl get pods  #角色绑定后在ik8s终端上进行获取pods信息，已经不会出现forbidden了
NAME                     READY     STATUS    RESTARTS   AGE
filebeat-ds-hxgdx        1/1       Running   1          36d
filebeat-ds-s466l        1/1       Running   2          36d
myapp-0                  1/1       Running   0          2d
myapp-1                  1/1       Running   0          2d
myapp-2                  1/1       Running   0          2d
myapp-3                  1/1       Running   0          2d
pod-sa-demo              1/1       Running   0          1d
pod-vol-demo             2/2       Running   0          4d
redis-5b5d6fbbbd-q8ppz   1/1       Running   1          4d
[ik8s@k8s-master ~]$ kubectl get pods -n ingress-nginx #更换名称空间进行查看也是可行的
NAME                                        READY     STATUS    RESTARTS   AGE
default-http-backend-7db7c45b69-nqxw9       1/1       Running   1          4d
nginx-ingress-controller-6bd7c597cb-9fzbw   1/1       Running   0          4d

[ik8s@k8s-master ~]$ kubectl delete pods pod-sa-demo  #但是进行删除pod就无法进行，因为在授权时是没有delete权限的
Error from server (Forbidden): pods "pod-sa-demo" is forbidden: User "magedu" cannot delete pods in the namespace "default"
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

**从上面的实验，我们可以知道对用户magedu进行集群角色绑定，用户magedu将会获取对集群内所有资源的对应权限。**

###  **3、User --> Rolebinding --> Clusterrole**

将maedu通过rolebinding到集群角色magedu-read-pods当中，此时，magedu仅作用于当前名称空间的所有pods资源的权限

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[root@k8s-master mainfests]# kubectl delete clusterrolebinding magedu-read-all-pods
clusterrolebinding.rbac.authorization.k8s.io "magedu-read-all-pods" deleted

[root@k8s-master mainfests]# kubectl create rolebinding magedu-read-pods --clusterrole=cluster-read --user=magedu --dry-run -o yaml > rolebinding-clusterrole-demo.yaml
[root@k8s-master mainfests]# vim rolebinding-clusterrole-demo.yaml 
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: magedu-read-pods
  namespace: default
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-read
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: User
  name: magedu

[root@k8s-master mainfests]# kubectl apply -f rolebinding-clusterrole-demo.yaml 
rolebinding.rbac.authorization.k8s.io/magedu-read-pods created

[ik8s@k8s-master ~]$ kubectl get pods
NAME                     READY     STATUS    RESTARTS   AGE
filebeat-ds-hxgdx        1/1       Running   1          36d
filebeat-ds-s466l        1/1       Running   2          36d
myapp-0                  1/1       Running   0          2d
myapp-1                  1/1       Running   0          2d
myapp-2                  1/1       Running   0          2d
myapp-3                  1/1       Running   0          2d
pod-sa-demo              1/1       Running   0          1d
pod-vol-demo             2/2       Running   0          4d
redis-5b5d6fbbbd-q8ppz   1/1       Running   1          4d
[ik8s@k8s-master ~]$ kubectl get pods -n ingress-nginx
No resources found.
Error from server (Forbidden): pods is forbidden: User "magedu" cannot list pods in the namespace "ingress-nginx"
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

##  四、RBAC的三种授权访问

RBAC不仅仅可以对user进行访问权限的控制，还可以通过group和serviceaccount进行访问权限控制。当我们想对一组用户进行权限分配时，即可将这一组用户归并到一个组内，从而通过对group进行访问权限的分配，达到访问权限控制的效果。

从前面serviceaccount我们可以了解到，Pod可以通过 spec.serviceAccountName来定义其是以某个serviceaccount的身份进行运行，当我们通过RBAC对serviceaccount进行访问授权时，即可以实现Pod对其他资源的访问权限进行控制。也就是说，当我们对serviceaccount进行rolebinding或clusterrolebinding，会使创建Pod拥有对应角色的权限和apiserver进行通信。如图：

![img](https://img2018.cnblogs.com/blog/1349539/201810/1349539-20181013171216120-114663466.png)

 

Don't forget the beginner's mind