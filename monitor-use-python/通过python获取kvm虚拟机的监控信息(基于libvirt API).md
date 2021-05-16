# 通过python获取kvm虚拟机的监控信息(基于libvirt API)


 通常在我们的云环境中，为了保证云平台中虚拟机的正常运行，基本都需要这样一个功能，就是收集虚拟机的监控数据，比如cpu的使用率、内存的使用率、磁盘io、网络io等基本信息。可以利用这些信息及时调整云平台环境中出现的一些问题，从而实现保证VM的正常运行。

 说到KVM管理工具，首先应该想到的就是libvirt，因为目前对KVM使用最为广泛的管理工具（应用程序接口）就是libvirt。Libvirt本身构建于一种抽象的概念上，它为受支持的虚拟机监控程序实现常用功能提供通用的API。Libvirt提供了操作KVM的原生层接口，可以实现对虚拟机的基本管理操作。Libvirt库用C实现，且包含对python的直接支持。Libvirt-python就是基于libvirt API的python语言绑定工具包，通过该包可以实现对VM日常管理和监控数据的获取。

 利用python通过调用libvirt API获取VM的监控信息

 1)通过导入libvirt模块，然后连接本地qemu虚拟机监控程序。获取宿主机上每个instance的domain并获取一些基本信息。

```python
import libvirt
conn = libvirt.open("qemu:///system")
for id in conn.listDomainsID():
    domain = conn.lookupByID(id)
    print domain.name()  
    print domain.UUIDString()
    print domain.info()
conn.close()
[root@kvm opt]# python libvirt_test.py 
KaMg8c0hOSn1
instance1
7dd3ec0e-9b56-4e35-b14d-a58811e5c6ce
[1, 2097152L, 2097152L, 2, 8823450000000L]
```

domain.info()返回列表参数说明：

[State:1, Max memory:2097152L, Used memory:2097152L, CPU(s):2, CPU time:4245630000000L]

 具体的参数值代表的意思请参考http://libvirt.org/html/libvirt-libvirt-domain.html对应的API。

 通过这个简单的示例可以看出libvirt通过python提供的强大功能。

 2）获取cpu的使用率

 Libvirt中不能直接获取虚拟机的cpu使用率但是可以通过cputime来计算出实际的使用率，计算公式为：

首先得到一个周期差：cputime_diff = （cpuTimenow — cpuTimet seconds ago）

计算实际使用率：%cpu = 100 × cpu_time_diff / (t × nr_cores × 109)实现：

说明：

可以通过dom.info()[4]获得cputime

通过dom.info()[3]获得cpu数

简单示例：

```python
import libvirt
import time
conn = libvirt.open("qemu:///system")
for id in conn.listDomainsID():
    domain = conn.lookupByID(id)
    t1 = time.time()
    c1 = int (domain.info()[4])
    time.sleep(1);
    t2 = time.time();
    c2 = int (domain.info()[4])
    c_nums = int (domain.info()[3])
    usage = (c2-c1)*100/((t2-t1)*c_nums*1e9)
    print "%s Cpu usage %f" % (domain.name(),usage)
conn.close()
[root@kvm opt]# python libvirt_test.py 
instance1 Cpu usage 0.998784
```

 3)获取网络流量信息

 可以利用dom.interfaceStats(interface)获取虚拟网卡的流量信息，但是该方法需要传递一个虚拟网卡名做为参数。可以使用libvirt的API获取domain的情况，并获取xml配置文件。通过xml的tree来获取每个可用的要监测设备的名称，再通过domain去获取设备的属性字段值即是要监控的数值。

简单示例：

```python
import libvirt
from xml.etree import ElementTree
conn = libvirt.open("qemu:///system")
for id in conn.listDomainsID():
    domain = conn.lookupByID(id)
    tree = ElementTree.fromstring(domain.XMLDesc())
    ifaces = tree.findall('devices/interface/target')
    for i in ifaces:
        iface = i.get('dev')
        ifaceinfo = domain.interfaceStats(iface)
        print domain.name(),iface,ifaceinfo
conn.close()
[root@kvm opt]# python libvirt_test.py 
instance1 vnet12 (90L, 1L, 0L, 0L, 1632L, 24L, 0L, 0L)
instance1 vnet13 (63120L, 256L, 0L, 371L, 0L, 0L, 0L, 0L)
```

domain.interfaceStats(iface)返回结果说明：

(rx_bytes:24194376L, rx_packets:363592L, rx_errs:0L, rx_drop:0L, tx_bytes:852996L, tx_packets:20302L, tx_errs:0L, tx_drop:0L)

可以通过对这些基本数据加工处理得到网络吞吐等信息。

 4)获取磁盘信息  

 获得磁盘的总量和已使用量，可以通过dom.blockInfo(dev)获取。该方法需要传递一个参数,可以使用libvirt的API获取domain的情况，并获取xml配置文件。通过xml的tree来获取每个可用的要监测设备的名称，再通过domain去获取设备的属性字段值即是要监控的数值。

