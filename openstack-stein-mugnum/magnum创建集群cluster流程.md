# magnum创建集群cluster流程





创建cluster  

controller:9511/v1/clusters



```
/usr/lib/python2.7/site-packages/magnum/api/controllers/v1/cluster.py(454)post()

class ClustersController(base.Controller):

	........省略部分代码
    @expose.expose(ClusterID, body=Cluster, status_code=202)
    @validation.enforce_cluster_type_supported()
    @validation.enforce_cluster_volume_storage_size()
    def post(self, cluster):
        """Create a new cluster.

        :param cluster: a cluster within the request body.
        """
        context = pecan.request.context
        policy.enforce(context, 'cluster:create',
                       action='cluster:create')

        self._check_cluster_quota_limit(context)

        temp_id = cluster.cluster_template_id
        cluster_template = objects.ClusterTemplate.get_by_uuid(context,
                                                               temp_id)
        # If keypair not present, use cluster_template value
        if cluster.keypair is None:
            cluster.keypair = cluster_template.keypair_id

        # If docker_volume_size is not present, use cluster_template value
        if (cluster.docker_volume_size == wtypes.Unset or
                not cluster.docker_volume_size):
            cluster.docker_volume_size = cluster_template.docker_volume_size

        # If labels is not present, use cluster_template value
        if cluster.labels == wtypes.Unset:
            cluster.labels = cluster_template.labels

        # If master_flavor_id is not present, use cluster_template value
        if (cluster.master_flavor_id == wtypes.Unset or
                not cluster.master_flavor_id):
            cluster.master_flavor_id = cluster_template.master_flavor_id

        # If flavor_id is not present, use cluster_template value
        if cluster.flavor_id == wtypes.Unset or not cluster.flavor_id:
            cluster.flavor_id = cluster_template.flavor_id

        cluster_dict = cluster.as_dict()

        attr_validator.validate_os_resources(context,
                                             cluster_template.as_dict(),
                                             cluster_dict)
        attr_validator.validate_master_count(cluster_dict,
                                             cluster_template.as_dict())

        cluster_dict['project_id'] = context.project_id
        cluster_dict['user_id'] = context.user_id
        # NOTE(yuywz): We will generate a random human-readable name for
        # cluster if the name is not specified by user.
        name = cluster_dict.get('name') or \
            self._generate_name_for_cluster(context)
        cluster_dict['name'] = name
        cluster_dict['coe_version'] = None
        cluster_dict['container_version'] = None

        new_cluster = objects.Cluster(context, **cluster_dict)
        new_cluster.uuid = uuid.uuid4()
        pecan.request.rpcapi.cluster_create_async(new_cluster,
                                                  cluster.create_timeout)

		# pecan.request.rpcapi:  <magnum.conductor.api.API object at 0x7f3781858790>
        return ClusterID(new_cluster.uuid)

```

代码参数详情

