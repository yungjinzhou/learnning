#### 1. 平均负载

##### 1.1 定义
平均负载其实就是平均活跃进程数。平均活跃进程数，直观上的理解就是单位时间内的活跃进程数，但它实际上是活跃进程数的指数衰减平均值。

先查看系统有几个cpu     ```grep 'model name' /proc/cpuinfo | wc -l```, 当平均负载比 CPU 个数还大的时候，系统已经出现了过载。

当平均负载高于 CPU 数量 70% 的时候，你就应该分析排查负载高的问题了。一旦负载过高，就可能导致进程响应变慢，进而影响服务的正常功能。

##### 1.2 常用分析命令

stress 是一个 Linux 系统压力测试工具，这里我们用作异常进程模拟平均负载升高的场
景。

```
运行 stress 命令，模拟一个 CPU 使用率 100% 的场景 
stress --cpu 1 --timeout 600
另一个终端查看
watch -d uptime，查看cpu平均负载

# -P ALL 表示监控所有 CPU，后面数字 5 表示间隔 5 秒后输出一组数据
$ mpstat -P ALL 5

# 间隔 5 秒后输出一组数据，查看哪个进程 的cpu使用率，哪个命令导致的
$ pidstat -u 5 1

CPU 密集型进程特点：
1 分钟的平均负载会慢慢增加到 1.00，而从终端三中还可以看到，
正好有一个 CPU 的使用率为 100%，但它的 iowait 只有 0。这说明，平均负载的升高正
是由于 CPU 使用率为 100% 。



# 运行 stress 命令，但这次模拟 I/O 压力，即不停地执行 sync
stress -i 1 --timeout 600

I/O 密集型进程的特点：
用mpstat -P ALL 5分析
1 分钟的平均负载会慢慢增加到 1.06，其中一个 CPU 的系统 CPU 使用
率升高到了 23.87，而 iowait 高达 67.53%。这说明，平均负载的升高是由于 iowait 的升
高。




大量进程的场景的特点：
当系统中运行进程超出 CPU 运行能力时，就会出现等待 CPU 的进程。
使用 stress，但这次模拟的是 8 个进程
$ stress -c 8 --timeout 600
，8 个进程在争抢 2 个 CPU，每个进程等待 CPU 的时间（也就是代码块中的
%wait 列）高达 75%。这些超出 CPU 计算能力的进程，最终导致 CPU 过载。
```



而 sysstat 包含了常用的 Linux 性能工具，用来监控和分析系统的性能。我们的案例会用
到这个包的两个命令 mpstat 和 pidstat。

mpstat 是一个常用的多核 CPU 性能分析工具，用来实时查看每个 CPU 的性能指标，
以及所有 CPU 的平均指标。
pidstat 是一个常用的进程性能分析工具，用来实时查看进程的 CPU、内存、I/O 以及
上下文切换等性能指标。





#### 2. cpu上下文切换

##### 2.1 上下文的概念

​       上下文：CPU 寄存器，是 CPU 内置的容量小、但速度极快的内存。而程序计数器，则是用来存储CPU 正在执行的指令位置、或者即将执行的下一条指令位置。它们都是 CPU 在运行任何任务前，必须的依赖环境，因此也被叫做 CPU 上下文。

​        CPU 上下文切换：就是先把前一个任务的 CPU 上下文（也就是 CPU 寄存器和程序计数器）保存起来，然后加载新任务的上下文到这些寄存器和程序计数器，最后再跳转到程序计数器所指的新位置，运行新任务。



##### 2.2 进程上下文切换

​        Linux 按照特权等级，把进程的运行空间分为内核空间和用户空间。从用户态到内核态的转变，需要通过系统调用来完成。一次系统调用实际发生了两次cpu上下文切换。

```
系统调用：CPU 寄存器里原来用户态的指令位置，需要先保存起来。接着，为了执行内核态代码，CPU 寄存器需要更新为内核态指令的新位置。最后才是跳转到内核态运行内核任务。而系统调用结束后，CPU 寄存器需要恢复原来保存的用户态，然后再切换到用户空间，继续运行进程
```

​        需要注意的是，系统调用过程中，并不会涉及到虚拟内存等进程用户态的资源，也不会切换进程。所以，系统调用过程通常称为特权模式切换，而不是上下文切换。

​        进程是由内核来管理和调度的，进程的切换只能发生在内核态。所以，进程的上下文不仅包括了虚拟内存、栈、全局变量等用户空间的资源，还包括了内核堆栈、寄存器等内核空间的状态。

​        进程切换的条件：

```
1. 当某个进程的时间片耗尽了，就会被系统挂起，切换到其它正在等待 CPU 的进程运行。
2. 进程在系统资源不足（比如内存不足）时，要等到资源满足后才可以运行，这个时候进程也会被挂起，并由系统调度其他进程运行。
3. 当进程通过睡眠函数 sleep 这样的方法将自己主动挂起时，自然也会重新调度。
4. 当有优先级更高的进程运行时，为了保证高优先级进程的运行，当前进程会被挂起，由高优先级进程来运行。
5. 发生硬件中断时，CPU 上的进程会被中断挂起，转而执行内核中的中断服务程序。
```



##### 2.3 线程上下文切换

线程与进程最大的区别在于，线程是调度的基本单位，而进程则是资源拥有的基本单位。

所谓内核中的任务调度，实际上的调度对象是线程；而进程只是给线程提供了虚拟内存、全局变量等资源。

##### 2.4 中断上下文切换

​        为了快速响应硬件的事件，中断处理会打断进程的正常调度和执行，转而调用中断处理程序，响应设备事件。而在打断其他进程时，就需要将进程当前的状态保存下来，这样在中断结束后，进程仍然可以从原来的状态恢复运行。

