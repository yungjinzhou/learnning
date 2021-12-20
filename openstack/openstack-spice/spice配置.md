## spice配置



#### 控制节点



```
yum install -y spice-html5 spice-protocol spice-server openstack-nova-spicehtml5proxy

#yum install -y spice-html5
wget https://www.spice-space.org/download/spice-html5/spice-html5-0.1.1-1.fc18.noarch.rpm
rpm -ivh spice-html5-0.1.1-1.fc18.noarch.rpm

```





配置nova.conf

```
[DEFAULT]
my_ip = 192.168.230.173
web=/usr/share/spice-html5
ssl_only=false

[spice]
enabled=true
agent_enabled=true
keymap=en-us
html5proxy_host=0.0.0.0
html5proxy_port=6082
html5proxy_base_url=http://192.168.230.173:6082/spice_auto.html
server_listen=0.0.0.0
server_proxyclient_address=$my_ip
keymap=en-us

```



启动

```
systemctl start openstack-nova-spicehtml5proxy.service
systemctl enable openstack-nova-spicehtml5proxy.service

```

重启nova服务



#### 计算节点

```
# spice-html5来自epel源，spice-server，spice-protocol来自CentOS官方源

yum install -y spice-server spice-protocol
# 手动安装spice-html5
#yum install -y spice-html5
wget https://www.spice-space.org/download/spice-html5/spice-html5-0.1.1-1.fc18.noarch.rpm
rpm -ivh spice-html5-0.1.1-1.fc18.noarch.rpm
```





```
[DEFAULT]
my_ip = 192.168.230.174
web=/usr/share/spice-html5
# vnc不影响spice
vnc_enabled=true
novnc_enabled=true
resize_confirm_window=30

[spice]
html5proxy_base_url=http://192.168.230.173:6082/spice_auto.html
server_listen=0.0.0.0
server_proxyclient_address=192.168.230.174
enabled=True
agent_enabled=true
keymap=en-us

```





