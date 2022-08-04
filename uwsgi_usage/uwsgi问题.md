





## 1. uwsgi满的问题



### [uwsgi listen queue of socket full 及 broken pipe 错误排查及解决方法](http://www.beiliangshizi.com/?p=822)



某天突然收到nginx检测到上游uwsgi服务中断的报警，然后过一段时间，uwsgi又自动恢复正常，这种情况偶尔发生，已经发生过几次，我想有必要去深究一下

uwsig错误日志的关键字：

```
*** uWSGI listen queue of socket ":6000" (fd: 6) full !!! (1024/1024) ***
*** HARAKIRI ON WORKER 13 (pid: 21576, try: 1) ***
- HARAKIRI [core 0] 10.82.156.14 - POST /api/distrib/report/exposure/?cuid=EA3E5CBAE69AA599FDFBB4F112B08ECC&ovr=6.0.1&os_level=23&device
uwsgi_response_write_body_do(): Broken pipe [core/writer.c line 341] during GET /api/recommend/index 
- HARAKIRI !!! end of worker 2 status !!! 
 Respawned uWSGI worker 2 (new pid: 952) 
uwsgi_response_write_body_do(): Broken pipe [core/writer.c line 341] during GET 
 DAMN ! worker 17 (pid: 21591) died, killed by signal 9 :( trying respawn ...
 *** uWSGI listen queue of socket ":6000" (fd: 6) full !!! (1025/1024)
```

### broken pipe 的出现

```
uwsgi_response_write_body_do(): Broken pipe [core/writer.c line 341] during GET /api/recommend/index 
```

broken pipe是send、write、writev时都有可能产生的错误，当一端在写另一端关闭了的连接的时候，就会产生broken pipe的错误。所以很显然，uwsgi在向nginx write之前，nginx已经关闭了连接，为什么？因为超时了。
nginx跟uwsgi 之间的连接有一个参数`uwsgi_read_timeout`默认是60秒，这个参数的意思是nginx从uwsgi读取response的超时时间，如果在这个时间内，uwsgi没有返回任何响应给nginx，那么nginx跟uwsgi的连接就会关闭。nginx此时就会报错

```
   upstream timed out (110: Connection timed out) while reading response header from upstream
```

那么问题是，为什么uwsgi会在60秒内都没有返回相应给nginx呢？可能的原因如下：

- 有某个请求一直阻塞了，没有做超时的限制，比如业务里面需要请求第三方接口，这时接口出了问题
- 并发请求量过大，超出了uwsgi的listen的backlog限制。

### 请求被阻塞，响应时间过慢

看看我们的uwsgi日志，出现了harakiri

```
- HARAKIRI [core 0] 10.82.156.14 - POST /api/distrib/report/exposure/
- HARAKIRI !!! worker 13 status !!!
Respawned uWSGI worker 13 (new pid: 1075)
```

**harakiri**这个选项会设置uwsgi harakiri(切腹，重启)进程的超时时间。如果一个请求花费的时间超过了这个harakiri超时时间，那么这个请求都会被丢弃，并且当前处理这个请求的工作进程会被回收再利用（即重启）。
我们的uwsgi配置了harakiri =30 意味着如果进程30秒内没有完成任务，正常响应的话，uwsgi就会杀掉这个uwsgi子进程，而出现的这个日志，说明我们的请求，确实超过30秒了，导致进程被杀掉。然后uwsgi就会重新生成子进程进行工作。这就是紧接着`Respawned uWSGI worker 1`日志出现的原因

我去代码检查了下，是因为有一个地方调用了第三方的接口，而发起请求的代码没有做超时异常处理
请求外部接口时没有设置timeout参数，所以会一直阻塞下去，从而导致其他请求也被阻塞了

uwsgi在自我重启进程的过程中，感觉应该没什么问题，但是可怕的是，过了一段时间，ngxin检测到uwsgi已经完全不能工作了
uwsgi出现了错误日志：

```
 uWSGI listen queue of socket ":6000" (fd: 6) full !!! (1025/1024)
```

这个错误代表，请求的连接数已经超过了uwsgi 设置的listen()最多的backlog数量了，而这个backlog代表的是什么呢？

### listen()的参数backlog参数

先看看官方对这个listen()的解释：

int listen (int sockfd, int backlog)
To understand the backlog argument, we must realize that for a given listening socket, the kernel maintains two queues:

- An incomplete connection queue, which contains an entry for each SYN that has arrived from a client for which the server is awaiting completion of the TCP three-way handshake. These sockets are in the SYN_RCVD state (Figure 2.4).
- A completed connection queue, which contains an entry for each client with whom the TCP three-way handshake has completed. These sockets are in the ESTABLISHED state (Figure 2.4).

