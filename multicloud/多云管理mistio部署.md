# 多云管理mistio部署



### 1. 部署测试环境：

centos7 x86_64

4cpu ,8G内存，20G磁盘

### 2.基本配置

配置ip地址，dns，ssh远程连接

```
# 配置ip
vim /etc/sysconfig/network-script/ifcfg-etho

# 配置dns
vim /etc/resolv.conf

# 配置ssh
vim /etc/ssh/sshd_config

```



配置基本软件环境

```
yum install -y wget vim 
```



### 3.设置aliyun源

```
# 备份
mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup

# 下载
wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
或
curl -o /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo

mv /etc/yum.repos.d/Centos-7.repo /etc/yum.repos.d/CentOS-Base.repo 
# 编辑，将文件中的所有http开头的地址更改为https
vim CentOS-Base.repo
将文件中的所有http开头的地址更改为https
:%s/http/https/g
```



### 4、更新镜像源

清除缓存：yum clean all
生成缓存：yum makecache

### 5.安装docker-ce

```
# 安装必要的一些系统工具
$ sudo yum install -y yum-utils device-mapper-persistent-data lvm2

# 添加软件源信息
$ sudo yum-config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo

# 更新并安装 docker-ce 以及 compose 插件
$ sudo yum makecache fast
$ sudo yum -y install docker-ce docker-ce-cli docker-compose-plugin

# 开启 docker 服务
$ sudo systemctl enable --now docker
```



### 6.下载mist docker-compose

wget https://github.com/mistio/mist-ce/releases/download/v4.7.1/docker-compose.yml

见附件

### 7.启动服务

```
docker compose up -d
```



### 8.设置用户密码



创建用户和设置密码、

```
docker-compose exec api sh

./bin/adduser --admin admin@example.com
```



参考链接：https://github.com/mistio/mist-ce#single-host















Docker-compose.yml

```
# Docker compose definition to run mist.io in production mode, so no mounted
# code, no dev containers etc. Only this single file is required.

version: '2.0'

services:


  mongodb:
    image: mongo:3.2
    restart: on-failure:5
    volumes:
      - mongodb:/data/db:rw

  rabbitmq:
    image: mist/rabbitmq
    restart: on-failure:5

  memcached:
    image: memcached:1.6.9
    restart: on-failure:5

  elasticsearch:
    image: elasticsearch:5.6.16
    restart: on-failure:5
    volumes:
      - elasticsearch:/usr/share/elasticsearch/data:rw
    environment:
      ES_JAVA_OPTS: "-Dlog4j2.formatMsgNoLookups=true"

  logstash:
    image: mistce/logstash:v4-7-1
    restart: on-failure:5
    depends_on:
      - elasticsearch
      - rabbitmq

  elasticsearch-manage:
    image: mistce/elasticsearch-manage:v4-7-1
    command: ./scripts/add_templates.py
    restart: on-failure:5
    depends_on:
      - elasticsearch
      - rabbitmq

  kibana:
    image: kibana:5.6.10
    environment:
      ELASTICSEARCH_URL: http://elasticsearch:9200
    restart: on-failure:5
    depends_on:
      - elasticsearch

  socat:
    image: mist/docker-socat
    restart: on-failure:5
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:rw

  mailmock:
    image: mist/mailmock
    restart: on-failure:5

  swagger:
    image: mist/swagger-ui
    environment:
      API_URL: /api/v1/spec
    restart: on-failure:5


  scheduler: &backend
    image: mistce/api:v4-7-1
    depends_on:
      - mongodb
      - elasticsearch
      - rabbitmq
    volumes:
      - ./settings:/etc/mist/settings
    environment:
      SETTINGS_FILE: /etc/mist/settings/settings.py
    stdin_open: true
    tty: true
    restart: on-failure:5
    command: bin/wait-all bin/scheduler

  hubshell:
    <<: *backend
    command: bin/wait-all bin/hubshell
  
  api:
    <<: *backend
    command: bin/wait-all bin/uwsgi
    expose:
      - 80

  api-v2:
    <<: *backend
    command: uwsgi --http 0.0.0.0:8080 --wsgi-file v2/mist_api_v2/__main__.py --callable application --master --processes 8 --max-requests 100 --honour-stdin --enable-threads
    expose:
      - 8080

  sockjs:
    <<: *backend
    command: bin/wait-all bin/sockjs
    expose:
      - 8081

  apply-migrations:
    <<: *backend
    command: bin/wait-all bin/migrate

  dramatiq:
    <<: *backend
    command: bin/wait-all bin/dramatiq

  ui:
    image: mistce/ui:v4-7-1
    command: sh /entry.sh
    stdin_open: true
    tty: true
    restart: on-failure:5
    expose:
      - 80

  landing:
    image: mistce/landing:v4-7-1
    command: sh /entry.sh
    stdin_open: true
    tty: true
    restart: on-failure:5
    expose:
      - 80

  nginx:
    image: mistce/nginx:v4-7-1
    restart: on-failure:5
    ports:
      - 80:80
    depends_on:
      - api
      - sockjs
      - landing
      - ui

  vminsert:
    image: victoriametrics/vminsert:v1.60.0-cluster
    command:
      - '--influxTrimTimestamp=1s'
      - '--storageNode=vmstorage:8400'
    ports:
      - 8480

  vmstorage:
    image: victoriametrics/vmstorage:v1.60.0-cluster
    command:
      - '--retentionPeriod=12'
      - '--storageDataPath=/var/lib/victoria-metrics-data'
    ports:
      - 8400
      - 8401
      - 8482
    volumes:
      - victoria-metrics:/var/lib/victoria-metrics-data

  vmselect:
    image: victoriametrics/vmselect:v1.60.0-cluster
    command:
      - '--search.latencyOffset=0s'
      - '--search.cacheTimestampOffset=15m'
      - '--storageNode=vmstorage:8401'
      - '--search.maxQueryLen=1GiB'
    ports:
      - 8481

  influxdb:
    image: influxdb:1.8.4
    environment:
      INFLUXDB_DB: telegraf
      INFLUXDB_BIND_ADDRESS: "0.0.0.0:8088"
    ports:
      - 8083:8083
      - 8086:8086
    volumes:
      - influxdb:/var/lib/influxdb

  gocky:
    image: mistce/gocky:v4-7-1
    command: -config /etc/gocky/config.toml
    ports:
      - 9096:9096
      - 9097:9097
    depends_on:
      - rabbitmq

  traefik:
    image: traefik:v1.5
    command:
      # - --logLevel=INFO
      - --accesslog
      # - --accesslog.format=json
      - --api
      - --api.entrypoint=traefik
      - --rest
      - --rest.entrypoint=traefik
      - --defaultentrypoints=http
      - --entrypoints=Name:http Address::80
      - --entrypoints=Name:traefik Address::8080
    ports:
      - 8040:80
      - 8041:8080

  huproxy:
    image: mistce/huproxy:v4-7-1
    command: /app --listen 0.0.0.0:8086
    environment:
      MONGO_URI: mongodb://mongodb:27017
    expose:
      - 8086

  wsproxy:
    image: mistce/wsproxy:v4-7-1
    expose:
      - 8764



volumes:
  elasticsearch: {}
  influxdb: {}
  mongodb: {}
  victoria-metrics: {}

```

