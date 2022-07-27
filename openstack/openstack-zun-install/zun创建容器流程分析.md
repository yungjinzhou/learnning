## stein版本zun在创建容器流程



### pecan处理

当向zun-api发送请求后，首先经过pecan处理，主要路由到对应的处理器以及参数校验等

```
# pecan/core.py    

    def __call__(self, environ, start_response):
        '''
        Implements the WSGI specification for Pecan applications, utilizing
        ``WebOb``.
        '''

        # create the request and response object
        req = self.request_cls(environ)
        #note: req: <Request at 0x7fa891fd4e50 POST http://192.168.230.173:9517/v1/containers/cf41abc5-0823-4add-9db4-04f0247b3486/volume_detach?cinder_volume_id=3dcc1a6a-0c1f-4e59-8ab4-479c66acede2>
        resp = self.response_cls()
        #note: resp: <Response at 0x7fa891fd4e90 200 OK>
        state = RoutingState(req, resp, self)
        #note: state: <pecan.core.RoutingState object at 0x7fa891fd4fd0>
        environ['pecan.locals'] = {
            'request': req,
            'response': resp
        }
        controller = None

        # track internal redirects
        internal_redirect = False

        # handle the request
        try:
            # add context and environment to the request
            req.context = environ.get('pecan.recursive.context', {})
            req.pecan = dict(content_type=None)

            controller, args, kwargs = self.find_controller(state)
            self.invoke_controller(controller, args, kwargs, state)
        except Exception as e:
            # if this is an HTTP Exception, set it as the response
            if isinstance(e, exc.HTTPException):
                # if the client asked for JSON, do our best to provide it
                accept_header = acceptparse.create_accept_header(
                    getattr(req.accept, 'header_value', '*/*') or '*/*')
                offers = accept_header.acceptable_offers(
                    ('text/plain', 'text/html', 'application/json'))
                best_match = offers[0][0] if offers else None
                state.response = e
                if best_match == 'application/json':
                    json_body = dumps({
                        'code': e.status_int,
                        'title': e.title,
                        'description': e.detail
                    })
                    if isinstance(json_body, six.text_type):
                        e.text = json_body
                    else:
                        e.body = json_body
                    state.response.content_type = best_match
                environ['pecan.original_exception'] = e

            # note if this is an internal redirect
            internal_redirect = isinstance(e, ForwardRequestException)

            # if this is not an internal redirect, run error hooks
            on_error_result = None
            if not internal_redirect:
                on_error_result = self.handle_hooks(
                    self.determine_hooks(state.controller),
                    'on_error',
                    state,
                    e
                )

            # if the on_error handler returned a Response, use it.
            if isinstance(on_error_result, WebObResponse):
                state.response = on_error_result
            else:
                if not isinstance(e, exc.HTTPException):
                    raise

            # if this is an HTTP 405, attempt to specify an Allow header
            if isinstance(e, exc.HTTPMethodNotAllowed) and controller:
                allowed_methods = _cfg(controller).get('allowed_methods', [])
                if allowed_methods:
                    state.response.allow = sorted(allowed_methods)
        finally:
            # if this is not an internal redirect, run "after" hooks
            if not internal_redirect:
                self.handle_hooks(
                    self.determine_hooks(state.controller),
                    'after',
                    state
                )

        self._handle_empty_response_body(state)

        # get the response
        return state.response(environ, start_response)



> /usr/lib/python2.7/site-packages/pecan/core.py(434)find_controller()

    def find_controller(self, state):
        '''
        The main request handler for Pecan applications.
        '''
        # get a sorted list of hooks, by priority (no controller hooks yet)
        req = state.request
        pecan_state = req.pecan

        # store the routing path for the current application to allow hooks to
        # modify it
        pecan_state['routing_path'] = path = req.path_info

        # handle "on_route" hooks
        self.handle_hooks(self.hooks, 'on_route', state)

        # lookup the controller, respecting content-type as requested
        # by the file extension on the URI
        pecan_state['extension'] = None

        # attempt to guess the content type based on the file extension
        if self.guess_content_type_from_ext \
                and not pecan_state['content_type'] \
                and '.' in path:
            _, extension = splitext(path.rstrip('/'))

            # preface with a letter to ensure compat for 2.5
            potential_type = guess_type('x' + extension)[0]

            if extension and potential_type is not None:
                path = ''.join(path.rsplit(extension, 1))
                pecan_state['extension'] = extension
                pecan_state['content_type'] = potential_type

        #note: req: <Request at 0x7fa891fd4e50 POST http://192.168.230.173:9517/v1/containers/cf41abc5-0823-4add-9db4-04f0247b3486/volume_detach?cinder_volume_id=3dcc1a6a-0c1f-4e59-8ab4-479c66acede2>
        #note: self.root: <zun.api.controllers.root.RootController object at 0x7fa892125450>
        #note: path: '/v1/containers/cf41abc5-0823-4add-9db4-04f0247b3486/volume_detach'
        controller, remainder = self.route(req, self.root, path)
        cfg = _cfg(controller)

        if cfg.get('generic_handler'):
            raise exc.HTTPNotFound

        # handle generic controllers
        im_self = None
        if cfg.get('generic'):
            im_self = six.get_method_self(controller)
            handlers = cfg['generic_handlers']
            controller = handlers.get(req.method, handlers['DEFAULT'])
            handle_security(controller, im_self)
            cfg = _cfg(controller)

        # add the controller to the state so that hooks can use it
        state.controller = controller

        # if unsure ask the controller for the default content type
        content_types = cfg.get('content_types', {})
        if not pecan_state['content_type']:
            # attempt to find a best match based on accept headers (if they
            # exist)
            accept = getattr(req.accept, 'header_value', '*/*') or '*/*'
            if accept == '*/*' or (
                    accept.startswith('text/html,') and
                    list(content_types.keys()) in self.SIMPLEST_CONTENT_TYPES):
                pecan_state['content_type'] = cfg.get(
                    'content_type',
                    'text/html'
                )
            else:
                best_default = None
                accept_header = acceptparse.create_accept_header(accept)
                offers = accept_header.acceptable_offers(
                    list(content_types.keys())
                )
                if offers:
                    # If content type matches exactly use matched type
                    best_default = offers[0][0]
                else:
                    # If content type doesn't match exactly see if something
                    # matches when not using parameters
                    for k in content_types.keys():
                        if accept.startswith(k):
                            best_default = k
                            break

                if best_default is None:
                    msg = "Controller '%s' defined does not support " + \
                          "content_type '%s'. Supported type(s): %s"
                    logger.error(
                        msg % (
                            controller.__name__,
                            pecan_state['content_type'],
                            content_types.keys()
                        )
                    )
                    raise exc.HTTPNotAcceptable()

                pecan_state['content_type'] = best_default
        elif cfg.get('content_type') is not None and \
                pecan_state['content_type'] not in content_types:

            msg = "Controller '%s' defined does not support content_type " + \
                  "'%s'. Supported type(s): %s"
            logger.error(
                msg % (
                    controller.__name__,
                    pecan_state['content_type'],
                    content_types.keys()
                )
            )
            raise exc.HTTPNotFound

        # fetch any parameters
        if req.method == 'GET':
            params = req.GET
        elif req.content_type in ('application/json',
                                  'application/javascript'):
            try:
                if not isinstance(req.json, dict):
                    raise TypeError('%s is not a dict' % req.json)
                params = NestedMultiDict(req.GET, req.json)
            except (TypeError, ValueError):
                params = req.params
        else:
            params = req.params

        # fetch the arguments for the controller
        args, varargs, kwargs = self.get_args(
            state,
            params.mixed(),
            remainder,
            cfg['argspec'],
            im_self
        )
        state.arguments = Arguments(args, varargs, kwargs)

        # handle "before" hooks
        self.handle_hooks(self.determine_hooks(controller), 'before', state)

        return controller, args + varargs, kwargs


> /usr/lib/python2.7/site-packages/pecan/core.py(292)route()


    def route(self, req, node, path):
        '''
        Looks up a controller from a node based upon the specified path.

        :param node: The node, such as a root controller object.
        :param path: The path to look up on this node.
        '''
        path = path.split('/')[1:]
        try:
            node, remainder = lookup_controller(node, path, req)
            return node, remainder
        except NonCanonicalPath as e:
            if self.force_canonical and \
                    not _cfg(e.controller).get('accept_noncanonical', False):
                if req.method == 'POST':
                    raise RuntimeError(
                        "You have POSTed to a URL '%s' which "
                        "requires a slash. Most browsers will not maintain "
                        "POST data when redirected. Please update your code "
                        "to POST to '%s/' or set force_canonical to False" %
                        (req.pecan['routing_path'],
                            req.pecan['routing_path'])
                    )
                redirect(code=302, add_slash=True, request=req)
            return e.controller, e.remainder



> /usr/lib/python2.7/site-packages/pecan/routing.py(127)lookup_controller()


def lookup_controller(obj, remainder, request=None):
    '''
    Traverses the requested url path and returns the appropriate controller
    object, including default routes.

    Handles common errors gracefully.
    '''
    if request is None:
        warnings.warn(
            (
                "The function signature for %s.lookup_controller is changing "
                "in the next version of pecan.\nPlease update to: "
                "`lookup_controller(self, obj, remainder, request)`." % (
                    __name__,
                )
            ),
            DeprecationWarning
        )

    notfound_handlers = []
    while True:
        try:
            obj, remainder = find_object(obj, remainder, notfound_handlers,
                                         request)
            handle_security(obj)
            return obj, remainder
        except (exc.HTTPNotFound, exc.HTTPMethodNotAllowed,
                PecanNotFound) as e:
            if isinstance(e, PecanNotFound):
                e = exc.HTTPNotFound()
            while notfound_handlers:
                name, obj, remainder = notfound_handlers.pop()
                if name == '_default':
                    # Notfound handler is, in fact, a controller, so stop
                    #   traversal
                    return obj, remainder
                else:
                    # Notfound handler is an internal redirect, so continue
                    #   traversal
                    result = handle_lookup_traversal(obj, remainder)
                    if result:
                        # If no arguments are passed to the _lookup, yet the
                        # argspec requires at least one, raise a 404
                        if (
                            remainder == [''] and
                            len(obj._pecan['argspec'].args) > 1
                        ):
                            raise e
                        obj_, remainder_ = result
                        return lookup_controller(obj_, remainder_, request)
            else:
                raise e



> /usr/lib/python2.7/site-packages/pecan/routing.py(196)find_object()

def find_object(obj, remainder, notfound_handlers, request):
    '''
    'Walks' the url path in search of an action for which a controller is
    implemented and returns that controller object along with what's left
    of the remainder.
    '''
    prev_obj = None
    while True:
        if obj is None:
            raise PecanNotFound
        if iscontroller(obj):
            if getattr(obj, 'custom_route', None) is None:
                return obj, remainder

        _detect_custom_path_segments(obj)

        if remainder:
            custom_route = __custom_routes__.get((obj.__class__, remainder[0]))
            if custom_route:
                return getattr(obj, custom_route), remainder[1:]

        # are we traversing to another controller
        cross_boundary(prev_obj, obj)
        try:
            next_obj, rest = remainder[0], remainder[1:]
            if next_obj == '':
                index = getattr(obj, 'index', None)
                if iscontroller(index):
                    return index, rest
        except IndexError:
            # the URL has hit an index method without a trailing slash
            index = getattr(obj, 'index', None)
            if iscontroller(index):
                raise NonCanonicalPath(index, [])

        default = getattr(obj, '_default', None)
        if iscontroller(default):
            notfound_handlers.append(('_default', default, remainder))

        lookup = getattr(obj, '_lookup', None)
        if iscontroller(lookup):
            notfound_handlers.append(('_lookup', lookup, remainder))

        route = getattr(obj, '_route', None)
        if iscontroller(route):
            if len(getargspec(route).args) == 2:
                warnings.warn(
                    (
                        "The function signature for %s.%s._route is changing "
                        "in the next version of pecan.\nPlease update to: "
                        "`def _route(self, args, request)`." % (
                            obj.__class__.__module__,
                            obj.__class__.__name__
                        )
                    ),
                    DeprecationWarning
                )
                next_obj, next_remainder = route(remainder)
            else:
                next_obj, next_remainder = route(remainder, request)
            cross_boundary(route, next_obj)
            #note: route: 
            #note: next_obj: <bound method ContainersController.post of <zun.api.controllers.v1.containers.ContainersController object at 0x7fe71451a390>>
            #note: next_remainder: [u'cf41abc5-0823-4add-9db4-04f0247b3486', u'volume_detach']
            return next_obj, next_remainder

        if not remainder:
            raise PecanNotFound

        prev_remainder = remainder
        prev_obj = obj
        remainder = rest
        try:
            obj = getattr(obj, next_obj, None)
        except UnicodeEncodeError:
            obj = None

        # Last-ditch effort: if there's not a matching subcontroller, no
        # `_default`, no `_lookup`, and no `_route`, look to see if there's
        # an `index` that has a generic method defined for the current request
        # method.
        if not obj and not notfound_handlers and hasattr(prev_obj, 'index'):
            if request.method in _cfg(prev_obj.index).get('generic_handlers',
                                                          {}):
                return prev_obj.index, prev_remainder



调用/usr/lib/python2.7/site-packages/pecan/rest.py(142)_route()


    @expose()
    def _route(self, args, request=None):
        '''
        Routes a request to the appropriate controller and returns its result.

        Performs a bit of validation - refuses to route delete and put actions
        via a GET request).
        '''
        if request is None:
            from pecan import request
        # convention uses "_method" to handle browser-unsupported methods
        method = request.params.get('_method', request.method).lower()

        # make sure DELETE/PUT requests don't use GET
        if request.method == 'GET' and method in ('delete', 'put'):
            abort(405)

        # check for nested controllers
        result = self._find_sub_controllers(args, request)
        if result:
            return result

        # handle the request
        handler = getattr(
            self,
            '_handle_%s' % method,
            self._handle_unknown_method
        )

        try:
            if len(getargspec(handler).args) == 3:
                result = handler(method, args)
            else:
                result = handler(method, args, request)

            #
            # If the signature of the handler does not match the number
            # of remaining positional arguments, attempt to handle
            # a _lookup method (if it exists)
            #
            argspec = self._get_args_for_controller(result[0])
            #note :argspec: ['run']
            num_args = len(argspec)
            if num_args < len(args):
                _lookup_result = self._handle_lookup(args, request)
                if _lookup_result:
                    return _lookup_result
        except (exc.HTTPClientError, exc.HTTPNotFound,
                exc.HTTPMethodNotAllowed) as e:
            #
            # If the matching handler results in a 400, 404, or 405, attempt to
            # handle a _lookup method (if it exists)
            #
            _lookup_result = self._handle_lookup(args, request)
            if _lookup_result:
                return _lookup_result

            # Build a correct Allow: header
            if isinstance(e, exc.HTTPMethodNotAllowed):

                def method_iter():
                    for func in ('get', 'get_one', 'get_all', 'new', 'edit',
                                 'get_delete'):
                        if self._find_controller(func):
                            yield 'GET'
                            break
                    for method in ('HEAD', 'POST', 'PUT', 'DELETE', 'TRACE',
                                   'PATCH'):
                        func = method.lower()
                        if self._find_controller(func):
                            yield method

                e.allow = sorted(method_iter())

            raise

        # return the result
        #note: result: (<bound method ContainersController.post of <zun.api.controllers.v1.containers.ContainersController object at 0x7f1717959390>>, [u'cf41abc5-0823-4add-9db4-04f0247b3486', u'volume_detach'])
        return result




> /usr/lib/python2.7/site-packages/pecan/routing.py(127)lookup_controller()

def lookup_controller(obj, remainder, request=None):
    '''
    Traverses the requested url path and returns the appropriate controller
    object, including default routes.

    Handles common errors gracefully.
    '''
    if request is None:
        warnings.warn(
            (
                "The function signature for %s.lookup_controller is changing "
                "in the next version of pecan.\nPlease update to: "
                "`lookup_controller(self, obj, remainder, request)`." % (
                    __name__,
                )
            ),
            DeprecationWarning
        )

    notfound_handlers = []
    while True:
        try:
            obj, remainder = find_object(obj, remainder, notfound_handlers,
                                         request)
            handle_security(obj)
            return obj, remainder
        except (exc.HTTPNotFound, exc.HTTPMethodNotAllowed,
                PecanNotFound) as e:
            if isinstance(e, PecanNotFound):
                e = exc.HTTPNotFound()
            while notfound_handlers:
                name, obj, remainder = notfound_handlers.pop()
                if name == '_default':
                    # Notfound handler is, in fact, a controller, so stop
                    #   traversal
                    return obj, remainder
                else:
                    # Notfound handler is an internal redirect, so continue
                    #   traversal
                    result = handle_lookup_traversal(obj, remainder)
                    if result:
                        # If no arguments are passed to the _lookup, yet the
                        # argspec requires at least one, raise a 404
                        if (
                            remainder == [''] and
                            len(obj._pecan['argspec'].args) > 1
                        ):
                            raise e
                        obj_, remainder_ = result
                        return lookup_controller(obj_, remainder_, request)
            else:
                raise e


> /usr/lib/python2.7/site-packages/pecan/rest.py(350)_handle_post()


    def _handle_post(self, method, remainder, request=None):
        '''
        Routes ``POST`` requests.
        '''
        if request is None:
        #note: request: <pecan.core.ObjectProxy object at 0x7fe71a3c2b10>
            self._raise_method_deprecation_warning(self._handle_post)

        # check for custom POST/PUT requests
        if remainder:
        #note: remainder： [u'cf41abc5-0823-4add-9db4-04f0247b3486', u'volume_detach']
            match = self._handle_custom_action(method, remainder, request)
            if match:
                return match

            controller = self._lookup_child(remainder[0])
            if controller and not ismethod(controller):
                return lookup_controller(controller, remainder[1:], request)

        # check for regular POST/PUT requests
        controller = self._find_controller(method)
        #note: controller: <bound method ContainersController.post of <zun.api.controllers.v1.containers.ContainersController object at 0x7f1717959390>>
        if controller:
            return controller, remainder

        abort(405)


> /usr/lib/python2.7/site-packages/pecan/rest.py(375)_handle_custom_action()


    def _handle_custom_action(self, method, remainder, request=None):
        if request is None:
            self._raise_method_deprecation_warning(self._handle_custom_action)

        remainder = [r for r in remainder if r]
        if remainder:
            if method in ('put', 'delete'):
                # For PUT and DELETE, additional arguments are supplied, e.g.,
                # DELETE /foo/XYZ
                method_name = remainder[0]
                remainder = remainder[1:]
            else:
                method_name = remainder[-1]
                remainder = remainder[:-1]
            if method.upper() in self._custom_actions.get(method_name, []):
                controller = self._find_controller(
                    '%s_%s' % (method, method_name),
                    method_name
                )
                if controller:
                    return controller, remainder



    #note: use in pecan/rest.py._route()
    def _find_sub_controllers(self, remainder, request):
        '''
        Identifies the correct controller to route to by analyzing the
        request URI.
        '''
        # need either a get_one or get to parse args
        method = None
        for name in ('get_one', 'get'):
            if hasattr(self, name):
                method = name
                break
        if not method:
            return

        # get the args to figure out how much to chop off
        args = self._get_args_for_controller(getattr(self, method))
        fixed_args = len(args) - len(
            request.pecan.get('routing_args', [])
        )
        var_args = getargspec(getattr(self, method)).varargs

        # attempt to locate a sub-controller
        if var_args:
            for i, item in enumerate(remainder):
                controller = self._lookup_child(item)
                if controller and not ismethod(controller):
                    self._set_routing_args(request, remainder[:i])
                    return lookup_controller(controller, remainder[i + 1:],
                                             request)
        elif fixed_args < len(remainder) and hasattr(
            self, remainder[fixed_args]
        ):
            controller = self._lookup_child(remainder[fixed_args])
            if not ismethod(controller):
                self._set_routing_args(request, remainder[:fixed_args])
                return lookup_controller(
                    controller,
                    remainder[fixed_args + 1:],
                    request
                )


> /usr/lib/python2.7/site-packages/zun/api/controllers/v1/__init__.py(225)_route()-
>(<bound m...2125210>>, [u'cf41ab...247b3486', u'volume_detach'])


> /usr/lib/python2.7/site-packages/zun/api/controllers/root.py(97)_route()->(<bound m...451a390>>, [u'cf41ab...247b3486', u'volume_detach'])


> /usr/lib/python2.7/site-packages/eventlet/wsgi.py(379)handle()






```









