## vnc源码流程分析



页面请求

url: servers/{server_id}/remote_consoles

根据pecan及wsme代码，定位到nova/api/openstack/compute/remote_consoles.py

1，接收api请求

```

    @wsgi.Controller.api_version("2.6")
    @wsgi.expected_errors((400, 404, 409, 501))
    @validation.schema(remote_consoles.create_v26, "2.6", "2.7")
    @validation.schema(remote_consoles.create_v28, "2.8")
    def create(self, req, server_id, body):
        context = req.environ['nova.context']
        instance = common.get_instance(self.compute_api, context, server_id)
        context.can(rc_policies.BASE_POLICY_NAME,
                    target={'project_id': instance.project_id})
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

nova.virt.libvirt.driver.LibvirtDriver下的get_vnc方法

```

    def get_vnc_console(self, context, instance):
        def get_vnc_port_for_instance(instance_name):
            guest = self._host.get_guest(instance)

            xml = guest.get_xml_desc()
            xml_dom = etree.fromstring(xml)

            graphic = xml_dom.find("./devices/graphics[@type='vnc']")
            if graphic is not None:
                return graphic.get('port')
            # NOTE(rmk): We had VNC consoles enabled but the instance in
            # question is not actually listening for connections.
            raise exception.ConsoleTypeUnavailable(console_type='vnc')

        port = get_vnc_port_for_instance(instance.name)
        host = CONF.vnc.server_proxyclient_address

        return ctype.ConsoleVNC(host=host, port=port)
```



获取token后，url，请求 openstack-nova-novncproxy

1 nova/cmd/novncproxy.py

```
def main():
    # set default web flag option
    CONF.set_default('web', '/usr/share/novnc')
    config.parse_args(sys.argv)

    baseproxy.proxy(
        host=CONF.vnc.novncproxy_host,
        port=CONF.vnc.novncproxy_port,
        security_proxy=rfb.RFBSecurityProxy())

```



nova/cmd/baseproxy.py

```

def proxy(host, port, security_proxy=None):
    """:param host: local address to listen on
    :param port: local port to listen on
    :param security_proxy: instance of
        nova.console.securityproxy.base.SecurityProxy

    Setup a proxy listening on @host:@port. If the
    @security_proxy parameter is not None, this instance
    is used to negotiate security layer with the proxy target
    """

    if CONF.ssl_only and not os.path.exists(CONF.cert):
        exit_with_error("SSL only and %s not found" % CONF.cert)

    # Check to see if tty html/js/css files are present
    if CONF.web and not os.path.exists(CONF.web):
        exit_with_error("Can not find html/js files at %s." % CONF.web)

    logging.setup(CONF, "nova")

    gmr.TextGuruMeditation.setup_autorun(version, conf=CONF)

    # Create and start the NovaWebSockets proxy
    websocketproxy.NovaWebSocketProxy(
        listen_host=host,
        listen_port=port,
        source_is_ipv6=CONF.source_is_ipv6,
        cert=CONF.cert,
        key=CONF.key,
        ssl_only=CONF.ssl_only,
        ssl_ciphers=CONF.console.ssl_ciphers,
        ssl_minimum_version=CONF.console.ssl_minimum_version,
        daemon=CONF.daemon,
        record=CONF.record,
        traffic=not CONF.daemon,
        web=CONF.web,
        file_only=True,
        RequestHandlerClass=websocketproxy.NovaProxyRequestHandler,
        security_proxy=security_proxy,
    ).start_server()

