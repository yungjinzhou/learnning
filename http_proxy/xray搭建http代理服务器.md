## xray搭建代理服务器

xray 代理服务器配置
1.下载xray

```
wget https://github.com/XTLS/Xray-core/releases/download/v1.7.5/Xray-linux-64.zip
```

Xray-linux-64.zip

2.执行
```shell
./xray run -c config.json

[root@host http_proxy]# ./xray run -c config.json 
Xray 1.7.5 (Xray, Penetrates Everything.) Custom (go1.20 linux/amd64)
A unified platform for anti-censorship.
2023/09/20 17:36:06 [Info] infra/conf/serial: Reading config: config.json
2023/09/20 17:36:06 [Warning] core: Xray 1.7.5 started

```

3.配置
config.json

```
{
  "inbounds": [
    {
      "port": 10086, // 服务器监听端口
      "protocol": "http",
      "settings": {
        
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom"
    }
  ]
}

```

￼
