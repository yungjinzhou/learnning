# cloudpods部署





### 1. 部署测试环境：

centos7 x86_64



### 2.基本配置

配置ip地址，dns，ssh远程连接

```
# 配置ip
vim /etc/sysconfig/network-script/ifcfg-etho

# 配置dns
vim /etc/resolv.conf

# 配置ssh
vim /etc/ssh/sshd_config

```



配置基本软件环境

```
yum install -y wget vim 
```



### 3.设置aliyun源

```
# 备份
mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup

# 下载
wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
或
curl -o /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo

mv /etc/yum.repos.d/Centos-7.repo /etc/yum.repos.d/CentOS-Base.repo 
# 编辑，将文件中的所有http开头的地址更改为https
vim CentOS-Base.repo
将文件中的所有http开头的地址更改为https
:%s/http/https/g
```



### 4、更新镜像源

清除缓存：yum clean all
生成缓存：yum makecache

### 5.安装docker-ce

```
# 安装必要的一些系统工具
$ sudo yum install -y yum-utils device-mapper-persistent-data lvm2

# 添加软件源信息
$ sudo yum-config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo

# 更新并安装 docker-ce 以及 compose 插件
$ sudo yum makecache fast
$ sudo yum -y install docker-ce docker-ce-cli docker-compose-plugin

# 开启 docker 服务
$ sudo systemctl enable --now docker
```



### 6.下载cloudpods



```
# 下载 ocboot 工具到本地
$ git clone -b release/3.10 https://github.com/yunionio/ocboot && cd ./ocboot

# 进入 compose 目录
$ cd compose
$ ls -alh docker-compose.yml

# 运行服务
$ docker compose up -d

等服务启动完成后，就可以登陆 https://<本机ip> 访问前端服务，默认登陆用户密码为：admin 和 admin@123 。



```

### 7. 登陆 climc 命令行容器

如果要使用命令行工具对平台做操作，可以使用下面的方法进入容器：

```bash
$ docker exec -ti compose-climc-1 bash
Welcome to Cloud Shell :-) You may execute climc and other command tools in this shell.
Please exec 'climc' to get started

# source 认证信息
bash-5.1# source /etc/yunion/rcadmin
bash-5.1# climc user-list
```



登录加入openstack云后，发现不能识别别名配置，比如nova_proxy，有些请求会异常，

可以登录到容器compose-region-1中，配置hosts，就可以发现云主机等资源的信息了

```
docker exec -it compose-region-1 sh

echo "192.168.232.106 nova_proxy" >> /etc/hosts
echo "192.168.232.107 controller" >> /etc/hosts
```









参考链接：https://www.cloudpods.org/zh/docs/quickstart/docker-compose/