```

2 websokify/websocket.py

```

    def start_server(self):
        """
        Daemonize if requested. Listen for for connections. Run
        do_handshake() method for each connection. If the connection
        is a WebSockets client then call new_websocket_client() method (which must
        be overridden) for each new client connection.
        """
        lsock = self.socket(self.listen_host, self.listen_port, False,
                            self.prefer_ipv6,
                            tcp_keepalive=self.tcp_keepalive,
                            tcp_keepcnt=self.tcp_keepcnt,
                            tcp_keepidle=self.tcp_keepidle,
                            tcp_keepintvl=self.tcp_keepintvl)

        if self.daemon:
            keepfd = self.get_log_fd()
            keepfd.append(lsock.fileno())
            self.daemonize(keepfd=keepfd, chdir=self.web)

        self.started()  # Some things need to happen after daemonizing

        # Allow override of signals
        original_signals = {
            signal.SIGINT: signal.getsignal(signal.SIGINT),
            signal.SIGTERM: signal.getsignal(signal.SIGTERM),
            signal.SIGCHLD: signal.getsignal(signal.SIGCHLD),
        }
        signal.signal(signal.SIGINT, self.do_SIGINT)
        signal.signal(signal.SIGTERM, self.do_SIGTERM)
        if not multiprocessing:
            # os.fork() (python 2.4) child reaper
            signal.signal(signal.SIGCHLD, self.fallback_SIGCHLD)
        else:
            # make sure that _cleanup is called when children die
            # by calling active_children on SIGCHLD
            signal.signal(signal.SIGCHLD, self.multiprocessing_SIGCHLD)

        last_active_time = self.launch_time
        try:
            while True:
                try:
                    try:
                        startsock = None
                        pid = err = 0
                        child_count = 0

                        if multiprocessing:
                            # Collect zombie child processes
                            child_count = len(multiprocessing.active_children())

                        time_elapsed = time.time() - self.launch_time
                        if self.timeout and time_elapsed > self.timeout:
                            self.msg('listener exit due to --timeout %s'
                                    % self.timeout)
                            break

                        if self.idle_timeout:
                            idle_time = 0
                            if child_count == 0:
                                idle_time = time.time() - last_active_time
                            else:
                                idle_time = 0
                                last_active_time = time.time()

                            if idle_time > self.idle_timeout and child_count == 0:
                                self.msg('listener exit due to --idle-timeout %s'
                                            % self.idle_timeout)
                                break

                        try:
                            self.poll()

                            ready = select.select([lsock], [], [], 1)[0]
                            if lsock in ready:
                                startsock, address = lsock.accept()
                            else:
                                continue
                        except self.Terminate:
                            raise
                        except Exception:
                            _, exc, _ = sys.exc_info()
                            if hasattr(exc, 'errno'):
                                err = exc.errno
                            elif hasattr(exc, 'args'):
                                err = exc.args[0]
                            else:
                                err = exc[0]
                            if err == errno.EINTR:
                                self.vmsg("Ignoring interrupted syscall")
                                continue
                            else:
                                raise

                        if self.run_once:
                            # Run in same process if run_once
                            self.top_new_client(startsock, address)
                            if self.ws_connection :
                                self.msg('%s: exiting due to --run-once'
                                        % address[0])
                                break
                        elif multiprocessing:
                            self.vmsg('%s: new handler Process' % address[0])
                            p = multiprocessing.Process(
                                    target=self.top_new_client,
                                    args=(startsock, address))
                            p.start()
                            # child will not return
                        else:
                            # python 2.4
                            self.vmsg('%s: forking handler' % address[0])
                            pid = os.fork()
                            if pid == 0:
                                # child handler process
                                self.top_new_client(startsock, address)
                                break  # child process exits

                        # parent process
                        self.handler_id += 1

                    except (self.Terminate, SystemExit, KeyboardInterrupt):
                        self.msg("In exit")
                        # terminate all child processes
                        if multiprocessing and not self.run_once:
                            children = multiprocessing.active_children()

                            for child in children:
                                self.msg("Terminating child %s" % child.pid)
                                child.terminate()

                        break
                    except Exception:
                        exc = sys.exc_info()[1]
                        self.msg("handler exception: %s", str(exc))
                        self.vmsg("exception", exc_info=True)

                finally:
                    if startsock:
                        startsock.close()
        finally:
            # Close listen port
            self.vmsg("Closing socket listening at %s:%s",
                      self.listen_host, self.listen_port)
            lsock.close()

            # Restore signals
            for sig, func in original_signals.items():
                signal.signal(sig, func)



