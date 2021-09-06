













## 5 实践案例：stein版本Nova创建虚拟机过程分析

这里以创建虚拟机过程为例，根据前面的理论基础，一步步跟踪其执行过程。需要注意的是，Nova支持同时创建多台虚拟机，因此在调度时需要同时选择调度多个宿主机。

### 5.1 nova-api

根据前面的理论，创建虚拟机的入口为`nova/api/openstack/compute/servers.py`的`create`方法，该方法检查了一堆参数以及policy后，调用`compute_api`的`create()`方法。

```
def create(self, req, body):
    """Creates a new server for a given user."""
    # ... 省略部分代码     try:
        inst_type = flavors.get_flavor_by_flavor_id(
                flavor_id, ctxt=context, read_deleted="no")

        supports_multiattach = common.supports_multiattach_volume(req)
        supports_port_resource_request = \
            common.supports_port_resource_request(req)
        (instances, resv_id) = self.compute_api.create(context,
            inst_type,
            image_uuid,
            display_name=name,
            display_description=description,
            availability_zone=availability_zone,
            forced_host=host, forced_node=node,
            metadata=server_dict.get('metadata', {}),
            admin_password=password,
            check_server_group_quota=True,
            supports_multiattach=supports_multiattach,
            supports_port_resource_request=supports_port_resource_request,
                **create_kwargs)
    except (exception.QuotaError,
            exception.PortLimitExceeded) as error:
            # ...
```

这里的`compute_api`即前面说的`nova/compute/api.py`模块，找到该模块的`create`方法，该方法会创建数据库记录、检查参数等，然后调用`compute_task_api`的`schedule_and_build_instances`方法:

```
@hooks.add_hook("create_instance")
    @hooks.add_hook("create_instance")
    def create(self, context, instance_type,
               image_href, kernel_id=None, ramdisk_id=None,
               min_count=None, max_count=None,
               display_name=None, display_description=None,
               key_name=None, key_data=None, security_groups=None,
               availability_zone=None, forced_host=None, forced_node=None,
               user_data=None, metadata=None, injected_files=None,
               admin_password=None, block_device_mapping=None,
               access_ip_v4=None, access_ip_v6=None, requested_networks=None,
               config_drive=None, auto_disk_config=None, scheduler_hints=None,
               legacy_bdm=True, shutdown_terminate=False,
               check_server_group_quota=False, tags=None,
               supports_multiattach=False, trusted_certs=None,
               supports_port_resource_request=False):
    		# ...省略部分代码
            return self._create_instance(
            context, instance_type,
            image_href, kernel_id, ramdisk_id,
            min_count, max_count,
            display_name, display_description,
            key_name, key_data, security_groups,
            availability_zone, user_data, metadata,
            injected_files, admin_password,
            access_ip_v4, access_ip_v6,
            requested_networks, config_drive,
            block_device_mapping, auto_disk_config,
            filter_properties=filter_properties,
            legacy_bdm=legacy_bdm,
            shutdown_terminate=shutdown_terminate,
            check_server_group_quota=check_server_group_quota,
            tags=tags, supports_multiattach=supports_multiattach,
            trusted_certs=trusted_certs,
            supports_port_resource_request=supports_port_resource_request)
            
            
    def _create_instance(self, context, instance_type,
               image_href, kernel_id, ramdisk_id,
               min_count, max_count,
               display_name, display_description,
               key_name, key_data, security_groups,
               availability_zone, user_data, metadata, injected_files,
               admin_password, access_ip_v4, access_ip_v6,
               requested_networks, config_drive,
               block_device_mapping, auto_disk_config, filter_properties,
               reservation_id=None, legacy_bdm=True, shutdown_terminate=False,
               check_server_group_quota=False, tags=None,
               supports_multiattach=False, trusted_certs=None,
               supports_port_resource_request=False):
               
           # ....省略部分代码
        else:
            self.compute_task_api.schedule_and_build_instances(
                context,
                build_requests=build_requests,
                request_spec=request_specs,
                image=boot_meta,
                admin_password=admin_password,
                injected_files=injected_files,
                requested_networks=requested_networks,
                block_device_mapping=block_device_mapping,
                tags=tags)

        return instances, reservation_id
            
            
            
```

`compute_task_api`即conductor的`api.py`。conductor的api并没有执行什么操作，直接调用了`conductor_compute_rpcapi`的`schedule_and_build_instances`方法:

