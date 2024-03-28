# redis 容器化



基础环境，需要有docker、docker-compose服务

### 1. 构建docker-compose.yaml

```
version: '3'
services:
  redis:
    image: redis:6.2.5
    restart: always
    container_name: redistest
    hostname: redishost
    sysctls:
      - net.core.somaxconn=4096
    volumes:
      - ./redis.conf:/etc/redis/redis.conf
      - ./data:/data
    #  - ./log/redis.log:/var/log/redis/redis.log
    ports:
      - 6379:6379
    privileged: true
    environment:
      TZ: Asia/Shanghai
      LANG: en_US.UTF-8
  #  command: redis-server --requirepass comleader --databases 16
    command: redis-server /etc/redis/redis.conf
```



redis.conf

```
# 设置端口
port 6379
# 是否启用AOF
appendonly yes
# 设置密码
requirepass foobared
databases 16
bind 0.0.0.0
# 设置备份 RDB   单位：秒    修改次数
save 900 1
save 300 10
save 60 10000
# 设置 RDB 文件名和文件路径
dbfilename dump.rdb
dir /data

```



### 2. 构建镜像及运行

运行docker

```
mkdir redis
mkdir redis/data/
cd redis
将docker-compsoe.yaml和redis.conf放置在redis目录下

docker compse up -d
# 停止
docker compse down

```



### 3. 外部访问测试

```
redis-cli -h 10.21.16.43 -p 6379

```

