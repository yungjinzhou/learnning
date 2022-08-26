



## 一、docker



#### 1.1 容器打包

```
 docker save -o cirros.tar 192.168.66.29:80/feinitaikaifa/cirros:latest
```

#### 1.2  容器提交

```
docker commit -m="test " -a="zun02" dc5363dc932c 192.168.66.29:80/feinitaikaifa/centos7:v2
```

- **-m:** 提交的描述信息
- **-a:** 指定镜像作者
- **e218edb10161：**容器 ID
- **192.168.66.29:80/feinitaikaifa/centos7:v2：** 指定要创建的目标镜像名（其中192.168.66.29:80为harbor地址，feinitaikaifa为harbor项目名称，centos7:v1为镜像名称:tag）



#### 1.3 容器上传至glance

glance使用需要是没有tag的tar包，可以从dockerhub上下载后上传，或者清除tag信息后再上传



打包后的容器xxx.tar文件

登录到控制节点



source ~./admin-xxx



```
openstack image create --disk-format raw --container-format docker  --file centos7.tar docker-centos7

```



#### 1.4 容器镜像保存本地

```
docker save image_id > xxxx.tar
```



#### 1.5 本地容器镜像上传到私有仓库(harbor)

```
docker save image_id > xxxx.tar
```



#### 1.6 从dockerhub拉取镜像到上传到harbor步骤

```
# 从google或者dockerhub拉取镜像
docker pull xxxx
docker pull arm64v8/centos:7 # 拉取arm64的镜像
# 保存到本地
docker save image_id > kubernetes-kubelet.tar
# 上传到可以连接到harbor服务器的主机上
scp  kubernetes-kubelet.tar root@192.168.230.161:/home/
# 导入到docker image
docker load -i kubernetes-kubelet.tar
# 给镜像打tag
docker tag docker.io/openstackmagnum/kubernetes-kubelet:v1.11.6 192.168.66.29:80/openstack_magnum/kubernetes-kubelet:v1.11.6
# 推送到镜像服务器
docker push 192.168.66.29:80/openstack_magnum/kubernetes-kubelet:v1.11.6

```







## 二、docker-compose











