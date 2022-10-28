## Gnocchi在 kp-compute-ubuntu18.04.5 LTS-aarch64下部署方法



>具体部署机器信息：
>
>系统信息：Linux kp-compute 4.15.0-112-generic #113-Ubuntu SMP Thu Jul 9 23:42:54 UTC 2020 aarch64 aarch64 aarch64 GNU/Linux   
>
>系统版本：Ubuntu 18.04.5 LTS



### 1. 配置arm源

```
deb http://mirrors.ustc.edu.cn/ubuntu-ports/ bionic-updates main restricted universe multiverse
deb-src http://mirrors.ustc.edu.cn/ubuntu-ports/ bionic-updates main restricted universe multiverse
deb http://mirrors.ustc.edu.cn/ubuntu-ports/ bionic-security main restricted universe multiverse
deb-src http://mirrors.ustc.edu.cn/ubuntu-ports/ bionic-security main restricted universe multiverse
deb http://mirrors.ustc.edu.cn/ubuntu-ports/ bionic-backports main restricted universe multiverse
deb-src http://mirrors.ustc.edu.cn/ubuntu-ports/ bionic-backports main restricted universe multiverse
deb http://mirrors.ustc.edu.cn/ubuntu-ports/ bionic main universe restricted
deb-src http://mirrors.ustc.edu.cn/ubuntu-ports/ bionic main universe restricted
```



### 2. 指定openstack版本

```
 apt-get install -y software-properties-common
        add-apt-repository cloud-archive:stein
        apt-get update && apt-get dist-upgrade
        apt-get clean all
```

### 3. 安装组件需要用的包

```
apt install uwsgi/bionic-updates uwsgi-plugin-python3 python3-mysqldb/bionic sysstat
```

### 安装gnocchi

```
apt install gnocchi-api gnocchi-metricd
```

安装过程中会弹出dbconfig的配置界面

![企业微信截图_57808727-ebd1-444b-b008-27408816d8b5](./dbconfig配置.png)

全部选否，完成安装





在13.37上安装顺利，但是在232测试环境安装时，总是安装错误，提示dbconfig-common没有配置

需要修改 /var/lib/dpkg/info/xdbconfig-common.postinst文件中的
dbc_write_global_config，注释掉

```
......
# dbc_write_global_config
......
```

然后再安装就可以了



### 5. gnocchi配置

gnocchi安装完成后，默认api走的apache2服务，需要禁用掉

```
systemctl stop apache2
systemctl disable apache2
```



编写配置文件/etc/gnocchi/gnocchi.conf

```

[DEFAULT]
verbose = true
log_dir = /var/log/gnocchi
parallel_operations = 200
coordination_url = redis://:comleader@controller:6379?db=5
[api]
auth_mode = keystone
host = 10.10.13.37
port = 8041
uwsgi_mode = http-socket
max_limit = 1000
[archive_policy]
default_aggregation_methods = mean,sum,count,rate:mean
[cors]
allowed_origin = http://controller:3000
[healthcheck]
[incoming]
redis_url = redis://:comleader@controller:6379?db=5
[indexer]
url = mysql+pymysql://gnocchi:comleader@123@controller/gnocchi
[metricd]
workers = 6
metric_processing_delay = 60
greedy = false
metric_reporting_delay = 120
metric_cleanup_delay = 300
processing_replicas=3
[oslo_middleware]
[oslo_policy]
[statsd]
[storage]
redis_url = redis://:comleader@controller:6379?db=5
driver = redis
[keystone_authtoken]
www_authenticate_uri = http://nova_proxy:5000
auth_url = http://nova_proxy:5000
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



编写配置文件 /etc/gnocchi/uwsgi-gnocchi.ini

```
[uwsgi]
http-socket = 10.10.13.37:8041
wsgi-file = /usr/bin/gnocchi-api
master = true
die-on-term = true
threads = 10
processes = 8
enabled-threads = true
thunder-lock = true
plugins = python3
buffer-size = 65535
listen = 4096
logto = /var/log/gnocchi/uwsgi-gnocchi.log
max-requests = 4000
socket-timeout = 60
pidfile = /var/run/gnocchi-uwsgi.pid

```

<font color=red>注意Plugins = python3，就安装对应uwsgi-plugin-python3</font>



编写gnocchi-api服务文件, vim /lib/systemd/system/gnocchi-api.service

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



重载service

```
systemctl daemon-reload
```



启动服务

```
systemctl start gnocchi-api gnocchi-metricd
```





### 6.gnocchi负载均衡（测试中）



nginx配置文件 /etc/nginx/conf.d/gnocchi.conf

```
upstream gnocchinfo {
    # ip_hash;
    server 192.168.232.108:8041;
    server 192.168.232.103:8041;
    server 192.168.226.46:8041;
    server 192.168.232.107:8047;
}

server {
    listen 8046;
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



修改云管、monitor-cache及其他请求gnocchi-api接口的端口为 8046

重启nginx

重启其他服务