### zun-api启动

/usr/bin/zun-api

```
#!/usr/bin/python
# PBR Generated from u'console_scripts'

import sys

from zun.cmd.api import main


if __name__ == "__main__":
    sys.exit(main())

```

#### api程序入口

从zun.cmd.api开始分析

main函数主要内容，读取配置文件，启动wsgi服务

以创建容器为例

 http://controller:9517/v1/containers/7becd252-b619-402d-a989-b6c1128b4c5c    post

#### 创建入口

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

#### 调用do_post

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

#### 调用compute/api.py



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


    def _record_action_start(self, context, container, action):
        objects.ContainerAction.action_start(context, container.uuid,
                                             action, want_result=False)

```



container_create首先调用scheduler，然后调用  self._record_action_start操作数据库，

最后发送rpcapi请求到zun-compute

##### 调度host

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



zun/scheduler/filter_scheduler.py

```

class FilterScheduler(driver.Scheduler):
    """Scheduler that can be used for filtering zun compute."""

    def __init__(self):
        super(FilterScheduler, self).__init__()
        self.filter_handler = filters.HostFilterHandler()
        filter_classes = self.filter_handler.get_matching_classes(
            CONF.scheduler.available_filters)
        self.filter_cls_map = {cls.__name__: cls for cls in filter_classes}
        self.filter_obj_map = {}
        self.enabled_filters = self._choose_host_filters(self._load_filters())

    def _schedule(self, context, container, extra_spec):
        """Picks a host according to filters."""
        services = self._get_services_by_host(context)
        nodes = objects.ComputeNode.list(context)
        hosts = services.keys()
        target_host = extra_spec.pop("target_host", None)
        if target_host and target_host in hosts:
            hosts = [target_host]
        nodes = [node for node in nodes if node.hostname in hosts]
        host_states = self.get_all_host_state(nodes, services)
        hosts = self.filter_handler.get_filtered_objects(self.enabled_filters,
                                                         host_states,
                                                         container,
                                                         extra_spec)
        if not hosts:
            msg = _("Is the appropriate service running?")
            raise exception.NoValidHost(reason=msg)

        return random.choice(hosts)


    def select_destinations(self, context, containers, extra_spec):
        """Selects destinations by filters."""
        dests = []
        for container in containers:
            host = self._schedule(context, container, extra_spec)
            host_state = dict(host=host.hostname, nodename=None,
                              limits=host.limits)
            dests.append(host_state)

        if len(dests) < 1:
            reason = _('There are not enough hosts available.')
            raise exception.NoValidHost(reason=reason)

        return dests

