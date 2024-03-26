# WIN10 x86环境部署ARM虚拟机（银河麒麟）



我们经常使用的是x86架构的cpu，而对于不同cpu架构的arm架构的操作系统，我们可以通过QEMU模拟器来进行模拟一个arm环境

### 1、部署前的准备

#### arm的镜像：

以此镜像为例：Kylin-Server-10-SP2-aarch64-Release-Build09-20210524.iso

https://res.frytea.com/d/OS/Kylin/Kylin-Server-10-SP2-Release-Build09-20210524-arm64.iso

#### QEMU 软件：

下载地址：https://qemu.weilnetz.de/w64/2021/qemu-w64-setup-20210505.exe



#### UEFI（BIOS的替代方案）：

下载地址：http://releases.linaro.org/components/kernel/uefi-linaro/16.02/release/qemu64/QEMU_EFI.fd



#### 网络配置

Win10物理网卡和tap虚拟网卡进行桥接
安装openvpn虚拟网卡
双击下载下来的openvpn-connect-3.3.6.2752_signed.msi软件，和安装其它软件一样，一步步安装即可。

修改网卡名称
安装完成后，在网络连接界面可以看到新增加了一块网卡，如下图所示：

![win 10 x86安装arm架构虚拟机 虚拟机安装arm系统_arm架构_05](https://s2.51cto.com/images/blog/202309/03095929_64f3e881355ce41562.png?x-oss-process=image/watermark,size_16,text_QDUxQ1RP5Y2a5a6i,color_FFFFFF,t_30,g_se,x_10,y_10,shadow_20,type_ZmFuZ3poZW5naGVpdGk=/format,webp/resize,m_fixed,w_1184)



注意：大的红框中的网卡是新增加的，黄色框中的名称是经过我修改后的，安装完openven后可能不是这个名字，下面马上要说修改网卡名称的操作。只需要关注小的红框中的网卡类型是否是“TAP-Windows Adapter”即可，找到这种类型的网卡就是新增加的网卡。且连接状态也是未连接状态，不用关注，等启动虚拟机后即可变为正常状态。红框下面的“以太网”是我电脑的真实物理网卡。右键单击新增加的网卡，重命名该网卡，



注意：我这里修改为了tap0，其它的名称也可以，建议还是修改为tapXX这种形式，最好不要用中文名称。



![img](https://img-blog.csdnimg.cn/img_convert/32eafe702889628b2af060145122f864.png)

同时选中tap0和以太网，右键创建网桥

![img](https://img-blog.csdnimg.cn/img_convert/ba8d0adab467eae0b363044186bd1176.png)





### 2、安装qemu软件

双击qemu-w64-setup-20210505.exe进行安装 ，下一步下一步，选择指定路径即可，例如：安装在D:\VM\arm64\qemu目录下

#### 配置环境变量

在“我的电脑”上右键，找到“属性”：

弹出“设置”界面，

点击“高级系统设置”，弹出系统属性界面，

点击“环境变量”按钮，弹出环境变量编辑界面

![win 10 x86安装arm架构虚拟机 虚拟机安装arm系统_windows_04](https://s2.51cto.com/images/blog/202309/03095929_64f3e8811ec561443.png?x-oss-process=image/watermark,size_16,text_QDUxQ1RP5Y2a5a6i,color_FFFFFF,t_30,g_se,x_10,y_10,shadow_20,type_ZmFuZ3poZW5naGVpdGk=/format,webp/resize,m_fixed,w_1184)

打开cmd，执行qemu-system-aarch64 -version，可以展示版本信息，如下所示：

qemu-system-aarch64 -version
QEMU emulator version 7.1.0 (v7.1.0-11925-g4ec481870e-dirty)
Copyright (c) 2003-2022 Fabrice Bellard and the QEMU Project developers



#### 生成虚拟机硬盘

安装好qemu软件后，通过qemu生成虚机硬盘，

进入到qemu的安装目录

qemu-img create -f qcow2 D:\VM\arm64\kylindisk.qcow2 40G
会生成kylindisk.qcow2硬盘文件



### 3、QEMU_EFI.fd文件

将QEMU_EFI.fd文件放到硬盘文件同目录下，例如D:\VM\arm64（镜像文件也可以放在此目录下）

### 4、安装arm系统

进入到qemu目录里面


进入到cmd命令行，执行以下命令

qemu-system-aarch64.exe -m 8192 -cpu cortex-a72 -smp 8,sockets=4,cores=2 -M virt -bios D:\VM\arm64\QEMU_EFI.fd -device VGA -device nec-usb-xhci -device usb-mouse -device usb-kbd -drive if=none,file=D:\vm\arm64\kylindisk.qcow2,id=hd0 -device virtio-blk-device,drive=hd0 -drive if=none,file=D:\VM\arm64\Kylin-Server-10-SP2-aarch64-Release-Build09-20210524.iso,id=cdrom,media=cdrom -device virtio-scsi-device -device scsi-cd,drive=cdrom  -net nic -net tap,ifname=tap0
-m 8192指的是运行内存

此时应该能看到系统安装界面，必须在五秒钟之内通过键盘方向键选择“Install Kylin-Desktop V10-SP1”，按下回车，否则会进入预览模式，如果你不小心错过了，请关闭QEMU窗口并重新执行上面的步骤。注意，安装期间请勿关闭控制台窗口，否则虚拟机进程也会关闭，安装界面如下

![img](https://img-blog.csdnimg.cn/a54f59e5561f43e491f2e49aaba24c8f.png)

之后便是漫长的等待……期间可能会长时间黑屏，不要怀疑自己，请让它继续运行

![img](https://img-blog.csdnimg.cn/7cc773fa54764034a450f844c7b506ec.png)





![img](https://img-blog.csdnimg.cn/29fa8e08e4584924b08c88aa4cc87d43.png)



![img](https://img-blog.csdnimg.cn/66dbb1d82a294179bb0ca0aa71c81175.png)



![img](https://img-blog.csdnimg.cn/437187ee89a445cfabb596540eefd45f.png)



![img](https://img-blog.csdnimg.cn/48b533998b494be4b91d226f5c24d89a.png)



![img](https://img-blog.csdnimg.cn/8f03d4cf17fc4adc85c27258930d544e.png)





![img](https://img-blog.csdnimg.cn/cc5083a836c84390b060e0a8a6500faf.png)

此处可以配置和物理机一个网段的ip地址



![img](https://img-blog.csdnimg.cn/f0251836d8d742c39ab8d6491b2cadad.png)



![img](https://img-blog.csdnimg.cn/3aec383aa2be40499c4ec5fa31f20857.png)

重启系统

![img](https://img-blog.csdnimg.cn/0aad96f89c8341719463c69894f62f60.png)





![img](https://img-blog.csdnimg.cn/821ddeae48dc43dd87b58552a03a1685.png)





![img](https://img-blog.csdnimg.cn/0aab28000a5c426dbf4f529ca2625808.png)



### 给虚拟机手动配置ip

网桥创建成功后启动虚拟机，然后给虚拟机手动配置ip。

![img](https://img-blog.csdnimg.cn/img_convert/73b0c289b32e7069d814208721eb5e37.png)





启动虚拟机
安装好后，我们需要再次启动（无需指定iso文件启动）
进入到qemu所在位置
进入到cmd命令行，执行以下命令

qemu-system-aarch64 -m 8192 -cpu cortex-a72 -smp 8,sockets=4,cores=2 -M virt -bios D:\VM\arm64\QEMU_EFI.fd -device VGA -device nec-usb-xhci -device usb-mouse -device usb-kbd -drive if=none,file=D:\vm\arm64\kylindisk.qcow2,id=hd0 -device virtio-blk-device,drive=hd0 -net nic -net tap,ifname=tap0





可以将上述命令写入  startsys.bat，双击即可启动

