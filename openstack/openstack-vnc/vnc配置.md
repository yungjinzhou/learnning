## vnc配置(密码)



### 一、vnc配置

#### 控制节点



yum install -y openstack-nova-novncproxy 



配置nova.conf

```
[DEFAULT]
my_ip = 192.168.230.173
use_neutron = true
vnc_enabled=true
novnc_enalbed=true
ssl_only=false
[vnc]
enabled = true
server_listen = $my_ip
server_proxyclient_address = $my_ip


```



启动

```
systemctl start openstack-nova-spicehtml5proxy.service
systemctl enable openstack-nova-spicehtml5proxy.service
systemctl restart openstack-nova-*
```

重启nova服务



#### 计算节点



```
[DEFAULT]
my_ip = 192.168.230.174
vnc_enabled=true
novnc_enabled=true
resize_confirm_window=30

[vnc]
enabled = true
server_listen = 0.0.0.0
server_proxyclient_address = $my_ip
novncproxy_base_url = http://192.168.230.173:6080/vnc_auto.html

```

#### vnc访问流程

![一个VNC Proxy在OpenStack里的处理流程](./20200612120014181.png)



### 二、vnc密码配置

参考链接：

https://blog.csdn.net/u013469753/article/details/106692758

https://segmentfault.com/a/1190000040482153









