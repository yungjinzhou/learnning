# Aodh源码分析


## aodh-api

### 启动

- 与其他组件一样，统一使用wsgi框架启动app以及服务，最终会调用到aodh\api\controllers\v2\root.py：

- 首先根据启动文件/usr/bin/aodh-api，调用了application = build_wsgi_app()

	- 找到aodh/api/app.py  
	  最终调用deploy.loadapp(xxxx)

		- paste源码中，根据调用栈看到调用了paste/deploy/loadwsgi.py中的loadapp(uri, name=None, **kw):

			- app启动时有配置invoke  
			  context.protocol == 'paste.app_factory'

				- 对应到aodh/api/api-paste.ini中，找到root  
				  [app:aodhv2]  
				  paste.app_factory = aodh.api.app:app_factory  
				  root = aodh.api.controllers.v2.root.V2Controller

### 创建告警

- 根据api启动方式，找到v2controller

	- /aodh/api/controllers/v2/root.py  
	  创建告警/v2/alarms，根据pecan路由，定位到alarms.AlarmsController()

		- /aodh/api/controllers/v2/alarms.py  
		  Def post方法创建告警

			- 连接存储后端(数据库)conn  
			  conn = pecan.request.storage  
			  示例：  
			  <aodh.storage.impl_sqlalchemy.Connection object at 0x7f9699eb5d50>

			- 校验参数及生成必要的参数

			- 检查配额

			- ALARMS_RULES[data.type].plugin.create_hook(data)  
			  示例  
			  ALARMS_RULES[data.type].plugin：<class 'aodh.api.controllers.v2.alarm_rules.gnocchi.AggregationMetricsByIdLookupRule'>)  
			  data.type：'gnocchi_aggregation_by_metrics_threshold'  
			  data：Alarm类的实例

			- 更新数据库

## listener/evaluator/notifier启动方式

### 借助cotyledon进程管理包启动各自的进程

### conf = service.prepare_service()  
  sm = cotyledon.ServiceManager()  
  sm.add(xxxxxx)  
  sm.run()

## aodh-listener

### aodh-listener 定义了监控event的告警，数据是从直接监听notification中获取，当监听的event触发告警时发送到rpc或者notification

### 通过cotyledon启动listener服务  
  sm.add(event_svc.EventAlarmEvaluationService, workers=conf.listener.workers, args=(conf,))

- 代码位置：  
  aodh/event.py

- 执行__init__初始化函数

	- 加载配置文件

	- 获取存储后端连接

	- 指定事件类型的evaluator  
	  self.evaluator = event.EventAlarmEvaluator(self.conf)  
	  <aodh.evaluator.event.EventAlarmEvaluator object at 0x7fa9cace57d0>

		- def evaluate_events

			- get_project_alarms(event.project)

			- evaluate_alarm(alarm, event)  
			  根据收到的事件评估告警

	- 监听器对象  
	  <oslo_messaging.notify.listener.BatchNotificationServer object at 0x7fa9c9797f90>

		- get_batch_notification_listener()  
		  Code position: aodh/messaging.py

			- 调用oslo.messaging/notify/listener.py的get_batch_notification_listener()

				- 初始化dispatcher  
				  (找到对应的处理方法sample)

					- oslo.messaging/notify/dispatcher.py

				- BatchNotificationServer

					- 把数据交给dispacher处理

		- 初始化oslo_messaging

		- topic：alarm.all

		- EventAlarmEndpoint

			- 初始化evaluator

			- def sample(self, notification)  
			  根据notification的数据进行evaluator

		- 监听器批量数据大小

		- 配置对象超时时间

	- 启动监听器

## aodh-evaluator

### aodh-evaluator 根据告警类型从ceilometer接口中或者gnochhi中获取，当数据触发告警规则时将告警发送到rpc或者notification

### 通过cotyledon启动evaluator服务  
  sm.add(evaluator_svc.AlarmEvaluationService, workers=conf.evaluator.workers, args=(conf,))

