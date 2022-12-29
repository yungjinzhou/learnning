# magnum部署k8s


## 创建template流程

### 代码位置：/api/controllers/v1/cluster_template.py  
  ClusterTemplatesController  
  def post

- 1.构建context；

- 2.policy.enforce验证创建模板的操作是否合规；

- 3.构造cluster_template_dict字典；

- 4.创建openstak cli对象； 

- 5.校验传进来的参数并验证是否存在；

- 6.验证镜像id；

- 7.验证os_distro(镜像属性)；

- 8.验证项目id；

- 9.验证用户；

- 10.设置验证模板公开或私有；

- 11.处理模板名称；

- 12.生成数据库对象(objects操作)；

	- 生成对象

	- 使用sqlarchemy库生成模型

- 13.写入数据库；

- 14.生成链接，返回链接。

## 创建cluster流程

### magnum-api

- magnum-api启动流程

	- wsgi  paste等实现启动

	- 

- 入口代码位置：/api/controllers/v1/cluster.py  
  ClusterController  
  def post

	- 1.构建context；

	- 2.验证执行动作(cluster:create)；

	- 3.校验cluster配额；

	- 4.提取模板信息；

	- 5.验证资源(用户、镜像等)；

	- 6.生成数据库对象；

	- 7.rpc调用请求创建cluster；  
	  pecan.request.rpcapi.cluster_create_async(new_cluster, cluster.create_timeout)

		- 调用magnum/conductor/api.py里API类的cluster_create_async方法  
		  self._cast('cluster_create', cluster=cluster,  
		  create_timeout=create_timeout)  
		  topic=magnum-conductor(该类加载了conf中的配置)

			- magnum/common/rpc_service.py  
			  调用rpc的API类的cast方法  
			  self._client.cast(self._context, method, *args, **kwargs)  
			  此时method=cluster_create  
			  transport=messaging.get_rpc_transport(CONF, **kwargs)

				- API类__init__加载的信息  
				  self._client是messaging中PRCClinet类的实例

					- 代码位置：magnum/common/rpc_service.py  
					  target = messaging.Target(topic=topic, server=server)

						- Target类定义了exchange等参数

					- self._client = messaging.RPCClient(transport, target,                           serializer=serializer, timeout=timeout)

				- 继续调用oslo.messaging/rpc/client.py中的cast方法  
				  self.prepare().cast(ctxt, method, **kwargs)  
				  self.prepare()：功能：调用上下文的方法(此处调用父类_BaseCallContext的cast方法)

					- 1.msg重构；

					- 2.ctxt序列化；    

					- 3.msg版本检查；

					- 4.发送rpc消息

						- 调用oslo.messaging/transport.py里Tranport类的_send发送消息  
						  self.transport._send(self.target, msg_ctxt, msg, retry=self.retry)

							- 调用对应的driver发送  
							  根据前面的解析，应该调用的driver是impl_rabbit，查看oslo_messaging/_drivers/impl_rabbit.py，没有send方法，查看父类(AMQPDriverBase), oslo_messaging/_drivers/amqpdriver.py的send方法，  
							  self._driver.send(target, ctxt, message, wait_for_reply=wait_for_reply, timeout=timeout, call_monitor_timeout=call_monitor_timeout, retry=retry)

								- 1.是否是call调用判断及处理；

								- 2.添加unique_id到rpc；

								- 3.封装数据；

								- 4.建立连接；

								- 5. 加载及获取数据  
								  topic: magnum-condutor  
								  exchange: magnum  
								  此处取default_exchange，  
								  exchange加载位置：magnum/common/config.py

								- 6. conn.topic_send发送

									- 代码位置：oslo_messaging/_drivers/rabbit.py里Connection类的topic_send

									- rpc发送topic类型的消息  
									  1.exchange对象及参数(从配置文件读取)durable: false；auto_delete:false；  
									  routing_key: topic(magnum-conductor)  
									  2. self._ensure_publishing(self._publish, exchange, msg,  
									                              routing_key=topic, timeout=timeout,  
									                              retry=retry)  
									  没有找到queue声明以及与exchange绑定的位置

										- self._publish调用的函数  
										  def _publish(self, exchange, msg, routing_key=None, timeout=None):  
										      """Publish a message."""  
										     。。。。。。          
										  self._producer.publish(msg, exchange=exchange, routing_key=routing_key,  
										                         expiration=timeout, compression=self.kombu_compression)

										- def _ensure_publishing(self, method, exchange, msg, routing_key=None,  
										                         timeout=None, retry=None):  
										      """Send to a publisher based on the publisher class."""  
										      method = functools.partial(method, exchange, msg, routing_key, timeout)  
										      with self._connection_lock:  
										          self.ensure(method, retry=retry, error_callback=_error_callback)

	- 8.返回cluster uuid。

