## stein版本zun在创建容器流程





zun-api启动

/usr/bin/zun-api

```
#!/usr/bin/python
# PBR Generated from u'console_scripts'

import sys

from zun.cmd.api import main


if __name__ == "__main__":
    sys.exit(main())

```

从zun.cmd.api开始分析

main函数主要内容，读取配置文件，启动wsgi服务

以创建容器为例

 http://controller:9517/v1/containers/7becd252-b619-402d-a989-b6c1128b4c5c    post

找到代码位置

zun/api/controllers/v1/containers.py 中的ContainersController

```

    @base.Controller.api_version("1.1", "1.19")
    @pecan.expose('json')
    @api_utils.enforce_content_types(['application/json'])
    @exception.wrap_pecan_controller_exception
    @validation.validate_query_param(pecan.request, schema.query_param_create)
    @validation.validated(schema.legacy_container_create)
    def post(self, run=False, **container_dict):
        # NOTE(hongbin): We convert the representation of 'command' from
        # string to list. For example:
        # '"nginx" "-g" "daemon off;"' -> ["nginx", "-g", "daemon off;"]
        command = container_dict.pop('command', None)
        if command is not None:
            if isinstance(command, six.string_types):
                command = shlex.split(command)
            container_dict['command'] = command

        return self._do_post(run, **container_dict)
```

调用do_post

