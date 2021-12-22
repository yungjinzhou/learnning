## vnc源码流程分析



页面请求

url: servers/{server_id}/remote_consoles

根据pecan及wsme代码，定位到nova/api/openstack/compute/remote_consoles.py

1，接收api请求

```



    @wsgi.Controller.api_version("2.1", "2.5")
    @wsgi.expected_errors((400, 404, 409, 501))
    @wsgi.action('os-getVNCConsole')
    @validation.schema(remote_consoles.get_vnc_console)
    def get_vnc_console(self, req, id, body):
        """Get text console output."""
        context = req.environ['nova.context']
        context.can(rc_policies.BASE_POLICY_NAME)

        # If type is not supplied or unknown, get_vnc_console below will cope
        console_type = body['os-getVNCConsole'].get('type')

        instance = common.get_instance(self.compute_api, context, id)
        try:
            output = self.compute_api.get_vnc_console(context,
                                                      instance,
                                                      console_type)
        except exception.ConsoleTypeUnavailable as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        except (exception.InstanceUnknownCell,
                     exception.InstanceNotFound) as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())
        except exception.InstanceNotReady as e:
            raise webob.exc.HTTPConflict(explanation=e.format_message())
        except NotImplementedError:
            common.raise_feature_not_supported()

        return {'console': {'type': console_type, 'url': output['url']}}

```

2其中self.compute_api.get_vnc_console是调用nova/compute/api.py中的get_vnc_console方法

```



    @check_instance_host
    @reject_instance_state(
        task_state=[task_states.DELETING, task_states.MIGRATING])
    def get_vnc_console(self, context, instance, console_type):
        """Get a url to an instance Console."""
        connect_info = self.compute_rpcapi.get_vnc_console(context,
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



2.1 首先获取vnc_console，然后认证，先看通过rpc获取console流程

nova/compute/rpcapi.py

```
    
    
    
    def get_vnc_console(self, ctxt, instance, console_type):
        version = '5.0'
        cctxt = self.router.client(ctxt).prepare(
                server=_compute_host(None, instance), version=version)
        return cctxt.call(ctxt, 'get_vnc_console',
                          instance=instance, console_type=console_type)


# cctxt.__dict__
{'retry': None, 'conf': <oslo_messaging._drivers.common.ConfigOptsProxy object at 0x7f945ca2cc10>, 'version_cap': None, 'transport': <oslo_messaging.transport.RPCTransport object at 0x7f945ca078d0>, 'timeout': None, 'call_monitor_timeout': None, 'serializer': <nova.rpc.ProfilerRequestContextSerializer object at 0x7f945cafe310>, 'target': <Target topic=compute, version=5.0, server=compute01>}
```

发送到nova-compute服务处理

nova/compute/manager.py

```
    @wrap_exception()
    @wrap_instance_fault
    def get_vnc_console(self, context, console_type, instance):
        """Return connection information for a vnc console."""
        context = context.elevated()
        LOG.debug("Getting vnc console", instance=instance)

        if not CONF.vnc.enabled:
            raise exception.ConsoleTypeUnavailable(console_type=console_type)

        if console_type == 'novnc':
            # For essex, novncproxy_base_url must include the full path
            # including the html file (like http://myhost/vnc_auto.html)
            access_url_base = CONF.vnc.novncproxy_base_url
        elif console_type == 'xvpvnc':
            access_url_base = CONF.vnc.xvpvncproxy_base_url
        else:
            raise exception.ConsoleTypeInvalid(console_type=console_type)

        try:
            # Retrieve connect info from driver, and then decorate with our
            # access info token
            console = self.driver.get_vnc_console(context, instance)
            console_auth = objects.ConsoleAuthToken(
                context=context,
                console_type=console_type,
                host=console.host,
                port=console.port,
                internal_access_path=console.internal_access_path,
                instance_uuid=instance.uuid,
                access_url_base=access_url_base,
            )
            console_auth.authorize(CONF.consoleauth.token_ttl)
            connect_info = console.get_connection_info(
                console_auth.token, console_auth.access_url)

        except exception.InstanceNotFound:
            if instance.vm_state != vm_states.BUILDING:
                raise
            raise exception.InstanceNotReady(instance_id=instance.uuid)

        return connect_info


# console_auth 
ConsoleAuthToken(access_url_base='http://192.168.230.173:6080/vnc_auto.html',console_type='novnc',created_at=2021-12-21T06:07:51Z,host='192.168.230.174',id=203,instance_uuid=ca931f42-a2e2-4bbb-b6c1-d22874ea2352,internal_access_path=None,port=5903,token='1b1f2d8d-c9bc-41e6-8b51-68a42350a9a9',updated_at=None)


# console.__dict__
(Pdb) console.__dict__
{'internal_access_path': None, 'host': '192.168.230.174', 'port': '5903}

# connect_info
{'access_url': u'http://192.168.230.173:6080/vnc_auto.html?path=%3Ftoken%3D1b1f2d8d-c9bc-41e6-8b51-68a42350a9a9', 'internal_access_path': None, 'host': '192.168.230.174', 'token': u'1b1f2d8d-c9bc-41e6-8b51-68a42350a9a9', 'port': '5903'}
```

其中 self.driver

<nova.virt.libvirt.driver.LibvirtDriver object at 0x7fb95be7af10>











2.2 然后认证流程



