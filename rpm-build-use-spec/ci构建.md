目前需要添加ci的仓库有：
MCS-nova
MCS-neutron
MCS-cinder
MCS-virt
MCS-ceilometer
MCS-mimic
MCS-zun
MCS-monitor-cache
MCS-octavia


gitlab-runner要运行的宿主机，后续会在生产云上添加，
目前先在虚拟机或者物理机上测试


#### 将自动化打包镜像，推送到harbor

1、登录harbor
```shell
cat > /etc/docker/daemon.json <<EOF
{"insecure-registries": ["192.168.66.29"]}
EOF
systemctl restart docker
docker login 192.168.66.29 -u admin -p comleader@123
```
```
# 登录成功会有提示
[root@intel-executor var]# docker login 192.168.66.29 -u admin -p comleader@123
Login Succeeded
```
2、推送镜像
```shell
docker tag neutron-rpm-build 192.168.66.29/package_build/neutron-rpm-build:latest
docker push 192.168.66.29/package_build/neutron-rpm-build:latest
```


#### 部署gitlab-runner
1、安装gitlab-runner
```
# centos
wget https://s3.amazonaws.com/gitlab-runner-downloads/main/rpm/gitlab-runner_amd64.rpm
rpm -i gitlab-runner*.rpm

# ubuntu
wget https://s3.amazonaws.com/gitlab-runner-downloads/main/deb/gitlab-runner_aarch64.deb
dpkg -i gitlab-runner*.deb
```
其他版本的gitlabrunner从以下链接中查找：
https://docs.gitlab.com/runner/install/bleeding-edge.html


2、注册gitlab-runner
打开gitlab页面，进入对应的仓库，比如MCS-neutron，点击左侧“设置” -》 ”CI/CD“，
展开Runner，在“专用Runner”侧，有Runner需要填写的信息

进入Runner所在服务器，注册runner
```
# gitlab-runner register
...
# gitlab地址
Enter the GitLab instance URL (for example, https://gitlab.com/):
http://192.168.66.33/
# token从页面上查看
Enter the registration token:
xxxxx
# 描述信息，描述信息尽量写清楚，以便区分开自己和别人的runner
Enter a description for the runner:
[24dc60abee0b]: neutron-rpm-build
# 标签是用于过滤runner，可以直接填default
Enter tags for the runner (comma-separated):
default
Registering runner... succeeded                     runner=iqxKz5XT
# 执行模式，目前默认采用shell，可以根据自己需求使用其他方式
Enter an executor: docker-ssh+machine, kubernetes, custom, shell, ssh, virtualbox, docker, docker-ssh, parallels, docker+machine:
shell


# 注册完成后，修改配置文件/etc/gitlab-runner/config.toml
# 添加内容：environment = ["PackageType=rpm"]， 也就是添加环境变量PackageType，脚本在执行的时候可以读取到，表示该runner构建的包的类型：
[root@executor-intel gitlab-runner]# cat /etc/gitlab-runner/config.toml
concurrent = 1
check_interval = 0
shutdown_timeout = 0

[session_server]
  session_timeout = 1800

[[runners]]
  name = "test"
  url = "http://192.168.66.33/"
  id = 1
  token = "f002bbb39c9ffaa92e4d049a09dc70"
  token_obtained_at = 2022-12-08T01:42:37Z
  token_expires_at = 0001-01-01T00:00:00Z
  executor = "shell"
  environment = ["PackageType=rpm"]
  [runners.cache]
    MaxUploadedArchiveSize = 0


# 重启gitlab-runner
root@24dc60abee0b:/# gitlab-runner restart

# 查看runner列表
root@24dc60abee0b:/# gitlab-runner list 
```

刷新gitlab的Runner页面，页面出现注册的runner，编辑runner信息，解除锁定


---

#####gitlab-runner用户授权
在gitlab-runner所在机器，把该用户加入到docker群组，使该用户有docker执行权限
```shell
sudo groupadd docker
sudo usermod -aG docker gitlab-runner
sudo chmod g+rwx "$HOME/.docker" -R
# gitlab-runner用户添加到sudoers
echo 'gitlab-runner   ALL=(ALL)   NOPASSWD:  ALL' >> /etc/sudoers
```
---



3. 编写 .gitlab-ci.yml 和 build.sh

先看一下最终neutron的代码结构：
  .gitlab-ci.yml在整个MCS-neutron仓库的根目录
  build目录里存放构建包相关的文件，包括dockerfile， rpm相关的有SOURCES、SPECS， deb相关的有debian

编写.gitlab-ci.yml 和 build.sh 的时候，要注意目录结构

> 特别强调， build目录里不能有patch文件，如果有patch，将patch合入代码
```
MCS-neutron
├── .git
├── .gitignore
├── .gitlab-ci.yml  # gitlab-runner运行时的模板
├── neutron
├── neutron-fwaas
├── neutron-lib
├── neutron-vpnaas
├── python_rpc_transfer
# 以上是代码，下面的build是构建相关
└── build
    ├── build.sh
    └── neutron
        └── centos   # centos目录
            ├── Dockerfile # 此处是Dockerfile，如果docker镜像实在不能自动构建，在此处写下手动构建文档
            ├── SOURCES
            │   ├── conf.README
            │   ├── neutron-destroy-patch-ports.service
            | ...
            └── SPECS
                └── openstack-neutron.spec
            ubuntu   # ubuntu目录
            ├── Dockerfile  # 此处是Dockerfile，如果docker镜像实在不能自动构建，在此处写下手动构建文档
            └── debian
                ...
```


