## 一、linux相关



### 1. 常用linux系统调用

系统调用（System Call）是操作系统为在用户态运行的进程与**硬件设备（如CPU、磁盘、打印机等）进行交互**提供的一组接口。当用户进程需要发生系统调用时，CPU 通过软中断切换到内核态开始执行内核系统调用函数

**系统调用在内核里的主要用途**。虽然给出了数种分类，不过总的概括来讲系统调用主要在系统中的用途无非以下几类：

- **控制硬件**——系统调用往往作为硬件资源和用户空间的抽象接口，比如读写文件时用到的write/read调用。

- **设置系统状态或读取内核数据**——因为系统调用是用户空间和内核的唯一通讯手段[2]，所以用户设置系统状态，比如开/关某项内核服务（设置某个内核变量），或读取内核数据都必须通过系统调用。比如getpgid、getpriority、setpriority、sethostname

- **进程管理**——一系列调用接口是用来保证系统中进程能以多任务，在虚拟内存环境下得以运行。比如 fork、clone、execve、exit等

**什么功能应该实现在内核而不是在用户空间**

- 服务必须获得内核数据，比如一些服务必须获得中断或系统时间等内核数据。

- 从安全角度考虑，在内核中提供的服务相比用户空间提供的毫无疑问更安全，很难被非法访问到。

- 从效率考虑，在内核实现服务避免了和用户空间来回传递数据以及保护现场等步骤，因此效率往往要比实现在用户空间高许多。比如,httpd等服务。

- 如果内核和用户空间都需要使用该服务，那么最好实现在内核空间，比如随机数产生。



信号：kill、signal/sigpending/sigsuspend/

管道：pipe

socket控制：socket/bind/connect/accept/send/listen/select/shutdown/setsockopt

用户管理：getuid/setuid/getgid/setgid/

网络管理：gethostname/sethostname/setdomainname/getdomainname/gethostid/sethostid

系统控制：reboot/time/uname/

文件系统控制：open/creat/close/read/write/readv/writev/pread/poll/truncate/access/stat/chown/chmod/chdir/rename/mkdir/mount/unmount/

进程控制：fork/clone/exit/execve/setpgid/getpid/getppid/nice/pause/ptrace/wait/wait3/waitpid/setsid/getsid

#### open

在用户态使用open()时，必须向该函数传入文件路径和打开权限。这两个参数传入内核后，内核首先检查这个文件路径存在的合法性，同时还需检查使用者是否有合法权限打开该文件。如果一切顺利，那么内核将对访问该文件的进程创建一个file结构。

在用户态，通常open()在操作成功时返回的是一个非负整数，即所谓的文件描述符（fd，file descriptor）；并且，用户态后续对文件的读写操作等都是通过fd来完成的。由此可见fd与file结构在内核中有一定的关联。

内核使用进程描述符task_struct来描述一个进程，而该进程所有已打开文件对应的file结构将形成一个数组files（其为files_struct结构），内核向用户返回的fd便是该数组中具体file结构的索引。默认情况下，每个进程创建后都已打开了标准输入文件、标准输出文件、标准错误文件，因此他们的文件描述符依次为0、1和2。



参考连接：https://www.cnblogs.com/shijiaqi1066/p/5749030.html





### 2. 进程、线程、协程







### 3. poll/epoll/select





常见进程调度算法





操作系统如何申请及管理内存





同步、阻塞、异步、并发、非阻塞、并行











## 二、网络相关





### 2.1. 三次握手、四次挥手

为什么是三次握手、不是两次握手，

参考-learnning\jike_qutanwangluoxieyi/网络学习





http与https





tcp与udp特点，区别



http网页，从请求到响应。 都走了那些步骤、（dns）





dns



http keepalive 和 tcp  keepalive





syn攻击、半连接



进程间如何通信



python的底层网络交互模块有哪些



OSI七层协议



## 三、数据库相关

##### mysql



mysql引擎，各个引擎之间有什么区别



数据库事务，及其特性



数据库事务隔离级别有哪些、区别与特点



死锁发生的情况，如何解决



索引的原理

mysql  B+索引、优缺点

mysql索引类型

聚簇索引和非聚簇索引

唯一索引和普通索引区别，使用索引有哪些优缺点

myql索引什么情况下会失效





mysql主从同步机制



数据库的ACID



如何开启慢查询日志



数据库的脏读、幻读、幻行的原理、发生场景，及解决方式





serializable 序列化、最好的事务级别



乐观锁、悲观锁



sql注入原理，如何在代码层面防止sql注入



数据库的优化













##### redis

redis单进程？多个客户端是多进程么



redis如何解决雪崩、缓存击穿、



redis 持久化中rdb和 aof方案的优缺点











## 四、python相关

restfull和rpc区别与联系



xreadlines（底层迭代原理）  readline ()



is 和 ==区别



字典按值排序（sorted(dict.iterms(), key=lambda x: x[1],）



翻转字符串  s = "w3423", s[::-1]



list1中age按由大到小排序（list1=[{"age": 5}, {"age": 67}, {"age": 56}],    sorted(list1, key=lambda x:x['age'], reverse=True)）



lista=[1,2,43,7],  lista[10:]



两个列表，找出相同元素和不同元素

list1= [1,2 ,4,6, 67],  list2=[3, 2, 43, 76]

set1=set(list1) , set2=set(list2), set1&set2,  set1^set2



什么是反射，反射应用场景





深拷贝和浅拷贝



简述`__new__和————init--`的区别



GIL对python性能的影响



双下划线和单下划线的区别





with语句，如何构造，原理



单例模式，优缺点，如何实现



json序列化时，会遇到中文转unicode，想保留中文如何做（json.dumps({"dd", "你好"}， ensure_ascii=False)）



mro



C3算法



判断邮箱合法，re使用



python函数调用时候参数的传递是值传递还是引用传递



递归函数停止的条件



python递归的最大层数



列表推导式和生成器表达式 输出结果分别是什么

```
[i % 2 for i in range(10)]

(i % 2 for i in range(10))
```



什么是闭包



## 五、框架相关（django）



python三大框架各自应用场景



uWSGI 和nginx的理解

uwsgi  区别uWSGI



### 5.1 django



手动删除了表，导致，django迁移失败原因及解决办法

django中 Model    ForeignKey字段的on_delete参数作用



基于django使用ajax发送post请求时，有哪种方法携带csrftoken



django  FBV  CBV



django的request对象是什么时候创建的



django请求的生命周期



django中如何在model保存前做一定的固定操作，比如写一句日志（signal Dispatcher）



django中间件的使用



django  ORM查询中  select_related和prefetch_related的区别





cookie和session的区别





celery分布式队列





## 六、其他



自学python最大的困难



