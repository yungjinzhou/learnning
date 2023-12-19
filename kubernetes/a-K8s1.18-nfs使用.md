

### 1. 容器云文件共享nfs

#### 1.1 搭建nfs

搭建环境Centos7.9-x86_64，可联网

```javascript
yum install rpcbind nfs-utils
mkdir /home/test
chmod -R 777 /home/test/
cd /home/test/


vim /etc/exports
写入 /home/test 10.21.16.43/24(rw)   

# 以下未测试
写入 /home/test *(rw,sync,insecure,no_subtree_check,no_root_squash)




```

是配置生效

```
exportfs -r
```



开启服务

```javascript
systemctl start rpcbind nfs
```

设置开机自启 

```
mkdir /nfs
echo "10.21.16.43:/home/test /nfs nfs4 defaults 0 0" >> /etc/fstab 
mount -av
```

查看共享信息

```
showmount -e 10.21.16.43  (此处ip地址为搭建服务器主机地址)
```



#### 1.2 pod使用nfs

```
$ vim nfs-busybox.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nfs-busybox
spec:
  replicas: 1
  selector:
    matchLabels:
      name: nfs-busybox
  template:
    metadata:
      labels:
        name: nfs-busybox
    spec:
      containers:
      - image: busybox
        command:
          - sh
          - -c
          - 'while true; do date > /mnt/index.html; hostname >> /mnt/index.html; sleep 10m; done'
        imagePullPolicy: IfNotPresent
        name: busybox
        volumeMounts:
          - name: nfs
            mountPath: "/mnt"
      volumes:
      - name: nfs
        nfs:
          path: /home/test
          server: 10.21.16.43 
```









简单说下，该 Deployment 使用 busybox 作为镜像，挂载 nfs 的 /data/nfs0 卷到容器 /mnt 目录，并输出系统当前时间及 hostname 到 /mnt/index.html 文件中。那么来创建一下该 Deployment。

```
# 创建
kubectl apply -f nfs-busybox.yaml 
# 查看
kubectl get pods -o wide
# 进入容器查看
kubectl exec -it nfs-busybox-5c98957964-g7mps /bin/sh
cat /mnt/index.html 
```



#### 1.3 pod 使用pv  pvc



我们知道 k8s 提供了两种 API 资源方式：PersistentVolume 和 PersistentVolumeClaim 来解决 Pod 删除掉，挂载 volume 中的数据丢失的问题，PV 拥有独立与 Pod 的生命周期，即使 Pod 删除了，但 PV 还在，PV 上的数据依旧存在，而 PVC 则定义用户对存储资源 PV 的请求消耗。接下来，来演示下如何使用 PV & PVC 方式使用 NFS。

创建nfs-pv.yaml

```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: nfs-pv
spec:
  capacity:
    storage: 1Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Recycle
  storageClassName: slow
  nfs:
    path: /home/test
    server: 10.21.16.43
```

创建nfs-pvc.yaml

```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nfs-pvc
spec:
  accessModes:

   - ReadWriteMany
     storageClassName: "slow"
       resources:
         requests:
     storage: 1Gi 
```



说明一下，这里 PV 定义了 accessModes 为 ReadWriteMany 即多次读写模式，NFS 是支持三种模式的 ReadWriteOnce、ReadOnlyMany、ReadWriteMany，

创建

```
kubectl create -f nfs-pv.yaml 

kubectl create -f nfs-pvc.yaml 

 kubectl get pv
 
 kubectl get pvc

```

成功创建，并处于 Bound 状态。接下来，创建一个挂载该 PVC 的 Pod，yaml 文件如下：

vim nfs-busybox-pvc.yaml

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nfs-busybox-pvc
spec:
  replicas: 1
  selector:
    matchLabels:
      name: nfs-busybox-pvc
  template:
    metadata:
      labels:
        name: nfs-busybox-pvc
    spec:
      containers:
      - image: busybox
        command:
          - sh
          - -c
          - 'while true; do date > /mnt/index.html; hostname >> /mnt/index.html; sleep 10m; done'
        imagePullPolicy: IfNotPresent
        name: busybox
        volumeMounts:
          - name: nfs
            mountPath: "/mnt"
      volumes:
      - name: nfs
        persistentVolumeClaim:
          claimName: nfs-pvc
```




```
kubectl create -f nfs-busybox-pvc.yaml

kubectl get pods -o wide
```













参考链接：

搭建

https://cloud.tencent.com/developer/article/1711894

在k8s中使用（在k8s1.18中验证，环境centos7.9-x86_64）

https://blog.csdn.net/aixiaoyang168/article/details/83988253









