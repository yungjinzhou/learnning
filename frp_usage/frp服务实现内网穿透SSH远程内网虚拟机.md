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