```
    def schedule_and_build_instances(self, context, build_requests,
                                     request_specs,
                                     image, admin_password, injected_files,
                                     requested_networks,
                                     block_device_mapping,
                                     tags=None):
        version = '1.17'
        kw = {'build_requests': build_requests,
              'request_specs': request_specs,
              'image': jsonutils.to_primitive(image),
              'admin_password': admin_password,
              'injected_files': injected_files,
              'requested_networks': requested_networks,
              'block_device_mapping': block_device_mapping,
              'tags': tags}

        if not self.client.can_send_version(version):
            version = '1.16'
            del kw['tags']

        cctxt = self.client.prepare(version=version)
        cctxt.cast(context, 'schedule_and_build_instances', **kw)
```

该方法即conductor RPC调用api，即`nova/conductor/rpcapi.py`模块，该方法除了一堆的版本检查，剩下的就是对RPC调用的封装，代码只有两行:

```
def schedule_and_build_instances(...):
    cctxt = self.client.prepare(version=version)
    cctxt.cast(context, 'schedule_and_build_instances', **kw)
```

其中`cast`表示异步调用，`schedule_and_build_instances`是RPC调用的方法，`kw`是传递的参数。参数是字典类型，没有复杂对象结构，因此不需要特别的序列化操作。

截至到现在，虽然目录由`api->compute->conductor`，但仍在nova-api进程中运行，直到cast方法执行，该方法由于是异步调用，会立即返回，不会等待RPC返回，因此nova-api任务完成，此时会响应用户请求，虚拟机状态为`building`。

### 5.2 nova-conductor

由于是向nova-conductor发起的RPC调用(根据RPC_TOPIC判定)，而前面说了接收端肯定是`manager.py`，因此进程跳到`nova-conductor`服务，入口为`nova/conductor/manager.py`的`schedule_and_build_instances`方法。

该方法首先调用了`_schedule_instances`方法，该方法首先调用了`scheduler_client`的`select_destinations`方法:

```
def schedule_and_build_instances(...):
    # Add all the UUIDs for the instances     instance_uuids = [spec.instance_uuid for spec in request_specs]
    try:
        host_lists = self._schedule_instances(context, request_specs[0],
                instance_uuids, return_alternates=True)
    except Exception as exc:
        ...
        
def _schedule_instances(self, context, request_spec,
                        instance_uuids=None, return_alternates=False):
    scheduler_utils.setup_instance_group(context, request_spec)
    with timeutils.StopWatch() as timer:
        host_lists = self.query_client.select_destinations(
            context, request_spec, instance_uuids, return_objects=True,
            return_alternates=return_alternates)
    LOG.debug('Took %0.2f seconds to select destinations for %s '
              'instance(s).', timer.elapsed(), len(instance_uuids))
    return host_lists
```

`scheduler_client`和`compute_api`以及`compute_task_api`都是一样对服务的client封装调用，不过scheduler没有`api.py`模块，而是有个单独的client目录，实现在`nova/scheduler/client`目录的`query.py`模块，`select_destinations`方法又很直接的调用了`scheduler_rpcapi`的`select_destinations`方法，终于又到了RPC调用环节。

```
def select_destinations(...):
    return self.scheduler_rpcapi.select_destinations(context, ...)
```

毫无疑问，RPC封装同样是在`nova/scheduler`的`rpcapi.py`中实现。该方法RPC调用代码如下:

```
def select_destinations(self, ...):
    # Modify the parameters if an older version is requested     # ...     cctxt = self.client.prepare(
        version=version,
        call_monitor_timeout=CONF.rpc_response_timeout,
        timeout=CONF.long_rpc_timeout)
    return cctxt.call(ctxt, 'select_destinations', **msg_args)
```

注意这里调用的是`call`方法，说明这是同步RPC调用，此时`nova-conductor`并不会退出，而是等待直到`nova-scheduler`返回。因此当前nova-conductor为堵塞状态，等待`nova-scheduler`返回，此时`nova-scheduler`接管任务。

### 5.3 nova-scheduler

同理找到scheduler的manager.py模块的`select_destinations`方法，该方法会调用driver方法:

```
@messaging.expected_exceptions(exception.NoValidHost)
def select_destinations(self, ctxt, ...):
    # ...     selections = self.driver.select_destinations(ctxt, spec_obj,...)
    return selections
```