​        跟进程上下文不同，中断上下文切换并不涉及到进程的用户态。中断上下文，其实只包括内核态中断服务程序执行所必需的状态，包括 CPU 寄存器、内核堆栈、硬件中断参数等。
​        对同一个 CPU 来说，中断处理比进程拥有更高的优先级，所以中断上下文切换并不会与进程上下文切换同时发生。同样道理，由于中断会打断正常进程的调度和执行，所以大部分中断处理程序都短小精悍，以便尽可能快的执行结束。



##### 2.5 查看系统上下文切换

可以使用 vmstat 这个工具，来查询系统的上下文切换情况。

```
# 每隔 5 秒输出 1 组数据
$ vmstat 5
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
r b swpd free buff cache si so bi bo in cs us sy id wa st
0 0 0 7005360 91564 818900 0 0 0 0 25 33 0 0 100 0 0

cs（context switch）是每秒上下文切换的次数。
in（interrupt）则是每秒中断的次数。
r（Running or Runnable）是就绪队列的长度，也就是正在运行和等待 CPU 的进程
数。
b（Blocked）则是处于不可中断睡眠状态的进程数。


```

vmstat 只给出了系统总体的上下文切换情况，要想查看每个进程的详细情况，就需要使用
我们前面提到过的 pidstat 了

```
$ pidstat -w 5
Linux 4.15.0 (ubuntu) 09/23/18 _x86_64_ (2 CPU)
08:18:26 UID PID cswch/s nvcswch/s Command
08:18:31 0 1 0.20 0.00 systemd
08:18:31 0 8 5.40 0.00 rcu_sched


一个是 cswch ，表示每秒自愿上下文切换
（voluntary context switches）的次数，另一个则是 nvcswch ，表示每秒非自愿上下文
切换（non voluntary context switches）的次数。

所谓自愿上下文切换，是指进程无法获取所需资源，导致的上下文切换。比如说，I/O、内存等系统资源不足时，就会发生自愿上下文切换。
而非自愿上下文切换，则是指进程由于时间片已到等原因，被系统强制调度，进而发生的上下文切换。比如说，大量进程都在争抢 CPU 时，就容易发生非自愿上下文切换。
```



##### 2.6 模拟上下文切换

使用 sysbench 来模拟系统多线程调度切换的情况。

sysbench 是一个多线程的基准测试工具，一般用来评估不同系统参数下的数据库负载情
况。当然，在这次案例中，我们只把它当成一个异常进程来看，作用是模拟上下文切换过
多的问题



```
# 以 10 个线程运行 5 分钟的基准测试，模拟多线程切换的问题
$ sysbench --threads=10 --max-time=300 threads run

分析cpu 队列，中断，切换次数
每隔 1 秒输出 1 组数据（需要 Ctrl+C 才结束）
$ vmstat 1

# 每隔 1 秒输出 1 组数据（需要 Ctrl+C 才结束）
# -w 参数表示输出进程切换指标，而 -u 参数则表示输出 CPU 使用指标， # -wt 参数表示输出线程的上下文切换指标
$ pidstat -w -u 1

读取中断信息
# -d 参数表示高亮显示变化的区域
$ watch -d cat /proc/interrupts

变化速度最快的是重调度中断（RES），这个中断类型表示，唤醒空闲状态的 CPU 来调度新的任务运行。这是多处理器系统（SMP）中，调度器用来分散任务到不同 CPU 的机制，通常也被称为处理器间中断（Inter-ProcessorInterrupts，IPI）。


```



##### 2.7 cpu切换多少正常

​         这个数值其实取决于系统本身的 CPU 性能。在我看来，如果系统的上下文切换次数比较稳定，那么从数百到一万以内，都应该算是正常的。但当上下文切换次数超过一万次，或者切换次数出现数量级的增长时，就很可能已经出现了性能问题。
​         比方说：自愿上下文切换变多了，说明进程都在等待资源，有可能发生了 I/O 等其他问题；非自愿上下文切换变多了，说明进程都在被强制调度，也就是都在争抢 CPU，说明 CPU的确成了瓶颈；中断次数变多了，说明 CPU 被中断处理程序占用，还需要通过查看 /proc/interrupts文件来分析具体的中断类型。



#### 3. cpu使用率

​       对比一下 top 和 ps 这两个工具报告的 CPU 使用率，默认的结果很可能不一样，因为 top 默认使用 3 秒时间间隔，而 ps 使用的却是进程的整个生命周期。

​         top 显示了系统总体的 CPU 和内存使用情况，以及各个进程的资源使用情况。ps 则只显示了每个进程的资源使用情况。

##### 3.1 分析工具perf

```
$ perf top
Samples: 833 of event 'cpu-clock', Event count (approx.): 97742399
Overhead Shared Object Symbol
7.28% perf [.] 0x00000000001f78a4
4.72% [kernel] [k] vsnprintf
4.32% [kernel] [k] module_get_kallsym
3.65% [kernel] [k] _raw_spin_unlock_irqrestore

输出结果中，第一行包含三个数据，分别是采样数（Samples）、事件类型（event）和事件总数量（Event count）。比如这个例子中，perf 总共采集了 833 个 CPU 时钟事件，而总事件数则为 97742399。

第一列 Overhead ，是该符号的性能事件在所有采样中的比例，用百分比来表示。
第二列 Shared ，是该函数或指令所在的动态共享对象（Dynamic Shared Object），如内核、进程名、动态链接库名、内核模块名等。
第三列 Object ，是动态共享对象的类型。比如 [.] 表示用户空间的可执行程序、或者动态链接库，而 [k] 则表示内核空间。
最后一列 Symbol 是符号名，也就是函数名。当函数名未知时，用十六进制的地址来表示。

# -g 开启调用关系分析，-p 指定 php-fpm 的进程号 21515
$ perf top -g -p 21515





perf record 和 perf report。 perf top 虽然实时展示了系统的性能信息，但它的缺点是并不保存数据，也就无法用于离线或者后续的分析。而 perf record 则提供了保存数据的功能，保存后的数据，需要你用 perf report 解析展示。

$ perf record # 按 Ctrl+C 终止采样
[ perf record: Woken up 1 times to write data ]
[ perf record: Captured and wrote 0.452 MB perf.data (6093 samples) ]
$ perf report # 展示类似于 perf top 的报告
```



