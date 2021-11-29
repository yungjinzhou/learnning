## openstack-neutron学习

### 1. 二层与三层
#### 1.1 OSI七层模型

一般情况下，OSI模型分为七层：应用层，表示层，会话层，传输层，网络层，数据链路层和物理层。

#### 1.2 二层、三层交换机

二层交换机工作于OSI模型的二层(数据链路层)，故而称为二层交换机，主要功能包括物理编址、错误校验、帧序列以及流控。而三层交换机位于三层（网络层），是一个具有三层交换功能的设备，即带有三层路由功能的二层交换机，但它是二者的有机结合，并不是简单地把路由器设备的硬件及软件叠加在局域网交换机上。

#### 1.3 二层、三层网络

二层网络仅仅通过MAC寻址即可实现通讯，但仅仅是同一个冲突域内；三层网络则需要通过IP路由实现跨网段的通讯，可以跨多个冲突域。

#### 1.4 Neutron几个重要概念

##### 1.4.1  **Router**

实现不同网段的通信，为租户提供路由、NAT等服务。

##### 1.4.2  **Network**

虚拟网络中的L2 domain。对应于一个真实物理网络中的二层局域网（VLAN），从租户的的角度而言，是租户私有的。

##### 1.4.3  **Subnet**

为网络中的三层概念，指定一段IPV4或IPV6地址并描述其相关的配置信息。它附加在一个二层Network上，指明属于这个network的虚拟机可使用的IP地址范围。

##### 1.4.4  **Port**

是一个逻辑的概念，虚拟网络中网卡对应的端口。

##### 1.4.5  **Neutron Security Group 实现** 

Security group通过Linux IPtables来实现，为此，在Compute节点上引入了qbr*这样的Linux传统bridge（iptables规则目前无法加载到直接挂在到ovs的tap设备上）。iptables只是一个用户空间的程序，真正干活的其实是Linux内核netfilter，通过iptables创建新规则，其实就是在netfilter中插入一个hook，从而实现修改数据包、控制数据包流向等。

##### 1.4.6 **Neutron Security Group 行为流程**

  ![1629447169549](.\1629447169549.png)

##### 1.4.7 DHCP

DHCP作用是分配IP地址，配置主机（默认网关，DNS等），管理主机地址和配置。

DHCP工作流程，采用UDP封装报文，端口67，68。

![img](.\企业微信截图_16294475302914.png)

DHCP Agent管理dnsmasq。每一个Network对应一个到多个dnsmasq进程，每个dnsmasq对应一个DHCP Server。

##### 1.4.8 Neutron DHCP实现

![img](.\企业微信截图_16294476175231.png)



##### 1.4.9 交换机与vlan 

当交换机的某个vlan的port被占完后，比如交换机A的vlan10的port被占完了，需要用到第二个交换机B，也给B划分vlan10，然后将A和B连接起来，连接的端口设置为trunk port，这样从trunk port出去的数据会加上vlan tag的标志，只有vlan tag一样的才能收到。



### 2. Linux虚拟网络基础

#### 2.1 tap与tun

Linux虚拟网络基础—tap（虚拟以太设备）

Linux中谈到tap，经常会和tun并列谈论。两者都是操作系统内核中的**虚拟网络设备**。**tap位于网络OSI模型的二层（数据链路层），tun位于网络的三层。**需要说明的是，这里所说的设备是Linux的概念，并不是我们平时生活中所说的设备。比如，生活中，我们常常把一台物理路由器称为一台设备。而Linux所说的设备，其背后指的是一个类似于数据结构、内核模块或设备驱动着样的含义。
虚拟网卡Tun/tap驱动是一个开源项目，支持很多的类UNIX平台，OpenVPN和Vtun都是基于它实现隧道包封装。
tun/tap驱动程序实现了虚拟网卡的功能，tun表示虚拟的是点对点设备，tap表示虚拟的是以太网设备，这两种设备针对网络包实施不同的封装。利用tun/tap驱动，可以将tcp/ip协议栈处理好的网络分包传给任何一个使用tun/tap驱动的进程，由进程重新处理后再发到物理链路中。

用户层程序通过**tun设备只能读写IP数据包**，而通过**tap设备能读写链路层数据包**，类似于普通socket和raw socket的差别一样，处理数据包的格式不一样。

#### 2.2 tap/tun与物理网络区别

根据数据包的收发流程，知道Linux内核中有一个网络设备管理层，处于网络设备驱动和协议栈之间，负责衔接它们之间的数据交互。驱动不需要了解协议栈的细节，协议栈也不需要了解设备驱动的细节。

​        对于一个网络设备来说，就像一个管道（pipe）一样，有两端，从其中任意一端收到的数据将从另一端发送出去。比如一个**物理网卡eth0**，它的两端分别是**内核协议栈**（通过内核网络设备管理模块间接的通信）和**外面的物理网络**，从物理网络收到的数据，会转发给内核协议栈，而应用程序从协议栈发过来的数据将会通过物理网络发送出去。

​       那么对于一个虚拟网络设备呢？首先它也归内核的网络设备管理子系统管理，对于**Linux内核网络设备管理模块**来说，虚拟设备和物理设备没有区别，都是网络设备，都能配置IP，从网络设备来的数据，都会转发给协议栈，协议栈过来的数据，也会交由网络设备发送出去，至于是怎么发送出去的，发到哪里去，那是设备驱动的事情，跟Linux内核就没关系了，所以说**虚拟网络设备的一端也是协议栈，而另一端是什么取决于虚拟网络设备的驱动实现。**

![img](.\企业微信截图_16283899163640.png)



![img](.\企业微信截图_16283900005302.png)

#### 2.3 Namespace

Namespace类似传统网络里的VRF，与VRF不同的是：VRF做的是网络层三层隔离。而namespace隔离的更彻底，它做的是整个协议栈的隔离，隔离的资源包括：UTS(UnixTimesharing  System的简称，包含内存名称、版本、 底层体系结构等信息)、IPS(所有与进程间通信（IPC）有关的信息)、mnt(当前装载的文件系统)、PID(有关进程ID的信息)、user(资源配额的信息)、net(网络信息)。

从网络角度看一个namespace提供了一份独立的网络协议栈（网络设备接口、IPv4/v6、IP路由、防火墙规则、sockets等），**而一个设备（Linux Device）只能位于一个namespace中，不同namespace中的设备可以利用vethpair进行桥接。**

#### 2.4 veth pair

veth pair不是一个设备，而是一对设备，以连接两个虚拟以太端口。操作vethpair，需要跟namespace一起配合，不然就没有意义。(<font color=red>**veth pair连接的是二层同网段的两个设备，tun是隧道，可以连接不同网段的设备**</font>)