这里的`driver`其实就是调度驱动，在配置文件中`scheduler`配置组指定，默认为`filter_scheduler`，对应`nova/scheduler/filter_scheduler.py`模块，该算法根据指定的filters过滤掉不满足条件的计算节点，然后通过`weigh`方法计算权值，最后选择权值高的作为候选计算节点返回。调度算法实现这里不展开，感兴趣的可以阅读。

最后nova-scheduler返回调度的`hosts`集合，任务结束。由于nova-conductor通过同步方法调用的该方法，因此nova-scheduler会把结果返回给nova-conductor服务。

### 5.4 nova-condutor

nova-conductor等待nova-scheduler返回后，拿到调度的计算节点列表，回到`scheduler/manager.py`的`schedule_and_build_instances`方法。

因为可能同时启动多个虚拟机，因此循环调用了`compute_rpcapi`的`build_and_run_instance`方法：

```
for (build_request, request_spec, host_list, instance) in zipped:
    # ...     with obj_target_cell(instance, cell) as cctxt:
        # ...         with obj_target_cell(instance, cell) as cctxt:
            self.compute_rpcapi.build_and_run_instance(
                    cctxt, ..., host_list=host_list)
```

看到xxxrpc立即想到对应的代码位置，位于`nova/compute/rpcapi`模块，该方法向nova-compute发起RPC请求:

```
def build_and_run_instance(self, ctxt, ...):
    # ...     client = self.router.client(ctxt)
    version = '5.0'
    cctxt = client.prepare(server=host, version=version)
    cctxt.cast(ctxt, 'build_and_run_instance', **kwargs)
```

由于是`cast`调用，因此发起的是异步RPC，因此nova-conductor任务结束，紧接着终于轮到nova-compute服务登场了。

### 5.5 nova-compute

终于等到nova-compute服务，服务入口为`nova/compute/manager.py`，找到`build_and_run_instance`方法，该方法调用关系如下：

```
build_and_run_instance()
  -> _locked_do_build_and_run_instance()
  -> _do_build_and_run_instance()
  -> _build_and_run_instance()
  -> driver.spawn()
```

这里的`driver`就是compute driver，通过`compute`配置组的`compute_driver`指定，这里为`libvirt.LibvirtDriver`，代码位于`nova/virt/libvirt/driver.py`，找到`spawn()`方法，该方法调用Libvirt创建虚拟机，并等待虚拟机状态为`Active`,nova-compute服务结束,整个创建虚拟机流程也到此结束。



















## todo: 分析api路径请求流程













## 分析nova组件启动流程，

以nova-conductor为例

根据服务启动代码

 /usr/bin/nova-conducotor

```
#!/usr/bin/python2
# PBR Generated from u'console_scripts'

import sys

from nova.cmd.conductor import main


if __name__ == "__main__":
    sys.exit(main())

```

启动入口在nova/cmd/conductor.py的main函数中，看下主要做了什么

```

def main():
    config.parse_args(sys.argv)
    logging.setup(CONF, "nova")
    objects.register_all()
    gmr_opts.set_defaults(CONF)
    objects.Service.enable_min_version_cache()

    gmr.TextGuruMeditation.setup_autorun(version, conf=CONF)

    server = service.Service.create(binary='nova-conductor',
                                    topic=rpcapi.RPC_TOPIC)
    workers = CONF.conductor.workers or processutils.get_worker_count()
    service.serve(server, workers=workers)
    service.wait()

```

server行上面，加载参数，加载配置，加载；server对象创建如下

