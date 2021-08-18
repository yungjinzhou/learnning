ceilometer-central服务发送到rpc

rpc到agent-notification服务及处理流程



ceilometer-central:

```
    def _send_notification(self, samples):
        self.manager.notifier.sample(
            {},
            'telemetry.polling',
            {'samples': samples}
        )

  # polling/manager.py
  
  '''
  samples data:
  {'counter_name': 'custom.hardware.cpu.idle.percentage', 'resource_id': '30.90.2.27', 'timestamp': '2021-07-30T02:37:21.211598', 'counter_volume': 80, 'user_id': None, 'message_signature': 'e4c78e67202a6b56041e1e5f4b9a2ea3930fbba5c4003620bd6d23786fea2a25', 'resource_metadata': {'resource_url': 'snmp://30.90.2.27'}, 'source': 'hardware', 'counter_unit': '%', 'project_id': None, 'message_id': '109e6394-f0df-11eb-9499-48dc2d0162df', 'monotonic_time': None, 'counter_type': 'gauge'}

  '''
```





```
oslo_messaging

    def sample(self, ctxt, event_type, payload):
        """Send a notification at sample level.

        Sample notifications are for high-frequency events
        that typically contain small payloads. eg: "CPU = 70%"

        Not all drivers support the sample level
        (log, for example) so these could be dropped.

        :param ctxt: a request context dict
        :type ctxt: dict
        :param event_type: describes the event, for example
                           'compute.create_instance'
        :type event_type: str
        :param payload: the notification payload
        :type payload: dict
        :raises: MessageDeliveryFailure
        """
        self._notify(ctxt, event_type, payload, 'SAMPLE')

# oslo_messaging/notify/notifier.py
'''
payload data :
{'samples': [{'counter_name': 'custom.hardware.cpu.idle.percentage', 'resource_id': '30.90.2.27', 'timestamp': '2021-07-30T03:24:07.018479', 'counter_volume': 87, 'user_id': None, 'message_signature': 'f5f3f5a81f4b14b51067d73f28d5e00322a33b2a1ee66cfef9b21d13e97234dd', 'resource_metadata': {'resource_url': 'snmp://30.90.2.27'}, 'source': 'hardware', 'counter_unit': '%', 'project_id': None, 'message_id': '99028a20-f0e5-11eb-b2a5-48dc2d0162df', 'monotonic_time': None, 'counter_type': 'gauge'}]}

'''





    def _notify(self, ctxt, event_type, payload, priority, publisher_id=None,
                retry=None):
        payload = self._serializer.serialize_entity(ctxt, payload)
        ctxt = self._serializer.serialize_context(ctxt)

        msg = dict(message_id=six.text_type(uuid.uuid4()),
                   publisher_id=publisher_id or self.publisher_id,
                   event_type=event_type,
                   priority=priority,
                   payload=payload,
                   timestamp=six.text_type(timeutils.utcnow()))

        def do_notify(ext):
            try:
                ext.obj.notify(ctxt, msg, priority, retry or self.retry)
            except Exception as e:
                _LOG.exception(_LE("Problem '%(e)s' attempting to send to "
                                   "notification system. Payload=%(payload)s"),
                               dict(e=e, payload=payload))

        if self._driver_mgr.extensions:
            self._driver_mgr.map(do_notify)
```





