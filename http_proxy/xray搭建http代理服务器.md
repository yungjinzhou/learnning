## xray搭建代理服务器

xray 代理服务器配置
1.下载xray

```
wget https://github.com/XTLS/Xray-core/releases/download/v1.3.0/Xray-linux-64.zip
```



Xray-linux-64.zip

2.执行
./xray run -c config.json
1
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
