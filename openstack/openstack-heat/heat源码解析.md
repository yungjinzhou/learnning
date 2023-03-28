# heat源码解析



## 资源类型

**对基础架构的编排**

对于不同的资源，Heat 都提供了对应的资源类型。比如对于VM，Heat 提供了OS::Nova::Server。OS::Nova::Server 有一些参数，比如key、image、flavor 等，这些参数可以直接指定，可以由客户在创建Stack 时提供，也可以由上下文其它的参数获得。创建一个VM的部分模板如下:

```
resources:
  server:
    type: OS::Nova::Server
    properties:
      key＿name: ｛ get＿param: key＿name ｝
      image: ｛ get＿param: image ｝
      flavor: ｛ get＿param: flavor ｝
      user＿data: ｜
       ＃！/bin/bash
       echo “10.10.10.10 testvm”＞＞ /etc/hosts
```

在上面创建VM 的例子中，我们选择从输入参数获得OS::Nova::Server 所需的值。其中利用user＿data 做了一些简单的配置。

**对软件配置和部署的编排**

Heat提供了多种资源类型来支持对于软件配置和部署的编排，如下所列:
OS::Heat::CloudConfig:VM 引导程序启动时的配置，由OS::Nova::Server 引用
OS::Heat::SoftwareConfig:描述软件配置
OS::Heat::SoftwareDeployment:执行软件部署
OS::Heat::SoftwareDeploymentGroup:对一组VM 执行软件部署
OS::Heat::SoftwareComponent:针对软件的不同生命周期部分，对应描述软件配置
OS::Heat::StructuredConfig:和OS::Heat::SoftwareConfig 类似，但是用Map 来表述配置
OS::Heat::StructuredDeployment:执行OS::Heat::StructuredConfig 对应的配置
OS::Heat::StructuredDeploymentsGroup:对一组VM 执行OS::Heat::StructuredConfig 对应的配置

其中最常用的是OS::Heat::SoftwareConfig 和OS::Heat::SoftwareDeployment。

**OS::Heat::SoftwareConfig**

下面是OS::Heat::SoftwareConfig 的用法，它指定了配置细节。

```
resources:  install＿db＿sofwareconfig
  type: OS::Heat::SoftwareConfig
  properties:
    group: script
  outputs:
   － name: result
  config: ｜
    ＃！/bin/bash －v
    yum －y install mariadb mariadb－server httpd [WordPress](https://www.ucloud.cn/yun/tag/WordPress/)
    touch /var/log/mariadb/mariadb.log
    chown mysql.mysql /var/log/mariadb/mariadb.log
    systemctl start mariadb.service
```



**OS::Heat::SoftwareDeployment**

下面是OS::Heat::SoftwareDeployment 的用法，它指定了在哪台服务器上做哪项配置。另外SofwareDeployment 也指定了以何种信号传输类型来和Heat 进行通信。

```
sw＿deployment:
type: OS::Heat::SoftwareDeployment
properties:
config: { get＿resource: install＿db＿sofwareconfig }
server: { get＿resource: server }
signal＿transport: HEAT＿SIGNAL
```



**OS::Heat::SoftwareConfig 和OS::Heat::SoftwareDeployment 执行流程**

OS::Heat::SoftwareConfig和OS::Heat::SoftwareDeployment协同工作，需要一系列Heat工具的自持。这些工具都是OpenStack的子项目。
首先，os－collect－config调用Heat API拿到对应VM的metadata。当metadata更新完毕后os－refresh－config开始工作了，它主要是运行下面目录所包含的脚本:

```
/opt/stack/os－config－refresh/pre－configure.d
/opt/stack/os－config－refresh/configure.d
/opt/stack/os－config－refresh/post－configure.d
/opt/stack/os－config－refresh/migration.d
/opt/stack/os－config－refresh/error.d
```

