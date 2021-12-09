## spice-html5配置



#### 安装依赖

```javascript
yum install spice-html5 spice-server spice-protocol openstack-nova-spicehtml5proxy
-y
```



#### 修改nova.conf配置

配置文件中确保vnc_enabled=false参数被设置。 如果novnc被启用，确保关闭。



##### 控制节点nova.conf

```
[spice]
enabled=true
agent_enabled=true
html5proxy_host=0.0.0.0
html5proxy_port=6082
html5proxy_base_url=http://controller:6082/spice_auto.html
server_listen=0.0.0.0
server_proxyclient_address=$my_ip  # 本机节点ip
keymap=en-us

```



##### 计算节点nova.conf

```
[spice]
html5proxy_base_url=http://controller:6082/spice_auto.html
server_listen=0.0.0.0
server_proxyclient_address=$my_ip   # 本机计算节点ip地址
enabled=true
agent_enabled=true
keymap=en-us

```



#### 设置iptables

```javascript
iptables -I INPUT -p tcp -m multiport --dports 6082 -m comment --comment "Allow SPICE connections for console access" -j ACCEPT
```

永久设置iptables

可以在文件/etc/sysconfig/iptables 中添加以上设备的规则，保存并重启iptables。



#### 重启服务

计算节点上重启服务

```javascript
# service openstack-nova-compute restart
```

控制节点上重启服务

```javascript
# service httpd restart
# service openstack-nova-spicehtml5proxy start
# service openstack-nova-spicehtml5proxy status 
# systemctl enable openstack-nova-spicehtml5proxy
```