再看看一个TCP三次握手的图：

![img](http://upload-images.jianshu.io/upload_images/1446087-12016d25ae0164f3.png?imageMogr2/auto-orient/strip|imageView2/2/w/641/format/webp)

我们分析下这个过程：
1、client发送SYN到server，将状态修改为SYN_SEND，如果server收到请求，则将状态修改为SYN_RCVD，并把该请求放到syns queue队列中。
2、server回复SYN+ACK给client，如果client收到请求，则将状态修改为ESTABLISHED，并发送ACK给server。
3、server收到ACK，将状态修改为ESTABLISHED，并把该请求从syns queue中放到accept queue。

所以在linux系统内核中对一个监听的socket维护了两个队列：syns queue和accept queue

- syns queue是用于保存半连接状态的请求
- accept queue 用于保存全连接状态的请求，其大小通过`/proc/sys/net/core/somaxconn`指定，在使用listen函数时，内核会根据传入的backlog参数与系统参数somaxconn，取二者的较小值。

而我们的uwsgi 配置里面配置了listen = 1024， 上面的错误日志显示`uWSGI listen queue of socket ":6000" (fd: 6) full !!! (1025/1024)`
说明这个请求进来的socket已经刚好超过了我们配置的1024backlog大小。
当这两个队列的总量超过 backlog 后，新来的 HTTP 连接三次握手的 SYN 包，服务器就不会理会了，直接丢弃。
所以nginx 转发给uwsgi的请求连接数已经超过了uwsgi 的1024后，uwsgi不理会之后的连接，nginx就会报错`resource temporarily unavailable` 然后返回502 Bad Gateway ,具体的nginx日志是会这样报错：

```
 [error] connect() to unix:///var/uwsgi/uwsgi.sock failed (11: Resource temporarily unavailable) while connecting to upstream, client: xxx.xxx.xx, server:
```

### 问题导致的结果

我们的服务请求是源源不断的，一分钟150K的请求量，uwsgi是process_based 模型，一个请求过来就用一个进程处理，如果一个进程被阻塞了，请求总量不变，势必会使得更多的请求分到其他的进程，而其他进程又碰到同一个阻塞的请求，如此循环，最后全部进程都不可用。

对uwsgi连接进来了会保存到accept queue队列里面，这个队列最多可以放进我们配置的1024个连接，uwsgi处理完一个就从队列里取出连接进行处理，但是当一个连接的请求阻塞了，出现以下结果：

- uwsgi来不及取出队列里面的剩余的连接，超过30秒后，uwsgi就会这个进程杀掉
- nginx来跟uwsgi的连接60秒都没响应，就会根据关闭连接
- ngxin继续转发请求到uwsgi，而uwsgi的socket队列又因为请求阻塞不断累积，导致socket队列爆了，直接抛弃nginx转发的请求，从而使得nginx报错`502 Bad Gateway Resource temporarily unavailable` 而uwsgi报错 `uWSGI listen queue of socket ":6000" (fd: 6) full !!!`
- 而uwsgi socket队列里面的连接，在uwsgi处理完上一个之后，不慌不忙的继续从accept queue取出连接，继续工作的时候，工作完准备把response发送给nginx, 此时nginx已经等到黄花菜都凉过了read_time的超时间，关闭跟uwsgi的连接了。uwsgi就得到一个错误 `Broken pipe [core/writer.c line 341] during GET /api/recommend/index`

所以，这一连串发生的现象就得以解释了！

### 增加listen的backlog能解决吗？

对于uwsgi 来说，backlog的值默认是100， 也就是配置项的listen=100，
而内核的这个backlog参数默认是128，可以通过命令来查看

```
cat /proc/sys/net/core/somaxconn 
```

或者 查看所有内核参数

```
sysctl -a 
sysctl -a|grep somaxconn
- 修改内核参数
$echo 200 > /proc/sys/net/core/somaxconn
or $ sysctl -w net.core.somaxconn=200
```

那么我们碰到这种情况，通过增加listen的backlog 参数，或者增加内核的somaxconn就能解决问题吗？
回答：增加可以，但不可以只依赖增加backlog
我们根据上面的分析就可以知道，uwsgi就是因为有某些操作阻塞了，或者长时间占用进程，导致他来不及取出accept queue的连接出来处理，等他处理完上一个请求，再来从队列取出，这时可能nginx就已经超时，或者uwsgi的harakiwi超时已经把进程杀掉了。在这种情况下你继续增加accept queue让uwsgi能接收更多的连接，也是无补于事的，因为队列里的连接已经处理不过了，你增加队列长度，他也是处理不过来！
增加accept queue能有效提高性能的情况下，是uwsgi的请求都能快速处理，能快速消费掉socket队列的情况下，比如从100->200 增加这样是有用的。
所以我们要根据实际情况，分析uwsgi的瓶颈到底是在哪里，盲目增加listen的backlog不一定有用！

### 关于nginx的504 timeout

- uwsgi是**process-based模型**的，一个进程同步的处理一个请求，出现了阻塞操作把uwsgi进程给堵了，nginx等不了返回响应，超时关闭连接，造成uwsgi return response的时候往已经关闭的连接中写，出现上述日志中描述`broken pipe`的那种情况。而nginx就会出现504 gate way timeout
- nginx的504 timeout 并不一定是某个请求已经超过了nginx的xxx read timeout，也有可能是并发量太大，请求连接数超过uwsgi的backlog导致的。比如uwsgi的backlog是100， 而每个请求花时4秒，开4个进程，也就是每分钟能处理60个请求，但此时如果同时并发200个请求，nginx就会转发200个请求给uwsgi，uwsgi的socket队列只能放进100个socket，多出的100个直接丢弃，nginx返回resource not avaliable 错误。
  而uwsgi 一分钟只能处理60个请求，队列里面还剩下40个请求，怎么办？一分钟后处理，但此时nginx已经等待1分钟，关闭了连接，返回504超时。此时uwsgi再返回响应给nginx就会出现broken pipe错误
- 一般这样的请求，每个才3-5秒钟，nginx默认的read time out要60秒，我们直观觉得不会超时，根据上面的分析，就知道当请求量过大的时候，就会出现

------

> 以上均转自[《uwsgi listen queue of socket full 及 broken pipe 错误排查及解决方法》](https://www.jianshu.com/p/d7f63d185c0e)，一顿操作最后没有解决问题，最终自己查询结合nginx和uwsgi的错误日志，尝试自行修改配置文件后解决问题，记录如下：

\1. 调整nginx中events配置的worker_connections的大小，设置工作进程可以打开的最大并发连接数，我从1024直接调到10240。应该记住，这个数字包括所有连接（例如与代理服务器的连接等，有反向代理链接数就会有相应增加），而不仅仅是与客户端的连接。另一个考虑因素是，同时连接的实际数量不能超过打开文件的最大数量的当前限制，可以通过worker_rlimit_nofile更改。

更改RLIMIT_NOFILE工作进程的最大打开文件数量限制（）。用于在不重新启动主进程的情况下增加限制。

```
worker_rlimit_nofile 65535;
events {
    worker_connections  10240;
}
```

在Linux下面部署应用的时候，有时候会遇上Socket/File: Can’t open so many files的问题，因为Linux有文件句柄限制的，默认仅仅为1024，所以我们需要对它进行一定的修改，才能支持nginx的连接数。
我们可以使用ulimit -a命令查看Linux相关限制
对于临时测试我们可以使用ulimit -n Number 修改最大文件句柄限制，但该种修改方式仅仅对当前session有效。

永久生效方案
vi /etc/security/limits.conf，在limits.conf中添加以下参数
soft nofile 40960
hard nofile 65536

参数：
代表所有用户有效
soft：软限制，超过会报warn
hard：实际限制
nofile：文件句柄参数
number：最大文件句柄数

修改完成保存后，退出ssh再次登录，使用ulimit -n 就可以看到open files 参数已经改变成功了。

\2. uwsgi的配置中，listen从1000直接上调到2W。uwsgi是同步阻塞的，单纯提高并发的话可以将listen的值设得高一些（一般1024），listen是指排队的请求。这里要将参数net.core.somaxconn 设得比listen高。其实listen参数变高只能提高并发，并不能提高你的生产效率。



## 2. uwsgi死锁，进程杀死重启

deadlock-detector,  process holding o robust mutex died, recovering

```
he "problem" is in the multiple threads usage, you spawn multiple of
them, so the max_requests check could happens in multiple threads once.

The thunder-lock is a performance-only measure, so even if it does not
work flawlessly for a single request, it will not hurt for sure and the
deadlock detector will fix it in time for the next request.

The right fix will be acquiring the thunder lock before destroying the
proces but, wait, we are about to destroy it so we will not be able to
release the lock as we are dead :)

At this point i think following an optimistic approach, and letting the
deadlock-detector clearing the situation, is the best thing we can do.

So yes, you are safe.
```

是由于 uwsgi.ini中的thunder-lock的配置，该配置是为了解决进程的惊群效应，