```



##### rpcapi请求

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



### zun-compute

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

```
# zun/container/docker/driver.py


    def create(self, context, container, image, requested_networks,
               requested_volumes):
        with docker_utils.docker_client() as docker:
            network_api = zun_network.api(context=context, docker_api=docker)
            name = container.name
            LOG.debug('Creating container with image %(image)s name %(name)s',
                      {'image': image['image'], 'name': name})
            self._provision_network(context, network_api, requested_networks)
            volmaps = requested_volumes.get(container.uuid, [])
            binds = self._get_binds(context, volmaps)
            kwargs = {
                'name': self.get_container_name(container),
                'command': container.command,
                'environment': container.environment,
                'working_dir': container.workdir,
                'labels': container.labels,
                'tty': container.interactive,
                'stdin_open': container.interactive,
                'hostname': container.hostname,
            }

            if not self._is_runtime_supported():
                if container.runtime:
                    raise exception.ZunException(_(
                        'Specifying runtime in Docker API is not supported'))
                runtime = None
            else:
                runtime = container.runtime or CONF.container_runtime

            host_config = {}
            host_config['privileged'] = container.privileged
            host_config['runtime'] = runtime
            host_config['binds'] = binds
            kwargs['volumes'] = [b['bind'] for b in binds.values()]
            self._process_exposed_ports(network_api.neutron_api, container)
            self._process_networking_config(
                context, container, requested_networks, host_config,
                kwargs, docker)
            if container.auto_remove:
                host_config['auto_remove'] = container.auto_remove
            if container.memory is not None:
                host_config['mem_limit'] = str(container.memory) + 'M'
            if container.cpu is not None:
                host_config['cpu_quota'] = int(100000 * container.cpu)
                host_config['cpu_period'] = 100000
            if container.restart_policy:
                count = int(container.restart_policy['MaximumRetryCount'])
                name = container.restart_policy['Name']
                host_config['restart_policy'] = {'Name': name,
                                                 'MaximumRetryCount': count}

            if container.disk:
                disk_size = str(container.disk) + 'G'
                host_config['storage_opt'] = {'size': disk_size}
            if container.cpu_policy == 'dedicated':
                host_config['cpuset_cpus'] = container.cpuset.cpuset_cpus
                host_config['cpuset_mems'] = str(container.cpuset.cpuset_mems)
            # The time unit in docker of heath checking is us, and the unit
            # of interval and timeout is seconds.
            if container.healthcheck:
                healthcheck = {}
                healthcheck['test'] = container.healthcheck.get('test', '')
                interval = container.healthcheck.get('interval', 0)
                healthcheck['interval'] = interval * 10 ** 9
                healthcheck['retries'] = int(container.healthcheck.
                                             get('retries', 0))
                timeout = container.healthcheck.get('timeout', 0)
                healthcheck['timeout'] = timeout * 10 ** 9
                kwargs['healthcheck'] = healthcheck

            kwargs['host_config'] = docker.create_host_config(**host_config)
            if image['tag']:
                image_repo = image['repo'] + ":" + image['tag']
            else:
                image_repo = image['repo']
            response = docker.create_container(image_repo, **kwargs)
            container.container_id = response['Id']

            addresses = self._setup_network_for_container(
                context, container, requested_networks, network_api)
            container.addresses = addresses

            response = docker.inspect_container(container.container_id)
            self._populate_container(container, response)
            container.save(context)
            return container

