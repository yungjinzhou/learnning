## frp服务实现内网穿透SSH远程内网虚拟机
###  1.准备工作
一台云服务（需要有公网IP）

本地主机的VmWare虚拟机（linux），我用的是CentOS7。

### 2.配置 
#### 2.1服务端配置
```
新建opt/frp文件夹,可自行决定存放位置，但需要记得。
mkdir /opt/frp

进入文件夹
cd /opt/frp

wget下载frp服务压缩包，这里是0.34版本，注意客户端与服务端需保持版本一致。
wget https://github.com/fatedier/frp/releases/download/v0.34.0/frp_0.34.0_linux_amd64.tar.gz

解压
tar -zxvf frp_0.34.0_linux_amd64.tar.gz

进入目录
cd frp_0.34.0_linux_amd64

查看服务端配置文件
cat frps.ini

[common]
bind_port = 7000
#不需要更改，有需要用vi自行更改。

运行
./frps -c frps.ini
```



#frpc.ini服务端默认端口为7000，可以通过frpc.ini更改。

#如果无法执行操作，添加777权限，chmod 777 frps.ini

 此时不可以ctrl+c或者关闭终端，否则程序会自动结束，可以新建终端通过ps aux | grep frpc.ini 查看进程是否运行。



#### 2.2客户端配置
我这里的客户端是本地主机Vmware里的虚拟机，此处必须保证服务端和客户端frp服务版本一致。

```
新建frp目录
mkdir /opt/frp

进入frp
cd /opt/frp

wget下载压缩包
wget https://github.com/fatedier/frp/releases/download/v0.34.0/frp_0.34.0_linux_amd64.tar.gz

解压
tar -zxvf frp_0.34.0_linux_amd64.tar.gz

进入目录
cd frp_0.34.0_linux_amd64

更改配置文件
vim frpc.ini
更改frpc.ini文件

server_addr：公网IP

server_port = 7000 服务端运行frps的端口，可以更改，但必须与服务端的frps.ini一致。

remote_port：公网映射端口，如果有多台客户端，每个客户端需要使用不同的端口号。

[common]
server_addr = *.*.*.* #公网ip
server_port = 7000 服务端运行frps的端口，必须与服务端的frps.ini一致

[ssh]
type = tcp
local_ip = 127.0.0.1 
local_port = 22
remote_port = 6000 # 实现映射，公网IP:6000会映射到本客户端的22端口
```


**如果有多个虚拟机，需要改变映射端口6001、6002...，并且[ssh]需要更改，例如[ssh_1]、[ssh_2]...，否则会报错，[ssh] start error: proxy name [ssh] is already in use。**

前台方式运行客户端frp

./frpc -c frpc.ini

#### 2.3测试
注意：需要在云服务器开放服务端和客户端端口，需要在云平台的安全组中设置，此处需要开放7000、6000端口。



外网任何一台机器都可以通过SSH协议连接。

SSH -p 6000 root@公网IP



 ### 3.自动化设置
#### 3.1程序后台运行
ctrl+c结束frp服务

以后台不关闭形式启动frp，这样即使ctrl+c或者关闭终端，frp服务仍然会在后台运行。首次运行不推荐使用这种方式，因为这种形式启动后有报错信息不会显示。

服务端：nohup ./frps -c frps.ini &

客户端：nohup ./frpc -c frpc.ini &

以客户端为例：



那如何结束nohup进程呢？

需要用到ps aux | grep frp查询进程号，使用kill -9 进程号结束进程，此时进程号为27905.



#### 3.2开机自启动服务
客户端：

结束frpc进程，使用kill -9 进程号结束进程，按照以下步骤进行。

1，将frpc的自带系统文件 复制到系统文件夹 /usr/lib/systemd/system/内
	cp /opt/frp/frp_0.34.0_linux_amd64/systemd/frpc.service /usr/lib/systemd/system/frpc.service

2，frpc.service内容如下，无需更改。
	[Unit]
	Description=Frp Client Service
	After=network.target
	

	[Service]
	Type=simple
	User=nobody
	Restart=on-failure
	RestartSec=5s
	ExecStart=/usr/bin/frpc -c /etc/frp/frpc.ini
	ExecReload=/usr/bin/frpc reload -c /etc/frp/frpc.ini
	
	[Install]
	WantedBy=multi-user.target

2，按照frpc.service内的命令配置，将frpc启动文件何frpc.ini配置文件复制到指定路径，frpc是命令位置。
	mkdir /etc/frp
	cp /opt/frp/frp_0.34.0_linux_amd64/frpc.ini /etc/frp/frpc.ini
	cp /opt/frp/frp_0.34.0_linux_amd64/frpc /usr/bin/frpc