![img](.\企业微信截图_1628390528266.png)

#### 2.5 Bridge

在Linux的语境里，Bridge（网桥）与Switch（交换机）是一个概念。因为一对veth pair只能连接两台device，因此如果需要多台设备互联则需要bridge。

如图：4个namespace，每个namespace都有一个tap，每个tap与网桥vb1的tap组成一对veth pair，这样，这4个namespace就可以**二层互通**了。

![img](.\企业微信截图_16283907317141.png)

##### 2.5.1 br-int

bridge-intergration，综合网桥，常用于表示实现主要内部网络功能的网桥。

##### 2.5.2 br-ex

bridge-external，外部网桥，通常表示负责跟外部网络通信的网桥。

#### 2.6 tun

tun是一个网络层(IP)的点对点设备，它启用了IP层隧道功能。Linux原生支持的三层隧道。支持隧道情况：ipip(ipv4 in ipv4)、gre(ipv4/ipv6 over ipv4)、sit(ipv6 over ipv4)、isatap(ipv6/ipv4隧道)、vti(ipsec接口)。
学过传统网络GRE隧道的人更容易理解，如图：
NS1的tun1的ip 10.10.10.1与NS2的tun2的ip 10.10.20.2建立tun
NS1的tun的ip是10.10.10.1，隧道的外层源ip是192.168.1.1，目的ip是192.168.2.1，是不是跟GRE很像。

![img](.\企业微信截图_16283912007141.png)

#### 2.7 Router

Linux创建Router并没有像创建虚拟Bridge那样，有一个直接的命令brctl，而且它间接的命令也没有，不能创建虚拟路由器……因为它就是路由器（Router) !
如图：我们需要在router(也就是我们的操作系统linux上增加去往各NS的路由)。

![img](.\企业微信截图_16283915711050.png)

#### 2.8 iptable

我们通常把iptable说成是linux的防火墙，实际上这种说法并不准确。实际上iptable只是一个运行在用户空间的命令行工具，真正实现防火墙功能的是内核空间的netfilter模块。

这里我们先知道防火墙执行模块netfilter位于内核空间，命令行iptable位于用户空间。我们在通过iptable配置的防火墙策略(包括NAT)会在netfilter执行。

iptables有5个链：PREROUTING,INPUT,FORWARD,OUTPUT,POSTROUTING

l  PREROUTING：报文进入网络接口尚未进入路由之前的时刻；

l  INPUT：路由判断是本机接收的报文，准备从内核空间进入到用户空间的时刻；

l  FORWARD：路由判断不是本机接收的报文，需要路由转发，路由转发的那个时刻；

l  OUTPUT：本机报文需要发出去 经过路由判断选择好端口以后，准备发送的那一刻；

l  POSTROUTING：FORWARD/OUTPUT已经完成，报文即将出网络接口的那一刻。

 DNAT用的是PREROUTING，修改的是目的地址，SNAT用的是POSTROUTING,修改的是源地址。

Iptable有5个表:filter,nat,mangle,raw, security，raw表和security表不常用。主流文档都是说5链4表，没有包括security表。

l  Raw表——决定数据包是否被状态跟踪机制处理

l  Mangle表——修改数据包的服务类型、TTL、并且可以配置路由实现QOS

l  Nat表——用于网络地址转换（IP、端口）

l  filter表——过滤数据包

l  security 表（用于强制访问控制网络规则，例如：SELinux）

4个表的优先级由高到低的顺序为:**raw-->mangle-->nat-->filter**。RAW表,在某个链上,RAW表处理完后,将跳过NAT表和 ip_conntrack处理,即不再做地址转换和数据包的链接跟踪处理了。RAW表可以应用在那些不需要做nat的情况下，以提高性能。如大量访问的web服务器，可以让80端口不再让iptables做数据包的链接跟踪处理，以提高用户的访问速度。

下面讲下数据包流向与处理：

1. 如果是外部访问的目的是本机，比如用户空间部署了WEB服务，外部来访问。数据包从外部进入网卡----->PREROUTING处理----->INPUT处理----->到达用户空间程序接口，程序处理完成后发出----->OUTPUT处理----->POSTROUTING处理。每个处理点都有对应的表，表的处理顺序按照raw-->mangle-->nat-->filter处理。
2. 如果用户访问的目的不是本机，linux只是一个中转(转发)设备，此时需要开启ip forward功能，数据流就是进入网卡-----> PREROUTING处理-----> FORWARD处理-----> POSTROUTING处理。

![img](.\企业微信截图_16283916492793.png)

#### 2.9 NAT

Netfilter中的NAT有三个点做处理，

(1)   NAT-PREROUTING (DNAT)

数据报文进入PREROUTING，NAT模块就会处理，比如用户空间的WEB服务私网地址192.168.0.1，对外提供公网ip是220.1.1.1。

当外部ip访问220.1.1.1时，PREROUTING接受数据包，NAT模块处理将目的ip 220.1.1.1转换为私网ip192.168.0.1，这就是DNAT。

(2)   NAT-POSTROUTING (SNAT)

用户空间应用程序访问外部网络，比如用户空间应用程序访问114.114.114.144，私网ip 192.168.0.1，此时数据包流经POSTROUTING，NAT模块会处理，将192.168.0.1转换为220.2.2.2，对于目的ip114.114.114.114来说，就是220.2.2.2访问它，这就是SNAT。

(3)   NAT-OUTPUT (DNAT)

我们把内核空间想象成一台防火墙，防火墙自身对外发送报文访问外部时，就在OUTPUT做DNAT，此时不需要再POSTROUTING点再做NAT。因为此时从OUTPUT出来的源IP已经是公网地址了

#### 2.10  Firewall

防火墙根据规则执行accept/reject动作，防火墙规则的元素如下：

入接口、出接口、协议、源地址/子网、目的地址/子网、源端口、目的端口。

Netfilter中的Firewall会在这三个点进行处理：INPUT/FORWARD/OUTPUT

#### 2.11 Mangle