```
# oslo_messaging/notify/messaging.py

    def notify(self, ctxt, message, priority, retry):
        priority = priority.lower()
        for topic in self.topics:
            target = oslo_messaging.Target(topic='%s.%s' % (topic, priority))
            try:
                self.transport._send_notification(target, ctxt, message,
                                                  version=self.version,
                                                  retry=retry)
            except Exception:
                LOG.exception(_LE("Could not send notification to %(topic)s. "
                                  "Payload=%(message)s"),
                              dict(topic=topic, message=message))




# oslo_messaging/transport.py

    def _send_notification(self, target, ctxt, message, version, retry=None):
        if not target.topic:
            raise exceptions.InvalidTarget('A topic is required to send',
                                           target)
        self._driver.send_notification(target, ctxt, message, version,
                                       retry=retry)


# oslo_messaging/_drivers/amqpdriver.py

    def send_notification(self, target, ctxt, message, version, retry=None):
        return self._send(target, ctxt, message,
                          envelope=(version == 2.0), notify=True, retry=retry)
                          


    def _send(self, target, ctxt, message,
              wait_for_reply=None, timeout=None, call_monitor_timeout=None,
              envelope=True, notify=False, retry=None):

        msg = message

        if wait_for_reply:
            msg_id = uuid.uuid4().hex
            msg.update({'_msg_id': msg_id})
            msg.update({'_reply_q': self._get_reply_q()})
            msg.update({'_timeout': call_monitor_timeout})

        rpc_amqp._add_unique_id(msg)
        unique_id = msg[rpc_amqp.UNIQUE_ID]

        rpc_amqp.pack_context(msg, ctxt)

        if envelope:
            msg = rpc_common.serialize_msg(msg)

        if wait_for_reply:
            self._waiter.listen(msg_id)
            log_msg = "CALL msg_id: %s " % msg_id
        else:
            log_msg = "CAST unique_id: %s " % unique_id

        try:
            with self._get_connection(rpc_common.PURPOSE_SEND) as conn:
                if notify:
                    exchange = self._get_exchange(target)
                    log_msg += "NOTIFY exchange '%(exchange)s'" \
                               " topic '%(topic)s'" % {
                                   'exchange': exchange,
                                   'topic': target.topic}

                    LOG.debug(log_msg)
                    # exchange: ceilometer
                    # topic : notifications.sample
                    conn.notify_send(exchange, target.topic, msg, retry=retry)
                elif target.fanout:
                    log_msg += "FANOUT topic '%(topic)s'" % {
                        'topic': target.topic}
                    LOG.debug(log_msg)
                    conn.fanout_send(target.topic, msg, retry=retry)
                else:
                    topic = target.topic
                    exchange = self._get_exchange(target)
                    if target.server:
                        topic = '%s.%s' % (target.topic, target.server)
                    log_msg += "exchange '%(exchange)s'" \
                               " topic '%(topic)s'" % {
                                   'exchange': exchange,
                                   'topic': topic}
                    LOG.debug(log_msg)
                    conn.topic_send(exchange_name=exchange, topic=topic,
                                    msg=msg, timeout=timeout, retry=retry)

            if wait_for_reply:
                result = self._waiter.wait(msg_id, timeout,
                                           call_monitor_timeout)
                if isinstance(result, Exception):
                    raise result
                return result
        finally:
            if wait_for_reply:
                self._waiter.unlisten(msg_id)






# oslo_messagin/_drivers/impl_rabbit.py

# msg:   {'priority': 'SAMPLE', '_unique_id': 'b9f26de05261426f9dc7c77fbc0e50af', 'event_type': 'telemetry.polling', 'timestamp': u'2021-08-02 01:50:14.194376', 'publisher_id': 'ceilometer.polling', 'payload': {'samples': [{'counter_name': 'custom.hardware.cpu.idle.percentage', 'resource_id': '30.90.2.27', 'timestamp': '2021-08-02T01:50:14.193594', 'counter_volume': 91, 'user_id': None, 'message_signature': '7601c98348428f492d40c50cf5f931e068d4fd3257672420a20fd18558e5cdf5', 'resource_metadata': {'resource_url': 'snmp://30.90.2.27'}, 'source': 'hardware', 'counter_unit': '%', 'project_id': None, 'message_id': 'fad2ed26-f333-11eb-8fbb-48dc2d0162df', 'monotonic_time': None, 'counter_type': 'gauge'}]}, 'message_id': u'4f4bb1ec-91c7-4c2d-b158-d28094cfd284'}
#   exchange_name: ceilometer, === topic: notifications.sample=====


    def notify_send(self, exchange_name, topic, msg, retry=None, **kwargs):
        """Send a notify message on a topic."""
        exchange = kombu.entity.Exchange(
            name=exchange_name,
            type='topic',
            durable=self.amqp_durable_queues,
            auto_delete=self.amqp_auto_delete)

        self._ensure_publishing(self._publish_and_creates_default_queue,
                                exchange, msg, routing_key=topic, retry=retry)
```







ceilometer-notification:

