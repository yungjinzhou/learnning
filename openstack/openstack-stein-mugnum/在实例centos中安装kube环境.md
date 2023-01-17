

## 在openstack虚拟机安装kubeadm环境

openstack stein版本

基础镜像：CentOS-7-x86_64-GenericCloud-20210422.qcow2



安装步骤：

通过启动时执行脚本，修改用户名，密码，然后基于此实例创建快照

通过已经创建的快照来创建实例



### 配置ip地址

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



YPE=Ethernet
BOOTPROTO=static
NAME=eth0
DEVICE=eth0
ONBOOT=yes
IPADDR=192.168.24.36
NETMASK=255.255.255.0
GATEWAY=10.0.0.2
DNS1=8.8.8.8
DNS2=114.114.114.114
HWADDR=fa:16:3e:58:24:d3 # 每个机器不一样
```

配置hostname

```
hostnamectl set-hostname k8smaster
```



```
vim /etc/hostname


```







配置nameserver

```
vim /etc/resolv.conf

nameserver 8.8.8.8
nameserver 114.114.114.114
```



```

yum install -y vim net-tools wget lrzsz tree screen lsof tcpdump nmap mlocate gcc  traceroute

# 6、命令提示符颜色
echo "PS1='[\[\e[31m\]\u\[\e[m\]@\[\e[36m\]\H\[\e[33m\] \W\[\e[m\]]\[\e[35m\]\\$ \[\e[m\]'" >>/etc/bashrc
source /etc/bashrc

```



### 更换下载源

```
mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup

wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo

yum clean all
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

### 配置网络

```gauss
cat > /etc/sysctl.d/k8s.conf << EOF 
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1 
EOF


echo 1 > /proc/sys/net/ipv4/ip_forward
# 生效
sysctl --system 

```

### 时间同步

```stylus
timedatectl set-timezone Asia/Shanghai 

yum install ntpdate -y
ntpdate time.windows.com

```

### 解决https请求失败问题

```
解决GenericCloud centos7  curl 请求https失败

curl -v https://www.baidu.com
[root@k8sminion.novalocal home]# curl -v https://www* About to connect() to www.baidu.com port 443 (#0)*   Trying 103.235.46.39...
* Connected to www.baidu.com (103.235.46.39) port 443 (#0)
* Initializing NSS with certpath: sql:/etc/pki/nssdb
* Closing connection 0
curl: (77) Problem with the SSL CA cert (path? access rights?)

解决办法：创建空文件 
touch /etc/sysconfig/64bit_strstr_via_64bit_strstr_sse2_unaligned




Unable to resolve HTTPs links from newly spawned VM using CENTOS generic cloud images.

Issue found with images for CENTOS available on https://cloud.centos.org/centos/7/images/
Tried on following IMAGES:

CentOS-7-x86_64-GenericCloud.qcow2 2019-06-04 09:28 898M
CentOS-7-x86_64-GenericCloud-1804_02.qcow2 2018-05-19 01:34 892M
CentOS-7-x86_64-GenericCloud-1606.qcow2 2016-07-05 15:12 873M

Command to test:
curl -I -v https://google.com
* About to connect() to google.com port 443 (#0)
* Trying x.x.x.x....
* Connected to google.com (x.x.x.x) port 443 (#0)
* Initializing NSS with certpath: sql:/etc/pki/nssdb
* Closing connection 0
curl: (77) Problem with the SSL CA cert (path? access rights?)
Steps To Reproduce	Install cloud instance on openstack with centos generic images and run "curl -I -v https://google.com"
Additional Information	The issue gets resolved after creating an empty "/etc/sysconfig/64bit_strstr_via_64bit_strstr_sse2_unaligned" file
```









重启机器



安装docker

```awk
wget -O /etc/yum.repos.d/docker-ce.repo  https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo

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



```
echo 1 > /proc/sys/net/ipv4/ip_forward
```





### 部署Kubenetes Master

在Master节点执行

```apache
kubeadm init --apiserver-advertise-address=10.0.0.7 --image-repository registry.aliyuncs.com/google_containers --kubernetes-version v1.18.0 --service-cidr=10.96.0.0/12 --pod-network-cidr=10.244.0.0/16


