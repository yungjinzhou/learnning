# 一、gnocchi/ceilometer-stein修改版配置与使用(2022.8.9版)



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

在<font color=red>**控制节点和计算节点**</font>分别安装gnocchi服务，共用数据库及rpc地址，**api服务地址是自己的ip地址**。

### 2.1 安转包

1. 安装Gnocchi包。

   ```
yum -y install openstack-gnocchi-api openstack-gnocchi-metricd python-gnocchiclient
   
版本：4.3.2
   ```

### 2.2 创建数据库

1. 为Gnocchi服务创建数据库。

   ![img](https://res-img3.huaweicloud.com/content/dam/cloudbu-site/archive/china/zh-cn/support/resource/framework/v3/images/support-doc-new-note.svg)说明：

   本文中将涉及的密码均设置为“<PASSWORD>”，请用户根据环境实际情况进行修改。

   ```
   mysql -u root -p
   CREATE DATABASE gnocchi3;
   GRANT ALL PRIVILEGES ON gnocchi3.* TO 'gnocchi'@'localhost' IDENTIFIED BY 'comleader@123';
   GRANT ALL PRIVILEGES ON gnocchi3.* TO 'gnocchi'@'%' IDENTIFIED BY 'comleader@123';
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
coordination_url = redis://:comleader@controller:6379?db=5
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



### 2.4 替换gnocchi源码/gnocchiclient源码

#### 2.4.1 替换gnocchi源码

安装包参考后面**6打包**章节,，安装后，会替换代码以及切割文件配置

**安装最新的修复该版本的源码。**

（有时间可以找 ，源码spec文件，修改后直接打成源码格式，就不用二次安装了）

```
rpm -ivh dm-mcs-dashboard-gnocchi-1.0.5-1.noarch.rpm --force

```



#### 2.4.2 替换gnocchiclient源码

`vim /usr/lib/python2.7/site-packages/gnocchiclient/shell.py`

将130行内容修改为：

os.environ["OS_AUTH_TYPE"] = "password"

修改前：

![点击放大](https://support.huaweicloud.com/dpmg-kunpengcpfs/zh-cn_image_0214513727.png)

修改后：

![点击放大](https://support.huaweicloud.com/dpmg-kunpengcpfs/zh-cn_image_0214513728.png)



### 2.5 初始化gnocchi

初始化gnocchi的数据库、文件索引

在控制节点执行以下操作。

<font color=red><b>需要配置好后才能执行</b></font>

```gnocchi-upgrade```

赋予“/var/lib/gnocchi”文件可读写权限。

```chmod -R 777 /var/lib/gnocchi```



### 2.6 配置/启动gnocchi

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

修改goncchi-api.service

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
systemctl daemon-reload
systemctl enable gnocchi-api.service gnocchi-metricd.service  
systemctl start gnocchi-api.service gnocchi-metricd.service
```


### 2.7 聚合策略/聚合策略规则

<font color=blue><b>更新代码后，策略和默认规则已经更改为horizon-mimic，确认数据库更新后下面的命令可以不执行</b></font>

#### 2.7.1 为gnocchi创建聚合策略

   ```
gnocchi archive-policy create -d granularity:1m,points:30 -d granularity:5m,points:288 -d granularity:30m,points:336 -d granularity:2h,points:360 -d granularity:1d,points:365 -m mean -m max -m min -m count -m sum -m std -m rate:mean horizon-mimic
   ```
#### 2.7.2 修改聚合策略规则

创建规则，如果已存在，先更新规则， 创建新规则，删除旧规则

   ```
gnocchi archive-policy-rule update default -n default-origin
gnocchi archive-policy-rule create -a horizon-mimic -m "*" default
gnocchi archive-policy-rule delete default-origin
   ```





### 2.8 gnocchi-api负载均衡（写入总部署文档中）

#### 2.8.1 nginx配置

```
# 配置位置： /etc/nginx/conf.d/gnocchi.conf

upstream gnocchinfo {
    # ip_hash;
    server 192.168.230.107:8049;
    server 192.168.230.106:8041;
    server 192.168.230.109:8041;
}

server {
    listen 8041;
    client_max_body_size 10240M;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 32k;
 
    access_log            /var/log/nginx/gnocchi_wsgi.access.log;
    error_log             /var/log/nginx/gnocchi_wsgi.error.log;
    
   location / {
       proxy_pass http://gnocchinfo;
    }
}

```



#### 2.8.2 控制节点gnocchi-api端口更改

由于nginx监听了8041端口，所以和nginx相同节点的gnocchi-api端口要修改，和上面nginx里配置一致



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

版本：12.1.0
```



### 4.2 <font color=red>替换代码☆☆☆</font>

```
rpm -ivh ceilometer-12.1.0-1.noarch.rpm --force
```

安装包参考后面**6打包**章节,，安装后，会替换代码以及配置文件

替换代码（此处替换前后，不应该更改默认app名称，否则无法初始化数据库，打包时跟源码包名称，版本号一致，待测试）

### 4.3 配置文件修改

#### 4.3.1 polling文件修改

<font color=blue><b>控制节点和计算节点，ip值不同，metric相同</b></font>

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
        - custom.hardware.disk.read.bytes.average
        - custom.hardware.disk.write.bytes.average
        - custom.hardware.disk.read.requests.average
        - custom.hardware.disk.write.requests.average
      resources:
        - snmp://30.90.2.27    # ip address of this node
      interval: 60


```



#### 4.3.2 pipeline文件修改

<font color=blue><b>只在有openstack-ceilometer-notification服务的节点修改</b></font>

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



#### 4.3.3 gnocchi_resources文件修改

<font color=blue><b>只在有openstack-ceilometer-notification服务的节点修改</b></font>

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
  - name: horizon-mimic
    aggregation_methods:
      - mean
      - rate:mean
      - max
      - min
      - count
      - std
      - sum
    back_window: 0
    definition:
      - granularity: 1 minute
        timespan: 30 minutes
      - granularity: 5 minutes
        timespan: 24 hours     
      - granularity: 30 minutes
        timespan: 183 days     
      - granularity: 2 hours
        timespan: 365 days
      - granularity: 1 day
        timespan: 365 days
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
      custom.hardware.network.interface.status:
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
    attributes:
      host_name: resource_metadata.resource_url
```

#### 4.3.4 ceilometer.conf文件修改

    sed -i.default -e '/^#/d' -e '/^$/d'  /etc/ceilometer/ceilometer.conf

##### 4.3.4.1 配置部分解释

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


##### 4.3.4.2 完整配置

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



#### 4.3.5 nova配置

<font color=blue><b>在计算节点执行以下操作。</b></font>

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



#### 4.3.6 权限配置

<font color=blue><b>由于增加了命令行，所以所有节点需要增加权限</b></font>

vim /etc/sudoers
增加一行：

```
ceilometer ALL = (root) NOPASSWD: ALL
```



#### 4.3.7 entry_points.txt文件修改(更新rpm包后，不用操作)

`/usr/lib/python2.7/site-packages/ceilometer-12.0.0-py2.7.egg-info`

```
[ceilometer.builder.poll.central]
hardware.snmp = ceilometer.hardware.pollsters.generic:GenericHardwareDeclarativePollster

[ceilometer.compute.virt]
hyperv = ceilometer.compute.virt.hyperv.inspector:HyperVInspector
libvirt = ceilometer.compute.virt.libvirt.inspector:LibvirtInspector
vsphere = ceilometer.compute.virt.vmware.inspector:VsphereInspector
xenapi = ceilometer.compute.virt.xenapi.inspector:XenapiInspector

[ceilometer.discover.central]
endpoint = ceilometer.polling.discovery.endpoint:EndpointDiscovery
fip_services = ceilometer.network.services.discovery:FloatingIPDiscovery
fw_policy = ceilometer.network.services.discovery:FirewallPolicyDiscovery
fw_services = ceilometer.network.services.discovery:FirewallDiscovery
images = ceilometer.image.discovery:ImagesDiscovery
ipsec_connections = ceilometer.network.services.discovery:IPSecConnectionsDiscovery
lb_health_probes = ceilometer.network.services.discovery:LBHealthMonitorsDiscovery
lb_listeners = ceilometer.network.services.discovery:LBListenersDiscovery
lb_loadbalancers = ceilometer.network.services.discovery:LBLoadBalancersDiscovery
lb_members = ceilometer.network.services.discovery:LBMembersDiscovery
lb_pools = ceilometer.network.services.discovery:LBPoolsDiscovery
lb_vips = ceilometer.network.services.discovery:LBVipsDiscovery
tenant = ceilometer.polling.discovery.tenant:TenantDiscovery
tripleo_overcloud_nodes = ceilometer.hardware.discovery:NodesDiscoveryTripleO
volume_backups = ceilometer.volume.discovery:VolumeBackupsDiscovery
volume_snapshots = ceilometer.volume.discovery:VolumeSnapshotsDiscovery
volumes = ceilometer.volume.discovery:VolumeDiscovery
vpn_services = ceilometer.network.services.discovery:VPNServicesDiscovery

[ceilometer.discover.compute]
local_instances = ceilometer.compute.discovery:InstanceDiscovery

[ceilometer.discover.ipmi]
local_node = ceilometer.polling.discovery.localnode:LocalNodeDiscovery

[ceilometer.event.publisher]
gnocchi = ceilometer.publisher.gnocchi:GnocchiPublisher
http = ceilometer.publisher.http:HttpPublisher
https = ceilometer.publisher.http:HttpPublisher
notifier = ceilometer.publisher.messaging:EventNotifierPublisher
test = ceilometer.publisher.test:TestPublisher
zaqar = ceilometer.publisher.zaqar:ZaqarPublisher

[ceilometer.event.trait_plugin]
bitfield = ceilometer.event.trait_plugins:BitfieldTraitPlugin
split = ceilometer.event.trait_plugins:SplitterTraitPlugin
timedelta = ceilometer.event.trait_plugins:TimedeltaPlugin

[ceilometer.hardware.inspectors]
snmp = ceilometer.hardware.inspector.snmp:SNMPInspector

[ceilometer.notification.pipeline]
event = ceilometer.pipeline.event:EventPipelineManager
meter = ceilometer.pipeline.sample:SamplePipelineManager

[ceilometer.poll.central]
image.size = ceilometer.image.glance:ImageSizePollster
ip.floating = ceilometer.network.floatingip:FloatingIPPollster
network.services.firewall = ceilometer.network.services.fwaas:FirewallPollster
network.services.firewall.policy = ceilometer.network.services.fwaas:FirewallPolicyPollster
network.services.lb.active.connections = ceilometer.network.services.lbaas:LBActiveConnectionsPollster
network.services.lb.health_monitor = ceilometer.network.services.lbaas:LBHealthMonitorPollster
network.services.lb.incoming.bytes = ceilometer.network.services.lbaas:LBBytesInPollster
network.services.lb.listener = ceilometer.network.services.lbaas:LBListenerPollster
network.services.lb.loadbalancer = ceilometer.network.services.lbaas:LBLoadBalancerPollster
network.services.lb.member = ceilometer.network.services.lbaas:LBMemberPollster
network.services.lb.outgoing.bytes = ceilometer.network.services.lbaas:LBBytesOutPollster
network.services.lb.pool = ceilometer.network.services.lbaas:LBPoolPollster
network.services.lb.total.connections = ceilometer.network.services.lbaas:LBTotalConnectionsPollster
network.services.lb.vip = ceilometer.network.services.lbaas:LBVipPollster
network.services.vpn = ceilometer.network.services.vpnaas:VPNServicesPollster
network.services.vpn.connections = ceilometer.network.services.vpnaas:IPSecConnectionsPollster
port = ceilometer.network.statistics.port_v2:PortPollster
port.receive.bytes = ceilometer.network.statistics.port_v2:PortPollsterReceiveBytes
port.receive.drops = ceilometer.network.statistics.port_v2:PortPollsterReceiveDrops
port.receive.errors = ceilometer.network.statistics.port_v2:PortPollsterReceiveErrors
port.receive.packets = ceilometer.network.statistics.port_v2:PortPollsterReceivePackets
port.transmit.bytes = ceilometer.network.statistics.port_v2:PortPollsterTransmitBytes
port.transmit.packets = ceilometer.network.statistics.port_v2:PortPollsterTransmitPackets
port.uptime = ceilometer.network.statistics.port_v2:PortPollsterUptime
radosgw.containers.objects = ceilometer.objectstore.rgw:ContainersObjectsPollster
radosgw.containers.objects.size = ceilometer.objectstore.rgw:ContainersSizePollster
radosgw.objects = ceilometer.objectstore.rgw:ObjectsPollster
radosgw.objects.containers = ceilometer.objectstore.rgw:ObjectsContainersPollster
radosgw.objects.size = ceilometer.objectstore.rgw:ObjectsSizePollster
radosgw.usage = ceilometer.objectstore.rgw:UsagePollster
storage.containers.objects = ceilometer.objectstore.swift:ContainersObjectsPollster
storage.containers.objects.size = ceilometer.objectstore.swift:ContainersSizePollster
storage.objects = ceilometer.objectstore.swift:ObjectsPollster
storage.objects.containers = ceilometer.objectstore.swift:ObjectsContainersPollster
storage.objects.size = ceilometer.objectstore.swift:ObjectsSizePollster
switch = ceilometer.network.statistics.switch:SWPollster
switch.flow = ceilometer.network.statistics.flow:FlowPollster
switch.flow.bytes = ceilometer.network.statistics.flow:FlowPollsterBytes
switch.flow.duration.nanoseconds = ceilometer.network.statistics.flow:FlowPollsterDurationNanoseconds
switch.flow.duration.seconds = ceilometer.network.statistics.flow:FlowPollsterDurationSeconds
switch.flow.packets = ceilometer.network.statistics.flow:FlowPollsterPackets
switch.port = ceilometer.network.statistics.port:PortPollster
switch.port.collision.count = ceilometer.network.statistics.port:PortPollsterCollisionCount
switch.port.receive.bytes = ceilometer.network.statistics.port:PortPollsterReceiveBytes
switch.port.receive.crc_error = ceilometer.network.statistics.port:PortPollsterReceiveCRCErrors
switch.port.receive.drops = ceilometer.network.statistics.port:PortPollsterReceiveDrops
switch.port.receive.errors = ceilometer.network.statistics.port:PortPollsterReceiveErrors
switch.port.receive.frame_error = ceilometer.network.statistics.port:PortPollsterReceiveFrameErrors
switch.port.receive.overrun_error = ceilometer.network.statistics.port:PortPollsterReceiveOverrunErrors
switch.port.receive.packets = ceilometer.network.statistics.port:PortPollsterReceivePackets
switch.port.transmit.bytes = ceilometer.network.statistics.port:PortPollsterTransmitBytes
switch.port.transmit.drops = ceilometer.network.statistics.port:PortPollsterTransmitDrops
switch.port.transmit.errors = ceilometer.network.statistics.port:PortPollsterTransmitErrors
switch.port.transmit.packets = ceilometer.network.statistics.port:PortPollsterTransmitPackets
switch.port.uptime = ceilometer.network.statistics.port:PortPollsterUptime
switch.ports = ceilometer.network.statistics.switch:SwitchPollsterPorts
switch.table = ceilometer.network.statistics.table:TablePollster
switch.table.active.entries = ceilometer.network.statistics.table:TablePollsterActiveEntries
switch.table.lookup.packets = ceilometer.network.statistics.table:TablePollsterLookupPackets
switch.table.matched.packets = ceilometer.network.statistics.table:TablePollsterMatchedPackets
volume.backup.size = ceilometer.volume.cinder:VolumeBackupSize
volume.size = ceilometer.volume.cinder:VolumeSizePollster
volume.snapshot.size = ceilometer.volume.cinder:VolumeSnapshotSize

[ceilometer.poll.compute]
cpu = ceilometer.compute.pollsters.instance_stats:CPUPollster
cpu_l3_cache = ceilometer.compute.pollsters.instance_stats:CPUL3CachePollster
cpu_util = ceilometer.compute.pollsters.instance_stats:CPUUtilPollster
disk.device.allocation = ceilometer.compute.pollsters.disk:PerDeviceAllocationPollster
disk.device.capacity = ceilometer.compute.pollsters.disk:PerDeviceCapacityPollster
disk.device.iops = ceilometer.compute.pollsters.disk:PerDeviceDiskIOPSPollster
disk.device.latency = ceilometer.compute.pollsters.disk:PerDeviceDiskLatencyPollster
disk.device.read.bytes = ceilometer.compute.pollsters.disk:PerDeviceReadBytesPollster
disk.device.read.latency = ceilometer.compute.pollsters.disk:PerDeviceDiskReadLatencyPollster
disk.device.read.requests = ceilometer.compute.pollsters.disk:PerDeviceReadRequestsPollster
disk.device.usage = ceilometer.compute.pollsters.disk:PerDevicePhysicalPollster
disk.device.write.bytes = ceilometer.compute.pollsters.disk:PerDeviceWriteBytesPollster
disk.device.write.latency = ceilometer.compute.pollsters.disk:PerDeviceDiskWriteLatencyPollster
disk.device.write.requests = ceilometer.compute.pollsters.disk:PerDeviceWriteRequestsPollster
memory.bandwidth.local = ceilometer.compute.pollsters.instance_stats:MemoryBandwidthLocalPollster
memory.bandwidth.total = ceilometer.compute.pollsters.instance_stats:MemoryBandwidthTotalPollster
memory.resident = ceilometer.compute.pollsters.instance_stats:MemoryResidentPollster
memory.swap.in = ceilometer.compute.pollsters.instance_stats:MemorySwapInPollster
memory.swap.out = ceilometer.compute.pollsters.instance_stats:MemorySwapOutPollster
memory.usage = ceilometer.compute.pollsters.instance_stats:MemoryUsagePollster
memory.util = ceilometer.compute.pollsters.instance_stats:MemoryUtilPollster
memory = ceilometer.compute.pollsters.instance_stats:MemoryPollster
network.incoming.bytes = ceilometer.compute.pollsters.net:IncomingBytesPollster
network.incoming.bytes.rate = ceilometer.compute.pollsters.net:IncomingBytesRatePollster
network.incoming.packets = ceilometer.compute.pollsters.net:IncomingPacketsPollster
network.incoming.packets.drop = ceilometer.compute.pollsters.net:IncomingDropPollster
network.incoming.packets.error = ceilometer.compute.pollsters.net:IncomingErrorsPollster
network.outgoing.bytes = ceilometer.compute.pollsters.net:OutgoingBytesPollster
network.outgoing.bytes.rate = ceilometer.compute.pollsters.net:OutgoingBytesRatePollster
network.outgoing.packets = ceilometer.compute.pollsters.net:OutgoingPacketsPollster
network.outgoing.packets.drop = ceilometer.compute.pollsters.net:OutgoingDropPollster
network.outgoing.packets.error = ceilometer.compute.pollsters.net:OutgoingErrorsPollster
perf.cache.misses = ceilometer.compute.pollsters.instance_stats:PerfCacheMissesPollster
perf.cache.references = ceilometer.compute.pollsters.instance_stats:PerfCacheReferencesPollster
perf.cpu.cycles = ceilometer.compute.pollsters.instance_stats:PerfCPUCyclesPollster
perf.instructions = ceilometer.compute.pollsters.instance_stats:PerfInstructionsPollster

[ceilometer.poll.ipmi]
hardware.ipmi.current = ceilometer.ipmi.pollsters.sensor:CurrentSensorPollster
hardware.ipmi.fan = ceilometer.ipmi.pollsters.sensor:FanSensorPollster
hardware.ipmi.node.airflow = ceilometer.ipmi.pollsters.node:AirflowPollster
hardware.ipmi.node.cpu_util = ceilometer.ipmi.pollsters.node:CPUUtilPollster
hardware.ipmi.node.cups = ceilometer.ipmi.pollsters.node:CUPSIndexPollster
hardware.ipmi.node.io_util = ceilometer.ipmi.pollsters.node:IOUtilPollster
hardware.ipmi.node.mem_util = ceilometer.ipmi.pollsters.node:MemUtilPollster
hardware.ipmi.node.outlet_temperature = ceilometer.ipmi.pollsters.node:OutletTemperaturePollster
hardware.ipmi.node.power = ceilometer.ipmi.pollsters.node:PowerPollster
hardware.ipmi.node.temperature = ceilometer.ipmi.pollsters.node:InletTemperaturePollster
hardware.ipmi.temperature = ceilometer.ipmi.pollsters.sensor:TemperatureSensorPollster
hardware.ipmi.voltage = ceilometer.ipmi.pollsters.sensor:VoltageSensorPollster

[ceilometer.sample.endpoint]
_sample = ceilometer.telemetry.notifications:TelemetryIpc
hardware.ipmi.current = ceilometer.ipmi.notifications.ironic:CurrentSensorNotification
hardware.ipmi.fan = ceilometer.ipmi.notifications.ironic:FanSensorNotification
hardware.ipmi.temperature = ceilometer.ipmi.notifications.ironic:TemperatureSensorNotification
hardware.ipmi.voltage = ceilometer.ipmi.notifications.ironic:VoltageSensorNotification
http.request = ceilometer.middleware:HTTPRequest
http.response = ceilometer.middleware:HTTPResponse
meter = ceilometer.meter.notifications:ProcessMeterNotifications

[ceilometer.sample.publisher]
file = ceilometer.publisher.file:FilePublisher
gnocchi = ceilometer.publisher.gnocchi:GnocchiPublisher
http = ceilometer.publisher.http:HttpPublisher
https = ceilometer.publisher.http:HttpPublisher
notifier = ceilometer.publisher.messaging:SampleNotifierPublisher
prometheus = ceilometer.publisher.prometheus:PrometheusPublisher
test = ceilometer.publisher.test:TestPublisher
udp = ceilometer.publisher.udp:UDPPublisher
zaqar = ceilometer.publisher.zaqar:ZaqarPublisher

[console_scripts]
ceilometer-agent-notification = ceilometer.cmd.agent_notification:main
ceilometer-polling = ceilometer.cmd.polling:main
ceilometer-rootwrap = oslo_rootwrap.cmd:main
ceilometer-send-sample = ceilometer.cmd.sample:send_sample
ceilometer-status = ceilometer.cmd.status:main
ceilometer-upgrade = ceilometer.cmd.storage:upgrade

[network.statistics.drivers]
opencontrail = ceilometer.network.statistics.opencontrail.driver:OpencontrailDriver
opendaylight = ceilometer.network.statistics.opendaylight.driver:OpenDayLightDriver

[oslo.config.opts]
ceilometer = ceilometer.opts:list_opts
ceilometer-auth = ceilometer.opts:list_keystoneauth_opts

```

 

### 4.4 初始化资源、数据库

 在Gnocchi创建Ceilometer资源。

`ceilometer-upgrade`

   **![img](https://res-img2.huaweicloud.com/content/dam/cloudbu-site/archive/china/zh-cn/support/resource/framework/v3/images/support-doc-new-notice.svg)须知：**

   Gnocchi必须在这个阶段状态为运行。

### 4.5 启动服务



<font color=blue><b>控制节点</b></font>

   ```
systemctl enable openstack-ceilometer-notification.service  openstack-ceilometer-central.service
systemctl start openstack-ceilometer-notification.service openstack-ceilometer-central.service
   ```

<font color=blue><b>计算节点</b></font>

```
systemctl enable openstack-ceilometer-central.service openstack-ceilometer-compute.service
systemctl start openstack-ceilometer-central.service openstack-ceilometer-compute.service
```

<font color=blue><b>再次更新配置</b></font>

```
ceilometer-upgrade
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

### 6.1 ceilometer打包

#### 6.1.1 新建目录(如openstack-ceilometer)

#### 6.1.2 拷贝文件

目录中包含，ceilometer/源码，polling.yaml/pipeline.yaml/gnocchi_resources.yaml三个配置文件，以及setup.py文件，yaml文件内容见章节4.3.1--4.3.3

![img](.\ceilometer打包目录.png)



setup.py文件内容如下：

```
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(name='ceilometer',
      version='12.1.0',
      description='dm-mcs-ceilometer v2.0.0',
      author='xindawangyu',
      author_email='xindawangyu',
      url='www.ieucd.com',
      license='GPL',
      packages=find_packages(),
      package_data = {'ceilometer': ['test.log', 'pipeline/data/*.yaml', 'hardware/pollsters/data/*.yaml', 'publisher/data/*.yaml', 'data/meters.d/*.yaml']},
      data_files=[
                ('/etc/ceilometer/', ['./conf/polling.yaml']),
                ('/etc/ceilometer/', ['./conf/pipeline.yaml']),
                ('/etc/ceilometer/', ['./conf/gnocchi_resources.yaml']),
                 ],
      entry_points={
    'ceilometer.builder.poll.central': [
    'hardware.snmp = ceilometer.hardware.pollsters.generic:GenericHardwareDeclarativePollster'],
                'ceilometer.compute.virt': ['hyperv = ceilometer.compute.virt.hyperv.inspector:HyperVInspector',
                                            'libvirt = ceilometer.compute.virt.libvirt.inspector:LibvirtInspector',
                                            'vsphere = ceilometer.compute.virt.vmware.inspector:VsphereInspector',
                                            'xenapi = ceilometer.compute.virt.xenapi.inspector:XenapiInspector'],
                'ceilometer.discover.central': ['endpoint = ceilometer.polling.discovery.endpoint:EndpointDiscovery',
                                                'fip_services = ceilometer.network.services.discovery:FloatingIPDiscovery',
                                                'fw_policy = ceilometer.network.services.discovery:FirewallPolicyDiscovery',
                                                'fw_services = ceilometer.network.services.discovery:FirewallDiscovery',
                                                'images = ceilometer.image.discovery:ImagesDiscovery',
                                                'ipsec_connections = ceilometer.network.services.discovery:IPSecConnectionsDiscovery',
                                                'lb_health_probes = ceilometer.network.services.discovery:LBHealthMonitorsDiscovery',
                                                'lb_listeners = ceilometer.network.services.discovery:LBListenersDiscovery',
                                                'lb_loadbalancers = ceilometer.network.services.discovery:LBLoadBalancersDiscovery',
                                                'lb_members = ceilometer.network.services.discovery:LBMembersDiscovery',
                                                'lb_pools = ceilometer.network.services.discovery:LBPoolsDiscovery',
                                                'lb_vips = ceilometer.network.services.discovery:LBVipsDiscovery',
                                                'tenant = ceilometer.polling.discovery.tenant:TenantDiscovery',
                                                'tripleo_overcloud_nodes = ceilometer.hardware.discovery:NodesDiscoveryTripleO',
                                                'volume_backups = ceilometer.volume.discovery:VolumeBackupsDiscovery',
                                                'volume_snapshots = ceilometer.volume.discovery:VolumeSnapshotsDiscovery',
                                                'volumes = ceilometer.volume.discovery:VolumeDiscovery',
                                                'vpn_services = ceilometer.network.services.discovery:VPNServicesDiscovery'],
                'ceilometer.discover.compute': ['local_instances = ceilometer.compute.discovery:InstanceDiscovery'],
                'ceilometer.discover.ipmi': ['local_node = ceilometer.polling.discovery.localnode:LocalNodeDiscovery'],
                'ceilometer.event.publisher': ['gnocchi = ceilometer.publisher.gnocchi:GnocchiPublisher',
                                               'http = ceilometer.publisher.http:HttpPublisher',
                                               'https = ceilometer.publisher.http:HttpPublisher',
                                               'notifier = ceilometer.publisher.messaging:EventNotifierPublisher',
                                               'test = ceilometer.publisher.test:TestPublisher',
                                               'zaqar = ceilometer.publisher.zaqar:ZaqarPublisher'],
                'ceilometer.event.trait_plugin': ['bitfield = ceilometer.event.trait_plugins:BitfieldTraitPlugin',
                                                  'split = ceilometer.event.trait_plugins:SplitterTraitPlugin',
                                                  'timedelta = ceilometer.event.trait_plugins:TimedeltaPlugin'],
                'ceilometer.hardware.inspectors': ['snmp = ceilometer.hardware.inspector.snmp:SNMPInspector'],
                'ceilometer.notification.pipeline': ['event = ceilometer.pipeline.event:EventPipelineManager',
                                                     'meter = ceilometer.pipeline.sample:SamplePipelineManager'],
                'ceilometer.poll.central': ['image.size = ceilometer.image.glance:ImageSizePollster',
                                            'ip.floating = ceilometer.network.floatingip:FloatingIPPollster',
                                            'network.services.firewall = ceilometer.network.services.fwaas:FirewallPollster',
                                            'network.services.firewall.policy = ceilometer.network.services.fwaas:FirewallPolicyPollster',
                                            'network.services.lb.active.connections = ceilometer.network.services.lbaas:LBActiveConnectionsPollster',
                                            'network.services.lb.health_monitor = ceilometer.network.services.lbaas:LBHealthMonitorPollster',
                                            'network.services.lb.incoming.bytes = ceilometer.network.services.lbaas:LBBytesInPollster',
                                            'network.services.lb.listener = ceilometer.network.services.lbaas:LBListenerPollster',
                                            'network.services.lb.loadbalancer = ceilometer.network.services.lbaas:LBLoadBalancerPollster',
                                            'network.services.lb.member = ceilometer.network.services.lbaas:LBMemberPollster',
                                            'network.services.lb.outgoing.bytes = ceilometer.network.services.lbaas:LBBytesOutPollster',
                                            'network.services.lb.pool = ceilometer.network.services.lbaas:LBPoolPollster',
                                            'network.services.lb.total.connections = ceilometer.network.services.lbaas:LBTotalConnectionsPollster',
                                            'network.services.lb.vip = ceilometer.network.services.lbaas:LBVipPollster',
                                            'network.services.vpn = ceilometer.network.services.vpnaas:VPNServicesPollster',
                                            'network.services.vpn.connections = ceilometer.network.services.vpnaas:IPSecConnectionsPollster',
                                            'port = ceilometer.network.statistics.port_v2:PortPollster',
                                            'port.receive.bytes = ceilometer.network.statistics.port_v2:PortPollsterReceiveBytes',
                                            'port.receive.drops = ceilometer.network.statistics.port_v2:PortPollsterReceiveDrops',
                                            'port.receive.errors = ceilometer.network.statistics.port_v2:PortPollsterReceiveErrors',
                                            'port.receive.packets = ceilometer.network.statistics.port_v2:PortPollsterReceivePackets',
                                            'port.transmit.bytes = ceilometer.network.statistics.port_v2:PortPollsterTransmitBytes',
                                            'port.transmit.packets = ceilometer.network.statistics.port_v2:PortPollsterTransmitPackets',
                                            'port.uptime = ceilometer.network.statistics.port_v2:PortPollsterUptime',
                                            'radosgw.containers.objects = ceilometer.objectstore.rgw:ContainersObjectsPollster',
                                            'radosgw.containers.objects.size = ceilometer.objectstore.rgw:ContainersSizePollster',
                                            'radosgw.objects = ceilometer.objectstore.rgw:ObjectsPollster',
                                            'radosgw.objects.containers = ceilometer.objectstore.rgw:ObjectsContainersPollster',
                                            'radosgw.objects.size = ceilometer.objectstore.rgw:ObjectsSizePollster',
                                            'radosgw.usage = ceilometer.objectstore.rgw:UsagePollster',
                                            'storage.containers.objects = ceilometer.objectstore.swift:ContainersObjectsPollster',
                                            'storage.containers.objects.size = ceilometer.objectstore.swift:ContainersSizePollster',
                                            'storage.objects = ceilometer.objectstore.swift:ObjectsPollster',
                                            'storage.objects.containers = ceilometer.objectstore.swift:ObjectsContainersPollster',
                                            'storage.objects.size = ceilometer.objectstore.swift:ObjectsSizePollster',
                                            'switch = ceilometer.network.statistics.switch:SWPollster',
                                            'switch.flow = ceilometer.network.statistics.flow:FlowPollster',
                                            'switch.flow.bytes = ceilometer.network.statistics.flow:FlowPollsterBytes',
                                            'switch.flow.duration.nanoseconds = ceilometer.network.statistics.flow:FlowPollsterDurationNanoseconds',
                                            'switch.flow.duration.seconds = ceilometer.network.statistics.flow:FlowPollsterDurationSeconds',
                                            'switch.flow.packets = ceilometer.network.statistics.flow:FlowPollsterPackets',
                                            'switch.port = ceilometer.network.statistics.port:PortPollster',
                                            'switch.port.collision.count = ceilometer.network.statistics.port:PortPollsterCollisionCount',
                                            'switch.port.receive.bytes = ceilometer.network.statistics.port:PortPollsterReceiveBytes',
                                            'switch.port.receive.crc_error = ceilometer.network.statistics.port:PortPollsterReceiveCRCErrors',
                                            'switch.port.receive.drops = ceilometer.network.statistics.port:PortPollsterReceiveDrops',
                                            'switch.port.receive.errors = ceilometer.network.statistics.port:PortPollsterReceiveErrors',
                                            'switch.port.receive.frame_error = ceilometer.network.statistics.port:PortPollsterReceiveFrameErrors',
                                            'switch.port.receive.overrun_error = ceilometer.network.statistics.port:PortPollsterReceiveOverrunErrors',
                                            'switch.port.receive.packets = ceilometer.network.statistics.port:PortPollsterReceivePackets',
                                            'switch.port.transmit.bytes = ceilometer.network.statistics.port:PortPollsterTransmitBytes',
                                            'switch.port.transmit.drops = ceilometer.network.statistics.port:PortPollsterTransmitDrops',
                                            'switch.port.transmit.errors = ceilometer.network.statistics.port:PortPollsterTransmitErrors',
                                            'switch.port.transmit.packets = ceilometer.network.statistics.port:PortPollsterTransmitPackets',
                                            'switch.port.uptime = ceilometer.network.statistics.port:PortPollsterUptime',
                                            'switch.ports = ceilometer.network.statistics.switch:SwitchPollsterPorts',
                                            'switch.table = ceilometer.network.statistics.table:TablePollster',
                                            'switch.table.active.entries = ceilometer.network.statistics.table:TablePollsterActiveEntries',
                                            'switch.table.lookup.packets = ceilometer.network.statistics.table:TablePollsterLookupPackets',
                                            'switch.table.matched.packets = ceilometer.network.statistics.table:TablePollsterMatchedPackets',
                                            'volume.backup.size = ceilometer.volume.cinder:VolumeBackupSize',
                                            'volume.size = ceilometer.volume.cinder:VolumeSizePollster',
                                            'volume.snapshot.size = ceilometer.volume.cinder:VolumeSnapshotSize'],
                'ceilometer.poll.compute': ['cpu = ceilometer.compute.pollsters.instance_stats:CPUPollster',
                                            'cpu_l3_cache = ceilometer.compute.pollsters.instance_stats:CPUL3CachePollster',
                                            'cpu_util = ceilometer.compute.pollsters.instance_stats:CPUUtilPollster',
                                            'disk.device.allocation = ceilometer.compute.pollsters.disk:PerDeviceAllocationPollster',
                                            'disk.device.capacity = ceilometer.compute.pollsters.disk:PerDeviceCapacityPollster',
                                            'disk.device.iops = ceilometer.compute.pollsters.disk:PerDeviceDiskIOPSPollster',
                                            'disk.device.latency = ceilometer.compute.pollsters.disk:PerDeviceDiskLatencyPollster',
                                            'disk.device.read.bytes = ceilometer.compute.pollsters.disk:PerDeviceReadBytesPollster',
                                            'disk.device.read.latency = ceilometer.compute.pollsters.disk:PerDeviceDiskReadLatencyPollster',
                                            'disk.device.read.requests = ceilometer.compute.pollsters.disk:PerDeviceReadRequestsPollster',
                                            'disk.device.usage = ceilometer.compute.pollsters.disk:PerDevicePhysicalPollster',
                                            'disk.device.write.bytes = ceilometer.compute.pollsters.disk:PerDeviceWriteBytesPollster',
                                            'disk.device.write.latency = ceilometer.compute.pollsters.disk:PerDeviceDiskWriteLatencyPollster',
                                            'disk.device.write.requests = ceilometer.compute.pollsters.disk:PerDeviceWriteRequestsPollster',
                                            'memory.bandwidth.local = ceilometer.compute.pollsters.instance_stats:MemoryBandwidthLocalPollster',
                                            'memory.bandwidth.total = ceilometer.compute.pollsters.instance_stats:MemoryBandwidthTotalPollster',
                                            'memory.resident = ceilometer.compute.pollsters.instance_stats:MemoryResidentPollster',
                                            'memory.swap.in = ceilometer.compute.pollsters.instance_stats:MemorySwapInPollster',
                                            'memory.swap.out = ceilometer.compute.pollsters.instance_stats:MemorySwapOutPollster',
                                            'memory.usage = ceilometer.compute.pollsters.instance_stats:MemoryUsagePollster',
                                            'memory.util = ceilometer.compute.pollsters.instance_stats:MemoryUtilPollster',
                                            'memory = ceilometer.compute.pollsters.instance_stats:MemoryPollster',
                                            'network.incoming.bytes = ceilometer.compute.pollsters.net:IncomingBytesPollster',
                                            'network.incoming.bytes.rate = ceilometer.compute.pollsters.net:IncomingBytesRatePollster',
                                            'network.incoming.packets = ceilometer.compute.pollsters.net:IncomingPacketsPollster',
                                            'network.incoming.packets.drop = ceilometer.compute.pollsters.net:IncomingDropPollster',
                                            'network.incoming.packets.error = ceilometer.compute.pollsters.net:IncomingErrorsPollster',
                                            'network.outgoing.bytes = ceilometer.compute.pollsters.net:OutgoingBytesPollster',
                                            'network.outgoing.bytes.rate = ceilometer.compute.pollsters.net:OutgoingBytesRatePollster',
                                            'network.outgoing.packets = ceilometer.compute.pollsters.net:OutgoingPacketsPollster',
                                            'network.outgoing.packets.drop = ceilometer.compute.pollsters.net:OutgoingDropPollster',
                                            'network.outgoing.packets.error = ceilometer.compute.pollsters.net:OutgoingErrorsPollster',
                                            'perf.cache.misses = ceilometer.compute.pollsters.instance_stats:PerfCacheMissesPollster',
                                            'perf.cache.references = ceilometer.compute.pollsters.instance_stats:PerfCacheReferencesPollster',
                                            'perf.cpu.cycles = ceilometer.compute.pollsters.instance_stats:PerfCPUCyclesPollster',
                                            'perf.instructions = ceilometer.compute.pollsters.instance_stats:PerfInstructionsPollster'],
                'ceilometer.poll.ipmi': [
                    'hardware.ipmi.current = ceilometer.ipmi.pollsters.sensor:CurrentSensorPollster',
                    'hardware.ipmi.fan = ceilometer.ipmi.pollsters.sensor:FanSensorPollster',
                    'hardware.ipmi.node.airflow = ceilometer.ipmi.pollsters.node:AirflowPollster',
                    'hardware.ipmi.node.cpu_util = ceilometer.ipmi.pollsters.node:CPUUtilPollster',
                    'hardware.ipmi.node.cups = ceilometer.ipmi.pollsters.node:CUPSIndexPollster',
                    'hardware.ipmi.node.io_util = ceilometer.ipmi.pollsters.node:IOUtilPollster',
                    'hardware.ipmi.node.mem_util = ceilometer.ipmi.pollsters.node:MemUtilPollster',
                    'hardware.ipmi.node.outlet_temperature = ceilometer.ipmi.pollsters.node:OutletTemperaturePollster',
                    'hardware.ipmi.node.power = ceilometer.ipmi.pollsters.node:PowerPollster',
                    'hardware.ipmi.node.temperature = ceilometer.ipmi.pollsters.node:InletTemperaturePollster',
                    'hardware.ipmi.temperature = ceilometer.ipmi.pollsters.sensor:TemperatureSensorPollster',
                    'hardware.ipmi.voltage = ceilometer.ipmi.pollsters.sensor:VoltageSensorPollster'],
                'ceilometer.sample.endpoint': ['_sample = ceilometer.telemetry.notifications:TelemetryIpc',
                                               'hardware.ipmi.current = ceilometer.ipmi.notifications.ironic:CurrentSensorNotification',
                                               'hardware.ipmi.fan = ceilometer.ipmi.notifications.ironic:FanSensorNotification',
                                               'hardware.ipmi.temperature = ceilometer.ipmi.notifications.ironic:TemperatureSensorNotification',
                                               'hardware.ipmi.voltage = ceilometer.ipmi.notifications.ironic:VoltageSensorNotification',
                                               'http.request = ceilometer.middleware:HTTPRequest',
                                               'http.response = ceilometer.middleware:HTTPResponse',
                                               'meter = ceilometer.meter.notifications:ProcessMeterNotifications'],
                'ceilometer.sample.publisher': ['file = ceilometer.publisher.file:FilePublisher',
                                                'gnocchi = ceilometer.publisher.gnocchi:GnocchiPublisher',
                                                'http = ceilometer.publisher.http:HttpPublisher',
                                                'https = ceilometer.publisher.http:HttpPublisher',
                                                'notifier = ceilometer.publisher.messaging:SampleNotifierPublisher',
                                                'prometheus = ceilometer.publisher.prometheus:PrometheusPublisher',
                                                'test = ceilometer.publisher.test:TestPublisher',
                                                'udp = ceilometer.publisher.udp:UDPPublisher',
                                                'zaqar = ceilometer.publisher.zaqar:ZaqarPublisher'],
                'console_scripts': ['ceilometer-agent-notification = ceilometer.cmd.agent_notification:main',
                                    'ceilometer-polling = ceilometer.cmd.polling:main',
                                    'ceilometer-rootwrap = oslo_rootwrap.cmd:main',
                                    'ceilometer-send-sample = ceilometer.cmd.sample:send_sample',
                                    'ceilometer-status = ceilometer.cmd.status:main',
                                    'ceilometer-upgrade = ceilometer.cmd.storage:upgrade'],
                'network.statistics.drivers': [
                    'opencontrail = ceilometer.network.statistics.opencontrail.driver:OpencontrailDriver',
                    'opendaylight = ceilometer.network.statistics.opendaylight.driver:OpenDayLightDriver'],
                'oslo.config.opts': ['ceilometer = ceilometer.opts:list_opts',
                                     'ceilometer-auth = ceilometer.opts:list_keystoneauth_opts']},
)

```

#### 6.1.3 生成rpm包

```
python setup.py bdist_rpm
```

entry_points文件打包进去有问题，暂时没有放到包里



### 6.2 gnocchi打包

#### 6.2.1 新建目录(如openstack-gnocchi/)

#### 6.2.2 拷贝文件

目录中包含，gnochi/源码，gnocchi/uwsgi-gnocchi.ini/openstack-gnocchi-api.service，以及setup.py文件

![img](.\gnocchi打包目录.png)



setup.py文件

内容如下：

```
from setuptools import setup, find_packages

setup(name='gnocchi',
      version='4.3.2',
      description='dm-mcs-gnocchi-1.0.5',
      author='xindawangyu',
      author_email='xindawangyu',
      url='www.ieucd.com',
      license='GPL',
      packages=find_packages(),
      package_data={'gnocchi':['gnocchi-config-generator.conf', 'indexer/alembic/versions/*.py',
                     'indexer/alembic/*.*','rest/prometheus/*.*','rest/*.*', 'tests/functional/gabbits/*.yaml',
                     'tests/functional/gabbits/prometheus_fixtures/*.dump', 'tests/functional_live/gabbits/*.yaml']},
      data_files=[
          ('/etc/logrotate.d/', ['./conf/gnocchi']),
          ('/etc/gnocchi/', ['./conf/uwsgi-gnocchi.ini']),
          ('/usr/lib/systemd/system/', ['./conf/gnocchi-api.service']),
      ],
      )
```

gnocchi日志切割文件

```
/var/log/gnocchi/*.log {
    rotate 4
    size 10M
    missingok
    compress
    copytruncate  
}
```

uwsgi-gnocchi.ini

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

gnocchi-api.service

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



#### 6.2.3 生成rpm包

```
python setup.py  bdist_rpm
```


