# openstack - stein版本 aodh安装与使用



## 1. Aodh -- 告警服务

Aodh根据Gnocchi和Panko中存储的计量和事件数据，提供告警通知功能。



### 1.1 主要组件

- **aodh-api**：运行在中心节点上，提供警告CRUD接口。
- **aodh-evaluator**：运行中心节点上，根据计量数据判断告警是否触发。
- **aodh-listener**：运行在中心节点上，根据事件数据判断告警是否触发。
- **aodh-notifier**：运行在中心节点上，当告警被触发时执行预设的通知动作。



### 1.2 部署配置

#### 1.2.1 配置Keystone

创建aodh用户并添加角色：

```
# openstack user create --domain default --password-prompt aodh
# openstack role add --project service --user aodh admin
```

创建aodh服务：

```
# openstack service create --name aodh --description "Telemetry Alarm" alarming
```

创建endpoints：

```
openstack endpoint create --region RegionOne alarming public http://controller:8042
openstack endpoint create --region RegionOne alarming internal http://controller:8042
openstack endpoint create --region RegionOne alarming admin http://controller:8042
```

#### 1.2.2 配置MySQL

使用MySQL保存索引数据，预先创建数据库和用户：

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
mysql -u root -p
mysql> CREATE DATABASE aodh;
mysql> GRANT ALL PRIVILEGES ON aodh.* TO 'aodh'@'localhost' \
  IDENTIFIED BY 'comleader@123';
mysql> GRANT ALL PRIVILEGES ON aodh.* TO 'aodh'@'%' \
  IDENTIFIED BY 'comleader@123';
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

#### 1.2.3 安装Aodh

```
yum install openstack-aodh-api openstack-aodh-evaluator openstack-aodh-notifier openstack-aodh-listener openstack-aodh-expirer python-aodhclient

版本：8.0.0
```

#### 1.2.4 编辑配置

/etc/aodh/aodh.conf：服务运行参数。

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
[DEFAULT]
auth_strategy = keystone
transport_url = rabbit://openstack:RABBIT_PASS@controller

[database]
connection = mysql+pymysql://aodh:AODH_DBPASS@controller/aodh

[keystone_authtoken]
www_authenticate_uri = http://controller:5000
auth_url = http://controller:5000
memcached_servers = controller:11211
auth_type = password
project_domain_id = default
user_domain_id = default
project_name = service
username = aodh
password = AODH_PASS

[service_credentials]
auth_type = password
auth_url = http://controller:5000/v3
project_domain_id = default
user_domain_id = default
project_name = service
username = aodh
password = AODH_PASS
interface = internalURL
region_name = RegionOne
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

#### 1.2.5 初始化数据库

```
# aodh-dbsync
```

#### 1.2.6 修改服务文件

- 以下是原生aodh-api启动方式（废弃）

Aodh服务默认监听8000端口，但帮助文档中描述的是8042端口。从Gnocchi监听8041端口来看，Aodh监听8042比较有延续性。修改aodh的服务文件，在启动命令中添加--port 8042参数：

```
# cat /usr/lib/systemd/system/openstack-aodh-api.service
[Unit]
Description=OpenStack Alarm API service
After=syslog.target network.target

[Service]
Type=simple
User=aodh
ExecStart=/usr/bin/aodh-api --port 8042 -- --logfile /var/log/aodh/api.log
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

[![复制代码](https://common.cnblogs.com/images/copycode.gif)](javascript:void(0);)

```
# systemctl daemon-reload
```



- 新aodh-api启动方式（忽略后面uwsgi启动）

配置/etc/aodh/uwsgi-aodh.ini，注意修改系统的监听数（默认128）,参考修改链接：https://blog.csdn.net/qq_35876972/article/details/105340159

```
[uwsgi]
http-socket = controller:8042
wsgi-file = /usr/bin/aodh-api
master = true
die-on-term = true
threads = 10
# Adjust based on the number of CPU
processes = 10
enabled-threads = true
thunder-lock = true
plugins = python
buffer-size = 65535
listen = 4096
max-requests = 2000
logto = /var/log/aodh/uwsgi.log
pidfile = /var/run/aodh-uwsgi.pid
log-maxsize = 100000000
```



修改openstack-aodh-api.service

```
[Unit]
Description=Aodh API service
After=syslog.target network.target