```
# nova/nova/service.py

class Service(service.Service):
    """Service object for binaries running on hosts.

    A service takes a manager and enables rpc by listening to queues based
    on topic. It also periodically runs tasks on the manager and reports
    its state to the database services table.
    """

    def __init__(self, host, binary, topic, manager, report_interval=None,
                 periodic_enable=None, periodic_fuzzy_delay=None,
                 periodic_interval_max=None, *args, **kwargs):
        super(Service, self).__init__()
        self.host = host
        self.binary = binary
        self.topic = topic
        self.manager_class_name = manager
        self.servicegroup_api = servicegroup.API()
        manager_class = importutils.import_class(self.manager_class_name)
        if objects_base.NovaObject.indirection_api:
            conductor_api = conductor.API()
            conductor_api.wait_until_ready(context.get_admin_context())
        self.manager = manager_class(host=self.host, *args, **kwargs)
        self.rpcserver = None
        self.report_interval = report_interval
        self.periodic_enable = periodic_enable
        self.periodic_fuzzy_delay = periodic_fuzzy_delay
        self.periodic_interval_max = periodic_interval_max
        self.saved_args, self.saved_kwargs = args, kwargs
        self.backdoor_port = None
        setup_profiler(binary, self.host)
	# ... 省略代码

    @classmethod
    def create(cls, host=None, binary=None, topic=None, manager=None,
               report_interval=None, periodic_enable=None,
               periodic_fuzzy_delay=None, periodic_interval_max=None):
        """Instantiates class and passes back application object.

        :param host: defaults to CONF.host
        :param binary: defaults to basename of executable
        :param topic: defaults to bin_name - 'nova-' part
        :param manager: defaults to CONF.<topic>_manager
        :param report_interval: defaults to CONF.report_interval
        :param periodic_enable: defaults to CONF.periodic_enable
        :param periodic_fuzzy_delay: defaults to CONF.periodic_fuzzy_delay
        :param periodic_interval_max: if set, the max time to wait between runs

        """
        if not host:
            host = CONF.host
        if not binary:
            binary = os.path.basename(sys.argv[0])
        if not topic:
            topic = binary.rpartition('nova-')[2]
        if not manager:
            manager = SERVICE_MANAGERS.get(binary)
        if report_interval is None:
            report_interval = CONF.report_interval
        if periodic_enable is None:
            periodic_enable = CONF.periodic_enable
        if periodic_fuzzy_delay is None:
            periodic_fuzzy_delay = CONF.periodic_fuzzy_delay

        debugger.init()

        service_obj = cls(host, binary, topic, manager,
                          report_interval=report_interval,
                          periodic_enable=periodic_enable,
                          periodic_fuzzy_delay=periodic_fuzzy_delay,
                          periodic_interval_max=periodic_interval_max)

        return service_obj
```



__init__ 方法中有两个地方需要注意：

一是根据 manager_name 动态导入 manager 类。每一个 service 都用 manager 对象干 一些特定的工作！通过 importutils.import_class 实现。

 二是 `self.conductor_api.wait_until_ready(context.get_admin_context())`， 这处代码的功能是：根据 db_allowed 的值，确定组件是否被允许直接访问数据库。 假如允许，函数直接返回；假如不允许直接访问数据库，那么一直等待，等到 nova-conductor 服务启动。 



```
# nova/conductor/api.py



class API(object):
    """Conductor API that does updates via RPC to the ConductorManager."""

    def __init__(self):
        self.conductor_rpcapi = rpcapi.ConductorAPI()
        self.base_rpcapi = baserpc.BaseAPI(topic=rpcapi.RPC_TOPIC)

    def object_backport_versions(self, context, objinst, object_versions):
        return self.conductor_rpcapi.object_backport_versions(context, objinst,
                                                              object_versions)

    def wait_until_ready(self, context, early_timeout=10, early_attempts=10):
        '''Wait until a conductor service is up and running.

        This method calls the remote ping() method on the conductor topic until
        it gets a response.  It starts with a shorter timeout in the loop
        (early_timeout) up to early_attempts number of tries.  It then drops
        back to the globally configured timeout for rpc calls for each retry.
        '''
        attempt = 0
        timeout = early_timeout
        # if we show the timeout message, make sure we show a similar
        # message saying that everything is now working to avoid
        # confusion
        has_timedout = False
        while True:
            # NOTE(danms): Try ten times with a short timeout, and then punt
            # to the configured RPC timeout after that
            if attempt == early_attempts:
                timeout = None
            attempt += 1

            # NOTE(russellb): This is running during service startup. If we
            # allow an exception to be raised, the service will shut down.
            # This may fail the first time around if nova-conductor wasn't
            # running when this service started.
            try:
                self.base_rpcapi.ping(context, '1.21 GigaWatts',
                                      timeout=timeout)
                if has_timedout:
                    LOG.info('nova-conductor connection '
                             'established successfully')
                break
            except messaging.MessagingTimeout:
                has_timedout = True
                LOG.warning('Timed out waiting for nova-conductor.  '
                            'Is it running? Or did this service start '
                            'before nova-conductor?  '
                            'Reattempting establishment of '
                            'nova-conductor connection...')

```



LocalAPI 的 wait_until_ready 方法直接返回，所以不需要等待 nova-conductor 服务启动。 而 API.wait_until_ready() 方法会发起 RPC 调用并阻塞等待结果！ self.base_rpcapi对象 topic 值为 “conductor” , 利用call() 方法发送消息时， 只有 topic 值也是 “conductor” ，并且 version 不低于 “1.0” 的 rpcserver 才会处理！

