# aodh 流程分析

## 依赖库

依赖库 需要看下 **cotyledon stevedore  oslo_messaging**

## Aodh介绍

aodh是从ceilometer拆分出来的告警组件，现在主要包括:
evaluator 服务，notifier服务，listener服务。
evaluator 周期性的检查除了event类型之外的其他告警条件是否满足，如果校验有告警产生，则与notifier服务通信，进行告警通知
notifier 服务接收来自evaluator服务的通信，将触发的告警以日志，http请求等形式进行告警分发
listener 根据消息总线上面的 Event事件消息，检查相应的event类型的告警是否满足alarm的告警条件

```python
# aodh.cmd.alarm
def notifier():
    conf = service.prepare_service()
    sm = cotyledon.ServiceManager()
    sm.add(notifier_svc.AlarmNotifierService,
           workers=conf.notifier.workers, args=(conf,))
    sm.run()


def evaluator():
    conf = service.prepare_service()
    sm = cotyledon.ServiceManager()
    sm.add(evaluator_svc.AlarmEvaluationService,
           workers=conf.evaluator.workers, args=(conf,))
    sm.run()


def listener():
    conf = service.prepare_service()
    sm = cotyledon.ServiceManager()
    sm.add(event_svc.EventAlarmEvaluationService,
           workers=conf.listener.workers, args=(conf,))
    sm.run()

```



##  Aodh notifier 服务

```python
def notifier():
    conf = service.prepare_service()
    sm = cotyledon.ServiceManager()
    sm.add(notifier_svc.AlarmNotifierService,# 主服务 
           workers=conf.notifier.workers, args=(conf,))
    sm.run()
```

notifier 主服务 AlarmNotifierService

```python
class AlarmNotifierService(cotyledon.Service):
    NOTIFIER_EXTENSIONS_NAMESPACE = "aodh.notifier"
    # 命名空间



    def __init__(self, worker_id, conf):
        super(AlarmNotifierService, self).__init__(worker_id)
        self.conf = conf
        transport = messaging.get_transport(self.conf)
        
        
        self.notifiers = extension.ExtensionManager(
            self.NOTIFIER_EXTENSIONS_NAMESPACE,
            invoke_on_load=True,
            invoke_args=(self.conf,))
           # 根据 NOTIFIER_EXTENSIONS_NAMESPACE 查找对应 setup.cfg 插件 
          """
          #
            aodh.notifier =
            log = aodh.notifier.log:LogAlarmNotifier
            test = aodh.notifier.test:TestAlarmNotifier
            http = aodh.notifier.rest:RestAlarmNotifier
            https = aodh.notifier.rest:RestAlarmNotifier
            trust+http = aodh.notifier.trust:TrustRestAlarmNotifier
            trust+https = aodh.notifier.trust:TrustRestAlarmNotifier
            zaqar = aodh.notifier.zaqar:ZaqarAlarmNotifier
            trust+zaqar = aodh.notifier.zaqar:TrustZaqarAlarmNotifier
					"""
        target = oslo_messaging.Target(topic=self.conf.notifier_topic)
        self.listener = messaging.get_batch_notification_listener(
            transport, [target], [AlarmEndpoint(self.notifiers)], False,
            self.conf.notifier.batch_size, self.conf.notifier.batch_timeout)
        self.listener.start()
```

把 self.notifiers 传入 AlarmEndpoint 运行去消费信息 

主要看AlarmEndpoint 

```python
#aodh.notifier.AlarmEndpoint._process_alarm
		@staticmethod
	def _process_alarm(notifiers, data):
	    """Notify that alarm has been triggered.
	
	    :param notifiers: list of possible notifiers
	    :param data: (dict): alarm data
	    """
	
	    actions = data.get('actions')
	    if not actions:
	        LOG.error("Unable to notify for an alarm with no action")
	        return
	
	    for action in actions:
	        AlarmEndpoint._handle_action(notifiers, action,
	                                     data.get('alarm_id'),
	                                     data.get('alarm_name'),
	                                     data.get('severity'),
	                                     data.get('previous'),
	                                     data.get('current'),
	                                     data.get('reason'),
	                                     data.get('reason_data'))
```