```







zun-compute 负责 container 创建，代码位于 zun/compute/manager.py，过程如下:



1. wait for volumes avaiable: 等待 volume 创建完成，状态变为 avaiable。
2. attach volumes：挂载 volumes，挂载过程后面再介绍。
3. checksupportdisk_quota: 如果使用本地盘，检查本地的 quota 配额。
4. pull or load image: 调用 Docker 拉取或者加载镜像。
5. 创建 docker network、创建 neutron port，这个步骤下面详细介绍。

```
# zun/container/docker/driver.py

    def _provision_network(self, context, network_api, requested_networks):
        for rq_network in requested_networks:
            self._get_or_create_docker_network(
                context, network_api, rq_network['network'])


    def _get_or_create_docker_network(self, context, network_api,
                                      neutron_net_id):
        docker_net_name = self._get_docker_network_name(context,
                                                        neutron_net_id)
        docker_networks = network_api.list_networks(names=[docker_net_name])
        if not docker_networks:
            network_api.create_network(neutron_net_id=neutron_net_id,
                                       name=docker_net_name)

```

创建网络

```
# zun/network/kuryr_network.py


    def create_network(self, name, neutron_net_id):
        """Create a docker network with Kuryr driver.

        The docker network to be created will be based on the specified
        neutron net. It is assumed that the neutron net will have one
        or two subnets. If there are two subnets, it must be a ipv4
        subnet and a ipv6 subnet and containers created from this network
        will have both ipv4 and ipv6 addresses.

        What this method does is finding the subnets under the specified
        neutron net, retrieving the cidr, gateway of each
        subnet, and compile the list of parameters for docker.create_network.
        """
        # find a v4 and/or v6 subnet of the network
        shared = \
            self.neutron_api.get_neutron_network(neutron_net_id)[
                'shared']
        subnets = self.neutron_api.list_subnets(network_id=neutron_net_id)
        subnets = subnets.get('subnets', [])
        v4_subnet = self._get_subnet(subnets, ip_version=4)
        v6_subnet = self._get_subnet(subnets, ip_version=6)
        if not v4_subnet and not v6_subnet:
            raise exception.ZunException(_(
                "The Neutron network %s has no subnet") % neutron_net_id)

        # IPAM driver specific options
        ipam_options = {
            "Driver": CONF.network.driver_name,
            "Options": {
                'neutron.net.shared': str(shared)
            },
            "Config": []
        }

        # Driver specific options
        options = {
            'neutron.net.uuid': neutron_net_id,
            'neutron.net.shared': str(shared)
        }

        if v4_subnet:
            ipam_options['Options']['neutron.subnet.uuid'] = \
                v4_subnet.get('id')
            ipam_options["Config"].append({
                "Subnet": v4_subnet['cidr'],
                "Gateway": v4_subnet['gateway_ip']
            })

            options['neutron.subnet.uuid'] = v4_subnet.get('id')
        if v6_subnet:
            ipam_options['Options']['neutron.subnet.v6.uuid'] = \
                v6_subnet.get('id')
            ipam_options["Config"].append({
                "Subnet": v6_subnet['cidr'],
                "Gateway": v6_subnet['gateway_ip']
            })

            options['neutron.subnet.v6.uuid'] = v6_subnet.get('id')

        network_dict = {}
        network_dict['project_id'] = self.context.project_id
        network_dict['user_id'] = self.context.user_id
        network_dict['name'] = name
        network_dict['neutron_net_id'] = neutron_net_id
        network = objects.Network(self.context, **network_dict)

        for attempt in (1, 2, 3):
            LOG.debug("Attempt (%s) to create network: %s", attempt, network)
            created_network = self._create_network_attempt(
                network, options, ipam_options)
            if created_network:
                return created_network
            time.sleep(1)

        raise exception.ZunException(_(
            "Cannot create docker network after several attempts %s"))

    def _create_network_attempt(self, network, options, ipam_options):
        # The DB model has unique constraint on 'neutron_net_id' field
        # which will guarantee only one request can create the network in here
        # (and call docker.create_network later) if there are concurrent
        # requests on creating networks for the same neutron net.
        try:
            network.create(self.context)
        except exception.NetworkAlreadyExists as e:
            if e.field != 'neutron_net_id':
                raise

            networks = objects.Network.list(
                self.context,
                filters={'neutron_net_id': network.neutron_net_id})
            LOG.debug("network objects with 'neutron_net_id' as '%(net_id)s': "
                      "%(networks)s",
                      {"net_id": network.neutron_net_id,
                       "networks": networks})
            docker_networks = self.list_networks(names=[network.name])
            LOG.debug("docker networks with name matching '%(name)s': "
                      "%(networks)s",
                      {"name": network.name,
                       "networks": docker_networks})
            if (networks and networks[0].network_id and
                    docker_networks and
                    networks[0].network_id == docker_networks[0]['Id']):
                LOG.debug("Network (%s) has already been created in docker",
                          network.name)
                return networks[0]
            else:
                # Probably, there are concurrent requests on creating the
                # network but the network is yet created in Docker.
                # We return False and let the caller retry.
                return False

        LOG.debug("Calling docker.create_network to create network %s, "
                  "ipam_options %s, options %s",
                  network.name, ipam_options, options)
        enable_ipv6 = bool(options.get('neutron.subnet.v6.uuid'))
        try:
            docker_network = self.docker.create_network(
                name=network.name,
                driver=CONF.network.driver_name,
                enable_ipv6=enable_ipv6,
                options=options,
                ipam=ipam_options)
        except Exception:
            with excutils.save_and_reraise_exception():
                network.destroy()

        network.network_id = docker_network['Id']
        network.save()
        return network

