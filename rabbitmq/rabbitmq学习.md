### rabbitmq  

message properties



#### Message properties

The AMQP 0-9-1 protocol predefines a set of 14 properties that go with a message. Most of the properties are rarely used, with the exception of the following:

- delivery_mode: Marks a message as persistent (with a value of 2) or transient (any other value). You may remember this property from [the second tutorial](https://www.rabbitmq.com/tutorials/tutorial-two-python.html).
- content_type: Used to describe the mime-type of the encoding. For example for the often used JSON encoding it is a good practice to set this property to: application/json.
- reply_to: Commonly used to name a callback queue.
- correlation_id: Useful to correlate RPC responses with requests.



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









