后面分析服务启动的start方法时，能看到，每一个rpcserver 服务的 endpoints 都 包括 `BaseRPCAPI` 对象！nova-conductor 服务的 BaseRPCAPI 实例化对象 topic 值刚好是 “conductor”， 我们可以从代码中看到这一点。所以，只有 nova-conductor 服务启动了，**并 处理 base_rpcapi 发起的 call 请求**，才会退出 while 循环！

初始化调用baserpc的BaseAPI

```
class BaseAPI(object):
    """Client side of the base rpc API.

    API version history:

        1.0 - Initial version.
        1.1 - Add get_backdoor_port
    """

    VERSION_ALIASES = {
        # baseapi was added in havana
    }

    def __init__(self, topic):
        super(BaseAPI, self).__init__()
        target = messaging.Target(topic=topic,
                                  namespace=_NAMESPACE,
                                  version='1.0')
        version_cap = self.VERSION_ALIASES.get(CONF.upgrade_levels.baseapi,
                                               CONF.upgrade_levels.baseapi)
        self.client = rpc.get_client(target, version_cap=version_cap)

    def ping(self, context, arg, timeout=None):
        arg_p = jsonutils.to_primitive(arg)
        cctxt = self.client.prepare(timeout=timeout)
        return cctxt.call(context, 'ping', arg=arg_p)

    def get_backdoor_port(self, context, host):
        cctxt = self.client.prepare(server=host, version='1.1')
        return cctxt.call(context, 'get_backdoor_port')
        
        
class BaseRPCAPI(object):
    """Server side of the base RPC API."""

    target = messaging.Target(namespace=_NAMESPACE, version='1.1')

    def __init__(self, service_name, backdoor_port):
        self.service_name = service_name
        self.backdoor_port = backdoor_port

    def ping(self, context, arg):
        resp = {'service': self.service_name, 'arg': arg}
        return jsonutils.to_primitive(resp)

    def get_backdoor_port(self, context):
        return self.backdoor_port
  
```



生成的service_obj对象`<Service: host=controller, binary=nova-conductor, manager_class_name=nova.conductor.manager.ConductorManager>`, 继续向下serve和wait方法

 后面分析服务启动的start方法时，能看到，每一个rpcserver 服务的 endpoints 都 包括 `BaseRPCAPI` 对象！nova-conductor 服务的 BaseRPCAPI 实例化对象 topic 值刚好是 “conductor”， 我们可以从代码中看到这一点。所以，只有 nova-conductor 服务启动了，并 处理 base_rpcapi 发起的 call 请求，才会退出 while 循环！ 



所以会调用ConductorManager运行，该类位置在nova/conductor/manger.py中

```
# nova/conductor/manager.py

class ConductorManager(manager.Manager):
    """Mission: Conduct things.

    The methods in the base API for nova-conductor are various proxy operations
    performed on behalf of the nova-compute service running on compute nodes.
    Compute nodes are not allowed to directly access the database, so this set
    of methods allows them to get specific work done without locally accessing
    the database.

    The nova-conductor service also exposes an API in the 'compute_task'
    namespace.  See the ComputeTaskManager class for details.
    """

    target = messaging.Target(version='3.0')

    def __init__(self, *args, **kwargs):
        super(ConductorManager, self).__init__(service_name='conductor',
                                               *args, **kwargs)
        self.compute_task_mgr = ComputeTaskManager()
        self.additional_endpoints.append(self.compute_task_mgr)

```



ConductorManager 实例化设置 service_name， BaseRPCAPI实例化时会根据 service_name 设置 topic！ 然后组成 endpoints 创建 rpcserver！

