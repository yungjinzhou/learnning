**显示域名**

一般使用Wireshark只能看到ip地址，但是看域名更方便更简明

只要修改一个配置就可以

编辑--》首选项

勾选Resolve network(IP) addresses



**不显示指定的域名**

过滤条件输入   http.host ne baidu.com



**过滤指定的域名**

过滤条件输入   http.host contains baidu.com

过滤条件输入   http.host == baidu.com



**过滤指定的请求**

过滤条件输入   http.request.uri  contains "product"

http.content_type == "text/html"

http.request.uri == "/produc"

http.request.method=="GET"

tcp.port==80

http && tcp.port==8613 or tcp.port==8090 or tcp.port==8091

ip.dst==42.159.245.203



**过滤响应**

http.response.phrase == “OK”
//过滤http响应中的phrase





**过滤tcp中的data数据**

tcp.payload contains "sendAppPushMsg"



**显示mysql语句**

如果抓包的mysql协议，想要看到具体的sql语句，可以进行如下设置：

过滤protocol    mysql

选中某一行，右键，协议首选项，选中show sql Query string in info column





**过滤mysql查询语句**

如果要对sql的查询进行过滤，如下：

mysql.query contains "archive"





