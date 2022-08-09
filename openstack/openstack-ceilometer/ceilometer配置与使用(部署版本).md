# 一、gnocchi/ceilometer-stein修改版配置与使用(dms-2.0.0)



## 1. 基本环境配置

### 1.1 创建用户

在控制节点执行以下操作。

1. 使用admin用户登录OpenStack 命令行。

   ```
   source /root/admin-openrc
   ```

   

2. 创建服务凭据。

   1. 创建ceilometer用户,并为该用户设置密码。

      ```
      openstack user create --domain default --password-prompt ceilometer
      ```

   2. 将admin角色添加到ceilometer用户。

      ```
      openstack role add --project service --user ceilometer admin
      ```

3. 在Keystone注册Gnocchi服务。

   1. 创建gnocchi用户，并设置密码。

      ```
      openstack user create --domain default --password-prompt gnocchi
      ```

   2. 创建gnocchi服务实体。

      ```
      openstack service create --name gnocchi --description "Metric Service" metric
      ```

   3. 将admin角色添加到gnocchi用户。

      ```
      openstack role add --project service --user gnocchi admin
      ```


### 1.2 创建endpoint

1. 创建度量服务API端点。

   ```
   openstack endpoint create --region RegionOne metric public http://controller:8041
   openstack endpoint create --region RegionOne metric internal http://controller:8041
   openstack endpoint create --region RegionOne metric admin http://controller:8041
   ```

   ![点击放大](https://support.huaweicloud.com/dpmg-kunpengcpfs/zh-cn_image_0207719471.png)




### 1.3 安装配置redis

在控制节点执行以下操作。

#### 1.3.1 安装

```
yum -y install redis
```

![点击放大](https://support.huaweicloud.com/dpmg-kunpengcpfs/zh-cn_image_0207719479.png)



#### 1.3.2 修改配置

编辑配置文件“/etc/redis.conf”，修改以下配置：

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

   

#### 1.3.3 启动、配置自启

以配置好的redis.conf启动redis server service。

```
redis-server /etc/redis.conf
```

![img](https://res-img3.huaweicloud.com/content/dam/cloudbu-site/archive/china/zh-cn/support/resource/framework/v3/images/support-doc-new-note.svg)说明：

redis服务不会开机自启动，可以将上述命令放入开机启动项里，否则每次关机需要手动启动，方法如下：

1. 编辑配置文件“/etc/rc.d/rc.local”。

   ```
   vim /etc/rc.d/rc.local
   ```

   并新增以下内容：

   ```
   redis-server /etc/redis.conf
   ```

2. 保存退出后，赋予“/etc/rc.d/rc.local”文件执行权限。

   ```
    chmod +x /etc/rc.d/rc.local
   ```



### 1.4. 安装uWSGI插件

在控制节点执行以下操作。

安装uWSGI插件。

```
 yum -y install uwsgi-plugin-common uwsgi-plugin-python uwsgi**
```



## 2. 安装配置Gnocchi

在<font color=red>**控制节点和计算节点**</font>分别安装gnocchi服务，共用数据库及rpc地址。

### 2.1 安转包

1. 安装Gnocchi包。

   ```
yum -y install openstack-gnocchi-api openstack-gnocchi-metricd python-gnocchiclient
   ```

### 2.2 创建数据库

1. 为Gnocchi服务创建数据库。

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




### 2.3 修改配置文件

1. 执行命令**vim /etc/gnocchi/gnocchi.conf**编辑配置文件**/etc/gnocchi/gnocchi.conf**，并且修改以下配置：

    ```
    sed -i.default -e '/^#/d' -e '/^$/d'  /etc/gnocchi/gnocchi.conf
    ```

   ***<font color=green>配置文件分解解释，可以跳过这部分，看后面完整配置</font>***

   #### 2.3.1 配置文件分解配置与解释

配置Gnocchi功能参数，log地址以及对接redis url端口。

   ```
      [DEFAULT]
   debug = true
      verbose = true
   log_dir = /var/log/gnocchi
      parallel_operations = 4
      coordination_url = redis://controller:6379
   ```

配置Gnocchi工作端口信息,host为控制节点管理IP

   ```
      [api]
   auth_mode = keystone
      host = 192.168.21.1
   port = 8041
      uwsgi_mode = http-socket
      max_limit = 1000
   ```

配置元数据默认存储方式。

```
   [archive_policy]
   default_aggregation_methods = mean,min,max,sum,std,count,rate:mean
```

*注意增加的**rate:mean***

配置允许的访问来源。

```
   [cors]
   allowed_origin = http://controller:3000
```

配置数据库检索。

```
   [indexer]
   url = mysql+pymysql://gnocchi:<PASSWORD>@controller/gnocchi
```

配置ceilometer测试指标。

```
   [metricd]
workers = 4
   metric_processing_delay = 60
greedy = true
   metric_reporting_delay = 120
   metric_cleanup_delay = 300
```

配置Gnocchi存储方式以及位置，在这种配置下将其存储到本地文件系统。

```
   [storage]
coordination_url = redis://controller:6379
   file_basepath = /var/lib/gnocchi
   driver = redis
```

配置Keystone认证信息，该模块需要另外添加。

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



#### 2.3.2 完整配置

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

### 2.4 初始化gnocchi

初始化gnocchi的数据库、文件索引

在控制节点执行以下操作。

```gnocchi-upgrade```

赋予“/var/lib/gnocchi”文件可读写权限。

```chmod -R 777 /var/lib/gnocchi```

### 2.5 启动gnocchi

配置/etc/gnocchi/uwsgi-gnocchi.ini，注意修改系统的监听数（默认128）,参考修改链接：https://blog.csdn.net/qq_35876972/article/details/105340159

```
[uwsgi]
http-socket = controller:8041
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
NotifyAccess=all
ExecStart=/usr/sbin/uwsgi --ini /etc/gnocchi/uwsgi-gnocchi.ini
ExecStop=/usr/sbin/uwsgi --stop /var/run/gnocchi-uwsgi.pid
ExecReload=/usr/sbin/uwsgi --reload /var/run/gnocchi-uwsgi.pid
Restart=always

[Install]
WantedBy=multi-user.target
```



```
systemctl enable openstack-gnocchi-api.service openstack-gnocchi-metricd.service  
systemctl start openstack-gnocchi-api.service openstack-gnocchi-metricd.service
```
### 2.6 聚合策略创建

为gnocchi创建聚合策略

   ```
   gnocchi archive-policy create -d granularity:1m,points:30 -d granularity:5m,points:288 -d granularity:30m,points:336 -d granularity:2h,points:360 -d granularity:1d,points:365 -m mean -m max -m min -m count -m sum -m std -m rate:mean horizon-mimic
   ```
### 2.7 修改聚合策3略规则

创建规则，如果已存在，先更新规则， 创建新规则，删除旧规则

   ```gnocchi archive-policy-rule create -a horizon-mimic -m "*" default
   gnocchi archive-policy-rule update default -n default-origin
   gnocchi archive-policy-rule create -a horizon-mimic -m "*" default
   gnocchi archive-policy-rule delete default-origin
   ```

   策略规则与策略需要配合使用，

### 2.8 替换源码，重启服务



```
systemctl status openstack-gnocchi-api.service openstack-gnocchi-metricd.service
```
#### 2.8.1 替换gnocchi源码

**修改源码，或者强制安装最新的修复该版本的源码，然后重新启动。**

（有时间可以找 ，源码spec文件，修改后直接打成源码格式，就不用二次安装了）

```
rpm -ivh dm-gnocchi.rpm --force

systemctl restart openstack-gnocchi-api.service openstack-gnocchi-metricd.service
```

#### 2.8.2 替换gnocchiclient源码

`vim /usr/lib/python2.7/site-packages/gnocchiclient/shell.py`

将130行内容修改为：

os.environ["OS_AUTH_TYPE"] = "password"

修改前：

![点击放大](https://support.huaweicloud.com/dpmg-kunpengcpfs/zh-cn_image_0214513727.png)

修改后：

![点击放大](https://support.huaweicloud.com/dpmg-kunpengcpfs/zh-cn_image_0214513728.png)



### 2.9 常用命令

```
# 首先要登陆
# source /root/admin-xxx
gnocchi resource list  # 资源列表
gnocchi resource show resource_id # 资源详情
gnocchi metric list # metric列表
gnocchi metric show metric_id # metric详情
gnocchi measures show metric_id # metric对应的数据
gnocchi measures show metric_id --aggregation mean --granularity 60 #  对应metric以60s为间隔的平均值
gnocchi measures show metric_id --aggregation rate:mean --granularity 60 #  对应metric以60s为间隔的差值平均值

```



## 3 安装snmp



### 3.1 安装

<font color=green>**（控制节点和计算节点）**</font>

```
yum install -y net-snmp net-snmp-utils
```

### 3.2 配置

```
sed -i.default -e '/^#/d' -e '/^$/d'  /etc/snmp/snmpd.conf
```

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

### 3.3 启动snmpd服务

`systemctl start snmpd`

查看状态`systemctl status snmpd`

### 3.4 测试

可以用snmpwalk测试snmpd运行是否正常

`snmpwalk -v 2c -c public 192.168.204.194 oid`

**snmp重启失败，不收集物理机数据时**
**重启libvirtd.service 然后重启snmpd服务**



## 4 安装配置ceilometer



### 4.1 安装包

在<font color=red>**控制节点和计算节点**</font>执行以下操作。
```
yum -y install openstack-ceilometer-notification openstack-ceilometer-central openstack-ceilometer-compute
```

### 4.2 配置文件修改



#### 4.2.1 polling文件修改

控制节点和计算节点，ip值不同，metric相同

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
        - memory.util
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
          - snmp://30.90.2.27  # ip address of this node
      meters:
        - hardware.network.incoming.bytes
        - hardware.network.incoming.errors
        - hardware.network.incoming.drop
        - hardware.network.incoming.packets
        - hardware.network.outgoing.bytes
        - hardware.network.outgoing.errors
        - hardware.network.outgoing.drop
        - hardware.network.outgoing.packets
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
        - custom.hardware.cpu.kernel.percentage
        - custom.hardware.cpu.guest.percentage
        - custom.hardware.cpu.guestnice.percentage
        - custom.hardware.cpu.util.percentage
        
        - custom.hardware.memory.used
        - custom.hardware.memory.total
        - custom.hardware.memory.cached
        - custom.hardware.memory.buffer
        - custom.hardware.memory.utilization
        - custom.hardware.swap.avail
        - custom.hardware.swap.total
        - custom.hardware.swap.utilization
        - custom.hardware.network.interface.status
        
        - custom.hardware.disk.size.used
        - custom.hardware.disk.size.total
        - custom.hardware.disk.utilization
        - custom.hardware.disk.read.bytes
        - custom.hardware.disk.write.bytes
        - custom.hardware.disk.read.requests
        - custom.hardware.disk.write.requests
        - custom.hardware.disk.read.bytes.average:
        - custom.hardware.disk.write.bytes.average:
        - custom.hardware.disk.read.requests.average:
        - custom.hardware.disk.write.requests.average:
      resources:
        - snmp://30.90.2.27    # ip address of this node
      interval: 60


```



#### 4.2.2 pipeline文件修改

只在有openstack-ceilometer-notification服务的节点修改

```
---
sources:
    - name: hardware_meter
      meters:
        - hardware.network.incoming.bytes
        - hardware.network.incoming.drop
        - hardware.network.incoming.errors
        - hardware.network.incoming.packets
        - hardware.network.outgoing.bytes
        - hardware.network.outgoing.drop
        - hardware.network.outgoing.errors
        - hardware.network.outgoing.packets
      resources:
          - snmp://192.168.230.107
          - snmp://192.168.230.106
          - snmp://192.168.230.109
          - snmp://192.168.230.110
          - snmp://192.168.230.111
          - snmp://192.168.230.122
          - snmp://192.168.230.105
      sinks:
          - meter_snmp_sink

    - name: some_pollsters
      meters:
        - cpu
        - vcpus
        - memory
        - memory.util
        - memory.usage
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
        - custom.hardware.memory.cached
        - custom.hardware.memory.buffer
        - custom.hardware.memory.utilization
        
        - custom.hardware.swap.avail
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
          - snmp://192.168.230.107
          - snmp://192.168.230.106
          - snmp://192.168.230.109
          - snmp://192.168.230.110
          - snmp://192.168.230.111
          - snmp://192.168.230.122
          - snmp://192.168.230.105
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



#### 4.2.3 gnocchi_resources文件修改

只在有openstack-ceilometer-notification服务的节点修改

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
  - resource_type: instance
    metrics:
      memory:
      memory.usage:
      memory.util:
      vcpus:
      cpu:
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
      disk.device.capacity:
      disk.device.allocation:
      disk.device.usage:
    attributes:
      name: resource_metadata.disk_name
      instance_id: resource_metadata.instance_id

  # remove resource_type   compute_host   
  - resource_type: host_disk
    metrics:
      custom.hardware.disk.read.bytes.average:
      custom.hardware.disk.write.bytes.average:
      custom.hardware.disk.read.requests.average:
      custom.hardware.disk.write.requests.average:
      custom.hardware.disk.read.bytes:
      custom.hardware.disk.write.bytes:
      custom.hardware.disk.read.requests:
      custom.hardware.disk.write.requests:
      custom.hardware.disk.size.total:
      custom.hardware.disk.size.used:
      custom.hardware.disk.utilization:
    attributes:
      host_name: resource_metadata.resource_url
      device_name: resource_metadata.device

  - resource_type: host_network_interface
    metrics:
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
 
      custom.hardware.memory.total:
      custom.hardware.memory.used:
      custom.hardware.memory.cached:
      custom.hardware.memory.buffer:
      custom.hardware.memory.utilization:

      custom.hardware.swap.avail:
      custom.hardware.swap.total:
      custom.hardware.swap.utilization:

      custom.hardware.network.interface.status:
    attributes:
      host_name: resource_metadata.resource_url
```

#### 4.2.4 ceilometer.conf文件修改

    sed -i.default -e '/^#/d' -e '/^$/d'  /etc/ceilometer/ceilometer.conf

##### 4.2.4.1 配置部分解释

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


##### 4.2.4.2 完整配置

```
[DEFAULT]
debug = true 
auth_strategy = keystone
transport_url = rabbit://openstack:comleader@123@controller
pipeline_cfg_file = pipeline.yaml
[compute]
instance_discovery_method = naive
[coordination]
[event]
[hardware]
[ipmi]
[meter]
[notification]
store_events = true 
messaging_urls = rabbit://openstack:comleader@123@controller
[oslo_concurrency]
[oslo_messaging_amqp]
[oslo_messaging_kafka]
[oslo_messaging_notifications]
[oslo_messaging_rabbit]
heartbeat_timeout_threshold = 30
[polling]
cfg_file = polling.yaml
[publisher]
[publisher_notifier]
[rgw_admin_credentials]
[rgw_client]
[service_credentials]
auth_url = http://nova_proxy:5000/v3
memcached_servers = controller:11211
auth_type = password
project_domain_id = default
user_domain_id = default
project_name = service
username = ceilometer
password = comleader@123
interface = internalURL
region_name = RegionOne
[service_types]
[vmware]
[xenapi]

```



#### 4.2.5 nova配置

在计算节点执行以下操作。

1. 编辑“/etc/nova/nova.conf”文件并在以下[DEFAULT]部分配置消息通知：

   `sed -i.default -e '/^#/d' -e '/^$/d'  /etc/nova/nova.conf`

   ```
   [DEFAULT]
   instance_usage_audit = True
   instance_usage_audit_period = hour
   
   [notifications]
   notify_on_state_change = vm_and_task_state
   
   [oslo_messaging_notifications]
   driver = messagingv2
   ```



#### 4.2.6 权限配置

由于增加了命令行，所以所有节点需要增加权限

vim /etc/sudoers
增加一行：

```
ceilometer ALL = (root) NOPASSWD: ALL
```



### 4.3 替换代码<font color=red>☆☆☆</font>

替换代码（此处替换前后，不应该更改默认app名称，否则无法初始化数据库，打包时跟源码包名称，版本号一致，待测试）



### 4.4 初始化资源、数据库

 在Gnocchi创建Ceilometer资源。

`ceilometer-upgrade`

   **![img](https://res-img2.huaweicloud.com/content/dam/cloudbu-site/archive/china/zh-cn/support/resource/framework/v3/images/support-doc-new-notice.svg)须知：**

   Gnocchi必须在这个阶段状态为运行。

### 4.5 启动服务

   ```
systemctl enable openstack-ceilometer-notification.service  openstack-ceilometer-central.service
systemctl start openstack-ceilometer-notification.service openstack-ceilometer-central.service
   ```



### 4.6 配置优化项

***源码中增加了过滤物理机硬件信息的配置文件，/etc/ceilometer/monitor_hardware.yaml，如果要过滤硬件信息，此项在每个节点都需要配置***

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



## 5. 安装libguestfs



libguest使用

**centos intel**

```
https://libguestfs.org/guestfs-building.1.html
https://download.libguestfs.org/1.40-stable/
下载源码包libguestfs-1.40.2.tar.gz
解压后进入目录
./configure
 发现缺少依赖包
 安装
 yum install -y pcre2-devel  augeas augeas-devel file-libs file-devel  jansson jansson-devel libcap libcap-devel hivex hivex-devel  supermin5 supermin5-devel supermin ocaml ocaml-findlib-devel  ocaml-findlib  ocaml-hivex.x86_64 ocaml-hivex-devel.x86_64 erlang-erl_interface.x86_64 gperf ncurses ncurses-devel
rm -rf  /usr/bin/supermin
ln -s /usr/bin/supermin5 /usr/bin/supermin
./configure --disable-erlang# 有提示，根据提示禁用erlang就行
make
运行 ./run virt-df -d instance-uuid





```

**hg**

```
yum install -y pcre2-devel  augeas augeas-devel file-libs file-devel  jansson jansson-devel libcap libcap-devel hivex hivex-devel  supermin5 supermin5-devel supermin ocaml ocaml-findlib-devel  ocaml-findlib  ocaml-hivex.x86_64 ocaml-hivex-devel.x86_64 erlang-erl_interface.x86_64 gperf ncurses ncurses-devel 
rm -rf  /usr/bin/supermin
ln -s /usr/bin/supermin5 /usr/bin/supermin

运行 ./run virt-df -d instance-uuid




```



**aarch64**  （长期评价测试）

```
下载源码包libguestfs-1.40.2.tar.gz
解压后进入目录
 
apt install -y gperf flex bison ncurses-dev pkg-config augeas-tools augeas-doc python-augeas
 libaugeas-dev libmagic-dev libjansson-dev libhivex-dev libhivex-ocaml libhivex-ocaml-dev supermin gdisk

./configure --with-default-backend="libvirt"
 make
 # export LIBGUESTFS_BACKEND=direct
 # export LIBGUESTFS_BACKEND=libvirt
```









## 6. 打包

日志切割文件拷贝

entry_points文件修改







##### 3.2.4 修改entry_points.txt添加entry_points，让stevedore能够扫描到新加的pollster

该位置加载代码中新添加的pollster

vim /usr/lib/python2.7/site-packages/ceilometer-12.1.0-py2.7.egg-info/entry_points.txt 

添加后可以从self.extension中获取

{'obj': <ceilometer.compute.pollsters.instance_stats.MemoryUtilPollster object at 0x7fb231486990>, 'entry_point': EntryPoint.parse('memory.util = ceilometer.compute.pollsters.instance_stats:MemoryUtilPollster'), 'name': 'memory.util', 'plugin': <class 'ceilometer.compute.pollsters.instance_stats.MemoryUtilPollster'>}

##### 3.2.5  修改配置文件

- 同时在polling.yanl （控制节点和计算节点）、pipeline.yaml（控制节点）、gnochi_resource.yaml（控制节点）增加对应metric
- 重启openstack-ceilometer-compute服务，gnocchi查询对应resource的对应metric，看是否新增，数据是否正常收集







## 四、日志切割



更改启动方式后，uwsgi日志需要定期处理

修改`/etc/logrotate.d/gnocchi`，

```
/var/log/gnocchi/*.log {
    rotate 4
    size 10M
    missingok
    compress
    copytruncate  # 切割后新日志正常写入
}

```