```
context:

{'service_user_domain_name': None, 'service_user_id': None, 'auth_token': 'gAAAAABhS89-cW5E4Y8s2OP7Tun9Ip8dBx8FwYFPyx9CmA2mMI5o6L4D8IeEULNmf8_q0UYj-cK8Q5CjdAntZTyNELWsA3cr-HgfImS0v9oSVon2_FfGpDqE77EcJk-5sk8YCNAfZjN-VEdWkoYtxv9WH1uSRc_nzzpy2ZWH7JUDVcn6C3hS9zW4eMF4isUZI5jS-UmFEUPy', '_user_domain_id': None, 'resource_uuid': None, 'auth_url': 'http://192.168.204.173:5000/v3', 'service_project_domain_name': None, 'trust_id': None, 'read_only': False, 'system_scope': None, 'service_token': None, 'service_project_name': None, 'domain_name': u'Default', 'is_admin_project': True, 'service_user_name': None, 'user_name': u'admin', 'user_domain_name': None, '_user_id': u'03b0360129f84f9790081df4cebf7844', 'project_domain_name': None, 'project_name': u'admin', 'global_request_id': None, 'service_project_id': None, 'service_project_domain_id': None, '_domain_id': u'default', 'is_admin': True, 'password': None, 'all_tenants': False, 'service_roles': [], 'show_deleted': False, 'roles': [u'admin', u'member', u'reader'], 'service_user_domain_id': None, 'auth_token_info': {u'token': {u'is_domain': False, u'methods': [u'token', u'password'], u'roles': [{u'id': u'8d83eac688a24848add64594e0ca2e97', u'name': u'admin'}, {u'id': u'b476263657d94c7b97cfddab7ed1c8e7', u'name': u'member'}, {u'id': u'919f0de7d1db4602979d7204251aea09', u'name': u'reader'}], u'auth_token': u'gAAAAABhS89-cW5E4Y8s2OP7Tun9Ip8dBx8FwYFPyx9CmA2mMI5o6L4D8IeEULNmf8_q0UYj-cK8Q5CjdAntZTyNELWsA3cr-HgfImS0v9oSVon2_FfGpDqE77EcJk-5sk8YCNAfZjN-VEdWkoYtxv9WH1uSRc_nzzpy2ZWH7JUDVcn6C3hS9zW4eMF4isUZI5jS-UmFEUPy', u'expires_at': u'2021-09-24T00:51:10.000000Z', u'project': {u'domain': {u'id': u'default', u'name': u'Default'}, u'id': u'b5a1eb4ee8374fa1aa88cd4b59afda98', u'name': u'admin'}, u'catalog': [{u'endpoints': [{u'url': u'http://192.168.204.173:9311', u'interface': u'public', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'1397ffbfd1ca41b381281a0ee2369440'}, {u'url': u'http://192.168.204.173:9311', u'interface': u'admin', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'2b8ad619de3446bb85a6074521bee2bb'}, {u'url': u'http://192.168.204.173:9311', u'interface': u'internal', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'bac6d7f630124d28a69e908b0bfb9a46'}], u'type': u'key-manager', u'id': u'0c38c80ab8234f15b5428d5e50d3184a', u'name': u'barbican'}, {u'endpoints': [{u'url': u'http://controller:8041', u'interface': u'admin', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'6ab1dbbf249a4d42a9fea119b6470d31'}, {u'url': u'http://controller:8041', u'interface': u'internal', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'7dcf1e2c86e84670af9316592f3eed88'}, {u'url': u'http://controller:8041', u'interface': u'public', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'ab597587c0ce49a8825110fed302d3bd'}], u'type': u'metric', u'id': u'21e3dbc1cc9b406f852c1ad42127afbd', u'name': u'gnocchi'}, {u'endpoints': [{u'url': u'http://192.168.204.173:8004/v1/b5a1eb4ee8374fa1aa88cd4b59afda98', u'interface': u'internal', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'18b68aa1900f4841874c5cdd757d334c'}, {u'url': u'http://192.168.204.173:8004/v1/b5a1eb4ee8374fa1aa88cd4b59afda98', u'interface': u'public', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'34d69c40167547d1bcf4ba96339a154b'}, {u'url': u'http://192.168.204.173:8004/v1/b5a1eb4ee8374fa1aa88cd4b59afda98', u'interface': u'admin', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'73b9c4c5f2b54dd4acaf9b9436ccdfe7'}], u'type': u'orchestration', u'id': u'605122cd5bc140f88106899683945f83', u'name': u'heat'}, {u'endpoints': [{u'url': u'http://192.168.204.173:8000/v1', u'interface': u'internal', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'a10e62ff3b7949f29e44754d1c5c3de5'}, {u'url': u'http://192.168.204.173:8000/v1', u'interface': u'admin', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'c2f47eb857814120bc148901f6106381'}, {u'url': u'http://192.168.204.173:8000/v1', u'interface': u'public', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'e7a4dee155054673a9301c261f3080b0'}], u'type': u'cloudformation', u'id': u'69a8d95c90734e57b9762dd3c1028478', u'name': u'heat-cfn'}, {u'endpoints': [{u'url': u'http://controller:8774/v2.1', u'interface': u'public', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'63af398c97b04456963bf2daffe2fdfe'}, {u'url': u'http://controller:8774/v2.1', u'interface': u'admin', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'90c3dd2c26c94346bc6055c59779ec58'}, {u'url': u'http://controller:8774/v2.1', u'interface': u'internal', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'd78558d917b0464db85030b71a649959'}], u'type': u'compute', u'id': u'7a42ef89a5cc4db5b69e6b175d4db6fc', u'name': u'nova'}, {u'endpoints': [{u'url': u'http://controller:9696', u'interface': u'admin', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'690803d4383d416680d2b31f32de5074'}, {u'url': u'http://controller:9696', u'interface': u'public', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'80396a4e143242e59003de7b72f26c41'}, {u'url': u'http://controller:9696', u'interface': u'internal', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'db7ddb9ef6e742528fdfdef58606c037'}], u'type': u'network', u'id': u'7ff3ded051c149ae9d4fbd9918164df5', u'name': u'neutron'}, {u'endpoints': [{u'url': u'http://192.168.204.173:9511/v1', u'interface': u'public', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'2fca7dd64416405c9501a2855050d465'}, {u'url': u'http://192.168.204.173:9511/v1', u'interface': u'admin', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'a4067347082b43418b20f2dd68da71dc'}, {u'url': u'http://192.168.204.173:9511/v1', u'interface': u'internal', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'b7f83e07c0e143edbb32ded3597e1849'}], u'type': u'container-infra', u'id': u'8a7b32264dfb4911a931d702e9ac84e2', u'name': u'magnum'}, {u'endpoints': [{u'url': u'http://controller:9517/v1', u'interface': u'public', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'4866531fcb854129bb682b38f03a72fb'}, {u'url': u'http://controller:9517/v1', u'interface': u'admin', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'd5b581b5af8840a9a8df34c7274fad8a'}, {u'url': u'http://controller:9517/v1', u'interface': u'internal', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'f77a4c3e541240b8bab9a734ba7af418'}], u'type': u'container', u'id': u'8e315c3e8d9a40578609fb1ea4cf72ca', u'name': u'zun'}, {u'endpoints': [{u'url': u'http://controller:8778', u'interface': u'public', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'108c6c4088074b5e9223a795db9c03ae'}, {u'url': u'http://controller:8778', u'interface': u'internal', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'8ae8aa0ed61f484eb28f949abc956999'}, {u'url': u'http://controller:8778', u'interface': u'admin', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'deecc3ce76864f8f97937463482e6f47'}], u'type': u'placement', u'id': u'942b9bfe4e0d4ab78c471e9c0c90406a', u'name': u'placement'}, {u'endpoints': [{u'url': u'http://controller:8776/v2/b5a1eb4ee8374fa1aa88cd4b59afda98', u'interface': u'public', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'138a88ac6aeb438c9de4edb533eb5890'}, {u'url': u'http://controller:8776/v2/b5a1eb4ee8374fa1aa88cd4b59afda98', u'interface': u'internal', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'2758d4be91444d478196768e72ad3967'}, {u'url': u'http://controller:8776/v2/b5a1eb4ee8374fa1aa88cd4b59afda98', u'interface': u'admin', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'596b79e909d0493eb446c126a5b12fb5'}], u'type': u'volumev2', u'id': u'a8d693525e42416fab514b92865fd605', u'name': u'cinderv2'}, {u'endpoints': [{u'url': u'http://:6385', u'interface': u'admin', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'60068aac878246dfa2056d364f1de441'}, {u'url': u'http://:6385', u'interface': u'internal', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'8933888c49ea4283a38df4703588720a'}, {u'url': u'http://:6385', u'interface': u'public', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'd93e812ae88548b0a55631c0fb43d960'}], u'type': u'baremetal', u'id': u'af8701b4f67d47d9843ca8637c4cdc32', u'name': u'ironic'}, {u'endpoints': [{u'url': u'http://controller:8776/v3/b5a1eb4ee8374fa1aa88cd4b59afda98', u'interface': u'admin', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'aec45dde67264ed6a3c14823d0f719c8'}, {u'url': u'http://controller:8776/v3/b5a1eb4ee8374fa1aa88cd4b59afda98', u'interface': u'public', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'c20888849f444cc5b296c5ec708e365a'}, {u'url': u'http://controller:8776/v3/b5a1eb4ee8374fa1aa88cd4b59afda98', u'interface': u'internal', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'c28d0e23000248bb8950db2dfae45075'}], u'type': u'volumev3', u'id': u'e3032206d2d34efd813e078c762e0c6a', u'name': u'cinderv3'}, {u'endpoints': [{u'url': u'http://controller:5000/v3/', u'interface': u'internal', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'0c9ccf3defa8498ca3e7a4c9b3e8ba65'}, {u'url': u'http://controller:5000/v3/', u'interface': u'admin', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'4b0f8306d3984a6fb54652c5eeb4c69a'}, {u'url': u'http://controller:5000/v3/', u'interface': u'public', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'bec1cd3c7dbf4169811e783126c6093c'}], u'type': u'identity', u'id': u'e786cc55a3894302a6a939c16b4080c9', u'name': u'keystone'}, {u'endpoints': [{u'url': u'http://controller:9292', u'interface': u'public', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'108adede98b840a98438b28bb78eb2bc'}, {u'url': u'http://controller:9292', u'interface': u'admin', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'3da1a54491704f4eb1f713323afd8d9d'}, {u'url': u'http://controller:9292', u'interface': u'internal', u'region': u'RegionOne', u'region_id': u'RegionOne', u'id': u'eaef84e516ee4901b6a44de04df40660'}], u'type': u'image', u'id': u'f256f4b3263545858f8e5246ee1e2886', u'name': u'glance'}], u'version': u'v3', u'user': {u'id': u'03b0360129f84f9790081df4cebf7844', u'domain': {u'id': u'default', u'name': u'Default'}, u'password_expires_at': None, u'name': u'admin'}, u'audit_ids': [u'SSCDkb94SoKTiRVqRp2uUA', u'ewE9z3hASCuPVIvN-DLkZQ'], u'issued_at': u'2021-09-23T00:51:10.000000Z'}}, 'request_id': 'req-aa5adfc5-9c57-4a86-b509-959a0c0d7129', '_project_id': u'b5a1eb4ee8374fa1aa88cd4b59afda98', '_project_domain_id': None}



new_cluster:
Cluster(api_address=<?>,ca_cert_ref=<?>,cluster_template=<?>,cluster_template_id='1b1742b0-0324-4eed-8ff8-6c0cd0af037c',coe_version=None,container_version=None,create_timeout=60,created_at=<?>,discovery_url=<?>,docker_volume_size=10,flavor_id='m1.small',health_status=<?>,health_status_reason=<?>,id=<?>,keypair='copmute01keypair',labels={docker_volume_type='lvm'},magnum_cert_ref=<?>,master_addresses=<?>,master_count=1,master_flavor_id='m1.small',name='atomichostv1cluster',node_addresses=<?>,node_count=1,project_id='b5a1eb4ee8374fa1aa88cd4b59afda98',stack_id=<?>,status=<?>,status_reason=<?>,trust_id=<?>,trustee_password=<?>,trustee_user_id=<?>,trustee_username=<?>,updated_at=<?>,user_id='03b0360129f84f9790081df4cebf7844',uuid=<?>)
```