3，配置生效
	刷新配置文件
	systemctl daemon-reload
	设置开机自启动，确保frpc和frpc.ini文件复制成功才能执行该命令
	systemctl enable frpc
	查看状态，这里发现服务是dead或者inactive是正常现象
	systemctl status frpc
    重启
    reboot

4，如果启动失败。应该是文件的权限问题。可以将frpc.service，frpc.ini，frpc这几个文件的权限设为 777

设置开机自启动，确保frpc和frpc.ini文件复制成功才能执行该命令，否则会出现服务无法停止现象，即使你kill进程程序仍然会自动重启，（我由于frpc文件没有cp成功）不断循环错误，除非你删除/etc/frp/frpc.ini文件或者systemctl disable frpc后kill进程。

systemctl list-unit-files | grep frpc 可以查看进程是否设置开机自启动

frpc.service核心：

ExecStart=/usr/bin/frpc -c /etc/frp/frpc.ini，相当于在使用了./frpc -c frpc.ini,只要你的ExecStart的地址与frpc.ini文件位置跟你实际存放对的位置一致即可，你甚至可以直接更改ExecStart的地址而不去复制frpc.ini。我们这里不更改配置文件内容，而是根据配置文件将frpc.ini文件复制到对应地址。

服务端：

服务端同理，不更改frps.service，复制frps.ini到ExecStart对应的地址即可，其他步骤均一致。

arch查看架构 显示686

ubuntu系统注意要下载386版本

wget https://github.com/fatedier/frp/releases/download/v0.34.0/frp_0.34.0_linux_386.tar.gz





## frp配置https代理



**前言：由于需要很多地方用到内网穿透环境，所以选择了frp，近阶段需要Https，所以有了此文，**
**本文分为frp自身功能和frp+Nginx进行反向代理实现https**
环境介绍：我这里的环境是服务端和客户端的配置均是可以在Linux/Windows下运行的，唯一需要注意的是linux上证书和windows获取方式不同，windows较麻烦，这里就不演示了，我这里用的是域名绑定的Linux服务端生成证书存放在Windows客户端下的

| 系统    | 版本               |
| :------ | :----------------- |
| Linux   | CentOS7            |
| Windows | Windows Server2012 |

***1\***|***0\*****一、frp**

frp的Github地址：https://github.com/fatedier/frp/releases

注意服务端和客户端的版本是需要一致的

如只有一端不知道版本可以进入目录通过`./frps -v`或者`./frpc -v`查看版本号

详细操作这里就不介绍了，可以参考其他文章

***2\***|***0\*****二、证书生成**

我这里用的是Let’s Encrypt，毕竟免费，哈哈,安装方式用的是Certbot

**这里的Certbot安装方式已经过时，请跳转到https://www.cnblogs.com/shook/p/14486938.html进行查看（2021.03更新）**

下面是wiki上的简介：

- Let’s Encrypt 是一个将于2015年末推出的数字证书认证机构，将通过旨在消除当前手动创建和安装证书的复杂过程的自动化流程，为安全网站提供免费的SSL/TLS证书。 Let’s Encrypt 是由互联网安全研究小组（ISRG，一个公益组织）提供的服务。主要赞助商包括电子前哨基金会，Mozilla基金会，Akamai以及思科。2015年4月9日，ISRG与Linux基金会宣布合作。用以实现这一新的数字证书认证机构的协议被称为自动证书管理环境（ACME）。 GitHub上有这一规范的草案，且提案的一个版本已作为一个Internet草案发布。Let’s Encrypt 宣称这一过程将十分简单、自动化并且免费。 2015年8月7日，该服务更新其推出计划，预计将在2015年9月7日当周某时发布首个证书，随后向列入白名单的域名发行少量证书并逐渐扩大发行。若一切按计划进行，该服务预计将在2015年11月16日当周某时全面开始提供.

**注意：在装证书之前先把Nginx或者80.443相关服务先停止，不然会发生端口冲突发生如下错误**



```
Cleaning up challenges
Problem binding to port 80: Could not bind to IPv4 or IPv6.
```

Linux下安装：

Github代码下载：`git clone https://github.com/letsencrypt/letsencrypt.git`

