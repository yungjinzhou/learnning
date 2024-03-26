# 在x86 centos7虚拟机上安装centos7-arm64虚拟机



基于x86架构的CentOS7虚拟机通过qemu安装ARM架构CentOS7虚拟机



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