##### 3.2 案例

1. 系统的 CPU 使用率很高，但却找不到高 CPU的应用

​     使用execsnoop 就是一个专为短时进程设计的工具。它通过 ftrace 实时监控进程的 exec() 行为，并输出短时进程的基本信息，包括进程 PID、父进程 PID、命令行参数以及执行的结果。

```
# -a 表示输出命令行选项
# p 表 PID
# s 表示指定进程的父进程
$ pstree -aps 3084



dstat ，它的好处是，可以同时查看 CPU 和 I/O这两种资源的使用情况，便于对比分析。
# 间隔 1 秒输出 10 组数据
$ dstat 1 10
You did not select any stats, using -cdngy by default.
--total-cpu-usage-- -dsk/total- -net/total- ---paging-- ---system--
usr sys idl wai stl| read writ| recv send| in out | int csw
0 0 96 4 0|1219k 408k| 0 0 | 0 0 | 42 885
0 0 2 98 0| 34M 0 | 198B 790B| 0 0 | 42 138
```



2. 软中断

sar 是一个系统活动报告工具，既可以实时查看系统的当前活动，又可以配置保存和报告历史统计数据。
hping3 是一个可以构造 TCP/IP 协议数据包的工具，可以对系统进行安全审计、防火墙测试等。
tcpdump 是一个常用的网络抓包工具，常用来分析各种网络问题。

```
# -S 参数表示设置 TCP 协议的 SYN（同步序列号），-p 表示目的端口为 80
# -i u100 表示每隔 100 微秒发送一个网络帧
# 注：如果你在实践过程中现象不明显，可以尝试把 100 调小，比如调成 10 甚至 1
$ hping3 -S -p 80 -i u100 192.168.0.30

```



```
watch -d cat /proc/softirqs
watch 命令，就可以定期运行一个命令来查看输出；如果再加上 -d 参数，还可以高亮出变化的部分，从高亮部分我们就可以直观看出，哪些内容变化得更快



# -n DEV 表示显示网络收发的报告，间隔 1 秒输出一组数据
$ sar -n DEV 1
15:03:46 IFACE rxpck/s txpck/s rxkB/s txkB/s rxcmp/s txcmp/s rxmcs
15:03:47 eth0 12607.00 6304.00 664.86 358.11 0.00 0.00 0

第一列：表示报告的时间。
第二列：IFACE 表示网卡。
第三、四列：rxpck/s 和 txpck/s 分别表示每秒接收、发送的网络帧数，也就是 PPS。
第五、六列：rxkB/s 和 txkB/s 分别表示每秒接收、发送的千字节数，也就是 BPS。
后面的其他参数基本接近 0，显然跟今天的问题没有直接关系，你可以先忽略掉。
```



![img](H:\code\learnning\linux-releated\linux性能\企业微信截图_16244955228161.png) 



![img](H:\code\learnning\linux-releated\linux性能\企业微信截图_1624495488667.png)  



 ![img](H:\code\learnning\linux-releated\linux性能\企业微信截图_16244954676633.png) 

#### 4. 内存

##### 4.1 内存概念

1. 内存分为虚拟内存和物理内存

   ​        虚拟内存比较大，并不是所有的虚拟内存都会分配物理内存，只有那些实际使用的虚拟内存才分配物理内存，并且分配后的物理内存，是通过内存映射来管理的。

2. 虚拟内存空间分布

 ![img](H:\code\learnning\linux-releated\linux性能\企业微信截图_16238465767688.png) 



     虚拟内存分内核空间和用户空间，其中用户空间又分为下面5部分：
     只读段，包括代码和常量等。
     数据段，包括全局变量等。
     堆，包括动态分配的内存，从低地址开始向上增长。
     文件映射段，包括动态库、共享内存等，从高地址开始向下增长。
     栈，包括局部变量和函数调用的上下文等。栈的大小是固定的，一般是 8 MB。
在这五个内存段中，堆和文件映射段的内存是动态分配的。比如说，使用 C 标准库的
malloc() 或者 mmap() ，就可以分别在堆和文件映射段动态分配内存。

3. 交换分区

​         Swap其实就是把一块磁盘空间当成内存来用。它可以把进程暂时不用的数据存储到磁盘中（这
个过程称为换出），当进程访问这些内存时，再从磁盘读取这些数据到内存中（这个过程
称为换入）。

4. 查看内存

   这些数据，包含了进程最重要的几个内存使用情况，我们挨个来看。
   VIRT 是进程虚拟内存的大小，只要是进程申请过的内存，即便还没有真正分配物理内存，也会计算在内。
   RES 是常驻内存的大小，也就是进程实际使用的物理内存大小，但不包括 Swap 和共享SHR 是共享内存。
   SHR 是共享内存的大小，比如与其他进程共同使用的共享内存、加载的动态链接库以及程序的代码段等。
   %MEM 是进程使用物理内存占系统总内存的百分比。

