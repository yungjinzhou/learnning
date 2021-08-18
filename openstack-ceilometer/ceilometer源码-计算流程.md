

## 一.  stein版本 ceilometer-compute收集实例sample流程分析

### 1.1 服务入口

```
# ceilometer/cmd/polling.py

def create_polling_service(worker_id, conf):
    return manager.AgentManager(worker_id,
                                conf,
                                conf.polling_namespaces)

# conf.polling_namespaces # 即是你在命令行中传入的参数，compute或者是central，分别代表两个服务

def main():
    conf = cfg.ConfigOpts()
    conf.register_cli_opts(CLI_OPTS)
    service.prepare_service(conf=conf)
    sm = cotyledon.ServiceManager()
    sm.add(create_polling_service, args=(conf,))
    oslo_config_glue.setup(sm, conf)
    sm.run()


'''
关键:
1 cotyledon.Service(worker_id)
作用: 创建一个新的服务
参数: worker_id (int) – service实例的标示符
2 ServiceManager()
2.1 作用
类似于主进程，管理服务的生命周期。
控制子进程的生命周期，如果子进程意外死亡就重启他们。
每一个子进程ServiceWorker运行在一个服务的实例上。
一个应用必须创建一个ServiceManager类并且使用
ServiceManager.run()做为和应用的主循环
样例:
class cotyledon.ServiceManager(wait_interval=0.01, graceful_shutdown_timeout=60)
    
2.2 cotyledon.ServiceManager.add
cotyledon.ServiceManager.add(service, workers=1, args=None, kwargs=None)
作用: 创建一个子进程来运行AgentService服务
参数:
service (callable) – callable that return an instance of Service
workers (int) – number of processes/workers for this service
args (tuple) – additional positional arguments for this service
kwargs (dict) – additional keywoard arguments for this service
Returns:
a service id
    
2.3 cotyledon.ServiceManager.run()
开启并监督服务工作者
这个方法将会开启和监督所有子进程，直到主进程被关闭了
    
    
参考:
https://blog.csdn.net/qingyuanluofeng/article/details/95533476
'''  

原文链接：https://blog.csdn.net/weixin_43700106/article/details/107006653

```

### 1.2 compute服务即从此处开始，调用AgentManager的 init方法初始化，然后调用run方法进行数据的采集



```
# ceilometer/polling/manager.py

class AgentManager(cotyledon.Service):

    def __init__(self, worker_id, conf, namespaces=None):
        namespaces = namespaces or ['compute', 'central']
        group_prefix = conf.polling.partitioning_group_prefix

        super(AgentManager, self).__init__(worker_id)

        self.conf = conf

        if type(namespaces) is not list:
            namespaces = [namespaces]

        # we'll have default ['compute', 'central'] here if no namespaces will
        # be passed
        extensions = (self._extensions('poll', namespace, self.conf).extensions
                      for namespace in namespaces)
        # get the extensions from pollster builder
        extensions_fb = (self._extensions_from_builder('poll', namespace)
                         for namespace in namespaces)
		# extension_fb为生成器，迭代后里面元素为空列表
        self.extensions = list(itertools.chain(*list(extensions))) + list(
            itertools.chain(*list(extensions_fb)))
		
		# self.extensions[0].__dict__:  {'obj': <ceilometer.compute.pollsters.instance_stats.CPUUtilPollster object at 0x7f9f5dc93c50>, 'entry_point': EntryPoint.parse('cpu_util = ceilometer.compute.pollsters.instance_stats:CPUUtilPollster'), 'name': 'cpu_util', 'plugin': <class 'ceilometer.compute.pollsters.instance_stats.CPUUtilPollster'>})

        if not self.extensions:
            LOG.warning('No valid pollsters can be loaded from %s '
                        'namespaces', namespaces)

        discoveries = (self._extensions('discover', namespace,
                                        self.conf).extensions
                       for namespace in namespaces)
        self.discoveries = list(itertools.chain(*list(discoveries)))
        # self.discoveries:  
        # {'obj': <ceilometer.compute.discovery.InstanceDiscovery object at 0x7f9f5dc9e3d0>, 'entry_point': EntryPoint.parse('local_instances = ceilometer.compute.discovery:InstanceDiscovery'), 'name': 'local_instances', 'plugin': <class 'ceilometer.compute.discovery.InstanceDiscovery'>})
        
        self.polling_periodics = None

        self.hashrings = None
        self.partition_coordinator = None
        if self.conf.coordination.backend_url:
            # XXX uuid4().bytes ought to work, but it requires ascii for now
            coordination_id = str(uuid.uuid4()).encode('ascii')
            self.partition_coordinator = coordination.get_coordinator(
                self.conf.coordination.backend_url, coordination_id)

        # Compose coordination group prefix.
        # We'll use namespaces as the basement for this partitioning.
        namespace_prefix = '-'.join(sorted(namespaces))
        self.group_prefix = ('%s-%s' % (namespace_prefix, group_prefix)
                             if group_prefix else namespace_prefix)

        # 收集数据后发送到指定队列
        self.notifier = oslo_messaging.Notifier(
            messaging.get_transport(self.conf),
            driver=self.conf.publisher_notifier.telemetry_driver,
            publisher_id="ceilometer.polling")
			
        self._keystone = None
        self._keystone_last_exception = None


    def _extensions(self, category, agent_ns=None, *args, **kwargs):
        namespace = ('ceilometer.%s.%s' % (category, agent_ns) if agent_ns
                     else 'ceilometer.%s' % category)
        return self._get_ext_mgr(namespace, *args, **kwargs)


    @staticmethod
    def _get_ext_mgr(namespace, *args, **kwargs):
        def _catch_extension_load_error(mgr, ep, exc):
            # Extension raising ExtensionLoadError can be ignored,
            # and ignore any3thing we can't import as a safety measure.
            if isinstance(exc, plugin_base.ExtensionLoadError):
                LOG.debug("Skip loading extension for %s: %s",
                          ep.name, exc.msg)
                return

            show_exception = (LOG.isEnabledFor(logging.DEBUG)
                              and isinstance(exc, ImportError))
            LOG.error("Failed to import extension for %(name)r: "
                      "%(error)s",
                      {'name': ep.name, 'error': exc},
                      exc_info=show_exception)
            if isinstance(exc, ImportError):
                return
            raise exc

        return extension.ExtensionManager(
            namespace=namespace,
            invoke_on_load=True,
            invoke_args=args,
            invoke_kwds=kwargs,
            on_load_failure_callback=_catch_extension_load_error,
        )
# ExtensionManger是stevedore里自动加载的
```