每个文件夹都应对了软件不同的阶段，比如预先配置阶段、配置阶段、后配置阶段和迁移阶段。如果任一阶段的脚本执行出现问题，它会运行error.d目录里的错误处理脚本。os－refresh－config 在配置阶段会调用一定预先定义的工具，比如heat－config，这样就触发了heat－config的应用，调用完heat－config后，又会调用os－apply－config。存在在heat－config或者os－apply－config里的都是一些脚本，也叫钩子。Heat对于各种不同的工具提供了不同的钩子脚本。用户也可以自己定义这样的脚本。

等一切调用完成无误后，heat－config－notify 会被调用，它用来发信号给Heat，告诉这个软件部署的工作已经完成。当Heat 收到heat－config－notify 发来的信号后，它会把OS::Heat::SoftwareConfig 对应资源的状态改为Complete。如果有任何错误发生，就会改为CREATE＿FAILED 状态。

**OS::Heat::SoftwareConfig 和OS::Heat::SoftwareDeployment 执行流程如下:**

![深度解码超实用的OpenStack Heat](.\1554185458727023821.jpg)





## heat源码解析

在magnum中调用heatclient ，向heatapi发送请求，请求连接：http://controller:8004/v1/b5a1eb4ee8374fa1aa88cd4b59afda98/stacks，下面对heat代码进行解析

### heatapi入口

```
heat-api入口
heat/api/openstack/v1/__init__.py


创建stack代码位置
/usr/lib/python2.7/site-packages/heat/api/openstack/v1/stacks.py(402)create()

    @util.registered_policy_enforce
    def create(self, req, body):
        """Create a new stack."""
        data = InstantiationData(body)

        args = self.prepare_args(data)
        result = self.rpc_client.create_stack(
            req.context,
            data.stack_name(),
            data.template(),
            data.environment(),
            data.files(),
            args,
            environment_files=data.environment_files(),
            files_container=data.files_container())

        formatted_stack = stacks_view.format_stack(
            req,
            {rpc_api.STACK_ID: result}
        )
        return {'stack': formatted_stack}





```

### rpc传给heat-engine

调用rpc_client发送到heat-engine服务

```
# heat/rpc/client.py  
class EngineClient(object):
    BASE_RPC_API_VERSION = '1.0'
    
  	# 。。。。。。省略部分代码
    def create_stack(self, ctxt, stack_name, template, params, files,
                     args, environment_files=None, files_container=None):
        """Creates a new stack using the template provided.

        Note that at this stage the template has already been fetched from the
        heat-api process if using a template-url.

        :param ctxt: RPC context.
        :param stack_name: Name of the stack you want to create.
        :param template: Template of stack you want to create.
        :param params: Stack Input Params/Environment
        :param files: files referenced from the environment.
        :param args: Request parameters/args passed from API
        :param environment_files: optional ordered list of environment file
               names included in the files dict
        :type  environment_files: list or None
        :param files_container: name of swift container
        """
        return self._create_stack(ctxt, stack_name, template, params, files,
                                  args, environment_files=environment_files,
                                  files_container=files_container)

    def _create_stack(self, ctxt, stack_name, template, params, files,
                      args, environment_files=None, files_container=None,
                      owner_id=None, nested_depth=0, user_creds_id=None,
                      stack_user_project_id=None, parent_resource_name=None,
                      template_id=None):
        """Internal interface for engine-to-engine communication via RPC.

        Allows some additional options which should not be exposed to users via
        the API:

        :param owner_id: parent stack ID for nested stacks
        :param nested_depth: nested depth for nested stacks
        :param user_creds_id: user_creds record for nested stack
        :param stack_user_project_id: stack user project for nested stack
        :param parent_resource_name: the parent resource name
        :param template_id: the ID of a pre-stored template in the DB
        """
        return self.call(
            ctxt, self.make_msg('create_stack', stack_name=stack_name,
                                template=template,
                                params=params, files=files,
                                environment_files=environment_files,
                                files_container=files_container,
                                args=args, owner_id=owner_id,
                                nested_depth=nested_depth,
                                user_creds_id=user_creds_id,
                                stack_user_project_id=stack_user_project_id,
                                parent_resource_name=parent_resource_name,
                                template_id=template_id),
            version='1.36')
```

### engine接收create_task方法

create_task由engine接收