[Service]
KillSignal=SIGQUIT
Type=notify
User=root
NotifyAccess=all
ExecStart=/usr/sbin/uwsgi --ini /etc/aodh/uwsgi-aodh.ini
ExecStop=/usr/sbin/uwsgi --stop /var/run/aodh-uwsgi.pid
ExecReload=/usr/sbin/uwsgi --reload /var/run/aodh-uwsgi.pid
Restart=always

[Install]
WantedBy=multi-user.target
```



```
systemctl daemon-reload
```



#### 1.2.7. 启动服务

```
systemctl enable openstack-aodh-api.service   openstack-aodh-evaluator.service  openstack-aodh-notifier.service   openstack-aodh-listener.service
systemctl start openstack-aodh-api.service   openstack-aodh-evaluator.service  openstack-aodh-notifier.service   openstack-aodh-listener.service
```



```systemctl stop openstack-aodh-api.service```

更改为uwsgi启动（**如果前面已经用新方式修改，忽略这个**）

```
[uwsgi]
http-socket = controller:8042
wsgi-file = /usr/bin/aodh-api
master = true
#lazy-apps = true
die-on-term = true
threads = 10
# Adjust based on the number of CPU
processes = 10
enabled-threads = true
thunder-lock = true
plugins = python
buffer-size = 65535
listen = 4096
max-requests = 2000
daemonize = /var/log/aodh/uwsgi.log
pidfile = /var/run/aodh-uwsgi.pid
log-maxsize = 100000000

```

启动方式：/usr/sbin/uwsgi --ini /etc/aodh/uwsgi_aodh.ini





**告警优化配置**

```
[DEFAULT]
transport_url = rabbit://openstack:comleader@123@controller
workers = 4
log_rotate_interval = 1
log_rotate_interval_type = days
log_rotation_type = interval
max_logfile_count = 30
[api]
auth_strategy = keystone
[coordination]
[cors]
[database]
connection = mysql+pymysql://aodh:comleader@123@controller/aodh
connection_recycle_time = 360
[evaluator]
workers = 2
[healthcheck]
[keystone_authtoken]
www_authenticate_uri = http://controller:5000
auth_url = http://controller:5000
memcached_servers = controller:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = aodh
password = comleader@123
service_token_roles_required = true  # add 
[listener]
workers = 2
[notifier]
workers = 2
[oslo_messaging_amqp]
[oslo_messaging_kafka]
[oslo_messaging_notifications]
[oslo_messaging_rabbit]
[oslo_middleware]
[oslo_policy]
[service_credentials]
auth_url = http://controller:5000/v3
memcached_servers = controller:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = aodh
password = comleader@123
interface = internalURL
region_name = RegionOne
[service_types]
[paste_deploy]
flavor = keystone
```







#### 以下为使用说明

aodh告警创建

命令
```
openstack alarm create --name cpu_high \
--type gnocchi_resources_threshold \
--description 'Instance Running HOT' \
--metric cpu_util --threshold 65 \
--comparison-operator ge \
--aggregation-method mean \
--granularity 300 --resource-id 5204dcff-c148-406c-a8ce-dcae8f128e50 \
--resource-type instance --alarm-action 'log://' --ok-action 'log://'

------------------------------------------

aodh alarm create --name cpu_high --type gnocchi_resources_threshold --description 'instance running cpu too high ' --metric cpu --threshold 600000000 --comparison-operator ge --aggregation-method rate:mean --granularity 300 --resource-id '' --resource-type instance --alarm-action 'log://' --ok-action 'log://'