```
# 启动 
#ceilometer/notification.py

    def run(self):
        # Delay startup so workers are jittered
        time.sleep(self.startup_delay)

        super(NotificationService, self).run()

        self.managers = [ext.obj for ext in named.NamedExtensionManager(
            namespace='ceilometer.notification.pipeline',
            names=self.conf.notification.pipelines, invoke_on_load=True,
            on_missing_entrypoints_callback=self._log_missing_pipeline,
            invoke_args=(self.conf,))]

        # FIXME(sileht): endpoint uses the notification_topics option
        # and it should not because this is an oslo_messaging option
        # not a ceilometer. Until we have something to get the
        # notification_topics in another way, we must create a transport
        # to ensure the option has been registered by oslo_messaging.
        messaging.get_notifier(messaging.get_transport(self.conf), '')

        endpoints = []
        for pipe_mgr in self.managers:
            endpoints.extend(pipe_mgr.get_main_endpoints())
        targets = self.get_targets()

        urls = self.conf.notification.messaging_urls or [None]
        #urls
        # ['rabbit://openstack:mima-xxxxxx@controller']
        for url in urls:
            transport = messaging.get_transport(self.conf, url)
            # NOTE(gordc): ignore batching as we want pull
            # to maintain sequencing as much as possible.
            # print(transport, targets, endpoints)
            """
            (<oslo_messaging.transport.NotificationTransport object at 0x7f3c5983d990>, [<Target exchange=ceilometer, topic=notifications>, <Target exchange=zaqar, topic=notifications>, <Target exchange=sahara, topic=notifications>, <Target exchange=trove, topic=notifications>, <Target exchange=aodh, topic=notifications>, <Target exchange=nova, topic=notifications>, <Target exchange=heat, topic=notifications>, <Target exchange=keystone, topic=notifications>, <Target exchange=dns, topic=notifications>, <Target exchange=magnum, topic=notifications>, <Target exchange=ironic, topic=notifications>, <Target exchange=cinder, topic=notifications>, <Target exchange=glance, topic=notifications>, <Target exchange=swift, topic=notifications>, <Target exchange=neutron, topic=notifications>], [<ceilometer.pipeline.event.EventEndpoint object at 0x7f3c595d9f90>, <ceilometer.middleware.HTTPRequest object at 0x7f3c592b2f50>, <ceilometer.ipmi.notifications.ironic.VoltageSensorNotification object at 0x7f3c592b21d0>, <ceilometer.ipmi.notifications.ironic.CurrentSensorNotification object at 0x7f3c592b2190>, <ceilometer.middleware.HTTPResponse object at 0x7f3c592b2110>, <ceilometer.ipmi.notifications.ironic.TemperatureSensorNotification object at 0x7f3c592b2c90>, <ceilometer.telemetry.notifications.TelemetryIpc object at 0x7f3c5983da50>, <ceilometer.meter.notifications.ProcessMeterNotifications object at 0x7f3c5983d450>, <ceilometer.ipmi.notifications.ironic.FanSensorNotification object at 0x7f3c5983d210>])
            
            """
            listener = messaging.get_batch_notification_listener(
                transport, targets, endpoints, allow_requeue=True)
            # listener
            # <oslo_messaging.notify.listener.BatchNotificationServer object at 0x7fb9dcd8ef10>
            listener.start(
                override_pool_size=self.conf.max_parallel_requests
            )
            self.listeners.append(listener)


# 获取队列，然后监听 listener.start()
#oslo_messaging/server.py

    @ordered(reset_after='stop')
    def start(self, override_pool_size=None):
        """Start handling incoming messages.

        This method causes the server to begin polling the transport for
        incoming messages and passing them to the dispatcher. Message
        processing will continue until the stop() method is called.

        The executor controls how the server integrates with the applications
        I/O handling strategy - it may choose to poll for messages in a new
        process, thread or co-operatively scheduled coroutine or simply by
        registering a callback with an event loop. Similarly, the executor may
        choose to dispatch messages in a new thread, coroutine or simply the
        current thread.
        """
        if self._started:
            LOG.warning(_LW('The server has already been started. Ignoring'
                            ' the redundant call to start().'))
            return

        self._started = True

        executor_opts = {}

        if self.executor_type in ("threading", "eventlet"):
            executor_opts["max_workers"] = (
                override_pool_size or self.conf.executor_thread_pool_size
            )
        self._work_executor = self._executor_cls(**executor_opts)

        try:
            self.listener = self._create_listener()
        except driver_base.TransportDriverError as ex:
            raise ServerListenError(self.target, ex)

        self.listener.start(self._on_incoming)



    def _on_incoming(self, incoming):
        """Handles on_incoming event

        :param incoming: incoming request.
        """
        # incoming: [<oslo_messaging._drivers.amqpdriver.NotificationAMQPIncomingMessage object at 0x7f6806f1bf50>]
        self._work_executor.submit(self._process_incoming, incoming)




# oslo_messaging/notify/listener.py

class BatchNotificationServer(NotificationServerBase):

    def _process_incoming(self, incoming):
        try:
            not_processed_messages = self.dispatcher.dispatch(incoming)
        except Exception:
            not_processed_messages = set(incoming)
            LOG.exception(_LE('Exception during messages handling.'))
        for m in incoming:
            try:
                if m in not_processed_messages and self._allow_requeue:
                    m.requeue()
                else:
                    m.acknowledge()
            except Exception:
                LOG.exception(_LE("Fail to ack/requeue message."))




# oslo_messagiong/notify/dispatcher.py

class BatchNotificationDispatcher(NotificationDispatcher):
    """A message dispatcher which understands Notification messages.

    A MessageHandlingServer is constructed by passing a callable dispatcher
    which is invoked with a list of message dictionaries each time 'batch_size'
    messages are received or 'batch_timeout' seconds is reached.
    """

    def dispatch(self, incoming):
        """Dispatch notification messages to the appropriate endpoint method.
        """

        messages_grouped = itertools.groupby(sorted(
            (self._extract_user_message(m) for m in incoming),
            key=operator.itemgetter(0)), operator.itemgetter(0))

        requeues = set()
        for priority, messages in messages_grouped:
            __, raw_messages, messages = six.moves.zip(*messages)
            if priority not in PRIORITIES:
                LOG.warning(_LW('Unknown priority "%s"'), priority)
                continue
            for screen, callback in self._callbacks_by_priority.get(priority,
                                                                    []):
                if screen:
                    filtered_messages = [message for message in messages
                                         if screen.match(
                                             message["ctxt"],
                                             message["publisher_id"],
                                             message["event_type"],
                                             message["metadata"],
                                             message["payload"])]
                else:
                    filtered_messages = list(messages)

                if not filtered_messages:
                    continue
				# callbak ： 下面对象
				# <bound method TelemetryIpc.sample of <ceilometer.telemetry.notifications.TelemetryIpc object at 0x7f3b02b7add0>>
				#  <bound method type._consume_and_drop of <class 'ceilometer.pipeline.event.EventEndpoint'>>
				# 调用TelemerryIpc的sample方法，其实是其父类的sample方法


                ret = self._exec_callback(callback, filtered_messages)
                if ret == NotificationResult.REQUEUE:
                    requeues.update(raw_messages)
                    break
        return requeues


    def _extract_user_message(self, incoming):
        ctxt = self.serializer.deserialize_context(incoming.ctxt)
        message = incoming.message

        publisher_id = message.get('publisher_id')
        event_type = message.get('event_type')
        metadata = {
            'message_id': message.get('message_id'),
            'timestamp': message.get('timestamp')
        }
        priority = message.get('priority', '').lower()
        payload = self.serializer.deserialize_entity(ctxt,
                                                     message.get('payload'))
        return priority, incoming, dict(ctxt=ctxt,
                                        publisher_id=publisher_id,
                                        event_type=event_type,
                                        payload=payload,
                                        metadata=metadata)




    def _exec_callback(self, callback, messages):
        try:
            return callback(messages)
        except Exception:
            LOG.exception("Callback raised an exception.")
            return NotificationResult.REQUEUE


```