```
# /usr/lib/python2.7/site-packages/heat/engine/service.py(827)create_stack()

@profiler.trace_cls("rpc")
class EngineService(service.ServiceBase):
    """Manages the running instances from creation to destruction.

	# ...... 省略部分代码
    @context.request_context
    def create_stack(self, cnxt, stack_name, template, params, files,
                     args, environment_files=None,
                     files_container=None, owner_id=None,
                     nested_depth=0, user_creds_id=None,
                     stack_user_project_id=None, parent_resource_name=None,
                     template_id=None):
        """Create a new stack using the template provided.

        Note that at this stage the template has already been fetched from the
        heat-api process if using a template-url.

        :param cnxt: RPC context.
        :param stack_name: Name of the stack you want to create.
        :param template: Template of stack you want to create.
        :param params: Stack Input Params
        :param files: Files referenced from the template
        :param args: Request parameters/args passed from API
        :param environment_files: optional ordered list of environment file
               names included in the files dict
        :type  environment_files: list or None
        :param files_container: optional swift container name
        :param owner_id: parent stack ID for nested stacks, only expected when
                         called from another heat-engine (not a user option)
        :param nested_depth: the nested depth for nested stacks, only expected
                         when called from another heat-engine
        :param user_creds_id: the parent user_creds record for nested stacks
        :param stack_user_project_id: the parent stack_user_project_id for
                         nested stacks
        :param parent_resource_name: the parent resource name
        :param template_id: the ID of a pre-stored template in the DB
        """
        LOG.info('Creating stack %s', stack_name)

        def _create_stack_user(stack):
            if not stack.stack_user_project_id:
                try:
                    stack.create_stack_user_project_id()
                except exception.AuthorizationFailure as ex:
                    stack.state_set(stack.action, stack.FAILED,
                                    str(ex))

        def _stack_create(stack, msg_queue=None):
            # Create/Adopt a stack, and create the periodic task if successful
            if stack.adopt_stack_data:
                stack.adopt()
            elif stack.status != stack.FAILED:
                stack.create(msg_queue=msg_queue)

        convergence = cfg.CONF.convergence_engine

        stack = self._parse_template_and_validate_stack(
            cnxt, stack_name, template, params, files, environment_files,
            files_container, args, owner_id, nested_depth,
            user_creds_id, stack_user_project_id, convergence,
            parent_resource_name, template_id)

        stack_id = stack.store()
        if cfg.CONF.reauthentication_auth_method == 'trusts':
            stack = parser.Stack.load(
                cnxt, stack_id=stack_id, use_stored_context=True)
        _create_stack_user(stack)
        if convergence:
            action = stack.CREATE
            if stack.adopt_stack_data:
                action = stack.ADOPT
            stack.thread_group_mgr = self.thread_group_mgr
            stack.converge_stack(template=stack.t, action=action)
        else:
            msg_queue = eventlet.queue.LightQueue()
            th = self.thread_group_mgr.start_with_lock(cnxt, stack,
                                                       self.engine_id,
                                                       _stack_create, stack,
                                                       msg_queue=msg_queue)
            th.link(self.thread_group_mgr.remove_msg_queue,
                    stack.id, msg_queue)
            self.thread_group_mgr.add_msg_queue(stack.id, msg_queue)

        return dict(stack.identifier())



```

#### 调用converge_stack

convergence   openstack N版本后，默认convergence=Ture

