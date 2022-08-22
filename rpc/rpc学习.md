



## 一、相关概念



### 1.1 virtual host定义

MySQL大家都不陌生，经常会出现多个业务线混用一个MySQL数据库的情况，就像下图这样，每个业务线都在MySQL中创建自己的数据库，使用时各自往各自的数据库中存储数据，彼此相互不干涉。
RabbitMQ和virtual host的关系也差不多，可以让多个业务线同时使用一个RabbitMQ，只要为业务线各个业务线绑定上不同的virtual host即可：

为了在一个单独的代理上实现多个隔离的环境（用户、用户组、交换机、队列 等），AMQP提供了一个虚拟主机（virtual hosts - vhosts）的概念。
这跟Web servers虚拟主机概念非常相似，这为AMQP实体提供了完全隔离的环境。当连接被建立的时候，AMQP客户端来指定使用哪个虚拟主机。

### 1.2 队列（ Queue ）

队列 存储着即将被应用消费掉的消息。

**名称** 可以为队列指定一个名称。

**队列持久化**

- 持久化队列（Durable queues）会被存储在磁盘上，当消息代理（broker）重启的时候，它可以被重新恢复。
- 没有被持久化的队列称作暂存队列（Transient queues）

### 1.3 绑定（Binding）

**绑定是**交换机（exchange）将消息（message）路由给队列（queue）所需遵循的**规则**。

如果要指示交换机“E”将消息路由给队列“Q”，那么“Q”就需要与“E”进行绑定。绑定操作需要定义一个可选的路由键（routing key）属性给某些类型的交换机。

路由键的意义在于从发送给交换机的众多消息中选择出某些消息，将其路由给绑定的队列。

### 1.4  消费者 （ Consumer ）

消费者即使用消息的客户。

**消费者标识** 每个消费者（订阅者）都有一个叫做消费者标签的标识符。它可以被用来退订消息。

一个队列可以注册多个消费者，也可以注册一个独享的消费者（当独享消费者存在时，其他消费者即被排除在外）。

### 1.5 消息确认 (acknowledgement)

什么时候删除消息才是正确的？有两种情况

- 自动确认模式：当消息代理（broker）将消息发送给应用后立即删除。
- 显式确认模式：待应用（application）发送一个确认回执（acknowledgement）后再删除消息。

在显式模式下，由消费者来选择什么时候发送确认回执（acknowledgement）。

- 应用可以在收到消息后立即发送
- 或将未处理的消息存储后发送
- 或等到消息被处理完毕后再发送确认回执。

如果一个消费者在尚未发送确认回执的情况下挂掉了，那代理会将消息重新投递给另一个消费者。如果当时没有可用的消费者了，消息代理会死等下一个注册到此队列的消费者，然后再次尝试投递。

**拒绝消息**

当一个消费者接收到某条消息后，处理过程有可能成功，有可能失败。

应用可以向消息代理表明，本条消息由于“拒绝消息（Rejecting Messages）”的原因处理失败了（或者未能在此时完成）。当拒绝某条消息时，应用可以告诉消息代理如何处理这条消息——销毁它或者重新放入队列。

### 1.6 消息 ( Message )

消息的组成：

- 消息属性
- 消息主体（有效载荷）

消息属性（Attributes）常见的有：

- Content type（内容类型）
- Content encoding（内容编码）
- Routing key（路由键）
- Delivery mode (persistent or not) 投递模式（持久化 或 非持久化）
- Message priority（消息优先权）
- Message publishing timestamp（消息发布的时间戳）
- Expiration period（消息有效期）
- Publisher application id（发布应用的ID）

消息体：

- 消息体即消息实际携带的数据，消息代理不会检查或者修改有效载荷。
- 消息可以只包含属性而不携带有效载荷。
- 它通常会使用类似JSON这种序列化的格式数据。
- 常常约定使用"content-type" 和 "content-encoding" 这两个字段分辨消息。

### 1.6 连接 (Connection)

AMQP 连接通常是长连接。AMQP是一个使用TCP提供可靠投递的应用层协议。AMQP使用认证机制并且提供TLS（SSL）保护。

当一个应用不再需要连接到AMQP代理的时候，<font color=blue><b>需要优雅的释放掉AMQP连接</b></font>，而不是直接将TCP连接关闭。

### 1.7 通道 （channels）

AMQP 提供了**通道**（channels）来处理多连接，可以把通道理解成<font color=blue><b>共享一个TCP连接的多个轻量化连接</b></font>。

信道是 “真实的” TCP连接内的虚拟连接，AMQP的命令都是通过通道发送的。在一条TCP连接上可以创建多条信道。

- 有些应用需要与 AMQP 代理建立多个连接。同时开启多个 TCP 连接不合适，因为会消耗掉过多的系统资源并且使得防火墙的配置更加困难。AMQP 0-9-1 提供了通道（channels）来处理多连接，可以把通道理解成共享一个 TCP 连接的多个轻量化连接。
- 在涉及多线程 / 进程的应用中，为每个线程 / 进程开启一个通道（channel）是很常见的，并且这些通道不能被线程 / 进程共享。
- 一个特定通道上的通讯与其他通道上的通讯是**完全隔离**的，因此每个 AMQP 方法都需要携带一个通道号，这样客户端就可以指定此方法是为哪个通道准备的。

### 1.8 交换机（Exchange)

exchange是一个很重要的概念。用来接收publisher发出的消息，并决定消息后续处理。后续处理取决于消息的路由算法，而路由算法又是由exchange type决定的。

>  交换机 用来传输消息的，交换机拿到一个消息之后将它路由给一个队列。 

它的传输策略是由交换机类型和被称作绑定（bindings）的规则所决定的。

四种交换机：

| Name（交换机类型）            | 默认名称                                |
| :---------------------------- | :-------------------------------------- |
| Direct exchange（直连交换机） | (空字符串) ， amq.direct                |
| Fanout exchange（扇型交换机） | amq.fanout                              |
| Topic exchange（主题交换机）  | amq.topic                               |
| Headers exchange（头交换机）  | amq.match (and amq.headers in RabbitMQ) |

**交换机状态** 交换机可以有两个状态：持久（durable）、暂存（transient）。持久化的交换机会在消息代理（broker）重启后依旧存在，而暂存的交换机则不会。并不是所有的应用场景都需要持久化的交换机。



### 1.9 交换机类型（exchange type）

AMQP中定义的类型包括：direct, topic, headers and fanout。

**direct**：消息路由到满足此条件的队列中(queue,可以有多个)： routing key = binding key 

topic：消息路由到满足此条件的队列中(queue,可以有多个)：routing key 匹配 binding pattern. binding pattern是类似正则表达式的字符串，可以满足复杂的路由条件。

fanout：消息路由到多个绑定到该exchange的队列中。

Openstack RPC中主要用了这三种exchange type。

binding ：

binding是用来描述exchange和queue之间的关系的概念，一个exchang可以绑定多个队列，这些关系由binding建立。前面说的binding key /binding pattern也是在binding中给出。

每个receiver在接收消息前都需要创建binding。


其他：

一个队列可以有多个receiver，队列里的一个消息只能发给一个receiver。至于发送给哪个receiver,由AMQP的负载算法决定，默认为在所有receiver中均匀发送(round robin).


一个消息可以被发送到一个队列中，也可以被发送到多个多列中。多队列情况下，一个消息可以被多个receiver收到并处理。Openstack RPC中这两种情况都会用到。



### 1.10 rpc

RPC即Remote Procedure Call(远程方法调用)，是Openstack中一种用来实现跨进程(或者跨机器)的通信机制。Openstack中同项目内(如nova, neutron, cinder...)各服务(service)及通过RPC实现彼此间通信。Openstack中还有另外两种跨进程的通信方式：数据库和Rest API。

Openstack中服务主要以进程的形式实现。也可以以线程的形式实现，但是Python中的线程是协作模型，无法发挥系统中多CPU(或多CPU核心)的能力。

RCP只定义了一个通信接口，其底层的实现可以各不相同。目前Openstack中的主要采用AMQP来实现。AMQP(
Advanced Message Queuing Protocol)是一种基于队列的可靠消息服务协议，具体可参考 http://en.wikipedia.org/wiki/Advanced_Message_Queuing_Protocol。作为一种通信协议，AMQP同样存在多个实现，如Apache Qpid, RabbitMQ等。



### 1.11 binding-key 和routing-key区别

<font color=blue><b>binding-key应用于队列</b></font>，是将哪些队列绑定到该交换机(exchange)上，或者说注册到该交换机上的队列
<font color=blue><b>routing-key应用于消息</b></font>，是到交换机上的消息 通过定义的routing-key(路由规则)发送到匹配的队列
Default Exchange，即交换机的direct模式，是将binding-key和routing-key设置成了和队列名称相同的字段


```
The binding-key is used with the queue. It is the key with which the queue is registered in the exchange.

The routing-key is used with the message. It is the key which will decide which queue(s) does this message should be routed to. Messages can have other type of identifiers for routing, like matchers in Topic Exchange.

> Every queue is automatically bound to the default exchange with a routing key which is the same as the queue name.

Now, the routing-key and binding-key is not the same concept. But, here, in the case of Default Exchange, the binding key will be the same as the name of the queue. So, the messages will also have the same routing-key as the Queue name.

```





