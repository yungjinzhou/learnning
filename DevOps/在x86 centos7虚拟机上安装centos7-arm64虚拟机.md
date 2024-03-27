# 在x86 centos7虚拟机上安装centos7-arm64虚拟机



### 1. 基于x86架构的CentOS7虚拟机通过qemu安装ARM架构CentOS7虚拟机

此种方案未能实现创建的虚拟机联网及与宿主机通信



（1）首先需要有一台CentOS虚拟机，如没有可参考 [VMWare安装CentOS7操作系统的虚拟机](http://devops-dev.com/article/427) 安装一台CentOS虚拟机

（2）安装基础命令

```
yum install -y net-toolsyum install -y wget
```

（3）下载ARM架构的centos7操作系统镜像

```
mkdir -p /opt/oscd /opt/oswget http://mirror.nju.edu.cn/centos-altarch/7.9.2009/isos/aarch64/CentOS-7-aarch64-Minimal-2009.iso --no-check-certificatechmod 777 /opt/os/CentOS-7-aarch64-Minimal-2009.iso
```

（4）下载ARM架构的EFI
路径为 /usr/share/AAVMF/AAVMF_CODE.fd

```
yum install -y http://mirror.centos.org/altarch/7/os/aarch64/Packages/AAVMF-20180508-6.gitee3198e672e2.el7.noarch.rpm
```

（5）安装基础依赖

```
yum groupinstall 'Development Tools' -yyum groupinstall "Virtualization Host" -yyum install -y kvm qemu virt-viewer virt-manager libvirt libvirt-python python-virtinstyum install libguestfs-tools -yyum install virt-install.noarch -ysystemctl enable libvirtdsystemctl start libvirtdusermod -aG libvirt $(whoami)yum install virt-install virt-viewer virt-manager -y
```

（6）修改qemu配置文件

```
vi /etc/libvirt/qemu.conf
```

将如下两行放开注释
![img](https://redrose2100.oss-cn-hangzhou.aliyuncs.com/img/f7edb8c0-642a-11ed-aed9-0242ac110002.png)

（7）重启虚拟机

```
reboot
```

（8）下载qemu

```
cd /optwget https://download.qemu.org/qemu-4.2.0.tar.xz
```

（9）安装基础依赖

```
yum install python2 zlib-devel glib2-devel pixman-devel -y
```

（10）将qemu解压

```
cd /opt/tar xf qemu-4.2.0.tar.xz
```

（11）安装qemu

```
cd qemu-4.2.0/./configure --target-list=aarch64-softmmu --prefix=/usrmake -j8make install
```

（12）创建磁盘

```
rm -rf /var/lib/libvirt/images/test.imgqemu-img create /var/lib/libvirt/images/test.img 30G
```

（13）启动虚拟机

```
qemu-system-aarch64 -m 1024 -cpu cortex-a57 -smp 2 -M virt -bios /usr/share/AAVMF/AAVMF_CODE.fd -nographic -drive if=none,file=/opt/os/CentOS-7-aarch64-Minimal-2009.iso,id=cdrom,media=cdrom -device virtio-scsi-device -device scsi-cd,drive=cdrom -drive if=none,file=/var/lib/libvirt/images/test.img,id=hd0 -device virtio-blk-device,drive=hd0 
```

（14）如下设置主机名
![img](https://redrose2100.oss-cn-hangzhou.aliyuncs.com/img/92451a26-6449-11ed-aed9-0242ac110002.png)

（15）如下设置网络为dhcp模式
![img](https://redrose2100.oss-cn-hangzhou.aliyuncs.com/img/c814e58c-6449-11ed-aed9-0242ac110002.png)

（16）设置磁盘挂载，这里简单处理了
![img](https://redrose2100.oss-cn-hangzhou.aliyuncs.com/img/1da1643a-644a-11ed-aed9-0242ac110002.png)

（17）设置root用户的密码
![img](https://redrose2100.oss-cn-hangzhou.aliyuncs.com/img/703abcb4-644a-11ed-aed9-0242ac110002.png)

（18）在设置时区，待如下位置没有叹号了，则继续安装
![img](https://redrose2100.oss-cn-hangzhou.aliyuncs.com/img/b97bf37a-644a-11ed-aed9-0242ac110002.png)

（19）安装完成后，按回车开始重启
![img](https://redrose2100.oss-cn-hangzhou.aliyuncs.com/img/045182c2-6480-11ed-aed9-0242ac110002.png)

（20）然后即可通过设置的root的密码登录了
![img](https://redrose2100.oss-cn-hangzhou.aliyuncs.com/img/5cd0cae8-6480-11ed-aed9-0242ac110002.png)



### 2.通过libvrit安装ARM架构CentOS7虚拟机

#### 2.1 基础环境 

准备好一台可以联网的centos7-x86（物理机或虚拟机）

关闭防火墙

#### 2.2 安装libvirt

```
yum install qemu-kvm libvirt virt-install bridge-utils
```



#查看是否加载kvm模块

```
[root@kvm ~]# lsmod|grep kvm

kvm_intel             138567  0

kvm                   441119  1 kvm_intel

#如果没有这两条，可以用"modprobe kvm"加载；

#相关命令"insmod;rmmod;modinfo"
```

启动libvirtd

```
systemctl start libvirtd
systemctl enable libvirtd
```



#### 2.3   通过libvirt(virt-manager)安装虚拟机centos7arm64



##### 2.3.1 virt-manager操作

![img](E:\code\learnning\DevOps\创建虚拟机.png)





![img](E:\code\learnning\DevOps\架构选择.png)







![img](E:\code\learnning\DevOps\选择iso镜像.png)





![img](E:\code\learnning\DevOps\配置cpu和内存.png)





![img](E:\code\learnning\DevOps\创建存储磁盘文件.png)







![img](E:\code\learnning\DevOps\网络设置为nat类型.png)



##### 2.3.2 安装操作系统

系统安装步骤如1所示

##### 2.3.3 配置网络

安装完成后登录

执行`dhclient`配置网络

即可与宿主机通信，也可联网



可以将网络配置为静态

```
systemctl stop NetworkManager
systemctl disable NetworkManager
修改/etc/sysconfig/network-scripts/ifcfg-eth0

systemctl restart network.service

# 3、关闭防火墙
systemctl stop firewalld.service
systemctl disable firewalld.service

# 4、关闭SeLinux        
sed -i 's#SELINUX=enforcing#SELINUX=disabled#g' /etc/selinux/config
grep -n 'SELINUX='  /etc/selinux/config 

# 5、安装常用的软件包
yum install -y vim net-tools wget lrzsz tree screen lsof tcpdump nmap mlocate

# 6、命令提示符颜色
echo "PS1='[\[\e[31m\]\u\[\e[m\]@\[\e[36m\]\H\[\e[33m\] \W\[\e[m\]]\[\e[35m\]\\$ \[\e[m\]'" >>/etc/bashrc
source /etc/bashrc

```





##### 2.3.4 配置yum源

centos 7-aarch64如何替换yum源

一、进入yum.repo.d
[root@node-01 ~]# cd /etc/yum.repos.d/

[root@node-01 yum.repos.d]# ls
CentOS-Base.repo  CentOS-Sources.repo
二、备份原yum源
[root@node-01 yum.repos.d]# mkdir yum-back

[root@node-01 yum.repos.d]# mv CentOS-* yum-back/

[root@node-01 yum.repos.d]# ls
yum-back
三、替换yum源为阿里源
[root@node-01 yum.repos.d]# cat CentOS-Base.repo 

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
name=CentOS-$releasever - Base
baseurl=https://mirrors.aliyun.com/centos-altarch/$releasever/os/$basearch/
gpgcheck=1
gpgkey=https://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7

#released updates 
[updates]
name=CentOS-$releasever - Updates
baseurl=https://mirrors.aliyun.com/centos-altarch/$releasever/updates/$basearch/
gpgcheck=0
gpgkey=https://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7

#additional packages that may be useful
[extras]
name=CentOS-$releasever - Extras
baseurl=https://mirrors.aliyun.com/centos-altarch/$releasever/extras/$basearch/
gpgcheck=0
gpgkey=https://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
enabled=1

#additional packages that extend functionality of existing packages
[centosplus]
name=CentOS-$releasever - Plus
baseurl=https://mirrors.aliyun.com/centos-altarch/$releasever/centosplus/$basearch/
gpgcheck=0
enabled=0
gpgkey=https://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
```



epel.repo

```
[epel]
name=Extra Packages for Enterprise Linux 7 - $basearch
#baseurl=http://download.fedoraproject.org/pub/epel/7/$basearch
baseurl=https://mirrors.tuna.tsinghua.edu.cn/epel/7/$basearch
#metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-7&arch=$basearch
failovermethod=priority
enabled=1
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-7

[epel-debuginfo]
name=Extra Packages for Enterprise Linux 7 - $basearch - Debug
#baseurl=http://download.fedoraproject.org/pub/epel/7/$basearch/debug
baseurl=https://mirrors.tuna.tsinghua.edu.cn/epel/7/$basearch/debug
#metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-debug-7&arch=$basearch
failovermethod=priority
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-7
gpgcheck=0

[epel-source]
name=Extra Packages for Enterprise Linux 7 - $basearch - Source
#baseurl=http://download.fedoraproject.org/pub/epel/7/SRPMS
baseurl=https://mirrors.tuna.tsinghua.edu.cn/epel/7/SRPMS
#metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-source-7&arch=$basearch
failovermethod=priority
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-7
gpgcheck=0
```



五、运行yum生成缓存
[root@node-01 ~]#  yum makecache

六、验证
[root@node-01 ~]# yum -y install gcc-c++ vim docker  docker-compose





参考https://blog.csdn.net/smart9527_zc/article/details/84976097







