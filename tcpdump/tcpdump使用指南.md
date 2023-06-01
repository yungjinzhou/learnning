### tcpdump使用指南



#### 指定网卡

tcpdump -i eth -w test_magnum.cpap



#### 指定host

tcpdump -i any host 192.168.204.173 -w test_magnum.cpap



#### 指定端口

tcpdump -i any host 192.168.204.173  and port 9511 -w test_magnum.cpap


tcpdump -i ens32 -nnvvv port 5900 -w vnc.pcap





#### 控制台打印

```
tcpdump 是一种常用的网络抓包工具，可以监听网络接口上的数据包，并将其进行分析和记录。-vvvnn 是 tcpdump 命令中的一组参数，含义如下：

-vvv：指定详细程度为三级，即输出更为详细的信息,比如解析 TCP 和 UDP 数据包的标志位等；；
-nn：表示不将 IP 地址和端口号解析为主机名和服务名，而是以数字形式直接输出；
-xxx：表示打印出每个数据包的十六进制内容。

因此，执行 tcpdump -vvvnn 命令可以监听网络接口上的数据包，并将其详细信息以数字形式进行显示，这样可以方便用户深入分析每个数据包的内容和特征。例如：

sudo tcpdump -vvvnn -i eth0
上述命令将在 eth0 网络接口上启动 tcpdump，并输出每个数据包的详细信息。由于加入了 -nn 参数，该命令不会将 IP 地址和端口号解析为主机名和服务名，而是直接以数字形式显示。

tcpdump -vvvnnxxx -i eth0
上述命令将在 eth0 网络接口上启动 tcpdump，并输出每个数据包的详细信息、IP 地址和端口号、十六进制内容等。由于加入了 -nn 参数，该命令不会将 IP 地址和端口号解析为主机名和服务名，而是直接以数字形式显示；同时，加入了 -xxx 参数，该命令还会将每个数据包的十六进制内容也一并输出。









```