```
    def _do_post(self, run=False, **container_dict):
        """Create or run a new container.

        :param run: if true, starts the container
        :param container_dict: a container within the request body.
        """
        context = pecan.request.context
        # <zun.common.context.RequestContext object at 0x7fdf6618ae90>
        compute_api = pecan.request.compute_api
        # <zun.compute.api.API object at 0x7fdf66230850>
        policy.enforce(context, "container:create",
                       action="container:create")

        if container_dict.get('security_groups'):
            # remove duplicate security_groups from list
            container_dict['security_groups'] = list(set(
                container_dict.get('security_groups')))
            for index, sg in enumerate(container_dict['security_groups']):
                security_group_id = self._check_security_group(context,
                                                               {'name': sg})
                container_dict['security_groups'][index] = security_group_id

        try:
            run = strutils.bool_from_string(run, strict=True)
            container_dict['interactive'] = strutils.bool_from_string(
                container_dict.get('interactive', False), strict=True)
        except ValueError:
            bools = ', '.join(strutils.TRUE_STRINGS + strutils.FALSE_STRINGS)
            raise exception.InvalidValue(_('Valid run or interactive '
                                           'values are: %s') % bools)

        # Check container quotas
        self._check_container_quotas(context, container_dict)

        auto_remove = container_dict.pop('auto_remove', None)
        if auto_remove is not None:
            api_utils.version_check('auto_remove', '1.3')
            try:
                container_dict['auto_remove'] = strutils.bool_from_string(
                    auto_remove, strict=True)
            except ValueError:
                bools = ', '.join(strutils.TRUE_STRINGS +
                                  strutils.FALSE_STRINGS)
                raise exception.InvalidValue(_('Valid auto_remove '
                                               'values are: %s') % bools)

        runtime = container_dict.pop('runtime', None)
        if runtime is not None:
            api_utils.version_check('runtime', '1.5')
            policy.enforce(context, "container:create:runtime",
                           action="container:create:runtime")
            container_dict['runtime'] = runtime

        hostname = container_dict.pop('hostname', None)
        if hostname is not None:
            api_utils.version_check('hostname', '1.9')
            container_dict['hostname'] = hostname

        nets = container_dict.get('nets', [])
        requested_networks = utils.build_requested_networks(context, nets)
        pci_req = self._create_pci_requests_for_sriov_ports(context,
                                                            requested_networks)

        healthcheck = container_dict.pop('healthcheck', {})
        if healthcheck:
            api_utils.version_check('healthcheck', '1.22')
            healthcheck['test'] = healthcheck.pop('cmd', '')
            container_dict['healthcheck'] = healthcheck

        mounts = container_dict.pop('mounts', [])
        if mounts:
            api_utils.version_check('mounts', '1.11')

        cpu_policy = container_dict.pop('cpu_policy', None)
        container_dict['cpu_policy'] = cpu_policy

        privileged = container_dict.pop('privileged', None)
        if privileged is not None:
            api_utils.version_check('privileged', '1.21')
            policy.enforce(context, "container:create:privileged",
                           action="container:create:privileged")
            try:
                container_dict['privileged'] = strutils.bool_from_string(
                    privileged, strict=True)
            except ValueError:
                bools = ', '.join(strutils.TRUE_STRINGS +
                                  strutils.FALSE_STRINGS)
                raise exception.InvalidValue(_('Valid privileged values '
                                               'are: %s') % bools)

        # Valiadtion accepts 'None' so need to convert it to None
        container_dict['image_driver'] = api_utils.string_or_none(
            container_dict.get('image_driver'))
        if not container_dict['image_driver']:
            container_dict['image_driver'] = CONF.default_image_driver

        container_dict['project_id'] = context.project_id
        container_dict['user_id'] = context.user_id
        name = container_dict.get('name') or \
            self._generate_name_for_container()
        container_dict['name'] = name
        self._set_default_resource_limit(container_dict)
        if container_dict.get('restart_policy'):
            utils.check_for_restart_policy(container_dict)

        exposed_ports = container_dict.pop('exposed_ports', None)
        if exposed_ports is not None:
            api_utils.version_check('exposed_ports', '1.24')
            exposed_ports = utils.build_exposed_ports(exposed_ports)
            container_dict['exposed_ports'] = exposed_ports

        registry = container_dict.pop('registry', None)
        if registry:
            api_utils.version_check('registry', '1.31')
            registry = utils.get_registry(registry)
            container_dict['registry_id'] = registry.id

        container_dict['status'] = consts.CREATING
        extra_spec = {}
        extra_spec['hints'] = container_dict.get('hints', None)
        extra_spec['pci_requests'] = pci_req
        extra_spec['availability_zone'] = container_dict.get(
            'availability_zone')
        # ------下面有数据交互，todo-------------------
        new_container = objects.Container(context, **container_dict)
        new_container.create(context)

        kwargs = {}
        kwargs['extra_spec'] = extra_spec
        kwargs['requested_networks'] = requested_networks
        kwargs['requested_volumes'] = (
            self._build_requested_volumes(context, new_container, mounts))
        if pci_req.requests:
            kwargs['pci_requests'] = pci_req
        kwargs['run'] = run
        compute_api.container_create(context, new_container, **kwargs)
        # 调用compute/api.py
        # Set the HTTP Location Header
        pecan.response.location = link.build_url('containers',
                                                 new_container.uuid)
        pecan.response.status = 202
        return view.format_container(context, pecan.request.host_url,
                                     new_container)

```

调用compute/api.py



```
# zun/compute/api.py

      def container_create(self, context, new_container, extra_spec,
                         requested_networks, requested_volumes, run,
                         pci_requests=None):
        try:
            host_state = self._schedule_container(context, new_container,
                                                  extra_spec)
        except exception.NoValidHost:
            new_container.status = consts.ERROR
            new_container.status_reason = _(
                "There are not enough hosts available.")
            new_container.save(context) # 数据库操作-----
            
            return
        except Exception:
            new_container.status = consts.ERROR
            new_container.status_reason = _("Unexpected exception occurred.")
            new_container.save(context) # 数据库操作------
            raise

        # NOTE(mkrai): Intent here is to check the existence of image
        # before proceeding to create container. If image is not found,
        # container create will fail with 400 status.
        if CONF.api.enable_image_validation:
            try:
                images = self.rpcapi.image_search(
                    context, new_container.image,
                    new_container.image_driver, True, new_container.registry,
                    host_state['host'])
                if not images:
                    raise exception.ImageNotFound(image=new_container.image)
                if len(images) > 1:
                    raise exception.Conflict('Multiple images exist with same '
                                             'name. Please use the container '
                                             'uuid instead.')
            except exception.OperationNotSupported:
                LOG.info("Skip validation since search is not supported for "
                         "image '%(image)s' and image driver '%(driver)s'.",
                         {'image': new_container.image,
                          'driver': new_container.image_driver})
            except exception.ReferenceInvalidFormat:
                raise exception.InvalidValue(_("The format of image name '%s' "
                                               "is invalid.")
                                             % new_container.image)
            except Exception as e:
                LOG.warning("Skip validation since image search failed with "
                            "unexpected exception: %s", str(e))

        self._record_action_start(context, new_container,
                                  container_actions.CREATE)
        self.rpcapi.container_create(context, host_state['host'],
                                     new_container, host_state['limits'],
                                     requested_networks, requested_volumes,
                                     run, pci_requests)

    def _schedule_container(self, context, new_container, extra_spec):
        dests = self.scheduler_client.select_destinations(context,
                                                          [new_container],
                                                          extra_spec)
        return dests[0]




    def _schedule_container(self, context, new_container, extra_spec):
        dests = self.scheduler_client.select_destinations(context,
                                                          [new_container],
                                                          extra_spec)
        return dests[0]


    def _record_action_start(self, context, container, action):
        objects.ContainerAction.action_start(context, container.uuid,
                                             action, want_result=False)

```