#### 1.2.1 stevedore调用动态加载配置

```

# stevedore/stevedore/extension.py



class ExtensionManager(object):
    """Base class for all of the other managers.

    :param namespace: The namespace for the entry points.
    :type namespace: str
    :param invoke_on_load: Boolean controlling whether to invoke the
        object returned by the entry point after the driver is loaded.
    :type invoke_on_load: bool
    :param invoke_args: Positional arguments to pass when invoking
        the object returned by the entry point. Only used if invoke_on_load
        is True.
    :type invoke_args: tuple
    :param invoke_kwds: Named arguments to pass when invoking
        the object returned by the entry point. Only used if invoke_on_load
        is True.
    :type invoke_kwds: dict
    :param propagate_map_exceptions: Boolean controlling whether exceptions
        are propagated up through the map call or whether they are logged and
        then ignored
    :type propagate_map_exceptions: bool
    :param on_load_failure_callback: Callback function that will be called when
        a entrypoint can not be loaded. The arguments that will be provided
        when this is called (when an entrypoint fails to load) are
        (manager, entrypoint, exception)
    :type on_load_failure_callback: function
    :param verify_requirements: Use setuptools to enforce the
        dependencies of the plugin(s) being loaded. Defaults to False.
    :type verify_requirements: bool
    """

    def __init__(self, namespace,
                 invoke_on_load=False,
                 invoke_args=(),
                 invoke_kwds={},
                 propagate_map_exceptions=False,
                 on_load_failure_callback=None,
                 verify_requirements=False):
        self._init_attributes(
            namespace,
            propagate_map_exceptions=propagate_map_exceptions,
            on_load_failure_callback=on_load_failure_callback)
        extensions = self._load_plugins(invoke_on_load,
                                        invoke_args,
                                        invoke_kwds,
                                        verify_requirements)
        self._init_plugins(extensions)

    @classmethod
    def make_test_instance(cls, extensions, namespace='TESTING',
                           propagate_map_exceptions=False,
                           on_load_failure_callback=None,
                           verify_requirements=False):
        """Construct a test ExtensionManager

        Test instances are passed a list of extensions to work from rather
        than loading them from entry points.

        :param extensions: Pre-configured Extension instances to use
        :type extensions: list of :class:`~stevedore.extension.Extension`
        :param namespace: The namespace for the manager; used only for
            identification since the extensions are passed in.
        :type namespace: str
        :param propagate_map_exceptions: When calling map, controls whether
            exceptions are propagated up through the map call or whether they
            are logged and then ignored
        :type propagate_map_exceptions: bool
        :param on_load_failure_callback: Callback function that will
            be called when a entrypoint can not be loaded. The
            arguments that will be provided when this is called (when
            an entrypoint fails to load) are (manager, entrypoint,
            exception)
        :type on_load_failure_callback: function
        :param verify_requirements: Use setuptools to enforce the
            dependencies of the plugin(s) being loaded. Defaults to False.
        :type verify_requirements: bool
        :return: The manager instance, initialized for testing

        """

        o = cls.__new__(cls)
        o._init_attributes(namespace,
                           propagate_map_exceptions=propagate_map_exceptions,
                           on_load_failure_callback=on_load_failure_callback)
        o._init_plugins(extensions)
        return o

    def _init_attributes(self, namespace, propagate_map_exceptions=False,
                         on_load_failure_callback=None):
        self.namespace = namespace
        self.propagate_map_exceptions = propagate_map_exceptions
        self._on_load_failure_callback = on_load_failure_callback

    def _init_plugins(self, extensions):
        self.extensions = extensions
        self._extensions_by_name_cache = None

    @property
    def _extensions_by_name(self):
        if self._extensions_by_name_cache is None:
            d = {}
            for e in self.extensions:
                d[e.name] = e
            self._extensions_by_name_cache = d
        return self._extensions_by_name_cache

    ENTRY_POINT_CACHE = {}

    def list_entry_points(self):
        """Return the list of entry points for this namespace.

        The entry points are not actually loaded, their list is just read and
        returned.

        """
        if self.namespace not in self.ENTRY_POINT_CACHE:
            eps = list(pkg_resources.iter_entry_points(self.namespace))
            self.ENTRY_POINT_CACHE[self.namespace] = eps
			# ('stevedore/extenson.py  namespace---', 'ceilometer.poll.compute')
			# ('stevedore/extenson.py-----ENTRY POINT CACHE', [EntryPoint.parse('cpu_l3_cache = ceilometer.compute.pollsters.instance_stats:CPUL3CachePollster'), EntryPoint.parse('perf.cache.misses = ceilometer.compute.pollsters.instance_stats:PerfCacheMissesPollster'), ....

		return self.ENTRY_POINT_CACHE[self.namespace]

    def entry_points_names(self):
        """Return the list of entry points names for this namespace."""
        return list(map(operator.attrgetter("name"), self.list_entry_points()))

    def _load_plugins(self, invoke_on_load, invoke_args, invoke_kwds,
                      verify_requirements):
        extensions = []
        for ep in self.list_entry_points():
            LOG.debug('found extension %r', ep)
            try:
                ext = self._load_one_plugin(ep,
                                            invoke_on_load,
                                            invoke_args,
                                            invoke_kwds,
                                            verify_requirements,
                                            )
                if ext:
                    extensions.append(ext)
            except (KeyboardInterrupt, AssertionError):
                raise
            except Exception as err:
                if self._on_load_failure_callback is not None:
                    self._on_load_failure_callback(self, ep, err)
                else:
                    # Log the reason we couldn't import the module,
                    # usually without a traceback. The most common
                    # reason is an ImportError due to a missing
                    # dependency, and the error message should be
                    # enough to debug that.  If debug logging is
                    # enabled for our logger, provide the full
                    # traceback.
                    LOG.error('Could not load %r: %s', ep.name, err,
                              exc_info=LOG.isEnabledFor(logging.DEBUG))
        return extensions

    def _load_one_plugin(self, ep, invoke_on_load, invoke_args, invoke_kwds,
                         verify_requirements):
        # NOTE(dhellmann): Using require=False is deprecated in
        # setuptools 11.3.
        if hasattr(ep, 'resolve') and hasattr(ep, 'require'):
            if verify_requirements:
                ep.require()
            plugin = ep.resolve()
        else:
            plugin = ep.load(require=verify_requirements)
        if invoke_on_load:
            obj = plugin(*invoke_args, **invoke_kwds)
        else:
            obj = None
        return Extension(ep.name, ep, plugin, obj)

    def names(self):
        "Returns the names of the discovered extensions"
        # We want to return the names of the extensions in the order
        # they would be used by map(), since some subclasses change
        # that order.
        return [e.name for e in self.extensions]

    def map(self, func, *args, **kwds):
        """Iterate over the extensions invoking func() for each.

        The signature for func() should be::

            def func(ext, *args, **kwds):
                pass

        The first argument to func(), 'ext', is the
        :class:`~stevedore.extension.Extension` instance.

        Exceptions raised from within func() are propagated up and
        processing stopped if self.propagate_map_exceptions is True,
        otherwise they are logged and ignored.

        :param func: Callable to invoke for each extension.
        :param args: Variable arguments to pass to func()
        :param kwds: Keyword arguments to pass to func()
        :returns: List of values returned from func()
        """
        if not self.extensions:
            # FIXME: Use a more specific exception class here.
            raise NoMatches('No %s extensions found' % self.namespace)
        response = []
        for e in self.extensions:
            self._invoke_one_plugin(response.append, func, e, args, kwds)
        return response

    @staticmethod
    def _call_extension_method(extension, method_name, *args, **kwds):
        return getattr(extension.obj, method_name)(*args, **kwds)

    def map_method(self, method_name, *args, **kwds):
        """Iterate over the extensions invoking a method by name.

        This is equivalent of using :meth:`map` with func set to
        `lambda x: x.obj.method_name()`
        while being more convenient.

        Exceptions raised from within the called method are propagated up
        and processing stopped if self.propagate_map_exceptions is True,
        otherwise they are logged and ignored.

        .. versionadded:: 0.12

        :param method_name: The extension method name
                            to call for each extension.
        :param args: Variable arguments to pass to method
        :param kwds: Keyword arguments to pass to method
        :returns: List of values returned from methods
        """
        return self.map(self._call_extension_method,
                        method_name, *args, **kwds)

    def _invoke_one_plugin(self, response_callback, func, e, args, kwds):
        try:
            response_callback(func(e, *args, **kwds))
        except Exception as err:
            if self.propagate_map_exceptions:
                raise
            else:
                LOG.error('error calling %r: %s', e.name, err)
                LOG.exception(err)

    def items(self):
        """
        Return an iterator of tuples of the form (name, extension).

        This is analogous to the Mapping.items() method.
        """
        return self._extensions_by_name.items()

    def __iter__(self):
        """Produce iterator for the manager.

        Iterating over an ExtensionManager produces the :class:`Extension`
        instances in the order they would be invoked.
        """
        return iter(self.extensions)

    def __getitem__(self, name):
        """Return the named extension.

        Accessing an ExtensionManager as a dictionary (``em['name']``)
        produces the :class:`Extension` instance with the
        specified name.
        """
        return self._extensions_by_name[name]

    def __contains__(self, name):
        """Return true if name is in list of enabled extensions.
        """
        return any(extension.name == name for extension in self.extensions)


```









