# [nginx 反向代理配置(一)](https://www.cnblogs.com/leeyongbard/p/10883346.html)

   **文章参考：https://blog.csdn.net/physicsdandan/article/details/45667357**

   **什么是代理？**

   代理在普通生活中的意义就是本来应该你做的事情，你让别人代你做了，那么那个帮你做的人就是你的代理。和在计算机网络中代理的概念差不多，

本来是要客户端做的网络访问，现在移交给另外一台机器做，那么那个机器就被称为代理服务器，代理服务器帮你访问。过程如下：

   正常情况：

   client-(send request)->server

   代理情况：

   client-(send request)->client proxy(send request)->server

   **什么是反向代理？**

   反向代理在计算机网络中是指这么一个过程，一般来说正向代理是客户端找人来代理把自己的请求转发给服务器，但是如果是反向代理，找代理的人不再

是客户端，而是服务端这边把自己接受的请求转发给背后的其他机器。

   反向代理情况：

   client-(send request)->server proxy(send request)->other server

   **下面看一个示例：**

```
#① part start
#运行nginx进程的账户
user www;
#
worker_process 1;
error_log /var/log/nginx/error.log
pid /var/run/nginx.pid;
 
events{
    use epoll;
    worker_connections 1024;
}
 
http{
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    access_log  /var/log/nginx/access.log  main;
    #
    sendfile        on;
    #
    keepalive_timeout  65;
    gzip  on;
 
    index   index.html index.htm;
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
    #② part start
    # 定义上游服务器列表组
    upstream web1 {
        server 127.0.0.1:111 weight=1;
        server 127.0.0.1:222 weight=1;
    }
    upstream web2 {
        server 127.0.0.2:111 weight=1;
        server 127.0.0.2:222 weight=6;
        server 127.0.0.2:333 weight=7;
    }
    #定义一个服务器，其监听80端口，配置的域名是www.company.com
    server{
        listen 80;
        # using www  domain to access the main website
        server_name www.company.com;
        access_log  /var/log/nginx/www.log
 
        location / {
            root /home/website_root;
 
        }
    }
    #③ part start
    #定义第二个服务器，其同样监听80端口，但是匹配域名是web.company.com
    server{
        listen 80;
        # using web sub domain to access
        server_name web.company.com;
        access_log  /var/log/nginx/web_access.log
 
        location / {
            root /home/web2_root;
            proxy_pass http://127.0.0.1:8080/web/;
            proxy_read_timeout 300;
            proxy_connect_timeout 300;
            proxy_redirect     off;
 
            proxy_set_header   X-Forwarded-Proto $scheme;
            proxy_set_header   Host              $http_host;
            proxy_set_header   X-Real-IP         $remote_addr;
        }
    }
    #定义第三个服务器，其同样监听80端口，但是匹配域名是web1.company.com，并把请求转发到web1上游服务
    server{
        listen 80;
        # using web1 sub domain to access
        server_name web1.company.com;
        access_log  /var/log/nginx/web1_access.log
 
        location / {
            root /home/web1_root;
            proxy_pass http://web1;
            proxy_read_timeout 300;
            proxy_connect_timeout 300;
            proxy_redirect     off;
 
            proxy_set_header   X-Forwarded-Proto $scheme;
            proxy_set_header   Host              $http_host;
            proxy_set_header   X-Real-IP         $remote_addr;
        }
    }
        #定义第三个服务器，其同样监听80端口，但是匹配域名是web2.company.com，并把请求转发到web2上游服务
    server{
        listen 80;
        # using web2 sub domain to access
        server_name web2.company.com;
        access_log  /var/log/nginx/web2_access.log
 
        location / {
            root /home/web2_root;
            proxy_pass http://web2;
            proxy_read_timeout 300;
            proxy_connect_timeout 300;
            proxy_redirect     off;
 
            proxy_set_header   X-Forwarded-Proto $scheme;
            proxy_set_header   Host              $http_host;
            proxy_set_header   X-Real-IP         $remote_addr;
        }
    }
}
```

 **这个示例都做了什么？**

​    1.第一部分，定义了 nginx 通用规则

​    2.第二部分，开始定义上游服务器组

​    3.第三部分，开始定义 server，并指定如何使用第二部分定义的 upstream

​    总体来说上面的示例提供了四个服务，www、web、web1、web2 4个网站，这个例子很适合一台机器，但是又想避免访问 url 中带有端口号，统一使用