```
# ceilometer/pipeline/sample.py  TelemetryIpc父类的sample方法
    
    
    def sample(self, notifications):
        """Convert message at sample level to Ceilometer Event.

        :param notifications: list of notifications
        """
        return self.process_notifications('sample', notifications)
   
   
   # notifications data: 
'''
    notifications----[{'payload': {u'samples': [{u'counter_name': u'custom.hardware.cpu.idle.percentage', u'user_id': None, u'message_signature': u'e504b879169bcb6a69732d77e6588a5d66ebecff8f7bcc6aeb3bd041b2a12594', u'timestamp': u'2021-07-30T02:33:11.969091', u'resource_id': u'30.90.2.27', u'message_id': u'7c0ef9b4-f0de-11eb-983c-48dc2d0162df', u'source': u'hardware', u'counter_unit': u'%', u'counter_volume': 0, u'project_id': None, u'resource_metadata': {u'resource_url': u'snmp://30.90.2.27'}, u'monotonic_time': None, u'counter_type': u'gauge'}]}, 'metadata': {'timestamp': u'2021-07-30 02:33:11.984029', 'message_id': u'e5594ff5-e2f7-4804-b1f9-e8f1caad926f'}, 'publisher_id': u'ceilometer.polling', 'event_type': u'telemetry.polling', 'ctxt': {'client_timeout': None}}]
'''

        
    def process_notifications(self, priority, notifications):
        for message in notifications:
            try:
                with self.publisher as p:
                    p(list(self.build_sample(message)))
            except Exception:
                LOG.error('Fail to process notification', exc_info=True)
                
                
 # 此处 self.publisher()，此处的 publisher 是在插件初始化的时候传进来的，是PublishContext类的实例，
 # publisher: <ceilometer.pipeline.base.PublishContext object at 0x7fdce87ea7d0>
 
 


# ceilometer/pipeline/base.py
 class PublishContext(object):
    def __init__(self, pipelines):
        self.pipelines = pipelines or []

    def __enter__(self):
        def p(data):
            for p in self.pipelines:
                p.publish_data(data)
        return p
 # 这里的 p 有两种类型，SamplePipeline和EventPipeline
 
 

 
 
 
 
 
 
 
 # ceilometer/telemetry/notifications.py
class TelemetryIpc(endpoint.SampleEndpoint):
    """Handle sample from notification bus

     Telemetry samples polled by polling agent.
     """

    event_types = ['telemetry.polling']

    def build_sample(self, message):
        samples = message['payload']['samples']
        for sample_dict in samples:
            yield sample.Sample(
                name=sample_dict['counter_name'],
                type=sample_dict['counter_type'],
                unit=sample_dict['counter_unit'],
                volume=sample_dict['counter_volume'],
                user_id=sample_dict['user_id'],
                project_id=sample_dict['project_id'],
                resource_id=sample_dict['resource_id'],
                timestamp=sample_dict['timestamp'],
                resource_metadata=sample_dict['resource_metadata'],
                source=sample_dict['source'],
                id=sample_dict['message_id'])
 
```