## 二、RabbitMQ的消息模型



RabbitMQ支持以下五种消息模型，第六种RPC本质上是服务调用，所以不算做服务通信消息模型。

[![img](https://img2020.cnblogs.com/blog/1496926/202012/1496926-20201206162020922-723030915.png)](https://img2020.cnblogs.com/blog/1496926/202012/1496926-20201206162020922-723030915.png)

[![img](https://img2020.cnblogs.com/blog/1496926/202012/1496926-20201206162022288-710990876.png)](https://img2020.cnblogs.com/blog/1496926/202012/1496926-20201206162022288-710990876.png)



#### Hello World[#](https://www.cnblogs.com/ZhuChangwu/p/14093107.html#hello-world)

[![img](https://img2018.cnblogs.com/blog/1496926/201907/1496926-20190708125542629-2135674001.png)](https://img2018.cnblogs.com/blog/1496926/201907/1496926-20190708125542629-2135674001.png)

P（producer/ publisher）：生产者，发送消息的服务

C（consumer）：消费者，接收消息的服务

红色区域就是MQ中的Queue，可以把它理解成一个邮箱

- 首先信件来了不强求必须马上马去拿
- 其次,它是有最大容量的(受主机和磁盘的限制,是一个缓存区)
- 允许多个消费者监听同一个队列，争抢消息



#### Worker模型[#](https://www.cnblogs.com/ZhuChangwu/p/14093107.html#worker模型)

[![img](https://img2018.cnblogs.com/blog/1496926/201907/1496926-20190708125528529-1014015990.png)](https://img2018.cnblogs.com/blog/1496926/201907/1496926-20190708125528529-1014015990.png)

Worker模型中也只有一个工作队列。但它是一种竞争消费模式。可以看到同一个队列我们绑定上了多个消费者，消费者争抢着消费消息，**这可以有效的避免消息堆积**。

比如对于短信微服务集群来说就可以使用这种消息模型，来了请求大家抢着消费掉。

如何实现这种架构：对于上面的HelloWorld这其实就是相同的服务我们启动了多次罢了，自然就是这种架构。



#### 订阅模型[#](https://www.cnblogs.com/ZhuChangwu/p/14093107.html#订阅模型)

订阅模型借助一个新的概念：Exchange（交换机）实现，不同的订阅模型本质上是根据交换机(Exchange)的类型划分的。

订阅模型有三种

1. Fanout（广播模型）: 将消息发送给绑定给交换机的所有队列(因为他们使用的是同一个RoutingKey)。
2. Direct（定向）: 把消息发送给拥有指定Routing Key (路由键)的队列。
3. Topic（通配符）: 把消息传递给拥有 符合Routing Patten(路由模式)的队列。



##### 订阅之Fanout模型

[![img](https://img2018.cnblogs.com/blog/1496926/201907/1496926-20190708125522017-1931971535.png)](https://img2018.cnblogs.com/blog/1496926/201907/1496926-20190708125522017-1931971535.png)

这个模型的特点就是它在发送消息的时候,并没有指明Rounting Key , 或者说他指定了Routing Key,但是所有的消费者都知道,大家都能接收到消息,就像听广播。





扇型交换机将消息路由给绑定到它身上的所有队列，而不理会绑定的路由键。

如果N个队列绑定到某个扇型交换机上，当有消息发送给此扇型交换机时，交换机会将消息的拷贝分别发送给这所有的N个队列。扇型用来交换机处理消息的广播路由（broadcast routing）。

案例：

- MMO游戏可以使用它来处理排行榜更新等全局事件
- 体育新闻网站可以用它来实时地将比分更新分发给多端
- 在群聊的时候，它被用来分发消息给参与群聊的用户。

![img](https://ask.qcloudimg.com/http-save/yehe-7043228/af8ztbbrma.png?imageView2/2/w/1620)

扇型交换机图例

**总结** 不管 消息的Routing Key，广播给这个交换机下的所有绑定队列。





##### 订阅之Direct模型

[![img](https://img2020.cnblogs.com/blog/1496926/202012/1496926-20201206162023832-709293422.png)](https://img2020.cnblogs.com/blog/1496926/202012/1496926-20201206162023832-709293422.png)

P：生产者，向Exchange发送消息，发送消息时，会指定一个routing key。

X：Exchange（交换机），接收生产者的消息，然后把消息递交给 与routing key完全匹配的队列

C1：消费者，其所在队列指定了需要routing key 为 error 的消息

C2：消费者，其所在队列指定了需要routing key 为 info、error、warning 的消息

拥有不同的RoutingKey的消费者，会收到来自交换机的不同信息，而不是大家都使用同一个Routing Key 和广播模型区分开来。





消息可以携带一个属性 “路由键（routing key）”，以辅助标识被路由的方式。直连型交换机（direct exchange）根据消息携带的路由键将消息投递给对应队列的。

它如何工作：

- 将一个队列绑定到某个交换机上，同时赋予该绑定（Binding）一个路由键（routing key）
- 当一个携带着路由键为 “key1” 的消息被发送给直连交换机时，交换机会把它路由给 “Binding名称等于 key1”  的队列。

![img](https://ask.qcloudimg.com/http-save/yehe-7043228/nfyrjify24.png?imageView2/2/w/1620)

直连型交换机图例

**总结：** Binding 的 Routing Key 要和 消息的 Routing Key 完全匹配











##### 订阅之Topic模型

[![img](https://img2020.cnblogs.com/blog/1496926/202012/1496926-20201206162025176-1413299944.png)](https://img2020.cnblogs.com/blog/1496926/202012/1496926-20201206162025176-1413299944.png)

类似于Direct模型。区别是Topic的Routing Key支持通配符。





主题交换机通过对消息的`路由键`和  “绑定的主题名称” 进行模式匹配，将消息路由给匹配成功的队列。

它的工作方式：

- 为绑定的 Routing Key 指定一个 “主题”。模式匹配用用 *, # 等字符进行模糊匹配。比如 usa.# 表示 以  usa.开头的多个消息 到这里来。
- 交换机将按消息的 Routing Key 的值的不同路由到  匹配的主题队列。

主题交换机经常用来实现各种分发/订阅模式及其变种。主题交换机通常用来实现消息的多播路由（multicast routing）。

![img](https://ask.qcloudimg.com/http-save/yehe-7043228/ezoelqmind.png?imageView2/2/w/1620)

image.png

使用案例：

- 由多个人完成的后台任务，每个人负责处理某些特定的任务
- 股票价格更新涉及到分类或者标签的新闻更新（

**总结：** 绑定 的 Routing Key 和 消息的 Routing Key 进行字符串的模糊匹配。





#### 消息确认机制[#](https://www.cnblogs.com/ZhuChangwu/p/14093107.html#消息确认机制)



##### ACK机制

[![img](https://img2020.cnblogs.com/blog/1496926/202012/1496926-20201206162109581-1996261690.png)](https://img2020.cnblogs.com/blog/1496926/202012/1496926-20201206162109581-1996261690.png)

所谓的ACK确认机制：

自动ACK：消费者接收到消息后自动发送ACK给RabbitMQ。

手动ACK：我们手动控制消费者接收到并成功消息后发送ACK给RabbitMQ。

你可以看上图：如果使用自动ACK，当消息者将消息从channel中取出后，RabbitMQ随即将消息给删除。接着不幸的是，消费者没来得及处理消息就挂了。那也就意味着消息其实丢失了。

你可能会说：会不会存在重复消费的情况呢？这其实就不是MQ的问题了。你完全可以在你代码的逻辑层面上进行诸如去重、插入前先检查是否已存在等逻辑规避重复消费问题。



参考链接：https://www.cnblogs.com/ZhuChangwu/p/14093107.html#%E4%BB%80%E4%B9%88%E6%98%AFamqp-%E5%92%8C-jms%EF%BC%9F



## 三、openstack相关rpc知识



### 3.1 rpc扩展概念

下面几个概念是RPC扩展的：
Namespace:用来组织server中的方法(method),默认是null。
Method：及被调用的方法，和普通(本地)方法调用中的方法是一个概念。
API version：用来标识server中方法的版本。随着时间的推移，server中的方法可能不断变化，提供版本信息可以保持对之前client的兼容。
Transport：对RPC的底层实现机制的抽象。

### 3.2 RPC的使用场景

Openstack中RPC的主要使用场景：

#### 3.2.1 随机调用某server上的一个方法

Invoke Method on One of Multiple Servers
这个应该是Openstack中最常用的一种RPC调用，每个方法都会有多个server来提供，client调用时由底层机制选择一个server来处理这个调用请求。
像nova-scheduler, nova-conductor都可以以这种多部署方式提供服务。

这种场景通过AMQP的topic exchange实现。
所有server在binding中为binding key指定一个相同的topic， client在调用时使用这个topic既可实现。

#### 3.2.2 调用某特定server上的一个方法

Invoke Method on a Specific Server
一般Openstack中的各种scheduler会以这种方式调用。通常scheduler都会先选定一个节点，然后调用该节点上的服务。

这种场景通过AMQP的topic exchange实现。
每个server在binding中为其binding key指定一个自己都有的topic， client在调用时使用这个topic既可实现。

#### 3.2.3 调用所有server上的一个方法

Invoke Method on all of Multiple Servers
这种其实就是一个广播系统。就像开会议，台上的人讲话，台下的人都能听到。
Openstack中有些rpcapi.py的某些方法带有fanout=True参数，这些都是让所有server处理某个请求的情况。
例子： neutron中所有plugin都会有一个AgentNotifierApi，这个rpc是用来调用安装在compute上的L2 agent。因为存在多个L2 agent(每个compute上都会有)，所以要用广播模式。

这种场景通过AMQP的fanout exchange实现。
每个server在binding中将其队列绑定到一个fanout exchange， client在调用时指定exchange类型为fanout即可。server和client使用同一个exchange。



### 3.3 RPC的实现

目前Openstack中有两种RPC实现，一种是在oslo messaging,一种是在openstack.common.rpc。
openstack.common.rpc是旧的实现，**oslo messaging**是对openstack.common.rpc的重构。openstack.common.rpc在每个项目中都存在一份拷贝，oslo messaging即将这些公共代码抽取出来，形成一个新的项目。oslo messaging也对RPC API进行了重新设计，具体参考前文。


以后的方向是各个项目都会使用oslo messaging的RPC功能，停止使用openstack.common.rpc。目前(icehouse release)nova, cinder都已经完成转变，neutron还在使用openstack.common.rpc。

**rpc.call和rpc.cast的区别**
从实现代码上看，他们的区别很小，就是call调用时候会带有wait_for_reply=True参数，cast不带

**notification**

oslo messaging中除了RPC外，还有另外一种跨进程通信方式，即消息通知(notification)。notification和前面的第三种RPC场景(广播系统)非常类似，区别就是notification的消息(message)格式是有固定格式的，而RPC中的消息并无固定格式，取决于client/server之间的约定。

目前消息系统的主要receiver(消息收集者)为ceilometer系统，而publisher就是Openstack个项目的service。如nova-compute会针对虚拟机的生命周期发出各种通知：start/stop/create/destroy等。

notification的底层机制可以使用RPC，及driver类型为MessagingDriver。

具体参见：https://wiki.openstack.org/wiki/Oslo/Messaging#oslo.notify









## 四、kombu分析



### 4.1摘要

本系列我们介绍消息队列 Kombu。Kombu 的定位是一个兼容 AMQP 协议的消息队列抽象。通过本文，大家可以了解 Kombu 是如何启动，以及如何搭建一个基本的架子。

因为之前有一个综述，所以大家会发现，一些概念讲解文字会同时出现在后续文章和综述之中。

### 示例

下面使用如下代码来进行说明。

本示例来自[liqiang.io/post/kombu-…](https://link.juejin.cn?target=https%3A%2F%2Fliqiang.io%2Fpost%2Fkombu-source-code-analysis-part-5%E7%B3%BB%E5%88%97%EF%BC%8C%E7%89%B9%E6%AD%A4%E6%B7%B1%E8%A1%A8%E6%84%9F%E8%B0%A2%E3%80%82)

```python
def main(arguments):
    hub = Hub()
    exchange = Exchange('asynt_exchange')
    queue = Queue('asynt_queue', exchange, 'asynt_routing_key')

    def send_message(conn):
        producer = Producer(conn)
        producer.publish('hello world', exchange=exchange, routing_key='asynt_routing_key')
        print('message sent')

    def on_message(message):
        print('received: {0!r}'.format(message.body))
        message.ack()
        # hub.stop()  # <-- exit after one message

    conn = Connection('redis://localhost:6379')
    conn.register_with_event_loop(hub)

    def p_message():
        print(' kombu ')

    with Consumer(conn, [queue], on_message=on_message):
        send_message(conn)
        hub.timer.call_repeatedly(3, p_message)
        hub.run_forever()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
复制代码
```

### 4.2启动

让我们顺着程序流程看看Kombu都做了些什么，也可以对 Kombu 内部有所了解。

本文关注的重点是：Connection，Channel 和 Hub 是如何联系在一起的。

#### 4.2.1 Hub

在程序开始，我们建立了Hub。

Hub的作用是建立消息Loop，但是此时尚未建立，因此只是一个静态实例。

```python
hub = Hub()
复制代码
```

其定义如下：

```python
class Hub:
    """Event loop object.
    Arguments:
        timer (kombu.asynchronous.Timer): Specify custom timer instance.
    """
    def __init__(self, timer=None):
        self.timer = timer if timer is not None else Timer()

        self.readers = {}
        self.writers = {}
        self.on_tick = set()
        self.on_close = set()
        self._ready = set()

        self._running = False
        self._loop = None

        self.consolidate = set()
        self.consolidate_callback = None

        self.propagate_errors = ()
        self._create_poller()
复制代码
```

因为此时没有建立loop，所以目前重要的步骤是建立Poll，其Stack如下：

```python
_get_poller, eventio.py:321
poll, eventio.py:328
_create_poller, hub.py:113
__init__, hub.py:96
main, testUb.py:22
<module>, testUb.py:55
复制代码
```

在eventio.py中有如下，我们可以看到Kombu可以使用多种模型来进行内核消息处理：

```python
def _get_poller():
    if detect_environment() != 'default':
        # greenlet
        return _select
    elif epoll:
        # Py2.6+ Linux
        return _epoll
    elif kqueue and 'netbsd' in sys.platform:
        return _kqueue
    elif xpoll:
        return _poll
    else:
        return _select
复制代码
```

因为本机情况，这里选择的是：_poll。

```python
+------------------+
| Hub              |
|                  |
|                  |            +-------------+
|      poller +---------------> | _poll       |
|                  |            |             |         +-------+
|                  |            |    _poller+---------> |  poll |
+------------------+            |             |         +-------+
                                +-------------+
复制代码
```

#### 4.2.2 Exchange与Queue

其次建立了Exchange与Queue。

- Exchange：交换机，消息发送者将消息发至 Exchange，Exchange 负责将消息分发至 Queue；
- Queue：消息队列，存储着即将被应用消费掉的消息，Exchange 负责将消息分发 Queue，消费者从 Queue 接收消息；

因为此时也没有具体消息，所以我们暂且无法探究Exchange机制。

```python
exchange = Exchange('asynt')
queue = Queue('asynt', exchange, 'asynt')
复制代码
```

此时将把Exchange与Queue联系起来。图示如下：

```python
+------------------+
| Hub              |
|                  |
|                  |            +-------------+
|      poller +---------------> | _poll       |
|                  |            |             |         +-------+
|                  |            |    _poller+---------> |  poll |
+------------------+            |             |         +-------+
                                +-------------+


+----------------+         +-------------------+
| Exchange       |         | Queue             |
|                |         |                   |
|                |         |                   |
|     channel    | <------------+ exchange     |
|                |         |                   |
|                |         |                   |
+----------------+         +-------------------+
复制代码
```

#### 4.2.3 Connection

第三步就是建立Connection。

Connection是对 MQ 连接的抽象，一个 Connection 就对应一个 MQ 的连接。现在就是对'redis://localhost:6379'连接进行抽象。

```python
conn = Connection('redis://localhost:6379')
复制代码
```

##### 4.2.3.1 定义

由定义注释可知，Connection是到broker的连接。从具体代码可以看出，Connection更接近是一个逻辑概念，具体功能都委托给别人完成。

消息从来不直接发送给队列，甚至 Producers 都可能不知道队列的存在。 Producer如何才能将消息发送给Consumer呢？这中间需要经过 Message Broker 的处理和传递。

AMQP中，承担 Message Broker 功能的就是 AMQP Server。也正是从这个角度讲，AMQP 的 Producer 和Consumer 都是 AMQP Client。

在Kombu 体系中，用 transport 对所有的 broker 进行了抽象，为不同的 broker 提供了一致的解决方案。通过Kombu，开发者可以根据实际需求灵活的选择或更换broker。

Connection主要成员变量是，但是此时没有赋值：

- _connection：
- _transport：就是上面提到的对 broker 的抽象。
- cycle：与broker交互的调度策略。
- failover_strategy：在连接失效时，选取其他hosts的策略。
- heartbeat：用来实施心跳。

代码如下：

```python
class Connection:
    """A connection to the broker"""

    port = None
    virtual_host = '/'
    connect_timeout = 5

    _connection = None
    _default_channel = None
    _transport = None
    uri_prefix = None

    #: The cache of declared entities is per connection,
    #: in case the server loses data.
    declared_entities = None

    #: Iterator returning the next broker URL to try in the event
    #: of connection failure (initialized by :attr:`failover_strategy`).
    cycle = None

    #: Additional transport specific options,
    #: passed on to the transport instance.
    transport_options = None

    #: Strategy used to select new hosts when reconnecting after connection
    #: failure.  One of "round-robin", "shuffle" or any custom iterator
    #: constantly yielding new URLs to try.
    failover_strategy = 'round-robin'

    #: Heartbeat value, currently only supported by the py-amqp transport.
    heartbeat = None

    resolve_aliases = resolve_aliases
    failover_strategies = failover_strategies

    hostname = userid = password = ssl = login_method = None
复制代码
```

##### 4.2.3.2 init 与 transport

Connection内部主要任务是建立了transport。

Stack大致如下：

```python
Transport, redis.py:1039
<module>, redis.py:1031
import_module, __init__.py:126
symbol_by_name, imports.py:56
resolve_transport, __init__.py:70
get_transport_cls, __init__.py:85
__init__, connection.py:183
main, testUb.py:40
<module>, testUb.py:55
复制代码
```

#### 4.2.4 Transport

在Kombu体系中，用transport对所有的broker进行了抽象，为不同的broker提供了一致的解决方案。通过Kombu，开发者可以根据实际需求灵活的选择或更换broker。

Transport：真实的 MQ 连接，也是真正连接到 MQ(redis/rabbitmq) 的实例。就是存储和发送消息的实体，用来区分底层消息队列是用amqp、Redis还是其它实现的。

Transport负责具体操作，但是很多操作移交给 loop 与 MultiChannelPoller 进行。

##### 4.2.4.1 定义

其主要成员变量为：

- 本transport的驱动类型，名字；
- 对应的 Channel；
- cycle：MultiChannelPoller，具体下文提到；

定义如下：

```python
class Transport(virtual.Transport):
    """Redis Transport."""

    Channel = Channel

    polling_interval = None  # disable sleep between unsuccessful polls.
    default_port = DEFAULT_PORT
    driver_type = 'redis'
    driver_name = 'redis'

    implements = virtual.Transport.implements.extend(
        asynchronous=True,
        exchange_type=frozenset(['direct', 'topic', 'fanout'])
    )

    def __init__(self, *args, **kwargs):
        if redis is None:
            raise ImportError('Missing redis library (pip install redis)')
        super().__init__(*args, **kwargs)

        # Get redis-py exceptions.
        self.connection_errors, self.channel_errors = self._get_errors()
        # All channels share the same poller.
        self.cycle = MultiChannelPoller()
复制代码
```

##### 4.2.4.2 移交操作

Transport负责具体操作，但是很多操作移交给 loop 与 MultiChannelPoller 进行，具体从下面代码可见。

```python
def register_with_event_loop(self, connection, loop):
    cycle = self.cycle
    cycle.on_poll_init(loop.poller)
    cycle_poll_start = cycle.on_poll_start
    add_reader = loop.add_reader
    on_readable = self.on_readable

    def _on_disconnect(connection):
        if connection._sock:
            loop.remove(connection._sock)
    cycle._on_connection_disconnect = _on_disconnect

    def on_poll_start():
        cycle_poll_start()
        [add_reader(fd, on_readable, fd) for fd in cycle.fds]
        
    loop.on_tick.add(on_poll_start)
    loop.call_repeatedly(10, cycle.maybe_restore_messages)
    
    health_check_interval = connection.client.transport_options.get(
        'health_check_interval',
        DEFAULT_HEALTH_CHECK_INTERVAL
    )
    
    loop.call_repeatedly(
        health_check_interval,
        cycle.maybe_check_subclient_health
    )
复制代码
```

其中重点是MultiChannelPoller。一个Connection有一个Transport， 一个Transport有一个MultiChannelPoller，对poll操作都是由MultiChannelPoller完成，redis操作由channel完成。

##### 4.2.4.3 MultiChannelPoller

定义如下，可以理解为执行engine，主要作用是：

- 收集channel；
- 建立fd到channel的映射；
- 建立channel到socks的映射；
- 使用poll；

```python
class MultiChannelPoller:
    """Async I/O poller for Redis transport."""

    eventflags = READ | ERR

    def __init__(self):
        # active channels
        self._channels = set()
        # file descriptor -> channel map.
        self._fd_to_chan = {}
        # channel -> socket map
        self._chan_to_sock = {}
        # poll implementation (epoll/kqueue/select)
        self.poller = poll()
        # one-shot callbacks called after reading from socket.
        self.after_read = set()
复制代码
```

##### 4.2.4.4 获取

Transport是预先生成的，若需要，则依据名字取得。

```python
TRANSPORT_ALIASES = {
    'amqp': 'kombu.transport.pyamqp:Transport',
    'amqps': 'kombu.transport.pyamqp:SSLTransport',
    'pyamqp': 'kombu.transport.pyamqp:Transport',
    'librabbitmq': 'kombu.transport.librabbitmq:Transport',
    'memory': 'kombu.transport.memory:Transport',
    'redis': 'kombu.transport.redis:Transport',
	......
    'pyro': 'kombu.transport.pyro:Transport'
}

_transport_cache = {}


def resolve_transport(transport=None):
    """Get transport by name. """
    if isinstance(transport, str):
        try:
            transport = TRANSPORT_ALIASES[transport]
        except KeyError:
            if '.' not in transport and ':' not in transport:
                from kombu.utils.text import fmatch_best
                alt = fmatch_best(transport, TRANSPORT_ALIASES)
        else:
            if callable(transport):
                transport = transport()
        return symbol_by_name(transport)
    return transport

def get_transport_cls(transport=None):
    """Get transport class by name.
    """
    if transport not in _transport_cache:
        _transport_cache[transport] = resolve_transport(transport)
    return _transport_cache[transport]
复制代码
```

此时Connection数据如下，注意其部分成员变量尚且没有意义：

```python
conn = {Connection} <Connection: redis://localhost:6379// at 0x7faa910cbd68>
 alt = {list: 0} []
 connect_timeout = {int} 5
 connection = {Transport} <kombu.transport.redis.Transport object at 0x7faa91277710>
 cycle = {NoneType} None
 declared_entities = {set: 0} set()
 default_channel = {Channel} <kombu.transport.redis.Channel object at 0x7faa912700b8>
 failover_strategies = {dict: 2} {'round-robin': <class 'itertools.cycle'>, 'shuffle': <function shufflecycle at 0x7faa9109a0d0>}
 failover_strategy = {type} <class 'itertools.cycle'>
 heartbeat = {int} 0
 host = {str} 'localhost:6379'
 hostname = {str} 'localhost'
 manager = {Management} <kombu.transport.virtual.base.Management object at 0x7faa91270160>
 port = {int} 6379
 recoverable_channel_errors = {tuple: 0} ()
 resolve_aliases = {dict: 2} {'pyamqp': 'amqp', 'librabbitmq': 'amqp'}
 transport = {Transport} <kombu.transport.redis.Transport object at 0x7faa91277710>
 transport_cls = {str} 'redis'
 uri_prefix = {NoneType} None
 userid = {NoneType} None
 virtual_host = {str} '/'
复制代码
```

至此，Kombu的基本就建立完成，但是彼此之间没有建立逻辑联系。

所以此时示例如下，注意此时三者没有联系：

```python
+-------------------+       +---------------------+       +--------------------+
| Connection        |       | redis.Transport     |       | MultiChannelPoller |
|                   |       |                     |       |                    |
|                   |       |                     |       |     _channels      |
|                   |       |        cycle +------------> |     _fd_to_chan    |
|     transport +---------> |                     |       |     _chan_to_sock  |
|                   |       |                     |       |     poller         |
+-------------------+       +---------------------+       |     after_read     |
                                                          |                    |
                                                          +--------------------+
+------------------+
| Hub              |
|                  |
|                  |            +-------------+
|      poller +---------------> | _poll       |
|                  |            |             |         +-------+
|                  |            |    _poller+---------> |  poll |
+------------------+            |             |         +-------+
                                +-------------+
+----------------+         +-------------------+
| Exchange       |         | Queue             |
|                |         |                   |
|                |         |                   |
|     channel    | <------------+ exchange     |
|                |         |                   |
|                |         |                   |
+----------------+         +-------------------+
复制代码
```

### 4.3 Connection注册hub

之前我们提到，基本架子已经建立起来，但是各个模块之间彼此没有联系，下面我们就看看如何建立联系。

示例代码来到：

```python
conn.register_with_event_loop(hub)
复制代码
```

这里进行了注册，此时作用是把hub与Connection联系起来。随之调用到：

```python
def register_with_event_loop(self, loop):
    self.transport.register_with_event_loop(self.connection, loop)
复制代码
```

进而调用到transport类：`<kombu.transport.redis.Transport object at 0x7fd23e962dd8>`

具体代码如下：

```python
def register_with_event_loop(self, connection, loop):
    cycle = self.cycle
    cycle.on_poll_init(loop.poller)# 这里建立联系，loop就是hub
    cycle_poll_start = cycle.on_poll_start
    add_reader = loop.add_reader
    on_readable = self.on_readable

    def _on_disconnect(connection):
        if connection._sock:
            loop.remove(connection._sock)
    cycle._on_connection_disconnect = _on_disconnect

    def on_poll_start():
        cycle_poll_start()
        [add_reader(fd, on_readable, fd) for fd in cycle.fds]
        
    loop.on_tick.add(on_poll_start)
    loop.call_repeatedly(10, cycle.maybe_restore_messages)
    
    health_check_interval = connection.client.transport_options.get(
        'health_check_interval',
        DEFAULT_HEALTH_CHECK_INTERVAL
    )
    
    loop.call_repeatedly(
        health_check_interval,
        cycle.maybe_check_subclient_health
    )
复制代码
```

#### 4.3.1 建立Channel

注册最初是建立Channel。这里有一个连接的动作，就是在这里，建立了Channel。

```python
@property
def connection(self):
    """The underlying connection object"""
    if not self._closed:
        if not self.connected:
            return self._ensure_connection(
                max_retries=1, reraise_as_library_errors=False
            )
        return self._connection
复制代码
```

具体建立是在 base.py 中完成，这是 Transport 基类。Stack 如下：

```python
create_channel, base.py:920
establish_connection, base.py:938
_establish_connection, connection.py:801
_connection_factory, connection.py:866
retry_over_time, functional.py:325
_ensure_connection, connection.py:439
connection, connection.py:859
register_with_event_loop, connection.py:266
main, testUb.py:41
<module>, testUb.py:55
复制代码
```

#### 4.3.2 Channel

Channel：与AMQP中概念类似，可以理解成共享一个Connection的多个轻量化连接。就是真正的连接。

可以认为是 redis 操作和连接的封装。每个 Channel 都可以与 redis 建立一个连接，在此连接之上对 redis 进行操作，每个连接都有一个 socket，每个 socket 都有一个 file，从这个 file 可以进行 poll。

为了更好的说明，我们提前给出这个通讯流程大约如下：

```java
            +---------------------------------------------------------------------------------------------------------------------------------------+
            |                                     +--------------+                                   6                       parse_response         |
            |                                +--> | Linux Kernel | +---+                                                                            |
            |                                |    +--------------+     |                                                                            |
            |                                |                         |                                                                            |
            |                                |                         |  event                                                                     |
            |                                |  1                      |                                                                            |
            |                                |                         |  2                                                                         |
            |                                |                         |                                                                            |
    +-------+---+    socket                  +                         |                                                                            |
    |   redis   | <------------> port +-->  fd +--->+                  v                                                                            |
    |           |                                   |           +------+--------+                                                                   |
    |           |    socket                         |           |  Hub          |                                                                   |
    |           | <------------> port +-->  fd +--->----------> |               |                                                                   |
    | port=6379 |                                   |           |               |                                                                   |
    |           |    socket                         |           |     readers +----->  Transport.on_readable                                        |
    |           | <------------> port +-->  fd +--->+           |               |                     +                                             |
    +-----------+                                               +---------------+                     |                                             |
                                                                                                      |                                             |
                                                        3                                             |                                             |
             +----------------------------------------------------------------------------------------+                                             |
             |                                                                                                                                      v
             |                                                                                                                                                  _receive_callback
             |                                                                                                                            5    +-------------+                      +-----------+
+------------+------+                     +-------------------------+                                    'BRPOP' = Channel._brpop_read +-----> | Channel     | +------------------> | Consumer  |
|       Transport   |                     |  MultiChannelPoller     |      +------>  channel . handlers  'LISTEN' = Channel._receive           +-------------+                      +---+-------+
|                   |                     |                         |      |                                                                                           8                |
|                   | on_readable(fileno) |                         |      |                                                                         ^                                  |
|           cycle +---------------------> |          _fd_to_chan +---------------->  channel . handlers  'BRPOP' = Channel._brpop_read               |                                  |
|                   |        4            |                         |      |                             'LISTEN' = Channel._receive                 |                                  |
|  _callbacks[queue]|                     |                         |      |                                                                         |                            on_m  |  9
|          +        |                     +-------------------------+      +------>  channel . handlers  'BRPOP' = Channel._brpop_read               |                                  |
+-------------------+                                                                                    'LISTEN' = Channel._receive                 |                                  |
           |                                                                                                                                         |                                  v
           |                                                7           _callback                                                                    |
           +-----------------------------------------------------------------------------------------------------------------------------------------+                            User Function

复制代码
```

手机上如下：

![img](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/47ad281407154fc6a84c91728609ff2f~tplv-k3u1fbpfcp-zoom-in-crop-mark:1304:0:0:0.awebp)

##### 4.3.2.1 定义

Channel 主要成员是：

- async_pool ：redis异步连接池；
- pool ：redis连接池；
- channel_id ：Channel ID；
- client ：就是StrictRedis之类的driver；
- connection ：对应的Transport；
- cycle = {FairCycle} <FairCycle: 0/0 []>
- queue_order_strategy ：获取queue的策略；
- state ：BrokerState状态；
- subclient ：PubSub所用的client； keyprefix_queue = '{p}_kombu.binding.%s'.format(p=KEY_PREFIX) ：bing用到的key；

比如_get_client可以看出来client。

```python
def _get_client(self):
    if redis.VERSION < (3, 2, 0):
        raise VersionMismatch(
            'Redis transport requires redis-py versions 3.2.0 or later. '
            'You have {0.__version__}'.format(redis))
    return redis.StrictRedis
复制代码
```

简化版定义如下：

```python
class Channel(virtual.Channel):
    """Redis Channel."""

    QoS = QoS

    _client = None
    _subclient = None
    keyprefix_queue = '{p}_kombu.binding.%s'.format(p=KEY_PREFIX)
    keyprefix_fanout = '/{db}.'
    sep = '\x06\x16'
    _fanout_queues = {}
    unacked_key = '{p}unacked'.format(p=KEY_PREFIX)
    unacked_index_key = '{p}unacked_index'.format(p=KEY_PREFIX)
    unacked_mutex_key = '{p}unacked_mutex'.format(p=KEY_PREFIX)
    unacked_mutex_expire = 300  # 5 minutes
    unacked_restore_limit = None
    visibility_timeout = 3600   # 1 hour
    max_connections = 10
    queue_order_strategy = 'round_robin'

    _async_pool = None
    _pool = None

    from_transport_options = (
        virtual.Channel.from_transport_options +
        ('sep',
         'ack_emulation',
         'unacked_key',
		 ......
         'max_connections',
         'health_check_interval',
         'retry_on_timeout',
         'priority_steps')  # <-- do not add comma here!
    )

    connection_class = redis.Connection if redis else None
复制代码
```

##### 4.3.2.2 基类

基类定义如下：

```python
class Channel(AbstractChannel, base.StdChannel):
    """Virtual channel.

    Arguments:
        connection (ConnectionT): The transport instance this
            channel is part of.
    """

    #: message class used.
    Message = Message

    #: QoS class used.
    QoS = QoS

    #: flag to restore unacked messages when channel
    #: goes out of scope.
    do_restore = True

    #: mapping of exchange types and corresponding classes.
    exchange_types = dict(STANDARD_EXCHANGE_TYPES)

    #: flag set if the channel supports fanout exchanges.
    supports_fanout = False

    #: Binary <-> ASCII codecs.
    codecs = {'base64': Base64()}

    #: Default body encoding.
    #: NOTE: ``transport_options['body_encoding']`` will override this value.
    body_encoding = 'base64'

    #: counter used to generate delivery tags for this channel.
    _delivery_tags = count(1)

    #: Optional queue where messages with no route is delivered.
    #: Set by ``transport_options['deadletter_queue']``.
    deadletter_queue = None

    # List of options to transfer from :attr:`transport_options`.
    from_transport_options = ('body_encoding', 'deadletter_queue')

    # Priority defaults
    default_priority = 0
    min_priority = 0
    max_priority = 9
复制代码
```

最终具体举例如下：

```python
self = {Channel} <kombu.transport.redis.Channel object at 0x7fe61aa88cc0>
 Client = {type} <class 'redis.client.Redis'>
 Message = {type} <class 'kombu.transport.virtual.base.Message'>
 QoS = {type} <class 'kombu.transport.redis.QoS'>
 active_fanout_queues = {set: 0} set()
 active_queues = {set: 0} set()
 async_pool = {ConnectionPool} ConnectionPool<Connection<host=localhost,port=6379,db=0>>
 auto_delete_queues = {set: 0} set()
 channel_id = {int} 1
 client = {Redis} Redis<ConnectionPool<Connection<host=localhost,port=6379,db=0>>>
 codecs = {dict: 1} {'base64': <kombu.transport.virtual.base.Base64 object at 0x7fe61a987668>}
 connection = {Transport} <kombu.transport.redis.Transport object at 0x7fe61aa399b0>
 connection_class = {type} <class 'redis.connection.Connection'>
 cycle = {FairCycle} <FairCycle: 0/0 []>
 deadletter_queue = {NoneType} None
 exchange_types = {dict: 3} {'direct': <kombu.transport.virtual.exchange.DirectExchange object at 0x7fe61aa53588>, 'topic': <kombu.transport.virtual.exchange.TopicExchange object at 0x7fe61aa53550>, 
 handlers = {dict: 2} {'BRPOP': <bound method Channel._brpop_read of <kombu.transport.redis.Channel object at 0x7fe61aa88cc0>>, 'LISTEN': <bound method Channel._receive of <kombu.transport.redis.Channel object at 0x7fe61aa88cc0>>}
 pool = {ConnectionPool} ConnectionPool<Connection<host=localhost,port=6379,db=0>>
 qos = {QoS} <kombu.transport.redis.QoS object at 0x7fe61aa88e48>
 queue_order_strategy = {str} 'round_robin'
 state = {BrokerState} <kombu.transport.virtual.base.BrokerState object at 0x7fe61a987748>
 subclient = {PubSub} <redis.client.PubSub object at 0x7fe61aa39cc0>
复制代码
```

##### 4.3.2.3 redis消息回调函数

关于上面成员变量，这里需要说明的是

```python
 handlers = {dict: 2} 
  {
    'BRPOP': <bound method Channel._brpop_read of <kombu.transport.redis.Channel object at 0x7fe61aa88cc0>>, 
    'LISTEN': <bound method Channel._receive of <kombu.transport.redis.Channel object at 0x7fe61aa88cc0>>
  }
复制代码
```

这是redis有消息时的回调函数，即：

- BPROP 有消息时候，调用 Channel._brpop_read；
- LISTEN 有消息时候，调用 Channel._receive；

##### 4.3.2.4  Redis 直接相关的主要成员

与Redis 直接相关的成员定义在：redis/client.py。

与 Redis 直接相关的主要成员是如下，会利用如下变量进行具体 redis操作：

- async_pool ：redis异步连接池；
- pool ：redis连接池；
- client ：就是StrictRedis之类的driver；
- subclient ：PubSub所用的client；

分别对应如下类型：

```java
channel = {Channel} <kombu.transport.redis.Channel object at 0x7fabeea23b00>
 Client = {type} <class 'redis.client.Redis'>
 async_pool = {ConnectionPool} ConnectionPool<Connection<host=localhost,port=6379,db=0>>
 client = {Redis} Redis<ConnectionPool<Connection<host=localhost,port=6379,db=0>>>
 connection = {Transport} <kombu.transport.redis.Transport object at 0x7fabeea23940>
 connection_class = {type} <class 'redis.connection.Connection'>
 connection_class_ssl = {type} <class 'redis.connection.SSLConnection'>
 pool = {ConnectionPool} ConnectionPool<Connection<host=localhost,port=6379,db=0>>
 subclient = {PubSub} <redis.client.PubSub object at 0x7fabeea97198>
复制代码
```

具体代码如下：

```python
def _create_client(self, asynchronous=False):
    if asynchronous:
        return self.Client(connection_pool=self.async_pool)
    return self.Client(connection_pool=self.pool)

def _get_pool(self, asynchronous=False):
    params = self._connparams(asynchronous=asynchronous)
    self.keyprefix_fanout = self.keyprefix_fanout.format(db=params['db'])
    return redis.ConnectionPool(**params)

def _get_client(self):
    if redis.VERSION < (3, 2, 0):
        raise VersionMismatch(
            'Redis transport requires redis-py versions 3.2.0 or later. '
            'You have {0.__version__}'.format(redis))
    return redis.StrictRedis

@property
def pool(self):
    if self._pool is None:
        self._pool = self._get_pool()
    return self._pool

@property
def async_pool(self):
    if self._async_pool is None:
        self._async_pool = self._get_pool(asynchronous=True)
    return self._async_pool

@cached_property
def client(self):
    """Client used to publish messages, BRPOP etc."""
    return self._create_client(asynchronous=True)

@cached_property
def subclient(self):
    """Pub/Sub connection used to consume fanout queues."""
    client = self._create_client(asynchronous=True)
    return client.pubsub()
复制代码
```

因为添加了Channel，所以此时如下：

```python
+-----------------+
| Channel         |
|                 |      +-----------------------------------------------------------+
|    client  +---------> | Redis<ConnectionPool<Connection<host=localhost,port=6379> |
|                 |      +-----------------------------------------------------------+
|                 |
|                 |      +---------------------------------------------------+-+
|    pool  +---------->  |ConnectionPool<Connection<host=localhost,port=6379 > |
|                 |      +---------------------------------------------------+-+
|                 |
|                 |
|                 |
|    connection   |
|                 |
+-----------------+

+-------------------+       +---------------------+       +--------------------+
| Connection        |       | redis.Transport     |       | MultiChannelPoller |
|                   |       |                     |       |                    |
|                   |       |                     |       |     _channels      |
|                   |       |        cycle +------------> |     _fd_to_chan    |
|     transport +---------> |                     |       |     _chan_to_sock  |
|                   |       |                     |       |     poller         |
+-------------------+       +---------------------+       |     after_read     |
                                                          |                    |
+------------------+                                      +--------------------+
| Hub              |
|                  |
|                  |            +-------------+
|      poller +---------------> | _poll       |
|                  |            |             |         +-------+
|                  |            |    _poller+---------> |  poll |
+------------------+            |             |         +-------+
                                +-------------+
+----------------+         +-------------------+
| Exchange       |         | Queue             |
|                |         |                   |
|                |         |                   |
|     channel    | <------------+ exchange     |
|                |         |                   |
|                |         |                   |
+----------------+         +-------------------+

复制代码
```

#### 4.3.3 channel 与 Connection 联系

讲到这里，基本道理大家都懂，但是具体两者之间如何联系，我们需要再剖析下。

##### 4.3.3.1 从Connection得到channel

在Connection定义中有如下，原来 Connection 是通过 transport 来得到 channel：

```python
def channel(self):
    """Create and return a new channel."""
    self._debug('create channel')
    chan = self.transport.create_channel(self.connection)
    return chan
复制代码
```

##### 4.3.3.2 Transport具体创建

在Transport之中有：

```python
def create_channel(self, connection):
    try:
        return self._avail_channels.pop()
    except IndexError:
        channel = self.Channel(connection)
        self.channels.append(channel)
        return channel
复制代码
```

原来在 Transport 有两个channels 列表：

```python
self._avail_channels
self.channels
复制代码
```

如果_avail_channels 有内容则直接获取，否则生成一个新的Channel。

在真正连接时候，会调用 establish_connection 放入self._avail_channels。

```python
def establish_connection(self):
    # creates channel to verify connection.
    # this channel is then used as the next requested channel.
    # (returned by ``create_channel``).
    self._avail_channels.append(self.create_channel(self))
    return self     # for drain events
复制代码
```

其堆栈如下：

```python
__init__, redis.py:557
create_channel, base.py:921
establish_connection, base.py:939
_establish_connection, connection.py:801
_connection_factory, connection.py:866
retry_over_time, functional.py:313
_ensure_connection, connection.py:439
connection, connection.py:859
channel, connection.py:283
<module>, node.py:11
复制代码
```

##### 4.3.3.3 建立联系

在init中有：

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    if not self.ack_emulation:  # disable visibility timeout
        self.QoS = virtual.QoS

    self._queue_cycle = cycle_by_name(self.queue_order_strategy)()
    self.Client = self._get_client()
    self.ResponseError = self._get_response_error()
    self.active_fanout_queues = set()
    self.auto_delete_queues = set()
    self._fanout_to_queue = {}
    self.handlers = {'BRPOP': self._brpop_read, 'LISTEN': self._receive}
 
    ......

    self.connection.cycle.add(self)  # add to channel poller.

    if register_after_fork is not None:
        register_after_fork(self, _after_fork_cleanup_channel)
复制代码
```

重点是：

```python
self.connection.cycle.add(self)  # add to channel poller.
复制代码
```

这就是把 Channel与Transport 中的 poller 联系起来，这样Transport可以利用Channel去与真实的redis进行交互。

堆栈如下：

```python
add, redis.py:277
__init__, redis.py:531
create_channel, base.py:920
establish_connection, base.py:938
_establish_connection, connection.py:801
_connection_factory, connection.py:866
retry_over_time, functional.py:325
_ensure_connection, connection.py:439
connection, connection.py:859
register_with_event_loop, connection.py:266
main, testUb.py:41
复制代码
```

因为已经联系起来，所以此时如下：

```python
+-----------------+
| Channel         |
|                 |      +-----------------------------------------------------------+
|    client  +---------> | Redis<ConnectionPool<Connection<host=localhost,port=6379> |
|                 |      +-----------------------------------------------------------+
|                 |
|                 |      +---------------------------------------------------+-+
|    pool  +---------->  |ConnectionPool<Connection<host=localhost,port=6379 > |
|                 |      +---------------------------------------------------+-+
|                 |
|                 |   <------------------------------------------------------------+
|                 |                                                                |
|    connection +---------------+                                                  |
|                 |             |                                                  |
+-----------------+             |                                                  |
                                v                                                  |
+-------------------+       +---+-----------------+       +--------------------+   |
| Connection        |       | redis.Transport     |       | MultiChannelPoller |   |
|                   |       |                     |       |                    |   |
|                   |       |                     |       |     _channels +--------+
|                   |       |        cycle +------------> |     _fd_to_chan    |
|     transport +---------> |                     |       |     _chan_to_sock  |
|                   |       |                     |       |     poller         |
+-------------------+       +---------------------+       |     after_read     |
                                                          |                    |
+------------------+                                      +--------------------+
| Hub              |
|                  |
|                  |            +-------------+
|      poller +---------------> | _poll       |
|                  |            |             |         +-------+
|                  |            |    _poller+---------> |  poll |
+------------------+            |             |         +-------+
                                +-------------+
+----------------+         +-------------------+
| Exchange       |         | Queue             |
|                |         |                   |
|                |         |                   |
|     channel    | <------------+ exchange     |
|                |         |                   |
|                |         |                   |
+----------------+         +-------------------+

复制代码
```

#### 4.3.4 Transport 与 Hub 联系

on_poll_init 这里就是把 kombu.transport.redis.Transport 与 Hub 联系起来。

用`self.poller = poller`把Transport与Hub的poll联系起来。这样 Transport 就可以利用 poll。

```python
def on_poll_init(self, poller):
    self.poller = poller
    for channel in self._channels:
        return channel.qos.restore_visible(
            num=channel.unacked_restore_limit,
        )
复制代码
```

此时变量如下：

```python
poller = {_poll} <kombu.utils.eventio._poll object at 0x7fb9bcd87240>
self = {MultiChannelPoller} <kombu.transport.redis.MultiChannelPoller object at 0x7fb9bcdd6a90>
 after_read = {set: 0} set()
 eventflags = {int} 25
 fds = {dict: 0} {}
 poller = {_poll} <kombu.utils.eventio._poll object at 0x7fb9bcd87240>
复制代码
```

因此，我们最终如下：

```python
+-----------------+
| Channel         |
|                 |      +-----------------------------------------------------------+
|    client  +---------> | Redis<ConnectionPool<Connection<host=localhost,port=6379> |
|                 |      +-----------------------------------------------------------+
|                 |
|                 |      +---------------------------------------------------+-+
|    pool  +---------->  |ConnectionPool<Connection<host=localhost,port=6379 > |
|                 |      +---------------------------------------------------+-+
|                 |
|                 |   <------------------------------------------------------------+
|                 |                                                                |
|    connection +---------------+                                                  |
|                 |             |                                                  |
+-----------------+             |                                                  |
                                v                                                  |
+-------------------+       +---+-----------------+       +--------------------+   |
| Connection        |       | redis.Transport     |       | MultiChannelPoller |   |
|                   |       |                     |       |                    |   |
|                   |       |                     |       |     _channels +--------+
|                   |       |        cycle +------------> |     _fd_to_chan    |
|     transport +---------> |                     |       |     _chan_to_sock  |
|                   |       |                     |    +<----+  poller         |
+-------------------+       +---------------------+    |  |     after_read     |
                                                       |  |                    |
+------------------+                    +--------------+  +--------------------+
| Hub              |                    |
|                  |                    v
|                  |            +-------+-----+
|      poller +---------------> | _poll       |
|                  |            |             |         +-------+
|                  |            |    _poller+---------> |  poll |
+------------------+            |             |         +-------+
                                +-------------+
+----------------+         +-------------------+
| Exchange       |         | Queue             |
|                |         |                   |
|                |         |                   |
|     channel    | <------------+ exchange     |
|                |         |                   |
|                |         |                   |
+----------------+         +-------------------+

复制代码
```



### 4.4 Poll系列模型

Kombu 利用了 Poll 模型，所以我们有必要介绍下。这就是IO多路复用。

IO多路复用是指内核一旦发现进程指定的一个或者多个IO条件准备读取，它就通知该进程。IO多路复用适用比如当客户处理多个描述字时（一般是交互式输入和网络套接口）。

与多进程和多线程技术相比，I/O多路复用技术的最大优势是系统开销小，系统不必创建进程/线程，也不必维护这些进程/线程，从而大大减小了系统的开销。

#### 4.4.1 select

select 通过一个select()系统调用来监视多个文件描述符的数组（在linux中一切事物皆文件，块设备，socket连接等）。

当select()返回后，该数组中就绪的文件描述符便会被内核修改标志位（变成ready），使得进程可以获得这些文件描述符从而进行后续的读写操作（select会不断监视网络接口的某个目录下有多少文件描述符变成ready状态【在网络接口中，过来一个连接就会建立一个'文件'】，变成ready状态后，select就可以操作这个文件描述符了）。

#### 4.4.2 poll

poll 和select在本质上没有多大差别，但是poll没有最大文件描述符数量的限制。

poll和select同样存在一个缺点就是，包含大量文件描述符的数组被整体复制于用户态和内核的地址空间之间，而不论这些文件描述符是否就绪，它的开销随着文件描述符数量的增加而线性增大。

select()和poll()将就绪的文件描述符告诉进程后，如果进程没有对其进行IO操作，那么下次调用select()和poll() 的时候将再次报告这些文件描述符，所以它们一般不会丢失就绪的消息，这种方式称为水平触发（Level Triggered）。

#### 4.4.2.3 epoll

epoll由内核直接支持，可以同时支持水平触发和边缘触发（Edge Triggered，只告诉进程哪些文件描述符刚刚变为就绪状态，它只说一遍，如果我们没有采取行动，那么它将不会再次告知，这种方式称为边缘触发），理论上边缘触发的性能要更高一些。

epoll同样只告知那些就绪的文件描述符，而且当我们调用epoll_wait()获得就绪文件描述符时，返回的不是实际的描述符，而是一个代表 就绪描述符数量的值，你只需要去epoll指定的一个数组中依次取得相应数量的文件描述符即可，这里也使用了内存映射（mmap）技术，这样便彻底省掉了 这些文件描述符在系统调用时复制的开销。

另一个本质的改进在于epoll采用基于事件的就绪通知方式。在select/poll中，进程只有在调用一定的方法后，内核才对所有监视的文件描 述符进行扫描，而epoll事先通过epoll_ctl()来注册一个文件描述符，一旦基于某个文件描述符就绪时，内核会采用类似callback的回调 机制，迅速激活这个文件描述符，当进程调用epoll_wait()时便得到通知。

#### 4.4.2.4 通俗理解

##### 4.4.2.4.1 阻塞I/O模式

阻塞I/O模式下，内核对于I/O事件的处理是阻塞或者唤醒，一个线程只能处理一个流的I/O事件。如果想要同时处理多个流，要么多进程(fork)，要么多线程(pthread_create)，很不幸这两种方法效率都不高。

##### 4.4.2.4.2 非阻塞模式

非阻塞忙轮询的I/O方式可以同时处理多个流。我们只要不停的把所有流从头到尾问一遍，又从头开始。这样就可以处理多个流了，但这样的做法显然不好，因为如果所有的流都没有数据，那么只会白白浪费CPU。

###### 4.4.2.4.2.1 代理模式

非阻塞模式下可以把I/O事件交给其他对象（select以及epoll）处理甚至直接忽略。

为了避免CPU空转，可以引进一个代理（一开始有一位叫做select的代理，后来又有一位叫做poll的代理，不过两者的本质是一样的）。这个代理比较厉害，可以同时观察许多流的I/O事件，在空闲的时候，会把当前线程阻塞掉，当有一个或多个流有I/O事件时，就从阻塞态中醒来，于是我们的程序就会轮询一遍所有的流（于是我们可以把“忙”字去掉了）。代码长这样:

```python
 while true {  
       select(streams[])  
       for i in streams[] {  
             if i has data  
             read until unavailable  
        }  
 }  
```

于是，如果没有I/O事件产生，我们的程序就会阻塞在select处。但是依然有个问题，我们从select那里仅仅知道了，有I/O事件发生了，但却并不知道是那几个流（可能有一个，多个，甚至全部），我们只能无差别轮询所有流，找出能读出数据，或者写入数据的流，对他们进行操作。

###### 4.4.2.4.2.2 epoll

epoll可以理解为event poll，**不同于忙轮询和无差别轮询，epoll只会把哪个流发生了怎样的I/O事件通知我们**。此时我们对这些流的操作都是有意义的（复杂度降低到了O(1)）。

epoll版服务器实现原理类似于select版服务器，都是通过某种方式对套接字进行检验其是否能收发数据等。但是epoll版的效率要更高，同时没有上限。

在select、poll中的检验，是一种被动的轮询检验，而epoll中的检验是一种主动地事件通知检测，即：当有套接字符合检验的要求，便会主动通知，从而进行操作。这样的机制自然效率会高一点。

同时在epoll中要用到文件描述符，所谓文件描述符实质上是数字。

epoll的主要用处在于：

```python
epoll_list = epoll.epoll()
```

如果进程在处理while循环中的代码时，一些套接字对应的客户端如果发来了数据，那么操作系统底层会自动的把这些套接字对应的文件描述符写入该列表中，当进程再次执行到epoll时，就会得到了这个列表，此时这个列表中的信息就表示着哪些套接字可以进行收发了。**因为epoll没有去依次的查看，而是直接拿走已经可以收发的fd，所以效率高！**





### 4.5 总结

具体如图，可以看出来，上面三个基本模块已经联系到了一起。

可以看到，

- 目前是以Transport为中心，把 Channel代表的真实 redis 与 Hub其中的poll联系起来，但是具体如何使用则尚未得知。
- 用户是通过Connection来作为API入口，connection可以得到Transport。

既然基本架构已经搭好，所以从下文开始，我们看看 Consumer 是如何运作的。


本节链接：https://juejin.cn/post/6937559898045546527





## 五、kombu使用

### 5.1 producer

#### 5.1.1 代码示例

##### 直接发送

```
import json

from kombu import Exchange, Queue, Connection
from kombu.pools import producers, connections


def _transport_func(queue, data):
    import json
    from kombu import Connection, Exchange, Producer, Queue
    hostname = f"amqp://openstack:comleader@123@192.168.230.107:5672//"
    conn = Connection(hostname)
    channel = conn.channel()
    # exchange = Exchange("snapshot", type="direct", durable=False)
    exchange = Exchange("test-12", durable=False)
    producer = Producer(exchange=exchange, channel=channel, routing_key=queue)
    queue_conn = Queue(name=queue, exchange=exchange, routing_key=queue)
    queue_conn.maybe_bind(conn)
    queue_conn.declare()
    producer.publish(json.dumps(data))
    conn.release()

```



##### 使用pools

```
import json

from kombu import Exchange, Queue, Connection
from kombu.pools import producers, connections


def _transport_func_use_pool(queue, data):
    # hostname = f"amqp{transport_url.split('rabbit')[-1]}:5672//"
    hostname = f"amqp://openstack:comleader@123@192.168.230.107:5672//"
    connection = Connection(hostname=hostname)
    exchange = Exchange('test-11', durable=False)
    send_queue_conn = Queue(queue, exchange=exchange, routing_key=queue)
    with connections[connection].acquire(block=True) as conn:
        with producers[conn].acquire(block=True) as producer:
            producer.publish(
                serializer='json',
                body=data,
                exchange=exchange,
                declare=[send_queue_conn],
                routing_key=queue
            )
    connection.release()

```



#### 5.1.2 参数解释

##### Producer参数

Producer 消息生产者.

```
class kombu.Producer(channel, exchange=None, routing_key=None, serializer=None, auto_declare=None, compression=None, on_return=None)
```

参数:	

```
channel – Connection 或者channel.
exchange – 可选参数，使用的exchange.
routing_key – 可选参数，消息的路由键.
serializer – 使用的序列化机制,默认使用“json”.
compression – 使用的压缩方法. 默认不压缩.
auto_declare – 在安装时自动声明使用的exchange. 默认值是True.
on_return – 消息不能递交时使用的callback,需要在publish()方法中使用mandatory或immediate参数. 这个callback的签名是: (exception, exchange, routing_key, message). 需要注意的是使用这个特性时,producer需要自己处理events.



默认值含义：
auto_declare  = True
默认情况下会在构造对象时自动声明exchange. 如果你想手动声明,需要设置此值为False.

compression  = None
采用的压缩方法,默认不压缩.

declare ( )
声明exchange.，声明后才会真正创建，exchange会自动声明,如果开启了auto_declare.

exchange  = None
默认的exchange.

maybe_declare ( entity,  retry=False,  **retry_policy )[source]
如果在会话里还没有声明exchange则声明.

on_return  = None
使用的callback,见参数描述.

```



##### publish()参数

向指定的exchange发布消息.

```
publish(body, routing_key=None, delivery_mode=None, mandatory=False,  immediate=False, priority=0, content_type=None, content_encoding=None,  serializer=None, headers=None, compression=None, exchange=None, retry=False, retry_policy=None, declare=[], expiration=None, **properties)
```



参数:	

```
body – 消息体.
routing_key – 消息的路由键.
delivery_mode – 了解delivery_mode.
mandatory – 目前还不支持.
immediate – 目前还不支持.
priority – 消息的优先级. 0到9.
content_type – 消息内容的类型,默认auto-detect.
content_encoding – 消息内容的编码,默认auto-detect.
serializer – 使用的序列化手段,默认auto-detect.
compression – 使用的压缩方法,默认是none.
headers – 附加到消息体的头.
exchange – 发布消息的exchange. 注意exchange必须被声明.
declare – 需要的实体对象列表,在发布消息之前必须声明.实体对象用maybe_declare()方法来声明.
retry – 尝试重新发布消息, 或者在连接丢失时声明实体对象.
retry_policy – 重新尝试的策略, 这是ensure()方法支持的一个关键字参数.
expiration – 每个消息的TTL,以秒为单位. 默认是没有.
**properties – 额外的消息属性,参考AMQP说明.
revive ( channel )[source]
连接断开后重新复活producer.

routing_key  = ''
默认的路由键.

serializer  = None
使用的序列化机制. 默认使用JSON.
```



参数解释参考链接：https://blog.csdn.net/happyAnger6/article/details/54696457





### 5.2 consumer



#### 5.2.1 代码示例

```
from kombu import Connection, Exchange, Queue, Consumer

hostname = f"amqp://openstack:comleader@123@192.168.230.107:5672//"
connection = Connection(hostname=hostname)
exchange = Exchange('test-12', durable=False)
queue_name = "test-12"
queue = Queue(queue_name, exchange=exchange, routing_key=queue_name)


def process_message(body, message):
    print("The body is {}".format(body))
    message.ack()


with Consumer(connection, queues=queue, callbacks=[process_message], accept=["text/plain", "application/json"]):
    connection.drain_events(timeout=2)

```



#### 5.2.2 参数解释

##### Consumer参数

消息消费者.

```
class kombu.Consumer(channel, queues=None, no_ack=None, auto_declare=None, callbacks=None, on_decode_error=None, on_message=None, accept=None, tag_prefix=None)
```

参数:	

```
channel – 这个消费者使用的connection/channel.
queues – 用于消费的单个或者一个队列列表.

auto_declare – 默认情况下,所有的实体对象会在安装时声明, 如果你想手动控制对象的声明设置此值为 False.

no_ack –是否自动对消息进行确认的标志. 如果开启,broker会自动确认消息. 这可以提高性能,但同时意味着消息被删除时你无法进行控制.默认关闭.

callbacks - 当消息到达时,按顺序调用的callbacks列表.

accept - 可以接收的消息类型列表.如果消费者接收到了不信任的消费类型会抛出异常. 默认情况下允许所有的消息类型,但是如果调用了kombu.disable_untrusted_serializers()将只允许接受json格式的消息.

declare - 声明队列,交换器和绑定.

on_decode_error - 消息不能解码时的callback.
```



##### Consumer函数说明

```
Consumer.add_queue(queue)
增加一个要消费的队列.调用这个函数不会开始从队列中消费消息, 你需要在之后调用consume().

Consumer.auto_declare = True
默认情况下,所有的实体对象会在安装时声明, 如果你想手动控制对象的声明设置此值为 False.

Consumer.callbacks = None
当消息到达时,按顺序调用的callbacks列表.


Consumer.cancel( )   结束所有活动的队列消费.
不会对已经递交的消息起作用, 这意味着服务器不会再向这个消费者发送任何消息.

Consumer.cancel_by_queue(queue)
从指定的队列取消消费消息.

Consumer.close( )
结束所有活动的队列消费.不会对已经递交的消息起作用, 这意味着服务器不会再向这个消费者发送任何消息.


Consumer.consume(no_ack=None) 开始消费消息.
可以被调用多次, 会从上次调用之后新加入的队列中消费消息, 它不会取消从删除的队列中消费消息 ( 使用cancel_by_queue()).

Consumer.consuming_from(queue) 返回True,如果消费者当前正在从队列中消费消息.


Consumer.declare( )声明队列,交换器和绑定. 这些会自动声明,如果设置了auto_declare.


Consumer.flow(active)
Enable/disable对端的流.
这是一种简单的流控机制,一端可以防止自己的队列溢出或者发现自己接收到了它所能够处理的最大消息数.接收到停止请求的一端会在发送完当前内容后停止发送走到另一端取消了流控.


Consumer.no_ack = None
是否自动对消息进行确认的标志. 如果开启,broker会自动确认消息. 这可以提高性能,但同时意味着消息被删除时你无法进行控制.默认关闭.


Consumer.on_decode_error = None
消息不能解码时的callback.
这个函数的签名有2个参数: (message, exc), 一个是解码失败的消息,另外一个是解码失败时抛出的异常.


Consumer.on_message =None
当消息接收时调用的可选函数
这个函数会代替 receive()方法, 同时 callbacks 也会被禁用.
所以当你不想消息被自动解码时可以用它来代替callbacks when you don’t want the body to be automatically decoded. 注意消息如果是压缩的仍然会被解压.
这个函数的签名要求一个参数, 是原始的消息对象 (Message的一个子类).
需要注意message.body属性, 代表了消息的原始内容, 在一些情况下是只读的buffer 对象.


Consumer.purge( ) 从所有队列中清除消息.
Warning 这会删除所有准备好的消息,没有undo操作.


Consumer.qos(prefetch_size=0, prefetch_count=0, apply_global=False)
指定qos.
客户端可以要求消息被提前发送在处理另外一个消息时,这样接下来的消息已经达到了本地而不需要再等待从channel中发送过来,这样的预发送机制可以提高性能.
如果设置了no_ack参数,则预发送窗口被忽略.
参数 :	
prefetch_size – 8进制的预发送窗口大小. 服务端将会提前发送消息如果这个值小于等于可以预发送的大小 (还有一些其它限制). 设置为0意味着没有限制, 其它的限制仍会起作用.
prefetch_count – 指定所有消息总共的预发送窗口.
apply_global – 在所有通道上应用新的全局配置.
Consumer. queues  = None
用于消费的单个或者一个队列列表.


Consumer.receive(body, message) 消息达到时调用方法.
分发到注册的callbacks.
参数:	
body – 解码后的消息体.
message – 消息实例.
抛出:	NotImplementedError – 如果没有注册callbacks.


Consumer.recover(requeue=False)重新递交没有确认的消息.
在指定的channel上要求broker重新递交所有未确认的消息.
参数:	requeue – 默认情况下消息会被重新递交给原来的接收者.如果设置require为True,服务器将会尝试对消息进行重新排队,可能将它递交给另外一个候选消费者.


Consumer.register_callback(callback)  注册一个新的callback用于接收到消息时调用.
callback的签名需要接收2个参数:(body, message), 解码后的消息体和消息实例 (Message的一个子类).


Consumer.revive(channel)
连接丢失时唤醒消费者.
```



参数解释参考链接：https://blog.csdn.net/happyAnger6/article/details/54696457