##### 4.2 内存指标

   1. 简单来说，Buffer 是对磁盘数据的缓存，而 Cache 是文件数据的缓存，它们既会用在读
      请求中，也会用在写请求中。

   ```
   利用vmstat同时dd命令观察 cache  buffer  bi bo指标确定buffer和cache的区别
   
   # 每隔 1 秒输出 1 组数据
   $ vmstat 1
   buff 和 cache 就是我们前面看到的 Buffers 和 Cache，单位是 KB。
   bi 和 bo 则分别表示块设备读取和写入的大小，单位为块 / 秒。因为 Linux 中块的大小是 1KB，所以这个单位也就等价于 KB/s。
   
   
   
   终端执行 dd 命令，通过读取随机设备，生成一个 500MB大小的文件：
   $ dd if=/dev/urandom of=/tmp/file bs=1M count=500
   
   
   # 首先清理缓存
   $ echo 3 > /proc/sys/vm/drop_caches
   # 运行 dd 命令读取文件数据
   $ dd if=/tmp/file of=/dev/null
   
   # 首先清理缓存
   $ echo 3 > /proc/sys/vm/drop_caches
   # 然后运行 dd 命令向磁盘分区 /dev/sdb1 写入 2G 数据
   $ dd if=/dev/urandom of=/dev/sdb1 bs=1M count=2048
   
   ```

共享内存是通过 tmpfs 实现的，所以它的大小也就是 tmpfs 使用的内存大小。tmpfs
其实也是一种特殊的缓存。

##### 4.3 缓存使用及指标查看

    两部分，一部分是磁盘读取文件的页缓存，用来缓存从磁盘读取的数据，可以加快以后再次访问的速度。另一部分，则是 Slab 分配器中的可回收内存。
    是对原始磁盘块的临时存储，用来缓存将要写入磁盘的数据。

1. 缓存指标查看

```
bcc 提供的所有工具就都安装到 /usr/share/bcc/tools 这个目录中了。
不过这里提醒你，bcc 软件包默认不会把这些工具配置到系统的 PATH 路径中，所以你得
自己手动配置：
1 $ export PATH=$PATH:/usr/share/bcc/tools

centos7上安装bcc-tools

# 升级系统
yum update -y
# 安装 ELRepo
rpm --import https://www.elrepo.org/RPM-GPG-KEY-elrepo.org
rpm -Uvh https://www.elrepo.org/elrepo-release-7.0-3.el7.elrepo.noarch.rpm
# 安装新内核
yum remove -y kernel-headers kernel-tools kernel-tools-libs
yum --enablerepo="elrepo-kernel" install -y kernel-ml kernel-ml-devel kernel-ml-headers
# 更新 Grub 后重启
grub2-mkconfig -o /boot/grub2/grub.cfg
grub2-set-default 0
reboot
# 重启后确认内核版本已升级为 4.20.0-1.el7.elrepo.x86_64
uname -r

# 安装 bcc-tools
yum install -y bcc-tools
# 配置 PATH 路径
export PATH=$PATH:/usr/share/bcc/tools
# 验证安装成功
cachestat


```



   ```
   bbc软件包的一部分
   cachestat 提供了整个操作系统缓存的读写命中情况。
   cachetop 提供了每个进程的缓存命中情况。
   
   
   $ cachestat 1 3
   它以 1 秒的时间间隔，输出了 3 组缓存统计数据：
   
   
   TOTAL ，表示总的 I/O 次数；
   MISSES ，表示缓存未命中的次数；
   HITS ，表示缓存命中的次数；
   DIRTIES， 表示新增到缓存中的脏页数；
   BUFFERS_MB 表示 Buffers 的大小，以 MB 为单位；
   CACHED_MB 表示 Cache 的大小，以 MB 为单位。
   
   
$ cachetop
而 READ_HIT 和 WRITE_HIT ，分别表示读和写的缓存命中率。
   
   ```

2. buffer和cache的区别

	换句话说，磁盘是存储数据的块设备，也是文件系统的载体。所以，文件系统确实还是要通过磁盘，来保证数据的持久化存储。
	在读写普通文件时，I/O 请求会首先经过文件系统，然后由文件系统负责，来与磁盘进行交互。而在读写块设备文件时，会跳过文件系统，直接与磁盘交互，也就是所谓的“裸I/O”。
	这两种读写方式使用的缓存自然不同。文件系统管理的缓存，其实就是 Cache 的一部分。而裸磁盘的缓存，用的正是 Buffer。

##### 4.4 内存泄漏

1. **内存泄漏**的可能部分

   有系统分配的内存一般会自动回收，不会造成内存泄漏。比如栈内存由系统自动分配和管理。
   只读段，包括程序的代码和常量，由于是只读的，不会再去分配新的内存，所以也不会产生内存泄漏。
   数据段，包括全局变量和静态变量，这些变量在定义时就已经确定了大小，所以也不会产生内存泄漏。
   **堆内存**由应用程序自己来分配和管理。除非程序退出，这些堆内存并不会被系统自动释放，而是需要应用程序明确调用库函数 free() 来释放它们。
   **内存映射段**，包括动态链接库和共享内存，其中共享内存由程序动态分配和管理。所以，如果程序在分配后忘了回收，就会导致跟堆内存类似的泄漏问题。

2. 内存泄漏的工具

   专门用来检测内存泄漏的工具，memleak。memleak 可以跟踪系统或指定进程的内存分配、释放请求，然后定期输出一个未释放内存和相应调用栈的汇总情况（默认 5 秒）。
   memleak是bbc软件包的一个工具，运行/usr/share/bcc/tools/memleak就可以运行它。

