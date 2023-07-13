# 自动化运维



## pxe



PXE，全名Pre-boot Execution Environment，预启动执行环境；

通过网络接口启动计算机，不依赖本地存储设备（如硬盘）或本地已安装的操作系统；

由Intel和Systemsoft公司于1999年9月20日公布的技术；

Client/Server的工作模式；

PXE客户端会调用网际协议(IP)、用户数据报协议(UDP)、动态主机设定协议(DHCP)、小型文件传输协议(TFTP)等网络协议；

PXE客户端(client)这个术语是指机器在PXE启动过程中的角色。一个PXE客户端可以是一台服务器、笔记本电脑或者其他装有PXE启动代码的机器（我们电脑的网卡）。

### PXE的工作过程[¶](http://www.chrisjing.com/003-自动化装机/01-自动化装机工具-kickstart/#pxe_1)

![image-20201016090622925](http://www.chrisjing.com/003-%E8%87%AA%E5%8A%A8%E5%8C%96%E8%A3%85%E6%9C%BA/photo/image-20201016090622925.png)

![image-20201016090628754](http://www.chrisjing.com/003-%E8%87%AA%E5%8A%A8%E5%8C%96%E8%A3%85%E6%9C%BA/photo/image-20201016090628754.png)

（1）PXE Client向DHCP发送请求

PXE Client从自己的PXE网卡启动，通过PXE BootROM(自启动芯片)会以UDP(简单用户数据报协议)发送一个广播请求，向本网络中的DHCP服务器索取IP。

（2）DHCP服务器提供信息

DHCP服务器收到客户端的请求，验证是否来至合法的PXE Client的请求，验证通过它将给客户端一个“提供”响应，这个“提供”响应中包含了为客户端分配的IP地址、pxelinux启动程序(TFTP)位置，以及配置文件所在位置。

（3）PXE客户端请求下载启动文件

客户端收到服务器的“回应”后，会回应一个帧，以请求传送启动所需文件。这些启动文件包括：pxelinux.0、pxelinux.cfg/default、vmlinuz、initrd.img等文件。

（4）Boot Server响应客户端请求并传送文件

当服务器收到客户端的请求后，他们之间之后将有更多的信息在客户端与服务器之间作应答, 用以决定启动参数。BootROM由TFTP通讯协议从Boot Server下载启动安装程序所必须的文件(pxelinux.0、pxelinux.cfg/default)。default文件下载完成后，会根据该文件中定义的引导顺序，启动Linux安装程序的引导内核。

（5）请求下载自动应答文件

客户端通过pxelinux.cfg/default文件成功的引导Linux安装内核后，安装程序首先必须确定你通过什么安装介质来安装linux，如果是通过网络安装(NFS, FTP, HTTP)，则会在这个时候初始化网络，并定位安装源位置。接着会读取default文件中指定的自动应答文件ks.cfg所在位置，根据该位置请求下载该文件。

这里有个问题，在第2步和第5步初始化2次网络了，这是由于PXE获取的是安装用的内核以及安装程序等，而安装程序要获取的是安装系统所需的二进制包以及配置文件。因此PXE模块和安装程序是相对独立的，PXE的网络配置并不能传递给安装程序，从而进行两次获取IP地址过程，但IP地址在DHCP的租期内是一样的。

（6）客户端安装操作系统

将ks.cfg文件下载回来后，通过该文件找到OS Server，并按照该文件的配置请求下载安装过程需要的软件包。

OS Server和客户端建立连接后，将开始传输软件包，客户端将开始安装操作系统。安装完成后，将提示重新引导计算机。











## dhcp服务



DHCP（Dynamic Host Configuration Protocol，动态主机配置协议）通常被应用在大型的局域网络环境中，主要作用是集中的管理、分配IP地址，使网络环境中的主机动态的获得IP地址、网关地址、DNS服务器地址等信息，并能够提升地址的使用率。

DHCP分为两个部分：一个是服务器端，另一个是客户端。

所有客户机的IP地址设定资料都由DHCP服务器集中管理，并负责处理客户端的DHCP请求；而客户端则会使用从服务器分配下来的IP地址。

![image-20201016090851143](http://www.chrisjing.com/003-%E8%87%AA%E5%8A%A8%E5%8C%96%E8%A3%85%E6%9C%BA/photo/image-20201016090851143.png)

### DHCP服务器IP分配方式

DHCP服务器提供三种IP分配方式：

***\*自动分配（Automatic Allocation）\****

自动分配是当DHCP客户端第一次成功地从DHCP服务器端分配到一个IP地址之后，就永远使用这个地址。

***\*动态分配（Dynamic Allocation）\****

动态分配是当DHCP客户端第一次从DHCP服务器分配到IP地址后，并非永久地使用该地址，每次使用完后，DHCP客户端就得释放这个IP地址，以给其他客户端使用。

***\*手动分配\****

手动分配是由DHCP服务器管理员专门为客户端指定IP地址。

### DHCP服务工作流程

DHCP客户机在启动时，会搜寻网络中是否存在DHCP服务器。如果找到，则给DHCP服务器发送一个请求。DHCP服务器接到请求后，为DHCP客户机选择TCP/IP配置的参数，并把这些参数发送给客户端。 如果已配置冲突检测设置，则DHCP服务器在将租约中的地址提供给客户机之前会使用Ping测试作用域中每个可用地址的连通性。这可确保提供给客户的每个IP地址都没有被使用手动TCP/IP配置的另一台非DHCP计算机使用。

根据客户端是否第一次登录网络，DHCP的工作形式会有所不同。客户端从DHCP服务器上获得IP地址的所有过程可以分为以下六个步骤：

其中新客户端的租约过程的4个步骤。

![image-20201016091011061](http://www.chrisjing.com/003-%E8%87%AA%E5%8A%A8%E5%8C%96%E8%A3%85%E6%9C%BA/photo/image-20201016091011061.png)

#### 工作过程1：寻找DHCP服务器

当DHCP客户端第一次登录网络的时候，计算机发现本机上没有任何IP地址设定，将以广播方式发送DHCP discover发现信息来寻找DHCP服务器，即向255.255.255.255发送特定的广播信息。网络上每一台安装了TCP/IP协议的主机都会接收这个广播信息，但只有DHCP服务器才会做出响应。

![image-20201016091030978](http://www.chrisjing.com/003-%E8%87%AA%E5%8A%A8%E5%8C%96%E8%A3%85%E6%9C%BA/photo/image-20201016091030978.png)

#### 工作过程2：分配IP地址

在网络中接收到DHCP discover发现信息的DHCP服务器就会做出响应，它从尚未分配的IP地址池中挑选一个分配给DHCP客户机，向DHCP客户机发送一个包含分配的IP地址和其他设置的DHCP offer提供信息。

![image-20201016091058876](http://www.chrisjing.com/003-%E8%87%AA%E5%8A%A8%E5%8C%96%E8%A3%85%E6%9C%BA/photo/image-20201016091058876.png)

#### 工作过程3：接受IP地址

DHCP客户端接受到DHCP offer提供信息之后，选择第一个接收到的提供信息，然后以广播的方式回答一个DHCP request请求信息，该信息包含向它所选定的DHCP服务器请求IP地址的内容。

![image-20201016091121974](http://www.chrisjing.com/003-%E8%87%AA%E5%8A%A8%E5%8C%96%E8%A3%85%E6%9C%BA/photo/image-20201016091121974.png)

#### 工作过程4：IP地址分配确认

当DHCP服务器收到DHCP客户端回答的DHCP request请求信息之后，便向DHCP客户端发送一个包含它所提供的IP地址和其他设置的DHCP ack确认信息，告诉DHCP客户端可以使用它提供的IP地址。然后，DHCP客户机便将其TCP/IP协议与网卡绑定，另外，除了DHCP客户机选中的DHCP服务器外，其他的DHCP服务器将收回曾经提供的IP地址。

![image-20201016091149214](http://www.chrisjing.com/003-%E8%87%AA%E5%8A%A8%E5%8C%96%E8%A3%85%E6%9C%BA/photo/image-20201016091149214.png)

#### 工作过程5：重新登录

以后DHCP客户端每次重新登录网络时，就不需要再发送DHCP discover发现信息了，而是直接发送包含前一次所分配的IP地址的DHCP request请求信息。当DHCP服务器收到这一信息后，它会尝试让DHCP客户机继续使用原来的IP地址，并回答一个DHCP ack确认信息。如果此IP地址已无法再分配给原来的DHCP客户机使用时，则DHCP服务器给DHCP客户机回答一个DHCP nack否认信息。当原来的DHCP客户机收到此DHCP nack否认信息后，它就必须重新发送DHCP discover发现信息来请求新的IP地址。

![image-20201016091211809](http://www.chrisjing.com/003-%E8%87%AA%E5%8A%A8%E5%8C%96%E8%A3%85%E6%9C%BA/photo/image-20201016091211809.png)

如果客户端DHCP request 内的IP地址在服务器端没有被使用，DHCP服务器回复DHCP ACK继续使用IP。

![image-20201016091223030](http://www.chrisjing.com/003-%E8%87%AA%E5%8A%A8%E5%8C%96%E8%A3%85%E6%9C%BA/photo/image-20201016091223030.png)

如果客户端DHCP request 内的IP地址在服务器端已被使用，DHCP服务器回复DHCP NACK告诉客户端IP已被使用。

![image-20201016091237669](http://www.chrisjing.com/003-%E8%87%AA%E5%8A%A8%E5%8C%96%E8%A3%85%E6%9C%BA/photo/image-20201016091237669.png)

客户端重新开始DHCP流程。

![image-20201016091255342](http://www.chrisjing.com/003-%E8%87%AA%E5%8A%A8%E5%8C%96%E8%A3%85%E6%9C%BA/photo/image-20201016091255342.png)

#### 工作过程6：更新租约

DHCP服务器向DHCP客户机出租的IP地址一般都有一个租借期限，期满后DHCP服务器便会收回出租的IP地址。如果DHCP客户机要延长其IP租约，则必须更新其IP租约。DHCP客户机启动时和IP租约期限到达租约的50%时，DHCP客户机都会自动向DHCP服务器发送更新其IP租约的信息。

![image-20201016091315902](http://www.chrisjing.com/003-%E8%87%AA%E5%8A%A8%E5%8C%96%E8%A3%85%E6%9C%BA/photo/image-20201016091315902.png)

### DHCP服务安装配置[¶](http://www.chrisjing.com/003-自动化装机/01-自动化装机工具-kickstart/#dhcp_2)

提示：配置DHCP服务之前一定要先将虚拟机的NAT网段的dhcp自动分配IP的功能取消，不然则会影响本次试验。

```
[root@m01 ~]# yum -y install dhcp           #安装dhcp服务软件
[root@m01 ~]# rpm -ql dhcp |grep "dhcpd.conf"
/etc/dhcp/dhcpd.conf    # 查看配置文件位置
/usr/share/doc/dhcp-4.1.1/dhcpd-conf-to-ldap
/usr/share/doc/dhcp-4.1.1/dhcpd.conf.sample
/usr/share/man/man5/dhcpd.conf.5.gz
 [root@linux-node1 ~]# cat /etc/dhcp/dhcpd.conf     #默认配置
#
# DHCP Server Configuration file.
#   see /usr/share/doc/dhcp*/dhcpd.conf.sample
#   see 'man 5 dhcpd.conf'
#
[root@linux-node1 ~]# vim /etc/dhcp/dhcpd.conf
subnet 10.0.0.0 netmask 255.255.255.0 {
        range 10.0.0.150 10.0.0.200;
        option subnet-mask 255.255.255.0;
        default-lease-time 21600;
        max-lease-time 43200;
        next-server 10.0.0.7;
        filename "/pxelinux.0";
}
# 配置注释
range 10.0.0.100 10.0.0.200;                # 可分配的起始IP-结束IP
option subnet-mask 255.255.255.0;       # 设定netmask
default-lease-time 21600;                   # 设置默认的IP租用期限
max-lease-time 43200;                        # 设置最大的IP租用期限
next-server 10.0.0.61;                      # 告知客户端TFTP服务器的ip
filename "/pxelinux.0";                      # 告知客户端从TFTP根目录下载pxelinux.0文件
[root@linux-node1 ~]# /etc/init.d/dhcpd start
Starting dhcpd:                                            [  OK  ]
[root@linux-node1 ~]# netstat -tunlp|grep dhcp
udp        0      0 0.0.0.0:67                  0.0.0.0:*                               1573/dhcpd
```

遇到的错误

![image-20201016091353704](http://www.chrisjing.com/003-%E8%87%AA%E5%8A%A8%E5%8C%96%E8%A3%85%E6%9C%BA/photo/image-20201016091353704.png)

解决方法：请将dhcp配置文件next-server 10.0.0.7;IP地址修改为你的kickstack服务器的地址，重启服务即可

****** 本来软件装完后都要加入开机自启动，但这个Kickstart系统就不能开机自启动，而且用完后服务都要关闭，防止未来重启服务器自动重装系统了。******

** 如果机器数量过多的话，注意dhcp服务器的地址池，不要因为耗尽IP而导致dhcpd服务器没有IP地址release的情况。**

### DHCP指定监听网卡[¶](http://www.chrisjing.com/003-自动化装机/01-自动化装机工具-kickstart/#dhcp_3)

说明：此知识点与本文无关，只是作者用过这个功能，记于此。

** 多网卡默认监听eth0，指定DHCP监听eth1网卡**

```
[root@linux-node1 ~]# vim /etc/sysconfig/dhcpd
# Command line options here
DHCPDARGS=eth1  # 指定监听网卡
[root@linux-node1 ~]# /etc/init.d/dhcpd restart
[root@linux-node1 ~]# tailf /var/log/messages
May 26 14:24:38 Kickstart kernel: e1000: eth1 NIC Link is Up 1000 Mbps Full Duplex, Flow Control: None
May 26 14:29:04 Kickstart dhcpd: Internet Systems Consortium DHCP Server 4.1.1-P1
May 26 14:29:04 Kickstart dhcpd: Copyright 2004-2010 Internet Systems Consortium.
May 26 14:29:04 Kickstart dhcpd: All rights reserved.
May 26 14:29:04 Kickstart dhcpd: For info, please visit https://www.isc.org/software/dhcp/
May 26 14:29:04 Kickstart dhcpd: Not searching LDAP since ldap-server, ldap-port and ldap-base-dn were not specified in the config file
May 26 14:29:04 Kickstart dhcpd: Wrote 0 leases to leases file.
May 26 14:29:04 Kickstart dhcpd: Listening on LPF/eth1/00:0c:29:ea:c1:83/10.0.10.0/24
May 26 14:29:04 Kickstart dhcpd: Sending on   LPF/eth1/00:0c:29:ea:c1:83/10.0.10.0/24
May 26 14:29:04 Kickstart dhcpd: Sending on   Socket/fallback/fallback-net
……
```