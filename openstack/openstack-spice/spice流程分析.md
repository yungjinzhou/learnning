## spice流程分析



请求nova-api

nova/api/openstack/compute/remote_consoles.py



```




    @wsgi.Controller.api_version("2.6")
    @wsgi.expected_errors((400, 404, 409, 501))
    @validation.schema(remote_consoles.create_v26, "2.6", "2.7")
    @validation.schema(remote_consoles.create_v28, "2.8")
    def create(self, req, server_id, body):
        context = req.environ['nova.context']
        context.can(rc_policies.BASE_POLICY_NAME)
        instance = common.get_instance(self.compute_api, context, server_id)
        protocol = body['remote_console']['protocol']
        console_type = body['remote_console']['type']
        try:
            handler = self.handlers.get(protocol)
            output = handler(context, instance, console_type)
            return {'remote_console': {'protocol': protocol,
                                       'type': console_type,
                                       'url': output['url']}}

        except exception.InstanceNotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())
        except exception.InstanceNotReady as e:
            raise webob.exc.HTTPConflict(explanation=e.format_message())
        except (exception.ConsoleTypeInvalid,
                exception.ConsoleTypeUnavailable,
                exception.ImageSerialPortNumberInvalid,
                exception.ImageSerialPortNumberExceedFlavorValue,
                exception.SocketPortRangeExhaustedException) as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        except NotImplementedError:
            common.raise_feature_not_supported()

```



nova/compute/api.py

```
    @check_instance_host
    @reject_instance_state(
        task_state=[task_states.DELETING, task_states.MIGRATING])
    def get_spice_console(self, context, instance, console_type):
        """Get a url to an instance Console."""
        connect_info = self.compute_rpcapi.get_spice_console(context,
                instance=instance, console_type=console_type)
        # TODO(melwitt): In Rocky, the compute manager puts the
        # console authorization in the database in the above method.
        # The following will be removed when everything has been
        # converted to use the database, in Stein.
        if CONF.workarounds.enable_consoleauth:
            self.consoleauth_rpcapi.authorize_console(context,
                    connect_info['token'], console_type,
                    connect_info['host'], connect_info['port'],
                    connect_info['internal_access_path'], instance.uuid,
                    access_url=connect_info['access_url'])

        return {'url': connect_info['access_url']}

```



2.1 首先获取spice_console，然后认证，先看通过rpc获取console流程

nova/compute/rpcapi.py

```
    def get_spice_console(self, ctxt, instance, console_type):
        version = '5.0'
        cctxt = self.router.client(ctxt).prepare(
                server=_compute_host(None, instance), version=version)
        return cctxt.call(ctxt, 'get_spice_console',
                          instance=instance, console_type=console_type)

```



发送到nova-compute服务处理

nova/compute/manager.py

```
    @wrap_exception()
    @wrap_instance_fault
    def get_spice_console(self, context, console_type, instance):
        """Return connection information for a spice console."""
        context = context.elevated()
        LOG.debug("Getting spice console", instance=instance)

        if not CONF.spice.enabled:
            raise exception.ConsoleTypeUnavailable(console_type=console_type)

        if console_type != 'spice-html5':
            raise exception.ConsoleTypeInvalid(console_type=console_type)

        try:
            # Retrieve connect info from driver, and then decorate with our
            # access info token
            console = self.driver.get_spice_console(context, instance)
            console_auth = objects.ConsoleAuthToken(
                context=context,
                console_type=console_type,
                host=console.host,
                port=console.port,
                internal_access_path=console.internal_access_path,
                instance_uuid=instance.uuid,
                access_url_base=CONF.spice.html5proxy_base_url,
            )
            console_auth.authorize(CONF.consoleauth.token_ttl)
            connect_info = console.get_connection_info(
                console_auth.token, console_auth.access_url)

        except exception.InstanceNotFound:
            if instance.vm_state != vm_states.BUILDING:
                raise
            raise exception.InstanceNotReady(instance_id=instance.uuid)

        return connect_info

```



其中 self.driver

<nova.virt.libvirt.driver.LibvirtDriver object at 0x7fb95be7af10>

nova.virt.libvirt.driver.LibvirtDriver下的get_spice方法

```
    def get_spice_console(self, context, instance):
        def get_spice_ports_for_instance(instance_name):
            guest = self._host.get_guest(instance)

            xml = guest.get_xml_desc()
            xml_dom = etree.fromstring(xml)

            graphic = xml_dom.find("./devices/graphics[@type='spice']")
            if graphic is not None:
                return (graphic.get('port'), graphic.get('tlsPort'))
            # NOTE(rmk): We had Spice consoles enabled but the instance in
            # question is not actually listening for connections.
            raise exception.ConsoleTypeUnavailable(console_type='spice')

        ports = get_spice_ports_for_instance(instance.name)
        host = CONF.spice.server_proxyclient_address

        return ctype.ConsoleSpice(host=host, port=ports[0], tlsPort=ports[1])

```



获取token后，url，请求openstack-nova-spicehtml5proxy