域名方式访问。4个网站都监听 80 端口，但是分配不同的二级域名即可。这就需要 nginx 反向代理，具体如何实现，我们重新举一个例子，如下所示：

​    (1) 只有一台服务器，一个 IP，一个域名 www.xsgzs.com

​    (2) 这台服务器上有多个应用运行在不同端口，如：

​      127.0.0.1：4000 运行着一个 博客应用

​      127.0.0.1：3009 运行着一个博客后台管理系统

​      我们不期望在访问的 url 中携带有端口号，统一使用域名方式访问，可以为运行在不同端口号的应用分配二级域名，同时把二级域名都解析到 80 端口，

但是转发到不同的端口去，希望访问 www.blog.xsgzs.com 能访问到 127.0.0.1:4000 ，访问 www.admin.xsgzs.com 能访问到 127.0.0.1:3009 

​    具体步骤：

​    (1) 在 nginx.conf 文件新增 upstream server(上游服务器)

```
upstream blog.xsgzs {
      server 127.0.0.1:4000
}
 
upstream admin.xsgzs {
      server 127.0.0.1:3009
}
```

 　　(2) 在配置文件中添加 server，都监听 80 端口 

```
server {     
                              listen      80;     
                              server_name www.blog.xsgzs.com;     
                              location / {     
                                          proxy_pass http://blog.xsgzs;     
                              }     
                              error_page  500 502 503 504  /50x.html;   
                              location = /50x.html {       
                                              root  html;     
                              }
 }
 
 server {     
                              listen      80;     
                              server_name www.admin.xsgzs.com;     
                              location / {     
                                      proxy_pass http://admin.xsgzs;     
                              }     
                              error_page  500 502 503 504  /50x.html;   
                              location = /50x.html {       
                                          root  html;     
                                }
 }
```

 **为什么需要反向代理？**

​    作为服务端代理，自然是一台机器处理不过来了，需要转发、分散请求给其他服务器做。下面列出一些适用场景：

​    1.负载均衡：

​    上面的例子1中 web1 和 web2 上游服务器组都使用了负载均衡，把请求转发向一组服务器。具体转发给哪台服务器，nginx 提供了多种负载均衡策略，上面使用的是加权方式

​    2.一个域名，多个网站。 如上面的例2

​    3.反向代理另一个作用就是隐藏后面的真实服务，以此达到一定的安全性

​    **仔细讲解各个模块**

​    nginx 配置文件主要分为六个区域

```
(1) main 全局设置
(2) events (nginx 工作模式)
(3) http (http设置)
(4) server (主机设置)
(5) location (URL匹配)
(6) upstream (负载均衡服务器设置)
```

　**main 模块(全局设置)**

​    下面是一个 main 区域，它是一个全局设置

```
user nobody nobody;
worker_processes 2;
error_log  /usr/local/var/log/nginx/error.log  notice;
worker_rlimit_nofile 1024;
```

　　user 用来设置运行 nginx 服务器的用户或用户组，语法格式：

```
user user [group]
```

user ， 指定可以运行 nginx 服务器的用户

​    group，可选项，指定可以运行 nginx 服务器的用户组

​    注：只有被指定的用户或用户组才有权限启动 nginx 进程，如果是其他用户 (test_user) 尝试启动 nginx 进程，将会报错

```
nginx: [emerg] getpwnam("test_user") failed (2:No such file or directory) in /Nginx/conf/nginx.conf:2
```

从上面的报错信息中可以知道，nginx 无法运行的原因是查找 test_user 失败，引起错误的原因在 nginx.conf 文件第二行即

配置运行 nginx 服务器的用户或用户组

​    如果希望所有的用户或用户组都有权限启动 nginx 进程，有两种方式：一是将此行指令注释掉、而是将用户或用户组设置

为 nobody，这也是 user 指令的默认值

​    worker_processes 用来指定 nginx 要开启的子进程数目

​    worker prcocess 是 nginx 服务器实现并发处理的关键所在，从理论上来说，worker process 的值越大，可以支持的并发处理量越大，但实际上它还要受到来自软件本身、

操作系统本身资源和能力、硬件设备(如：CPU 和 磁盘驱动器)等制约，其语法格式：

```
worker_processes number | auto
```

　number，来指定 nginx 要开启的子进程数目

​    auto，nginx 自动检测