kubeadm init --apiserver-advertise-address=192.168.24.16 --image-repository registry.aliyuncs.com/google_containers --kubernetes-version v1.18.0 --service-cidr=10.96.0.0/12 --pod-network-cidr=10.244.0.0/16

```

得到token

```
kubeadm join 10.0.0.7:6443 --token lj8kxk.xs9oy9jj7x0vp0s0 \
    --discovery-token-ca-cert-hash sha256:4b958a86348e11904a74e4507dd3b076e58364a2caaccd07d96e04c55afd1eb2 
```



### 提示使用kubectl工具

```awk
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

kubectl get nodes
```



### 部署CNI网络插件

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













```
# CentOS-Base.repo
#
# The mirror system uses the connecting IP address of the client and the
# update status of each mirror to pick mirrors that are updated to and
# geographically close to the client.  You should use this for CentOS updates
# unless you are manually picking other mirrors.
#
# If the mirrorlist= does not work for you, as a fall back you can try the 
# remarked out baseurl= line instead.
#
#
 
[base]
name=CentOS-7.9.2009 - Base - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/os/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/os/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/$releasever/os/$basearch/
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
 
#released updates 
[updates]
name=CentOS-$releasever - Updates - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/7.9.2009/updates/$basearch/
        http://mirrors.aliyuncs.com/centos/7.9.2009/updates/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/7.9.2009/updates/$basearch/
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
 
#additional packages that may be useful
[extras]
name=CentOS-$releasever - Extras - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/7.9.2009/extras/$basearch/
        http://mirrors.aliyuncs.com/centos/7.9.2009/extras/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/7.9.2009/extras/$basearch/
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
 
#additional packages that extend functionality of existing packages
[centosplus]
name=CentOS-$releasever - Plus - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/7.9.2009/centosplus/$basearch/
        http://mirrors.aliyuncs.com/centos/7.9.2009/centosplus/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/7.9.2009/centosplus/$basearch/
gpgcheck=1
enabled=0
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
 
#contrib - packages by Centos Users
[contrib]
name=CentOS-$releasever - Contrib - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/7.9.2009/contrib/$basearch/
        http://mirrors.aliyuncs.com/centos/7.9.2009/contrib/$basearch/
        http://mirrors.cloud.aliyuncs.com/centos/7.9.2009/contrib/$basearch/
gpgcheck=1
enabled=0
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7

```





```



	Unfortunately, an error has occurred:
		timed out waiting for the condition

	This error is likely caused by:
		- The kubelet is not running
		- The kubelet is unhealthy due to a misconfiguration of the node in some way (required cgroups disabled)

	If you are on a systemd-powered system, you can try to troubleshoot the error with the following commands:
		- 'systemctl status kubelet'
		- 'journalctl -xeu kubelet'

	Additionally, a control plane component may have crashed or exited when started by the container runtime.
	To troubleshoot, list all containers using your preferred container runtimes CLI.

	Here is one example how you may list all Kubernetes containers running in docker:
		- 'docker ps -a | grep kube | grep -v pause'
		Once you have found the failing container, you can inspect its logs with:
		- 'docker logs CONTAINERID'

error execution phase wait-control-plane: couldn't initialize a Kubernetes cluster
To see the stack trace of this error execute with --v=5 or higher



```







创建时执行脚本

```
	Unfortunately, an error has occurred:
		timed out waiting for the condition

	This error is likely caused by:
		- The kubelet is not running
		- The kubelet is unhealthy due to a misconfiguration of the node in some way (required cgroups disabled)

	If you are on a systemd-powered system, you can try to troubleshoot the error with the following commands:
		- 'systemctl status kubelet'
		- 'journalctl -xeu kubelet'

	Additionally, a control plane component may have crashed or exited when started by the container runtime.
	To troubleshoot, list all containers using your preferred container runtimes CLI.

	Here is one example how you may list all Kubernetes containers running in docker:
		- 'docker ps -a | grep kube | grep -v pause'
		Once you have found the failing container, you can inspect its logs with:
		- 'docker logs CONTAINERID'

