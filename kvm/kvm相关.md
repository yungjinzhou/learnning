## kvm相关



### virsh命令

查看虚拟机原有网卡信息

```cobol
[root@room1pc01 ~]# virsh domiflist kylin-wd
Interface  Type       Source     Model       MAC
```





给运行中的虚拟机添加网卡

```
virsh define /etc/libvirt/qemu/snale.xml
virsh attach-interface snale --type bridge --source br0  --target vnet1 --config

virsh attach-interface snale --type bridge --source br0  --target vnet1 --live  --config   在线更新

virsh attach-interface <domain-name> --type bridge --source <net-bridge> --model virtio --config --live

说明：type类型，一般是桥接bridge，还有network类型
domain-name: 虚拟机名称或ID
net-bridge：网桥名称
–config：写入配置文件
–live：在线添加（表面上添加了，实际上网络不通，需要重启网卡）
source，桥接到哪个网桥
target：不要重复，先brctl show查看一下；，或者自定义名字，可以在宿主机上查看

添加好后，在指定位置配置ifcfg-ens12，配置ip等


对于银河麒麟（4.0.2）或者ubuntu
配置 /etc/network/interfaces
或者/etc/netplan/interface

配置好后，重启网卡ifdown ens8 && ifup ens8
可能网卡两个ip（一个主一个从）

设置一个内核参数， 当主IP宕掉时可以将从IP提升为primary ip： 
echo "1" > /proc/sys/net/ipv4/conf/all/promote_secondaries
再次执行删除IP的命令：
ip addr del 192.168.213.132 dev ens8

主从ip信息参考链接
参考链接： https://developer.aliyun.com/article/897211
```







virsh命令详解

参考链接：https://www.cnblogs.com/hukey/p/11246126.html







修改xml文件

```
virsh edit /etc/libvirt/qemu/xxx.xml
```



kvm镜像路径

```
/var/lib/libvirt/image/
```







### virt-install命令



```
qemu-img create -f qcow2 /qcow/cloudexploer-ubuntu.qcow2  200G


virt-install --name=cloudexploer-ubuntu --vcpus=8 --ram=16384 --disk path=/qcow/cloudexploer-ubuntu.qcow2 --cdrom /ISO/ubuntu-20.04.4-live-server-amd64.iso --network bridge=br1,model=virtio --network bridge=nm-bridge,model=virtio --force --autostart --graphics vnc --osinfo detect=on,name=generic





qemu-img create -f qcow2 /qcow/cloudexploer-ubuntu.qcow2  200G

virt-install --name=cloudexploer-ubuntu --vcpus=8 --ram=16384 --disk path=/qcow/cloudexploer-ubuntu.qcow2 --cdrom /ISO/ubuntu-20.04.4-live-server-amd64.iso --network bridge=br1,model=virtio --network bridge=nm-bridge,model=virtio --force --autostart --graphics vnc --osinfo detect=on,name=generic




qemu-img create -f qcow2 /home/qcow2/kylin-01.qcow2  20G

virt-install --name=kylin-01 --vcpus=8 --ram=16384 --disk path=/home/qcow2/kylin-01.qcow2 --cdrom /home/exec/Kylin-4.0.2-server.iso --network bridge=br1,model=virtio --force --autostart --graphics vnc --osinfo detect=on,name=generic
```









### Virt-sysprep

给qcow2格式的镜像修改密码



```
yum install -y libguestfs-tools-c
virt-sysprep --root-password password:comleader@123 -a my-image.qcow2
```







### mount



在云上创建了规格为1T硬盘的虚拟机，但是由于制作的qcow2虚拟机磁盘是200G，还有800G未识别，下面是操作步骤

```
# 查看现有分区
fdisk -l 

# 创建新分区
fdisk /dev/vda
# 依次输入m/n/p/回车/回车/w保存，
# 查看，会有800G的新分区vda4
fdisk -l

# 创建目录
mkdir /data

# 格式化新分区
sudo mkfs.ext4 /dev/vda4

# 挂盘
mount /dev/vda4 /data
```







### qemu-img

```

qemu-img create -f qcow2 /qcow/cloudexploer-ubuntu.qcow2  200G


virt-install --name=cloudexploer-ubuntu --vcpus=8 --ram=16384 --disk path=/qcow/cloudexploer-ubuntu.qcow2 --cdrom /ISO/ubuntu-20.04.4-live-server-amd64.iso --network bridge=br1,model=virtio --network bridge=nm-bridge,model=virtio --force --autostart --graphics vnc --osinfo detect=on,name=generic





qemu-img create -f qcow2 /qcow/cloudexploer-ubuntu.qcow2  200G

virt-install --name=cloudexploer-ubuntu --vcpus=8 --ram=16384 --disk path=/qcow/cloudexploer-ubuntu.qcow2 --cdrom /ISO/ubuntu-20.04.4-live-server-amd64.iso --network bridge=br1,model=virtio --network bridge=nm-bridge,model=virtio --force --autostart --graphics vnc --osinfo detect=on,name=generic




qemu-img create -f qcow2 /home/qcow2/kylin-01.qcow2  20G

virt-install --name=kylin-01 --vcpus=8 --ram=16384 --disk path=/home/qcow2/kylin-01.qcow2 --cdrom /home/exec/Kylin-4.0.2-server.iso --network bridge=br1,model=virtio --force --autostart --graphics vnc --osinfo detect=on,name=generic
```





### nmcli

# 

```
# 更改网络名称
nmcli connection modify <OLD_CONNECTION_NAME> connection.id <NEW_CONNECTION_NAME>



# 查看连接
nmcli connection show


# 生成网卡配置： 
<DEVICE_NAME> 接口名称， <CONNECTION_NAME> 新连接的名称。
nmcli connection add type ethernet con-name <CONNECTION_NAME> ifname <DEVICE_NAME>

# 配置网络参数：
nmcli connection modify <CONNECTION_NAME> ipv4.method manual ipv4.addresses <IP_ADDRESS>/<SUBNET_MASK> ipv4.gateway <GATEWAY> ipv4.dns <DNS_SERVERS>

```





