```
# -a 表示显示每个内存分配请求的大小以及地址
# -p 指定案例应用的 PID 号
$ /usr/share/bcc/tools/memleak -a -p $(pidof app)
WARNING: Couldn't find .text section in /app
WARNING: BCC can't handle sym look ups for /app
addr = 7f8f704732b0 size = 8192
addr = 7f8f704772d0 size = 8192
addr = 7f8f704712a0 size = 8192
addr = 7f8f704752c0 size = 8192
32768 bytes in 4 allocations from stack
[unknown] [app]
[unknown] [app]
```

##### 4.5 内存回收

    内存回收，也就是系统释放掉可以回收的内存。
    在内存资源紧张时，Linux 通过直接内存回收和定期扫描的方式，来释放文件页和匿名
页，以便把内存分配给更需要的进程使用

1. 文件页、脏页、匿名页

   文件页：缓存和缓冲区，就属于可回收内存。它们在内存管理中，通常被叫做文件页。，通过内存映射获取的文件映射页，也是一种常见的文件页。
   脏页：而那些被应用程序修改过，并且暂时还没写入磁盘的数据（也就是脏页），就得先写入磁盘，然后才能进行内存释放。脏页写入磁盘有两种方式：
       可以在应用程序中，通过系统调用 fsync ，把脏页同步到磁盘中；
       也可以交给系统，由内核线程 pdflush 负责这些脏页的刷新。
   匿名页：应用程序动态分配的堆内存，也就是我们在内存管理中说到的匿名页（Anonymous Page）。

2. swap原理

    Swap 把这些不常访问的内存先写到磁盘中，然后释放这些内存，给其他更需要的进程使用。再次访问这些内存时，重新从磁盘读入内存就可以了。
    Swap 说白了就是把一块磁盘空间或者一个本地文件（以下讲解以磁盘为例），当成内存来使用。它包括换出和换入两个过程。
        换出：就是把进程暂时不用的内存数据存储到磁盘中，并释放这些数据占用的内存；
        换入：则是在进程再次访问这些内存的时候，把它们从磁盘读到内存中。
    我们常见的笔记本电脑的休眠和快速开机的功能，也基于 Swap 。

3.  定期回收内存

   除了直接内存回收，还有一个专门的内核线程用来定期回收内存，也就是kswapd0。为了衡量内存的使用情况，kswapd0 定义了三个内存阈值（watermark，也称为水位），分别是页最小阈值（pages_min）、页低阈值（pages_low）和页高阈值（pages_high）。剩余内存，则使用 pages_free 表示。

    ![img](H:\code\learnning\linux-releated\linux性能\企业微信截图_1624580713665.png) 

```
可以通过内核选项 /proc/sys/vm/min_free_kbytes 来间接设置。min_free_kbytes 设置
了页最小阈值，而其他两个阈值，都是根据页最小阈值计算生成的，
pages_low = pages_min*5/4
pages_high = pages_min*3/2

```

5. NUMA

   你明明发现了 Swap 升高，可是在分析系统的内存使用时，却很可能发现，系统剩余内存还多着呢,，这正是处理器的 NUMA （Non-UniformMemory Access）架构导致的。
在 NUMA 架构下，多个处理器被划分到不同 Node 上，且每个 Node 都拥有自己的本地内存空间。

6. 调整内存回收机制：swappiness

    对文件页的回收，当然就是直接回收缓存，或者把脏页写回磁盘后再回收。
    对匿名页的回收，其实就是通过 Swap 机制，把它们写入磁盘后再释放内存。
    Linux 提供了一个 /proc/sys/vm/swappiness 选项，用来调整使用 Swap 的积极
程度。swappiness 的范围是 0-100，数值越大，越积极使用 Swap，也就是更倾向于回收匿名
页；数值越小，越消极使用 Swap，也就是更倾向于回收文件页。

6. 案例

```
# -r表示显示内存使用情况，-S表示显示Swap使用情况
$ sar -r -S

kbcommit，表示当前系统负载需要的内存。它实际上是为了保证系统内存不溢出，对
需要内存的估计值。%commit，就是这个值相对总内存的百分比。
kbactive，表示活跃内存，也就是最近使用过的内存，一般不会被系统回收。
kbinact，表示非活跃内存，也就是不常访问的内存，有可能会被系统回收。
总的内存使用率（%memused）
剩余内存（kbmemfree）不断减少，而缓冲区（kbbuffers）则不断增大
通过 /proc/zoneinfo ，观察剩余内存、内存阈值以及匿名页
和文件页的活跃情况。


# -d 表示高亮变化的字段
# -A 表示仅显示 Normal 行以及之后的 15 行输出
$ watch -d grep -A 15 'Normal' /proc/zoneinfo

```

7. 原理,三种回收方式

    前两种方式，**缓存回收和 Swap 回收**，实际上都是基于 LRU 算法，也就是优先回收不常访问的内存。LRU 回收算法，实际上维护着 active 和 inactive 两个双向链表，
    active 记录活跃的内存页；
    inactive 记录非活跃的内存页。
越接近链表尾部，就表示内存页越不常访问。

```
# grep 表示只保留包含 active 的指标（忽略大小写）
# sort 表示按照字母顺序排序
$ cat /proc/meminfo | grep -i active | sort
Active(anon): 167976 kB
Active(file): 971488 kB
Active: 1139464 kB

```

    第三种方式，OOM 机制按照 oom_score 给进程排序。oom_score 越大，进程就越容易被系统杀死。
    OOM 触发的时机基于虚拟内存。换句话说，进程在申请内存时，如果申请的虚拟内存加上服务器实际已用的内存之和，比总的物理内存还大，就会触发 OOM。
OOM 发生时，你可以在 dmesg 中看到 Out of memory 的信息，从而知道是哪些进程被 OOM 杀死了。比如，你可以执行下面的命令，查询 OOM 日志：

```
$ dmesg | grep -i "Out of memory"
```