- 进入AlarmEvaluationService类中  
  代码位置/aodh/aodh/evaluator/__init__.py  
  AlarmEvaluationService的def __init__(self, worker_id, conf)

	- 主函数

		- PARTITIONING_GROUP_NAME = "alarm_evaluator"  
		  EVALUATOR_EXTENSIONS_NAMESPACE = "aodh.evaluator"  
		    
		  def __init__(self, worker_id, conf):  
		      super(AlarmEvaluationService, self).__init__(worker_id)  
		      self.conf = conf  
		    
		      ef = lambda: futures.ThreadPoolExecutor(max_workers=10)  
		      self.periodic = periodics.PeriodicWorker.create(  
		          [], executor_factory=ef)  
		    
		      self.evaluators = extension.ExtensionManager(  
		          namespace=self.EVALUATOR_EXTENSIONS_NAMESPACE,  
		          invoke_on_load=True,  
		          invoke_args=(self.conf,)  
		      )  
		      self.storage_conn = storage.get_connection_from_config(self.conf)  
		    
		      self.partition_coordinator = coordination.PartitionCoordinator(  
		          self.conf)  
		      self.partition_coordinator.start()  
		      self.partition_coordinator.join_group(self.PARTITIONING_GROUP_NAME)  
		    
		      # allow time for coordination if necessary  
		      delay_start = self.partition_coordinator.is_active()  
		    
		      if self.evaluators:  
		          @periodics.periodic(spacing=self.conf.evaluation_interval,  
		                              run_immediately=not delay_start)  
		          def evaluate_alarms():  
		              self._evaluate_assigned_alarms()  
		    
		          self.periodic.add(evaluate_alarms)  
		    
		      if self.partition_coordinator.is_active():  
		          heartbeat_interval = min(self.conf.coordination.heartbeat,  
		                                   self.conf.evaluation_interval / 4)  
		    
		          @periodics.periodic(spacing=heartbeat_interval,  
		                              run_immediately=True)  
		          def heartbeat():  
		              self.partition_coordinator.heartbeat()  
		    
		          self.periodic.add(heartbeat)  
		    
		      t = threading.Thread(target=self.periodic.start)  
		      t.daemon = True  
		      t.start()

	- 构建线程池及周期任务 
	  ef = lambda: futures.ThreadPoolExecutor(max_workers=10)  
	  self.periodic = periodics.PeriodicWorker.create( [],executor_factory=ef)

	- self.evaluators  
	  加载evaluators的扩展

		- 扩展位置：    
		  </usr/lib/python2.7/site-packages/aodh-8.0.0-py2.7.egg-info/entry_points.txt>

		- evaluators对象
		  <stevedore.extension.ExtensionManager object at 0x7f953ecbcad0>)

		- 扩展对象
		  <aodh.evaluator.gnocchi.GnocchiAggregationMetricsThresholdEvaluator object at 0x7fcf5a588e90>, 'entry_point': EntryPoint.parse('gnocchi_aggregation_by_metrics_threshold = aodh.evaluator.gnocchi:GnocchiAggregationMetricsThresholdEvaluator'), 'name': 'gnocchi_aggregation_by_metrics_threshold', 'plugin': <class 

	- 连接存储对象  
	  storage_conn

		- < aodh.storage.impl_sqlalchemy.Connection object at 0x7f953d53c090

	- 任务管理协调服务

		- self.partition_coordinator = coordination.PartitionCoordinator(self.conf)  
		  self.partition_coordinator.start()  
		  self.partition_coordinator.join_group(self.PARTITIONING_GROUP_NAME)  
		  delay_start = self.partition_coordinator.is_active()

	- 有插件，添加进周期任务中

		- 调用evaluate_alarms、_evaluate_assigned_alarms

			- 过滤alarms

				- 连接数据库

				- 挑选对应的告警数据

			- 根据告警对象，处理告警  
			  self.evaluators[alarm.type].obj.evaluate(alarm)

				- 代码位置  
				  aodh/aodh/evaluator/threshold.py    def evaluate()

				- evaluate_rule  
				  触发告警规则时处理数据

					- 格式化alarm时间

					- statistics调用gnocchi的类获取数据

						- self._statistics  
						  Aodh/evaluator/gnocchi.py 下的GnocchiResourceThresholdEvaluator类下的方法

					- 格式化statistics

						- self._sanitize  
						  Aodh/evaluator/gnocchi.py 下的GnocchiBase下的方法

					- 对比

					- 处理告警数据、状态

				- 更新状态  
				  transition_alarm

					- 根据数据更新状态

					- 刷新refresh

						- 更新数据到数据库

						- 记录改变，发送notification：alarm.state_transition队列  
						  publisher_id:  aodh.evaluator

						- 发送通知notify  
						  driver: messagingv2  
						  publisher_id:  alarming.evaluator  
						  alarm.update  
						  aodh/queue.py

							- self.notifier

								- {  
								  '_serializer': <oslo_messaging.serializer.NoOpSerializer object at 0x7fe8919f0190>,   
								  '_driver_mgr': <stevedore.named.NamedExtensionManager object at 0x7fe8919f01d0>,   
								  'retry': -1,   
								  '_driver_names': ['messagingv2'],   
								  '_topics': ['alarming'],   
								  'publisher_id': 'alarming.evaluator',   
								  'transport': <oslo_messaging.transport.NotificationTransport object at 0x7fe892c6df90>  
								  }

	- 是否对该服务进行心跳检测以及配置

	- 启动周期性任务，守护进程  
	  任务:心跳检测、评估

## aodh-notifier

### aodh-notifier 从rpc或者notification中获取告警并进行发送到外部系统例如http、https、Log等

### sm.add(notifier_svc.AlarmNotifierService, workers=conf.notifier.workers, args=(conf,))

- def __init__(self, worker_id, conf):

	- super(AlarmNotifierService, self).__init__(worker_id)

	- 初始化配置

	- 建立transport

		- topic： alarming

	- self.notifiers = extension.ExtensionManager

		- aodh.notifier

		- 扩展插件/usr/lib/python2.7/site-pacakages/aodh-8.0.0-py2.7.egg-info/entry_points.txt  
		  [aodh.notifier]  
		  http = aodh.notifier.rest:RestAlarmNotifier  
		  https = aodh.notifier.rest:RestAlarmNotifier  
		  log = aodh.notifier.log:LogAlarmNotifier  
		  test = aodh.notifier.test:TestAlarmNotifier  
		  trust+http = aodh.notifier.trust:TrustRestAlarmNotifier  
		  trust+https = aodh.notifier.trust:TrustRestAlarmNotifier  
		  trust+zaqar = aodh.notifier.zaqar:TrustZaqarAlarmNotifier  
		  zaqar = aodh.notifier.zaqar:ZaqarAlarmNotifier

	- 监听队列数据

		- [AlarmEndpoint(self.notifiers)],

			- 根据notifiers处理监听到的数据