### 1.3 初始化后调用run方法，收集数据

```
# ceilometer/polling/manager.py

    def run(self):
        super(AgentManager, self).run()
        self.polling_manager = PollingManager(self.conf)
        # polling manager:  {'sources': [<ceilometer.polling.manager.PollingSource object at 0x7f8a4a2ae290>, <ceilometer.polling.manager.PollingSource object at 0x7f8a4a2ae410>, <ceilometer.polling.manager.PollingSource object at 0x7f8a4a2ae0d0>], 'conf': <oslo_config.cfg.ConfigOpts object at 0x7f8a4b5500d0>})
        if self.partition_coordinator:
            self.partition_coordinator.start(start_heart=True)
            self.join_partitioning_groups()
        self.start_polling_tasks()
        
    
        
    def start_polling_tasks(self):
        data = self.setup_polling_tasks()

        # Don't start useless threads if no task will run
        if not data:
            return

        # One thread per polling tasks is enough
        self.polling_periodics = periodics.PeriodicWorker.create(
            [], executor_factory=lambda:
            futures.ThreadPoolExecutor(max_workers=len(data)))

        for interval, polling_task in data.items():

            @periodics.periodic(spacing=interval, run_immediately=True)
            def task(running_task):
                self.interval_task(running_task)

            self.polling_periodics.add(task, polling_task)

        utils.spawn_thread(self.polling_periodics.start, allow_empty=True) 
        
        
    def setup_polling_tasks(self):
        polling_tasks = {}
        for source in self.polling_manager.sources:
            for pollster in self.extensions:
                if source.support_meter(pollster.name):
                    polling_task = polling_tasks.get(source.get_interval())
                    if not polling_task:
                        polling_task = PollingTask(self)
                        polling_tasks[source.get_interval()] = polling_task
                    polling_task.add(pollster, source)
        # pollster: 
        
        return polling_tasks

"""
setup_polling_tasks中
sources:  {'name': 'some_pollsters1', 'cfg': {'interval': 60, 'meters': ['cpu', 'vcpus', 'cpu_util', 'memory', 'memory.usage', 'memory.resident', 'memory.swap.in', 'memory.swap.out', 'network.incoming.bytes', 'network.incoming.packets', 'network.outgoing.bytes', 'network.outgoing.packets', 'network.incoming.packets.drop', 'network.incoming.packets.error', 'network.outgoing.packets.drop', 'network.outgoing.packets.error', 'disk.device.read.bytes', 'disk.device.read.requests', 'disk.device.write.bytes', 'disk.device.write.requests', 'disk.device.read.bytes.rate', 'disk.device.read.requests.rate', 'disk.device.write.bytes.rate', 'disk.device.write.requests.rate', 'disk.device.capacity', 'disk.device.allocation', 'disk.device.usage', 'disk.root.size', 'disk.usage'], 'name': 'some_pollsters1'}, 'interval': 60, 'meters': ['cpu', 'vcpus', 'cpu_util', 'memory', 'memory.usage', 'memory.resident', 'memory.swap.in', 'memory.swap.out', 'network.incoming.bytes', 'network.incoming.packets', 'network.outgoing.bytes', 'network.outgoing.packets', 'network.incoming.packets.drop', 'network.incoming.packets.error', 'network.outgoing.packets.drop', 'network.outgoing.packets.error', 'disk.device.read.bytes', 'disk.device.read.requests', 'disk.device.write.bytes', 'disk.device.write.requests', 'disk.device.read.bytes.rate', 'disk.device.read.requests.rate', 'disk.device.write.bytes.rate', 'disk.device.write.requests.rate', 'disk.device.capacity', 'disk.device.allocation', 'disk.device.usage', 'disk.root.size', 'disk.usage'], 'resources': [], 'discovery': []}
{'name': 'hardware_snmp', 'cfg': {'interval': 60, 'meters': ['hardware.cpu.util', 'hardware.cpu.user', 'hardware.cpu.nice', 'hardware.cpu.system', 'hardware.cpu.idle', 'hardware.cpu.wait', 'hardware.cpu.kernel', 'hardware.cpu.interrupt', 'hardware.disk.size.total', 'hardware.disk.size.used', 'hardware.disk.read.bytes', 'hardware.disk.write.bytes', 'hardware.disk.read.requests', 'hardware.disk.write.requests', 'hardware.memory.used', 'hardware.memory.total', 'hardware.memory.buffer', 'hardware.memory.cached', 'hardware.memory.swap.avail', 'hardware.memory.swap.total', 'hardware.network.incoming.bytes', 'hardware.network.incoming.errors', 'hardware.network.incoming.drop', 'hardware.network.incoming.packets', 'hardware.network.outgoing.bytes', 'hardware.network.outgoing.errors', 'hardware.network.outgoing.drop', 'hardware.network.outgoing.packets', 'hardware.network.ip.incoming.datagrams', 'hardware.network.ip.outgoing.datagrams'], 'name': 'hardware_snmp', 'resources': ['snmp://30.90.2.18']}, 'interval': 60, 'meters': ['hardware.cpu.util', 'hardware.cpu.user', 'hardware.cpu.nice', 'hardware.cpu.system', 'hardware.cpu.idle', 'hardware.cpu.wait', 'hardware.cpu.kernel', 'hardware.cpu.interrupt', 'hardware.disk.size.total', 'hardware.disk.size.used', 'hardware.disk.read.bytes', 'hardware.disk.write.bytes', 'hardware.disk.read.requests', 'hardware.disk.write.requests', 'hardware.memory.used', 'hardware.memory.total', 'hardware.memory.buffer', 'hardware.memory.cached', 'hardware.memory.swap.avail', 'hardware.memory.swap.total', 'hardware.network.incoming.bytes', 'hardware.network.incoming.errors', 'hardware.network.incoming.drop', 'hardware.network.incoming.packets', 'hardware.network.outgoing.bytes', 'hardware.network.outgoing.errors', 'hardware.network.outgoing.drop', 'hardware.network.outgoing.packets', 'hardware.network.ip.incoming.datagrams', 'hardware.network.ip.outgoing.datagrams'], 'resources': ['snmp://30.90.2.18'], 'discovery': []}
{'name': 'user_defined', 'cfg': {'interval': 60, 'meters': ['custom.hardware.cpu.user.percentage', 'custom.hardware.cpu.nice.percentage', 'custom.hardware.cpu.wait.percentage', 'custom.hardware.cpu.system.percentage', 'custom.hardware.cpu.idle.percentage', 'custom.hardware.cpu.steal.percentage', 'custom.hardware.cpu.softinterrupt.percentage', 'custom.hardware.cpu.interrupt.percentage', 'custom.hardware.disk.utilization', 'custom.hardware.memory.utilization', 'custom.hardware.swap.utilization', 'custom.hardware.network.interface.status', 'custom.hardware.disk.read.bytes', 'custom.hardware.disk.write.bytes', 'custom.hardware.disk.read.requests', 'custom.hardware.disk.write.requests'], 'name': 'user_defined', 'resources': ['snmp://30.90.2.18']}, 'interval': 60, 'meters': ['custom.hardware.cpu.user.percentage', 'custom.hardware.cpu.nice.percentage', 'custom.hardware.cpu.wait.percentage', 'custom.hardware.cpu.system.percentage', 'custom.hardware.cpu.idle.percentage', 'custom.hardware.cpu.steal.percentage', 'custom.hardware.cpu.softinterrupt.percentage', 'custom.hardware.cpu.interrupt.percentage', 'custom.hardware.disk.utilization', 'custom.hardware.memory.utilization', 'custom.hardware.swap.utilization', 'custom.hardware.network.interface.status', 'custom.hardware.disk.read.bytes', 'custom.hardware.disk.write.bytes', 'custom.hardware.disk.read.requests', 'custom.hardware.disk.write.requests'], 'resources': ['snmp://30.90.2.18'], 'discovery': []}

"""



    def interval_task(self, task):
        # NOTE(sileht): remove the previous keystone client
        # and exception to get a new one in this polling cycle.
        self._keystone = None
        self._keystone_last_exception = None

        # Note(leehom): if coordinator enabled call run_watchers to
        # update group member info before collecting
        if self.partition_coordinator:
            self.partition_coordinator.run_watchers()

        task.poll_and_notify()
        
 
        
    def poll_and_notify(self):
        """Polling sample and notify."""
        cache = {}
        discovery_cache = {}
        poll_history = {}
        for source_name, pollsters in iter_random(
                self.pollster_matches.items()):
            for pollster in iter_random(pollsters):
                # source_name: some_pollsters
                 # pollster.name: cpu_util
                key = Resources.key(source_name, pollster)
                # key: some_pollsters-cpu_util
                candidate_res = list(
                    self.resources[key].get(discovery_cache))
                if not candidate_res and pollster.obj.default_discovery:
                    candidate_res = self.manager.discover(
                        [pollster.obj.default_discovery], discovery_cache)

				# candidate_res: [<Server: left>, <Server: exec-1>, <Server: exec-3>, <Server: exec-2>, <Server: right>, <Server: amphora-b137109c-c068-4a2b-a0d4-8cee11f39439>, <Server: IntelX86-vm3>, <Server: Intel X86 + Centos7.6-1>, <Server: stor_test_vm_01>, <Server: Intelx86-centos>, <Server: storage>, <Server: stor_test_vm_02>, <Server: non-exec>, <Server: centos>, <Server: dispatch>]
                # Remove duplicated resources and black resources. Using
                # set() requires well defined __hash__ for each resource.
                # Since __eq__ is defined, 'not in' is safe here.
                polling_resources = []
                black_res = self.resources[key].blacklist
                history = poll_history.get(pollster.name, [])
                for x in candidate_res:
                    if x not in history:
                        history.append(x)
                        if x not in black_res:
                            polling_resources.append(x)
                poll_history[pollster.name] = history

                # If no resources, skip for this pollster
                if not polling_resources:
                    p_context = 'new ' if history else ''
                    LOG.debug("Skip pollster %(name)s, no %(p_context)s"
                              "resources found this cycle",
                              {'name': pollster.name, 'p_context': p_context})
                    continue

                LOG.info("Polling pollster %(poll)s in the context of "
                         "%(src)s",
                         dict(poll=pollster.name, src=source_name))
                try:
                    polling_timestamp = timeutils.utcnow().isoformat()
                    # pollster.obj: {'obj': <ceilometer.compute.pollsters.instance_stats.CPUUtilPollster object at 0x7fbc48199c10>, 'entry_point': EntryPoint.parse('cpu_util = ceilometer.compute.pollsters.instance_stats:CPUUtilPollster'), 'name': 'cpu_util', 'plugin': <class 'ceilometer.compute.pollsters.instance_stats.CPUUtilPollster'>}
                    samples = pollster.obj.get_samples(
                        manager=self.manager,
                        cache=cache,
                        resources=polling_resources
                    )
                    sample_batch = []

                    for sample in samples:
                        # Note(yuywz): Unify the timestamp of polled samples
                        sample.set_timestamp(polling_timestamp)
                        sample_dict = (
                            publisher_utils.meter_message_from_counter(
                                sample, self._telemetry_secret
                            ))
                        if isinstance(sample_dict, dict) and sample_dict.get("resource_id"):
                            resource_id = sample_dict.get("resource_id")
                            if need_filter(resource_id):
                                continue

                        if "custom" in str(sample_dict):
                            sample_dict = self.reprocess_custom_meters(sample_dict)
                        if "hardware.disk." in str(sample_dict):
                            sample_dict = self.reprocess_inherent_meters(sample_dict)
                        if self._batch_size:
                            if len(sample_batch) >= self._batch_size:
                                self._send_notification(sample_batch)
                                sample_batch = []
                            sample_batch.append(sample_dict)
                        else:
                            self._send_notification([sample_dict])

                    if sample_batch:
                        self._send_notification(sample_batch)

                except plugin_base.PollsterPermanentError as err:
                    LOG.error(
                        'Prevent pollster %(name)s from '
                        'polling %(res_list)s on source %(source)s anymore!',
                        dict(name=pollster.name,
                             res_list=str(err.fail_res_list),
                             source=source_name))
                    self.resources[key].blacklist.extend(err.fail_res_list)
                except Exception as err:
                    LOG.error(
                        'Continue after error from %(name)s: %(error)s'
                        % ({'name': pollster.name, 'error': err}),
                        exc_info=True)
        
        




```