```
# ceilometer/pipeline/sample.py

class SamplePipeline(base.Pipeline):
    """Represents a pipeline for Samples."""

    def _validate_volume(self, s):
        volume = s.volume
        if volume is None:
            LOG.warning(
                'metering data %(counter_name)s for %(resource_id)s '
                '@ %(timestamp)s has no volume (volume: None), the sample will'
                ' be dropped'
                % {'counter_name': s.name,
                   'resource_id': s.resource_id,
                   'timestamp': s.timestamp if s.timestamp else 'NO TIMESTAMP'}
            )
            return False
        if not isinstance(volume, (int, float)):
            try:
                volume = float(volume)
            except ValueError:
                LOG.warning(
                    'metering data %(counter_name)s for %(resource_id)s '
                    '@ %(timestamp)s has volume which is not a number '
                    '(volume: %(counter_volume)s), the sample will be dropped'
                    % {'counter_name': s.name,
                       'resource_id': s.resource_id,
                       'timestamp': (
                           s.timestamp if s.timestamp else 'NO TIMESTAMP'),
                       'counter_volume': volume}
                )
                return False
        return True

    def publish_data(self, samples):
        if not isinstance(samples, list):
            samples = [samples]
        supported = [s for s in samples if self.supported(s)
                     and self._validate_volume(s)]
        self.sink.publish_samples(supported)

        
# 调用SampleSink的publish_samples方法

class SampleSink(base.Sink):

    def publish_samples(self, samples):
        """Push samples into pipeline for publishing.

        :param samples: Sample list.
        """

        if samples:
            """
            [<ceilometer.publisher.gnocchi.GnocchiPublisher object at 0x7f2a64077a90>]
            """
            for p in self.publishers:
                try:
                    p.publish_samples(samples)
                except Exception:
                    LOG.error("Pipeline %(pipeline)s: Continue after "
                              "error from publisher %(pub)s"
                              % {'pipeline': self, 'pub': p},
                              exc_info=True)

    @staticmethod
    def flush():
        pass







```







