## 交换机配置/网卡配置



### 硬件连接

需要串口线

USB接口连接电脑，串口接口连接交换机的console接口

### 软件连接

选择xshell（或者），新建连接

#### 选择串口协议（SERIAL）

![img](.\企业微信截图_16359423523155.png)

#### **配置serial**

![img](.\企业微信截图_16359424763708.png)



#### 登录

（重置密码方法）

连着串口线重新开机，开机时候会提示Ctrl+B 或者 Ctrl+E重置密码



### 常用命令集

#### 用户视图模式下（查询命令）

```
<Quidway>display current-configuration //显示现在交换机正在运行的配置明细
<Quidway>display device //显示S9303各设备状态
<Quidway>display interface ？ //显示单个端口状态，用?可以查看后边跟的选项
<Quidway>display version //查看交换机固件版本信息
<Quidway>display vlan ？ // 查看vlan的配置信息
```

查看所有端口的当前配置信息

```
display-current
display current(不同型号命令不同)
```

#### 进入系统视图(从用户视图)

```
system-view
```

#### 创建vlan

```
vlan 10   # （进入系统视图后）创建id为10的vlan
commit   # (有的交换机执行vlan 10后没有提示，需要commit才会生效)
quit   # 退出vlan配置视图
```

#### 查看vlan信息

```
display vlan(查看所有vlan信息)
display vlan vid(查看具体的vlan配置)
```



#### 端口操作

##### 进入端口视图

```
# 数字依次代表插槽号/子板号/端口号
interface GigabitEthernet2/0/1  # （千兆交换机操作命令）
interface XGigabitEthernet0/0/1  # （万兆交换机操作命令）
interface XGE0/0/9   #（万兆交换机操作命令）
interface 10GE1/0/47    # （万兆交换机操作命令）
```

##### 配置端口模式

```
# 在进入对应端口配置视图后操作
port link-type access 
port link-type trunk
port link-type 
```

##### 将端口加入vlan

```
port default vlan 100   # 在进入对应端口配置视图后操作
port GigabitEthernet 1/0/0 to 1/0/29  # 将多个端口加入到vlan中（在vlan配置视图中操作）
```

##### 配置trunk端口

```
# 进入端口配置视图后
port trunk allow-pass vlan 100 10  # 允许id为100、10的vlan通过
```



#### 交换机配置ip地址(未测试)

```
[Quidway] interface Vlanif100 // 进入vlan100接口视图与vlan 100命令进入的地方不同
[Quidway-Vlanif100] ip address 119.167.200.90 255.255.255.252 // 定义vlan100管理IP三层 交换网关路由
[Quidway-Vlanif100] quit 返回视图
[Quidway] interface Vlanif10 // 进入vlan10接口视图与vlan 10命令进入的地方不同
[Quidway-Vlanif10] ip address 119.167.206.129 255.255.255.128 // 定义vlan10管理IP三层交换网关路由
[Quidway-Vlanif10] quit
```

#### 配置默认网关(未测试)

```
[Quidway]ip route-static 0.0.0.0 0.0.0.0 119.167.200.89 //配置默认网关。
```

#### 交换机保存设置和重置命令

```
# 用户视图下操作
<Quidway>save //保存配置信息
<Quidway>reset saved-configuration /重置交换机的配置
<Quidway>reboot //重新启动交换机
```



#### 恢复交换机出厂设置

```
# 用户视图下操作
<Quidway>reset saved-configuration /重置交换机的配置
```







## 交换机基础知识

### 以太网的3种链接类型

以太网端口有 3种链路类型：access、trunk、hybird

- Access类型端口：只能属于1个VLAN，一般用于连接计算机端口，且该端口不打tag；
- Trunk类型端口：可以允许多个VLAN通过,可以接收和发送多个VLAN 报文, 一般用于交换机与交换机相关的接口，且该端口都是打tag的。
- Hybrid类型端口：可以允许多个VLAN通过，可以接收和发送多个VLAN 报文，可以用于交换机的间连接也可以用于连接用户计算机，该端口在vlan中是否打tag由用户根据具体情况而定。

首先，将交换机的类型进行划分，交换机分为低端(SOHO级)和高端(企业级)。其两者的重要区别就是低端的交换机每一个物理端口为一个逻辑端口，而高端交换机则是将多个物理端口捆绑成一个逻辑端口再进行的配置的。

cisco网络中，交换机在局域网中最终稳定状态的接口类型主要有四种：access/trunk/ multi/ dot1q-tunnel。

1、access: 主要用来接入终端设备，如PC机、服务器、打印服务器等。

2、trunk: 主要用在连接其它交换机，以便在线路上承载多个vlan。

3、multi: 在一个线路中承载多个vlan，但不像trunk,它不对承载的数据打标签。主要用于接入支持多vlan的服务器或者一些网络分析设备。现在基本不使用此类接口，在cisco的网络设备中，也基本不支持此类接口了。

4、dot1q-tunnel: 用在Q-in-Q隧道配置中。

### **链路类型**

vlan的链路类型可以分为接入链路和干道链路。