##### 4.6 内存分配
    系统调用内存分配请求后，并不会立刻为其分配物理内存，而是在请求首次访问时，通过缺页异常来分配。缺页异常又分为下面两种场景：
        可以直接从物理内存中分配时，被称为次缺页异常。
        需要磁盘 I/O 介入（比如 Swap）时，被称为主缺页异常。

![img](H:\code\learnning\linux-releated\linux性能\企业微信截图_16245816702213.png) 

 ![img](C:\Users\lenovo\AppData\Local\Temp\企业微信截图_16245817045477.png) 

 ![img](H:\code\learnning\linux-releated\linux性能\企业微信截图_16245817207878.png) 

 ![img](H:\code\learnning\linux-releated\linux性能\企业微信截图_16245817521386.png) 





#### 5. 存储-磁盘-linux文件系统

##### 5.1 存储概念

磁盘为系统提供了最基本的持久化存储。
文件系统则在磁盘的基础上，提供了一个用来管理文件的树状结构。

Linux 文件系统为每个文件都分配两个数据结构，索引节点（index node）和目录项（directory entry）。

索引节点同样占用磁盘空间。

目录项，简称为 dentry，用来记录文件的名字、索引节点指针以及与其他目录项的关联关系。多个关联的目录项，就构成了文件系统的目录结构。目录项是由内核维护的一个内存数据结构，所以通常也被叫做目录项缓存。



文件系统又把连续的扇区组成了逻辑块，然后每次都以逻辑块为最小单元，来管理数据。常见的逻辑块大小为 4KB，也就是由连续的 8 个扇区组成。

![img](H:\code\learnning\linux-releated\linux性能\企业微信截图_16254875676017.png) 



磁盘在执行文件系统格式化时，会被分成三个存储区域，超级块、索引节点区和数
据块区。其中，

超级块，存储整个文件系统的状态。
索引节点区，用来存储索引节点。
数据块区，则用来存储文件数据。

Linux 内核在用户进程和文件系统的中间，又引入了一个抽象层，也就是虚拟文件系统 VFS（Virtual File System）。

按照存储位置的不同，这些文件系统可以分为三类。

第一类是基于磁盘的文件系统，也就是把数据直接存储在计算机本地挂载的磁盘中。常见的 Ext4、XFS、OverlayFS 等，都是这类文件系统。
第二类是基于内存的文件系统，也就是我们常说的虚拟文件系统。这类文件系统，不需要任何磁盘分配存储空间，但会占用内存。我们经常用到的 /proc 文件系统，其实就是一种最常见的虚拟文件系统。此外，/sys 文件系统也属于这一类，主要向用户空间导出层次化的内核对象。
第三类是网络文件系统，也就是用来访问其他计算机数据的文件系统，比如 NFS、
SMB、iSCSI 等。

这些文件系统，要先挂载到 VFS 目录树中的某个子目录（称为挂载点），然后才能访问其中的文件。

也就是基于磁盘的文件系统为例，在安装系统时，要先挂载一个根目录（/），在根目录下再把其他文件系统（比如其他的磁盘分区、/proc 文件系统、/sys文件系统、NFS 等）挂载进来。



文件读写方式的各种差异，导致 I/O 的分类多种多样。最常见的有，缓冲与非缓冲 I/O、直接与非直接 I/O、阻塞与非阻塞 I/O、同步与异步 I/O 等。 



第一种，根据是否利用标准库缓存，可以把文件 I/O 分为缓冲 I/O 与非缓冲 I/O。

缓冲 I/O，是指利用标准库缓存来加速文件的访问，而标准库内部再通过系统调度访问文件。

非缓冲 I/O，是指直接通过系统调用来访问文件，不再经过标准库缓存。



第二，根据是否利用操作系统的页缓存，可以把文件 I/O 分为直接 I/O 与非直接 I/O。

直接 I/O，是指跳过操作系统的页缓存，直接跟文件系统交互来访问文件。

非直接 I/O 正好相反，文件读写时，先要经过系统的页缓存，然后再由内核或额外的系统调用，真正写入磁盘。



跳过文件系统读写磁盘的情况，也就是我们通常所说的裸 I/O。



索引节点的容量，（也就是 Inode 个数）是在格式化磁盘时设定好的，一般由格式化工具自动生成。当你发现索引节点空间不足，但磁盘空间充足时，很可能就是过多小文件导致的。

在实际性能分析中，我们更常使用 slabtop ，来找到占用内存最多的缓存类型。



##### 5.2 磁盘i/o工作原理

目录项是一个内存缓存；而超级块、索引节点和逻辑块，都是存储在磁盘中的持久
化数据。



常见磁盘可以分为两类：机械磁盘和固态磁盘。

第一类，机械磁盘，也称为硬盘驱动器（Hard Disk Driver），通常缩写为 HDD。

，连续 I/O 的工作原理。与之相对应的，当然就是随机 I/O，它需要不停地移动磁头，来定位数据位置，所以读写速度就会比较慢。

第二类，固态磁盘（Solid State Disk），通常缩写为 SSD，由固态电子元器件组成。固态磁盘不需要磁道寻址，所以，不管是连续 I/O，还是随机 I/O 的性能，都比机械磁盘要好得多。

，是按照接口来分类，比如可以把硬盘分为 IDE（Integrated Drive Electronics）、SCSI（Small Computer SystemInterface） 、SAS（Serial Attached SCSI） 、SATA（Serial ATA） 、FC（FibreChannel） 等。





IDE 设备会分配一个 hd 前缀的设备名，SCSI 和 SATA 设备会分配一个 sd 前缀的设备名。

这些磁盘，往往还会根据需要，划分为不同的逻辑分区，每个分区再用数字编号。



通用块层，其实是处在文件系统和磁盘驱动中间的一个块设备抽象层