samples = pollster.obj.get_samples()方法

```
# ceilometer/compute/pollsters/__init__.py


    def get_samples(self, manager, cache, resources):
        self._inspection_duration = self._record_poll_time()
        for instance in resources:
            try:
                polled_time, result = self._inspect_cached(
                    cache, instance, self._inspection_duration)
                # ('polled time ====', 1045093.589053434)
				# ('result-----', [<ceilometer.compute.virt.inspector.InstanceStats object at 0x7f1869fca450>])
				# 	('polled time ====', 1045093.366060635)
				# ('result-----', [InterfaceStats(name='tap4b122ff0-a3', mac='fa:16:3e:8f:ad:c1', fref=None, parameters={'interfaceid': None, 'bridge': 'qbr4b122ff0-a3'}, rx_bytes=3362318L, tx_bytes=3075909L, rx_packets=63813L, tx_packets=29041L, rx_drop=0L, tx_drop=0L, rx_errors=0L, tx_errors=0L), InterfaceStats(name='tapd5326057-37', mac='fa:16:3e:00:ca:be', fref=None, parameters={'interfaceid': None, 'bridge': 'qbrd5326057-37'}, rx_bytes=12722L, tx_bytes=0L, rx_packets=257L, tx_packets=0L, rx_drop=42589L, tx_drop=0L, rx_errors=0L, tx_errors=0L)])

                if not result:
                    continue
                for stats in self.aggregate_method(result):
                    yield self._stats_to_sample(instance, stats, polled_time)
            except NoVolumeException:
                # FIXME(sileht): This should be a removed... but I will
                # not change the test logic for now
                LOG.warning("%(name)s statistic in not available for "
                            "instance %(instance_id)s" %
                            {'name': self.sample_name,
                             'instance_id': instance.id})
            except virt_inspector.InstanceNotFoundException as err:
                # Instance was deleted while getting samples. Ignore it.
                LOG.debug('Exception while getting samples %s', err)
            except virt_inspector.InstanceShutOffException as e:
                LOG.debug('Instance %(instance_id)s was shut off while '
                          'getting sample of %(name)s: %(exc)s',
                          {'instance_id': instance.id,
                           'name': self.sample_name, 'exc': e})
            except virt_inspector.NoDataException as e:
                LOG.warning('Cannot inspect data of %(pollster)s for '
                            '%(instance_id)s, non-fatal reason: %(exc)s',
                            {'pollster': self.__class__.__name__,
                             'instance_id': instance.id, 'exc': e})
                raise plugin_base.PollsterPermanentError(resources)
            except ceilometer.NotImplementedError:
                # Selected inspector does not implement this pollster.
                LOG.debug('%(inspector)s does not provide data for '
                          '%(pollster)s',
                          {'inspector': self.inspector.__class__.__name__,
                           'pollster': self.__class__.__name__})
                raise plugin_base.PollsterPermanentError(resources)
            except Exception as err:
                LOG.error(
                    'Could not get %(name)s events for %(id)s: %(e)s', {
                        'name': self.sample_name, 'id': instance.id, 'e': err},
                    exc_info=True)


    def _stats_to_sample(self, instance, stats, polled_time):
        # stats.__dict__ : {'cpu_number': 8, 'cpu_time': 210303750000L, 'memory_swap_in': 0L, 'memory_usage': 460L, 'memory_bandwidth_total': None, 'memory_bandwidth_local': None, 'cpu_cycles': None, 'cache_references': None, 'cpu_util': None, 'memory_swap_out': 0L, 'cache_misses': None, 'cpu_l3_cache_usage': None, 'memory_resident': 1037L, 'instructions': None}

        
        volume = getattr(stats, self.sample_stats_key)
        LOG.debug("%(instance_id)s/%(name)s volume: "
                  "%(volume)s" % {
                      'name': self.sample_name,
                      'instance_id': instance.id,
                      'volume': (volume if volume is not None
                                 else 'Unavailable')})

        if volume is None:
            raise NoVolumeException()

        return util.make_sample_from_instance(
            self.conf,
            instance,
            name=self.sample_name,
            unit=self.sample_unit,
            type=self.sample_type,
            resource_id=self.get_resource_id(instance, stats),
            volume=volume,
            additional_metadata=self.get_additional_metadata(
                instance, stats),
            monotonic_time=polled_time,
        )
        
        
        
```



