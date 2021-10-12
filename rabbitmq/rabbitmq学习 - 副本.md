### rabbitmq  

message properties





### Correlation id

In the method presented above we suggest creating a callback queue for every RPC request. That's pretty inefficient, but fortunately there is a better way - let's create a single callback queue per client.

That raises a new issue, having received a response in that queue it's not clear to which request the response belongs. That's when the correlation_id property is used. We're going to set it to a unique value for every request. Later, when we receive a message in the callback queue we'll look at this property, and based on that we'll be able to match a response with a request. If we see an unknown correlation_id value, we may safely discard the message - it doesn't belong to our requests.

You may ask, why should we ignore unknown messages in the callback queue, rather than failing with an error? It's due to a possibility of a race condition on the server side. Although unlikely, it is possible that the RPC server will die just after sending us the answer, but before sending an acknowledgment message for the request. If that happens, the restarted RPC server will process the request again. That's why on the client we must handle the duplicate responses gracefully, and the RPC should ideally be idempotent.





参考链接：https://www.rabbitmq.com/tutorials/tutorial-six-python.html







[Manual message acknowledgments](https://www.rabbitmq.com/confirms.html) are turned on by default. In previous examples we explicitly turned them off via the auto_ack=True flag. It's time to remove this flag and send a proper acknowledgment from the worker, once we're done with a task.





没有确认的消息会耗内存

It's a common mistake to miss the basic_ack. It's an easy error, but the consequences are serious. Messages will be redelivered when your client quits (which may look like random redelivery), but RabbitMQ will eat more and more memory as it won't be able to release any unacked messages.

查未确认的任务

```
sudo rabbitmqctl list_queues name messages_ready messages_unacknowledged

# on windows, use follow command
rabbitmqctl.bat list_queues name messages_ready messages_unacknowledged
```



消息持久化，该设置需要在客户端服务端代码中都设置

```python
channel.queue_declare(queue='hello', durable=True)
```

设置消息持久化对新的队列生效

RabbitMQ doesn't allow you to redefine an existing queue with different parameters and will return an error to any program that tries to do that. But there is a quick workaround - let's declare a queue with different name, for example task_queue:







列出所有exchanges

```
rabbitmqctl list_exchanges
```





1. 为tracing命名，选择要监听的vhost、消息在日志中的格式，可以限制要记录消息payload的大小。（译者注，实际使用中发现，Json格式的payload是序列化之后的内容，且消息之间没有明显分隔符，可读性较差，可能更适合提供给下游进一步处理。如果追求可读性，应选择Text格式，payload会自动反序列化为原始文本内容，且消息之间有明确的分隔符。）
   **Warning**: 如果同名的日志文件存在，应该先删除，否则创建tracing时会失败。
2. Pattern的填写：实践中发现，publish需要绑定exchange，deliver需要绑定queue。即，追踪进入MQ的消息，需要绑定到exchange，追踪离开MQ的消息，需要绑定到queue。

- `#` 追踪所有进入和离开MQ的消息
- `publish.#` 追踪所有进入MQ的消息
- `publish.myExchage` 追踪所有进入到`myExchange`的消息
- `deliver.#` 跟踪所有离开MQ的消息
- `deliver.myQueue` 追踪所有从`myQueue`离开的消息
- `#.myQueue`实测效果等同于deliver.myQueue





trace使用

     a) 列出本机已安装的插件：rabbitmq-plugins list（请先定位到Rabbitmq服务安装目录）
    
     b) 启动Trace插件：rabbitmqctl trace_on   (关闭Trace：rabbitmqctl trace_off)


#### 启用日志插件命令

当发现admin没有trace的时候：

![在这里插入图片描述](.\20210630185459260.png)





首先，enable该插件

执行如下命令：

> rabbitmq-plugins enable rabbitmq_tracing



 可以通过如下命令完全禁用Tracing插件，
`rabbimq-plugins disable rabbitmq_tracing` 



trace填写说明



- Name：自定义，建议标准点容易区分
- Format：表示输出的消息日志格式，有Text和JSON两种，Text格式的日志方便人类阅读，JSON的方便程序解析。
- JSON格式的payload（消息体）默认会采用Base64进行编码，如上面的“trace test payload.”会被编码成“dHJhY2UgdGVzdCBwYXlsb2FkLg==”。
- Max payload bytes：表示每条消息的最大限制，单位为B。比如设置了了此值为10，那么当有超过10B的消息经



- Pattern：用来设置匹配的模式，和Firehose的类似。如“#”匹配所有消息流入流出的情况，即当有客户端生产消息或者消费消息的时候，会把相应的消息日志都记录下来；“publish.#”匹配所有消息流入的情况；“deliver.#”匹配所有消息流出的情况；“publish.exchange.b2b.gms.ass”只匹配发送者(Exchanges)为exchange.b2b.gms.ass的所有消息流入的情况。

































