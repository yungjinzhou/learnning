### tcpdump使用指南



#### 指定网卡

tcpdump -i eth -w test_magnum.cpap



#### 指定host

tcpdump -i any host 192.168.204.173 -w test_magnum.cpap



#### 指定端口

tcpdump -i any host 192.168.204.173  and port 9511 -w test_magnum.cpap