这里就是alarm通知进程，调用用了_ handle_ action下面來分析这个方法的主要代码：

```python
notifier = notifiers[action.scheme].obj # 获取 notifier方式


"""
# <aodh.notifier.rest.RestAlarmNotifier object at 0x7fcdf413c190>
""" 
```
notifier 调用 notify

```python
try:
        LOG.debug("Notifying alarm %(id)s with action %(act)s",
                  {'id': alarm_id, 'act': action})
        notifier.notify(action, alarm_id, alarm_name, severity,
                        previous, current, reason, reason_data)
```

具体起作用的类 是  LogAlarmNotifier RestAlarmNotifier

```python
# RestAlarmNotifier 分析
class RestAlarmNotifier(notifier.AlarmNotifier):
    """Rest alarm notifier."""

    def __init__(self, conf):
        super(RestAlarmNotifier, self).__init__(conf)
        self.conf = conf

    def notify(self, action, alarm_id, alarm_name, severity, previous,
               current, reason, reason_data, headers=None):
        headers = headers or {}
				
				······

        max_retries = self.conf.rest_notifier_max_retries
        session = requests.Session()
        session.mount(action.geturl(),
                      requests.adapters.HTTPAdapter(max_retries=max_retries))
        resp = session.post(action.geturl(), **kwargs)
        # 发送到 alarm 项目的8006端口
        LOG.info('Notifying alarm <%(id)s> gets response: %(status_code)s '
                 '%(reason)s.', {'id': alarm_id,
                                 'status_code': resp.status_code,
                                 'reason': resp.reason})


```

## Aodh evaluator 服务

```python
def evaluator():
    conf = service.prepare_service()
    sm = cotyledon.ServiceManager()
    sm.add(evaluator_svc.AlarmEvaluationService,
           workers=conf.evaluator.workers, args=(conf,))
    sm.run()
```

通过上面代码 进入 AlarmEvaluationService

```python
# aodh.evaluator.AlarmEvaluationService
class AlarmEvaluationService(cotyledon.Service):

    PARTITIONING_GROUP_NAME = "alarm_evaluator"
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
        # 加载插件同上 EVALUATOR_EXTENSIONS_NAMESPACE 
        """
            gnocchi_resources_threshold = aodh.evaluator.gnocchi:GnocchiResourceThresholdEvaluator
            gnocchi_aggregation_by_metrics_threshold = aodh.evaluator.gnocchi:GnocchiAggregationMetricsThresholdEvaluator
            gnocchi_aggregation_by_resources_threshold = aodh.evaluator.gnocchi:GnocchiAggregationResourcesThresholdEvaluator
            composite = aodh.evaluator.composite:CompositeEvaluator
        """
        self.storage_conn = storage.get_connection_from_config(self.conf)

        
        # tooz 模块相关
        self.partition_coordinator = coordination.PartitionCoordinator(
            self.conf)
        self.partition_coordinator.start()
        self.partition_coordinator.join_group(self.PARTITIONING_GROUP_NAME)

        # allow time for coordination if necessary
        delay_start = self.partition_coordinator.is_active()

        if self.evaluators:
            # 周期性 执行  evaluate_alarms -->_evaluate_assigned_alarms
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
```

evaluate_alarms -->_evaluate_assigned_alarms

```python
    def _evaluate_assigned_alarms(self):
        try:
            
            alarms = self._assigned_alarms()
            # 除去 event 类型的告警 
            LOG.info('initiating evaluation cycle on %d alarms',
                     len(alarms))
            for alarm in alarms:
                self._evaluate_alarm(alarm)
        except Exception:
            LOG.exception('alarm evaluation cycle failed')
```

--> _evaluate_alarm