```
# nova/service.py


class Service(service.Service):
    """Service object for binaries running on hosts.

    A service takes a manager and enables rpc by listening to queues based
    on topic. It also periodically runs tasks on the manager and reports
    its state to the database services table.
    """

    def __init__(self, host, binary, topic, manager, report_interval=None,
                 periodic_enable=None, periodic_fuzzy_delay=None,
                 periodic_interval_max=None, *args, **kwargs):
        super(Service, self).__init__()
        self.host = host
        self.binary = binary
        self.topic = topic
        self.manager_class_name = manager
        self.servicegroup_api = servicegroup.API()
        manager_class = importutils.import_class(self.manager_class_name)
        if objects_base.NovaObject.indirection_api:
            conductor_api = conductor.API()
            conductor_api.wait_until_ready(context.get_admin_context())
        self.manager = manager_class(host=self.host, *args, **kwargs)
        self.rpcserver = None
        self.report_interval = report_interval
        self.periodic_enable = periodic_enable
        self.periodic_fuzzy_delay = periodic_fuzzy_delay
        self.periodic_interval_max = periodic_interval_max
        self.saved_args, self.saved_kwargs = args, kwargs
        self.backdoor_port = None
        setup_profiler(binary, self.host)

    def __repr__(self):
        return "<%(cls_name)s: host=%(host)s, binary=%(binary)s, " \
               "manager_class_name=%(manager)s>" % {
                 'cls_name': self.__class__.__name__,
                 'host': self.host,
                 'binary': self.binary,
                 'manager': self.manager_class_name
                }

    def start(self):
        """Start the service.

        This includes starting an RPC service, initializing
        periodic tasks, etc.
        """
        # NOTE(melwitt): Clear the cell cache holding database transaction
        # context manager objects. We do this to ensure we create new internal
        # oslo.db locks to avoid a situation where a child process receives an
        # already locked oslo.db lock when it is forked. When a child process
        # inherits a locked oslo.db lock, database accesses through that
        # transaction context manager will never be able to acquire the lock
        # and requests will fail with CellTimeout errors.
        # See https://bugs.python.org/issue6721 for more information.
        # With python 3.7, it would be possible for oslo.db to make use of the
        # os.register_at_fork() method to reinitialize its lock. Until we
        # require python 3.7 as a mininum version, we must handle the situation
        # outside of oslo.db.
        context.CELL_CACHE = {}

        assert_eventlet_uses_monotonic_clock()

        verstr = version.version_string_with_package()
        LOG.info(_LI('Starting %(topic)s node (version %(version)s)'),
                  {'topic': self.topic, 'version': verstr})
        self.basic_config_check()
        self.manager.init_host()
        self.model_disconnected = False
        ctxt = context.get_admin_context()
        self.service_ref = objects.Service.get_by_host_and_binary(
            ctxt, self.host, self.binary)
        if self.service_ref:
            _update_service_ref(self.service_ref)

        else:
            try:
                self.service_ref = _create_service_ref(self, ctxt)
            except (exception.ServiceTopicExists,
                    exception.ServiceBinaryExists):
                # NOTE(danms): If we race to create a record with a sibling
                # worker, don't fail here.
                self.service_ref = objects.Service.get_by_host_and_binary(
                    ctxt, self.host, self.binary)

        self.manager.pre_start_hook()

        if self.backdoor_port is not None:
            self.manager.backdoor_port = self.backdoor_port

        LOG.debug("Creating RPC server for service %s", self.topic)

        target = messaging.Target(topic=self.topic, server=self.host)

        endpoints = [
            self.manager,
            baserpc.BaseRPCAPI(self.manager.service_name, self.backdoor_port)
        ]
        endpoints.extend(self.manager.additional_endpoints)

        serializer = objects_base.NovaObjectSerializer()

        self.rpcserver = rpc.get_server(target, endpoints, serializer)
        self.rpcserver.start()

        self.manager.post_start_hook()

        LOG.debug("Join ServiceGroup membership for this service %s",
                  self.topic)
        # Add service to the ServiceGroup membership group.
        self.servicegroup_api.join(self.host, self.topic, self)

        if self.periodic_enable:
            if self.periodic_fuzzy_delay:
                initial_delay = random.randint(0, self.periodic_fuzzy_delay)
            else:
                initial_delay = None

            self.tg.add_dynamic_timer(self.periodic_tasks,
                                     initial_delay=initial_delay,
                                     periodic_interval_max=
                                        self.periodic_interval_max)


```











经过上面这么多步骤，还只是创建了一个服务对象，服务并没有运行。我们接下来看下面的代码


 

```
# nova/nova/service.py


def serve(server, workers=None):
    global _launcher
    if _launcher:
        raise RuntimeError(_('serve() can only be called once'))

    _launcher = service.launch(CONF, server, workers=workers,
                               restart_method='mutate')
     # <oslo_service.service.ProcessLauncher object at 0x7f8167c90ed0>


def wait():
    _launcher.wait()


```









其中serve调用的launch方法，并启动

