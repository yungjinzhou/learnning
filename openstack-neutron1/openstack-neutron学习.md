## openstack-neutron学习

### 1. 二层与三层
#### 1.1 OSI七层模型

一般情况下，OSI模型分为七层：应用层，表示层，会话层，传输层，网络层，数据链路层和物理层。

#### 1.2 二层、三层交换机

二层交换机工作于OSI模型的二层(数据链路层)，故而称为二层交换机，主要功能包括物理编址、错误校验、帧序列以及流控。而三层交换机位于三层（网络层），是一个具有三层交换功能的设备，即带有三层路由功能的二层交换机，但它是二者的有机结合，并不是简单地把路由器设备的硬件及软件叠加在局域网交换机上。

#### 1.3 二层、三层网络

二层网络仅仅通过MAC寻址即可实现通讯，但仅仅是同一个冲突域内；三层网络则需要通过IP路由实现跨网段的通讯，可以跨多个冲突域。





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

![img](E:\code\learnning\openstack-neutron1\企业微信截图_16283899163640.png)



![img](E:\code\learnning\openstack-neutron1\企业微信截图_16283900005302.png)

#### 2.3 Namespace

Namespace类似传统网络里的VRF，与VRF不同的是：VRF做的是网络层三层隔离。而namespace隔离的更彻底，它做的是整个协议栈的隔离，隔离的资源包括：UTS(UnixTimesharing  System的简称，包含内存名称、版本、 底层体系结构等信息)、IPS(所有与进程间通信（IPC）有关的信息)、mnt(当前装载的文件系统)、PID(有关进程ID的信息)、user(资源配额的信息)、net(网络信息)。

从网络角度看一个namespace提供了一份独立的网络协议栈（网络设备接口、IPv4/v6、IP路由、防火墙规则、sockets等），**而一个设备（Linux Device）只能位于一个namespace中，不同namespace中的设备可以利用vethpair进行桥接。**

#### 2.4 veth pair

veth pair不是一个设备，而是一对设备，以连接两个虚拟以太端口。操作vethpair，需要跟namespace一起配合，不然就没有意义。(<font color=red>**veth pair连接的是二层同网段的两个设备，tun是隧道，可以连接不同网段的设备**</font>)

![img](E:\code\learnning\openstack-neutron1\企业微信截图_1628390528266.png)

#### 2.5 Bridge

在Linux的语境里，Bridge（网桥）与Switch（交换机）是一个概念。因为一对veth pair只能连接两台device，因此如果需要多台设备互联则需要bridge。

如图：4个namespace，每个namespace都有一个tap，每个tap与网桥vb1的tap组成一对veth pair，这样，这4个namespace就可以**二层互通**了。

![img](E:\code\learnning\openstack-neutron1\企业微信截图_16283907317141.png)

#### 2.6 tun

tun是一个网络层(IP)的点对点设备，它启用了IP层隧道功能。Linux原生支持的三层隧道。支持隧道情况：ipip(ipv4 in ipv4)、gre(ipv4/ipv6 over ipv4)、sit(ipv6 over ipv4)、isatap(ipv6/ipv4隧道)、vti(ipsec接口)。
学过传统网络GRE隧道的人更容易理解，如图：
NS1的tun1的ip 10.10.10.1与NS2的tun2的ip 10.10.20.2建立tun
NS1的tun的ip是10.10.10.1，隧道的外层源ip是192.168.1.1，目的ip是192.168.2.1，是不是跟GRE很像。

![img](E:\code\learnning\openstack-neutron1\企业微信截图_16283912007141.png)

#### 2.7 Router

Linux创建Router并没有像创建虚拟Bridge那样，有一个直接的命令brctl，而且它间接的命令也没有，不能创建虚拟路由器……因为它就是路由器（Router) !
如图：我们需要在router(也就是我们的操作系统linux上增加去往各NS的路由)。

![img](E:\code\learnning\openstack-neutron1\企业微信截图_16283915711050.png)

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

![img](E:\code\learnning\openstack-neutron1\企业微信截图_16283916492793.png)

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







### 4. Neutron三种网络类型-VxLAN、GRE、 VLAN

Neutron当前支持的二层网络类型有Local、Flat、VLAN、GRE、VXLAN、Geneve 6种，每种类型的网络实现模型都有所不同。

#### 4.1 qbr、br-int、br-thx、veth pair概念

Neutron的VLAN实现模型，如下：
![img](E:\code\learnning\openstack-neutron1\企业微信截图_16284120355076.png)