```python
import libvirt
from xml.etree import ElementTree
conn = libvirt.open("qemu:///system")
for id in conn.listDomainsID():
    domain = conn.lookupByID(id)
    tree = ElementTree.fromstring(domain.XMLDesc())
    devices = tree.findall('devices/disk/target')
    for d in devices:
        device = d.get('dev')
        try:
            devinfo = domain.blockInfo(device)
        except libvirt.libvirtError:
            pass
        print domain.name(),device,devinfo
conn.close()
[root@kvm opt]# python libvirt_test.py 
instance1 vda [42949672960L, 2233990656L, 2300968960L]
domain.blockInfo(device)返回结果说明：
```

(capacity:42949672960L, allocation:2233990656L,physical:2300968960L)



 获得磁盘的i/o，可以通过dom.blockStats(dev)获取。

```python
import libvirt
from xml.etree import ElementTree
conn = libvirt.open("qemu:///system")
for id in conn.listDomainsID():
    domain = conn.lookupByID(id)
    tree = ElementTree.fromstring(domain.XMLDesc())
    devices = tree.findall('devices/disk/target')
    for d in devices:
        device = d.get('dev')
        try:
            devstats = domain.blockStats(device)
            print domain.name(),device,devstats
        except libvirt.libvirtError:
            pass
conn.close()
[root@kvm opt]# python libvirt_test.py 
instance1 vda (15100L, 240801280L, 48509L, 395756032L, -1L)
instance1 hda (6L, 164L, 0L, 0L, -1L)
```

domain.blockStats(device)返回列表参数说明：

(read_bytes=1412453376L,read_requests=67017L, write_bytes=2315730432L, write_requests=245180L,errors=-1L)



 通过上边的基础操作可以得到一些磁盘的基础数据，可以对这些数据处理得到想要的磁盘信息，如：磁盘iops等

 5)获得内存信息

 可以通过domain.memoryStats()来获取memory的相关信息。

简单示例：

```python
import libvirt
conn = libvirt.open("qemu:///system")
for id in conn.listDomainsID():
    domain = conn.lookupByID(id)
    domain.setMemoryStatsPeriod(10)
    meminfo = domain.memoryStats()
    free_mem = float(meminfo['unused'])
    total_mem = float(meminfo['available'])
    util_mem = ((total_mem-free_mem) / total_mem)*100
    print (str(domain.name())+' Memory usage :' + str(util_mem))
conn.close()
[root@kvm opt]# python libvirt_test.py 
instance1 Memory usage :27.4561247103
```

domain.memoryStats()返回结果说明：

{'swap_out': 0L, 'available': 1884432L, 'actual': 2097152L, 'major_fault': 457L, 'swap_in': 0L, 'unused': 1367032L, 'minor_fault': 1210349717L, 'rss': 743604L}

 其中actual是启动虚机时设置的最大内存，rss是qemu process在宿主机上所占用的内存，unused代表虚机内部未使用的内存量，available代表虚机内部识别出的总内存量，

那么虚机内部的内存使用量则是可以通过(available-unused)得到。

其实可以使用libvirt的命令行工具获取并查看虚机的内存信息

具体操作如下：

```bash
$ virsh dommemstat instance1
actual 2097152
swap_in 0
rss 743604
```

如果出现如上情况，是因为在VM内没有安装virtio驱动，所有不能获取VM内存的详细信息。



正常在VM内部安装virtio驱动并且支持memballoon，执行上述操作可以看到如下结果：

```bash
$ virsh dommemstat instance1
actual 2097152
swap_in 0
swap_out 0
unused 1367032
available 2050112
rss 743604
```

注意：

 要获取VM内存使用详细信息，VM中需要安装virtio驱动并且支持memballoon。

 关于virtio驱动：Linux一般都会包含(通过 lsmod | grep virtio 查看)，但是windows的virtio驱动需要自己在镜像中安装。

windows注意事项：

 首先windows需要安装virtio-win相关驱动，驱动下载地址 在这里 ，除此之外还需要启动BLNSVR服务。

在 Windows 2008r2 and Windows 2012/Win8 :

  Copy and rename as Administrator the WIN7AMD64 directory from the virtio.iso to “c:/Program files/Balloon”

  Open a CMD as Administrator and cd into “c:/Program Files/Balloon”

  Install the BLNSVR with “BLNSVR.exe -i”

在 Windows 2003 / Windows Xp :

  Download the “devcon” software on microsoft website kb311272

  devcon install BALLOON.inf “PCIVEN_1AF4&DEV_1002&SUBSYS_00051AF4&REV_00”

更多详情请参考: https://pve.proxmox.com/wiki/Dynamic_Memory_Management