InstanceStats

```
# ceilometer/compute/virt/inspector.py

class InstanceStats(object):
    fields = [
        'cpu_number',              # number: number of CPUs
        'cpu_time',                # time: cumulative CPU time
        'cpu_util',                # util: CPU utilization in percentage
        'cpu_l3_cache_usage',      # cachesize: Amount of CPU L3 cache used
        'memory_usage',            # usage: Amount of memory used
        'memory_resident',         #
        'memory_swap_in',          # memory swap in
        'memory_swap_out',         # memory swap out
        'memory_bandwidth_total',  # total: total system bandwidth from one
                                   #   level of cache
        'memory_bandwidth_local',  # local: bandwidth of memory traffic for a
                                   #   memory controller
        'cpu_cycles',              # cpu_cycles: the number of cpu cycles one
                                   #   instruction needs
        'instructions',            # instructions: the count of instructions
        'cache_references',        # cache_references: the count of cache hits
        'cache_misses',            # cache_misses: the count of caches misses
    ]

    def __init__(self, **kwargs):
        for k in self.fields:
            setattr(self, k, kwargs.pop(k, None))
        if kwargs:
            raise AttributeError(
                "'InstanceStats' object has no attributes '%s'" % kwargs)
                
                
                
                
```



InstanceStats具体实现