​    在默认配置文件中，number = 1，启动 nginx 服务器之后，使用以下命令可以看到此时的 nginx 除了主进程 master process 之外还生成了一个 worker process，在这里我将

number 指定为 4 ，除了主进程 master process 之外还生成了 4 个 worker process

![img](https://img2018.cnblogs.com/blog/1302542/201905/1302542-20190518112206210-889488844.png) 

 在这里还有一点需要注意的地方：

​    worker_processes 指的是操作系统启动多少个工作进程运行 nginx，注意这里说的是工作进程(worker process)。在 nginx 运行的时候，会启动两种进程，一种进程是 master pro

cess(主进程)，一种是 worker process(工作进程)。主进程负责监控端口，协调工作进程的工作状态，分配工作任务，工作进程负责进行任务处理，一般这个参数要和操作系统 CPU 内

核数成倍数。

​    error_log 关于错误日志的配置可以参考这一篇文章：https://www.cnblogs.com/leeyongbard/p/10880356.html

​    worker_rlimit_nofile 用来设定一个 nginx worker process (工作进程)，可打开最大文件数

​    **events 模块**

​    events 模块用来指定 nginx 的工作模式以及每一个 worker process 同时开启的最大连接数，如下：

```
events {
    use epoll; #Linux平台
    worker_connections  1024;
}
```

use 用来指定 nginx 的工作模式，nginx 支持的工作模式有：select、poll、Kqueue、epoll、rtsig 和 /dev/poll，select 和 poll 是标准的工作模式，Kqueue 和 epoll 是

高效的工作模式，不同的是 epoll 是用在 linux 平台，而 Kqueue 是用在 BSD 系统，而 mac 基于 BSD ，所以 mac 上的 nginx 工作模式是 Kqueue ，epoll 是 Linux 上nginx

工作模式的首选 

​    worker_connections 用来设置允许每一个 worker process 同时开启的最大连接数，即接收前端的最大请求数。最大客户端连接数由 worker_processes 和 worker_conn

ectios决定，即 max_clients = worker_processes * worker_connections ，在作为反向代理时，max_clients = worker_processes * worker_connections/4。注意，一个进程建

立一个连接后，进程将打开一个文件副本。所以，worker_connections 的 number 值还受到操作系统设定的，进程最大可打开文件数

其语法格式：

```
worker_connections number
```

设置 nginx 进程最大可打开文件数(不能超过系统级别设定的进程可打开最大文件数)

​    1.更改系统级别 "进程可打开最大文件数"

​     首先需要要有 root 权限，修改 /etc/security/limits.conf

​     在主配置文件中添加下面两句

```
* soft nofile 327680
* hard nofile 327680
```

　soft 表示应用软件级别限制的最大可打开文件数，hard 表示操作系统级别限制的最大可打开文件数，"*" 表示对所有用户都生效

​    保存配置不会立即生效，需要通过 ulimit 命令 或 重启系统

```
ulimit -n 327680
```

　　执行命令后，通过 ulimit -a 查看修改是否生效

```
core file size          (blocks, -c) 0
data seg size           (kbytes, -d) unlimited
scheduling priority             (-e) 0
file size               (blocks, -f) unlimited
pending signals                 (-i) 63704
max locked memory       (kbytes, -l) 64
max memory size         (kbytes, -m) unlimited
open files                      (-n) 327680
pipe size            (512 bytes, -p) 8
POSIX message queues     (bytes, -q) 819200
real-time priority              (-r) 0
stack size              (kbytes, -s) 10240
cpu time               (seconds, -t) unlimited
max user processes              (-u) 63704
virtual memory          (kbytes, -v) unlimited
file locks                      (-x) unlimited
```

注意，open files 这一项变化了表示修改生效

​    \2. 修改 nginx 软件级别的 "进程最大可打开文件数"

​     第一步只是修改了操作系统级别的 "进程最大可打开文件数"，作为 nginx 来说，我们还需要对这个软件进行修改，打开 nginx.conf 主配置文件，修改 worker_rlimit_nofile 属性

​     修改完成之后，需要重启 nginx 配置才能生效

​    3.验证 nginx 的 "进程最大可打开文件数" 是否生效

​     在 Linux 中，所有的进程都会有一个临时的核心配置文件描述，存放位置：/pro/进程号/limit

 ![img](https://img2018.cnblogs.com/blog/1302542/201905/1302542-20190518142304993-562792850.png) 

​     我们可以看到，nginx worker process 的进程号分别是：4872、4873、4874、4875，我们选择其中一个查看其核心配置信息：

 ![img](https://img2018.cnblogs.com/blog/1302542/201905/1302542-20190518142517062-1218097528.png) 

 可以看到 Max open files 分别是65535，更改配置信息后，重启 nginx，如上所示方式查看是否生效

​     **http 模块**

​    http 模块可以说是最核心的模块了，它主要负责 HTTP 服务器相关属性的配置，它里面的 server、upstream 至关重要，下面看一个简单的 http 模块配置

```
http{
    include       mime.types;
    default_type  application/octet-stream;
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';
    access_log  /usr/local/var/log/nginx/access.log  main;
    sendfile        on;
    tcp_nopush      on;
    tcp_nodelay     on;
    keepalive_timeout  10;
    #gzip  on;
    upstream myproject {
        .....
    }
    server {
        ....
    }
}
```

说一下每个配置项的具体含义

​    include：nginx 服务器作为 web 服务器，必须能够识别前端请求过来的资源类型，include mime.types 用来设置 nginx 所能识别的文件类型，mime.types 在

nginx 主配置文件同级目录下

​    default_type：设置默认的类型为二进制流，也就是当请求的资源类型在 mime.types 里面未定义时默认使用该类型

​    access_log、log_format 可以参考这篇文章：https://www.cnblogs.com/leeyongbard/p/10880356.html

​    sendfile 用于开启高效的文件传输模式。将 tcp_nopush、tcp_nodelay 设置为 on 用于防止网络阻塞

​    keepalive_timeout：用于设置与用户建立连接之后，nginx 服务器可以保持这些连接一段时间

​    **server 模块**

​    server 模块是 http 模块的子模块，主要用于定义一个虚拟主机，下面先看一个简单的 server 是如何做的？

```
server {
        listen       8080;
        server_name  localhost 192.168.12.10 www.yangyi.com;
        # 全局定义，如果都是这一个目录，这样定义最简单。
        root   /Users/yangyi/www;
        index  index.php index.html index.htm;
        charset utf-8;
        access_log  usr/local/var/log/host.access.log  main;
        error_log  usr/local/var/log/host.error.log  error;
        ....
}
```

server，标志定义虚拟主机开始

​    listen，指定虚拟主机的服务端口

​    server_name，用来指定 IP 地址或 域名，多个域名之间用空格分开

​    root，配置请求的根目录

​        web 服务器在接收到网络请求后，需要在服务端指定的根目录中寻找请求的资源。在 nginx 服务器中 root 指令就是设置这个根目录的，其语法为：

```
root path
```

path 为 nginx 服务器接收到请求后查找资源的根目录。root 指令可以在 http，server，location 块中都可以配置，多数情况下 root 指令是配置在 location

​        块中，看一个简单的示例

```
location /data/
{
        root     /locationtest1;
}
```

  当 location 块接收到 /data/index.html 的请求时，将会在 /locationtest1/data/ 目录下寻找 index.html 响应请求

​     index，用于设定只输入域名时访问的默认首页地址，有个先后顺序：index.php、index.html、index.htm 如果没有开启目录浏览权限，又找不到这些默认首页，则会报 403 

​     charset，设置网页的默认编码格式

​     access_log，error_log 这里不再说

​     **location 模块**

​     location 模块也是一个非常重要且常用的模块，根据字面意思就可以知道主要用于定位，定位 URL，解析 URL，它提供了非常强大的正则匹配功能，也支持条件判断匹配

​     在 nginx 官方文档中定义的 location 语法为：

```
location [ = | ~ | ~* | ^~] uri {
    ................
    ................
}
```

 其中，uri 是待匹配的请求字符串，可以是不含正则表达式的字符串，如，/myserver.php，也可以是包含正则表达式的字符串，如，.php$(表示以 .php 结尾)

​     不包含正则表达式的 uri -> 标准 uri

​     包含正则表达式的 uri -> 正则 uri

​     方括号里面的部分是可选项，在介绍四种标识之前先了解下如果不添加此选项时，nginx 服务器是如何在 server 块中搜索并使用 location 块和 uri 实现和请求字符串匹配的

​     在不添加此选项时，nginx 服务器会在 server 块的多个 location 块中搜索是否有和标准 uri 匹配的请求字符串，如果有多个可以匹配，就记录匹配度最高的一个。然后再用

​     location 块中的正则 uri 和请求字符串匹配，当正则 uri 匹配成功之后，结束搜索，使用此 location 块处理请求。如果正则 uri 匹配失败，就是用上面匹配度最高的 location

​     块处理此请求。

​     四种标识(=、~、~*、^~)

```
1. =，用于标准 uri 前，要求请求字符串和 uri 严格匹配。如果匹配成功，就停止向下继续搜索并立即使用该 location 块处理请求
2，~，用于表示 uri 包含正则表达式，并区分大小写
3，~*，用于表示 uri 包含正则表达式，并且不区分大小写
4，^~，用于标准 uri 前，要求 nginx 服务器找到和请求字符串匹配度最高的标准 uri 后，立即使用该 location 快处理请求，不再使用 location 块的正则 uri 和请求字符串做匹配
```

　　 注意：

```
我们知道浏览器传送 uri 时，会对一部分 uri 进行编码，比如，空格会被编码成 "%20"，问号会被编码成 '%3f"等，"^"有一个特点，它会对 uri 中的这些符号做编码处理，如，如果 location 块接收到的 uri 是 /html/%20/data，则当 nginx 服务器搜索到配置为 /html//data 的 location 块时就可以匹配成功
```

**upstream 模块**

​    upstream 模块负责负载均衡，目前 nginx 的负载均衡支持 4 种方式：

​    1，轮询(默认)

​      每个请求按照时间顺序逐一分配到不同后端服务器，如果后端服务器 down 掉，则自动剔除，使用户访问不受影响

​    2，weight(指定轮询权重)

​      weight 的值越大分配到的访问概率越高，主要用于后端每台服务器性能不均衡的情况下，或仅仅在主从情况下设置不同的权值，达到有效合理的利用主机资源。

```
upstream bakend {
        server 192.168.0.14 weight=10;
        server 192.168.0.15 weight=10;
}
```

3，ip_hash

​       每个请求按照访问 ip 的哈希结果分配，使来自同一个 ip 的访客固定访问一台后端服务器

```
upstream bakend {
       ip_hash;
       server 192.168.0.14:88;
       server 192.168.0.15:80;
}
```

4，fair 

​      比 weight、ip_hash 更加智能的负载均衡算法，fair 可以根据页面大小和加载时间长短智能地进行负载均衡，也就是根据后端服务器的响应时间来分配请求，响应时间

的优先分配。nginx 本身并不支持 fair，如果要使用这种调度算法，则需要安装 upstream_fair 模块。

```
upstream backend {
        server server1;
        server server2;
        fair;
}
```

　4，url_hash

​      按照访问 url 的哈希结果分配，使每一个 url 定向到后端某一台服务器，可以进一步提高后端缓存服务器的效率，不过 nginx 本身是不支持这种调度算法的，需要安装

nginx 的 hash 软件包

```
例：在upstream中加入hash语句，server语句中不能写入weight等其他的参数，hash_method是使用的hash算法
upstream backend {
        server squid1:3128;
        server squid2:3128;
        hash $request_uri;
        hash_method crc32;
}
```

　　在 nginx 的 upstream 模块，可以设置每台后端服务器在负载均衡中的调度状态，常用的状态：

```
1，down，表示当前机器暂时不参与负载均衡
2，backup，预留的备份机器。当其他所有的非 backup 机器出现故障或忙的时候，才会请求 backup 机器，因为此台机器的访问压力最小
3，max_fails，允许请求的失败次数，默认为 1，当超过最大次数时，返回 proxy_next_upstream 模块定义的错误
4，fail_timeout，请求失败超时时间，在经历了 max_fails 次失败后，暂停服务的时间。max_fails 和 fail_timeout 可以一起使用
```

下面看一个简单的 upstream 模块配置：

​    1，在 http 节点下添加 upstream 节点

```
upstream linuxidc {
      server 10.0.6.108:7080;
      server 10.0.0.85:8980;
}
```

　　2，将 server 节点下的 location 节点中的 proxy_pass 配置为：http:// + upstream名称

```
location / {
      root hml;
      index index.html index.htm;
      proxy_pass http://linuxidc;
}
```

　　现在负载均衡初步完成了，upstream 按照轮询(默认)方式进行负载均衡。