error execution phase wait-control-plane: couldn't initialize a Kubernetes cluster
To see the stack trace of this error execute with --v=5 or higher

```







kubectl get nodes

node not  ready

```
NetworkPluginNotReady message:docker: network plugin is not ready: cni config uninitialized



kubectl describe node
```















## 用到的docker 镜像



```
registry.aliyuncs.com/google_containers/pause:3.2
k8s.gcr.io/pause-amd64:3.1
cnych/pause-amd64:3.1
k8s.gcr.io/k8s-dns-kube-dns-amd64:1.14.8
cnych/k8s-dns-kube-dns-amd64:1.14.8
k8s.gcr.io/k8s-dns-sidecar-amd64:1.14.8
cnych/k8s-dns-sidecar-amd64:1.14.8
k8s.gcr.io/k8s-dns-dnsmasq-nanny-amd64:1.14.8
cnych/k8s-dns-dnsmasq-nanny-amd64:1.14.8
quay.io/coreos/flannel:v0.10.0-amd64
cnych/flannel:v0.10.0-amd64
k8s.gcr.io/etcd-amd64:3.1.12
cnych/etcd-amd64:3.1.12
cnych/kube-scheduler-amd64:v1.10.0
k8s.gcr.io/kube-scheduler-amd64:v1.10.0
k8s.gcr.io/kube-controller-manager-amd64:v1.10.0
cnych/kube-controller-manager-amd64:v1.10.0
k8s.gcr.io/kube-apiserver-amd64:v1.10.0
cnych/kube-apiserver-amd64:v1.10.0
k8s.gcr.io/kube-proxy-amd64:v1.10.0
cnych/kube-proxy-amd64:v1.10.0
registry.aliyuncs.com/google_containers/etcd:3.4.3-0
registry.aliyuncs.com/google_containers/coredns:1.6.7
registry.aliyuncs.com/google_containers/pause:3.2
registry.aliyuncs.com/google_containers/kube-controller-manager:v1.18.0
registry.aliyuncs.com/google_containers/kube-apiserver:v1.18.0
registry.aliyuncs.com/google_containers/kube-scheduler:v1.18.0
registry.aliyuncs.com/google_containers/kube-proxy:v1.18.0
kubernetesui/dashboard:v2.0.2
quay.io/coreos/flannel:v0.14.0
rancher/mirrored-flannelcni-flannel-cni-plugin:v1.1.0
rancher/mirrored-flannelcni-flannel:v0.19.2
k8s.gcr.io/heapster-amd64:v1.4.2
cnych/heapster-amd64:v1.4.2
k8s.gcr.io/heapster-grafana-amd64:v4.4.3
cnych/heapster-grafana-amd64:v4.4.3
k8s.gcr.io/heapster-influxdb-amd64:v1.3.3
cnych/heapster-influxdb-amd64:v1.3.3
k8s.gcr.io/pause-amd64:3.1
cnych/pause-amd64:3.1
cnych/k8s-dns-kube-dns-amd64:1.14.8
k8s.gcr.io/kubernetes-dashboard-amd64:v1.8.3
cnych/kubernetes-dashboard-amd64:v1.8.3
k8s.gcr.io/kube-proxy-amd64:v1.10.0
cnych/kube-proxy-amd64:v1.10.0
registry.aliyuncs.com/google_containers/coredns:1.6.7
registry.aliyuncs.com/google_containers/pause:3.2
kubernetesui/metrics-scraper:v1.0.4
kubernetesui/dashboard:v2.0.2
quay.io/coreos/flannel:v0.14.0
rancher/mirrored-flannelcni-flannel-cni-plugin:v1.1.0
rancher/mirrored-flannelcni-flannel:v0.19.2
























```