```

# ceilometer/compute/virt/libvirt/inspector.py  
    
    
    @libvirt_utils.raise_nodata_if_unsupported
    @libvirt_utils.retry_on_disconnect
    def inspect_instance(self, instance, duration=None):
        domain = self._get_domain_not_shut_off_or_raise(instance)

        memory_used = memory_resident = None
        memory_swap_in = memory_swap_out = None
        memory_stats = domain.memoryStats()
        # Stat provided from libvirt is in KB, converting it to MB.
        if 'usable' in memory_stats and 'available' in memory_stats:
            memory_used = (memory_stats['available'] -
                           memory_stats['usable']) / units.Ki
        elif 'available' in memory_stats and 'unused' in memory_stats:
            memory_used = (memory_stats['available'] -
                           memory_stats['unused']) / units.Ki
        if 'rss' in memory_stats:
            memory_resident = memory_stats['rss'] / units.Ki
        if 'swap_in' in memory_stats and 'swap_out' in memory_stats:
            memory_swap_in = memory_stats['swap_in'] / units.Ki
            memory_swap_out = memory_stats['swap_out'] / units.Ki

        # TODO(sileht): stats also have the disk/vnic info
        # we could use that instead of the old method for Queen
        stats = self.connection.domainListGetStats([domain], 0)[0][1]
        cpu_time = 0
        current_cpus = stats.get('vcpu.current')
        # Iterate over the maximum number of CPUs here, and count the
        # actual number encountered, since the vcpu.x structure can
        # have holes according to
        # https://libvirt.org/git/?p=libvirt.git;a=blob;f=src/libvirt-domain.c
        # virConnectGetAllDomainStats()
        for vcpu in six.moves.range(stats.get('vcpu.maximum', 0)):
            try:
                cpu_time += (stats.get('vcpu.%s.time' % vcpu) +
                             stats.get('vcpu.%s.wait' % vcpu))
                current_cpus -= 1
            except TypeError:
                # pass here, if there are too many holes, the cpu count will
                # not match, so don't need special error handling.
                pass

        if current_cpus:
            # There wasn't enough data, so fall back
            cpu_time = stats.get('cpu.time')

        return virt_inspector.InstanceStats(
            cpu_number=stats.get('vcpu.current'),
            cpu_time=cpu_time / stats.get('vcpu.current'),
            memory_usage=memory_used,
            memory_resident=memory_resident,
            memory_swap_in=memory_swap_in,
            memory_swap_out=memory_swap_out,
            cpu_cycles=stats.get("perf.cpu_cycles"),
            instructions=stats.get("perf.instructions"),
            cache_references=stats.get("perf.cache_references"),
            cache_misses=stats.get("perf.cache_misses"),
            memory_bandwidth_total=stats.get("perf.mbmt"),
            memory_bandwidth_local=stats.get("perf.mbml"),
            cpu_l3_cache_usage=stats.get("perf.cmt"),
        )

```