```python
    def _evaluate_alarm(self, alarm):
        """Evaluate the alarms assigned to this evaluator."""
        if alarm.type not in self.evaluators:
            LOG.debug('skipping alarm %s: type unsupported', alarm.alarm_id)
            return

        LOG.debug('evaluating alarm %s', alarm.alarm_id)
        try:
            self.evaluators[alarm.type].obj.evaluate(alarm)
            """
          2021-08-24 15:38:40.796 17932 INFO aodh.evaluator [-] self.evaluators[alarm.type].obj.evaluate:<bound method GnocchiAggregationMetricsThresholdEvaluator.evaluate of <aodh.evaluator.gnocchi.GnocchiAggregationMetricsThresholdEvaluator object at 0x7f32170b5fd0>>
          # aodh.evaluator.threshold.ThresholdEvaluator.evaluate 执行对应的方法
          也就是上面加载的插件的对应的方法
          2021-08-24 15:38:40.796 17932 INFO aodh.evaluator [-] self.evaluators[alarm.type].obj:<aodh.evaluator.gnocchi.GnocchiAggregationMetricsThresholdEvaluator object at 0x7f32170b5fd0>
            """
        except Exception:
            LOG.exception('Failed to evaluate alarm %s', alarm.alarm_id)
```

拿 `aodh.evaluator.threshold.ThresholdEvaluator.evaluate`  为例子

```python
    def evaluate(self, alarm):
        if not self.within_time_constraint(alarm):
            LOG.debug('Attempted to evaluate alarm %s, but it is not '
                      'within its time constraint.', alarm.alarm_id)
            return

        try:
            evaluation = self.evaluate_rule(alarm.rule)
            # alarm 对应的数据库里面的对象
            # alarm.rule 对应的数据：{"evaluation_periods": 1, "metrics": ["13a30b01-c52d-464a-aaeb-1bbabe9cb8e1"], "aggregation_method": "rate:mean", "granularity": 60, "threshold": 42000000000.0, "comparison_operator": "gt"}
        except InsufficientDataError as e:
            evaluation = (evaluator.UNKNOWN, None, e.statistics, 0,
                          e.reason)
        self._transition_alarm(alarm, *evaluation)

```

---> evaluate_rule

```python
    def evaluate_rule(self, alarm_rule):
        """Evaluate alarm rule.

        :returns: state, trending state and statistics.
        """
        start, end = self._bound_duration(alarm_rule)
        statistics = self._statistics(alarm_rule, start, end)
        statistics = self._sanitize(alarm_rule, statistics)
        sufficient = len(statistics) >= alarm_rule['evaluation_periods']
        if not sufficient:
            raise InsufficientDataError(
                '%d datapoints are unknown' % alarm_rule['evaluation_periods'],
                statistics)

        def _compare(value):
            op = COMPARATORS[alarm_rule['comparison_operator']]
            limit = alarm_rule['threshold']
            LOG.debug('comparing value %(value)s against threshold'
                      ' %(limit)s', {'value': value, 'limit': limit})
            return op(value, limit)

        compared = list(six.moves.map(_compare, statistics))
        distilled = all(compared)
        unequivocal = distilled or not any(compared)
        number_outside = len([c for c in compared if c])

        if unequivocal:
            state = evaluator.ALARM if distilled else evaluator.OK
            return state, None, statistics, number_outside, None
        else:
            trending_state = evaluator.ALARM if compared[-1] else evaluator.OK
            return None, trending_state, statistics, number_outside, None
```



--> self._transition_alarm(alarm, *evaluation) --> _refresh



```python
    def _refresh(self, alarm, state, reason, reason_data, always_record=False):
        """Refresh alarm state."""
        try:
            previous = alarm.state
            alarm.state = state
            alarm.state_reason = reason
            if previous != state or always_record:
                LOG.info('alarm %(id)s transitioning to %(state)s because '
                         '%(reason)s', {'id': alarm.alarm_id,
                                        'state': state,
                                        'reason': reason})
                try:
                    self._storage_conn.update_alarm(alarm)
                    # 更新状态
                except storage.AlarmNotFound:
                    LOG.warning("Skip updating this alarm's state, the"
                                "alarm: %s has been deleted",
                                alarm.alarm_id)
                else:
                    self._record_change(alarm, reason)
                self.notifier.notify(alarm, previous, reason, reason_data)
                # 通知 请看 notify 流程
            elif alarm.repeat_actions:
                self.notifier.notify(alarm, previous, reason, reason_data)
        except Exception:
            # retry will occur naturally on the next evaluation
            # cycle (unless alarm state reverts in the meantime)
            LOG.exception('alarm state update failed')

```