```

websockify/websocket.py

```


    def do_GET(self):
        """Handle GET request. Calls handle_websocket(). If unsuccessful,
        and web server is enabled, SimpleHTTPRequestHandler.do_GET will be called."""
        if not self.handle_websocket():
            if self.only_upgrade:
                self.send_error(405, "Method Not Allowed")
            else:
                SimpleHTTPRequestHandler.do_GET(self)

```





websokify/websocket.py

```

    def handle_websocket(self):
        """Upgrade a connection to Websocket, if requested. If this succeeds,
        new_websocket_client() will be called. Otherwise, False is returned.
        """

        if (self.headers.get('upgrade') and
            self.headers.get('upgrade').lower() == 'websocket'):

            # ensure connection is authorized, and determine the target
            self.validate_connection()

            if not self.do_websocket_handshake():
                return False

            # Indicate to server that a Websocket upgrade was done
            self.server.ws_connection = True
            # Initialize per client settings
            self.send_parts = []
            self.recv_part  = None
            self.start_time = int(time.time()*1000)

            # client_address is empty with, say, UNIX domain sockets
            client_addr = ""
            is_ssl = False
            try:
                client_addr = self.client_address[0]
                is_ssl = self.client_address[2]
            except IndexError:
                pass

            if is_ssl:
                self.stype = "SSL/TLS (wss://)"
            else:
                self.stype = "Plain non-SSL (ws://)"

            self.log_message("%s: %s WebSocket connection", client_addr,
                             self.stype)
            self.log_message("%s: Version %s, base64: '%s'", client_addr,
                             self.version, self.base64)
            if self.path != '/':
                self.log_message("%s: Path: '%s'", client_addr, self.path)

            if self.record:
                # Record raw frame data as JavaScript array
                fname = "%s.%s" % (self.record,
                                   self.handler_id)
                self.log_message("opening record file: %s", fname)
                self.rec = open(fname, 'w+')
                encoding = "binary"
                if self.base64: encoding = "base64"
                self.rec.write("var VNC_frame_encoding = '%s';\n"
                               % encoding)
                self.rec.write("var VNC_frame_data = [\n")

            try:
                self.new_websocket_client()
            except self.CClose:
                # Close the client
                _, exc, _ = sys.exc_info()
                self.send_close(exc.args[0], exc.args[1])
            return True
        else:
            return False