```
/usr/lib/python2.7/site-packages/heat/engine/stack.py(1344)converge_stack()

    
    @profiler.trace('Stack.converge_stack', hide_args=False)
    @reset_state_on_error
    def converge_stack(self, template, action=UPDATE, new_stack=None,
                       pre_converge=None):
        """Update the stack template and trigger convergence for resources."""
        if action not in [self.CREATE, self.ADOPT]:
            # no back-up template for create action
            self.prev_raw_template_id = getattr(self.t, 'id', None)

        # switch template and reset dependencies
        self.defn = self.defn.clone_with_new_template(template,
                                                      self.identifier(),
                                                      clear_resource_data=True)
        self.reset_dependencies()
        self._resources = None

        if action != self.CREATE:
            self.updated_time = oslo_timeutils.utcnow()

        if new_stack is not None:
            self.disable_rollback = new_stack.disable_rollback
            self.timeout_mins = new_stack.timeout_mins
            self.converge = new_stack.converge

            self.defn = new_stack.defn
            self._set_param_stackid()

            self.tags = new_stack.tags

        self.action = action
        self.status = self.IN_PROGRESS
        self.status_reason = 'Stack %s started' % self.action

        # generate new traversal and store
        previous_traversal = self.current_traversal
        self.current_traversal = uuidutils.generate_uuid()
        # we expect to update the stack having previous traversal ID
        stack_id = self.store(exp_trvsl=previous_traversal)
        if stack_id is None:
            LOG.warning("Failed to store stack %(name)s with traversal "
                        "ID %(trvsl_id)s, aborting stack %(action)s",
                        {'name': self.name, 'trvsl_id': previous_traversal,
                         'action': self.action})
            return
        self._send_notification_and_add_event()

        # delete the prev traversal sync_points
        if previous_traversal:
            sync_point.delete_all(self.context, self.id, previous_traversal)

        # TODO(later): lifecycle_plugin_utils.do_pre_ops

        self.thread_group_mgr.start(self.id, self._converge_create_or_update,
                                    pre_converge=pre_converge)

    @reset_state_on_error
    def _converge_create_or_update(self, pre_converge=None):
        current_resources = self._update_or_store_resources()
        self._compute_convg_dependencies(self.ext_rsrcs_db, self.dependencies,
                                         current_resources)
        # Store list of edges
        self.current_deps = {
            'edges': [[rqr, rqd] for rqr, rqd in
                      self.convergence_dependencies.graph().edges()]}
        stack_id = self.store()
        if stack_id is None:
            # Failed concurrent update
            LOG.warning("Failed to store stack %(name)s with traversal "
                        "ID %(trvsl_id)s, aborting stack %(action)s",
                        {'name': self.name, 'trvsl_id': self.current_traversal,
                         'action': self.action})
            return

        if callable(pre_converge):
            pre_converge()
        if self.action == self.DELETE:
            try:
                self.delete_all_snapshots()
            except Exception as exc:
                self.state_set(self.action, self.FAILED, str(exc))
                self.purge_db()
                return

        LOG.debug('Starting traversal %s with dependencies: %s',
                  self.current_traversal, self.convergence_dependencies)

        # create sync_points for resources in DB
        for rsrc_id, is_update in self.convergence_dependencies:
            sync_point.create(self.context, rsrc_id,
                              self.current_traversal, is_update,
                              self.id)
        # create sync_point entry for stack
        sync_point.create(
            self.context, self.id, self.current_traversal, True, self.id)

        leaves = set(self.convergence_dependencies.leaves())
        if not leaves:
            self.mark_complete()
        else:
            for rsrc_id, is_update in sorted(leaves,
                                             key=lambda n: n.is_update):
                if is_update:
                    LOG.info("Triggering resource %s for update", rsrc_id)
                else:
                    LOG.info("Triggering resource %s for cleanup",
                             rsrc_id)
                input_data = sync_point.serialize_input_data({})
                self.worker_client.check_resource(self.context, rsrc_id,
                                                  self.current_traversal,
                                                  input_data, is_update,
                                                  self.adopt_stack_data,
                                                  self.converge)
                if scheduler.ENABLE_SLEEP:
                    eventlet.sleep(1)

```







        #(Pdb) current_resources 
        {
        u'etcd_lb': <heat.engine.resources.template_resource.TemplateResource object at 0x7f47e2dd84d0>, 
        u'secgroup_rule_tcp_kube_minion': <heat.engine.resources.openstack.neutron.security_group_rule.SecurityGroupRule object at 0x7f47e2d9ac10>, 
        u'kube_masters': <heat.engine.resources.openstack.heat.resource_group.ResourceGroup object at 0x7f47e2da0850>, 
        u'kube_cluster_config': <heat.engine.resources.openstack.heat.software_config.SoftwareConfig object at 0x7f47e36887d0>, 
        u'secgroup_kube_master': <heat.engine.resources.openstack.neutron.security_group.SecurityGroup object at 0x7f47e2d9ac50>, 
        u'secgroup_kube_minion': <heat.engine.resources.openstack.neutron.security_group.SecurityGroup object at 0x7f47e2e09690>, 
        u'api_lb': <heat.engine.resources.template_resource.TemplateResource object at 0x7f47e2de16d0>, 
        u'master_nodes_server_group': <heat.engine.resources.openstack.nova.server_group.ServerGroup object at 0x7f47e2e36b50>, 
        u'etcd_address_lb_switch': <heat.engine.resources.template_resource.TemplateResource object at 0x7f47e2d9a790>, 
        u'kube_cluster_deploy': <heat.engine.resources.openstack.heat.software_deployment.SoftwareDeployment object at 0x7f47e3e527d0>, 
        u'kube_minions': <heat.engine.resources.openstack.heat.resource_group.ResourceGroup object at 0x7f47e2ded3d0>, 
        u'api_address_floating_switch': <heat.engine.resources.template_resource.TemplateResource object at 0x7f47e34f8dd0>, 
        u'worker_nodes_server_group': <heat.engine.resources.openstack.nova.server_group.ServerGroup object at 0x7f47e3500850>, 
        u'api_address_lb_switch': <heat.engine.resources.template_resource.TemplateResource object at 0x7f47e34f8150>, 
        u'secgroup_rule_udp_kube_minion': <heat.engine.resources.openstack.neutron.security_group_rule.SecurityGroupRule object at 0x7f47e2da8b50>, 
        u'network': <heat.engine.resources.template_resource.TemplateResource object at 0x7f47e2d9a990>}