## Aodh  listener 服务



```python
def listener():
    conf = service.prepare_service()
    sm = cotyledon.ServiceManager()
    sm.add(event_svc.EventAlarmEvaluationService,
           workers=conf.listener.workers, args=(conf,))
    sm.run()

```

-->EventAlarmEvaluationService

```python
class EventAlarmEvaluationService(cotyledon.Service):
    def __init__(self, worker_id, conf):
        super(EventAlarmEvaluationService, self).__init__(worker_id)
        self.conf = conf
        self.storage_conn = storage.get_connection_from_config(self.conf)
        # 主要针对的 event 告警
        self.evaluator = event.EventAlarmEvaluator(self.conf)
        
        self.listener = messaging.get_batch_notification_listener(
            messaging.get_transport(self.conf),
            [oslo_messaging.Target(
                topic=self.conf.listener.event_alarm_topic)],
            [EventAlarmEndpoint(self.evaluator)], False,
            self.conf.listener.batch_size,
            self.conf.listener.batch_timeout)
        # EventAlarmEndpoint 最终会执行EventAlarmEvaluator 对应的 evaluate_events 方法
        self.listener.start()
```

--> EventAlarmEvaluator 代码

```python

class EventAlarmEvaluator(evaluator.Evaluator):

    def __init__(self, conf):
        super(EventAlarmEvaluator, self).__init__(conf)
        self.caches = {}

    def evaluate_events(self, events):
        """Evaluate the events by referring related alarms."""

        if not isinstance(events, list):
            events = [events]

        LOG.debug('Starting event alarm evaluation: #events = %d',
                  len(events))
        for e in events:
            LOG.debug('Evaluating event: event = %s', e)
            try:
                event = Event(e)
            except InvalidEvent:
                LOG.warning('Event <%s> is invalid, aborting evaluation '
                            'for it.', e)
                continue

            for id, alarm in six.iteritems(
                    self._get_project_alarms(event.project)):
                try:
                    self._evaluate_alarm(alarm, event)
                    # 通过参考接收到的事件来评估警报
                except Exception:
                    LOG.exception('Failed to evaluate alarm (id=%(a)s) '
                                  'triggered by event = %(e)s.',
                                  {'a': id, 'e': e})

        LOG.debug('Finished event alarm evaluation.')
```

self._evaluate_alarm --> _fire_alarm

```python
    def _fire_alarm(self, alarm, event):
        """Update alarm state and fire alarm via alarm notifier."""

        state = evaluator.ALARM
        reason = (('Event <id=%(id)s,event_type=%(event_type)s> hits the '
                   'query <query=%(alarm_query)s>.') %
                  {'id': event.id,
                   'event_type': event.get_value('event_type'),
                   'alarm_query': json.dumps(alarm.obj.rule['query'],
                                             sort_keys=True)})
        reason_data = {'type': 'event', 'event': event.obj}
        always_record = alarm.obj.repeat_actions
        self._refresh(alarm.obj, state, reason, reason_data, always_record)
```

最终到 self._refresh： 也就是回到了notifer通知服务

```python
  #  aodh.evaluator.Evaluator._refresh
   def _refresh(self, alarm, state, reason, reason_data, always_record=False):
        """Refresh alarm state."""
        try:
            previous = alarm.state
            alarm.state = state
            alarm.state_reason = reason
            if previous != state or always_record:
                LOG.info('alarm %(id)s transitioning to %(state)s because '
                         '%(reason)s', {'id': alarm.alarm_id,
                                        'state': state,
                                        'reason': reason})
                try:
                    self._storage_conn.update_alarm(alarm)
                except storage.AlarmNotFound:
                    LOG.warning("Skip updating this alarm's state, the"
                                "alarm: %s has been deleted",
                                alarm.alarm_id)
                else:
                    self._record_change(alarm, reason)
                self.notifier.notify(alarm, previous, reason, reason_data)
            elif alarm.repeat_actions:
                self.notifier.notify(alarm, previous, reason, reason_data)
        except Exception:
            # retry will occur naturally on the next evaluation
            # cycle (unless alarm state reverts in the meantime)
            LOG.exception('alarm state update failed')
```