```



3 oslo_db.sqlalchemy.engines

4 nova.objects.console_auth_token

5 oslo_concurrency.lockutils





6 nova.console.websocketproxy

```
    def new_websocket_client(self):
        """Called after a new WebSocket connection has been established."""
        # Reopen the eventlet hub to make sure we don't share an epoll
        # fd with parent and/or siblings, which would be bad
        from eventlet import hubs
        hubs.use_hub()

        # The nova expected behavior is to have token
        # passed to the method GET of the request
        token = urlparse.parse_qs(
            urlparse.urlparse(self.path).query
        ).get('token', ['']).pop()
        if not token:
            # NoVNC uses it's own convention that forward token
            # from the request to a cookie header, we should check
            # also for this behavior
            hcookie = self.headers.get('cookie')
            if hcookie:
                cookie = Cookie.SimpleCookie()
                for hcookie_part in hcookie.split(';'):
                    hcookie_part = hcookie_part.lstrip()
                    try:
                        cookie.load(hcookie_part)
                    except Cookie.CookieError:
                        # NOTE(stgleb): Do not print out cookie content
                        # for security reasons.
                        LOG.warning('Found malformed cookie')
                    else:
                        if 'token' in cookie:
                            token = cookie['token'].value

        ctxt = context.get_admin_context()
        connect_info = self._get_connect_info(ctxt, token)

        # Verify Origin
        expected_origin_hostname = self.headers.get('Host')
        if ':' in expected_origin_hostname:
            e = expected_origin_hostname
            if '[' in e and ']' in e:
                expected_origin_hostname = e.split(']')[0][1:]
            else:
                expected_origin_hostname = e.split(':')[0]
        expected_origin_hostnames = CONF.console.allowed_origins
        expected_origin_hostnames.append(expected_origin_hostname)
        origin_url = self.headers.get('Origin')
        # missing origin header indicates non-browser client which is OK
        if origin_url is not None:
            origin = urlparse.urlparse(origin_url)
            origin_hostname = origin.hostname
            origin_scheme = origin.scheme
            # If the console connection was forwarded by a proxy (example:
            # haproxy), the original protocol could be contained in the
            # X-Forwarded-Proto header instead of the Origin header. Prefer the
            # forwarded protocol if it is present.
            forwarded_proto = self.headers.get('X-Forwarded-Proto')
            if forwarded_proto is not None:
                origin_scheme = forwarded_proto
            if origin_hostname == '' or origin_scheme == '':
                detail = _("Origin header not valid.")
                raise exception.ValidationError(detail=detail)
            if origin_hostname not in expected_origin_hostnames:
                detail = _("Origin header does not match this host.")
                raise exception.ValidationError(detail=detail)
            if not self.verify_origin_proto(connect_info, origin_scheme):
                detail = _("Origin header protocol does not match this host.")
                raise exception.ValidationError(detail=detail)

        sanitized_info = copy.copy(connect_info)
        sanitized_info.token = '***'
        self.msg(_('connect info: %s'), sanitized_info)

        host = connect_info.host
        port = connect_info.port

        # Connect to the target
        self.msg(_("connecting to: %(host)s:%(port)s") % {'host': host,
                                                          'port': port})
        tsock = self.socket(host, port, connect=True)

        # Handshake as necessary
        if 'internal_access_path' in connect_info:
            path = connect_info.internal_access_path
            if path:
                tsock.send(encodeutils.safe_encode(
                    'CONNECT %s HTTP/1.1\r\n\r\n' % path))
                end_token = "\r\n\r\n"
                while True:
                    data = tsock.recv(4096, socket.MSG_PEEK)
                    token_loc = data.find(end_token)
                    if token_loc != -1:
                        if data.split("\r\n")[0].find("200") == -1:
                            raise exception.InvalidConnectionInfo()
                        # remove the response from recv buffer
                        tsock.recv(token_loc + len(end_token))
                        break

        if self.server.security_proxy is not None:
            tenant_sock = TenantSock(self)

            try:
                tsock = self.server.security_proxy.connect(tenant_sock, tsock)  # 第7步rfb.py中的connect
            except exception.SecurityProxyNegotiationFailed:
                LOG.exception("Unable to perform security proxying, shutting "
                              "down connection")
                tenant_sock.close()
                tsock.shutdown(socket.SHUT_RDWR)
                tsock.close()
                raise

            tenant_sock.finish_up()

        # Start proxying
        try:
            self.do_proxy(tsock)
        except Exception:
            if tsock:
                tsock.shutdown(socket.SHUT_RDWR)
                tsock.close()
                self.vmsg(_("%(host)s:%(port)s: "
                          "Websocket client or target closed") %
                          {'host': host, 'port': port})
            raise

