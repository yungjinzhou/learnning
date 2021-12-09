## vmware虚拟机动态扩展磁盘空间

Vmware中虚拟机使用时间长，发现磁盘空间不够，有些情况是无法新加新硬盘扩容到虚拟机中，因为有些数据不好移动或数据目录无法修改。 所以，在不加新的硬盘情况下，VMware中直接在原来的硬盘上新增空间扩容。操作思路是，硬盘增加空间、虚拟机硬盘fdisk分区、扩展卷组、扩容逻辑卷、重新定义文件系统操作。

#### VMware虚拟机增加硬盘空间

进入虚拟机的编辑设置，将已有的硬盘空间40G增加到50G，如下图

#### Fdisk分区（fdisk -l）

进入Linux服务器中，输入fdisk -l 命令查看现有分区情况。

发现分了两个区。用 fdisk /dev/sda 命令进行分区，依次输入 m、n、p、默认回车、默认回车、w 命令。
再次输入fdisk -l 命令查看分区，发现多了 /dev/sda3 分区。

#### 扩展卷组

输入 **lsblk** 命令查看新加的硬盘分区状况。实际操作发现新加的分区 /dev/sda3 在 lsblk 命令下不显示，需重启虚拟机。

对新加的未挂载的硬盘分区 /dev/sda3 添加到扩展卷组中，输入：

```
vgextend centos /dev/sda3
```

现在查看卷组，输入 vgdisplay 命令。

```
vgdisplay
```

发现卷组中 Free 项多了10个G的空间。现在可将该10个G空间加入到逻辑中。
#### 扩展逻辑卷

将10个G空间添加到 /dev/centos/root 逻辑卷中，输入命令。

```
lvextend -r -L +10G /dev/centos/root
```

接下来查看逻辑卷空间，输入 lvs 或者 lvsdisplay 命令查看。
#### 重新定义文件系统

Centos7系统使用 xfs_growfs 命令重新定义文件系统，如果是CentOS6使用 resize2fs 命令。

```
xfs_growfs /dev/mapper/centos-root
```



**最后 df -h 命令可查看到 /dev/mapper/centos-root 文件系统下 / 增加了10G空间。**



参考链接：https://blog.51cto.com/u_10874766/2517183