#### 调用check_resource

worker_client.check_resource具体调用

```
# heat/engine/worker.py


    @context.request_context
    @log_exceptions
    def check_resource(self, cnxt, resource_id, current_traversal, data,
                       is_update, adopt_stack_data, converge=False):
        """Process a node in the dependency graph.

        The node may be associated with either an update or a cleanup of its
        associated resource.
        """
        in_data = sync_point.deserialize_input_data(data)
        resource_data = node_data.load_resources_data(in_data if is_update
                                                      else {})
        # rsource_data: {u'kube_master_eth0': <heat.engine.node_data.NodeData object at 0x7f2881f5d328>, u'kube_master_init': <heat.engine.node_data.NodeData object at 0x7f2881f5db48>}
        rsrc, stk_defn, stack = check_resource.load_resource(cnxt, resource_id,
                                                             resource_data,
                                                             current_traversal,
                                                             is_update)

        if rsrc is None:
            return

        rsrc.converge = converge

        msg_queue = eventlet.queue.LightQueue()
        try:
            self.thread_group_mgr.add_msg_queue(stack.id, msg_queue)
            cr = check_resource.CheckResource(self.engine_id,
                                              self._rpc_client,
                                              self.thread_group_mgr,
                                              msg_queue, in_data)
            if current_traversal != stack.current_traversal:
                LOG.debug('[%s] Traversal cancelled; re-trigerring.',
                          current_traversal)
                self._retrigger_replaced(is_update, rsrc, stack, cr)
            else:
                cr.check(cnxt, resource_id, current_traversal, resource_data,
                         is_update, adopt_stack_data, rsrc, stack)
        finally:
            self.thread_group_mgr.remove_msg_queue(None,
                                                   stack.id, msg_queue)
```

#### 调用check

cr = check_resource.CheckResource结合 cr.check

调用checkResource类的check方法