## 二、compute增加pollster

以驱动为libvirt为例修改三个地方



### 2.1 修改inspector函数对应位置添加meter及转换方式

`ceilometer/compute/virt/libvirt/insector.py`

<font color=red>增加memory.util</font>

```
    @libvirt_utils.raise_nodata_if_unsupported
    @libvirt_utils.retry_on_disconnect
    def inspect_instance(self, instance, duration=None):
        domain = self._get_domain_not_shut_off_or_raise(instance)

        memory_used = memory_resident = None
        memory_swap_in = memory_swap_out = None
        memory_util = None
        memory_stats = domain.memoryStats()
        # Stat provided from libvirt is in KB, converting it to MB.
        if 'usable' in memory_stats and 'available' in memory_stats:
            memory_used = (memory_stats['available'] -
                           memory_stats['usable']) / units.Ki
            memory_util = round(float(memory_used) / (memory_stats['available'] / units.Ki), 2)
        elif 'available' in memory_stats and 'unused' in memory_stats:
            memory_used = (memory_stats['available'] -
                           memory_stats['unused']) / units.Ki
            memory_util = round(float(memory_used) / (memory_stats['available'] / units.Ki), 2)
        if 'rss' in memory_stats:
            memory_resident = memory_stats['rss'] / units.Ki
        if 'swap_in' in memory_stats and 'swap_out' in memory_stats:
            memory_swap_in = memory_stats['swap_in'] / units.Ki
            memory_swap_out = memory_stats['swap_out'] / units.Ki

        # TODO(sileht): stats also have the disk/vnic info
        # we could use that instead of the old method for Queen
        stats = self.connection.domainListGetStats([domain], 0)[0][1]
        cpu_time = 0
        current_cpus = stats.get('vcpu.current')
        # Iterate over the maximum number of CPUs here, and count the
        # actual number encountered, since the vcpu.x structure can
        # have holes according to
        # https://libvirt.org/git/?p=libvirt.git;a=blob;f=src/libvirt-domain.c
        # virConnectGetAllDomainStats()
        for vcpu in six.moves.range(stats.get('vcpu.maximum', 0)):
            try:
                cpu_time += (stats.get('vcpu.%s.time' % vcpu) +
                             stats.get('vcpu.%s.wait' % vcpu))
                current_cpus -= 1
            except TypeError:
                # pass here, if there are too many holes, the cpu count will
                # not match, so don't need special error handling.
                pass

        if current_cpus:
            # There wasn't enough data, so fall back
            cpu_time = stats.get('cpu.time')

        return virt_inspector.InstanceStats(
            cpu_number=stats.get('vcpu.current'),
            cpu_time=cpu_time / stats.get('vcpu.current'),
            memory_usage=memory_used,
            memory_util=memory_util,
            memory_resident=memory_resident,
            memory_swap_in=memory_swap_in,
            memory_swap_out=memory_swap_out,
            cpu_cycles=stats.get("perf.cpu_cycles"),
            instructions=stats.get("perf.instructions"),
            cache_references=stats.get("perf.cache_references"),
            cache_misses=stats.get("perf.cache_misses"),
            memory_bandwidth_total=stats.get("perf.mbmt"),
            memory_bandwidth_local=stats.get("perf.mbml"),
            cpu_l3_cache_usage=stats.get("perf.cmt"),
        )

```