```
# oslo_service/service.py

def launch(conf, service, workers=1, restart_method='reload'):
    """Launch a service with a given number of workers.

    :param conf: an instance of ConfigOpts
    :param service: a service to launch, must be an instance of
           :class:`oslo_service.service.ServiceBase`
    :param workers: a number of processes in which a service will be running
    :param restart_method: Passed to the constructed launcher. If 'reload', the
        launcher will call reload_config_files on SIGHUP. If 'mutate', it will
        call mutate_config_files on SIGHUP. Other values produce a ValueError.
    :returns: instance of a launcher that was used to launch the service
    """

    if workers is not None and workers <= 0:
        raise ValueError(_("Number of workers should be positive!"))

    if workers is None or workers == 1:
        launcher = ServiceLauncher(conf, restart_method=restart_method)
    else:
        launcher = ProcessLauncher(conf, restart_method=restart_method)
    launcher.launch_service(service, workers=workers)

    return launcher

```

launcher.launch_service启动服务

```
# oslo_service/service.py

class ProcessLauncher(object):
    """Launch a service with a given number of workers."""
     
     # ... 省略代码
    def launch_service(self, service, workers=1):
        """Launch a service with a given number of workers.

       :param service: a service to launch, must be an instance of
              :class:`oslo_service.service.ServiceBase`
       :param workers: a number of processes in which a service
              will be running
        """
        _check_service_base(service)
        wrap = ServiceWrapper(service, workers)

        # Hide existing objects from the garbage collector, so that most
        # existing pages will remain in shared memory rather than being
        # duplicated between subprocesses in the GC mark-and-sweep. (Requires
        # Python 3.7 or later.)
        if hasattr(gc, 'freeze'):
            gc.freeze()

        LOG.info('Starting %d workers', wrap.workers)
        while self.running and len(wrap.children) < wrap.workers:
            self._start_child(wrap)
```



所以会调用ConductorManager运行，该类位置在nova/conductor/manger.py中

```
# nova/conductor/manager.py

class ConductorManager(manager.Manager):
    """Mission: Conduct things.

    The methods in the base API for nova-conductor are various proxy operations
    performed on behalf of the nova-compute service running on compute nodes.
    Compute nodes are not allowed to directly access the database, so this set
    of methods allows them to get specific work done without locally accessing
    the database.

    The nova-conductor service also exposes an API in the 'compute_task'
    namespace.  See the ComputeTaskManager class for details.
    """

    target = messaging.Target(version='3.0')

    def __init__(self, *args, **kwargs):
        super(ConductorManager, self).__init__(service_name='conductor',
                                               *args, **kwargs)
        self.compute_task_mgr = ComputeTaskManager()
        self.additional_endpoints.append(self.compute_task_mgr)

```



ConductorManager 实例化设置 service_name， BaseRPCAPI实例化时会根据 service_name 设置 topic！ 然后组成 endpoints 创建 rpcserver！



conductor调用ComputeTaskManager，conductor实际处理发送过来rpc函数名称来处理的类，即namespace='compute_task'的实际处理函数的位置，

```
# nova/conductor/manager.py

@profiler.trace_cls("rpc")
class ComputeTaskManager(base.Base):
    """Namespace for compute methods.

    This class presents an rpc API for nova-conductor under the 'compute_task'
    namespace.  The methods here are compute operations that are invoked
    by the API service.  These methods see the operation to completion, which
    may involve coordinating activities on multiple compute nodes.
    """

    target = messaging.Target(namespace='compute_task', version='1.20')

    def __init__(self):
        super(ComputeTaskManager, self).__init__()
        self.compute_rpcapi = compute_rpcapi.ComputeAPI()
        self.volume_api = cinder.API()
        self.image_api = image.API()
        self.network_api = network.API()
        self.servicegroup_api = servicegroup.API()
        self.query_client = query.SchedulerQueryClient()
        self.report_client = report.SchedulerReportClient()
        self.notifier = rpc.get_notifier('compute', CONF.host)
        # Help us to record host in EventReporter
        self.host = CONF.host
```















## 分析call和cast方法具体流程

以nova创建实例过程中，`schedule_and_build_instances`RPC调用的方法进行分析，rpc的namespace是compute_task，从nova/conductor/rpcapi.py 的ComputeTaskAPI类中调用rpc发送的



```

        cctxt = self.client.prepare(version=version)
        cctxt.cast(context, 'schedule_and_build_instances', **kw)
```

先来看cctxt对象

