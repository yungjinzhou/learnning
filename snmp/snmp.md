##  SNMP

### 1.1  SNMP简介

SNMP（Simple Network Management Protocol，简单网络管理协议）广泛用于网络设备的远程管理和操作。SNMP允许管理员通过NMS对网络上不同厂商、不同物理特性、采用不同互联技术的设备进行管理，包括状态监控、数据采集和故障处理。

#### 1.1.1  SNMP的网络架构

SNMP网络架构由三部分组成：NMS、Agent和MIB。NMS、Agent和MIB之间的关系如[图1-1](https://www.h3c.com/cn/d_202003/1279413_30005_0.htm#_Ref290627539)所示。

·            NMS（Network Management System，网络管理系统）是SNMP网络的管理者，能够提供友好的人机交互界面，来获取、设置Agent上参数的值，方便网络管理员完成大多数的网络管理工作。

·            Agent是SNMP网络的被管理者，负责接收、处理来自NMS的SNMP报文。在某些情况下，如接口状态发生改变时，Agent也会主动向NMS发送告警信息。

·            MIB（Management Information Base，管理信息库）是被管理对象的集合。NMS管理设备的时候，通常会关注设备的一些参数，比如接口状态、CPU利用率等，这些参数就是被管理对象，在MIB中称为节点。每个Agent都有自己的MIB。MIB定义了节点之间的层次关系以及对象的一系列属性，比如对象的名称、访问权限和数据类型等。被管理设备都有自己的MIB文件，在NMS上编译这些MIB文件，就能生成该设备的MIB。NMS根据访问权限对MIB节点进行读/写操作，从而实现对Agent的管理。

图1-1 NMS、Agent和MIB关系图

![img](.\20200330_4832342_image001_1279413_30005_0.png)

 

#### 1.1.2  MIB和MIB视图

MIB以树状结构进行存储。树的每个节点都是一个被管理对象，它用从根开始的一条路径唯一地识别（OID）。如[图1-2](https://www.h3c.com/cn/d_202003/1279413_30005_0.htm#_Ref290627563)所示，被管理对象B可以用一串数字{1.2.1.1}唯一确定，这串数字是被管理对象的OID（Object Identifier，对象标识符）。

MIB视图是MIB的子集合，将团体名/用户名与MIB视图绑定，可以限制NMS能够访问的MIB对象。当用户配置MIB视图包含某个MIB子树时，NMS可以访问该子树的所有节点；当用户配置MIB视图不包含某个MIB子树时，NMS不能访问该子树的所有节点。

图1-2 MIB树结构

![img](https://www.h3c.com/cn/res/202003/30/20200330_4832343_image002_1279413_30005_0.png)

 

#### 1.1.3  SNMP基本操作

SNMP提供四种基本操作：

·            Get操作：NMS使用该操作查询Agent MIB中节点的值。

·            Set操作：NMS使用该操作配置Agent MIB中节点的值。

·            告警操作：SNMP告警包括Trap和Inform两种。

*¡*  *Trap**操作：**Agent**使用该操作向**NMS**发送**Trap**报文。**Agent**不要求**NMS**发送回应报文，**NMS**也不会对**Trap**报文进行回应。**SNMPv1**、**SNMPv2c**和**SNMPv3**均支持**Trap**操作。*

*¡*  *Inform**操作：**Agent**使用该操作向**NMS**发送**Inform**报文。**Agent**要求**NMS**发送回应报文，因此，**Inform**报文比**Trap**报文更可靠*，但消耗的系统资源更多*。**如果**Agent**在一定时间内没有收到**NMS**的回应报文，则会启动重发机制。**只有**SNMPv2c**和**SNMPv3**支持**Inform**操作。*

#### 1.1.4  SNMP版本介绍

目前，设备运行于非FIPS模式时，支持SNMPv1、SNMPv2c和SNMPv3三种版本；设备运行于FIPS模式时，只支持SNMPv3版本。只有NMS和Agent使用的SNMP版本相同时，NMS才能和Agent建立连接。

·            SNMPv1采用团体名（Community Name）认证机制。团体名类似于密码，用来限制NMS和Agent之间的通信。如果NMS配置的团体名和被管理设备上配置的团体名不同，则NMS和Agent不能建立SNMP连接，从而导致NMS无法访问Agent，Agent发送的告警信息也会被NMS丢弃。

·            SNMPv2c也采用团体名认证机制。SNMPv2c对SNMPv1的功能进行了扩展：提供了更多的操作类型；支持更多的数据类型；提供了更丰富的错误代码，能够更细致地区分错误。

·            SNMPv3采用USM（User-Based Security Model，基于用户的安全模型）认证机制。网络管理员可以配置认证和加密功能。认证用于验证报文发送方的合法性，避免非法用户的访问；加密则是对NMS和Agent之间的传输报文进行加密，以免被窃听。采用认证和加密功能可以为NMS和Agent之间的通信提供更高的安全性。

#### 1.1.5  SNMP支持的访问控制方式

SNMP支持的访问控制方式包括：

·            VACM（View-based Access Control Model，基于视图的访问控制模型）：将团体名/用户名与指定的MIB视图进行绑定，可以限制NMS能够访问哪些MIB对象，以及对MIB对象不同的操作权限。

·            RBAC（Role Based Access Control，基于角色的访问控制）：创建团体名/用户名时，可以指定对应的用户角色，通过用户角色下制定的规则，来限制NMS能够访问哪些MIB对象，以及对MIB对象不同的操作权限。

¡  拥有network-admin或level-15用户角色的SNMP团体/用户，可以对所有的MIB对象进行读写操作；

¡  拥有network-operator用户角色的SNMP团体/用户，可以对所有的MIB对象进行读操作；

¡  拥有自定义用户角色的SNMP团体/用户，可以对角色规则中指定的MIB对象进行操作。

对于同一SNMP用户名/团体名，只能配置一种控制方式，多次使用两种控制方式配置同一用户名/团体名时，以最后一次的配置方式为准。

RBAC配置方式限制的是MIB节点的读写权限，VACM配置方式限制的是MIB视图的读写权限，而一个视图中通常包括多个MIB节点。所以，RBAC配置方式更精准、更灵活。关于RBAC的详细介绍请参见“基础配置”中的“RBAC”。



**参考链接**：https://www.h3c.com/cn/d_202003/1279413_30005_0.htm



### 1.2 snmp安装与配置

#### 1.2.1 snmp安装

centos7上安装

```
yum install -y net-snmp
yum install -y net-snmp-devel
yum install -y net-snmp-libs
yum install -y net-snmp-perl
yum install -y net-snmp-utils
yum install -y mrtg
```

#### 1.2.2 snmp配置文件

sed -i.default -e '/^#/d' -e '/^$/d'  /etc/snmp/snmpd.conf

复制snmpd.conf文件到/etc/snmp/目录下。（原有的重命名，保存）

```
# 下面是所有配置项 5.7.2
agentAddress udp:161
com2sec notConfigUser  default       public
group   notConfigGroup v1           notConfigUser
group   notConfigGroup v2c           notConfigUser
view    all    included   .1
view    systemview    included   .1
view    systemview    included   .1.3.6.1.2.1.1
view    systemview    included   .1.3.6.1.2.1.25.1.1
access  notConfigGroup ""      any       noauth    exact  systemview none none
syslocation Unknown (edit /etc/snmp/snmpd.conf)
syscontact Root <root@localhost> (configure /etc/snmp/snmp.local.conf)
dontLogTCPWrappersConnects yes
includeAllDisks for all partitions and disks
```

**配置解释**

- 首选是定义一个共同体名 (community) ，这里是 public ，及可以访问这个 public 的用户名（ sec name ），这里是 notConfigUser 。 Public 相当于用户 notConfigUser 的密码
- 定义一个组名（ groupName ）这里是 notConfigGroup ，及组的安全级别，把 notConfigGroup 这个用户加到这个组中。   
- 定义一个可操作的范围 (view) 名，   这里是 all ，范围是  .1 
- 定义 notConfigUser 这个组在 all 这个 view 范围内可做的操作，这时定义了 notConfigUser 组的成员可对.1 这个范围做只读操作。 
- 要获取硬盘信息，需要在snmpd.conf中加入以下信息（假设硬盘只有一个根分区(/)）：
  Disk / 100000（也可以写所有     includeAllDisks for all partitions and disks）

 **man snmpd.conf 可以查看具体配置项信息**

#### 1.2. 3 启动snmpd服务

systemctl start snmpd

查看状态systemctl status snmpd

**snmp重启失败，不收集物理机数据时**
**重启libvirtd.service 然后重启snmpd服务**

##### 关闭selinux和防火墙

```
#setenforce 0

#vi /etc/sysconfig/selinux

 修改为：SELINUX=disabled

#service snmpd start

#chkconfig snmpd on
```

#### 1.2.4 测试

##### 1.2.4.1 查看扫描指标个数

snmpwalk -v 2c -c public localhost:161 | wc -l

如果获取的几十个指标，说明配置有问题，重新检查配置和服务

##### 1.2.4.2 查看类

**正常获取**

```
[root@compute02 ~]# snmpwalk -v 2c -c public localhost:161 memory
UCD-SNMP-MIB::memIndex.0 = INTEGER: 0
UCD-SNMP-MIB::memErrorName.0 = STRING: swap
UCD-SNMP-MIB::memTotalSwap.0 = INTEGER: 2097148 kB
UCD-SNMP-MIB::memAvailSwap.0 = INTEGER: 2097148 kB
UCD-SNMP-MIB::memTotalReal.0 = INTEGER: 3861508 kB
UCD-SNMP-MIB::memAvailReal.0 = INTEGER: 579332 kB
UCD-SNMP-MIB::memTotalFree.0 = INTEGER: 2676480 kB
UCD-SNMP-MIB::memMinimumSwap.0 = INTEGER: 16000 kB
UCD-SNMP-MIB::memShared.0 = INTEGER: 176028 kB
UCD-SNMP-MIB::memBuffer.0 = INTEGER: 2112 kB
UCD-SNMP-MIB::memCached.0 = INTEGER: 871696 kB
UCD-SNMP-MIB::memTotalSwapX.0 = Counter64: 2097148 kB
UCD-SNMP-MIB::memAvailSwapX.0 = Counter64: 2097148 kB
UCD-SNMP-MIB::memTotalRealX.0 = Counter64: 3861508 kB
UCD-SNMP-MIB::memAvailRealX.0 = Counter64: 579332 kB
UCD-SNMP-MIB::memTotalFreeX.0 = Counter64: 2676480 kB
UCD-SNMP-MIB::memMinimumSwapX.0 = Counter64: 16000 kB
UCD-SNMP-MIB::memSharedX.0 = Counter64: 176028 kB
UCD-SNMP-MIB::memBufferX.0 = Counter64: 2112 kB
UCD-SNMP-MIB::memCachedX.0 = Counter64: 871696 kB
UCD-SNMP-MIB::memSwapError.0 = INTEGER: noError(0)
UCD-SNMP-MIB::memSwapErrorMsg.0 = STRING: 

```

**异常获取**

`UCD-SNMP-MIB::memory = No more variables left in this MIB View (It is past the end of the MIB tree)`

##### 1.2.4.3 查看具体指标

可以用snmpwalk测试snmpd运行是否正常

snmpwalk -v 2c -c public 192.168.204.194 oid

### 1.3 snmpwalk使用

#### 1.3.1 查看磁盘名称

snmpwalk -v 2c -c public 127.0.0.1  diskIODevice

#### 1.3.2 查看MIB和OID对应关系

snmptranslate -Tz -m all

**截取部分**

```
"snmpSetGroup"			"1.3.6.1.6.3.1.2.2.5"
"systemGroup"			"1.3.6.1.6.3.1.2.2.6"
"snmpBasicNotificationsGroup"			"1.3.6.1.6.3.1.2.2.7"
"snmpGroup"			"1.3.6.1.6.3.1.2.2.8"
"snmpCommunityGroup"			"1.3.6.1.6.3.1.2.2.9"
"snmpObsoleteGroup"			"1.3.6.1.6.3.1.2.2.10"
"snmpWarmStartNotificationGroup"			"1.3.6.1.6.3.1.2.2.11"
"snmpNotificationGroup"			"1.3.6.1.6.3.1.2.2.12"
"snmpFrameworkMIB"			"1.3.6.1.6.3.10"
```



#### 1.3.3 看看网络接口及网络接口名称
**查看接口：**
snmpwalk -v 1 222.90.47.169 -c public ifIndex

**网络接口名称**:
snmpwalk -v 1 222.90.47.169 -c public ifDescr

**MIB的相关定义是Interface组**

针对普通网络设备的端口，，主要管理如下信息:

```
ifIndex                 端口索引号
ifDescr                 端口描述
ifType                  端口类型
ifMtu                   最大传输包字节数
ifSpeed                 端口速度
ifPhysAddress           物理地址
ifOperStatus            操作状态
ifLastChange            上次状态更新时间
*ifInOctets             输入字节数
*ifInUcastPkts          输入非广播包数
*ifInNUcastPkts         输入广播包数
*ifInDiscards           输入包丢弃数
*ifInErrors             输入包错误数
*ifInUnknownProtos      输入未知协议包数
*ifOutOctets            输出字节数
*ifOutUcastPkts         输出非广播包数
*ifOutNUcastPkts        输出广播包数
*ifOutDiscards          输出包丢弃数
*ifOutErrors            输出包错误数
ifOutQLen               输出队长
```



