# 多云管理mistio部署





环境：centos7 x86_64

配置ip地址，dns，ssh远程连接





配置基本软件环境

```
yum install -y wget vim 
```





更改配置文件（很重要）
1、备份CentOS 7系统自带yum源配置文件/etc/yum.repos.d/CentOS-Base.repo命令：

mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup

配置aliyun

```
wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
或
curl -o /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
```



2、找到yum源的配置路径
cd /etc/yum.repos.d



4、打开CentOS-Base.repo文件:
vim CentOS-Base.repo

或者

vi CentOS-Base.repo

5、将文件中的所有http开头的地址更改为https（下图中只是列出部分内容，并不完善）：



3、更新镜像源
清除缓存：yum clean all
生成缓存：yum makecache



安装docker-ce

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



部署安装：

wget https://github.com/mistio/mist-ce/releases/download/v4.7.1/docker-compose.yml

见附件

docker-compose up -d

 

创建用户和设置密码

docker-compose exec api sh

./bin/adduser --admin [admin@example.com](mailto:admin@example.com)















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

















cloudpods

```
# 下载 ocboot 工具到本地
$ git clone -b release/3.10 https://github.com/yunionio/ocboot && cd ./ocboot

# 进入 compose 目录
$ cd compose
$ ls -alh docker-compose.yml

# 运行服务
$ docker compose up
```

### 2. 登陆 climc 命令行容器[ ](https://www.cloudpods.org/zh/docs/quickstart/docker-compose/#2-登陆-climc-命令行容器)

如果要使用命令行工具对平台做操作，可以使用下面的方法进入容器：

```bash
$ docker exec -ti compose-climc-1 bash
Welcome to Cloud Shell :-) You may execute climc and other command tools in this shell.
Please exec 'climc' to get started

# source 认证信息
bash-5.1# source /etc/yunion/rcadmin
bash-5.1# climc user-list
```