```

其中network.create(self.context)是写入数据库

```

# zun/objects/network.py

    @base.remotable
    def create(self, context):
        """Create a Network record in the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Network(context)

        """
        values = self.obj_get_changes()
        db_network = dbapi.create_network(context, values)
        self._from_db_object(self, db_network)
```

​    docker_network = self.docker.create_network是docker创建网络

```
# self.docker
# zun.container.docker.utils.DockerHTTPClient object at 0x7fec5bc93390

# docker/api/network.py


    def create_network(self, name, driver=None, options=None, ipam=None,
                       check_duplicate=None, internal=False, labels=None,
                       enable_ipv6=False, attachable=None, scope=None,
                       ingress=None):
        """
        Create a network. Similar to the ``docker network create``.

        Args:
            name (str): Name of the network
            driver (str): Name of the driver used to create the network
            options (dict): Driver options as a key-value dictionary
            ipam (IPAMConfig): Optional custom IP scheme for the network.
            check_duplicate (bool): Request daemon to check for networks with
                same name. Default: ``None``.
            internal (bool): Restrict external access to the network. Default
                ``False``.
            labels (dict): Map of labels to set on the network. Default
                ``None``.
            enable_ipv6 (bool): Enable IPv6 on the network. Default ``False``.
            attachable (bool): If enabled, and the network is in the global
                scope,  non-service containers on worker nodes will be able to
                connect to the network.
            scope (str): Specify the network's scope (``local``, ``global`` or
                ``swarm``)
            ingress (bool): If set, create an ingress network which provides
                the routing-mesh in swarm mode.

        Returns:
            (dict): The created network reference object

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.

        Example:
            A network using the bridge driver:

                >>> client.api.create_network("network1", driver="bridge")

            You can also create more advanced networks with custom IPAM
            configurations. For example, setting the subnet to
            ``192.168.52.0/24`` and gateway address to ``192.168.52.254``.

            .. code-block:: python

                >>> ipam_pool = docker.types.IPAMPool(
                    subnet='192.168.52.0/24',
                    gateway='192.168.52.254'
                )
                >>> ipam_config = docker.types.IPAMConfig(
                    pool_configs=[ipam_pool]
                )
                >>> client.api.create_network("network1", driver="bridge",
                                                 ipam=ipam_config)
        """
        if options is not None and not isinstance(options, dict):
            raise TypeError('options must be a dictionary')

        data = {
            'Name': name,
            'Driver': driver,
            'Options': options,
            'IPAM': ipam,
            'CheckDuplicate': check_duplicate,
        }

        if labels is not None:
            if version_lt(self._version, '1.23'):
                raise InvalidVersion(
                    'network labels were introduced in API 1.23'
                )
            if not isinstance(labels, dict):
                raise TypeError('labels must be a dictionary')
            data["Labels"] = labels

        if enable_ipv6:
            if version_lt(self._version, '1.23'):
                raise InvalidVersion(
                    'enable_ipv6 was introduced in API 1.23'
                )
            data['EnableIPv6'] = True

        if internal:
            if version_lt(self._version, '1.22'):
                raise InvalidVersion('Internal networks are not '
                                     'supported in API version < 1.22')
            data['Internal'] = True

        if attachable is not None:
            if version_lt(self._version, '1.24'):
                raise InvalidVersion(
                    'attachable is not supported in API version < 1.24'
                )
            data['Attachable'] = attachable

        if ingress is not None:
            if version_lt(self._version, '1.29'):
                raise InvalidVersion(
                    'ingress is not supported in API version < 1.29'
                )

            data['Ingress'] = ingress

        if scope is not None:
            if version_lt(self._version, '1.30'):
                raise InvalidVersion(
                    'scope is not supported in API version < 1.30'
                )
            data['Scope'] = scope

        url = self._url("/networks/create")
        res = self._post_json(url, data=data)
        return self._result(res, json=True)