rpcapi发送到

```
/usr/lib/python2.7/site-packages/magnum/conductor/api.py(41)cluster_create_async()


@profiler.trace_cls("rpc")
class API(rpc_service.API):
	# ........省略部分代码
    def cluster_create_async(self, cluster, create_timeout):
        self._cast('cluster_create', cluster=cluster,
                   create_timeout=create_timeout)
                   
                   
  
  
  
  
/usr/lib/python2.7/site-packages/magnum/common/rpc_service.py
class API(object):
    def __init__(self, transport=None, context=None, topic=None, server=None,
                 timeout=None):
        serializer = _init_serializer()
        if transport is None:
            exmods = rpc.get_allowed_exmods()
            transport = messaging.get_rpc_transport(
                CONF, allowed_remote_exmods=exmods)
        self._context = context
        if topic is None:
            topic = ''
        # topic:  magnum-conductor
        target = messaging.Target(topic=topic, server=server)
        self._client = messaging.RPCClient(transport, target,
                                           serializer=serializer,
                                           timeout=timeout)
    
    def _cast(self, method, *args, **kwargs):
        self._client.cast(self._context, method, *args, **kwargs)

```

发送cluster_create方法到conductor服务的rpc队列

**todo:   rpc过程**

调用cluster_create()方法

```
/usr/lib/python2.7/site-packages/magnum/conductor/handlers/cluster_conductor.py(48)cluster_create()


@profiler.trace_cls("rpc")
class Handler(object):

    def __init__(self):
        super(Handler, self).__init__()

    # Cluster Operations

    def cluster_create(self, context, cluster, create_timeout):
        LOG.debug('cluster_heat cluster_create')

        osc = clients.OpenStackClients(context)

        cluster.status = fields.ClusterStatus.CREATE_IN_PROGRESS
        cluster.status_reason = None
        cluster.create()  # 数据库处理

        try:
            # Create trustee/trust and set them to cluster
            trust_manager.create_trustee_and_trust(osc, cluster)
            # Generate certificate and set the cert reference to cluster
            cert_manager.generate_certificates_to_cluster(cluster,
                                                          context=context)
            conductor_utils.notify_about_cluster_operation(
                context, taxonomy.ACTION_CREATE, taxonomy.OUTCOME_PENDING)
            # Get driver
            cluster_driver = driver.Driver.get_driver_for_cluster(context,
                                                                  cluster)
            # Create cluster：  <magnum.drivers.k8s_fedora_atomic_v1.driver.Driver object at 0x7fc055eaeb50>
            cluster_driver.create_cluster(context, cluster, create_timeout)
            cluster.save()

        except Exception as e:
            cluster.status = fields.ClusterStatus.CREATE_FAILED
            cluster.status_reason = six.text_type(e)
            cluster.save()
            conductor_utils.notify_about_cluster_operation(
                context, taxonomy.ACTION_CREATE, taxonomy.OUTCOME_FAILURE)

            if isinstance(e, exc.HTTPBadRequest):
                e = exception.InvalidParameterValue(message=six.text_type(e))

                raise e
            raise

        return cluster

```