```
# heat/engine/check_resource.py

    def check(self, cnxt, resource_id, current_traversal,
              resource_data, is_update, adopt_stack_data,
              rsrc, stack):
        """Process a node in the dependency graph.

        The node may be associated with either an update or a cleanup of its
        associated resource.
        """
        if stack.has_timed_out():
            self._handle_stack_timeout(cnxt, stack)
            return

        tmpl = stack.t
        stack.adopt_stack_data = adopt_stack_data
        stack.thread_group_mgr = self.thread_group_mgr

        try:
            check_resource_done = self._do_check_resource(cnxt,
                                                          current_traversal,
                                                          tmpl, resource_data,
                                                          is_update,
                                                          rsrc, stack,
                                                          adopt_stack_data)

            if check_resource_done:
                # initiate check on next set of resources from graph
                self._initiate_propagate_resource(cnxt, resource_id,
                                                  current_traversal, is_update,
                                                  rsrc, stack)
        except BaseException as exc:
            with excutils.save_and_reraise_exception():
                msg = six.text_type(exc)
                LOG.exception("Unexpected exception in resource check.")
                self._handle_resource_failure(cnxt, is_update, rsrc.id,
                                              stack, msg)


```

#### create_convergence

调用do_check_resource，最终调用create_convergence方法

```
# heat/engine/check_resource.py

def check_resource_update(rsrc, template_id, requires, engine_id,
                          stack, msg_queue):
    """Create or update the Resource if appropriate."""
    check_message = functools.partial(_check_for_message, msg_queue)
    if rsrc.action == resource.Resource.INIT:
        rsrc.create_convergence(template_id, requires, engine_id,
                                stack.time_remaining(), check_message)
    else:
        rsrc.update_convergence(template_id, requires, engine_id,
                                stack.time_remaining(), stack,
                                check_message)
```



调用 resource.py中 create_convergence方法

```
# heat/engine/resource.py


    
     def create_convergence(self, template_id, requires, engine_id,
                           timeout, progress_callback=None):
        """Creates the resource by invoking the scheduler TaskRunner."""
        self._calling_engine_id = engine_id
        self.requires = requires
        self.current_template_id = template_id
        if self.stack.adopt_stack_data is None:
            runner = scheduler.TaskRunner(self.create)
        else:
            adopt_data = self.stack._adopt_kwargs(self)
            runner = scheduler.TaskRunner(self.adopt, **adopt_data)

        runner(timeout=timeout, progress_callback=progress_callback)
```

#### 调度创建任务



```
# heat/engine/resource.py

    @scheduler.wrappertask
    def create(self):
        """Create the resource.

        Subclasses should provide a handle_create() method to customise
        creation.
        """
        action = self.CREATE
        if (self.action, self.status) != (self.INIT, self.COMPLETE):
            exc = exception.Error(_('State %s invalid for create')
                                  % six.text_type(self.state))
            raise exception.ResourceFailure(exc, self, action)

        if self.external_id is not None:
            yield self._do_action(self.ADOPT,
                                  resource_data={
                                      'resource_id': self.external_id})
            self.check()
            return

        # This method can be called when we replace a resource, too. In that
        # case, a hook has already been dealt with in `Resource.update` so we
        # shouldn't do it here again:
        if self.stack.action == self.stack.CREATE:
            yield self._break_if_required(
                self.CREATE, environment.HOOK_PRE_CREATE)

        LOG.info('creating %s', self)

        # Re-resolve the template, since if the resource Ref's
        # the StackId pseudo parameter, it will change after
        # the parser.Stack is stored (which is after the resources
        # are __init__'d, but before they are create()'d). We also
        # do client lookups for RESOLVE translation rules here.

        self.reparse()
        self._update_stored_properties()

        count = {self.CREATE: 0, self.DELETE: 0}

        retry_limit = max(cfg.CONF.action_retry_limit, 0)
        first_failure = None

        while (count[self.CREATE] <= retry_limit and
               count[self.DELETE] <= retry_limit):
            pre_func = None
            if count[action] > 0:
                delay = timeutils.retry_backoff_delay(count[action],
                                                      jitter_max=2.0)
                waiter = scheduler.TaskRunner(self.pause)
                yield waiter.as_task(timeout=delay)
            elif action == self.CREATE:
                # Only validate properties in first create call.
                pre_func = self.properties.validate

            try:
                yield self._do_action(action, pre_func)
                if action == self.CREATE:
                    first_failure = None
                    break
                else:
                    action = self.CREATE
            except exception.ResourceFailure as failure:
                exc = failure.exc
                if isinstance(exc, exception.StackValidationFailed):
                    path = [self.t.name]
                    path.extend(exc.path)
                    raise exception.ResourceFailure(
                        exception_or_error=exception.StackValidationFailed(
                            error=exc.error,
                            path=path,
                            message=exc.error_message
                        ),
                        resource=failure.resource,
                        action=failure.action
                    )
                if not (isinstance(exc, exception.ResourceInError) or
                        self._default_client_plugin().is_conflict(exc)):
                    raise failure

                count[action] += 1
                if action == self.CREATE:
                    action = self.DELETE
                    count[action] = 0

                if first_failure is None:
                    # Save the first exception
                    first_failure = failure

        if first_failure:
            raise first_failure

        if self.stack.action == self.stack.CREATE:
            yield self._break_if_required(
                self.CREATE, environment.HOOK_POST_CREATE)

```

