```







websockify/websocketproxy.py

```


    def do_proxy(self, target):
        """
        Proxy client WebSocket to normal target socket.
        """
        cqueue = []
        c_pend = 0
        tqueue = []
        rlist = [self.request, target]

        if self.server.heartbeat:
            now = time.time()
            self.heartbeat = now + self.server.heartbeat
        else:
            self.heartbeat = None

        while True:
            wlist = []

            if self.heartbeat is not None:
                now = time.time()
                if now > self.heartbeat:
                    self.heartbeat = now + self.server.heartbeat
                    self.send_ping()

            if tqueue: wlist.append(target)
            if cqueue or c_pend: wlist.append(self.request)
            try:
                ins, outs, excepts = select.select(rlist, wlist, [], 1)
            except (select.error, OSError):
                exc = sys.exc_info()[1]
                if hasattr(exc, 'errno'):
                    err = exc.errno
                else:
                    err = exc[0]

                if err != errno.EINTR:
                    raise
                else:
                    continue

            if excepts: raise Exception("Socket exception")

            if self.request in outs:
                # Send queued target data to the client 将数据发送给客户端
                c_pend = self.send_frames(cqueue)

                cqueue = []

            if self.request in ins:
                # Receive client data, decode it, and queue for target 从客户端接收数据
                bufs, closed = self.recv_frames()
                tqueue.extend(bufs)

                if closed:
                    # TODO: What about blocking on client socket?
                    if self.verbose:
                        self.log_message("%s:%s: Client closed connection",
                                self.server.target_host, self.server.target_port)
                    raise self.CClose(closed['code'], closed['reason'])


            if target in outs:
                # Send queued client data to the target 将客户端数据发送到目标vnc地址
                dat = tqueue.pop(0)
                sent = target.send(dat)
                if sent == len(dat):
                    self.print_traffic(">")
                else:
                    # requeue the remaining data
                    tqueue.insert(0, dat[sent:])
                    self.print_traffic(".>")


            if target in ins:
                # Receive target data, encode it and queue for client 从目标vnc地址接收收据
                buf = target.recv(self.buffer_size)
                if len(buf) == 0:
                    if self.verbose:
                        self.log_message("%s:%s: Target closed connection",
                                self.server.target_host, self.server.target_port)
                    raise self.CClose(1000, "Target closed")

                cqueue.append(buf)
                self.print_traffic("{")

```











7 nova.console.securityproxy.rfb

```
    def connect(self, tenant_sock, compute_sock):
        """Initiate the RFB connection process.

        This method performs the initial ProtocolVersion
        and Security messaging, and returns the socket-like
        object to use to communicate with the server securely.
        If an error occurs SecurityProxyNegotiationFailed
        will be raised.
        """

        def recv(sock, num):
            b = sock.recv(num)
            if len(b) != num:
                reason = _("Incorrect read from socket, wanted %(wanted)d "
                           "bytes but got %(got)d. Socket returned "
                           "%(result)r") % {'wanted': num, 'got': len(b),
                                            'result': b}
                raise exception.RFBAuthHandshakeFailed(reason=reason)
            return b

        # Negotiate version with compute server
        compute_version = recv(compute_sock, auth.VERSION_LENGTH)
        LOG.debug(
            "Got version string '%s' from compute node",
            compute_version[:-1].decode('utf-8'))

        if self._parse_version(compute_version) != 3.8:
            reason = _(
                "Security proxying requires RFB protocol version 3.8, "
                "but server sent %s")
            raise exception.SecurityProxyNegotiationFailed(
                reason=reason % compute_version[:-1].decode('utf-8'))
        compute_sock.sendall(compute_version)

        # Negotiate version with tenant
        tenant_sock.sendall(compute_version)
        tenant_version = recv(tenant_sock, auth.VERSION_LENGTH)
        LOG.debug(
            "Got version string '%s' from tenant",
            tenant_version[:-1].decode('utf-8'))

        if self._parse_version(tenant_version) != 3.8:
            reason = _(
                "Security proxying requires RFB protocol version 3.8, "
                "but tenant asked for %s")
            raise exception.SecurityProxyNegotiationFailed(
                reason=reason % tenant_version[:-1].decode('utf-8'))

        # Negotiate security with server
        permitted_auth_types_cnt = recv(compute_sock, 1)[0]

        if permitted_auth_types_cnt == 0:
            # Decode the reason why the request failed
            reason_len_raw = recv(compute_sock, 4)
            reason_len = struct.unpack('!I', reason_len_raw)[0]
            reason = recv(compute_sock, reason_len)

            tenant_sock.sendall(auth.AUTH_STATUS_FAIL +
                                reason_len_raw + reason)

            raise exception.SecurityProxyNegotiationFailed(reason=reason)

        f = recv(compute_sock, permitted_auth_types_cnt)
        permitted_auth_types = []
        for auth_type in f:
            if isinstance(auth_type, str):
                auth_type = ord(auth_type)
            permitted_auth_types.append(auth_type)

        LOG.debug(
            "Server sent security types: %s",
            ", ".join(
                '%d (%s)' % (auth.AuthType(t).value, auth.AuthType(t).name)
                for t in permitted_auth_types
            ))

        # Negotiate security with client before we say "ok" to the server
        # send 1:[None]
        tenant_sock.sendall(auth.AUTH_STATUS_PASS +
                            bytes((auth.AuthType.NONE,)))
        client_auth = recv(tenant_sock, 1)[0]

        # 验证client_auth类型
        if client_auth != auth.AuthType.NONE:
            self._fail(
                tenant_sock, compute_sock,
                _("Only the security type %d (%s) is supported") % (
                    auth.AuthType.NONE.value, auth.AuthType.NONE.name,
                ))

            reason = _(
                "Client requested a security type other than %d (%s): "
                "%d (%s)"
            ) % (
                auth.AuthType.NONE.value,
                auth.AuthType.NONE.name,
                auth.AuthType(client_auth).value,
                auth.AuthType(client_auth).name,
            )
            raise exception.SecurityProxyNegotiationFailed(reason=reason)

        try:
            scheme = self.auth_schemes.find_scheme(permitted_auth_types)
        except exception.RFBAuthNoAvailableScheme as e:
            # Intentionally don't tell client what really failed
            # as that's information leakage
            self._fail(tenant_sock, compute_sock,
                       _("Unable to negotiate security with server"))
            raise exception.SecurityProxyNegotiationFailed(
                reason=_("No compute auth available: %s") % str(e)) compute_sock.sendall(bytes((scheme.security_type(),)))

        LOG.debug(
            "Using security type %d (%s) with server, %d (%s) with client",
            scheme.security_type().value, scheme.security_type().name,
            auth.AuthType.NONE.value, auth.AuthType.NONE.name)

        try:
            compute_sock = scheme.security_handshake(compute_sock)
        except exception.RFBAuthHandshakeFailed as e:
            # Intentionally don't tell client what really failed
            # as that's information leakage
            self._fail(tenant_sock, None,
                       _("Unable to negotiate security with server"))
            LOG.debug("Auth failed %s", str(e))
            raise exception.SecurityProxyNegotiationFailed(
                reason=_("Auth handshake failed"))

        LOG.info("Finished security handshake, resuming normal proxy "
                 "mode using secured socket")

        # we can just proxy the security result -- if the server security
        # negotiation fails, we want the client to think it has failed

        return compute_sock