向上，为文件系统和应用程序，提供访问块设备的标准接口；向下，把各种异构的磁盘设备抽象为统一的块设备，并提供统一框架来管理这些设备的驱动程序。



，通用块层还会给文件系统和应用程序发来的 I/O 请求排队，并通过重新排
序、请求合并等方式，提高磁盘读写的效率。

对 I/O 请求排序的过程，也就是我们熟悉的 I/O 调度



，Linux 内核支持四种 I/O 调度算法，分别是 NONE、NOOP、CFQ 以及 DeadLine。



第一种 NONE ，更确切来说，并不能算 I/O 调度算法。因为它完全不使用任何 I/O 调度器，对文件系统和应用程序的 I/O 其实不做任何处理，常用在虚拟机中（此时磁盘 I/O 调度完全由物理机负责）。

第二种 NOOP ，是最简单的一种 I/O 调度算法。它实际上是一个先入先出的队列，只做一些最基本的请求合并，常用于 SSD 磁盘。



第三种 CFQ（Completely Fair Scheduler），也被称为完全公平调度器，是现在很多发行版的默认 I/O 调度器，它为每个进程维护了一个 I/O 调度队列，并按照时间片来均匀分布每个进程的 I/O 请求。

，CFQ 还支持进程 I/O 的优先级调度，所以它适用于运行大量进程的系统，像是桌面环境、多媒体应用等。



最后一种 DeadLine 调度算法，分别为读、写请求创建了不同的 I/O 队列，可以提高机械
磁盘的吞吐量，并确保达到最终期限（deadline）的请求被优先处理。DeadLine 调度算
法，多用在 I/O 压力比较重的场景，比如数据库等。



通用块层，包括块设备 I/O 队列和 I/O 调度器。

设备层，包括存储设备和相应的驱动程序，负责最终物理设备的 I/O 操作。



使用率，是指磁盘处理 I/O 的时间百分比。

饱和度，是指磁盘处理 I/O 的繁忙程度。

IOPS（Input/Output Per Second），是指每秒的 I/O 请求数。

吞吐量，是指每秒的 I/O 请求大小。

响应时间，是指 I/O 请求从发出到收到响应的间隔时间。



用性能测试工具 fio ，来测试磁盘的 IOPS、吞吐量以及响应时间等核心
指标。



 ![img](H:\code\learnning\linux-releated\linux性能\企业微信截图_16254883048336.png) 

%util ，就是我们前面提到的磁盘 I/O 使用率；
r/s+ w/s ，就是 IOPS；
rkB/s+wkB/s ，就是吞吐量；
r_await+w_await ，就是响应时间。



我推荐另一个工具， iotop。它是一个类似于 top 的工具，你可以按照 I/O
大小对进程排序，然后找到 I/O 较大的那些进程。





你可以用 iostat ，确认是否有 I/O 性能瓶颈。再用 strace 和 lsof ，来定位应用程序以及它正在写入的日志文件路径。最后通过应用程序的接口调整日志级别，完美解决 I/O 问题。



通过 df 我们知道，系统还有足够多的磁盘空间。

，我们可以先用 top 来观察 CPU 和内存的使用情况，然后再用 iostat 来观察磁盘的 I/O 情况。



介绍一个新工具， filetop，基于 Linux 内核的eBPF（extended Berkeley Packet Filters）机制，主要跟踪内核中文件的读写情况，并输出线程 ID（TID）、读写大小、读写类型以及文件名称。

```
#
切换到工具目录
$ cd /usr/share/bcc/tools
# -C
选项表示输出新内容时不清空屏幕
$ ./filetop -C



你会看到，filetop 输出了 8 列内容，分别是线程 ID、线程命令行、读写次数、读写的大小（单位 KB）、文件类型以及读写的文件名称。
```

filetop 只给出了文件名称，却没有文件路径。

我再介绍一个好用的工具，opensnoop 。它同属于 bcc 软件包，可以动态跟踪内核中的open 系统调用。这样，我们就可以找出这些 txt 文件的路径。





观察 top 的输出，我们发现，两个 CPU 的 iowait 都比较高，特别是 CPU0，iowait 已经超过 60%。而具体到各个进程， CPU 使用率并不高，最高的也只有 1.7%。



然后，执行下面的 iostat 命令，看看有没有 I/O 性能问题：



，MySQL 是一个多线程的数据库应用，为了不漏掉这些线程的数据读取情况，你要
记得在执行 stace 命令时，加上 -f 参数：

无非就是，先用 strace 确认它是不是在写文件，再用 lsof 找出文件描述符对应的文件即可。

```
# -t表示显示线程
，-a表示显示命令行参数

$ pstree -t -a -p 27458



$ lsof -p 27458
COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME
...
mysqld 27458 999 38u REG 8,1 512440000 2601895 /var/lib/mysql/test/products

```



从输出中可以看到， mysqld 进程确实打开了大量文件，而根据文件描述符（FD）的编号，我们知道，描述符为 38 的是一个路径为/var/lib/mysql/test/products.MYD 的文件。

到，那就是在 MySQL 命令行界面中，执行 show processlist 命令，
来查看当前正在执行的 SQL 语句。



##### 5.3 案例分析

```
# -f 表示跟踪子进程和子线程，-T 表示显示系统调用的时长，-tt 表示显示跟踪时间
$ strace -f -T -tt -p 9085


你还可以用 strace ，观察这个系统调用的执行情况。
比如通过 -e 选项指定fdatasync
$ strace -f -p 9085 -T -tt -e fdatasync

从这里你可以看到，每隔 10ms 左右，就会有一次 fdatasync 调用，并且每次调用本身也要消耗 7~8ms。
```