### magnum-conductor

- 代码位置：magnum/cmd/conductor.py  
  cmd启动

	- 1.获取参数及版本检查

	- 2.要注册进rpc服务的endpoints

		- indrection_api.Handler()

			- 有_object_dispatch获取方法

		- cluster_conductor.Handler(),  
		  处理cluster操作

			- 其中cluster_create方法

		- conductor_listener.Handler(),

		- ca_conductor.Handler(),

		- federation_conductor.Handler()

	- 3.rpc服务对象创建  
	  server = rpc_service.Service.create(CONF.conductor.topic,  
	     conductor_id, endpoints, binary='magnum-conductor')  
	  其中topic：magnum-conductor

		- 创建为mangum/common/rpc_service.py中的create方法

		- 分发对象(初始化中self._server)  
		  dispatcher = rpc_dispatcher.RPCDispathcher(endpoints, serializer, access_policy)

			- RPCDsipatcher初始化了endpoints，加载了方法

		- 返回对象为  
		  service_obj = cls(topic, server, handlers, binary)  
		  该对象是rpc_service.py中Service类，而该类又继承了oslo_service/service.py中的Service类，该类实现了运行在机器上的二进制的服务

			- rpc_service.py中Service类初始化了self._server对象是messaging.get_rpc_server(xxxxxx)

	- 4.启动参数加载

	- 5.创建周期任务

	- 6.启动服务  
	  server.start()

		- 调用的magnum/common/rpc_service.py的Service类的start方法  
		  self._server.start()  
		  此处self._server对象是messaging.get_rpc_server(xxxxxx)  
		  而get_rpc_server返回的RPCServer类对象，代码位置oslo_messaging/rpc/server.py  
		  查看该类的start方法，父类MessageHandlingServer类的start方法

			- 该方法拉取incoming messages然后分配给分发器  
			  代码位置：oslo_messaging/server.py的MessageHandlingServer

			- 1.选取执行类型

			- 2.定义启动的池大小

			- 3.创建监听服务  
			  self.listener = self._create_listener()

				- 该类没有实现，查看子类oslo_messaging/server.py  
				  调用子类RPCserver的_create_listener()  
				  返回self._transport._listen(xxxx)

					- self._tranport根据上下文找到是oslo_messaging/transport.py中Transport类，因此调用该类的_listen方法

					- self._driver.listen(xxxx)

						- self._driver是impl_rabbit.py中的RabbitDriver类，继承AMQPDriverBase类(oslo_messaging/_drivers/amqpdriver.py)

							- 1.建立连接  
							  conn = self._get_connection(rpc_common.PURPOSE_LISTEN)  
							  listener = RpcAMQPListener(self, conn)

								- oslo_messaging/_drivers/ampqdriver.py中AMQPDriverBase的_get_connection方法  
								  返回rpc_common.ConnectionContext(self._connection_pool, purpose=purpose)

									- 由于AMQPDriverBase是RabbitDrvier的父类，所以  
									  onnectionContext继承oslo_messaging/_drivers/impl_rabbit.py的Connection类

									- self._connection_pool对象

										- 是impl_rabbit.py里Connection的对象池

							- 2.通过连接声明消费者

								- 队列严格和topic相同的  
								  conn.declare_topic_consumer(exchange_name=self._get_exchange(target),  
								                                   topic=target.topic, callback=listener)

									- 根据上一步connection分析，知道conn.declare_topic_consumer实际调用的是impl_rabbit.py中Connection的declare_topic_consumer方法

										- 可以看到消费的队列，exchange，等rpc信息，看到消费者是从magnum-conductor取的消息

										- def declare_topic_consumer(self, exchange_name, topic, callback=None,  
										                             queue_name=None):  
										      """Create a 'topic' consumer."""  
										      consumer = Consumer(exchange_name=exchange_name,  
										                          queue_name=queue_name or topic,  
										                          routing_key=topic,  
										                          type='topic',  
										                          durable=self.amqp_durable_queues,  
										                          exchange_auto_delete=self.amqp_auto_delete,  
										                          queue_auto_delete=self.amqp_auto_delete,  
										                          callback=callback,  
										                          rabbit_ha_queues=self.rabbit_ha_queues)

											- 声明了队列

										-     self.declare_consumer(consumer)

											- def declare_consumer(self, consumer):  
											      “””创建消费者并加入消费者列表  
											      """  
											      def _connect_error(exc):  
											          xxxxx      
											      def _declare_consumer():  
											          consumer.declare(self)  
											             self._new_tags.add(tag)  
											          self._consumers[consumer] = tag  
											          return consumer  
											    
											      with self._connection_lock:  
											          return self.ensure(_declare_consumer,  
											                             error_callback=_connect_error)

								- 队列和topic.server相同的  
								  conn.declare_topic_consumer(exchange_name=self._get_exchange(target),  
								                  topic='%s.%s' % (target.topic, target.server), callback=listener)

								- 交换机fanout类型的队列  
								  conn.declare_fanout_consumer(target.topic, listener)

							- 3.返回  
							  base.PollStyleListenerAdapter(listener, batch_size, batch_timeout)

			- 4.启动监听服务  
			  self.listener.start(self._on_incoming)

	- 7.等待服务接受任务/监听服务

- conductor创建cluster流程

	- cluster_conductor.Handler(),  
	  处理cluster操作

		- 代码位置：/usr/lib/python2.7/site-packages/magnum/conductor/handlers/cluster_conductor.py(48)cluster_create()

		- 1.生成osc对象(openstack client)

		- 2.数据库变更cluster状态

		- 3.创建cluster认证、证书等相关资源

		- 4.发送notify通知

			- conductor_utils.notify_about_cluster_operation(  
			  context, taxonomy.ACTION_CREATE, taxonomy.OUTCOME_PENDING)

				- 待分析

		- 5.获取集群驱动driver

			- magnum.drivers.k8s_fedora_atomic_v1.driver.Driver object

		- 6.调用driver创建cluster

			- cluster_driver.create_cluster  
			  (context, cluster, create_timeout)

				- k8s_fedora_atomic_v1.driver.Driver继承driver.HeatDriver  
				  代码位置：/usr/lib/python2.7/site-packages/magnum/drivers/heat/driver.py(98)create_cluster()

					- 创建集群self._create_stack

						- 1.获取模板数据

						- 2.获取环境变量等数据

						- 3.更新模板数据

						- 4.生成stack相关信息

						- 5.创建stack  
						  created_stack = osc.heat().stacks.create(**fields)

							- osc: magnum.common.clients.OpenStackClients  
							  heatclient/v1/client.py  
							  osc.heat():  <heatclient.v1.client.Client  
							  osc.heat().stacks:   stacks.StackManager(self.http_client)  
							  osc.heat().stack.create:   heatclient/v1/stacks.py中StackManager中的create

								- def create(self, **kwargs):  
								      """Create a stack."""  
								      headers = self.client.credentials_headers()  
								      resp = self.client.post('/stacks', data=kwargs, headers=headers)  
								      body = utils.get_response_body(resp)  
								      return body    

							- 在magnum中调用heatclient ，向heatapi发送请求，  
							  请求连接：http://controller:8004/v1/b5a1eb4ee8374fa1aa88cd4b59afda98/stacks

		- 7.发送集群创建通知

			- conductor_utils.notify_about_cluster_operation(  
			  context, taxonomy.ACTION_CREATE, taxonomy.OUTCOME_PENDING)

				- 待分析

### conductor发送到heatpi

### heat处理流程

## fedora-atomic脚本对应关系 

### part-001

- atomic-install-openstack-ca.sh

### part-002

### part-003

### part-004

- start-container-agent.sh

### part-005

- write-kube-os-config.sh

### part-006

- make-cert.sh

### part-007

- configure-docker-storage.sh

- configure_docker_storage_driver_aotmic.sh

### part-008

- config-docker-registry.sh

### part-009

- configure-kubernetes-minion.sh

### part-010

- add-proxy.sh

### part-011

- enable-services-minion.sh

### part-012

- enable-docker-registry.sh

### part-013

- wc-notify-master.sh

### part-014

### part-015

### part-016