```







pdb定位第二步请求流程

```

2
nova.console.websocketproxy [-] 192.168.31.113: new handler Process vmsg /usr/lib/python2.7/site-packages/websockify/websocket.py:875     
nova.console.websocketproxy [-] 192.168.31.113 - - [28/Dec/2021 11:43:35] 192.168.31.113: Plain non-SSL (ws://) WebSocket connection
nova.console.websocketproxy [-] 192.168.31.113 - - [28/Dec/2021 11:43:35] 192.168.31.113: Version hybi-13, base64: 'False'
nova.console.websocketproxy [-] 192.168.31.113 - - [28/Dec/2021 11:43:35] 192.168.31.113: Path: '/?token=441a97dd-35f1-42ba-8cd4-017430e6bde7'
3
oslo_db.sqlalchemy.engines [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -] MySQL server mode set to STRICT_TRANS_TABLES,STRICT_ALL_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,TRADITIONAL,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION _check_effective_sql_mode /usr/lib/python2.7/site-packages/oslo_db/sqlalchemy/engines.py:307
4
nova.objects.console_auth_token [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -] Validated token - console connection is ConsoleAuthToken(access_url_base='http://192.168.230.173:6080/vnc_auto.html',console_type='novnc',created_at=2021-12-28T03:43:35Z,host='192.168.230.174',id=248,instance_uuid=ca931f42-a2e2-4bbb-b6c1-d22874ea2352,internal_access_path=None,port=5903,token='***',updated_at=None) validate /usr/lib/python2.7/site-packages/nova/objects/console_auth_token.py:169
5
oslo_concurrency.lockutils [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -] Acquired lock "compute-rpcapi-router" lock /usr/lib/python2.7/site-packages/oslo_concurrency/lockutils.py:265
2021-12-28 11:43:36.154 96180 DEBUG oslo_concurrency.lockutils [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -] Releasing lock "compute-rpcapi-router" lock /usr/lib/python2.7/site-packages/oslo_concurrency/lockutils.py:281
6
nova.console.websocketproxy [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -]   2: connect info: {'instance_uuid': u'ca931f42-a2e2-4bbb-b6c1-d22874ea2352', 'access_url': u'http://192.168.230.173:6080/vnc_auto.html?path=%3Ftoken%3D441a97dd-35f1-42ba-8cd4-017430e6bde7', 'internal_access_path': None, 'token': '***', 'console_type': u'novnc', 'host': u'192.168.230.174', 'port': 5903}
2021-12-28 11:43:36.200 96180 INFO nova.console.websocketproxy [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -]   2: connecting to: 192.168.230.174:5903
7
nova.console.securityproxy.rfb [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -] Got version string 'RFB 003.008' from compute node connect /usr/lib/python2.7/site-packages/nova/console/securityproxy/rfb.py:107
2021-12-28 11:43:36.203 96180 DEBUG nova.console.securityproxy.rfb [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -] Got version string 'RFB 003.008' from tenant connect /usr/lib/python2.7/site-packages/nova/console/securityproxy/rfb.py:119
2021-12-28 11:43:36.204 96180 DEBUG nova.console.securityproxy.rfb [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -]   connect /usr/lib/python2.7/site-packages/nova/console/securityproxy/rfb.py:142
2021-12-28 11:43:36.204 96180 DEBUG nova.console.securityproxy.rfb [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -] The server sent security types [2] connect /usr/lib/python2.7/site-packages/nova/console/securityproxy/rfb.py:148
2021-12-28 11:43:36.205 96180 DEBUG nova.console.securityproxy.rfb [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -] =============3332=== connect /usr/lib/python2.7/site-packages/nova/console/securityproxy/rfb.py:168
2021-12-28 11:43:36.205 96180 DEBUG nova.console.securityproxy.rfb [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -] -------permitted auth types--[2] connect /usr/lib/python2.7/site-packages/nova/console/securityproxy/rfb.py:169
2021-12-28 11:43:36.206 96180 DEBUG nova.console.securityproxy.rfb [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -] =============4444========== connect /usr/lib/python2.7/site-packages/nova/console/securityproxy/rfb.py:172
2021-12-28 11:43:36.206 96180 DEBUG nova.console.securityproxy.rfb [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -] Using security type 1 with server, None with client connect /usr/lib/python2.7/site-packages/nova/console/securityproxy/rfb.py:184
2021-12-28 11:43:36.206 96180 DEBUG nova.console.securityproxy.rfb [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -] ---------compute sock---:<eventlet.greenio.base.GreenSocket object at 0x7fcf983a7b50> connect /usr/lib/python2.7/site-packages/nova/console/securityproxy/rfb.py:186
2021-12-28 11:43:36.207 96180 DEBUG nova.console.securityproxy.rfb [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -] ------after=====---compute sock---:<eventlet.greenio.base.GreenSocket object at 0x7fcf983a7b50> connect /usr/lib/python2.7/site-packages/nova/console/securityproxy/rfb.py:188
2021-12-28 11:43:36.207 96180 INFO nova.console.securityproxy.rfb [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -] Finished security handshake, resuming normal proxy mode using secured socket

8
nova.console.websocketproxy [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -]   2: 192.168.230.174:5903: Websocket client or target closed vmsg /usr/lib/python2.7/site-packages/websockify/websocket.py:291
2021-12-28 11:43:38.263 96180 INFO nova.console.websocketproxy [req-22d5fed7-3948-4b02-9a7d-1d7b4f60284a - - - - -] 192.168.31.113 - - [28/Dec/2021 11:43:38] code 400, message Bad request syntax ("\x88\x8f\x8e\xa1s\x8f\x8dI'\xee\xfc\xc6\x16\xfb\xae\xc2\x1f\xe0\xfd\xc4\x17")

```