##### .gitlab-ci.yml参考如下， 
build阶段调用脚本build/build.sh，制作包，并上传至ftp服务器
```yml
stages:
  - build
  - clean

variables:
  CI_WORK_DIR: /tmp/mcs_neutron_ci/workdir/

build_job:
  stage: build
  tags:
    - default
  only:
    - master
  script:
    - mkdir -p $CI_WORK_DIR
    - cp -r ./* $CI_WORK_DIR/
    - bash $CI_WORK_DIR/build/build.sh

clean_job:
  stage: clean
  tags:
    - default
  only:
    - master
  script:
    - rm -rf $CI_WORK_DIR
```

**stages** : 定义各个阶段job的执行顺序
**stage**： 表示当前job所在的阶段
**tags**：查找对应标签的gitlab-runner，触发流程
**only**：触发ci的代码分支
**script** : script执行要求执行的命令，可以在gitlab-runner所在的机器编写脚本执行
**variables**： 定义变量

---

##### build.sh自动化构建脚本
neutron示例如下：
目前build只是构建rpm包、deb包，如果有余力可以把dockerfile生成镜像并推送到haobor的过程也写入脚本中。
>    注意： MCS-neutron仓库下包含5个项目：neutron、neutron-lib、neutron-fwaas、neutron-vpnaas、python_rpc_transfer,
> 由于每次提交代码都会触发构建流程，但是不一定所有的代码都需要重新打包，所以在脚本里做了一些限制操作。
> 在gitlab-runner中，环境变量CI_COMMIT_TITLE会记录git commit提交的标题，
> 所以这个脚本通过判断commit的标题里是否含有指定的标签来决定构建哪些包。其他组件可以依据情况进行调整。
```shell
#!/bin/bash
BUILD_PATH=/tmp/MCS-neutron
mkdir -p $BUILD_PATH

function help(){
    echo 'Build neutron: git commit -m "build_neutron: xxxx"'
    echo 'Build neutron-lib: git commit -m "build_neutron_lib: xxxx"'
    echo 'Build neutron-fwaas: git commit -m "build_neutron_fwaas: xxxx"'
    echo 'Build neutron-vpnaas: git commit -m "build_neutron_vpnaas: xxxx"'
    echo 'Build python_rpc_transfer: git commit -m "build_python_rpc_transfer: xxxx"'
}

function build_neutron_rpm(){
    mkdir -p $BUILD_PATH/rpmbuild
    sudo rm -rf $BUILD_PATH/rpmbuild/*
    cp -r neutron/centos/SOURCES $BUILD_PATH/rpmbuild/
    cp -r neutron/centos/SPECS $BUILD_PATH/rpmbuild/
    mv ../neutron  neutron-14.4.2
    tar -zcvf $BUILD_PATH/rpmbuild/SOURCES/neutron-14.4.2.tar.gz neutron-14.4.2/*
    docker ps -a -qf name=neutron-build  | xargs docker rm -f
    docker run \
        -v $BUILD_PATH/rpmbuild:/root/rpmbuild:rw  \
        --name neutron-build \
        192.168.66.29/package_build/neutron-rpm-build:latest

# 上传rpm包值ftp服务器
# 由于容器权限问题，此处的rpm包的owner为root。不想处理权限问题，可以在.gitlab-ci.yml用sudo执行build.sh脚本
# 或者修改dockerfile， 把推送到ftp这个过程放到容器里执行
sudo chown -R gitlab-runner $BUILD_PATH/rpmbuild/RPMS/noarch/*.rpm
ftp -n<<!
open 192.168.67.183 4449
user chenkai comleader@123
binary
lcd $BUILD_PATH/rpmbuild/RPMS/noarch/
cd /packages/rpms/
put openstack-neutron-14.4.2-1.el7.noarch.rpm
put openstack-neutron-common-14.4.2-1.el7.noarch.rpm
put openstack-neutron-linuxbridge-14.4.2-1.el7.noarch.rpm
put openstack-neutron-macvtap-agent-14.4.2-1.el7.noarch.rpm
put openstack-neutron-metering-agent-14.4.2-1.el7.noarch.rpm
put openstack-neutron-ml2-14.4.2-1.el7.noarch.rpm
put openstack-neutron-openvswitch-14.4.2-1.el7.noarch.rpm
put openstack-neutron-rpc-server-14.4.2-1.el7.noarch.rpm
put openstack-neutron-sriov-nic-agent-14.4.2-1.el7.noarch.rpm
put python2-neutron-14.4.2-1.el7.noarch.rpm
put python2-neutron-tests-14.4.2-1.el7.noarch.rpm
prompt
close
bye
!
}

function build_neutron_deb(){
    pass
}

function build_neutron_lib_rpm(){
    pass
}

function build_neutron_lib_deb(){
    pass
}

function build(){
    # 通过环境变量CI_COMMIT_TITLE确定需要构建的项目， PackageType指定包的类型
    if echo $CI_COMMIT_TITLE | grep "build_neutron:"; then
        build_neutron_$PackageType
    elif echo $CI_COMMIT_TITLE | grep "build_neutron_lib:"; then
        build_neutron_lib_$PackageType
    else
        help
    fi
}

pushd $(dirname $(realpath $0))
    build
popd

sudo rm -rf $BUILD_PATH
```

最后，提交代码，指定构建neutron
```shell
git add .
git commit -m "build_neutron: test ci"
git push origin HEAD:refs/for/master
```
触发ci后，在gitlab的仓库MCS-neutron页面，左侧 CI/CD-》流水线 ， 可以看到构建的过程，
最后在ftp服务器192.168.67.183上可以看到推送的安装包