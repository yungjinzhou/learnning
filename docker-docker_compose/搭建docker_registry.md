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





安装docker-registry-web



## 关于Registry

官方的Docker hub是一个用于管理公共镜像的好地方，我们可以在上面找到我们想要的镜像，也可以把我们自己的镜像推送上去。

但是有时候我们的使用场景需要我们拥有一个私有的镜像仓库用于管理我们自己的镜像。这个可以通过开源软件Registry来达成目的。

 Registry在github上有两份代码：老代码库和新代码库。老代码是采用python编写的，存在pull和push的性能问题，出到0.9.1版本之后就标志为deprecated，不再继续开发。

 从2.0版本开始就到在新代码库进行开发，新代码库是采用go语言编写，修改了镜像id的生成算法、registry上镜像的保存结构，大大优化了pull和push镜像的效率。

 官方在Docker hub上提供了registry的镜像，我们可以直接使用该registry镜像来构建一个容器，搭建我们自己的私有仓库服务。

 

------

## 二、搭建Registry

#### 首先搜索并拉取镜像

```
docker search registry　　　　# 建议先搜索一下，可以看一下相关的镜像，说不定哪天就有更好的镜像了
docker pull registry　　　　# 标签可以不加，因为当前最新就是v2
```

 

 

#### 　　运行一个registry容器

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
docker run -d \            # 后台运行
--name registry-srv \    # 指定容器名
--restart=always \        # 设置自动启动
-p 5000:5000 \            # 端口映射宿主机，通过宿主机地址访问
-v /opt/zwx-registry:/var/lib/registry \     # 把镜像存储目录挂载到本地，方便管理和持久化
-v /opt/zwx-registry/srv-config.yml:/etc/docker/registry/config.yml \    # 把配置文件挂载到本地，方便修改和保存
registry
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

 

#### 　　srv-config.yml内容如下

　　标红delete参数设置为true，是为了让仓库支持删除功能。默认没有这个参数，也就是不能删除仓库镜像。

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
version: 0.1
log:
  fields:
    service: registry
storage:
  delete:
    enabled: true
  cache:
    blobdescriptor: inmemory
  filesystem:
    rootdirectory: /var/lib/registry
http:
  addr: :5000
  headers:
    X-Content-Type-Options: [nosniff]
health:
  storagedriver:
    enabled: true
    interval: 10s
    threshold: 3
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

#### 　　注册https协议（否则push安全认证过不去）

　　需要通过本地仓库下载镜像，均需要配置　　

```
vim /etc/docker/daemon.json　　　　　　　　# 默认无此文件，需自行添加，有则追加以下内容。
{ "insecure-registries":["xx.xx.xx.xx:5000"] }　　# 指定IP地址或域名

systemctl daemon-reload    # 守护进程重启
systemctl restart docker    # 重启docker服务
```

#### 镜像上传与下载

```
docker push xx.xx.xx.xx:5000/nginx            # 一定要注明仓库地址，否则会报错
docker pull xx.xx.xx.xx:5000/nginx
```

 

#### 　　查看仓库镜像信息

```
curl -XGET http://xx.xx.xx.xx:5000/v2/_catalog　　　　# 查看仓库镜像列表（也可以通过windows浏览器打开查看）
curl -XGET http://xx.xx.xx.xx:5000/v2/image_name/tags/list　　# 查看指定应用镜像tag
```

 

 

 

------

## 三、搭建Registry web

#### 首先搜索并拉取镜像

```
docker search docker-registry-web
docker pull hyper/docker-registry-web　　　　# 这个镜像用的人较多
```

 

####  

#### 　　运行一个registry web容器

```
docker run -d \            # 后台运行
--name registry-web \    # 指定容器名
--restart=always \        # 设置自动启动
-p 8000:8080 \            # 端口映射宿主机，通过宿主机地址访问
-v /opt/zwx-registry/web-config.yml:/conf/config.yml \    # 把配置文件挂载到本地，方便修改和保存
hyper/docker-registry-web
```

 

####  

#### 　　web-config.yml文件内容如下

标红readonly参数设置为false，是为了web页面可以显示删除按钮。默认是true，只读状态，没有删除按钮，只能查看。

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
registry:
  # Docker registry url
  url: http://10.88.77.32:5000/v2
  # Docker registry fqdn
  name: localhost:5000
  # To allow image delete, should be false
  readonly: false
  auth:
    # Disable authentication
    enabled: false
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

#### 部署完成后，浏览器打开仓库UI地址即可查看到所有应用镜像

![img](https://img2018.cnblogs.com/i-beta/1059616/201912/1059616-20191216172801430-1490140624.png)

选择任意应用镜像库，即可查看到该镜像的所有tag信息，每个tag后面都有个删除按钮（默认没有，配置参考config.yml）

 ![img](https://img2018.cnblogs.com/i-beta/1059616/201912/1059616-20191216172830271-680915343.png)

 

 

------

## 四、快捷部署

　　集群模式可以通过docker stack快速部署registry和registry web。

　　新建配置文件srv-config.yml、web-config.yml放到指定路径，再新建docker-compose.yml文件，执行命令即可。

```
docker stack deploy -c docker-compose.yml RGT
```

 

```
version: '3.7'　　　　　　# docker stack 需要是3.0以上版本
services:
  registry-srv:　　　　　　# 服务名
    image: registry
    
    ports:　　　　　　　　　# 映射端口
      - 5000:5000
      
    volumes:　　　　　　　　# 挂载镜像路径和配置文件，注意修改路径与实际一致
      - /opt/zwx-registry:/var/lib/registry
      - /opt/zwx-registry/srv-config.yml:/etc/docker/registry/config.yml
      
    deploy:　　　　　　　　# 设置单任务，并约束主节点运行
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.role == manager
      
  registry-web:　　　　　　# 服务名　　
    image: hyper/docker-registry-web
    
    ports:　　　　　　　　# 映射端口
      - 8000:8080
    
    volumes:　　　　　　# 挂载配置文件，注意修改路径与实际一致
      - /opt/zwx-registry/web-config.yml:/conf/config.yml
      
    environment:
      - REGISTRY_URL=http://registry-srv:5000/v2
      - REGISTRY_NAME=localhost:5000
    
    deploy:　　　　　　　　# 设置单任务，并约束主节点运行
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.role == manager
```







参考链接：https://www.cnblogs.com/leozhanggg/p/12050322.html