br-ethx、br-int、qbr-xxx、qbr-yyy都是Bridge，只不过实现方式不同。前两者选择的是OVS（Open vSwitch），后两者选择的是Linux Bridge。

##### 4.1.1 qbr及br-int

qbr-xxx、qbr-yyy一般简称qbr。**qbr**这个缩写比较有意思，它是**Quantum Bridge的缩写**，而OpenStack网络组件的前一个商标名就是Quantum，只不过由于版权的原因，才改为Neutron。从这个称呼我们也能看到Neutron里面Quantum的影子。

br-int，表达的是**Integration Bridge（综合网桥）**的含义。至于它到底“综合”了哪些内容，我们这里先不纠结，我们就当它是一个普通的Bridge。

qbr与br-int都是Bridge。**qbr的实现载体是Linux Bridge，br-int的实现载体是OVS（Open vSwitch）**。需要强调的是，并不是绝对地说qbr一定就是Linux Bridge，br-int一定就是OVS，也可以用其他的实现方式来替换它们。只不过这样的实现方式是当前OpenStack解决方案的比较经典的方式而已。

**qbr与br-int之间，通过veth pair连接，VM与qbr之间，通过tap连接。**其实VM与qbr之间只有1个tap，也就是说是1个tap分别挂接在VM和qbr之上。

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

![img](E:\code\learnning\openstack-neutron1\企业微信截图_16284801373425.png)

##### 4.2.1 VM和VLAN ID

对前面的实现模型的一个更加简化的模型：忽略掉那些各种各样的Bridge，各种各样的tap，veth pair等接口。简单理解，一个Host内有一个Bridge，Bridge连接着虚拟机。

![img](E:\code\learnning\openstack-neutron1\企业微信截图_16284805267764.png)

**内部视角**是在Host内部，4个VM的VLAN ID完全不是什么100、200，而是10、20、30、40。

**外部视角**是用户视角，它不关心内部实现细节，它只需要知道创建了两个VLAN网络，VLAN ID分别是100和200，每个VLAN里面有两个VM。

#####  4.2.2 内外VLAN ID的转换过程

（1）出报文VLAN ID转换过程

VLAN类型网络，出报文的内外VLAN ID转换过程如图所示。

![img](E:\code\learnning\openstack-neutron1\企业微信截图_16284809136334.png)

![1628492796648](E:\code\learnning\openstack-neutron1\1628492796648.png)

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

![1628492846735](E:\code\learnning\openstack-neutron1\1628492846735.png)

图中，我们以VM1-1为例，讲述内外VID的转换过程。报文从Host进入，从qbr-xxx进入VM1-1，这一路的VID转换如下：

①报文从Host进入到br-ethx，是Tag报文，VID = 100；

②报文从br-ethx离开，在离开的端口F，报文VID转变为10；

③报文从E端口进入br-int，此时报文VID = 10；

④报文进入br-int后，从D端口被转发出去，在离开D时，被剥去Tag，变成Untag报文；

⑤报文从C端口进入qbr-xxx，然后从B端口离开，再从A端口进入VM1-1，这一路都是Untag报文。

可以看到，报文在br-ethx的F端口做了内外VID的转化，在br-int的D端口被剥去VLAN标签，变成了Untag报文。

#### 4.3 nuetron网络实现模型-VxLAN

 VXLAN的实现模型与VLAN的实现模型非常相像，如下图

![img](E:\code\learnning\openstack-neutron1\7da0e98734369fb6090096f3a5a4eca1.png)

从表面来看，VXLAN与VLAN的实现模型相比，仅仅一个差别：VLAN中对应的br-ethx，而VXLAN中对应的是br-tun（br-tun是一个混合单词的缩写：Bridge-Tunnel。此时的Tunnel是VXLAN Tunnel。）

其实，br-ethx是一个OVS，br-tun也是一个OVS。所有说，两者的差别不是实现组件的差别，而是组件所执行功能的差别。**br-ethx所执行的一个普通二层交换机的功能**，**br-tun所执行的是VXLAN中VTEP的功能**，上图中两个tun所对应的接口IP分时标识为10.0.100.88和10.0.100.77，这两个IP就是VXLAN的隧道终结点IP。

VXLAN与VLAN一样也存在内外VID的转换。通过VXLAN，就可以明白Neutron为什么要做内外VID的转换。

如下图所示

![img](E:\code\learnning\openstack-neutron1\9e5ebc161c0159e1d7c423fdd4b6acb2.png)