```
        self.client = rpc.get_client(target, serializer=serializer)
```



```
# nova/nova/rpc.py

def get_client(target, version_cap=None, serializer=None,
               call_monitor_timeout=None):
    assert TRANSPORT is not None

    if profiler:
        serializer = ProfilerRequestContextSerializer(serializer)
    else:
        serializer = RequestContextSerializer(serializer)

    return messaging.RPCClient(TRANSPORT,
                               target,
                               version_cap=version_cap,
                               serializer=serializer,
                               call_monitor_timeout=call_monitor_timeout)

```



RPCClient的prepare方法

```
    def prepare(self, exchange=_marker, topic=_marker, namespace=_marker,
                version=_marker, server=_marker, fanout=_marker,
                timeout=_marker, version_cap=_marker, retry=_marker,
                call_monitor_timeout=_marker):
        """Prepare a method invocation context.

        Use this method to override client properties for an individual method
        invocation. For example::

            def test(self, ctxt, arg):
                cctxt = self.prepare(version='2.5')
                return cctxt.call(ctxt, 'test', arg=arg)

        :param exchange: see Target.exchange
        :type exchange: str
        :param topic: see Target.topic
        :type topic: str
        :param namespace: see Target.namespace
        :type namespace: str
        :param version: requirement the server must support, see Target.version
        :type version: str
        :param server: send to a specific server, see Target.server
        :type server: str
        :param fanout: send to all servers on topic, see Target.fanout
        :type fanout: bool
        :param timeout: an optional default timeout (in seconds) for call()s
        :type timeout: int or float
        :param version_cap: raise a RPCVersionCapError version exceeds this cap
        :type version_cap: str
        :param retry: an optional connection retries configuration:
                      None or -1 means to retry forever.
                      0 means no retry is attempted.
                      N means attempt at most N retries.
        :type retry: int
        :param call_monitor_timeout: an optional timeout (in seconds) for
                                     active call heartbeating. If specified,
                                     requires the server to heartbeat
                                     long-running calls at this interval
                                     (less than the overall timeout
                                     parameter).
        :type call_monitor_timeout: int
        """
        return _CallContext._prepare(self,
                                     exchange, topic, namespace,
                                     version, server, fanout,
                                     timeout, version_cap, retry,
                                     call_monitor_timeout)

```



然后调用RPCClient的cast方法`self.prepare().cast(ctxt, method, **kwargs)`，继而调用oslo_messaging/rpc/client.py的_BaseCallContext的cast方法，call方法也是在这里被调用

```
    def cast(self, ctxt, method, **kwargs):
        """Invoke a method and return immediately. See RPCClient.cast()."""
        msg = self._make_message(ctxt, method, kwargs)
        msg_ctxt = self.serializer.serialize_context(ctxt)

        self._check_version_cap(msg.get('version'))

        try:
            self.transport._send(self.target, msg_ctxt, msg, retry=self.retry)
        except driver_base.TransportDriverError as ex:
            raise ClientSendError(self.target, ex)
```



```
    # oslo_messaging/transport.py
    def _send(self, target, ctxt, message, wait_for_reply=None, timeout=None,
              call_monitor_timeout=None, retry=None):
        if not target.topic:
            raise exceptions.InvalidTarget('A topic is required to send',
                                           target)
        return self._driver.send(target, ctxt, message,
                                 wait_for_reply=wait_for_reply,
                                 timeout=timeout,
                                 call_monitor_timeout=call_monitor_timeout,
                                 retry=retry)
```

此处用的driver是amqpdriver

```
    # oslo_messaging/_drivers/amqpdriver.py
    def send(self, target, ctxt, message, wait_for_reply=None, timeout=None,
             call_monitor_timeout=None, retry=None):
        return self._send(target, ctxt, message, wait_for_reply, timeout,
                          call_monitor_timeout, retry=retry)
                          
                          
                      

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
```

调用impl_rabbit.py的notify_send方法

```
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











实例创建参考链接：https://www.jingh.top/2019/04/29/%E5%A6%82%E4%BD%95%E9%98%85%E8%AF%BBOpenStack%E6%BA%90%E7%A0%81(%E6%9B%B4%E6%96%B0%E7%89%88)/

rpc流程参考链接：https://rootdeep.github.io/posts/rpc-call-procedure-in-oslo-messaging/

nova-conductor服务启动流程参考链接：https://gtcsq.readthedocs.io/en/latest/openstack/nova_rpcserver_start.html