成功写入
aodh alarm create --name host_memory_too_hgih --type gnocchi_aggregation_by_metrics_threshold --description 'host running memory too high ' --metric e5dde883-dfc8-42eb-b6b7-d06e9285a802 --threshold 14007082.0 --comparison-operator ge --aggregation-method mean --granularity 300 --resource-id 'c905b301-bb6c-5853-95a8-324acbe8fc37' --resource-type host --severity critical --repeat-actions True --state 'alarm' --alarm-action 'http://74.82.196.212:8902/api/test_alarm/' --alarm-action 'log://' --insufficient-data-action  'http://74.82.196.212:8902/api/test_alarm/'  --insufficient-data-action  'log://' --ok-action 'http://74.82.196.212:8902/api/test_alarm/' --ok-action 'log://'





aodh alarm update --name host_memory_too_hgih --type gnocchi_aggregation_by_metrics_threshold --description 'host running memory too high ' --metric e5dde883-dfc8-42eb-b6b7-d06e9285a802 --threshold 14007082.0 --comparison-operator ge --aggregation-method mean --granularity 300 --evaluation-periods 5 --resource-id 'c905b301-bb6c-5853-95a8-324acbe8fc37' --resource-type host --severity moderate --repeat-actions True --state 'alarm' --alarm-action 'http://74.82.196.212:8902/api/test_alarm/' --alarm-action 'log://' --insufficient-data-action  'http://74.82.196.212:8902/api/test_alarm/'  --insufficient-data-action  'log://' --ok-action 'http://74.82.196.212:8902/api/test_alarm/' --ok-action 'log://'


# 测试 --time-constraint参数
aodh alarm update --name host_memory_too_hgih --type gnocchi_aggregation_by_metrics_threshold --description 'host running memory too high ' --metric e5dde883-dfc8-42eb-b6b7-d06e9285a802 --threshold 14007082.0 --comparison-operator ge --aggregation-method mean --granularity 300 --evaluation-periods 5 --resource-id 'c905b301-bb6c-5853-95a8-324acbe8fc37' --time-constraint  name='2 min alarm';start='*/2 * * * *';duration=60;description='sdfds';   --resource-type host --severity moderate --repeat-actions True --state 'alarm' --alarm-action 'http://74.82.196.212:8902/api/test_alarm/' --alarm-action 'log://' --insufficient-data-action  'http://74.82.196.212:8902/api/test_alarm/'  --insufficient-data-action  'log://' --ok-action 'http://74.82.196.212:8902/api/test_alarm/' --ok-action 'log://'


aodh alarm update --name host_memory_too_hgih  --time-constraint “name='test_2_min';start='*/2 * * * *';duration=60;description='sdfds'”  --resource-type host --severity moderate --repeat-actions True --state 'alarm' --alarm-action 'http://74.82.196.212:8902/api/test_alarm/' --alarm-action 'log://' --insufficient-data-action  'http://74.82.196.212:8902/api/test_alarm/'  --insufficient-data-action  'log://' --ok-action 'http://74.82.196.212:8902/api/test_alarm/' --ok-action 'log://'





aodh alarm create --name host_memory_too_hgih --type gnocchi_aggregation_by_metrics_threshold --description 'host running memory too high ' --metric e5dde883-dfc8-42eb-b6b7-d06e9285a802 --threshold 14007082.0 --comparison-operator ge --aggregation-method mean --granularity 300 --resource-id 'c905b301-bb6c-5853-95a8-324acbe8fc37' --severity critical --repeat-actions True --state 'alarm' --alarm-action 'http://74.82.196.212:8902/api/test_alarm/' --alarm-action 'log://' --insufficient-data-action  'http://74.82.196.212:8902/api/test_alarm/'  --insufficient-data-action  'log://' --ok-action 'http://74.82.196.212:8902/api/test_alarm/' --ok-action 'log://'

```

这里设置触发器状态变为alarm和ok时都执行log动作，即记录到aodh-notifier日志中。可以将log://替换为外部告警接口，触发邮件、短信等通知，或者heat、senlin的扩容接口，实现服务自动扩容。







api入口

aodhclient/v2/alarm_cli.py--校验参数









源码增加emergency







