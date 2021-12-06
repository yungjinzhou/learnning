## todo



**解决需求列表中的遗留问题**



zun    磁盘问题



网速慢定位方法步骤



许可证过期状态，依然可以登录（正式版，可以登陆，已处理提示信息）



写入数据库，会有多个写入license_node_info表中

重复节点的处理



license处理nova，401问题（已处理）



celery启动后，停止redis，celery正常运行？



首次启动horizon，自动迁移的问题，考虑配置正确/不正确的情况



node  info 对服务信息的监控，优化，会获取其他节点，但是不用启动的服务



route -n



ip netns 



ip route



ip  a



brctl show

ovs-vsctl





**spice配置    161上**

 杨金周 9-9 16:09:26
这个spice咋配置啊，有没有文档

杨金周 9-9 16:09:38
我按官方文档操作的，进不去

陈凯 9-9 16:10:20
173是controller节点？

杨金周 9-9 16:10:29
对

陈凯 9-9 16:12:02
controller节点上spice-server spice-protocol     openstack-nova-spicehtml5proxy spice-html5 这几个软件有没有装？openstack-nova-spicehtml5proxy.service服务有没有启动？

杨金周 9-9 16:12:32
openstack-nova-spicehtml5proxy.service服务启动了

杨金周 9-9 16:12:50
上面几个我看看

杨金周 9-9 16:18:11
我看194也就一个服务啊

陈凯 9-9 16:18:55
服务就proxy一个，其他几个是软件包

杨金周 9-9 16:19:16
安装后是不是要重新创建一个实例才行

陈凯 9-9 16:19:36
应该不需要吧

杨金周 9-9 16:19:49
安装了，然后服务重启了，进不去

陈凯 9-9 16:20:14
你虚拟机在哪个机器上？

杨金周 9-9 16:20:23
175上

杨金周 9-9 16:20:27
174上也有

陈凯 9-9 16:20:49
你创建的实例这两个上面都有？

杨金周 9-9 16:21:14
![img](file:///C:/Users/lenovo/Documents/WXWork/1688853085010740/Cache/Image/2021-09/企业微信截图_1631175673206.png)

杨金周 9-9 16:21:23
http://192.168.204.193:21730/compute/instance 