### 2.2 新加pollster代码

`ceilometer/compute/pollsters/instance_stats.py`



```
class MemoryUtilPollster(InstanceStatsPollster):
    sample_name = 'memory.util'
    sample_unit = '%'
    sample_stats_key = 'memory_util'
```



### 2.3 修改总入口，添加stats_key

```
# ceilometer/compute/virt/inspector.py 

class InstanceStats(object):
    fields = [
        'cpu_number',              # number: number of CPUs
        'cpu_time',                # time: cumulative CPU time
        'cpu_util',                # util: CPU utilization in percentage
        'cpu_l3_cache_usage',      # cachesize: Amount of CPU L3 cache used
        'memory_usage',            # usage: Amount of memory used
        'memory_util',            # memory_util: memory utilization in percentage
        'memory_resident',         #
        'memory_swap_in',          # memory swap in
        'memory_swap_out',         # memory swap out
        'memory_bandwidth_total',  # total: total system bandwidth from one
                                   #   level of cache
        'memory_bandwidth_local',  # local: bandwidth of memory traffic for a
                                   #   memory controller
        'cpu_cycles',              # cpu_cycles: the number of cpu cycles one
                                   #   instruction needs
        'instructions',            # instructions: the count of instructions
        'cache_references',        # cache_references: the count of cache hits
        'cache_misses',            # cache_misses: the count of caches misses
    ]

    def __init__(self, **kwargs):
        for k in self.fields:
            setattr(self, k, kwargs.pop(k, None))
        if kwargs:
            raise AttributeError(
                "'InstanceStats' object has no attributes '%s'" % kwargs)

```



### 2.4 修改entry_points.txt添加entry_points，让stevedore能够扫描到新加的pollster

该位置加载代码中新添加的pollster

vim /usr/lib/python2.7/site-packages/ceilometer-12.1.0-py2.7.egg-info/entry_points.txt 

添加后可以从self.extension中获取

{'obj': <ceilometer.compute.pollsters.instance_stats.MemoryUtilPollster object at 0x7fb231486990>, 'entry_point': EntryPoint.parse('memory.util = ceilometer.compute.pollsters.instance_stats:MemoryUtilPollster'), 'name': 'memory.util', 'plugin': <class 'ceilometer.compute.pollsters.instance_stats.MemoryUtilPollster'>}



### 2.5 修改polling.yaml

```

---
sources:
    - name: some_pollsters
      interval: 60
      meters:
        - cpu
        - vcpus
      #  - cpu_util
        - memory
        - memory.util
        - memory.usage
        - memory.resident
        - memory.swap.in
        - memory.swap.out
        - network.incoming.bytes
        - network.incoming.packets
        - network.outgoing.bytes
        - network.outgoing.packets
        - network.incoming.packets.drop
        - network.incoming.packets.error
        - network.outgoing.packets.drop
        - network.outgoing.packets.error
        - disk.device.read.bytes
        - disk.device.read.requests
        - disk.device.write.bytes
        - disk.device.write.requests
        - disk.device.read.bytes.rate
        - disk.device.read.requests.rate
        - disk.device.write.bytes.rate
        - disk.device.write.requests.rate
        - disk.device.capacity
        - disk.device.allocation
        - disk.device.usage
        - disk.root.size
        - disk.usage
    - name: hardware_snmp
      interval: 60
      resources:
          - snmp://30.90.2.18
      meters:
        - hardware.cpu.util
        - hardware.cpu.user
        - hardware.cpu.nice
        - hardware.cpu.system
        - hardware.cpu.idle
        - hardware.cpu.wait
        - hardware.cpu.kernel
        - hardware.cpu.interrupt
        - hardware.disk.size.total
        - hardware.disk.size.used
        - hardware.disk.read.bytes
        - hardware.disk.write.bytes
        - hardware.disk.read.requests
        - hardware.disk.write.requests
        - hardware.memory.used
        - hardware.memory.total
        - hardware.memory.buffer
        - hardware.memory.cached
        - hardware.memory.swap.avail
        - hardware.memory.swap.total
        - hardware.network.incoming.bytes
        - hardware.network.incoming.errors
        - hardware.network.incoming.drop
        - hardware.network.incoming.packets
        - hardware.network.outgoing.bytes
        - hardware.network.outgoing.errors
        - hardware.network.outgoing.drop
        - hardware.network.outgoing.packets
        - hardware.network.ip.incoming.datagrams
        - hardware.network.ip.outgoing.datagrams
    - name: user_defined # 配置节点对应ip
      meters:
        - custom.hardware.cpu.user.percentage
        - custom.hardware.cpu.nice.percentage
        - custom.hardware.cpu.wait.percentage
        - custom.hardware.cpu.system.percentage
        - custom.hardware.cpu.idle.percentage
        - custom.hardware.cpu.steal.percentage
        - custom.hardware.cpu.softinterrupt.percentage
        - custom.hardware.cpu.interrupt.percentage
        - custom.hardware.disk.utilization
        - custom.hardware.memory.utilization
        - custom.hardware.swap.utilization
        - custom.hardware.network.interface.status
        - custom.hardware.disk.read.bytes
        - custom.hardware.disk.write.bytes
        - custom.hardware.disk.read.requests
        - custom.hardware.disk.write.requests
      resources:
        - snmp://30.90.2.18
      interval: 60


```