1. **接入链路**（access link）指的交换机到用户设备的链路，即是接入到户，可以理解为由交换机向用户的链路。由于大多数电脑不能发送带vlan tag的帧，所以这段链路可以理解为不带vlan tag的链路。

2. **干道链路**（trunk link）指的交换机到上层设备如路由器的链路，可以理解为向广域网走的链路。这段链路由于要靠vlan来区分用户或者服务，所以一般都带有vlan tag。

### **端口类型**

端口类型在以前主要分为两种，基本上用的也是access和trunk这两种端口。

1. **access端口**：它是交换机上用来连接用户电脑的一种端口，只用于接入链路。
  >当一个端口属于vlan 10时，那么带着vlan 10的数据帧会被发送到交换机这个端口上，当这个数据帧通过这个端口时，vlan 10 tag 将会被剥掉，到达用户电脑时，就是一个以太网的帧。而当用户电脑发送一个以太网的帧时，通过这个端口向上走，那么这个端口就会给这个帧加上一个vlan 10 tag。而其他vlan tag的帧则不能从这个端口上下发到电脑上。access端口一般是untag不打标记的端口,而且一个access vlan端口只允许一个access vlan通过。

2. **trunk端口**：这个端口是交换机之间或者交换机和上层设备之间的通信端口，用于干道链路。一个trunk端口可以拥有一个主vlan和多个副vlan。
  >这个概念可以举个例子来理解：例如：当一个trunk端口有主vlan 10 和多个副vlan11、12、30时，带有vlan 30的数据帧可以通过这个端口，通过时vlan 30不被剥掉；当带有vlan 10的数据帧通过这个端口时也可以通过。如果一个不带vlan 的数据帧通过，那么将会被这个端口打上vlan 10 tag。这种端口的存在就是为了多个vlan的跨越交换机进行传递。trunk一般是打tag标记的,一般只允许打了该tag标记的vlan 通过,所以该端口可以允许多个打tag标记的vlan 通过。

access和truck 主要是区分VLAN中交换机的端口类型。truck端口为与其它交换机端口相连的VLAN汇聚口，access端口为交换机与VLAN域中主机相连的端口。









## 网卡配置

### 激活网卡

```
ifconfig eth0 up
```



### 配置ip地址（x86_64为例/centos）

```
vim /etc/sysconfig/network-scripts/ifcfg-eth0
```

### ethtool命令

ethtool 是用于查询及设置网卡参数的命令。

```
ethtool ethx       //查询ethx网口基本设置，其中 x 是对应网卡的编号，如eth0、eth1等等
ethtool –h        //显示ethtool的命令帮助(help)
ethtool –i ethX    //查询ethX网口的相关信息 
ethtool –d ethX    //查询ethX网口注册性信息
ethtool –r ethX    //重置ethX网口到自适应模式
ethtool –S ethX    //查询ethX网口收发包统计
ethtool –s ethX [speed 10|100|1000] [duplex half|full]  [autoneg on|off]        //设置网口速率10/100/1000M、设置网口半/全双工、设置网口是否自协商

ethtool -E eth0 magic 0x10798086 offset 0x10 value 0x1A  修改网卡EEPROM内容（0x1079 网卡device id , 0x8086网卡verdor id  ）

ethtool -e eth0  : dump网卡EEPROM内容
```



### 网卡bond操作

#### bond网卡
网卡bond是通过多张网卡绑定为一个逻辑网卡，实现本地网卡的冗余，带宽扩容和负载均衡，在生产场景中是一种常用的技术。

可以通过以下命令确定内核是否支持 bonding：

```
cat /boot/config-3.10.0-514.el7.x86_64 | grep -i bonding
```

#### bond的模式

bond的模式常用的有两种：

1. mode=0（balance-rr）
   表示**负载分担**round-robin，并且是**轮询**的方式比如第一个包走eth0，第二个包走eth1，直到数据包发送完毕。
  >优点：流量提高一倍
  >缺点：需要接入交换机做端口聚合，否则可能无法使用

2.  mode=1（active-backup）
   表示**主备模式**，即同时只有1块网卡在工作。
>优点：冗余性高
缺点：链路利用率低，两块网卡只有1块在工作

3. bond其他模式：
mode=2(balance-xor)(平衡策略)
表示XOR Hash负载分担，和交换机的聚合强制不协商方式配合。（需要xmit_hash_policy，需要交换机配置port channel）
特点：基于指定的传输HASH策略传输数据包。缺省的策略是：(源MAC地址 XOR 目标MAC地址) % slave数量。其他的传输策略可以通过xmit_hash_policy选项指定，此模式提供负载平衡和容错能力

**mode=3(broadcast)(广播策略)**
表示所有包从所有网络接口发出，这个不均衡，只有冗余机制，但过于浪费资源。此模式适用于金融行业，因为他们需要高可靠性的网络，不允许出现任何问题。需要和交换机的聚合强制不协商方式配合。
特点：在每个slave接口上传输每个数据包，此模式提供了容错能力