```





1. create container: 调用 Docker 创建容器。
2. container start: 调用 Docker 启动容器。



以上调用 Dokcer 拉取镜像、创建容器、启动容器的代码位于 zun/container/docker/driver.py，该模块基本就是对社区 Docker SDK for Python 的封装。







## 支持指定host创建容器

修改代码

zun/api/controllers/v1/containers.py

```

    def _do_post(self, run=False, **container_dict):
    ......
        extra_spec = {}
        target_host = container_dict.pop("host", None)
        if target_host:
            extra_spec['target_host'] = target_host
     ......
     
```

zun/scheduler/filter_scheduler.py

```

    def _schedule(self, context, container, extra_spec):
        """Picks a host according to filters."""
        ......
        hosts = services.keys()
        target_host = extra_spec.pop("target_host", None)
        if target_host and target_host in hosts:
            hosts = [target_host]
         ......
```

zun/api/controllers/v1/schemas/containers.py

```

_legacy_container_properties = {
    ......
    "host": parameter_types.host,
    ......
}

```

zun/api/controllers/v1/schemas/parameter_types.py

```
......
host = {
    'type': 'string', 'minLength': 1, 'maxLength': 255,
    # target host
    'pattern': '^[a-zA-Z0-9-._]*$',
}
......
```







## 容器网络问题

kuryr-libnetwork设置为global时，在一个zun-compute节点创建该docker网络，会同步在其他节点创建，同步代码逻辑暂时没有定位到。



kuryr-libnetwork 和neutron交互逻辑没有分析