mangle表主要用于修改数据包的ToS(  Type of Service，服务类型）、 TTL(Time to Live，生存周期）以及为数据包设置Mark标记，以实现QoS(Qualityof Service，服务质量）调整以及策略路由等应用。Netfilter每个点都可以做mangle。







### 3. OpenVSwitch

#### 31. 介绍

**openvSwitch**是一个高质量的、多层**虚拟交换机**，使用开源Apache2.0许可协议，由 Nicira Networks开发，主要实现代码为可移植的C代码。它的目的是让大规模网络自动化可以通过编程扩展,同时仍然支持标准的管理接口和协议（例如NetFlow, sFlow, SPAN, RSPAN, CLI, LACP, 802.1ag）。此外,它被设计位支持跨越多个物理服务器的分布式环境，类似于VMware的vNetwork分布式vswitch或Cisco Nexus 1000 V。Open vSwitch支持多种linux 虚拟化技术，包括Xen/XenServer， KVM和VirtualBox。
　　openvswitch是一个虚拟交换软件，主要用于虚拟机VM环境，作为一个虚拟交换机，支持Xen/XenServer，KVM以及virtualBox多种虚拟化技术。在这种虚拟化的环境中，一个虚拟交换机主要有两个作用：传递虚拟机之间的流量，以及实现虚拟机和外界网络的通信。
　　内核模块实现了多个“数据路径”（类似于网桥），每个都可以有多个“vports”（类似于桥内的端口）。每个数据路径也通过关联一下流表（flow table）来设置操作，而这些流表中的流都是用户空间在报文头和元数据的基础上映射的关键信息，一般的操作都是将数据包转发到另一个vport。当一个数据包到达一个vport，内核模块所做的处理是提取其流的关键信息并在流表中查找这些关键信息。当有一个匹配的流时它执行对应的操作。如果没有匹配，它会将数据包送到用户空间的处理队列中（作为处理的一部分，用户空间可能会设置一个流用于以后碰到相同类型的数据包可以在内核中执行操作）。

在基于Linux内核的系统上，应用最广泛的还是系统自带的虚拟交换机`Linux Bridge`，它是一个单纯的基于MAC地址学习的二层交换机，简单高效，但同时缺乏一些高级特性，比如OpenFlow,VLAN tag,QOS,ACL,Flow等，而且在隧道协议支持上，Linux Bridge只支持vxlan，OVS支持gre/vxlan/IPsec等，这也决定了OVS更适用于实现SDN技术。


#### 3.2 OVS架构

看下OVS整体架构，用户空间主要组件有数据库服务ovsdb-server和守护进程ovs-vswitchd。kernel中是datapath内核模块。最上面的Controller表示OpenFlow控制器，控制器与OVS是通过OpenFlow协议进行连接，控制器不一定位于OVS主机上，下面分别介绍图中各组件
![1628772049407](.\1628772049407.png)

##### 3.2.1 ovs-vswitchd

`ovs-vswitchd`守护进程是OVS的核心部件，它和`datapath`内核模块一起实现OVS基于流的数据交换。作为核心组件，它使用openflow协议与上层OpenFlow控制器通信，使用OVSDB协议与`ovsdb-server`通信，使用`netlink`和`datapath`内核模块通信。`ovs-vswitchd`在启动时会读取`ovsdb-server`中配置信息，然后配置内核中的`datapaths`和所有OVS switches，当ovsdb中的配置信息改变时(例如使用ovs-vsctl工具)，`ovs-vswitchd`也会自动更新其配置以保持与数据库同步。
在OVS中，`ovs-vswitchd`从OpenFlow控制器获取流表规则，然后把从`datapath`中收到的数据包在流表中进行匹配，找到匹配的flows并把所需应用的actions返回给`datapath`，同时作为处理的一部分，`ovs-vswitchd`会在`datapath`中设置一条datapath flows用于后续相同类型的数据包可以直接在内核中执行动作，此datapath flows相当于OpenFlow flows的缓存。

##### 3.2.2 ovsdb-server

`ovsdb-server`是OVS轻量级的数据库服务，用于整个OVS的配置信息，包括接口/交换内容/VLAN等，OVS主进程`ovs-vswitchd`根据数据库中的配置信息工作，下面是`ovsdb-server`进程详细信息

```cpp
ps -ef |grep ovsdb-server
root     22166 22165  0 Jan17 ?        00:02:32 ovsdb-server /etc/openvswitch/conf.db -vconsole:emer -vsyslog:err -vfile:info --remote=punix:/var/run/openvswitch/db.sock --private-key=db:Open_vSwitch,SSL,private_key --certificate=db:Open_vSwitch,SSL,certificate --bootstrap-ca-cert=db:Open_vSwitch,SSL,ca_cert --no-chdir --log-file=/var/log/openvswitch/ovsdb-server.log --pidfile=/var/run/openvswitch/ovsdb-server.pid --detach --monitor
```

`/etc/openvswitch/conf.db`是数据库文件存放位置，文件形式存储保证了服务器重启不会影响其配置信息，`ovsdb-server`需要文件才能启动，可以使用`ovsdb-tool create`命令创建并初始化此数据库文件； `--remote=punix:/var/run/openvswitch/db.sock` 实现了一个Unix sockets连接，OVS主进程`ovs-vswitchd`或其它命令工具(ovsdb-client)通过此socket连接管理ovsdb
 `/var/log/openvswitch/ovsdb-server.log`是日志记录。

##### 3.2.3 OpenFlow

OpenFlow是开源的用于管理交换机流表的协议，OpenFlow在OVS中的地位可以参考上面架构图，它是Controller和ovs-vswitched间的通信协议。需要注意的是，OpenFlow是一个独立的完整的流表协议，不依赖于OVS，OVS只是支持OpenFlow协议，有了支持，我们可以使用OpenFlow控制器来管理OVS中的流表，OpenFlow不仅仅支持虚拟交换机，某些硬件交换机也支持OpenFlow协议

OVS常用作SDN交换机(OpenFlow交换机)，其中控制数据转发策略的就是OpenFlow flow。OpenStack Neutron中实现了一个OpenFlow控制器用于向OVS下发OpenFlow flows控制虚拟机间的访问或隔离。本文讨论的默认是作为SDN交换机场景下

OpenFlow flow的流表项存放于用户空间主进程`ovs-vswitchd`中，OVS除了连接OpenFlow控制器获取这种flow，文章后面会提到的命令行工具`ovs-ofctl`工具也可以手动管理OVS中的OpenFlow flow，可以查看`man ovs-ofctl`了解

在OVS中，OpenFlow flow是最重要的一种flow, 然而还有其它几种flows存在，文章下面OVS概念部分会提到。

##### 3.2.4 Controller

Controller指OpenFlow控制器。OpenFlow控制器可以通过OpenFlow协议连接到任何支持OpenFlow的交换机，比如OVS。控制器通过向交换机下发流表规则来控制数据流向。除了可以通过OpenFlow控制器配置OVS中flows，也可以使用OVS提供的`ovs-ofctl`命令通过OpenFlow协议去连接OVS，从而配置flows，命令也能够对OVS的运行状况进行动态监控。

##### 3.2.5 Kernel Datapath

datapath是一个Linux内核模块，它负责执行数据交换。关于datapath，[The Design and Implementation of Open vSwitch](https://link.jianshu.com?t=http%3A%2F%2Fbenpfaff.org%2Fpapers%2Fovs.pdf)中有描述

> <small>The datapath module in the kernel receives the packets first, from a physical NIC or a VM’s virtual NIC. Either ovs-vswitchd has instructed the datapath how to handle packets of this type, or it has not. In the former case, the datapath module simply follows the instructions, called actions, given by ovs-vswitchd, which list physical ports or tunnels on which to transmit the packet. Actions may also specify packet modifications, packet sampling, or instructions to drop the packet. In the other case, where the datapath has not been told what to do with the packet, it delivers it to ovs-vswitchd. In userspace, ovs-vswitchd determines how the packet should be handled, then it passes the packet back to the datapath with the desired handling. Usually, ovs-vswitchd also tells the datapath to cache the actions, for handling similar future packets.</small>

为了说明datapath，来看一张更详细的架构图

![1628772456877](.\1628772456877.png)

用户空间`ovs-vswitchd`和内核模块`datapath`决定了数据包的转发，首先，`datapath`内核模块收到进入数据包(物理网卡或虚拟网卡)，然后查找其缓存(datapath flows)，当有一个匹配的flow时它执行对应的操作，否则`datapath`会把该数据包送入用户空间由`ovs-vswitchd`负责在其OpenFlow flows中查询(图1中的First Packet)，`ovs-vswitchd`查询后把匹配的actions返回给`datapath`并设置一条datapath flows到`datapath`中，这样后续进入的同类型的数据包(图1中的Subsequent Packets)因为缓存匹配会被`datapath`直接处理，不用再次进入用户空间。

`datapath`专注于数据交换，它不需要知道OpenFlow的存在。与OpenFlow打交道的是`ovs-vswitchd`，`ovs-vswitchd`存储所有Flow规则供`datapath`查询或缓存.

虽然有`ovs-dpctl`管理工具的存在，但我们没必要去手动管理`datapath`，这是用户空间`ovs-vswitchd`的工作。

#### 3.3 OVS 在neutron+vxlan模式下涉及组件的概念

###### 1. Bridge

Bridge代表一个以太网交换机(Switch)，一个主机中可以创建一个或者多个Bridge。Bridge的功能是根据一定规则，把从端口收到的数据包转发到另一个或多个端口，上面例子中有三个Bridge，`br-tun`，`br-int`，`br-ext`

###### 2. Port

端口Port与物理交换机的端口概念类似，Port是OVS Bridge上创建的一个虚拟端口，每个Port都隶属于一个Bridge。Port有以下几种类型:

- **Normal**：可以把操作系统中已有的网卡(物理网卡em1/eth0,或虚拟机的虚拟网卡tapxxx)挂载到ovs上，ovs会生成一个同名Port处理这块网卡进出的数据包。此时端口类型为Normal。有一点要注意的是，挂载到OVS上的网卡设备不支持分配IP地址
- **Internal**：Internal类型是OVS内部创建的虚拟网卡接口，每创建一个Port，OVS会自动创建一个同名接口(Interface)挂载到新创建的Port上。当ovs创建一个新网桥时，默认会创建一个与网桥同名的Internal Port。在OVS中，只有”internal”类型的设备才支持配置IP地址信息，
- **Patch**：当主机中有多个ovs网桥时，可以使用Patch Port把两个网桥连起来。Patch Port总是成对出现，分别连接在两个网桥上，从一个Patch Port收到的数据包会被转发到另一个Patch Port，类似于Linux系统中的`veth`。使用Patch连接的两个网桥跟一个网桥没什么区别，OpenStack Neutron中使用到了Patch Port。
- **Tunnel**：OVS中支持添加隧道(Tunnel)端口，常见隧道技术有两种`gre`或`vxlan`。隧道技术是在现有的物理网络之上构建一层虚拟网络，上层应用只与虚拟网络相关，以此实现的虚拟网络比物理网络配置更加灵活，并能够实现跨主机的L2通信以及必要的租户隔离。不同隧道技术其大体思路均是将以太网报文使用隧道协议封装，然后使用底层IP网络转发封装后的数据包，其差异性在于选择和构造隧道的协议不同。Tunnel在OpenStack中用作实现大二层网络以及租户隔离，以应对公有云大规模，多租户的复杂网络环境。

上面Normal和INternal两种Port类型区别在于，Internal类型会自动创建接口(Interface)，而Normal类型是把主机中已有的网卡接口添加到OVS中

###### 3. Interface

Interface是连接到Port的网络接口设备，是OVS与外部交换数据包的组件，在通常情况下，Port和Interface是一对一的关系，只有在配置Port为 bond模式后，Port和Interface是一对多的关系。这个网络接口设备可能是创建`Internal`类型Port时OVS自动生成的虚拟网卡，也可能是系统的物理网卡或虚拟网卡(TUN/TAP)挂载在ovs上。 OVS中只有”Internal”类型的网卡接口才支持配置IP地址。`Interface`是一块网络接口设备，负责接收或发送数据包，Port是OVS网桥上建立的一个虚拟端口，`Interface`挂载在Port上。

#### 3.4 OVS中的各种流(flows)

flows是OVS进行数据转发策略控制的核心数据结构，区别于Linux Bridge是个单纯基于MAC地址学习的二层交换机，flows的存在使OVS作为一款SDN交换机成为云平台网络虚拟机化主要组件。
OVS中有多种flows存在，用于不同目的，但最主要的还是OpenFlow flows这种，文中未明确说明的flows都是指OpenFlow flow。
##### 3.4.1 OpenFlow flows
OpenFlow是开源的用于管理交换机流表的协议，OpenFlow在OVS中的地位可以参考OVS架构的图，它是Controller和ovs-vswitched间的通信协议。需要注意的是，OpenFlow是一个独立的完整的流表协议，不依赖于OVS，OVS只是支持OpenFlow协议，有了支持，我们可以使用OpenFlow控制器来管理OVS中的流表，OpenFlow不仅仅支持虚拟交换机，某些硬件交换机也支持OpenFlow协议

OVS常用作SDN交换机(OpenFlow交换机)，其中控制数据转发策略的就是OpenFlow flow。OpenStack Neutron中实现了一个OpenFlow控制器用于向OVS下发OpenFlow flows控制虚拟机间的访问或隔离。本文讨论的默认是作为SDN交换机场景下

OpenFlow flow的流表项存放于用户空间主进程ovs-vswitchd中，OVS除了连接OpenFlow控制器获取这种flow，文章后面会提到的命令行工具ovs-ofctl工具也可以手动管理OVS中的OpenFlow flow，可以查看man ovs-ofctl了解。

##### 3.4.2 “hidden” flows

OVS在使用OpenFlow flow时，需要与OpenFlow控制器建立TCP连接，若此TCP连接不依赖OVS，即没有OVS依然可以建立连接，此时就是out-of-band control模式，这种模式下不需要”hidden” flows

但是在in-band control模式下，TCP连接的建立依赖OVS控制的网络，但此时OVS依赖OpenFLow控制器下发的flows才能正常工作，没法建立TCP连接也就无法下发flows，这就产生矛盾了，因此需要存在一些”hidden” flows，这些”hidden” flows保证了TCP连接能够正常建立。关于in-band control详细介绍，参考OVS官方文档Design Decisions In Open vSwitch 中In-Band Control部分

“hidden” flows优先级高于OpenFlow flows，它们不需要手动设置。可以使用ovs-appctl查看这些flows，下面命令输出内容包括OpenFlow flows,"hidden" flows

```
ovs-appctl bridge/dump-flows
```

##### 3.4.3 dataath flows

datapath flows是`datapath`内核模块维护的flows，由内核模块维护意味着我们并不需要去修改管理它。与OpenFlow flows不同的是，它不支持优先级，并且只有一个表，这些特点使它非常适合做缓存。与OpenFlow一样的是它支持通配符，也支持指令集(多个action)

datapath flows可以来自用户空间`ovs-vswitchd`缓存，也可以是datapath内核模块进行MAC地址学习到的flows，这取决与OVS是作为SDN交换机，还是像Linux Bridge那样只是一个简单基于MAC地址学习的二层交换机。



#### 3.4 管理flows的命令行工具

#### 3.5 ovs-*工具的使用及区别

第三章参考链接

https://www.jianshu.com/p/9b1fa7b1b705




### 4. Neutron三种网络类型-VxLAN、GRE、 VLAN

Neutron当前支持的二层网络类型有Local、Flat、VLAN、GRE、VXLAN、Geneve 6种，每种类型的网络实现模型都有所不同。

openstack的网络实现方式有flat，vlan，gre，vxlan
*flat* :即所有的设备都连接到同一交换机上，可以互相通信。
*vlan* :由于flat容易产生广播风暴，所以引入vlan，在二层进行vlan划分，隔离网络。
*gre & vxlan* ：由于vlan的个数有限，只能有4094个，对公有云来说不够。所以引入gre，vxlan。
gre和vxlan是三层的隧道技术。通过在三层重新封装数据包，在节点之间创建隧道，通过UDP进行传输。



#### 4.1 qbr、br-int、br-thx、veth pair概念

Neutron的VLAN实现模型，如下：
![img](.\企业微信截图_16284120355076.png)

br-ethx、br-int、qbr-xxx、qbr-yyy都是Bridge，只不过实现方式不同。前两者选择的是OVS（Open vSwitch），后两者选择的是Linux Bridge。

##### 4.1.1 qbr及br-int、qvo、qvb

qbr-xxx、qbr-yyy一般简称qbr。**qbr**这个缩写比较有意思，它是**Quantum Bridge的缩写**，而OpenStack网络组件的前一个商标名就是Quantum，只不过由于版权的原因，才改为Neutron。从这个称呼我们也能看到Neutron里面Quantum的影子。

br-int，表达的是**Integration Bridge（综合网桥）**的含义。至于它到底“综合”了哪些内容，我们这里先不纠结，我们就当它是一个普通的Bridge。

qbr与br-int都是Bridge。**qbr的实现载体是Linux Bridge，br-int的实现载体是OVS（Open vSwitch）**。需要强调的是，并不是绝对地说qbr一定就是Linux Bridge，br-int一定就是OVS，也可以用其他的实现方式来替换它们。只不过这样的实现方式是当前OpenStack解决方案的比较经典的方式而已。

**qbr与br-int之间，通过veth pair连接，VM与qbr之间，通过tap连接。**其实VM与qbr之间只有1个tap，也就是说是1个tap分别挂接在VM和qbr之上。

**qvo、qvb**：在 VM1 中，虚拟机的网卡实际上连接到了物理机的一个 TAP 设备（即 A，常见名称如 tap-XXX）上，A 则进一步通过VETH pair（A-B）连接到网桥 qbr-XXX 的端口 vnet0（端口 B）上，之后再通过 VETH pair（C-D）连到br-int网桥上。一般C的名字格式为 qvb-XXX（neutron veth，Linux Bridge-side），而 D 的名字格式为 qvo-XXX（neutron veth，OVS-side）。注意它们的名称除了前缀外，后面的 id 都是一样的，表示位于同一个虚拟机网络到物理机网络的连接上。

##### 4.1.2 两层bridge的原因

这里面有个问题：为什么需要两层Bridge？VM先接qbr（Linux Bridge），再接br-int（OVS），为什么不是VM直接接入br-int？原因有两点：

1. 如果只有一个qbr，由于qbr仅仅是一个Linux Bridge，它的功能不能满足实际场景的需求。
2. 如果只有一个br-int，由于br-int实际是一个OVS，而OVS比较任性，它到现在竟然还不支持基于iptables规则的安全组功能，而OpenStack偏偏是要基于iptables规则来实现安全组功能。

OpenStack引入qbr其目的主要就是利用iptables来实现security group功能（qbr有时候也被称为安全网桥），而引入br-int，才是真正为了实现一个综合网桥的功能。

##### 4.1.3 br-ethx

**br-ethx也是一个Bridge，也是一个OVS**，它的含义是：**Bridge-Ethernet-External**。顾名思义，br-ethx负责与“外”部通信，这里的“外”部指的是Host外部，但是却又要属于一个Network（这个Network指的是Neutron的概念）的内部，对于本小节而言指的是VLAN内部。这非常关键，后面我们还会涉及“外”部其他的概念。
br-ethx与br-int之间的接口是veth pair。
值得注意的是，**br-ethx上的接口是一个真正的Host的网卡接口**（NIC Interface，Interface in Network Interface Card）。网卡接口是网卡物理口上的一个Interface。

引入qbr只是一个历史原因，现在的实际部署中可以没有。OVS的Stateful openflow规则已经可以支持安全功能。

vxlan、qbr、br-int知识参考：https://bbs.huaweicloud.com/blogs/116044

#### 4.2 nuetron网络实现模型-VLAN

两个Host内的4个VM，分别属于两个VLAN：VM1-1与VM2-1属于VLAN 100，VM1-2与VM2-2属于VLAN 200。br-ethx、br-int、qbr-xxx、qbr-yyy都是Bridge，只不过实现方式不同。前两者选择的是OVS（Open vSwitch），后两者选择的是Linux Bridge。这些Bridge构建了两个VLAN（VLAN ID分别为100、200）。不同的Bridge之间、Bridge与VM之间通过不同的接口进行对接。

![img](.\企业微信截图_16284801373425.png)

##### 4.2.1 VM和VLAN ID

对前面的实现模型的一个更加简化的模型：忽略掉那些各种各样的Bridge，各种各样的tap，veth pair等接口。简单理解，一个Host内有一个Bridge，Bridge连接着虚拟机。

![img](.\企业微信截图_16284805267764.png)

**内部视角**是在Host内部，4个VM的VLAN ID完全不是什么100、200，而是10、20、30、40。

**外部视角**是用户视角，它不关心内部实现细节，它只需要知道创建了两个VLAN网络，VLAN ID分别是100和200，每个VLAN里面有两个VM。

#####  4.2.2 内外VLAN ID的转换过程

（1）出报文VLAN ID转换过程

VLAN类型网络，出报文的内外VLAN ID转换过程如图所示。

![img](.\企业微信截图_16284809136334.png)

![1628492796648](.\1628492796648.png)

上图提到了VID，这是一种抽象的称呼，它的含义随着网络类型的不同而不同：对于VLAN网络而言，VID指的就是VLAN ID；对于VXLAN网络而言，VID指的就是VNI；对于GRE网络，VID指的就是GRE Key。

图3-8中，我们以VM1-1为例，讲述内外VID的转换过程。报文从VM1-1发出，从br-ethx离开Host，这一路的VID转换如下：

①报文从VM1-1的A端口发出，是Untag报文；

②报文从B端口进入qbr-xxx，再从C端口离开qbr-xxx，也是Untag报文（A、B端口其实是同一个tap设备，以下不再重复这个说明）；

③报文从D端口进入br-int，在D端口，报文被打上标签，VLAN ID = 10；

④报文从E端口离开br-int，此时报文VID = 10；

⑤报文从F端口进入br-ethx，在F端口，报文的标签被转变为VLAN ID = 100；

⑥报文从G端口离开Host，VLAN ID = 100。

可以看到，报文在br-int的D端口被打上内部VLAN标签，变成了Tag报文，在br-ethx

的F端口做了内外VID的转化。图3-8中，在VM1-1上标识了VLAN 10，其实表达的是它在Host内的br-int上所对应的接口VLAN ID = 10，并不是说从VM1-1发出的报文的VLAN ID = 10。

（2）入报文VLAN ID转换过程

VLAN类型网络，入报文的内外VLAN ID转换过程，如图所示。

![1628492846735](.\1628492846735.png)

图中，我们以VM1-1为例，讲述内外VID的转换过程。报文从Host进入，从qbr-xxx进入VM1-1，这一路的VID转换如下：

①报文从Host进入到br-ethx，是Tag报文，VID = 100；

②报文从br-ethx离开，在离开的端口F，报文VID转变为10；

③报文从E端口进入br-int，此时报文VID = 10；

④报文进入br-int后，从D端口被转发出去，在离开D时，被剥去Tag，变成Untag报文；

⑤报文从C端口进入qbr-xxx，然后从B端口离开，再从A端口进入VM1-1，这一路都是Untag报文。

可以看到，报文在br-ethx的F端口做了内外VID的转化，在br-int的D端口被剥去VLAN标签，变成了Untag报文。

#### 4.3 nuetron网络实现模型-VxLAN

 VXLAN的实现模型与VLAN的实现模型非常相像，如下图

![img](.\7da0e98734369fb6090096f3a5a4eca1.png)

从表面来看，VXLAN与VLAN的实现模型相比，仅仅一个差别：VLAN中对应的br-ethx，而VXLAN中对应的是br-tun（br-tun是一个混合单词的缩写：Bridge-Tunnel。此时的Tunnel是VXLAN Tunnel。）

其实，br-ethx是一个OVS，br-tun也是一个OVS。所有说，两者的差别不是实现组件的差别，而是组件所执行功能的差别。**br-ethx所执行的一个普通二层交换机的功能**，**br-tun所执行的是VXLAN中VTEP的功能**，上图中两个tun所对应的接口IP分时标识为10.0.100.88和10.0.100.77，这两个IP就是VXLAN的隧道终结点IP。

VXLAN与VLAN一样也存在内外VID的转换。通过VXLAN，就可以明白Neutron为什么要做内外VID的转换。

如下图所示

![img](.\9e5ebc161c0159e1d7c423fdd4b6acb2.png)

该图把br-tun一分为二，设想为两部分：上层是VTEP，对VXLAN隧道进行了终结；下层是一个普通的VLAN Bridge。所以，对于Host来说，它有两层网络，虚线以上是VXLAN网络，虚线以下是VLAN网络。如此一来，VXLAN内外VID的转换则变成了不得不做得工作，因为它不仅仅是表面上看起的那样是VID数值的转变，而且背后蕴含着网络类型的转变。

VLAN类型的网络并不存在VXLAN这样的问题。当Host遇到VLAN时，它并不会变成两重网络，可为什么要做内外VID的转换呢？这主要是为了避免内部VLAN ID的冲突。**内部VLAN ID是体现在br-int上的**，而一个Host内装有1个br-int,也就是说**VLAN和VXLAN是共用一个br-int**。假如VLAN网络不做内外VID的转换，则很可能引发br-int上的内部VLAN ID冲突，如下表。

![img](.\f486ad06947ed55be6761440dff9495e.png)

VXLAN做内外VID转换时，并不知道VLAN的外部VID是什么，所以它就根据自己的算法将内部VID转换为100，结果很不辛，与VLAN网络的外部VID相等。因为VLAN的内部VID没有做转换，仍然等于外部VID，所以两者在br-int上产生了冲突。正是这个原因，所以VLAN类型的网络，也要做内外VID的转换，而且所有的网络类型都需要做VID的转换。这样的话Neutron就能统一掌控，从而避免内部VID的冲突。

VXLAN的转换过程如下：

1. 出报文的VID转换过程：

![img](.\1b7258e0e0b4758a4a3f7bdfaa85778e.png)

我们以VM1-3为例，讲述内外VID的转换过程（在VxLAN里VID表示VNI）。报文从VM1-3发出，从br-tun离开Host，这一路的VID转换如下：

①报文从VM1-3的A端口发出，是Untag报文；

②报文从B端口进入qbr-xxx，再从C端口离开qbr-xxx，也是Untag报文；

③报文从D端口进入br-int，在D端口，报文被打上标签，VLAN ID = 50；

④报文从E端口离开br-int，此时报文VID = 50；

⑤报文从F端口进入br-tun，此时报文VID = 50；

⑥报文从G端口离开Host，在G端口，报文被从VLAN封装为VXLAN，并且VNI = 100。

可以看到，报文在br-int的D端口被打上内部VLAN标签，变成了Tag报文，在br-tun的G端口做了两件事情：报文格式从VLAN封装为VXLAN，VNI赋值为100。

2. 入报文VID转换过程如下：

![img](.\1702825e69a22413e8c4af509aa38734.png)

以VM1-3为例，讲述内外VID的转换过程。报文从Host进入，从qbr-xxx进入VM1-3，这一路的VID转换如下：

①报文来到Host进到br-tun，是VXLAN

报文，VNI = 100；

②报文在br-tun的G端口，被转换为VLAN报文，VLAN ID = 50；

③报文从br-tun离开，一直到进入br-int，都是VLAN报文，VLAN ID = 50；

④报文从br-int D端口离开br-int，报文被剥去Tag，变成Untag报文；

⑤报文从C端口进入qbr-xxx，然后再从B端口离开，再从A端口进入VM1-3，这一路都是Untag报文。

可以看到，报文在br-tun的G端口做了两件事情：报文格式从VXLAN拆封为VLAN，VLAN ID赋值为50，在br-int的D端口被剥去VLAN标签，变成了Untag报文。

#### 4.4 nuetron网络实现模型-GRE

GRE的实现模型与VXLAN的实现模型一模一样。所不同的是，VXLAN的br-tun构建的是VXLAN Tunnel，而GRE的br-tun构建的是GRE Tunnel。

![img](.\企业微信截图_16284818482246.png)



GRE网络，虽然不像VLAN、VXLAN网络那样对于租户有一个可见的网络ID（VLAN ID/VNI），但是它内部的实现仍然是有一个Tunnel ID，这样就一样存在这样的转换：内部VLAN ID与Tunnel ID之间的转换。



#### 4.5 用户网络和本地网路

（1）用户网络层

**用户网络层（User Network）**，指的是Open-Stack的用户创建的网络，也就是前文一直**说的外部网络**，这个外部网络是相对于Host内部网络而言的。用户网络层对应的Bridge是br-ethx（对应Flat、VLAN等非隧道型二层网络）或者br-tun（对应VXLAN、GRE等隧道型二层网络），其实现载体一般来说是OVS。用户网络层的功能是将用户网络与本地网络（Host内部的本地网络）进行相互转换，比如我们前面介绍的：内外VID转换，VXLAN封装与解封装，等等。为“用户网络层”是对本地网络层的一个屏蔽，即不管用户网络采用什么技术（比如VXLAN，GRE等），**本地网络永远感知的仅仅是一个技术：VLAN。**

（2）本地网络层

**本地网络指的是Host内部的本地网络。**由于用户网络层（Local Network）对这一层的屏蔽，本地网络层只需要感知一种技术：VLAN。本地网络层再分为两层。根据前文介绍，**qbr**的实现载体是Linux Bridge，它仅仅是负责安全，所以**称之为安全层**。**br-int**的实现载体一般是OVS，它负责内部交换，所以**称之为Bridge层**。

Bridge层是对VM层的一个屏蔽。从VM发出的Untag报文，被Bridge层转换为Tag报文转发到br-ethx/br-tun；从br-ethx/br-tun转发到br-int的Tag报文，被br-int剥去Tag，变成Untag报文，然后再转发给VM。

位于同一个Host的本地网络中的不同VM之间的通信，它们经过本地网络层（即经过br-int）即可完成，不需要再往外走到用户网络层

推荐网址：https://hardocs.com/d/openstack-neutron/vlan_mode/



### 5. neutron配置文件

#### 5.1 neutron+vxlan+linuxbridge模式

##### 5.1.1控制节点/etc/neutron配置

###### 5.1.1.1 dhcp_agent.ini

```
[DEFAULT]
interface_driver = linuxbridge
dhcp_driver = neutron.agent.linux.dhcp.Dnsmasq
enable_isolated_metadata = true

```

###### 5.1.1.2 l3_agent.ini

```
[DEFAULT]
interface_driver = linuxbridge
external_network_bridge = 
[AGENT]
extensions = fwaas_v2,vpnaas
[vpnagent]
vpn_device_driver = neutron_vpnaas.services.vpn.device_drivers.libreswan_ipsec.LibreSwanDriver

```

###### 5.1.1.3 metadata_agent.ini

```
[DEFAULT]
nova_metadata_host = controller
metadata_proxy_shared_secret = metadata_secret
[cache]
```

###### 5.1.1.4 neutron.conf

```
[DEFAULT]
core_plugin = ml2
service_plugins = router
allow_overlapping_ips = true
transport_url = rabbit://openstack:openstack@controller
auth_strategy = keystone
notify_nova_on_port_status_changes = true
notify_nova_on_port_data_changes = true
[cors]
[database]
connection = mysql+pymysql://neutron:comleader@123@controller/neutron
[keystone_authtoken]
www_authenticate_uri = http://controller:5000
auth_url = http://controller:5000
memcached_servers =controller:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = neutron
password = comleader@123
[oslo_concurrency]
lock_path = /var/lib/neutron/tmp
[oslo_messaging_amqp]
[oslo_messaging_kafka]
[oslo_messaging_notifications]
[oslo_messaging_rabbit]
[oslo_middleware]
[oslo_policy]
[privsep]
[ssl]
[nova]
auth_url = http://controller:5000
auth_type = password
project_domain_name = default
user_domain_name = default
region_name = RegionOne
project_name = service
username = nova
password = comleader@123

```

###### 5.1.1.5 plugin.ini

```
[DEFAULT]
[ml2]
type_drivers = flat,vlan,vxlan
tenant_network_types = vxlan
mechanism_drivers = linuxbridge,l2population
extension_drivers = port_security

[ml2_type_flat]
flat_networks = provider

[ml2_type_vxlan]
vni_ranges = 1:1000

[securitygroup]
enable_ipset = true
```

###### 5.1.1.6 ml2_conf.ini

/etc/neutron/plugins/ml2

```
[DEFAULT]
[ml2]
type_drivers = flat,vlan,vxlan
tenant_network_types = vxlan
mechanism_drivers = linuxbridge,l2population
extension_drivers = port_security

[ml2_type_flat]
flat_networks = provider

[ml2_type_vxlan]
vni_ranges = 1:1000

[securitygroup]
enable_ipset = true

```



###### 5.1.1.7 linuxbridge_agent.ini

/etc/neutron/plugins/ml2

```
[DEFAULT]
[linux_bridge]
#physical_interface_mappings = provider:eth0
physical_interface_mappings = provider:ens32

[vxlan]
enable_vxlan = true
local_ip = 192.168.204.173
l2_population = true

[securitygroup]
enable_security_group = true
firewall_driver = neutron.agent.linux.iptables_firewall.IptablesFirewallDriver
```



##### 5.1.2 计算节点/etc/neutron配置

###### 5.1.2.1 neutron.conf配置

```
[DEFAULT]
transport_url = rabbit://openstack:openstack@controller
auth_strategy = keystone
[cors]
[database]
[keystone_authtoken]
www_authenticate_uri = http://controller:5000
auth_url = http://controller:5000
memcached_servers =controller:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = neutron
password = comleader@123
[oslo_concurrency]
lock_path = /var/lib/neutron/tmp
[oslo_messaging_amqp]
[oslo_messaging_kafka]
[oslo_messaging_notifications]
[oslo_messaging_rabbit]
[oslo_middleware]
[oslo_policy]
[privsep]
[ssl]


```

###### 5.1.2.2  linuxbridge_agent.ini配置

/etc/neutron/plugins/ml2/linuxbridge_agent.ini

```
[DEFAULT]
[linux_bridge]
physical_interface_mappings = provider:ens32

[vxlan]
enable_vxlan = true
local_ip = 192.168.204.174
l2_population = true

[securitygroup]
enable_security_group = true
firewall_driver = neutron.agent.linux.iptables_firewall.IptablesFirewallDriver

```





### 6. neutron服务

#### 6.1 neutron架构

![img](.\企业微信截图_162945139528.png)

- Neutron 通过 plugin 和 agent 提供的网络服务。

- plugin 位于 Neutron server，包括 core plugin 和 service plugin。

- agent 位于各个节点，负责实现网络服务。

- core plugin 提供 L2 功能，ML2 是推荐的 plugin。

- 使用最广泛的 L2 agent 是 linux bridage 和 open vswitch。

- service plugin 和 agent 提供扩展功能，包括 dhcp, routing, load balance, firewall, vpn 等。
  



#### 6.2 服务简介

##### 6.2.1 neutron-server

可以理解为类似于nova-api那样的一个组件，一个专门用来接收neutron REST API调用的服务器。负责将不同的rest api发送到不同的neutron-plugin。接受和路由API请求到网络plug-in。一般部署在控制节点（controller），负责通过Neutron-server响应的API请求；

##### 6.2.2 neutron-plugin

可以理解为不同网络功能（例如创建端口（ports）、网络（Networks）、子网（Subnets）等）实现的入口，现在大部分都是软件定义网络，各个厂商都开发自己的plugin(插件)。neutron-plugin接收netron-server发过来的rest api，向neutron database完成一些信息注册（比如用户要建端口）。然后将具体要执行的业务操作和参数通知给自身对应的neutron-agent。Openstack的plugins一般支持Open vSwitch、Linux Bridging、思科物理/虚拟交换机等等。一般Core plugin 和service plugin已经集成到neutron-server中，不需要运行独立的plugin服务。

- plugin 解决的是 What 的问题，即网络要配置成什么样子？而至于如何配置 How 的工作则交由 agent 完成。
- plugin，agent 和 network provider 是配套使用的，如果network provider用的linux bridge则使用对应的plugin和agent，若是使用的OVS则使用OVS的plugin和agent；
- plugin 的一个主要的职责是在数据库中维护 Neutron 网络的状态信息。通过ML2（Modular Layer 2）plugin，各种 network provider 无需开发自己的 plugin，只需要针对 ML2 开发相应的 driver 就可以了；
- plugin 按照功能分为两类： core plugin 和 service plugin。core plugin 维护 Neutron 的 netowrk, subnet 和 port 相关资源的信息，与 core plugin 对应的 agent 包括 linux bridge, OVS 等； service plugin 提供 routing, firewall, load balance 等服务，也有相应的 agent。
        

##### 6.2.3 neutron-agent

常见的agent包括L3、DHCP、plugin agent；一般网络节点需要部署Core Plugin的代理和service Plugin的代理，计算节点也需要部署Core Plugin的代理，通过该代理才能建立二层连接。

- L3 agent (neutron-l3-agent)	提供L3/NAT转发，使租户内的虚机实例被外部网络访问

- dhcp agent (neutron-dhcp-agent)	为租户网络提供dhcp功能

- metering agent (neutron-metering-agent)	提供L3数据流量的监控、计算

- metadata agent	是提供一个机制给用户，可以设定每一个instance 的参数

- OpenvSwitch agent	使用Open vSwitch来实现VLAN， GRE，VxLAN来实现网络的隔离，还包括了网络流量的转发控制

- plug-in agent ( neutron-*-agent )	在每个hypervisor上运行以执行本地vSwitch配置。 这个插件是否运行取决于使用的插件，有些插件不需要代理。
  neutron-lbaas-agent	提供LB的服务
  neutron-firewall-agent	提供防火墙服务

##### 6.2.4  ML2 Core Plugin
使用ML2 Core Plugin的需求是：（1）传统Core Plugin无法同时提供多种network provider；（2）开发工作量大。

采用 ML2 plugin 后，可以在不同节点上分别部署 linux bridge agent, open vswitch agent, hyper-v agent 或其他第三方 agent。ML2 不但支持异构部署方案，同时能够与现有的 agent 无缝集成：以前用的 agent 不需要变，只需要将 Neutron server 上的传统 core plugin 替换为 ML2。

ML2 对二层网络进行抽象和建模，引入了 type driver 和 mechansim driver。type driver 负责维护网络类型的状态，执行验证，创建网络等，支持vlan、vxlan、gre、flat、local网络；mechanism driver 负责获取由 type driver 维护的网络状态，并确保在相应的网络设备（物理或虚拟）上正确实现这些状态。

mechanism driver 有三种类型：（1）Agent-based：包括 linux bridge, open vswitch 等。（2）Controller-based：包括 OpenDaylight, VMWare NSX 等。（3）基于物理交换机；此外，涉及L2 population driver，其作用是优化和限制 overlay 网络中的广播流量。
![img](.\企业微信截图_16294512209414.png)





#### 6.1 neutron+vxlan+linuxbridge模式

在配置正确的情况下，确定服务启动正常，各个服务日志正常

##### 6.1.1 控制节点部署服务

- neutron-dhcp-agent.service
- neutron-l3-agent.service
- neutron-metadata-agent.service
- neutron-server.service

##### 6.1.2 计算节点部署服务

- neutron-linuxbridge-agent.service



