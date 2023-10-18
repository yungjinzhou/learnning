## 搭建docker registry

选择合适的机器安装docker registry，假设机器上已经安装了docker

比如在192.168.55.45上部署registry



1. 拉取镜像或者拷贝镜像

   ```
   docker pull registry
   # 如果提供了离线registry，执行
   docker load -i registry.tar
   ```

2. 运行仓库

   ```
   docker run -d -p 5000:5000 -v /home/docker_registry/:/tmp/registry --privileged=true registry
   ```

   默认情况下，仓库创建在容器的`/var/lib/registry`目录下，***也就是说每次我们上传到registry的私人服务器仓库的文件就存储到`/var/lib/registry`目录下***。考虑到权限管理问题，在实际应用中通常需要自定义容器卷映射，以便与宿主机[联调](https://so.csdn.net/so/search?q=联调&spm=1001.2101.3001.7020)。



3. 上传镜像

   ```
   # 假设镜像原名称是 hello:v1
   docker tag hello:v1 192.168.55.45:5000/hello:v1
   
   ```

   

4. 设置docker（**在所有需要用到该私有仓库的宿主机的daemon.json中修改**）

   在/etc/docker/daemon.json中加入insecure-registries

   ```
     "registry-mirrors": [
       "http://192.168.100.190:8082",
       "http://registry.kubeoperator.io:8082",
       "https://reg-mirror.qiniu.com",
       "https://hub-mirror.c.163.com"
     ],
     "insecure-registries": ["192.168.55.45:5000"]
   }
   
   
   ```

   重启docker `systemctl restart docker`

5. 推送镜像

```
docker push 192.168.55.45:5000/hello:v1
```



6. 在其他宿主机中，拉取镜像测试(注意配置daemon.json中私有仓库的地址，否则拉取失败)

```
docker pull 192.168.55.45:5000/hello:v1
```