**mode=4(802.3ad)(IEEE 802.3ad 动态链接聚合)**
表示支持802.3ad协议，和交换机的聚合LACP方式配合（需要xmit_hash_policy）.标准要求所有设备在聚合操作时，要在同样的速率和双工模式，而且，和除了balance-rr模式外的其它bonding负载均衡模式一样，任何连接都不能使用多于一个接口的带宽。
特点：创建一个聚合组，它们共享同样的速率和双工设定。根据802.3ad规范将多个slave工作在同一个激活的聚合体下。外出流量的slave选举是基于传输hash策略，该策略可以通过xmit_hash_policy选项从缺省的XOR策略改变到其他策略。需要注意的是，并不是所有的传输策略都是802.3ad适应的，尤其考虑到在802.3ad标准43.2.4章节提及的包乱序问题。不同的实现可能会有不同的适应性。
必要条件：
条件1：ethtool支持获取每个slave的速率和双工设定
条件2：switch(交换机)支持IEEE802.3ad Dynamic link aggregation
条件3：大多数switch(交换机)需要经过特定配置才能支持802.3ad模式

**mode=5(balance-tlb)(适配器传输负载均衡)**
是根据每个slave的负载情况选择slave进行发送，接收时使用当前轮到的slave。该模式要求slave接口的网络设备驱动有某种ethtool支持；而且ARP监控不可用。
特点：不需要任何特别的switch(交换机)支持的通道bonding。在每个slave上根据当前的负载（根据速度计算）分配外出流量。如果正在接受数据的slave出故障了，另一个slave接管失败的slave的MAC地址。
必要条件：
ethtool支持获取每个slave的速率

**mode=6(balance-alb)(适配器适应性负载均衡)**
在5的tlb基础上增加了rlb(接收负载均衡receiveload balance).不需要任何switch(交换机)的支持。接收负载均衡是通过ARP协商实现的.
特点：该模式包含了balance-tlb模式，同时加上针对IPV4流量的接收负载均衡(receiveload balance, rlb)，而且不需要任何switch(交换机)的支持。接收负载均衡是通过ARP协商实现的。bonding驱动截获本机发送的ARP应答，并把源硬件地址改写为bond中某个slave的唯一硬件地址，从而使得不同的对端使用不同的硬件地址进行通信。来自服务器端的接收流量也会被均衡。当本机发送ARP请求时，bonding驱动把对端的IP信息从ARP包中复制并保存下来。当ARP应答从对端到达时，bonding驱动把它的硬件地址提取出来，并发起一个ARP应答给bond中的某个slave。使用ARP协商进行负载均衡的一个问题是：每次广播 ARP请求时都会使用bond的硬件地址，因此对端学习到这个硬件地址后，接收流量将会全部流向当前的slave。这个问题可以通过给所有的对端发送更新（ARP应答）来解决，应答中包含他们独一无二的硬件地址，从而导致流量重新分布。当新的slave加入到bond中时，或者某个未激活的slave重新激活时，接收流量也要重新分布。接收的负载被顺序地分布（round robin）在bond中最高速的slave上当某个链路被重新接上，或者一个新的slave加入到bond中，接收流量在所有当前激活的slave中全部重新分配，通过使用指定的MAC地址给每个 client发起ARP应答。下面介绍的updelay参数必须被设置为某个大于等于switch(交换机)转发延时的值，从而保证发往对端的ARP应答不会被switch(交换机)阻截。

4. bond模式小结：
   mode5和mode6不需要交换机端的设置，网卡能自动聚合。mode4需要支持802.3ad。mode0，mode2和mode3理论上需要静态聚合方式。

#### 配置bond

1. 测试环境：

```
cat /etc/redhat-release 
CentOS Linux release 7.3.1611 (Core)
```

2. 关闭networkmanager服务

```
# systemctl stop NetworkManager.service 
# systemctl disable NetworkManager.service
```

3. 加载bonding模块

```
# modprobe bonding
```



4. 创建基于bond0接口的网卡文件

```
# vim /etc/sysconfig/network-scripts/ifcfg-bond0
DEVICE=bond0
TYPE=Bond
IPADDR=192.168.20.110
NETMASK=255.255.255.0
GATEWAY=192.168.20.2
DNS1=114.114.114.114
USERCTL=no #是否允许非root用户控制该设备
BOOTPROTO=none
ONBOOT=yes
BONDING_MASTER=yes
```



5. 将 需求mode配置在系统文件中

```
# vim /etc/modprobe.d/bond.conf
alias bond0 bonding
options bond0 miimon=100 mode=0 
```



6. 修改物理网卡

```
# vim ifcfg-ens33 
DEVICE=ens33
USERCTL=no
ONBOOT=yes
MASTER=bond0                                                    
SLAVE=yes
BOOTPROTO=none


# vim ifcfg-ens37
DEVICE=ens37
USERCTL=no
ONBOOT=yes
MASTER=bond0                                                    
SLAVE=yes
BOOTPROTO=none
```



7. 重启网络服务

```
systemctl restart network
```



#### 解除bond

```
# 删除/etc/sysconfig/network-scripts/下的bond配置文件
# 清除被bond网卡的slave配置，重新配置网卡
# 在/etc/sysconfig/network-scripts/ 下grep -i bond * 查询目录下所有文件内容包含bond的文件
```