## magnum创建cluster到请求heat的代码分析









```

2023-01-06 17:12:18.257 155917 INFO heat.engine.service [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] Creating stack on-delte-v2-lm47gfxm2pr4


2023-01-06 17:12:18.296 155921 INFO heat.engine.resource [req-55545d88-319a-4f51-b661-32eb6757c2ba - admin - default default] deleting NoneResource "etcd_volume_attach" [81c77cc8-d88a-4cd0-b778-90cd41b7cb71] Stack "on-delte-v1-o7gxrubzbkhl-kube_masters-bhntcum7mzrs-0-5wccfz57k6y3" [a3ee5aa0-5a87-4f09-ba73-622bad7d9a9f]


2023-01-06 17:12:19.075 155917 INFO heat.engine.environment [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] on-delte-v2-lm47gfxm2pr4 Registered: [Template](User:True) Magnum::ApiGatewaySwitcher -> file:///usr/lib/python2.7/site-packages/magnum/drivers/common/templates/fragments/api_gateway_switcher_master.yaml



2023-01-06 17:12:19.076 155917 INFO heat.engine.environment [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] on-delte-v2-lm47gfxm2pr4 Registered: [Template](User:True) file:///usr/lib/python2.7/site-packages/magnum/drivers/k8s_centos_v1/templates/kubeminion.yaml -> file:///usr/lib/python2.7/site-packages/magnum/drivers/k8s_centos_v1/templates/kubeminion.yaml


2023-01-06 17:12:19.076 155917 INFO heat.engine.environment [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] on-delte-v2-lm47gfxm2pr4 Registered: [Template](User:True) file:///usr/lib/python2.7/site-packages/magnum/drivers/k8s_centos_v1/templates/kubemaster.yaml -> file:///usr/lib/python2.7/site-packages/magnum/drivers/k8s_centos_v1/templates/kubemaster.yaml



2023-01-06 17:12:20.022 155917 INFO heat.engine.service [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] --------convergence---True---
2023-01-06 17:12:20.022 155917 INFO heat.engine.stack [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] ---template---<heat.engine.hot.template.HOTemplate20141016 object at 0x7fcbd02bdb50>----




2023-01-06 17:12:20.022 155917 INFO heat.engine.service [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] --------convergence---True---
2023-01-06 17:12:20.022 155917 INFO heat.engine.stack [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] ---template---<heat.engine.hot.template.HOTemplate20141016 object at 0x7fcbd02bdb50>----
2023-01-06 17:12:20.026 155917 INFO heat.engine.stack [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] ---defn---<heat.engine.stk_defn.StackDefinition object at 0x7fcbcfdabd90>----




2023-01-06 17:12:20.520 155908 INFO heat.engine.stack [req-ddff843c-7886-42a8-a610-b36d2b6ae7cf - - - - -] --------------self.thread_group_mgr: <heat.engine.service.ThreadGroupManager object at 0x7fcbd07dc450>----
2023-01-06 17:12:20.648 155908 INFO heat.engine.stack [req-ddff843c-7886-42a8-a610-b36d2b6ae7cf - - - - -] Triggering resource 3701 for update
2023-01-06 17:12:20.686 155921 INFO heat.engine.resource [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] creating NoneResource "extrouter" Stack "on-delte-v2-lm47gfxm2pr4-network-gfk4bf3dl62d" [d80f9a2d-65e2-4219-a485-9296e8d17cc1]
2023-01-06 17:12:21.369 155917 INFO heat.engine.stack [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] Triggering resource 3695 for update
2023-01-06 17:12:21.417 155917 INFO heat.engine.resource [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] creating ServerGroup "master_nodes_server_group" Stack "on-delte-v2-lm47gfxm2pr4" [19dbd9b5-a2ba-42c3-8eb4-ce18f9ee8eaf]
2023-01-06 17:12:21.651 155908 INFO heat.engine.stack [req-ddff843c-7886-42a8-a610-b36d2b6ae7cf - - - - -] Triggering resource 3705 for update
2023-01-06 17:12:21.678 155908 INFO heat.engine.resource [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] creating NoneResource "private_network" Stack "on-delte-v2-lm47gfxm2pr4-network-gfk4bf3dl62d" [d80f9a2d-65e2-4219-a485-9296e8d17cc1]
2023-01-06 17:12:21.781 155911 INFO heat.engine.resource [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] creating NoneResource "private_subnet" Stack "on-delte-v2-lm47gfxm2pr4-network-gfk4bf3dl62d" [d80f9a2d-65e2-4219-a485-9296e8d17cc1]
2023-01-06 17:12:21.870 155921 INFO heat.engine.resource [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] creating NoneResource "extrouter_inside" Stack "on-delte-v2-lm47gfxm2pr4-network-gfk4bf3dl62d" [d80f9a2d-65e2-4219-a485-9296e8d17cc1]
2023-01-06 17:12:21.880 155917 INFO heat.engine.resource [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] creating TemplateResource "network_switch" Stack "on-delte-v2-lm47gfxm2pr4-network-gfk4bf3dl62d" [d80f9a2d-65e2-4219-a485-9296e8d17cc1]
2023-01-06 17:12:21.909 155917 INFO heat.engine.service [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] Creating stack on-delte-v2-lm47gfxm2pr4-network-gfk4bf3dl62d-network_switch-bgq5nou6ytcn





2023-01-06 17:12:21.909 155917 INFO heat.engine.service [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] Creating stack on-delte-v2-lm47gfxm2pr4-network-gfk4bf3dl62d-network_switch-bgq5nou6ytcn
2023-01-06 17:12:21.930 155917 INFO heat.engine.service [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] --------convergence---True---
2023-01-06 17:12:21.931 155917 INFO heat.engine.stack [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] ---template---<heat.engine.hot.template.HOTemplate20141016 object at 0x7fcbcfd36a50>----
2023-01-06 17:12:21.932 155917 INFO heat.engine.stack [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] ---defn---<heat.engine.stk_defn.StackDefinition object at 0x7fcbcfc85710>----
2023-01-06 17:12:21.949 155917 INFO heat.engine.stack [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] --------------self.id: ee5f35ae-8346-4947-9007-fa423ce7fa86----
2023-01-06 17:12:21.949 155917 INFO heat.engine.stack [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] --------------self.thread_group_mgr: <heat.engine.service.ThreadGroupManager object at 0x7fcbd07dc450>----
2023-01-06 17:12:21.976 155917 INFO heat.engine.stack [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] [on-delte-v2-lm47gfxm2pr4-network-gfk4bf3dl62d-network_switch-bgq5nou6ytcn(ee5f35ae-8346-4947-9007-fa423ce7fa86)] update traversal 40857fa2-d889-45f1-ac08-b41476603367 complete
2023-01-06 17:12:21.977 155917 INFO heat.engine.stack [req-7788c1d7-e4c0-4e72-8ffb-088f94ead510 - admin - default default] Stack CREATE COMPLETE (on-delte-v2-lm47gfxm2pr4-network-gfk4bf3dl62d-network_switch-bgq5nou6ytcn): Stack CREATE completed successfully


```