```
#
下面的命令用到的 nsenter 工具，可以进入容器命名空间。
app
由于这两个容器共享同一个网络命名空间，所以我们只需要进入\的网络命名空间即可
$ PID=$(docker inspect --format {{.State.Pid}} app)
# -i 表示显示网络套接字信息
$ nsenter --target $PID --net -- lsof -i

```



![img](H:\code\learnning\linux-releated\linux性能\企业微信截图_16257905929796.png) 





第一，在文件系统的原理中，我介绍了查看文件系统容量的工具 df。它既可以查看文件系统数据的空间容量，也可以查看索引节点的容量。至于文件系统缓存，我们通过
/proc/meminfo、/proc/slabinfo 以及 slabtop 等各种来源，观察页缓存、目录项缓
存、索引节点缓存以及具体文件系统的缓存情况。

第二，在磁盘 I/O 的原理中，我们分别用 iostat 和 pidstat 观察了磁盘和进程的 I/O 情况。它们都是最常用的 I/O 性能分析工具。通过 iostat ，我们可以得到磁盘的 I/O 使用率、吞吐量、响应时间以及 IOPS 等性能指标；而通过 pidstat ，则可以观察到进程的 I/O吞吐量以及块设备 I/O 的延迟等。

第三，在狂打日志的案例中，我们先用 top 查看系统的 CPU 使用情况，发现 iowait 比较高；然后，又用 iostat 发现了磁盘的 I/O 使用率瓶颈，并用 pidstat 找出了大量 I/O 的进程；最后，通过 strace 和 lsof，我们找出了问题进程正在读写的文件，并最终锁定性能问题的来源——原来是进程在狂打日志。

第四，在磁盘 I/O 延迟的单词热度案例中，我们同样先用 top、iostat ，发现磁盘有 I/O瓶颈，并用 pidstat 找出了大量 I/O 的进程。可接下来，想要照搬上次操作的我们失败了。在随后的 strace 命令中，我们居然没看到 write 系统调用。于是，我们换了一个思路，用新工具 filetop 和 opensnoop ，从内核中跟踪系统调用，最终找出瓶颈的来源。

最后，在 MySQL 和 Redis 的案例中，同样的思路，我们先用 top、iostat 以及 idstat
，确定并找出 I/O 性能问题的瓶颈来源，它们正是 mysqld 和 redis-server。随后，我们又用 strace+lsof 找出了它们正在读写的文件



 ![img](H:\code\learnning\linux-releated\linux性能\企业微信截图_16257907709794.png) 



 ![img](H:\code\learnning\linux-releated\linux性能\企业微信截图_16257908083610.png) 



**分析思路**

1. 先用 iostat 发现磁盘 I/O 性能瓶颈；
2. 再借助 pidstat ，定位出导致瓶颈的进程；
3. 随后分析进程的 I/O 行为；
4. 最后，结合应用程序的原理，分析这些 I/O 的来源。



 ![img](H:\code\learnning\linux-releated\linux性能\企业微信截图_16257908709466.png) 





##### 5.4 磁盘I/O性能测试

fio（Flexible I/O Tester）正是最常用的文件系统和磁盘 I/O 性能基准测试工具。它提供了大量的可定制化选项，可以用来测试，裸盘或者文件系统在各种场景下的 I/O 性能，包括了不同块大小、不同 I/O 引擎以及是否使用缓存等场景。

```

# 随机读
fio -name=randread -direct=1 -iodepth=64 -rw=randread -ioengine=libaio -bs=4k -size=1G -
# 随机写
fio -name=randwrite -direct=1 -iodepth=64 -rw=randwrite -ioengine=libaio -bs=4k -size=1G
# 顺序读
fio -name=read -direct=1 -iodepth=64 -rw=read -ioengine=libaio -bs=4k -size=1G -numjobs=
# 顺序写
fio -name=write -direct=1 -iodepth=64 -rw=write -ioengine=libaio -bs=4k -size=1G -numjob

```



在这其中，有几个参数需要你重点关注一下。

direct，表示是否跳过系统缓存。上面示例中，我设置的 1 ，就表示跳过系统缓存。
iodepth，表示使用异步 I/O（asynchronous I/O，简称 AIO）时，同时发出的 I/O 请
求上限。在上面的示例中，我设置的是 64。
rw，表示 I/O 模式。我的示例中， read/write 分别表示顺序读 / 写，而
randread/randwrite 则分别表示随机读 / 写。
ioengine，表示 I/O 引擎，它支持同步（sync）、异步（libaio）、内存映射
（mmap）、网络（net）等各种 I/O 引擎。上面示例中，我设置的 libaio 表示使用异步 I/O。
bs，表示 I/O 的大小。示例中，我设置成了 4K（这也是默认值）。
filename，表示文件路径，当然，它可以是磁盘路径（测试磁盘性能），也可以是文件路径（测试文件系统性能）。示例中，我把它设置成了磁盘 /dev/sdb。不过注意，用磁盘路径测试写，会破坏这个磁盘中的文件系统，所以在使用前，你一定要事先做好数据备份。





fio 支持 I/O 的重放。

```
# 使用blktrace跟踪磁盘I/O，注意指定应用程序正在操作的磁盘
$ blktrace /dev/sdb
#查看blktrace记录的结果
# ls
sdb.blktrace.0
sdb.blktrace.1
#
将结果转化为二进制文件
$ blkparse sdb -d sdb.bin
#使用fio重放日志
$ fio --name=replay --filename=/dev/sdb --direct=1 --read_iolog=sdb.bin
```



这样，我们就通过 blktrace+fio 的组合使用，得到了应用程序 I/O 模式的基准测试报告。

i/o性能优化

应用程序优化

文件系统优化

磁盘优化