该图把br-tun一分为二，设想为两部分：上层是VTEP，对VXLAN隧道进行了终结；下层是一个普通的VLAN Bridge。所以，对于Host来说，它有两层网络，虚线以上是VXLAN网络，虚线以下是VLAN网络。如此一来，VXLAN内外VID的转换则变成了不得不做得工作，因为它不仅仅是表面上看起的那样是VID数值的转变，而且背后蕴含着网络类型的转变。

VLAN类型的网络并不存在VXLAN这样的问题。当Host遇到VLAN时，它并不会变成两重网络，可为什么要做内外VID的转换呢？这主要是为了避免内部VLAN ID的冲突。**内部VLAN ID是体现在br-int上的**，而一个Host内装有1个br-int,也就是说**VLAN和VXLAN是共用一个br-int**。假如VLAN网络不做内外VID的转换，则很可能引发br-int上的内部VLAN ID冲突，如下表。

![img](E:\code\learnning\openstack-neutron1\f486ad06947ed55be6761440dff9495e.png)

VXLAN做内外VID转换时，并不知道VLAN的外部VID是什么，所以它就根据自己的算法将内部VID转换为100，结果很不辛，与VLAN网络的外部VID相等。因为VLAN的内部VID没有做转换，仍然等于外部VID，所以两者在br-int上产生了冲突。正是这个原因，所以VLAN类型的网络，也要做内外VID的转换，而且所有的网络类型都需要做VID的转换。这样的话Neutron就能统一掌控，从而避免内部VID的冲突。

VXLAN的转换过程如下：

1. 出报文的VID转换过程：

![img](E:\code\learnning\openstack-neutron1\1b7258e0e0b4758a4a3f7bdfaa85778e.png)

我们以VM1-3为例，讲述内外VID的转换过程（在VxLAN里VID表示VNI）。报文从VM1-3发出，从br-tun离开Host，这一路的VID转换如下：

①报文从VM1-3的A端口发出，是Untag报文；

②报文从B端口进入qbr-xxx，再从C端口离开qbr-xxx，也是Untag报文；

③报文从D端口进入br-int，在D端口，报文被打上标签，VLAN ID = 50；

④报文从E端口离开br-int，此时报文VID = 50；

⑤报文从F端口进入br-tun，此时报文VID = 50；

⑥报文从G端口离开Host，在G端口，报文被从VLAN封装为VXLAN，并且VNI = 100。

可以看到，报文在br-int的D端口被打上内部VLAN标签，变成了Tag报文，在br-tun的G端口做了两件事情：报文格式从VLAN封装为VXLAN，VNI赋值为100。

2. 入报文VID转换过程如下：

![img](E:\code\learnning\openstack-neutron1\1702825e69a22413e8c4af509aa38734.png)

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

![img](E:\code\learnning\openstack-neutron1\企业微信截图_16284818482246.png)



GRE网络，虽然不像VLAN、VXLAN网络那样对于租户有一个可见的网络ID（VLAN ID/VNI），但是它内部的实现仍然是有一个Tunnel ID，这样就一样存在这样的转换：内部VLAN ID与Tunnel ID之间的转换。



#### 4.5 用户网络和本地网路

（1）用户网络层

**用户网络层（User Network）**，指的是Open-Stack的用户创建的网络，也就是前文一直**说的外部网络**，这个外部网络是相对于Host内部网络而言的。用户网络层对应的Bridge是br-ethx（对应Flat、VLAN等非隧道型二层网络）或者br-tun（对应VXLAN、GRE等隧道型二层网络），其实现载体一般来说是OVS。用户网络层的功能是将用户网络与本地网络（Host内部的本地网络）进行相互转换，比如我们前面介绍的：内外VID转换，VXLAN封装与解封装，等等。为“用户网络层”是对本地网络层的一个屏蔽，即不管用户网络采用什么技术（比如VXLAN，GRE等），**本地网络永远感知的仅仅是一个技术：VLAN。**

（2）本地网络层

**本地网络指的是Host内部的本地网络。**由于用户网络层（Local Network）对这一层的屏蔽，本地网络层只需要感知一种技术：VLAN。本地网络层再分为两层。根据前文介绍，**qbr**的实现载体是Linux Bridge，它仅仅是负责安全，所以**称之为安全层**。**br-int**的实现载体一般是OVS，它负责内部交换，所以**称之为Bridge层**。

Bridge层是对VM层的一个屏蔽。从VM发出的Untag报文，被Bridge层转换为Tag报文转发到br-ethx/br-tun；从br-ethx/br-tun转发到br-int的Tag报文，被br-int剥去Tag，变成Untag报文，然后再转发给VM。

位于同一个Host的本地网络中的不同VM之间的通信，它们经过本地网络层（即经过br-int）即可完成，不需要再往外走到用户网络层















