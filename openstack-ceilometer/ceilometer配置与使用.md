## 一、ceilometer-stein版配置与使用

参考链接：https://support.huaweicloud.com/dpmg-kunpengcpfs/kunpengopenstackstein_04_0013.html

#### 1. 环境配置

在控制节点执行以下操作。

1. 使用admin用户登录OpenStack 命令行。

   **source /root/admin-openrc**

   

2. 创建服务凭据。

   

   1. 创建ceilometer用户,并为该用户设置密码。

      **openstack user create --domain default --password-prompt ceilometer**

   2. 将admin角色添加到ceilometer用户。

      **openstack role add --project service --user ceilometer admin**

   

3. 在Keystone注册Gnocchi服务。

   

   1. 创建gnocchi用户，并设置密码。

      **openstack user create --domain default --password-prompt gnocchi**

   2. 创建gnocchi服务实体。

      **openstack service create --name gnocchi --description "Metric Service" metric**

   3. 将admin角色添加到gnocchi用户。

      **openstack role add --project service --user gnocchi admin**

   

4. 创建度量服务API端点。

   

   **openstack endpoint create --region RegionOne metric public http://controller:8041**

   **openstack endpoint create --region RegionOne metric internal http://controller:8041**

   **openstack endpoint create --region RegionOne metric admin http://controller:8041**

   ![点击放大](https://support.huaweicloud.com/dpmg-kunpengcpfs/zh-cn_image_0207719471.png)

   

#### 2. 安装配置Gnocchi

在控制节点执行以下操作。

1. 安装Gnocchi包。

   

   **yum -y install openstack-gnocchi-api openstack-gnocchi-metricd python-gnocchiclient**

   

2. 为Gnocchi服务创建数据库。

   

   ![img](https://res-img3.huaweicloud.com/content/dam/cloudbu-site/archive/china/zh-cn/support/resource/framework/v3/images/support-doc-new-note.svg)说明：

   本文中将涉及的密码均设置为“<PASSWORD>”，请用户根据环境实际情况进行修改。

   ```
   mysql -u root -p
   CREATE DATABASE gnocchi;
   GRANT ALL PRIVILEGES ON gnocchi.* TO 'gnocchi'@'localhost' IDENTIFIED BY 'comleader@123';
   GRANT ALL PRIVILEGES ON gnocchi.* TO 'gnocchi'@'%' IDENTIFIED BY 'comleader@123';
   exit
   ```

   

   ![点击放大](https://support.huaweicloud.com/dpmg-kunpengcpfs/zh-cn_image_0221749706.png)

   

3. 执行命令**vim /etc/gnocchi/gnocchi.conf**编辑配置文件**/etc/gnocchi/gnocchi.conf**，并且修改以下配置：

    sed -i.default -e '/^#/d' -e '/^$/d'  /etc/gnocchi/gnocchi.conf

   1. 配置Gnocchi功能参数，log地址以及对接redis url端口。

      ```
      [DEFAULT]
      debug = true
      verbose = true
      log_dir = /var/log/gnocchi
      parallel_operations = 4
      coordination_url = redis://controller:6379
      ```

      

   1. 配置Gnocchi工作端口信息,host为控制节点管理IP

      ```
      [api]
      auth_mode = keystone
      host = 192.168.21.1
      port = 8041
      uwsgi_mode = http-socket
      max_limit = 1000
      ```

      

   1. 配置元数据默认存储方式。

      ```
      [archive_policy]
      default_aggregation_methods = mean,min,max,sum,std,count,rate:mean
      ```

      *注意增加的**rate:mean***

   4. 配置允许的访问来源。

      ```
      [cors]
      allowed_origin = http://controller:3000
      ```

      

   5. 配置数据库检索。

      ```
      [indexer]
      url = mysql+pymysql://gnocchi:<PASSWORD>@controller/gnocchi
      ```

      

   6. 配置ceilometer测试指标。

      ```
      [metricd]
      workers = 4
      metric_processing_delay = 60
      greedy = true
      metric_reporting_delay = 120
      metric_cleanup_delay = 300
      ```

      

   7. 配置Gnocchi存储方式以及位置，在这种配置下将其存储到本地文件系统。

      ```
      [storage]
      coordination_url = redis://controller:6379
      file_basepath = /var/lib/gnocchi
      driver = redis
      ```

      

   8. 配置Keystone认证信息，该模块需要另外添加。

      ```
      [keystone_authtoken]
      region_name = RegionOne
      www_authenticate_uri = http://controller:5000
      auth_url = http://controller:5000/v3
      memcached_servers = controller:11211
      auth_type = password
      project_domain_name = default
      user_domain_name = default
      project_name = service
      username = gnocchi
      password = <PASSWORD>
      service_token_roles_required = true
      ```

      




完整配置

```
[DEFAULT]
verbose = true
log_dir = /var/log/gnocchi
parallel_operations = 200
coordination_url = redis://controller:6379?db=5
[api]
auth_mode = keystone
host = controller
port = 8041
#port = 9041
uwsgi_mode = http-socket
max_limit = 1000
[archive_policy]
#default_aggregation_methods = mean,min,max,sum,std,count,rate:mean
default_aggregation_methods = mean,sum,count,rate:mean
[cors]
allowed_origin = http://controller:3000
[healthcheck]
[incoming]
redis_url = redis://controller:6379?db=5
[indexer]
url = mysql+pymysql://gnocchi:comleader@123@controller/gnocchi
[metricd]
workers = 6
metric_processing_delay = 60
greedy = false
metric_reporting_delay = 120
metric_cleanup_delay = 300
processing_replicas=1
[oslo_middleware]
[oslo_policy]
[statsd]
[storage]
redis_url = redis://controller:6379?db=5
#coordination_url = redis://controller:6379
#file_basepath = /var/lib/gnocchi
#driver = file
driver = redis
[keystone_authtoken]
www_authenticate_uri = http://controller:5000
auth_url = http://controller:5000
memcached_servers = controller:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = gnocchi
password = comleader@123
interface = internalURL
region_name = RegionOne
service_token_roles_required = true


```



#### 3. 安装配置redis

在控制节点执行以下操作。

1. 安装redis server。

   

   **# yum -y install redis**

   ![点击放大](https://support.huaweicloud.com/dpmg-kunpengcpfs/zh-cn_image_0207719479.png)

   

2. 编辑配置文件“/etc/redis.conf”，修改以下配置：

   

   **vim /etc/redis.conf**

   1. 配置redis可以在后台启动。

      ```
      daemonize yes
      ```

      

   2. 配置redis关闭安全模式。

      ```
      protected-mode no
      ```

      

   3. 配置redis绑定控制节点主机。

      ```
      bind 192.168.204.194
      ```

      

   

3. 以配置好的redis.conf启动redis server service。

   

   **# redis-server /etc/redis.conf**

   ![img](https://res-img3.huaweicloud.com/content/dam/cloudbu-site/archive/china/zh-cn/support/resource/framework/v3/images/support-doc-new-note.svg)说明：

   redis服务不会开机自启动，可以将上述命令放入开机启动项里，否则每次关机需要手动启动，方法如下：

   1. 编辑配置文件“/etc/rc.d/rc.local”。

      **vim /etc/rc.d/rc.local**

      并新增以下内容：

      ```
      redis-server /etc/redis.conf
      ```

      

   2. 保存退出后，赋予“/etc/rc.d/rc.local”文件执行权限。

      **# chmod +x /etc/rc.d/rc.local**

   

#### 4. 安装uWSGI插件

在控制节点执行以下操作。

安装uWSGI插件。

 yum -y install uwsgi-plugin-common uwsgi-plugin-python uwsgi**

#### 5. 完成Gnocchi的安装

在控制节点执行以下操作。

##### 5.1. 初始化Gnocchi。

```gnocchi-upgrade```

##### 5.2. 赋予“/var/lib/gnocchi”文件可读写权限。

```chmod -R 777 /var/lib/gnocchi```

###### 5.3.  启动gnocchi

配置/etc/gnocchi/uwsgi-gnocchi.ini，注意修改系统的监听数（默认128）,参考修改链接：https://blog.csdn.net/qq_35876972/article/details/105340159

```
[uwsgi]
http-socket = controller:8041
#http-socket = controller:8071
wsgi-file = /usr/bin/gnocchi-api
master = true
die-on-term = true
threads = 10
processes = 8
enabled-threads = true
thunder-lock = true
plugins = python
buffer-size = 65535
listen = 4096
logto = /var/log/gnocchi/uwsgi-gnocchi.log
max-requests = 4000
log-maxsize = 50000000
socket-timeout = 60
pidfile = /var/run/gnocchi-uwsgi.pid
```



修改openstack-goncchi-api.service

```
[Unit]
Description=Gnocchi API service
After=syslog.target network.target

[Service]
KillSignal=SIGQUIT
Type=notify
User=root
Type=notify
NotifyAccess=all
ExecStart=/usr/sbin/uwsgi --ini /etc/gnocchi/uwsgi-gnocchi.ini
ExecStop=/usr/sbin/uwsgi --stop /var/run/gnocchi-uwsgi.pid
ExecReload=/usr/sbin/uwsgi --reload /var/run/gnocchi-uwsgi.pid
Restart=always

[Install]
WantedBy=multi-user.target
```





```
systemctl enable openstack-gnocchi-api.service openstack-gnocchi-metricd.service  systemctl start openstack-gnocchi-api.service openstack-gnocchi-metricd.service
```
###### 5.4. 为gnocchi创建聚合策略
   ```
   gnocchi archive-policy create -d granularity:1m,points:30 -d granularity:5m,points:288 -d granularity:30m,points:336 -d granularity:2h,points:360 -d granularity:1d,points:365 -m mean -m max -m min -m count -m sum -m std -m rate:mean horizon-mimic
   ```
   创建规则，如果已存在，先更新规则， 创建新规则，删除旧规则

   ```gnocchi archive-policy-rule create -a horizon-mimic -m "*" default
   gnocchi archive-policy-rule update default -n default-origin
   gnocchi archive-policy-rule create -a horizon-mimic -m "*" default
   gnocchi archive-policy-rule delete default-origin
   ```

   策略规则与策略需要配合使用，

###### 5.5. 完成Gnocchi的安装

###### 5.6.  查看Gnocchi服务状态。
```
systemctl status openstack-gnocchi-api.service openstack-gnocchi-metricd.service
```
      ![点击放大](https://support.huaweicloud.com/dpmg-kunpengcpfs/zh-cn_image_0207719480.png)
    
      ![点击放大](https://support.huaweicloud.com/dpmg-kunpengcpfs/zh-cn_image_0207719481.png)

###### 5.7.  **修改源码，或者强制安装最新的修复该版本的源码，然后重新启动。**

```
rpm -ivh dm-gnocchi.rpm --force

systemctl restart openstack-gnocchi-api.service openstack-gnocchi-metricd.service
```









#### 6. 安装和配置Ceilometer（控制节点）

在控制节点执行以下操作。
##### 6.1. 安装Ceilometer包。
   **# yum -y install openstack-ceilometer-notification openstack-ceilometer-central openstack-ceilometer-compute**

   

##### 6.2.  编辑配置文件“/etc/ceilometer/pipeline.yaml--polling.yaml---gnocchi_resource.yaml”并完成以下部分：具体见配置详情项

控制节点：pipeline.yaml

<font color=red>1.0.6新增</font>

```
---
sources:
    - name: hardware_meter
      meters:
        - hardware.cpu.util
        - hardware.cpu.user
        - hardware.cpu.nice
        - hardware.cpu.system
        - hardware.cpu.idle
        - hardware.cpu.wait
        - hardware.cpu.kernel
        - hardware.cpu.interrupt
        - hardware.disk.size.total
        - hardware.disk.size.used
        - hardware.disk.read.bytes
        - hardware.disk.write.bytes
        - hardware.disk.read.requests
        - hardware.disk.write.requests
        - hardware.memory.used
        - hardware.memory.total
        - hardware.memory.buffer
        - hardware.memory.cached
        - hardware.memory.swap.avail
        - hardware.memory.swap.total
        - hardware.network.incoming.bytes
        - hardware.network.incoming.drop
        - hardware.network.incoming.errors
        - hardware.network.incoming.packets
        - hardware.network.outgoing.bytes
        - hardware.network.outgoing.drop
        - hardware.network.outgoing.errors
        - hardware.network.outgoing.packets
        - hardware.network.ip.incoming.datagrams
        - hardware.network.ip.outgoing.datagrams
      resources:
          - snmp://30.90.2.27
          - snmp://30.90.2.18
          - snmp://30.90.2.20
          - snmp://30.90.2.19
      sinks:
          - meter_snmp_sink

    - name: some_pollsters
      meters:
        - cpu
        - vcpus
        - cpu_util
        - memory
        - memory.usage
        - memory.resident
        - memory.swap.in
        - memory.swap.out
        - network.incoming.bytes
        - network.incoming.packets
        - network.outgoing.bytes
        - network.outgoing.packets
        - network.incoming.packets.drop
        - network.incoming.packets.error
        - network.outgoing.packets.drop
        - network.outgoing.packets.error
        - disk.device.read.bytes
        - disk.device.read.requests
        - disk.device.write.bytes
        - disk.device.write.requests
        - disk.device.usage
        - disk.device.capacity
        - disk.device.allocation
        - disk.root.size
      sinks:
        - instance_sink
    
    - name: user_defined 
      meters:
        - custom.hardware.cpu.user.percentage
        - custom.hardware.cpu.nice.percentage
        - custom.hardware.cpu.wait.percentage
        - custom.hardware.cpu.system.percentage
        - custom.hardware.cpu.idle.percentage
        - custom.hardware.cpu.steal.percentage
        - custom.hardware.cpu.softinterrupt.percentage
        - custom.hardware.cpu.interrupt.percentage
        - custom.hardware.disk.utilization
        - custom.hardware.memory.utilization
        - custom.hardware.swap.utilization
        - custom.hardware.network.interface.status
        # 1.0.6 新增
        - custom.hardware.cpu.util.percentage
        - custom.hardware.disk.read.bytes
        - custom.hardware.disk.write.bytes
        - custom.hardware.disk.read.requests
        - custom.hardware.disk.write.requests
      resources:
        - snmp://30.90.2.27
      sinks:
          - user_defined_sink

sinks:
    - name: meter_snmp_sink
      transformers:
      publishers:
        - gnocchi://?filter_project=service&archive_policy=horizon-mimic

    - name: instance_sink
      transformers:
      publishers:
        - gnocchi://?filter_project=service&archive_policy=horizon-mimic

    - name: meter_sink
      transformers:
      publishers:
        - gnocchi://?filter_project=service&archive_policy=horizon-mimic

    - name: user_defined_sink
      transformers:
      publishers:
          - gnocchi://?filter_project=service&archive_policy=horizon-mimic


```



控制节点：polling.yaml

​      <font color=red>修改策略，只采集本机的metric</font>

```
---
sources:
    - name: some_pollsters
      interval: 60
      meters:
        - cpu
        - vcpus
        - cpu_util
        - memory
        - memory.usage
        - memory.resident
        - memory.swap.in
        - memory.swap.out
        - network.incoming.bytes
        - network.incoming.packets
        - network.outgoing.bytes
        - network.outgoing.packets
        - network.incoming.packets.drop
        - network.incoming.packets.error
        - network.outgoing.packets.drop
        - network.outgoing.packets.error
        - disk.device.read.bytes
        - disk.device.read.requests
        - disk.device.write.bytes
        - disk.device.write.requests
        - disk.device.usage
        - disk.device.capacity
        - disk.device.allocation
    - name: hardware_snmp
      interval: 60
      resources:
      # 1.0.6改动策略
          - snmp://30.90.2.27
      meters:
        - hardware.cpu.util
        - hardware.cpu.user
        - hardware.cpu.nice
        - hardware.cpu.system
        - hardware.cpu.idle
        - hardware.cpu.wait
        - hardware.cpu.kernel
        - hardware.cpu.interrupt
        - hardware.disk.size.total
        - hardware.disk.size.used
        - hardware.disk.read.bytes
        - hardware.disk.write.bytes
        - hardware.disk.read.requests
        - hardware.disk.write.requests
        - hardware.memory.used
        - hardware.memory.total
        - hardware.memory.buffer
        - hardware.memory.cached
        - hardware.memory.swap.avail
        - hardware.memory.swap.total
        - hardware.network.incoming.bytes
        - hardware.network.incoming.errors
        - hardware.network.incoming.drop
        - hardware.network.incoming.packets
        - hardware.network.outgoing.bytes
        - hardware.network.outgoing.errors
        - hardware.network.outgoing.drop
        - hardware.network.outgoing.packets
        - hardware.network.ip.incoming.datagrams
        - hardware.network.ip.outgoing.datagrams

    - name: user_defined  # 每个节点配置resources时配置各自的ip，其他一样
      meters:
        - custom.hardware.cpu.user.percentage
        - custom.hardware.cpu.nice.percentage
        - custom.hardware.cpu.wait.percentage
        - custom.hardware.cpu.system.percentage
        - custom.hardware.cpu.idle.percentage
        - custom.hardware.cpu.steal.percentage
        - custom.hardware.cpu.softinterrupt.percentage
        - custom.hardware.cpu.interrupt.percentage
        - custom.hardware.disk.utilization
        - custom.hardware.memory.utilization
        - custom.hardware.swap.utilization
        # 1.0.6新增
        - custom.hardware.cpu.util.percentage
        - custom.hardware.network.interface.status
        - custom.hardware.disk.read.bytes
        - custom.hardware.disk.write.bytes
        - custom.hardware.disk.read.requests
        - custom.hardware.disk.write.requests
      resources:
        - snmp://30.90.2.27
      interval: 60


```



控制节点：gnocchi_resource.yaml

<font color=red>1.0.6新增 disk读写</font>

```
---
archive_policy_default: horizon-mimic
archive_policies:
  # NOTE(sileht): We keep "mean" for now to not break all gating that
  # use the current tempest scenario.
  - name: ceilometer-low
    aggregation_methods:
      - mean
    back_window: 0
    definition:
      - granularity: 5 minutes
        timespan: 30 days
  - name: ceilometer-low-rate
    aggregation_methods:
      - mean
      - rate:mean
    back_window: 0
    definition:
      - granularity: 5 minutes
        timespan: 30 days
  - name: ceilometer-high
    aggregation_methods:
      - mean
    back_window: 0
    definition:
      - granularity: 1 second
        timespan: 1 hour
      - granularity: 1 minute
        timespan: 1 day
      - granularity: 1 hour
        timespan: 365 days
  - name: ceilometer-high-rate
    aggregation_methods:
      - mean
      - rate:mean
    back_window: 0
    definition:
      - granularity: 1 second
        timespan: 1 hour
      - granularity: 1 minute
        timespan: 1 day
      - granularity: 1 hour
        timespan: 365 days

resources:
  - resource_type: identity
    metrics:
      identity.authenticate.success:
      identity.authenticate.pending:
      identity.authenticate.failure:
      identity.user.created:
      identity.user.deleted:
      identity.user.updated:
      identity.group.created:
      identity.group.deleted:
      identity.group.updated:
      identity.role.created:
      identity.role.deleted:
      identity.role.updated:
      identity.project.created:
      identity.project.deleted:
      identity.project.updated:
      identity.trust.created:
      identity.trust.deleted:
      identity.role_assignment.created:
      identity.role_assignment.deleted:

  - resource_type: instance
    metrics:
      memory:
      memory.usage:
      memory.resident:
      memory.swap.in:
      memory.swap.out:
      memory.bandwidth.total:
      memory.bandwidth.local:
      network.incoming.bytes:
      network.incoming.packets:
      network.outgoing.bytes:
      network.outgoing.packets:
      network.incoming.packets.drop:
      network.incoming.packets.error:
      network.outgoing.packets.drop:
      network.outgoing.packets.error:
      vcpus:
      cpu_util:
      cpu:
      cpu_l3_cache:
      disk.root.size:
      disk.ephemeral.size:
      disk.latency:
      disk.iops:
      disk.capacity:
      disk.allocation:
      disk.usage:
      disk.device.read.requests:
      disk.device.write.requests:
      disk.device.read.bytes:
      disk.device.write.bytes:
      disk.device.capacity:
      disk.device.allocation:
      disk.device.usage:
      disk.root.size:
      disk.usage:
      compute.instance.booting.time:
      perf.cpu.cycles:
      perf.instructions:
      perf.cache.references:
      perf.cache.misses:
    attributes:
      host: resource_metadata.(instance_host|host)
      image_ref: resource_metadata.image_ref
      launched_at: resource_metadata.launched_at
      created_at: resource_metadata.created_at
      deleted_at: resource_metadata.deleted_at
      display_name: resource_metadata.display_name
      flavor_id: resource_metadata.(instance_flavor_id|(flavor.id)|flavor_id)
      flavor_name: resource_metadata.(instance_type|(flavor.name)|flavor_name)
      server_group: resource_metadata.user_metadata.server_group
    event_delete: compute.instance.delete.start
    event_attributes:
      id: instance_id
    event_associated_resources:
      instance_network_interface: '{"=": {"instance_id": "%s"}}'
      instance_disk: '{"=": {"instance_id": "%s"}}'

  - resource_type: instance_network_interface
    metrics:
      network.outgoing.packets:
      network.incoming.packets:
      network.outgoing.packets.drop:
      network.incoming.packets.drop:
      network.outgoing.packets.error:
      network.incoming.packets.error:
      network.outgoing.bytes:
      network.incoming.bytes:
    attributes:
      name: resource_metadata.vnic_name
      instance_id: resource_metadata.instance_id

  - resource_type: instance_disk
    metrics:
      disk.device.read.requests:
      disk.device.write.requests:
      disk.device.read.bytes:
      disk.device.write.bytes:
      disk.device.latency:
      disk.device.read.latency:
      disk.device.write.latency:
      disk.device.iops:
      disk.device.capacity:
      disk.device.allocation:
      disk.device.usage:
    attributes:
      name: resource_metadata.disk_name
      instance_id: resource_metadata.instance_id


  - resource_type: compute_host
    metrics:
      hardware.cpu.load.1min:
      hardware.cpu.load.5min:
      hardware.cpu.load.15min:
      hardware.cpu.util:
      hardware.cpu.user:
      hardware.cpu.nice:
      hardware.cpu.system:
      hardware.cpu.idle:
      hardware.cpu.wait:
      hardware.cpu.kernel:
      hardware.cpu.interrupt:
      custom.hardware.cpu.user.percentage:
      custom.hardware.cpu.system.percentage:
      custom.hardware.cpu.idle.percentage:
      custom.hardware.cpu.nice.percentage:
      custom.hardware.cpu.steal.percentage:
      custom.hardware.cpu.wait.percentage:
      custom.hardware.cpu.interrupt.percentage:
      custom.hardware.cpu.softinterrupt.percentage:
      custom.hardware.disk.utilization:
      custom.hardware.memory.utilization:
      custom.hardware.swap.utilization:
      custom.hardware.network.interface.status:
      hardware.disk.size.total:
      hardware.disk.size.used:
      hardware.memory.total:
      hardware.memory.used:
      hardware.memory.utilization:
      hardware.memory.swap.total:
      hardware.memory.swap.avail:
      hardware.memory.buffer:
      hardware.memory.cached:
      hardware.network.ip.outgoing.datagrams:
      hardware.network.ip.incoming.datagrams:
      hardware.system_stats.cpu.idle:
      hardware.system_stats.io.outgoing.blocks:
      hardware.system_stats.io.incoming.blocks:
    attributes:
      host_name: resource_metadata.resource_url

  - resource_type: host_disk
    metrics:
      hardware.cpu.load.1min:
      hardware.cpu.load.5min:
      hardware.cpu.load.15min:
      hardware.cpu.util:
      hardware.cpu.user:
      hardware.cpu.nice:
      hardware.cpu.system:
      hardware.cpu.idle:
      hardware.cpu.wait:
      hardware.cpu.kernel:
      hardware.cpu.interrupt:
      hardware.disk.size.total:
      hardware.disk.size.used:
      hardware.disk.read.bytes:
      hardware.disk.write.bytes:
      hardware.disk.read.requests:
      hardware.disk.write.requests:
      # 1.0.6新增
      custom.hardware.disk.read.bytes:
      custom.hardware.disk.write.bytes:
      custom.hardware.disk.read.requests:
      custom.hardware.disk.write.requests:
      
      hardware.memory.total:
      hardware.memory.used:
      hardware.memory.swap.total:
      hardware.memory.swap.avail:
      hardware.memory.buffer:
      hardware.memory.cached:
      hardware.network.ip.outgoing.datagrams:
      hardware.network.ip.incoming.datagrams:
      hardware.system_stats.cpu.idle:
      hardware.system_stats.io.outgoing.blocks:
      hardware.system_stats.io.incoming.blocks:
      custom.hardware.cpu.user.percentage:
      custom.hardware.cpu.system.percentage:
      custom.hardware.cpu.idle.percentage:
      custom.hardware.cpu.nice.percentage:
      custom.hardware.cpu.steal.percentage:
      custom.hardware.cpu.wait.percentage:
      custom.hardware.cpu.interrupt.percentage:
      custom.hardware.cpu.softinterrupt.percentage:
      custom.hardware.cpu.util.percentage:
      custom.hardware.disk.utilization:
      custom.hardware.memory.utilization:
      custom.hardware.swap.utilization:
      custom.hardware.network.interface.status:
    attributes:
      host_name: resource_metadata.resource_url
      device_name: resource_metadata.device

  - resource_type: host_network_interface
    metrics:
      hardware.network.ip.incoming.datagrams:
      hardware.network.ip.outgoing.datagrams:
      hardware.network.incoming.bytes:
      hardware.network.incoming.drop:
      hardware.network.incoming.errors:
      hardware.network.incoming.packets:
      hardware.network.outgoing.bytes:
      hardware.network.outgoing.drop:
      hardware.network.outgoing.errors:
      hardware.network.outgoing.packets:
    attributes:
      host_name: resource_metadata.resource_url
      device_name: resource_metadata.name

  - resource_type: host
    metrics:
      hardware.cpu.load.1min:
      hardware.cpu.load.5min:
      hardware.cpu.load.15min:
      hardware.cpu.util:
      hardware.cpu.user:
      hardware.cpu.nice:
      hardware.cpu.system:
      hardware.cpu.idle:
      hardware.cpu.wait:
      hardware.cpu.kernel:
      hardware.cpu.interrupt:
      hardware.disk.size.total:
      hardware.disk.size.used:
      hardware.disk.read.bytes:
      hardware.disk.write.bytes:
      hardware.disk.read.requests:
      hardware.disk.write.requests:
      # 1.0.6新增
      custom.hardware.disk.read.bytes:
      custom.hardware.disk.write.bytes:
      custom.hardware.disk.read.requests:
      custom.hardware.disk.write.requests:
      
      hardware.memory.total:
      hardware.memory.used:
      hardware.memory.swap.total:
      hardware.memory.swap.avail:
      hardware.memory.buffer:
      hardware.memory.cached:
      hardware.network.ip.outgoing.datagrams:
      hardware.network.ip.incoming.datagrams:
      hardware.system_stats.cpu.idle:
      hardware.system_stats.io.outgoing.blocks:
      hardware.system_stats.io.incoming.blocks:
      custom.hardware.cpu.user.percentage:
      custom.hardware.cpu.system.percentage:
      custom.hardware.cpu.idle.percentage:
      custom.hardware.cpu.nice.percentage:
      custom.hardware.cpu.steal.percentage:
      custom.hardware.cpu.util.percentage:
      custom.hardware.cpu.wait.percentage:
      custom.hardware.cpu.interrupt.percentage:
      custom.hardware.cpu.softinterrupt.percentage:
      custom.hardware.disk.utilization:
      custom.hardware.memory.utilization:
      custom.hardware.swap.utilization:
      custom.hardware.network.interface.status:
    attributes:
      host_name: resource_metadata.resource_url

```



计算节点：polling.yaml

<font color=red>计算节点polling.yaml调整</font>

```
---
sources:
    - name: some_pollsters
      interval: 60
      meters:
        - cpu
        - vcpus
        - memory
        - memory.usage
        - memory.resident
        - memory.swap.in
        - memory.swap.out
      #  - memory.bandwidth.total
      #  - memory.bandwidth.local
        - network.incoming.bytes
        - network.incoming.packets
        - network.outgoing.bytes
        - network.outgoing.packets
        - network.incoming.packets.drop
        - network.incoming.packets.error
        - network.outgoing.packets.drop
        - network.outgoing.packets.error
        - disk.device.read.bytes
        - disk.device.read.requests
        - disk.device.write.bytes
        - disk.device.write.requests
        - disk.device.read.bytes.rate
        - disk.device.read.requests.rate
        - disk.device.write.bytes.rate
        - disk.device.write.requests.rate
        - disk.device.capacity
        - disk.device.allocation
        - disk.device.usage
        - disk.root.size
        - disk.usage
    - name: hardware_snmp
      interval: 60
      resources:
          - snmp://30.90.2.18
      meters:
        - hardware.cpu.util
        - hardware.cpu.user
        - hardware.cpu.nice
        - hardware.cpu.system
        - hardware.cpu.idle
        - hardware.cpu.wait
        - hardware.cpu.kernel
        - hardware.cpu.interrupt
        - hardware.disk.size.total
        - hardware.disk.size.used
        - hardware.disk.read.bytes
        - hardware.disk.write.bytes
        - hardware.disk.read.requests
        - hardware.disk.write.requests
        - hardware.memory.used
        - hardware.memory.total
        - hardware.memory.buffer
        - hardware.memory.cached
        - hardware.memory.swap.avail
        - hardware.memory.swap.total
        - hardware.network.incoming.bytes
        - hardware.network.incoming.errors
        - hardware.network.incoming.drop
        - hardware.network.incoming.packets
        - hardware.network.outgoing.bytes
        - hardware.network.outgoing.errors
        - hardware.network.outgoing.drop
        - hardware.network.outgoing.packets
        - hardware.network.ip.incoming.datagrams
        - hardware.network.ip.outgoing.datagrams
    - name: user_defined # 配置节点对应ip
      meters:
        - custom.hardware.cpu.user.percentage
        - custom.hardware.cpu.nice.percentage
        - custom.hardware.cpu.wait.percentage
        - custom.hardware.cpu.system.percentage
        - custom.hardware.cpu.idle.percentage
        - custom.hardware.cpu.steal.percentage
        - custom.hardware.cpu.softinterrupt.percentage
        - custom.hardware.cpu.interrupt.percentage
        - custom.hardware.disk.utilization
        - custom.hardware.memory.utilization
        - custom.hardware.swap.utilization
        - custom.hardware.network.interface.status
        - custom.hardware.disk.read.bytes
        - custom.hardware.disk.write.bytes
        - custom.hardware.disk.read.requests
        - custom.hardware.disk.write.requests
      resources:
        - snmp://30.90.2.18
      interval: 60

```




##### 6.3. 编辑配置文件“/etc/ceilometer/ceilometer.conf”并完成以下操作：

    sed -i.default -e '/^#/d' -e '/^$/d'  /etc/ceilometer/ceilometer.conf

   1. 配置身份认证方式以及消息列队访问。

      ```
      [DEFAULT]
      debug = true
      auth_strategy = keystone
      transport_url = rabbit://openstack:<PASSWORD>@controller
      pipeline_cfg_file = pipeline.yaml
      
      
      [compute]
      # 在计算节点配置此项收集实例信息，修改配置后需要重新启动服务
      #instance_discovery_method = libvirt_metadata
      instance_discovery_method = naive
      ```

      

   1. 配置日志消息窗口。

      ```
      [notification]
      store_events = true
      messaging_urls = rabbit://openstack:<PASSWORD>@controller
      ```

      

   1. 定义轮询配置文件。

      ```
      [polling]
      cfg_file = polling.yaml
      ```

      

   1. 配置服务凭据。

      ```
      [service_credentials]
      auth_type = password
      auth_url = http://controller:5000/v3
      project_domain_id = default
      user_domain_id = default
      project_name = service
      username = ceilometer
      password = <PASSWORD>
      interface = internalURL
      region_name = RegionOne
      ```

      

   

##### 6.4. 在Gnocchi创建Ceilometer资源。

   先启动ceilometer，执行下面命令

   **# ceilometer-upgrade**

   **![img](https://res-img2.huaweicloud.com/content/dam/cloudbu-site/archive/china/zh-cn/support/resource/framework/v3/images/support-doc-new-notice.svg)须知：**

   Gnocchi必须在这个阶段状态为运行。

##### 6.5. 更改ceilometer执行权限（每个安装ceilometer的节点都需要配置）
vim /etc/sudoers
增加一行：
```
ceilometer ALL = (root) NOPASSWD: ALL
```

##### 6.6.  完成Ceilometer安装，

   

   **systemctl enable openstack-ceilometer-notification.service  openstack-ceilometer-central.service**

****

   **systemctl start openstack-ceilometer-notification.service openstack-ceilometer-central.service**

****

##### 6.7.  **修改源码，或者强制安装最新的修复该版本的源码，重新启动**。

rpm -ivh dm-mcs-dashboard-ceilometer-1.0.2-1.noarch.rpm --force

systemctl restart openstack-ceilometer-notification.service openstack-ceilometer-central.service



##### 6.8.  ***源码中增加了过滤物理机硬件信息的配置文件，/etc/ceilometer/monitor_hardware.yaml，如果要过滤硬件信息，此项在每个节点都需要配置***

```
host:
  disk_name:
    - /dev/sda
  network_interface_name:
    - ens192
    - ens224
    - ens256
instance:
  disk_name: []
  network_interface_name: []
```

***如果不配置，则默认收集全部信息，如果配置，按照配置项进行收集***

需要PyYAML==5.3.1以上的支持，验证方式

```
python2.7
>>>import yaml
>>> yaml.__version__
查看版本
```

如果版本不支持，可以按照如下方式安装

```
pip install --ignore-installed PyYAML==5.3.1
```



##### 6.9.  查看Ceilometer服务状态。

   

   **systemctl status openstack-ceilometer-notification.service openstack-ceilometer-central.service**

   ![点击放大](https://support.huaweicloud.com/dpmg-kunpengcpfs/zh-cn_image_0207719482.png)

   

#### 7. 安装和配置Ceilometer（计算节点）

在计算节点执行以下操作**，计算节点需要启动compute服务和central服务**，polling.yaml配置详情见文档。**安装完成后更新自己的ceilometer包，注意修改sudoers的配置，和控制节点相同**

##### 7.1.  安装软件，其中openstack-ceilometer-ipmi为可选安装项，不用安装。
   **yum -y install openstack-ceilometer-compute  openstack-ceilometer-central** 
##### 7.2.  编辑配置文件“/etc/ceilometer/ceilometer.conf”并完成以下操作。

    sed -i.default -e '/^#/d' -e '/^$/d'  /etc/ceilometer/ceilometer.conf

   1. 配置消息列队访问。

      ```
      [DEFAULT]
      transport_url = rabbit://openstack:<PASSWORD>@controller
      
      
      [compute]
      # 配置此项收集实例信息，修改配置后需要重新启动服务
      #instance_discovery_method = libvirt_metadata
      instance_discovery_method = naive
      
      ```

      *注意配置项的更改 **naive***

   1. 配置度量服务凭据。

      ```
      [service_credentials]
      auth_type = password
      auth_url = http://controller:5000/v3
      project_domain_id = default
      user_domain_id = default
      project_name = service
      username = ceilometer
      password = <PASSWORD>
      interface = internalURL
      region_name = RegionOne
      ```

      

   

##### 7.3.   配置nova

在计算节点执行以下操作。

1. 编辑“/etc/nova/nova.conf”文件并在以下[DEFAULT]部分配置消息通知：

    sed -i.default -e '/^#/d' -e '/^$/d'  /etc/nova/nova.conf

   1. 
   
   ```
   [DEFAULT]
   instance_usage_audit = True
   instance_usage_audit_period = hour
   
   [notifications]
   notify_on_state_change = vm_and_task_state
   
   [oslo_messaging_notifications]
   driver = messagingv2
   ```

##### 7.4.  完成安装

在计算节点执行以下操作。

1. 启动代理并将其配置为在系统引导时启动。

   

   **# systemctl enable openstack-ceilometer-compute.service openstack-ceilometer-central.service**

   **# systemctl start openstack-ceilometer-compute.service openstack-ceilometer-central.service**

##### 7.5. 执行替换

rpm -ivh dm-mcs-dashboard-ceilometer-1.0.2-1.noarch.rpm --force

##### 7.6.  ***源码中增加了过滤物理机硬件信息的配置文件，/etc/ceilometer/monitor_hardware.yaml，如果要过滤硬件信息，此项在每个节点都需要配置***

```
host:
  disk_name:
    - /dev/sda
  network_interface_name:
    - ens192
    - ens224
    - ens256
instance:
  disk_name: []
  network_interface_name: []
```

***如果不配置，则默认收集全部信息，如果配置，按照配置项进行收集***

需要PyYAML==5.3.1以上的支持，验证方式

```
python2.7
>>>import yaml
>>> yaml.__version__
查看版本
```

如果版本不支持，可以按照如下方式安装

```
pip install --ignore-installed PyYAML==5.3.1
```



systemctl restart openstack-ceilometer-compute.service openstack-ceilometer-central.service



##### 7.5.   重新启动Compute服务。
   **# systemctl restart openstack-nova-compute.service openstack-ceilometer-central.service**

   






##### 7.6 源码修改

在控制节点执行以下操作。

1. OpenStack源码脚本有一处报错，在使用Ceilometer之前需要进行修改。

   

   **vim /usr/lib/python2.7/site-packages/gnocchiclient/shell.py**

   将130行内容修改为：

   os.environ["OS_AUTH_TYPE"] = "password"

   修改前：

   ![点击放大](https://support.huaweicloud.com/dpmg-kunpengcpfs/zh-cn_image_0214513727.png)

   修改后：

   ![点击放大](https://support.huaweicloud.com/dpmg-kunpengcpfs/zh-cn_image_0214513728.png)

   

2. **openstack**源码中通过snmp收集物理机信息时有报错，需要修改，**强制更新代码后忽略此条修改**。

   **vim /usr/lib/python2.7/site-packages/ceilometer/hardware/inspector/snmp.py**

```

修改之前

    def prepare_params(self, param):
        processed = {}
        processed['matching_type'] = param['matching_type']
        processed['metric_oid'] = (param['oid'], eval(param['type']))
        processed['post_op'] = param.get('post_op', None)
        processed['metadata'] = {}
        for k, v in six.iteritems(param.get('metadata', {})):
            processed['metadata'][k] = (v['oid'], eval(v['type']))
        return processed



修改之后
    def prepare_params(self, param):
        processed = {}
        processed['matching_type'] = param['matching_type']
        processed['metric_oid'] = (param['oid'], eval(param['type']))
        processed['post_op'] = param.get('post_op', None)
        processed['metadata'] = {}
        for k, v in six.iteritems(param.get('metadata', {})):
            if 'type' not in v:
                continue
            processed['metadata'][k] = (v['oid'], eval(v['type']))
        return processed
```







#### 8. 收集物理机信息

##### 8.1. 物理服务器配置

##### 8.1.1安装（控制节点和计算节点）

```
#yum install -y net-snmp net-snmp-utils
```

##### 8.1.2   配置

sed -i.default -e '/^#/d' -e '/^$/d'  /etc/snmp/snmpd.conf

复制snmpd.conf文件到/etc/snmp/目录下。（原有的重命名，保存）

```
# 下面是增加的配置
agentAddress udp:161
com2sec notConfigUser  default       public

view    all    included   .1
view   systemview included .1   # 当大部分没有时候添加这一行

# snmp收集disk磁盘信息-增加，可以不加
includeAllDisks for all partitions and disks


# 下面是所有配置项
agentAddress udp:161
com2sec notConfigUser  default       public
group   notConfigGroup v1           notConfigUser
group   notConfigGroup v2c           notConfigUser
view    all    included   .1
view    systemview    included   .1
view    systemview    included   .1.3.6.1.2.1.1
view    systemview    included   .1.3.6.1.2.1.25.1.1
access  notConfigGroup ""      any       noauth    exact  systemview none none
syslocation Unknown (edit /etc/snmp/snmpd.conf)
syscontact Root <root@localhost> (configure /etc/snmp/snmp.local.conf)
dontLogTCPWrappersConnects yes



```

 **man snmpd.conf 可以查看具体配置项信息**

##### 8.1. 3 启动snmpd服务

systemctl start snmpd

查看状态systemctl status snmpd

可以用snmpwalk测试snmpd运行是否正常

snmpwalk -v 2c -c public 192.168.204.194 oid



**snmp重启失败，不收集物理机数据时**
**重启libvirtd.service 然后重启snmpd服务**



对应snmp项在ceilometer中的配置，见控制节点pipeline.yaml     polling.yaml配置

##### 8.1.4 关闭selinux和防火墙



```
#setenforce 0

#vi /etc/sysconfig/selinux

 修改为：SELINUX=disabled

#service snmpd start

#chkconfig snmpd on
```



**计算节点需要启动central服务**

#### 9. 常用命令

```
# 控制节点
# 首先要登陆
gnocchi resource list  # 资源列表
gnocchi resource show resource_id # 资源详情
gnocchi metric list # metric列表
gnocchi metric show metric_id # metric详情
gnocchi measures show metric_id # metric对应的数据
gnocchi measures show metric_id --aggregation mean --granularity 60 #  对应metric以60s为间隔的平均值
gnocchi measures show metric_id --aggregation rate:mean --granularity 60 #  对应metric以60s为间隔的差值平均值

```



#### 10.最新配置文件(1.7更新后)

##### 10.1 polling.yaml (所有要监控的节点)

```
---
sources:
    - name: some_pollsters
      interval: 60
      meters:
        - cpu
        - vcpus
      #  - cpu_util
        - memory
        - memory.util
        - memory.usage
        - memory.resident
        - memory.swap.in
        - memory.swap.out
        - network.incoming.bytes
        - network.incoming.packets
        - network.outgoing.bytes
        - network.outgoing.packets
        - network.incoming.packets.drop
        - network.incoming.packets.error
        - network.outgoing.packets.drop
        - network.outgoing.packets.error
        - disk.device.read.bytes
        - disk.device.read.requests
        - disk.device.write.bytes
        - disk.device.write.requests
        - disk.device.read.bytes.rate
        - disk.device.read.requests.rate
        - disk.device.write.bytes.rate
        - disk.device.write.requests.rate
        - disk.device.capacity
        - disk.device.allocation
        - disk.device.usage
        - disk.root.size
        - disk.usage
    - name: hardware_snmp
      interval: 60
      resources:
          - snmp://192.168.204.174
      meters:
        - hardware.cpu.util
        - hardware.cpu.user
        - hardware.cpu.nice
        - hardware.cpu.system
        - hardware.cpu.idle
        - hardware.cpu.wait
        - hardware.cpu.kernel
        - hardware.cpu.interrupt
        - hardware.disk.size.total
        - hardware.disk.size.used
        - hardware.disk.read.bytes
        - hardware.disk.write.bytes
        - hardware.disk.read.requests
        - hardware.disk.write.requests
        - hardware.memory.used
        - hardware.memory.total
        - hardware.memory.buffer
        - hardware.memory.cached
        - hardware.memory.swap.avail
        - hardware.memory.swap.total
        - hardware.network.incoming.bytes
        - hardware.network.incoming.errors
        - hardware.network.incoming.drop
        - hardware.network.incoming.packets
        - hardware.network.outgoing.bytes
        - hardware.network.outgoing.errors
        - hardware.network.outgoing.drop
        - hardware.network.outgoing.packets
        - hardware.network.ip.incoming.datagrams
        - hardware.network.ip.outgoing.datagrams
    - name: user_defined # 配置节点对应ip
      meters:
        - custom.hardware.cpu.user.percentage
        - custom.hardware.cpu.nice.percentage
        - custom.hardware.cpu.wait.percentage
        - custom.hardware.cpu.system.percentage
        - custom.hardware.cpu.idle.percentage
        - custom.hardware.cpu.steal.percentage
        - custom.hardware.cpu.softinterrupt.percentage
        - custom.hardware.cpu.interrupt.percentage
        - custom.hardware.cpu.kernel.percentage
        - custom.hardware.cpu.guest.percentage
        - custom.hardware.cpu.guestnice.percentage
        - custom.hardware.cpu.util.percentage
        - custom.hardware.memory.total
        - custom.hardware.memory.used
        - custom.hardware.memory.cache
        - custom.hardware.memory.buffer
        - custom.hardware.memory.utilization
        - custom.hardware.swap.total
        - custom.hardware.swap.available
        - custom.hardware.swap.utilization
        - custom.hardware.network.interface.status
        - custom.hardware.disk.utilization
        - custom.hardware.disk.read.bytes.average
        - custom.hardware.disk.write.bytes.average
        - custom.hardware.disk.read.requests.average
        - custom.hardware.disk.write.requests.average
        - custom.hardware.disk.read.bytes
        - custom.hardware.disk.write.bytes
        - custom.hardware.disk.read.requests
        - custom.hardware.disk.write.requests
        - custom.hardware.disk.size.total
        - custom.hardware.disk.size.used
      resources:
        - snmp://192.168.204.174
      interval: 60

```





##### 10.2 pipeline.yaml(控制节点)

```
---
sources:
    - name: hardware_meter
      meters:
        - hardware.cpu.util
        - hardware.cpu.user
        - hardware.cpu.nice
        - hardware.cpu.system
        - hardware.cpu.idle
        - hardware.cpu.wait
        - hardware.cpu.kernel
        - hardware.cpu.interrupt
        - hardware.disk.size.total
        - hardware.disk.size.used
        - hardware.disk.read.bytes
        - hardware.disk.write.bytes
        - hardware.disk.read.requests
        - hardware.disk.write.requests
        - hardware.memory.used
        - hardware.memory.total
        - hardware.memory.buffer
        - hardware.memory.cached
        - hardware.memory.swap.avail
        - hardware.memory.swap.total
        - hardware.network.incoming.bytes
        - hardware.network.incoming.drop
        - hardware.network.incoming.errors
        - hardware.network.incoming.packets
        - hardware.network.outgoing.bytes
        - hardware.network.outgoing.drop
        - hardware.network.outgoing.errors
        - hardware.network.outgoing.packets
        - hardware.network.ip.incoming.datagrams
        - hardware.network.ip.outgoing.datagrams
      resources:
          - snmp://30.90.2.27
      sinks:
          - meter_snmp_sink

    - name: some_pollsters
      meters:
        - cpu
        - vcpus
        - cpu_util
        - memory
        - memory.util
        - memory.usage
        - memory.resident
        - memory.swap.in
        - memory.swap.out
        - network.incoming.bytes
        - network.incoming.packets
        - network.outgoing.bytes
        - network.outgoing.packets
        - network.incoming.packets.drop
        - network.incoming.packets.error
        - network.outgoing.packets.drop
        - network.outgoing.packets.error
        - disk.device.read.bytes
        - disk.device.read.requests
        - disk.device.write.bytes
        - disk.device.write.requests
        - disk.device.usage
        - disk.device.capacity
        - disk.device.allocation
        - disk.root.size
      sinks:
        - instance_sink
    
    - name: user_defined  # 每个节点配置resources时配置各自的ip，其他一样
      meters:
        - custom.hardware.cpu.user.percentage
        - custom.hardware.cpu.nice.percentage
        - custom.hardware.cpu.wait.percentage
        - custom.hardware.cpu.system.percentage
        - custom.hardware.cpu.idle.percentage
        - custom.hardware.cpu.steal.percentage
        - custom.hardware.cpu.softinterrupt.percentage
        - custom.hardware.cpu.interrupt.percentage
        - custom.hardware.cpu.kernel.percentage
        - custom.hardware.cpu.guest.percentage
        - custom.hardware.cpu.guestnice.percentage
        - custom.hardware.cpu.util.percentage
        - custom.hardware.disk.size.total
        - custom.hardware.disk.size.used
        - custom.hardware.disk.utilization
        - custom.hardware.memory.used
        - custom.hardware.memory.total
        - custom.hardware.memory.cache
        - custom.hardware.memory.buffer
        - custom.hardware.memory.utilization
        - custom.hardware.swap.available
        - custom.hardware.swap.total
        - custom.hardware.swap.utilization
        - custom.hardware.network.interface.status
        - custom.hardware.disk.read.bytes.average
        - custom.hardware.disk.write.bytes.average
        - custom.hardware.disk.read.requests.average
        - custom.hardware.disk.write.requests.average
        - custom.hardware.disk.read.bytes
        - custom.hardware.disk.write.bytes
        - custom.hardware.disk.read.requests
        - custom.hardware.disk.write.requests
      resources:
        - snmp://30.90.2.27
      sinks:
          - user_defined_sink

sinks:
    - name: meter_snmp_sink
      transformers:
      publishers:
        - gnocchi://?filter_project=service&archive_policy=horizon-mimic

    - name: instance_sink
      transformers:
      publishers:
        - gnocchi://?filter_project=service&archive_policy=horizon-mimic

    - name: meter_sink
      transformers:
      publishers:
        - gnocchi://?filter_project=service&archive_policy=horizon-mimic

    - name: user_defined_sink
      transformers:
      publishers:
          - gnocchi://?filter_project=service&archive_policy=horizon-mimic


```



##### 10.3 gnocchi_resource.yaml(控制节点)

```
---
archive_policy_default: horizon-mimic
archive_policies:
  # NOTE(sileht): We keep "mean" for now to not break all gating that
  # use the current tempest scenario.
  - name: ceilometer-low
    aggregation_methods:
      - mean
    back_window: 0
    definition:
      - granularity: 5 minutes
        timespan: 30 days
  - name: ceilometer-low-rate
    aggregation_methods:
      - mean
      - rate:mean
    back_window: 0
    definition:
      - granularity: 5 minutes
        timespan: 30 days
  - name: ceilometer-high
    aggregation_methods:
      - mean
    back_window: 0
    definition:
      - granularity: 1 second
        timespan: 1 hour
      - granularity: 1 minute
        timespan: 1 day
      - granularity: 1 hour
        timespan: 365 days
  - name: ceilometer-high-rate
    aggregation_methods:
      - mean
      - rate:mean
    back_window: 0
    definition:
      - granularity: 1 second
        timespan: 1 hour
      - granularity: 1 minute
        timespan: 1 day
      - granularity: 1 hour
        timespan: 365 days

resources:
  - resource_type: identity
    metrics:
      identity.authenticate.success:
      identity.authenticate.pending:
      identity.authenticate.failure:
      identity.user.created:
      identity.user.deleted:
      identity.user.updated:
      identity.group.created:
      identity.group.deleted:
      identity.group.updated:
      identity.role.created:
      identity.role.deleted:
      identity.role.updated:
      identity.project.created:
      identity.project.deleted:
      identity.project.updated:
      identity.trust.created:
      identity.trust.deleted:
      identity.role_assignment.created:
      identity.role_assignment.deleted:

  - resource_type: instance
    metrics:
      memory:
      memory.usage:
      memory.util:
      memory.resident:
      memory.swap.in:
      memory.swap.out:
      memory.bandwidth.total:
      memory.bandwidth.local:
      network.incoming.bytes:
      network.incoming.packets:
      network.outgoing.bytes:
      network.outgoing.packets:
      network.incoming.packets.drop:
      network.incoming.packets.error:
      network.outgoing.packets.drop:
      network.outgoing.packets.error:
      vcpus:
      cpu_util:
      cpu:
      cpu_l3_cache:
      disk.root.size:
      disk.ephemeral.size:
      disk.latency:
      disk.iops:
      disk.capacity:
      disk.allocation:
      disk.usage:
      disk.device.read.requests:
      disk.device.write.requests:
      disk.device.read.bytes:
      disk.device.write.bytes:
      disk.device.capacity:
      disk.device.allocation:
      disk.device.usage:
      disk.root.size:
      disk.usage:
      compute.instance.booting.time:
      perf.cpu.cycles:
      perf.instructions:
      perf.cache.references:
      perf.cache.misses:
    attributes:
      host: resource_metadata.(instance_host|host)
      image_ref: resource_metadata.image_ref
      launched_at: resource_metadata.launched_at
      created_at: resource_metadata.created_at
      deleted_at: resource_metadata.deleted_at
      display_name: resource_metadata.display_name
      flavor_id: resource_metadata.(instance_flavor_id|(flavor.id)|flavor_id)
      flavor_name: resource_metadata.(instance_type|(flavor.name)|flavor_name)
      server_group: resource_metadata.user_metadata.server_group
    event_delete: compute.instance.delete.start
    event_attributes:
      id: instance_id
    event_associated_resources:
      instance_network_interface: '{"=": {"instance_id": "%s"}}'
      instance_disk: '{"=": {"instance_id": "%s"}}'

  - resource_type: instance_network_interface
    metrics:
      network.outgoing.packets:
      network.incoming.packets:
      network.outgoing.packets.drop:
      network.incoming.packets.drop:
      network.outgoing.packets.error:
      network.incoming.packets.error:
      network.outgoing.bytes:
      network.incoming.bytes:
    attributes:
      name: resource_metadata.vnic_name
      instance_id: resource_metadata.instance_id

  - resource_type: instance_disk
    metrics:
      disk.device.read.requests:
      disk.device.write.requests:
      disk.device.read.bytes:
      disk.device.write.bytes:
      disk.device.latency:
      disk.device.read.latency:
      disk.device.write.latency:
      disk.device.iops:
      disk.device.capacity:
      disk.device.allocation:
      disk.device.usage:
    attributes:
      name: resource_metadata.disk_name
      instance_id: resource_metadata.instance_id


  - resource_type: compute_host
    metrics:
      hardware.cpu.load.1min:
      hardware.cpu.load.5min:
      hardware.cpu.load.15min:
      hardware.cpu.util:
      hardware.cpu.user:
      hardware.cpu.nice:
      hardware.cpu.system:
      hardware.cpu.idle:
      hardware.cpu.wait:
      hardware.cpu.kernel:
      hardware.cpu.interrupt:
      custom.hardware.cpu.user.percentage:
      custom.hardware.cpu.system.percentage:
      custom.hardware.cpu.idle.percentage:
      custom.hardware.cpu.nice.percentage:
      custom.hardware.cpu.steal.percentage:
      custom.hardware.cpu.wait.percentage:
      custom.hardware.cpu.interrupt.percentage:
      custom.hardware.cpu.softinterrupt.percentage:
      custom.hardware.disk.utilization:
      custom.hardware.memory.utilization:
      custom.hardware.swap.utilization:
      custom.hardware.network.interface.status:
      hardware.disk.size.total:
      hardware.disk.size.used:
      hardware.memory.total:
      hardware.memory.used:
      hardware.memory.utilization:
      hardware.memory.swap.total:
      hardware.memory.swap.avail:
      hardware.memory.buffer:
      hardware.memory.cached:
      hardware.network.ip.outgoing.datagrams:
      hardware.network.ip.incoming.datagrams:
      hardware.system_stats.cpu.idle:
      hardware.system_stats.io.outgoing.blocks:
      hardware.system_stats.io.incoming.blocks:
    attributes:
      host_name: resource_metadata.resource_url

  - resource_type: host_disk
    metrics:
      hardware.cpu.load.1min:
      hardware.cpu.load.5min:
      hardware.cpu.load.15min:
      hardware.cpu.util:
      hardware.cpu.user:
      hardware.cpu.nice:
      hardware.cpu.system:
      hardware.cpu.idle:
      hardware.cpu.wait:
      hardware.cpu.kernel:
      hardware.cpu.interrupt:
      hardware.disk.size.total:
      hardware.disk.size.used:
      hardware.disk.read.bytes:
      hardware.disk.write.bytes:
      hardware.disk.read.requests:
      hardware.disk.write.requests:
      hardware.memory.total:
      hardware.memory.used:
      hardware.memory.swap.total:
      hardware.memory.swap.avail:
      hardware.memory.buffer:
      hardware.memory.cached:
      hardware.network.ip.outgoing.datagrams:
      hardware.network.ip.incoming.datagrams:
      hardware.system_stats.cpu.idle:
      hardware.system_stats.io.outgoing.blocks:
      hardware.system_stats.io.incoming.blocks:
      custom.hardware.cpu.user.percentage:
      custom.hardware.cpu.system.percentage:
      custom.hardware.cpu.idle.percentage:
      custom.hardware.cpu.nice.percentage:
      custom.hardware.cpu.steal.percentage:
      custom.hardware.cpu.wait.percentage:
      custom.hardware.cpu.interrupt.percentage:
      custom.hardware.cpu.softinterrupt.percentage:
      custom.hardware.cpu.util.percentage:
      custom.hardware.cpu.kernel.percentage:
      custom.hardware.cpu.guest.percentage:
      custom.hardware.cpu.guestnice.percentage:
      custom.hardware.disk.size.total:
      custom.hardware.disk.size.used:
      custom.hardware.disk.utilization:
      custom.hardware.disk.read.bytes.average:
      custom.hardware.disk.write.bytes.average:
      custom.hardware.disk.read.requests.average:
      custom.hardware.disk.write.requests.average:
      custom.hardware.disk.read.bytes:
      custom.hardware.disk.write.bytes:
      custom.hardware.disk.read.requests:
      custom.hardware.disk.write.requests:
      custom.hardware.memory.total:
      custom.hardware.memory.used:
      custom.hardware.memory.cache:
      custom.hardware.memory.buffer:
      custom.hardware.memory.utilization:
      custom.hardware.swap.total:
      custom.hardware.swap.available:
      custom.hardware.swap.utilization:
      custom.hardware.network.interface.status:
    attributes:
      host_name: resource_metadata.resource_url
      device_name: resource_metadata.device

  - resource_type: host_network_interface
    metrics:
      hardware.network.ip.incoming.datagrams:
      hardware.network.ip.outgoing.datagrams:
      hardware.network.incoming.bytes:
      hardware.network.incoming.drop:
      hardware.network.incoming.errors:
      hardware.network.incoming.packets:
      hardware.network.outgoing.bytes:
      hardware.network.outgoing.drop:
      hardware.network.outgoing.errors:
      hardware.network.outgoing.packets:
    attributes:
      host_name: resource_metadata.resource_url
      device_name: resource_metadata.name

  - resource_type: host
    metrics:
      hardware.cpu.load.1min:
      hardware.cpu.load.5min:
      hardware.cpu.load.15min:
      hardware.cpu.util:
      hardware.cpu.user:
      hardware.cpu.nice:
      hardware.cpu.system:
      hardware.cpu.idle:
      hardware.cpu.wait:
      hardware.cpu.kernel:
      hardware.cpu.interrupt:
      hardware.disk.size.total:
      hardware.disk.size.used:
      hardware.disk.read.bytes:
      hardware.disk.write.bytes:
      hardware.disk.read.requests:
      hardware.disk.write.requests:
      hardware.memory.total:
      hardware.memory.used:
      hardware.memory.swap.total:
      hardware.memory.swap.avail:
      hardware.memory.buffer:
      hardware.memory.cached:
      hardware.network.ip.outgoing.datagrams:
      hardware.network.ip.incoming.datagrams:
      hardware.system_stats.cpu.idle:
      hardware.system_stats.io.outgoing.blocks:
      hardware.system_stats.io.incoming.blocks:
      custom.hardware.cpu.user.percentage:
      custom.hardware.cpu.system.percentage:
      custom.hardware.cpu.idle.percentage:
      custom.hardware.cpu.nice.percentage:
      custom.hardware.cpu.steal.percentage:
      custom.hardware.cpu.util.percentage:
      custom.hardware.cpu.wait.percentage:
      custom.hardware.cpu.interrupt.percentage:
      custom.hardware.cpu.softinterrupt.percentage:
      custom.hardware.cpu.kernel.percentage:
      custom.hardware.cpu.guest.percentage:
      custom.hardware.cpu.guestnice.percentage:
      custom.hardware.disk.utilization:
      custom.hardware.disk.size.total:
      custom.hardware.disk.size.used:
      custom.hardware.disk.read.bytes.average:
      custom.hardware.disk.write.bytes.average:
      custom.hardware.disk.read.requests.average:
      custom.hardware.disk.write.requests.average:
      custom.hardware.disk.read.bytes:
      custom.hardware.disk.write.bytes:
      custom.hardware.disk.read.requests:
      custom.hardware.disk.write.requests:
      custom.hardware.memory.total:
      custom.hardware.memory.used:
      custom.hardware.memory.cache:
      custom.hardware.memory.buffer:
      custom.hardware.memory.utilization:
      custom.hardware.swap.available:
      custom.hardware.swap.total:
      custom.hardware.swap.utilization:
      custom.hardware.network.interface.status:
    attributes:
      host_name: resource_metadata.resource_url

```



##### 10.4 monitor_hardware.yaml(所有要监控的节点)

**需要收集单个磁盘读写速率的需要配置此项，否则收集失败**

```
host:
  disk_name:
    - /dev/sda
instance:
  disk_name: []
  network_interface_name: []

```





## 二、版本更新信息

### 1.0.7

新处理多块磁盘读写；优化收集程序，减少开销

- **磁盘读写新增metric，需要同时在polling.yanl （控制节点和计算节点）、pipeline.yaml（控制节点）、gnochi_resource.yaml（控制节点）增加，重启服务**
- **每个节点都需要安装sysstat**

```
# xxxx.average配置代表所有磁盘平均读写速率
# 没有xxx.average代表多个磁盘的读写，但是此情况需要在/etc/ceilometer/monitor_hardware.yaml中配置要监控的磁盘名称，如（/dev/sda）
        - custom.hardware.cpu.kernel.percentage
        - custom.hardware.cpu.guest.percentage
        - custom.hardware.cpu.guestnice.percentage
        - custom.hardware.cpu.util.percentage
        - custom.hardware.memory.total
        - custom.hardware.memory.used
        - custom.hardware.memory.cache
        - custom.hardware.memory.buffer
        - custom.hardware.memory.utilization
        - custom.hardware.swap.total
        - custom.hardware.swap.available
        - custom.hardware.swap.utilization
        - custom.hardware.network.interface.status
        - custom.hardware.disk.size.total
        - custom.hardware.disk.size.used
        - custom.hardware.disk.read.bytes.average
        - custom.hardware.disk.write.bytes.average
        - custom.hardware.disk.read.requests.average
        - custom.hardware.disk.write.requests.average
        - custom.hardware.disk.read.bytes
        - custom.hardware.disk.write.bytes
        - custom.hardware.disk.read.requests
        - custom.hardware.disk.write.requests

```



### 1.0.6

新增custom的metric，解决默认磁盘读取数据不准的问题，针对磁盘平均读写；

磁盘读写新增metric，需要同时在polling.yanl （控制节点和计算节点）、pipeline.yaml（控制节点）、gnochi_resource.yaml（控制节点）增加，重启服务

```
        # 1.0.6新增
        - custom.hardware.cpu.util.percentage
        - custom.hardware.network.interface.status
        - custom.hardware.disk.read.bytes
        - custom.hardware.disk.write.bytes
        - custom.hardware.disk.read.requests
        - custom.hardware.disk.write.requests
```







## 三、增加pollster的方法

#### 3.1 物理机增加metric方法

- 修改/ceilometer/hardware/pollsters/data/snmp.yaml添加对应metric
- ceilometer/polling/manager.py  ceilometer/polling/data_process.py做对应处理
- 同时在polling.yanl （控制节点和计算节点）、pipeline.yaml（控制节点）、gnochi_resource.yaml（控制节点）增加对应metric
- 重启openstack-ceilometer-central服务，gnocchi查询对应resource的对应metric，看是否新增，数据是否正常收集



#### 3.2 虚拟机增加metric方法

以驱动为libvirt为例修改三个地方

##### 3.2.1 修改inspector函数对应位置添加meter及转换方式

`ceilometer/compute/virt/libvirt/insector.py`

**<font color=red>增加memory.util为例</font>**

```
    @libvirt_utils.raise_nodata_if_unsupported
    @libvirt_utils.retry_on_disconnect
    def inspect_instance(self, instance, duration=None):
        domain = self._get_domain_not_shut_off_or_raise(instance)

        memory_used = memory_resident = None
        memory_swap_in = memory_swap_out = None
        memory_util = None
        memory_stats = domain.memoryStats()
        # Stat provided from libvirt is in KB, converting it to MB.
        if 'usable' in memory_stats and 'available' in memory_stats:
            memory_used = (memory_stats['available'] -
                           memory_stats['usable']) / units.Ki
            memory_util = round(float(memory_used) / (memory_stats['available'] / units.Ki), 2)
        elif 'available' in memory_stats and 'unused' in memory_stats:
            memory_used = (memory_stats['available'] -
                           memory_stats['unused']) / units.Ki
            memory_util = round(float(memory_used) / (memory_stats['available'] / units.Ki), 2)
        if 'rss' in memory_stats:
            memory_resident = memory_stats['rss'] / units.Ki
        if 'swap_in' in memory_stats and 'swap_out' in memory_stats:
            memory_swap_in = memory_stats['swap_in'] / units.Ki
            memory_swap_out = memory_stats['swap_out'] / units.Ki

        # TODO(sileht): stats also have the disk/vnic info
        # we could use that instead of the old method for Queen
        stats = self.connection.domainListGetStats([domain], 0)[0][1]
        cpu_time = 0
        current_cpus = stats.get('vcpu.current')
        # Iterate over the maximum number of CPUs here, and count the
        # actual number encountered, since the vcpu.x structure can
        # have holes according to
        # https://libvirt.org/git/?p=libvirt.git;a=blob;f=src/libvirt-domain.c
        # virConnectGetAllDomainStats()
        for vcpu in six.moves.range(stats.get('vcpu.maximum', 0)):
            try:
                cpu_time += (stats.get('vcpu.%s.time' % vcpu) +
                             stats.get('vcpu.%s.wait' % vcpu))
                current_cpus -= 1
            except TypeError:
                # pass here, if there are too many holes, the cpu count will
                # not match, so don't need special error handling.
                pass

        if current_cpus:
            # There wasn't enough data, so fall back
            cpu_time = stats.get('cpu.time')

        return virt_inspector.InstanceStats(
            cpu_number=stats.get('vcpu.current'),
            cpu_time=cpu_time / stats.get('vcpu.current'),
            memory_usage=memory_used,
            memory_util=memory_util,
            memory_resident=memory_resident,
            memory_swap_in=memory_swap_in,
            memory_swap_out=memory_swap_out,
            cpu_cycles=stats.get("perf.cpu_cycles"),
            instructions=stats.get("perf.instructions"),
            cache_references=stats.get("perf.cache_references"),
            cache_misses=stats.get("perf.cache_misses"),
            memory_bandwidth_total=stats.get("perf.mbmt"),
            memory_bandwidth_local=stats.get("perf.mbml"),
            cpu_l3_cache_usage=stats.get("perf.cmt"),
        )

```



##### 3.2.2 新加pollster类

`ceilometer/compute/pollsters/instance_stats.py`



```
class MemoryUtilPollster(InstanceStatsPollster):
    sample_name = 'memory.util'
    sample_unit = '%'
    sample_stats_key = 'memory_util'
```

##### 3.2.3 修改总入口，添加stats_key

```
# ceilometer/compute/virt/inspector.py 

class InstanceStats(object):
    fields = [
        'cpu_number',              # number: number of CPUs
        'cpu_time',                # time: cumulative CPU time
        'cpu_util',                # util: CPU utilization in percentage
        'cpu_l3_cache_usage',      # cachesize: Amount of CPU L3 cache used
        'memory_usage',            # usage: Amount of memory used
        'memory_util',            # memory_util: memory utilization in percentage
        'memory_resident',         #
        'memory_swap_in',          # memory swap in
        'memory_swap_out',         # memory swap out
        'memory_bandwidth_total',  # total: total system bandwidth from one
                                   #   level of cache
        'memory_bandwidth_local',  # local: bandwidth of memory traffic for a
                                   #   memory controller
        'cpu_cycles',              # cpu_cycles: the number of cpu cycles one
                                   #   instruction needs
        'instructions',            # instructions: the count of instructions
        'cache_references',        # cache_references: the count of cache hits
        'cache_misses',            # cache_misses: the count of caches misses
    ]

    def __init__(self, **kwargs):
        for k in self.fields:
            setattr(self, k, kwargs.pop(k, None))
        if kwargs:
            raise AttributeError(
                "'InstanceStats' object has no attributes '%s'" % kwargs)

```



##### 3.2.4 修改entry_points.txt添加entry_points，让stevedore能够扫描到新加的pollster

该位置加载代码中新添加的pollster

vim /usr/lib/python2.7/site-packages/ceilometer-12.1.0-py2.7.egg-info/entry_points.txt 

添加后可以从self.extension中获取

{'obj': <ceilometer.compute.pollsters.instance_stats.MemoryUtilPollster object at 0x7fb231486990>, 'entry_point': EntryPoint.parse('memory.util = ceilometer.compute.pollsters.instance_stats:MemoryUtilPollster'), 'name': 'memory.util', 'plugin': <class 'ceilometer.compute.pollsters.instance_stats.MemoryUtilPollster'>}

##### 3.2.5  修改配置文件

- 同时在polling.yanl （控制节点和计算节点）、pipeline.yaml（控制节点）、gnochi_resource.yaml（控制节点）增加对应metric
- 重启openstack-ceilometer-compute服务，gnocchi查询对应resource的对应metric，看是否新增，数据是否正常收集

## 注意事项

#### 3.1. 关于配置yaml文件

controller节点
polling.yaml--接受snmp提供的物理机监控数据，需要同步与gnocchi_resource对应metric项一致
pipeline.yaml     将接受的sample转换成对象发送到gnocchi
gnocchi_resource.yaml   聚合监控数据并保存到gnocchi

compute 节点
polling.yaml--指定实例要获取的metric项，与gnocchi_resource对应metric项一致



#### 3.2. 关于获取cpu_util

由于stein版本ceilometer取消了获取cpu_util项

需要创建有rate:mean聚合方法的策略

```
1.创建 rate:mean的策略的聚合方法
2.修改pipeline中vcpus  cpus策略
3.修改gnocchi_resources.yaml文件中策略和对应cpu  vcpus策略
4.修改archive-policy-rule中的策略与正则匹配cpu
4.重启服务(systemctl restart openstack-cei*       systemctl restart gno*     systemctl restart openstack-nova*)
5.创建新的实例
6.查询创建
gnocchi measures show --resource-id 847ab913-b149-4daa-b263-3d7d228a3bcf --aggregation rate:mean cpu --granularity 60
7. 得到的value是cpu时间，需要转换，参考链接
```

参考链接：https://berndbausch.medium.com/how-i-learned-to-stop-worrying-and-love-gnocchi-aggregation-c98dfa2e20fe



#### 3.3 创建策略相关

创建规则

```gnocchi archive-policy-rule create -a low -m "*" default
gnocchi archive-policy-rule create -a low -m "*" default
```


为gnocchi创建聚合策略

```
openstack metric archive-policy create -d granularity:1m,points:30 -d granularity:5m,points:288 -d granularity:30m,points:336 -d granularity:2h,points:360 -d granularity:1d,points:365 -m  -m mean -m max -m min -m count -m sum -m std horizon-mimic
```


创建规则，如果已存在，先创建新规则，删除旧规则，更新新规则

```gnocchi archive-policy-rule create -a horizon-mimic -m "*" default
gnocchi archive-policy-rule update default -n default-origin
gnocchi archive-policy-rule create -a horizon-mimic -m "*" default
gnocchi archive-policy-rule delete default-origin
```

策略规则与策略需要配合使用，策略配置好后，需要查看策略规则是否过滤掉需要收集的metric项





#### 3.4. 收集不到云主机信息
看nova配置是否修改
看计算节点polling.yaml是否有收集项
看控制节点gnocchi_resources.yaml中是对应instance, instance_disk, instance_network_interface中对应metric是否正确
看实例是在计算节点还是控制节点，最好都在计算节点部署
修改完对应配置后，重启相关服务，重建虚拟机进行验证



#### 3.5 stein版本取消了pipeline中transfomer的配置功能