目录结构：
[![img](https://img2020.cnblogs.com/blog/1582377/202004/1582377-20200427200018324-139668910.png)](https://img2020.cnblogs.com/blog/1582377/202004/1582377-20200427200018324-139668910.png)

先执行：



```
yum install snapd
systemctl enable --now snapd.socket
ln -s /var/lib/snapd/snap /snap
```

再进入目录：

执行：
`./letsencrypt-auto certonly --standalone --email 123@123.com -d 二级域名.域名.com`

如果使用的是xx云默认的python环境出现



```
subprocess.CalledProcessError: Command '['virtualenv', '--no-site-packages', '--python', '/usr/bin/python2.7                                                    ', '/opt/eff.org/certbot/venv']' returned non-zero exit status 1
```

这种错误

使用：`pip install --upgrade virtualenv==16.7.9`升级即可

没有报错的话会出现如下提示：

可以看到证书存放地址以及域名过期时间

[![img](https://img2020.cnblogs.com/blog/1582377/202004/1582377-20200427202325698-87738633.png)](https://img2020.cnblogs.com/blog/1582377/202004/1582377-20200427202325698-87738633.png)

进入目录查看一下

[![img](https://img2020.cnblogs.com/blog/1582377/202004/1582377-20200427202906609-411016375.png)](https://img2020.cnblogs.com/blog/1582377/202004/1582377-20200427202906609-411016375.png)

[![img](https://img2020.cnblogs.com/blog/1582377/202004/1582377-20200427202935940-323294666.png)](https://img2020.cnblogs.com/blog/1582377/202004/1582377-20200427202935940-323294666.png)

这里只展示单域名，现在通配符泛域名解析letsencrypt也是支持的了，但是需要DNS解析，我这里以后有需要会写出方法

- certbot自动定时续期证书方法

certbot renew #手动测试，查看证书过期时间

certbot renew --force-renewal #忽略证书过期时间，直接重置证书时间

crontab -e #定时任务

0 0 1 * * /usr/bin/certbot renew --force-renewal #编辑文件

***3\***|***0\*****三、frp自身进行反向代理实现https**

- 为了体现内网穿透，这里我们准备了一台服务端和一台客户端，系统分别是CentOS和WindowsServer，具体情况具体分析吧

**需要注意的是这里的证书是放在客户端下的**

**服务端配置(Linux上frps.ini)**



```
[common]
bind_port=7000                       #服务端端口
#privilege_token=*******             #客户端连接凭证
max_pool_count=5                     #最大连接数
vhost_http_port = 80                 #客户端http映射的端口
vhost_https_port = 443               #客户端https映射的端口
dashboard_port=7505                  #服务端看板的访问端口
dashboard_user=root                  #服务端看板账户
dashboard_pwd=***                    #服务端看板账户密码
```

配置完之后运行服务端

Linux : `./frps -c ./frps.ini`

Windows : 进入目录`frps.exe`

服务端配置完成

**客户端配置(Windows上frpc.ini)**



```
server_addr = 192.168.100.100                    #服务端的IP地址，好像也可以写域名，没试过
server_port = 7000                               #服务端端口

[test_http]                                      #Http服务，映射的是服务端http80端口
type = http                                      #服务方式
local_ip = 127.0.0.1                             #服务端ip，可写本地，局域网等做反向代理的ip
local_port = 8000                                #服务端端口
custom_domains = test.test.com                   #需要反向代理的域名，就是服务端要代理的域名

[test_https]                                     #Https服务，映射的是服务端https443端口
type = https                                     #服务方式
local_ip = 127.0.0.1                             #服务端ip，可写本地，局域网等做反向代理的ip
local_port = 8000                                #服务端端口
custom_domains = test.test.com                   #需要反向代理的域名，就是服务端要代理的域名

# 以下为https新加的内容
plugin = https2http                             #将 https请求转换成http请求后再发送给本地服务
plugin_local_addr = 127.0.0.1:8000              #转换http后的端口  

#证书相关配置
plugin_crt_path = C:\Users\Administrator\Desktop\test.test.com\fullchain1.crt  #linux下生成的证书为fullchain.pem格式，复制到Windows上改成.crt后缀即可
plugin_key_path = C:\Users\Administrator\Desktop\test.test.com\privkey1.key    #linux下生成的证书为privkey.pem格式，复制到Windows上改成.key后缀即可
plugin_host_header_rewrite = 127.0.0.1            
plugin_header_X-From-Where = frp
```

配置完之后运行服务端

Linux : `./frpc -c ./frpc.ini`

Windows : 进入目录`frpc.exe`

服务端配置完成

关于frp命令的后台启动方法

使用systemctl来控制启动
\```sudo vim /lib/systemd/system/frps.service````

写入以下内容



```
[Unit]
Description=fraps service
After=network.target syslog.target
Wants=network.target

[Service]
Type=simple
#启动服务的命令（此处写你的frps的实际安装目录）
ExecStart=/yourpath/frps -c /yourpath/frps.ini
[Install]
WantedBy=multi-user.target
```

然后就启动frps
`sudo systemctl start frps`
再打开自启动
`sudo systemctl enable frps`

如果要重启应用，可以这样，`sudo systemctl restart frps`

如果要停止应用，可以输入，`sudo systemctl stop frps`

如果要查看应用的日志，可以输入，`sudo systemctl status frps`

就可以运行了

frp官方文档：https://github.com/fatedier/frp/blob/master/README_zh.md 建议多读官方的文档

[![img](https://img2020.cnblogs.com/blog/1582377/202004/1582377-20200428083314497-374284531.png)](https://img2020.cnblogs.com/blog/1582377/202004/1582377-20200428083314497-374284531.png)

frps完整版配置文件：https://github.com/fatedier/frp/blob/master/conf/frps_full.ini

frpc完整版配置文件：https://github.com/fatedier/frp/blob/master/conf/frpc_full.ini

***4\***|***0\*****四、 Nginx+frp的配置**

这里的环境也是一台服务端和一台客户端，系统分别是CentOS和WindowsServer

**需要注意的是这里的证书是放在服务端下的**

Nginx这里不介绍安装了

直接上配置文件 .conf



```
server 
	{
        listen 80;                                                               # http对应端口
	listen 443 ssl;                                                          # https对应端口，
  	ssl_certificate /etc/letsencrypt/live/test.test.com/fullchain.pem;       # 证书存放位置
  	ssl_certificate_key /etc/letsencrypt/live/test.test.com/privkey.pem;     # 证书存放位置
        server_name *.test.test.com;                                             # ip，域名，我这里以泛域名举例，毕竟是做反向代理，http就不用配置了
                                                                                 # https还可以做其他安全配置，需要的去看其他文章
    location / {
        proxy_pass  http://127.0.0.1:12369;                                      # 映射的frp服务端frps.ini的 vhost_http_port端口
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_set_header X-NginX-Proxy true;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_max_temp_file_size 0;
        proxy_redirect off;
        proxy_read_timeout 240s;
    }
                                                                                 # 我这里没做http强制转换为https，有需要的可以做一下
        error_page   500 502 503 504  /50x.html; 
  	location = /50x.html {
        root   /usr/share/nginx/html;
    }
}
```

改完了记得重载配置[![img](https://img2020.cnblogs.com/blog/1582377/202004/1582377-20200428110710600-2128336193.png)](https://img2020.cnblogs.com/blog/1582377/202004/1582377-20200428110710600-2128336193.png)

**服务端配置(Linux上frps.ini)**



```
[common]
bind_port=7000                       #服务端端口
#privilege_token=*******             #客户端连接凭证
max_pool_count=5                     #最大连接数
vhost_http_port = 12369              #客户端http映射的端口，就是上面Nginx的proxy_pass对应端口
vhost_https_port = 12399             #客户端https映射的端口
dashboard_port=7505                  #服务端看板的访问端口
dashboard_user=root                  #服务端看板账户
dashboard_pwd=***                    #服务端看板账户密码
```

配置完之后还是运行服务端测试一下

Linux : `./frps -c ./frps.ini`

Windows : 进入目录`frps.exe`

**客户端配置(Windows上frpc.ini)**



```
server_addr = 192.168.100.100                    #服务端的IP地址，好像也可以写域名，没试过
server_port = 7000                               #服务端端口

[test_http]                                      #Http服务，映射的是服务端http80端口
type = http                                      #服务方式
local_ip = 127.0.0.1                             #服务端ip，可写本地，局域网等做反向代理的ip
local_port = 8000                                #服务端端口
custom_domains = test.test.com                   #需要反向代理的域名，就是服务端要代理的域名
```

配置完之后还是运行客户端测试一下

Linux : `./frpc -c ./frpc.ini`

Windows : 进入目录`frpc.exe`

[![img](https://img2020.cnblogs.com/blog/1582377/202004/1582377-20200428111718454-2102556672.png)](https://img2020.cnblogs.com/blog/1582377/202004/1582377-20200428111718454-2102556672.png)

到此的话应该就没有其他问题了

参考文章：https://cloud.tencent.com/developer/article/1581948







## frp为其他服务配置代理









