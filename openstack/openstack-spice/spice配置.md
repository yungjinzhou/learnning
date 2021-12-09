spice配置



在控制节点安装



yum install -y spice-html5 spice-protocol spice-server openstack-nova-spicehtml5proxy



配置nova.conf

```
[spice]
enabled=true
agent_enabled=true
keymap=en-us
html5proxy_host=0.0.0.0
html5proxy_port=6082
html5proxy_base_url=http://192.168.230.161:6082/spice_auto.html
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