其中的  cluster.create()  # 数据库处理

```
/usr/lib/python2.7/site-packages/magnum/objects/cluster.py(223)create()
    
    
@base.MagnumObjectRegistry.register
class Cluster(base.MagnumPersistentObject, base.MagnumObject,
              base.MagnumObjectDictCompat):
    # .......省略
    
    @base.remotable
    def create(self, context=None):
        """Create a Cluster record in the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Cluster(context)

        """
        values = self.obj_get_changes()
        db_cluster = self.dbapi.create_cluster(values)
        self._from_db_object(self, db_cluster)
```

而cluster_driver，模板选的fedora_k8s，此处调用<magnum.drivers.k8s_fedora_atomic_v1.driver.Driver object at 0x7fc055eaeb50>， k8s_fedora_atomic_v1.driver.Driver继承driver.HeatDriver

```
/usr/lib/python2.7/site-packages/magnum/drivers/heat/driver.py(98)create_cluster()


@six.add_metaclass(abc.ABCMeta)
class HeatDriver(driver.Driver):
    """Base Driver class for using Heat

       Abstract class for implementing Drivers that leverage OpenStack Heat for
       orchestrating cluster lifecycle operations
    """
    # ......省略部分代码

    def create_cluster(self, context, cluster, cluster_create_timeout):
        stack = self._create_stack(context, clients.OpenStackClients(context),
                                   cluster, cluster_create_timeout)
        # TODO(randall): keeping this for now to reduce/eliminate data
        # migration. Should probably come up with something more generic in
        # the future once actual non-heat-based drivers are implemented.
        cluster.stack_id = stack['stack']['id']


    def _create_stack(self, context, osc, cluster, cluster_create_timeout):
        template_path, heat_params, env_files = (
            self._extract_template_definition(context, cluster))

        tpl_files, template = template_utils.get_template_contents(
            template_path)

        environment_files, env_map = self._get_env_files(template_path,
                                                         env_files)
        tpl_files.update(env_map)

        # Make sure we end up with a valid hostname
        valid_chars = set(ascii_letters + digits + '-')

        # valid hostnames are 63 chars long, leaving enough room
        # to add the random id (for uniqueness)
        stack_name = cluster.name[:30]
        stack_name = stack_name.replace('_', '-')
        stack_name = stack_name.replace('.', '-')
        stack_name = ''.join(filter(valid_chars.__contains__, stack_name))

        # Make sure no duplicate stack name
        stack_name = '%s-%s' % (stack_name, short_id.generate_id())
        stack_name = stack_name.lower()
        if cluster_create_timeout:
            heat_timeout = cluster_create_timeout
        else:
            # no cluster_create_timeout value was passed in to the request
            # so falling back on configuration file value
            heat_timeout = cfg.CONF.cluster_heat.create_timeout
        fields = {
            'stack_name': stack_name,
            'parameters': heat_params,
            'environment_files': environment_files,
            'template': template,
            'files': tpl_files,
            'timeout_mins': heat_timeout
        }
        # osc: <magnum.common.clients.OpenStackClients
        # osc.heat():  <heatclient.v1.client.Client object at 0x7f8487733510>
        created_stack = osc.heat().stacks.create(**fields)

        return created_stack


```

在magnum中调用heatclient ，向heatapi发送请求，请求连接：http://controller:8004/v1/b5a1eb4ee8374fa1aa88cd4b59afda98/stacks，下面对heat代码进行解析

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





























































