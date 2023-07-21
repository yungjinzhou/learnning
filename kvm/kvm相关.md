## kvm相关





、查看虚拟机原有网卡信息

```cobol
[root@room1pc01 ~]# virsh domiflist kylin-wd
Interface  Type       Source     Model       MAC
```





给运行中的虚拟机添加网卡

```
virsh define /etc/libvirt/qemu/snale.xml
virsh attach-interface snale --type bridge --source br0  --target vnet1 --config

virsh attach-interface snale --type bridge --source br0  --target vnet1 --live  --config   在线更新

说明：type类型，一般是桥接bridge，还有network类型
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













