



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

绑定是交换机（exchange）将消息（message）路由给队列（queue）所需遵循的规则。

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

当一个应用不再需要连接到AMQP代理的时候，需要优雅的释放掉AMQP连接，而不是直接将TCP连接关闭。

### 1.7 通道 （channels）

AMQP 提供了通道（channels）来处理多连接，可以把通道理解成共享一个TCP连接的多个轻量化连接。

这可以应对有些应用需要建立多个连接的情形，开启多个TCP连接会消耗掉过多的系统资源。

在多线程/进程的应用中，为每个线程/进程开启一个通道（channel）是很常见的，并且这些通道不能被线程/进程共享。

**通道号** 通道之间是完全隔离的，因此每个AMQP方法都需要携带一个通道号，这样客户端就可以指定此方法是为哪个通道准备的。

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

direct：消息路由到满足此条件的队列中(queue,可以有多个)： routing key = binding key 

topic：消息路由到满足此条件的队列中(queue,可以有多个)：routing key 匹配 binding pattern. binding pattern是类似正则表达式的字符串，可以满足复杂的路由条件。

fanout：消息路由到多有绑定到该exchange的队列中。

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





下面几个概念是RPC扩展的：
Namespace:用来组织server中的方法(method),默认是null。
Method：及被调用的方法，和普通(本地)方法调用中的方法是一个概念。
API version：用来标识server中方法的版本。随着时间的推移，server中的方法可能不断变化，提供版本信息可以保持对之前client的兼容。
Transport：对RPC的底层实现机制的抽象。

、RPC的使用场景
Openstack中RPC的主要使用场景：
随机调用某server上的一个方法：
Invoke Method on One of Multiple Servers
这个应该是Openstack中最常用的一种RPC调用，每个方法都会有多个server来提供，client调用时由底层机制选择一个server来处理这个调用请求。
像nova-scheduler, nova-conductor都可以以这种多部署方式提供服务。

这种场景通过AMQP的topic exchange实现。
所有server在binding中为binding key指定一个相同的topic， client在调用时使用这个topic既可实现。

调用某特定server上的一个方法：
Invoke Method on a Specific Server
一般Openstack中的各种scheduler会以这种方式调用。通常scheduler都会先选定一个节点，然后调用该节点上的服务。

这种场景通过AMQP的topic exchange实现。
每个server在binding中为其binding key指定一个自己都有的topic， client在调用时使用这个topic既可实现。

调用所有server上的一个方法：
Invoke Method on all of Multiple Servers
这种其实就是一个广播系统。就像开会议，台上的人讲话，台下的人都能听到。
Openstack中有些rpcapi.py的某些方法带有fanout=True参数，这些都是让所有server处理某个请求的情况。
例子： neutron中所有plugin都会有一个AgentNotifierApi，这个rpc是用来调用安装在compute上的L2 agent。因为存在多个L2 agent(每个compute上都会有)，所以要用广播模式。

这种场景通过AMQP的fanout exchange实现。
每个server在binding中将其队列绑定到一个fanout exchange， client在调用时指定exchange类型为fanout即可。server和client使用同一个exchange。

RCP的实现
目前Openstack中有两种RPC实现，一种是在oslo messaging,一种是在openstack.common.rpc。
openstack.common.rpc是旧的实现，oslo messaging是对openstack.common.rpc的重构。openstack.common.rpc在每个项目中都存在一份拷贝，oslo messaging即将这些公共代码抽取出来，形成一个新的项目。oslo messaging也对RPC API进行了重新设计，具体参考前文。


以后的方向是各个项目都会使用oslo messaging的RPC功能，停止使用openstack.common.rpc。目前(icehouse release)nova, cinder都已经完成转变，neutron还在使用openstack.common.rpc。

rpc.call和rpc.cast的区别：
从实现代码上看，他们的区别很小，就是call调用时候会带有wait_for_reply=True参数，cast不带

notification

oslo messaging中除了RPC外，还有另外一种跨进程通信方式，即消息通知(notification)。notification和前面的第三种RPC场景(广播系统)非常类似，区别就是notification的消息(message)格式是有固定格式的，而RPC中的消息并无固定格式，取决于client/server之间的约定。

目前消息系统的主要receiver(消息收集者)为ceilometer系统，而publisher就是Openstack个项目的service。如nova-compute会针对虚拟机的生命周期发出各种通知：start/stop/create/destroy等。

notification的底层机制可以使用RPC，及driver类型为MessagingDriver。

具体参见：https://wiki.openstack.org/wiki/Oslo/Messaging#oslo.notify



