container_create首先调用scheduler，然后调用  self._record_action_start操作数据库，最后发送rpcapi请求到zun-compute

调用scheduler

```
# zun/scheduler/client.py

class SchedulerClient(object):
    """Client library for placing calls to the scheduler."""

    def __init__(self):
        scheduler_driver = CONF.scheduler.driver
        self.driver = driver.DriverManager(
            "zun.scheduler.driver",
            scheduler_driver,
            invoke_on_load=True).driver

    def select_destinations(self, context, containers, extra_spec):
        return self.driver.select_destinations(context, containers, extra_spec)

```









rpcapi请求

```
# zun/compute/rpcapi.py
    
    def container_create(self, context, host, container, limits,
                         requested_networks, requested_volumes, run,
                         pci_requests):
        self._cast(host, 'container_create', limits=limits,
                   requested_networks=requested_networks,
                   requested_volumes=requested_volumes,
                   container=container,
                   run=run,
                   pci_requests=pci_requests)
```



















**zun/api/controllers/v1/containers.py**



1. policy enforce: 检查 policy，验证用户是否具有创建 container 权限的 API 调用。
2. check security group: 检查安全组是否存在，根据传递的名称返回安全组的 ID。
3. check container quotas: 检查 quota 配额。
4. build requested network: 检查网络配置，比如 port 是否存在、network id 是否合法，最后构建内部的 network 对象模型字典。注意，这一步只检查并没有创建 port。
5. create container object：根据传递的参数，构造 container 对象模型。
6. build requeted volumes: 检查 volume 配置，如果传递的是 volume id，则检查该 volume 是否存在，如果没有传递 volume id 只指定了 size，则调用 Cinder API 创建新的 volume。



**zun/compute/api.py**



1. schedule container: 使用 FilterScheduler 调度 container，返回宿主机的 host 对象。这个和 nova-scheduler 非常类似，只是 Zun 集成到 zun-api 中了。目前支持的 filters 如 CPUFilter、RamFilter、LabelFilter、ComputeFilter、RuntimeFilter 等。
2. image validation: 检查镜像是否存在，这里会远程调用 zun-compute 的 image_search 方法，其实就是调用 docker search。这里主要为了实现快速失败，避免到了 compute 节点才发现 image 不合法。
3. record action: 和 Nova 的 record action 一样，记录 container 的操作日志。
4. rpc cast container_create: 远程异步调用 zun-compute 的 container_create()方法，zun-api 任务结束。























#### 4.1.2 zun-compute

上一步rpc调用 container_create方法，到zun/compute/manager.py里