```
# ceilometer/publisher/gnocchi.py    
    
    def publish_samples(self, data):

        # print(data)
        # if "hardware.memory.total" in str(data) and "192.168.204.195" in str(data):
        # if "hardware.memory.total" in str(data):
        """
            [<name: hardware.memory.total, volume: 8009568, resource_id: 192.168.204.196, timestamp: 2021-01-20T06:10:58.487364>, <name: hardware.memory.total, volume: 16266124, resource_id: 192.168.204.195, timestamp: 2021-01-20T06:10:58.487364>, <name: hardware.memory.total, volume: 16266124, resource_id: 192.168.204.194, timestamp: 2021-01-20T06:10:58.487364>]
            
        """
        # print(data)
        # if "custom" in str(data) and "cpu" not in str(data):
        #     print(data)
        # print(str(samples))
        # for item in datsa:
        #     if 'hardware.cpu.interrupt' in str(item) and "192.168.204.194" in str(item):
        #         print(item)


        self.ensures_archives_policies()
        # NOTE(sileht): skip sample generated by gnocchi itself
        data = [s for s in data if not self._is_gnocchi_activity(s)]
        data.sort(key=operator.attrgetter('resource_id'))
        resource_grouped_samples = itertools.groupby(
            data, key=operator.attrgetter('resource_id'))
        gnocchi_data = {}
        measures = {}
        for resource_id, samples_of_resource in resource_grouped_samples:
            # NOTE(sileht): / is forbidden by Gnocchi
            resource_id = resource_id.replace('/', '_')

            for sample in samples_of_resource:
                metric_name = sample.name
                rd = self.metric_map.get(metric_name)
                # "<ceilometer.publisher.gnocchi.ResourcesDefinition object at 0x7fa0440ad690>"
                if rd is None:
                    if metric_name not in self._already_logged_metric_names:
                        LOG.warning("metric %s is not handled by Gnocchi" %
                                    metric_name)
                        self._already_logged_metric_names.add(metric_name)
                    continue

                if resource_id not in gnocchi_data:
                    gnocchi_data[resource_id] = {
                        'resource_type': rd.cfg['resource_type'],
                        'resource': {"id": resource_id,
                                     "user_id": sample.user_id,
                                     "project_id": sample.project_id}}

                gnocchi_data[resource_id].setdefault(
                    "resource_extra", {}).update(rd.sample_attributes(sample))
                measures.setdefault(resource_id, {}).setdefault(
                    metric_name,
                    {"measures": [],
                     "archive_policy_name":
                     rd.metrics[metric_name]["archive_policy_name"],
                     "unit": sample.unit}
                )["measures"].append(
                    {'timestamp': sample.timestamp,
                     'value': sample.volume}
                )

        try:
            self.batch_measures(measures, gnocchi_data)
        except gnocchi_exc.ClientException as e:
            LOG.error(six.text_type(e))
        except Exception as e:
            LOG.error(six.text_type(e), exc_info=True)

        for info in gnocchi_data.values():
            resource = info["resource"]
            resource_type = info["resource_type"]
            resource_extra = info["resource_extra"]
            if not resource_extra:
                continue
            try:
                self._if_not_cached(resource_type, resource['id'],
                                    resource_extra)
            except gnocchi_exc.ClientException as e:
                LOG.error(six.text_type(e))
            except Exception as e:
                LOG.error(six.text_type(e), exc_info=True)

```







参考链接：https://blog.csdn.net/weixin_43700106/article/details/107006677

