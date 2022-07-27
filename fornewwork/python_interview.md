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