```
    def container_create(self, context, limits, requested_networks,
                         requested_volumes, container, run, pci_requests=None):
        @utils.synchronized(container.uuid)
        def do_container_create():
            self._wait_for_volumes_available(context, requested_volumes,
                                             container)
            self._attach_volumes(context, container, requested_volumes)
            self._check_support_disk_quota(context, container)
            created_container = self._do_container_create(
                context, container, requested_networks, requested_volumes,
                pci_requests, limits)
            if run:
                self._do_container_start(context, created_container)

        utils.spawn_n(do_container_create)
        
        
        
    @wrap_container_event(prefix='compute')
    def _do_container_create(self, context, container, requested_networks,
                             requested_volumes, pci_requests=None,
                             limits=None):
        LOG.debug('Creating container: %s', container.uuid)

        try:
            rt = self._get_resource_tracker()
            with rt.container_claim(context, container, pci_requests, limits):
                created_container = self._do_container_create_base(
                    context, container, requested_networks, requested_volumes,
                    limits)
                return created_container
        except exception.ResourcesUnavailable as e:
            with excutils.save_and_reraise_exception():
                LOG.exception("Container resource claim failed: %s",
                              six.text_type(e))
                self._fail_container(context, container, six.text_type(e),
                                     unset_host=True)



    def _do_container_create_base(self, context, container, requested_networks,
                                  requested_volumes,
                                  limits=None):
        self._update_task_state(context, container, consts.IMAGE_PULLING)
        image_driver_name = container.image_driver
        repo, tag = utils.parse_image_name(container.image, image_driver_name,
                                           registry=container.registry)
        image_pull_policy = utils.get_image_pull_policy(
            container.image_pull_policy, tag)
        try:
            image, image_loaded = self.driver.pull_image(
                context, repo, tag, image_pull_policy, image_driver_name,
                registry=container.registry)
            image['repo'], image['tag'] = repo, tag
            if not image_loaded:
                self.driver.load_image(image['path'])
        except exception.ImageNotFound as e:
            with excutils.save_and_reraise_exception():
                LOG.error(six.text_type(e))
                self._fail_container(context, container, six.text_type(e))
        except exception.DockerError as e:
            with excutils.save_and_reraise_exception():
                LOG.error("Error occurred while calling Docker image API: %s",
                          six.text_type(e))
                self._fail_container(context, container, six.text_type(e))
        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.exception("Unexpected exception: %s",
                              six.text_type(e))
                self._fail_container(context, container, six.text_type(e))

        container.task_state = consts.CONTAINER_CREATING
        container.image_driver = image.get('driver')
        container.save(context)
        try:
            if image['driver'] == 'glance':
                self.driver.read_tar_image(image)
            if image['tag'] != tag:
                LOG.warning("The input tag is different from the tag in tar")
            if isinstance(container, objects.Capsule):
                container = self.driver.create_capsule(context, container,
                                                       image,
                                                       requested_networks,
                                                       requested_volumes)
            elif isinstance(container, objects.Container):
                container = self.driver.create(context, container, image,
                                               requested_networks,
                                               requested_volumes)
            self._update_task_state(context, container, None)
            return container
        except exception.DockerError as e:
            with excutils.save_and_reraise_exception():
                LOG.error("Error occurred while calling Docker create API: %s",
                          six.text_type(e))
                self._fail_container(context, container, six.text_type(e),
                                     unset_host=True)
        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.exception("Unexpected exception: %s",
                              six.text_type(e))
                self._fail_container(context, container, six.text_type(e),
                                     unset_host=True)

        
```



调用container/docker/dirver.py 创建docker







zun-compute 负责 container 创建，代码位于 zun/compute/manager.py，过程如下:



1. wait for volumes avaiable: 等待 volume 创建完成，状态变为 avaiable。
2. attach volumes：挂载 volumes，挂载过程后面再介绍。
3. checksupportdisk_quota: 如果使用本地盘，检查本地的 quota 配额。
4. pull or load image: 调用 Docker 拉取或者加载镜像。
5. 创建 docker network、创建 neutron port，这个步骤下面详细介绍。
6. create container: 调用 Docker 创建容器。
7. container start: 调用 Docker 启动容器。



以上调用 Dokcer 拉取镜像、创建容器、启动容器的代码位于 zun/container/docker/driver.py，该模块基本就是对社区 Docker SDK for Python 的封装。