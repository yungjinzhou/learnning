## stein版本gnocchi-4.3.2源码解析

### 1. gnochi架构介绍

#### 1.1 服务模块介绍

Gnocchi：用于将采集数据进行计算合并和存储并提供rest api方式接收和查询监控数据

![img](.\企业微信截图_16291872131546.png)



从图可以看出Gnocchi的服务主要包含两大服务，API和Metricd服务。同时可以看到有三个存储，Measure Storage、Aggregate Storage和Index。

**Measure Storage**：是经过ceilometer-agent-notification服务处理后发送过来的数据，是实际的监控数据，但这些数据还需要经过gnocchi服务处理，处理后就会删除掉。比如这部分数据就可以保存到file中，当然也支持保存到ceph，但这属于临时数据，所以用file保存就可以了。

**Aggregate Storage**：Aggreate是总数、合计的意思，gnocchi服务采用的是一种独特的时间序列存储方法，这个存储存放的是按照预定义的策略进行聚合计算后的数据，这样在获取监控数据展示时速度就会很快，因为已经计算过了。用户看到的是这层数据。后端存储包括file、swift、ceph，influxdb，默认使用file。可以保存到ceph中，这样可在任意一个节点上获取，但由于存储的都是大量小文件，大量的小文件对ceph来说并不友好。

**Index**：通常是一个关系型数据库（比如MYSQL），是监控数据的元数据，用以索引取出resources和metrics，使得可以快速的从Measure Storage和Aggregate Storage中取出所需要的数据。

**API**：gnocchi-api服务进程，可以托管到httpd服务一起启动，通过Indexer和Storage的driver，提供查询和操作ArchivePolicy，Resource，Metric，Measure的接口，并将新到来的Measure（也就是ceilometer-agent-notification发送到gnocchi-api服务的数据）存入Measure Storage。

**Metricd**：gnocchi-metricd服务进程，根据Metric定义的ArchivePolicy规则周期性的从Measure Storage中获取未处理的Measure数据并进行处理，将处理结果保存到Aggregate Storage中，同时也对Aggregate Storage中的数据进行聚合计算和清理过期的数据。

API和Metricd服务都是设计成了无状态的服务，可以横向拓展来加快数据的处理。

#### 1.2 主要数据介绍

Gnocchi中有三层数据，resources -> metric -> measure

**Resource**：是gnocchi对openstack监控数据的一个大体的划分，比如虚拟机的磁盘的所有监控资源作为一个resource，可用命令gnocchi resource list查看

**Metric**：是gnocchi对openstack监控数据的第二层划分，归属于resource，代表一个较具体的资源，比如cpu值，可用命令gnocchi metric list查看

**Measure**：是gnocchi对openstack监控数据的第三层划分，归属于metric，表示在某个时间戳对应资源的值，可用命令gnocchi measures show metric_id



### 2. gnocchi-api启动流程

telemetry项目主要使用的pecan框架，如gnocchi采用的是**paste.deploy+pecan**实现。

#### 2.1 初始代码加载

systemctl start gnochi-api.service中，实际执行的/usr/bin/gnocchi-api

```
# /usr/bin/gnocchi-api执行内容如下：

from gnocchi.cli import api

if __name__ == '__main__':
    sys.exit(api.api())
else:
    application = api.wsgi()

```



而gnocchi/rest/wsgi.py中

```
from gnocchi.cli import api
from gnocchi.rest import app
application = app.load_app(api.prepare_service())
```



先看api.prepare_service()

```
# gnocchi/cli/api.py


def prepare_service(conf=None):
    if conf is None:
        conf = cfg.ConfigOpts()

    opts.set_defaults()
    policy_opts.set_defaults(conf)
    conf = service.prepare_service(conf=conf)
    cfg_path = conf.oslo_policy.policy_file
    if not os.path.isabs(cfg_path):
        cfg_path = conf.find_file(cfg_path)
    if cfg_path is None or not os.path.exists(cfg_path):
        cfg_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   '..', 'rest', 'policy.json'))
    conf.set_default('policy_file', cfg_path, group='oslo_policy')
    return conf
  
  
  
  
 # conf具体值如下，就是加载了gnocchi.conf下的配置，实例化，还有其他配置
 
  {
	'_namespace': _Namespace(_conf = < oslo_config.cfg.ConfigOpts object at 0x7f13088b3ad0 > , _config_dirs = [], _emitted_deprecations = set([]), _files_not_found = [], _files_permission_denied = [], _normalized = [{
		'statsd': {},
		'incoming': {
			'redis_url': ['redis://controller:6379?db=5']
		},
		'metricd': {
			'metric_reporting_delay': ['120'],
			'metric_processing_delay': ['60'],
			......
		},
		'DEFAULT': {
			'debug': ['true'],
			'parallel_operations': ['200'],
			......
		},
		'keystone_authtoken': {
			'auth_type': ['password'],
			......
		},
		'oslo_policy': {}
	}, ....
	}], _parsed = [{
		'statsd': {},
		'incoming': {
			'redis_url': ['redis://controller:6379?db=5']
		},
		'metricd': {
			'metric_reporting_delay': ['120'],
			......
		},
		....
	}], _sections_to_file = {
		'statsd': '/etc/gnocchi/gnocchi.conf',
		'incoming': '/etc/gnocchi/gnocchi.conf',
			......
	}, config_dir = None, config_file = None, debug = 'true', log_dir = '/var/log/gnocchi', log_file = '/var/log/gnocchi/test-api.log', verbose = 'true'),
	'_oparser': _CachedArgumentParser(prog = 'uwsgi', usage = None, description = None, version = None, formatter_class = < class 'argparse.HelpFormatter' > , conflict_handler = 'error', add_help = True),
	'_mutable_ns': None,
	'_ConfigOpts__cache': {},
	'default_config_files': ['/usr/share/gnocchi/gnocchi-dist.conf', '/etc/gnocchi/gnocchi.conf'],
	'_env_driver': < oslo_config.sources._environment.EnvironmentConfigurationSource object at 0x7f13088b3b10 > ,
	'_use_env': True,
	'_ConfigOpts__drivers_cache': {},
	'_sources': [],
	'_opts': {
		'config_file': {
			'opt': < oslo_config.cfg._ConfigFileOpt object at 0x7f13088c2d50 > ,
			'cli': True
		},
	},
	'_args': ['--log-file', '/var/log/gnocchi/test-api.log'],
	'version': '4.3.2',
	'_mutate_hooks': set([]),
	'usage': None,
	'_groups': {
		'statsd': < oslo_config.cfg.OptGroup object at 0x7f13088c2b10 > ,
		'incoming': < oslo_config.cfg.OptGroup object at 0x7f13088c2ad0 > ,
		......
	},
	'_config_opts': [ < oslo_config.cfg._ConfigFileOpt object at 0x7f13088c2d50 > , < oslo_config.cfg._ConfigDirOpt object at 0x7f13088c2c90 > ],
	'prog': 'uwsgi',
	'default_config_dirs': [],
	'_cli_opts': deque([{
		'opt': < oslo_config.cfg._ConfigDirOpt object at 0x7f13088c2c90 > ,
		'group': None
	}, ]),
	'_validate_default_values': True,
	'_ext_mgr': None,
	'project': 'gnocchi',
	'_deprecated_opts': {
		'DEFAULT': {
			'refresh_timeout': {
				'opt': < oslo_config.cfg.IntOpt object at 0x7f13088c2510 > ,
				'group': < oslo_config.cfg.OptGroup object at 0x7f13088c2a50 >
			},
			......
		},
		'database': {
			'idle_timeout': {
				'opt': < oslo_config.cfg.IntOpt object at 0x7f13088aec50 > ,
				'group': < oslo_config.cfg.OptGroup object at 0x7f13088b3c50 >
			}
		}
		}
	}
})
  
```



再看下app.load_app的代码

```
# gnocchi/rest/app.py

def load_app(conf, not_implemented_middleware=True):
    global APPCONFIGS

    # Build the WSGI app
    cfg_path = conf.api.paste_config
    # cfg_path:  api-paste.ini
    if not os.path.isabs(cfg_path):
        cfg_path = conf.find_file(cfg_path)

    if cfg_path is None or not os.path.exists(cfg_path):
        LOG.debug("No api-paste configuration file found! Using default.")
        cfg_path = os.path.abspath(pkg_resources.resource_filename(
            __name__, "api-paste.ini"))

    config = dict(conf=conf,
                  not_implemented_middleware=not_implemented_middleware)
    configkey = str(uuid.uuid4())
    APPCONFIGS[configkey] = config

    LOG.info("WSGI config used: %s", cfg_path)

    appname = "gnocchi+" + conf.api.auth_mode
    app = deploy.loadapp("config:" + cfg_path, name=appname,
                         global_conf={'configkey': configkey})
    return cors.CORS(app, conf=conf)

```



#### 2.2 pastedeploy加载uwsgi 不同的app

加载配置文件api-paste.ini，启动方式是deploy.loadapp，涉及到pastedeploy用法，简单介绍下

- PasteDeploy用来发现和配置WSGI应用的一套系统。WSGI的使用者，提供了一个单一简单的函数(loadapp)用于通过配置文件或python egg中加载WSGI。对于WSGI提供者，仅仅要求提供一个单一的简单的应用入口。 无需应用者展示应用的具体实现。

  **PasteDeploy配置文件**
   PasteDeploy定义了以下几个部件：

  - app：callable object，WSGI服务
  - filter： 过滤器，主要用于预处理的一些工作，如身份验证等。执行完毕之后直接返回或是交给下一个filter/app继续处理。filter是一个callable object,参数是app，对app进行封装后返回，
  - pipeline：由若干个filter和1个APP服务
  - composite：实现对不同app的分发。如根据url的参数分发给不同的app。

具体可以参考：

https://www.jianshu.com/p/ed07aa2c9578

https://www.cnblogs.com/Security-Darren/p/4087587.html



```
# api-paste.ini文件

[composite:gnocchi+basic]
use = egg:Paste#urlmap
/ = gnocchiversions_pipeline
/v1 = gnocchiv1+noauth
/healthcheck = healthcheck

[composite:gnocchi+keystone]
use = egg:Paste#urlmap
/ = gnocchiversions_pipeline
/v1 = gnocchiv1+keystone
/healthcheck = healthcheck

[composite:gnocchi+remoteuser]
use = egg:Paste#urlmap
/ = gnocchiversions_pipeline
/v1 = gnocchiv1+noauth
/healthcheck = healthcheck

[pipeline:gnocchiv1+noauth]
pipeline = http_proxy_to_wsgi gnocchiv1

[pipeline:gnocchiv1+keystone]
pipeline = http_proxy_to_wsgi keystone_authtoken gnocchiv1

[pipeline:gnocchiversions_pipeline]
pipeline = http_proxy_to_wsgi gnocchiversions

[app:gnocchiversions]
paste.app_factory = gnocchi.rest.app:app_factory
root = gnocchi.rest.api.VersionsController

[app:gnocchiv1]
paste.app_factory = gnocchi.rest.app:app_factory
root = gnocchi.rest.api.V1Controller

[filter:keystone_authtoken]
use = egg:keystonemiddleware#auth_token
oslo_config_project = gnocchi

[filter:http_proxy_to_wsgi]
use = egg:oslo.middleware#http_proxy_to_wsgi
oslo_config_project = gnocchi

[app:healthcheck]
use = egg:oslo.middleware#healthcheck
oslo_config_project = gnocchi

```

本用例app加载流程是：

1. 根据配置文件，找到 [composite:gnocchi+keystone]，表示分发请求至不同的应用；

2. use = egg:Paste#urlmap表示：使用Paste Package中的urlmap应用。urlmap主要用于根据路径前缀将请求映射至不同的应用；

3. 根据请求是v1开头，找到/v1 = gnocchiv1+keystone，由于gnocchiv1+keystone的app找不到，寻找对应 [pipeline:gnocchiv1+keystone]

4. pipeline也是app，pipeline = http_proxy_to_wsgi keystone_authtoken gnocchiv1
   其中:

   - http_proxy_to_wsgi是一個过滤器：
     [filter:http_proxy_to_wsgi]
     use = egg:oslo.middleware#http_proxy_to_wsgi
     oslo_config_project = gnocchi

   - keystone_authtoken也是一个过滤器:
     [filter:keystone_authtoken]
     use = egg:keystonemiddleware#auth_token
     oslo_config_project = gnocchi

   - **gnocchiv1**是一个app：
     [app:gnocchiv1]
     paste.app_factory = gnocchi.rest.app:app_factory
     root = gnocchi.rest.api.V1Controller

5. 加载:app_factory，根据app名称加载对应的app

   ```
   # gnocchi/rest/app.py
   
   def app_factory(global_config, **local_conf):
       global APPCONFIGS
       appconfig = APPCONFIGS.get(global_config.get('configkey'))
       return _setup_app(root=local_conf.get('root'), **appconfig)
   ```



#### 2.3 pecan app加载

根据上一步，由pastedeploy加载app:gnocchiv1， 构建app，调用_setup_app

并且代码开始位置在root = gnocchi.rest.api.V1Controller

```
# gnocchi/rest/app.py

def _setup_app(root, conf, not_implemented_middleware):
    app = pecan.make_app(
        root,
        hooks=(GnocchiHook(conf),),
        guess_content_type_from_ext=False,
        custom_renderers={"json": JsonRenderer}
    )

    if not_implemented_middleware:
        app = webob.exc.HTTPExceptionMiddleware(NotImplementedMiddleware(app))

    return app
```



V1Controller是请求的入口，根据url路径，转发给对应的SubController进行处理。

简单介绍一下pecan路由：

Pecan是一个**路由对象分发**的python web框架。本质上可以将url通过分割为每一部分，然后对每一部分查找对应处理该URL部分的处理类，处理后，继续交给后面部分的URL处理，直到所有URL部分都被处理后，调用最后分割的URL对应的处理函数处理。

##### 2.3.1 pecan源码处理流程

代码位于Pecan的core.py中。

1. 当一个请求从wsgiserver转发过来，首先处理的是Pecan中的__call__方法。

>  主要调用了find_controller和invoke_controller方法。find_controller根据对象分发机制找到url的处理方法，如果没找到，则抛出异常，由后面的except代码块处理，找到了就调用invoke_controller执行该处理方法，将处理结果保存到state中。

2. find_controller方法中主要调用了route方法

route方法中调用了lookup_controller方法对截取后的路径进行继续处理
lookup_controller针对每一个controller对象，在其中查找对应的处理方法，如果没找到，则根据notfound_handlers队列里的方法顺序，采取后进先出的方式pop出来方法，加载比如 `default`、`_look_up`方法，直到找到对应的方法，或 为空抛出异常。

3.  找到方法后调用invoke_controller 执行该方法。



##### 2.3.2 分析根据metric_id获取measures的pecan流程

请求路径：/v1/metric/{metric_id}/measures?granularity={granularity}&aggregation={aggregation}&start={start_time}&end={end_time}

- 根据v1， gnocchi.rest.api.V1Controller；
- 根据metric，找到subController---: MetricsController；
- 根据MetricsController的__look_up方法，调用了MetricController方法
- 根据measures及pecan的custom_actions用法，找到get_measures方法

```
# pecan/rest.py
# custom_actions用法

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

```



参考链接：https://www.cnblogs.com/luohaixian/p/11145939.html





#### 2.4 gnocchi-api查询数据分析（未完成）

根据2.3.2例子，代码最终定位到MetricController的get_measures方法

```
# gnochi/rest/api.py

    @pecan.expose('json')
    def get_measures(self, start=None, stop=None, aggregation='mean',
                     granularity=None, resample=None, refresh=False,
                     **param):
        self.enforce_metric("get measures")

        if resample:
            if not granularity:
                abort(400, 'A granularity must be specified to resample')
            try:
                resample = (resample if calendar.GROUPINGS.get(resample) else
                            utils.to_timespan(resample))
            except ValueError as e:
                abort(400, six.text_type(e))

        if granularity is None:
            granularity = [d.granularity
                           for d in self.metric.archive_policy.definition]
            start, stop, _, _, _ = validate_qs(
                start=start, stop=stop)
        else:
            start, stop, granularity, _, _ = validate_qs(
                start=start, stop=stop, granularity=granularity)

        if aggregation not in self.metric.archive_policy.aggregation_methods:
            abort(404, {
                "cause": "Aggregation method does not exist for this metric",
                "detail": {
                    "metric": self.metric.id,
                    "aggregation_method": aggregation,
                },
            })

        aggregations = []
        for g in sorted(granularity, reverse=True):
            agg = self.metric.archive_policy.get_aggregation(
                aggregation, g)
            if agg is None:
                abort(404, six.text_type(
                    storage.AggregationDoesNotExist(
                        self.metric, aggregation, g)
                ))
            aggregations.append(agg)

        if (strtobool("refresh", refresh) and
                pecan.request.incoming.has_unprocessed(self.metric.id)):
            try:
                pecan.request.chef.refresh_metrics(
                    [self.metric],
                    pecan.request.conf.api.operation_timeout)
            except chef.SackAlreadyLocked:
                abort(503, 'Unable to refresh metric: %s. Metric is locked. '
                      'Please try again.' % self.metric.id)
        try:
            return pecan.request.storage.get_measures(
                self.metric, aggregations, start, stop, resample)[aggregation]
        except storage.AggregationDoesNotExist as e:
            abort(404, six.text_type(e))
        except storage.MetricDoesNotExist:
            return []

```

上面代码逻辑，验证，最终调用存储driver的get_measures方法获取数据

```
# gnocchi/storage/__init__.py


    def get_measures(self, metric, aggregations,
                     from_timestamp=None, to_timestamp=None,
                     resample=None):
        """Get aggregated measures from a metric.

        Deprecated. Use `get_aggregated_measures` instead.

        :param metric: The metric measured.
        :param aggregations: The aggregations to retrieve.
        :param from timestamp: The timestamp to get the measure from.
        :param to timestamp: The timestamp to get the measure to.
        :param resample: The granularity to resample to.
        """
        timeseries = self.get_aggregated_measures(
            {metric: aggregations}, from_timestamp, to_timestamp)[metric]

        if resample:
            for agg, ts in six.iteritems(timeseries):
                timeseries[agg] = ts.resample(resample)

        return {
            aggmethod: list(itertools.chain(
                *[[(timestamp, timeseries[agg].aggregation.granularity, value)
                   for timestamp, value
                   in timeseries[agg].fetch(from_timestamp, to_timestamp)]
                  for agg in sorted(aggs,
                                    key=ATTRGETTER_GRANULARITY,
                                    reverse=True)]))
            for aggmethod, aggs in itertools.groupby(timeseries.keys(),
                                                     ATTRGETTER_METHOD)
        }



    def get_aggregated_measures(self, metrics_and_aggregations,
                                from_timestamp=None, to_timestamp=None):
        """Get aggregated measures from a metric.

        :param metrics_and_aggregations: The metrics and aggregations to
                                         retrieve in format
                                         {metric: [aggregation, …]}.
        :param from timestamp: The timestamp to get the measure from.
        :param to timestamp: The timestamp to get the measure to.
        """
        metrics_aggs_keys = self._list_split_keys(metrics_and_aggregations)

        for metric, aggregations_keys in six.iteritems(metrics_aggs_keys):
            for aggregation, keys in six.iteritems(aggregations_keys):
                start = (
                    carbonara.SplitKey.from_timestamp_and_sampling(
                        from_timestamp, aggregation.granularity)
                ) if from_timestamp else None

                stop = (
                    carbonara.SplitKey.from_timestamp_and_sampling(
                        to_timestamp, aggregation.granularity)
                ) if to_timestamp else None

                # Replace keys with filtered version
                metrics_aggs_keys[metric][aggregation] = [
                    key for key in sorted(keys)
                    if ((not start or key >= start)
                        and (not stop or key <= stop))
                ]

        metrics_aggregations_splits = self._get_splits_and_unserialize(
            metrics_aggs_keys)

        results = collections.defaultdict(dict)
        for metric, aggregations in six.iteritems(metrics_and_aggregations):
            for aggregation in aggregations:
                ts = carbonara.AggregatedTimeSerie.from_timeseries(
                    metrics_aggregations_splits[metric][aggregation],
                    aggregation)
                # We need to truncate because:
                # - If the driver is not in WRITE_FULL mode, then it might read
                # too much data that will be deleted once the split is
                # rewritten. Just truncate so we don't return it.
                # - If the driver is in WRITE_FULL but the archive policy has
                # been resized, we might still have too much points stored,
                # which will be deleted at a later point when new points will
                # be processed. Truncate to be sure we don't return them.
                if aggregation.timespan is not None:
                    ts.truncate(aggregation.timespan)
                results[metric][aggregation] = ts.fetch(
                    from_timestamp, to_timestamp)

        return results

```









### 3. gnocchi-metricd源码分析（未开始）

#### 3.1 初始代码加载

服务启动依赖脚本/usr/bin/gnocchi-metricd

```
#!/usr/bin/python2
# EASY-INSTALL-ENTRY-SCRIPT: 'gnocchi==4.3.2','console_scripts','gnocchi-metricd'
__requires__ = 'gnocchi==4.3.2'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('gnocchi==4.3.2', 'console_scripts', 'gnocchi-metricd')()

```

/usr/lib/python2.7/site-packages/gnocchi-4.3.2-py2.7.egg-info/entry_points.txt 

```
gnocchi-metricd = gnocchi.cli.metricd:metricd
```

启动的gnocchi/cli/metricd.py下的metricd

```
def metricd():
    conf = cfg.ConfigOpts()
    conf.register_cli_opts([
        cfg.IntOpt("stop-after-processing-metrics",
                   default=0,
                   min=0,
                   help="Number of metrics to process without workers, "
                   "for testing purpose"),
    ])
    conf = service.prepare_service(conf=conf)

    if conf.stop_after_processing_metrics:
        metricd_tester(conf)
    else:
        MetricdServiceManager(conf).run()
```

看下  MetricdServiceManager都做了什么

```


class MetricdServiceManager(cotyledon.ServiceManager):
    def __init__(self, conf):
        super(MetricdServiceManager, self).__init__()
        oslo_config_glue.setup(self, conf)

        self.conf = conf
        self.metric_processor_id = self.add(
            MetricProcessor, args=(self.conf,),
            workers=conf.metricd.workers)
        if self.conf.metricd.metric_reporting_delay >= 0:
            self.add(MetricReporting, args=(self.conf,))
        self.add(MetricJanitor, args=(self.conf,))

        self.register_hooks(on_reload=self.on_reload)

    def on_reload(self):
        # NOTE(sileht): We do not implement reload() in Workers so all workers
        # will received SIGHUP and exit gracefully, then their will be
        # restarted with the new number of workers. This is important because
        # we use the number of worker to declare the capability in tooz and
        # to select the block of metrics to proceed.
        self.reconfigure(self.metric_processor_id,
                         workers=self.conf.metricd.workers)


```



分析:
MetricReporting服务每隔2分钟统计并以日志形式输出未处理的监控项个数和未处理的measure数目
MetricJanitor每隔已定时间清理已经删除的metric数据
以及最重要的监控数据聚合处理服务**MetricProcessor**，它从MetricScheduler服务存放在多进程队列中获取需要处理的监控数据进行最终的聚合运算。

```
# gnocchi/cli/metricd.py

class MetricProcessor(MetricProcessBase):
    name = "processing"
    GROUP_ID = b"gnocchi-processing"

    def __init__(self, worker_id, conf):
        super(MetricProcessor, self).__init__(
            worker_id, conf, conf.metricd.metric_processing_delay)
        self._tasks = []
        self.group_state = None
        self.sacks_with_measures_to_process = set()
        # This stores the last time the processor did a scan on all the sack it
        # is responsible for
        self._last_full_sack_scan = utils.StopWatch().start()
        # Only update the list of sacks to process every
        # metric_processing_delay
        self._get_sacks_to_process = cachetools.func.ttl_cache(
            ttl=conf.metricd.metric_processing_delay
        )(self._get_sacks_to_process)

    @tenacity.retry(
        wait=utils.wait_exponential,
        # Never retry except when explicitly asked by raising TryAgain
        retry=tenacity.retry_never)
    def _configure(self):
        super(MetricProcessor, self)._configure()

        # create fallback in case paritioning fails or assigned no tasks
        self.fallback_tasks = list(self.incoming.iter_sacks())
        try:
            self.partitioner = self.coord.join_partitioned_group(
                self.GROUP_ID, partitions=200)
            LOG.info('Joined coordination group: %s',
                     self.GROUP_ID.decode())
        except tooz.NotImplemented:
            LOG.warning('Coordinator does not support partitioning. Worker '
                        'will battle against other workers for jobs.')
        except tooz.ToozError as e:
            LOG.error('Unexpected error configuring coordinator for '
                      'partitioning. Retrying: %s', e)
            raise tenacity.TryAgain(e)

        if self.conf.metricd.greedy:
            filler = threading.Thread(target=self._fill_sacks_to_process)
            filler.daemon = True
            filler.start()

    @utils.retry_on_exception.wraps
    def _fill_sacks_to_process(self):
        try:
            for sack in self.incoming.iter_on_sacks_to_process():
                if sack in self._get_sacks_to_process():
                    LOG.debug(
                        "Got notification for sack %s, waking up processing",
                        sack)
                    self.sacks_with_measures_to_process.add(sack)
                    self.wakeup()
        except exceptions.NotImplementedError:
            LOG.info("Incoming driver does not support notification")
        except Exception as e:
            LOG.error(
                "Error while listening for new measures notification, "
                "retrying",
                exc_info=True)
            raise tenacity.TryAgain(e)

    def _get_sacks_to_process(self):
        try:
            self.coord.run_watchers()
            if (not self._tasks or
                    self.group_state != self.partitioner.ring.nodes):
                self.group_state = self.partitioner.ring.nodes.copy()
                self._tasks = [
                    sack for sack in self.incoming.iter_sacks()
                    if self.partitioner.belongs_to_self(
                        sack, replicas=self.conf.metricd.processing_replicas)]
        except tooz.NotImplemented:
            # Do not log anything. If `run_watchers` is not implemented, it's
            # likely that partitioning is not implemented either, so it already
            # has been logged at startup with a warning.
            pass
        except Exception as e:
            LOG.error('Unexpected error updating the task partitioner: %s', e)
        finally:
            return self._tasks or self.fallback_tasks

    def _run_job(self):
        m_count = 0
        s_count = 0
        # We are going to process the sacks we got notified for, and if we got
        # no notification, then we'll just try to process them all, just to be
        # sure we don't miss anything. In case we did not do a full scan for
        # more than `metric_processing_delay`, we do that instead.
        if self._last_full_sack_scan.elapsed() >= self.interval_delay:
            sacks = self._get_sacks_to_process()
        else:
            sacks = (self.sacks_with_measures_to_process.copy()
                     or self._get_sacks_to_process())
        for s in sacks:
            try:
                try:
                    # Chef是一个配置管理自动化工具
                    m_count += self.chef.process_new_measures_for_sack(s)
                except chef.SackAlreadyLocked:
                    continue
                s_count += 1
                self.incoming.finish_sack_processing(s)
                self.sacks_with_measures_to_process.discard(s)
            except Exception:
                LOG.error("Unexpected error processing assigned job",
                          exc_info=True)
        LOG.debug("%d metrics processed from %d sacks", m_count, s_count)
        try:
            # Update statistics
            self.coord.update_capabilities(self.GROUP_ID,
                                           self.store.statistics)
        except tooz.NotImplemented:
            pass
        if sacks == self._get_sacks_to_process():
            # We just did a full scan of all sacks, reset the timer
            self._last_full_sack_scan.reset()
            LOG.debug("Full scan of sacks has been done")

    def close_services(self):
        self.coord.stop()

```

重点看run_job中process_new_measures_for_sack函数

```
 # gnocchi/chef.py   
    
    def process_new_measures_for_sack(self, sack, blocking=False, sync=False):
        """Process added measures in background.

        Lock a sack and try to process measures from it. If the sack cannot be
        locked, the method will raise `SackAlreadyLocked`.

        :param sack: The sack to process new measures for.
        :param blocking: Block to be sure the sack is processed or raise
                         `SackAlreadyLocked` otherwise.
        :param sync: If True, raise any issue immediately otherwise just log it
        :return: The number of metrics processed.

        """
        lock = self.get_sack_lock(sack)
        if not lock.acquire(blocking=blocking):
            raise SackAlreadyLocked(sack)
        LOG.debug("Processing measures for sack %s", sack)
        try:
            with self.incoming.process_measures_for_sack(sack) as measures:
                # process only active metrics. deleted metrics with unprocessed
                # measures will be skipped until cleaned by janitor.
                if not measures:
                    return 0

                metrics = self.index.list_metrics(
                    attribute_filter={
                        "in": {"id": measures.keys()}
                    })
                self.storage.add_measures_to_metrics({
                    metric: measures[metric.id]
                    for metric in metrics
                })
                LOG.debug("Measures for %d metrics processed",
                          len(metrics))
                return len(measures)
        except Exception:
            if sync:
                raise
            LOG.error("Error processing new measures", exc_info=True)
            return 0
        finally:
            lock.release()

```



处理后的sacks保存到storage      self.storage.add_measures_to_metrics({

```
# gnocchi/storage/__init__.py    
    
    def add_measures_to_metrics(self, metrics_and_measures):
        """Update a metric with a new measures, computing new aggregations.

        :param metrics_and_measures: A dict there keys are `storage.Metric`
                                     objects and values are timeseries array of
                                     the new measures.
        """
        with self.statistics.time("raw measures fetch"):
            raw_measures = self._get_or_create_unaggregated_timeseries(
                metrics_and_measures.keys())
        self.statistics["raw measures fetch"] += len(metrics_and_measures)
        self.statistics["processed measures"] += sum(
            map(len, metrics_and_measures.values()))

        new_boundts = []
        splits_to_delete = {}
        splits_to_update = {}

        for metric, measures in six.iteritems(metrics_and_measures):
            measures = numpy.sort(measures, order='timestamps')

            agg_methods = list(metric.archive_policy.aggregation_methods)
            block_size = metric.archive_policy.max_block_size
            back_window = metric.archive_policy.back_window
            # NOTE(sileht): We keep one more blocks to calculate rate of change
            # correctly
            if any(filter(lambda x: x.startswith("rate:"), agg_methods)):
                back_window += 1

            if raw_measures[metric] is None:
                ts = None
            else:
                try:
                    ts = carbonara.BoundTimeSerie.unserialize(
                        raw_measures[metric], block_size, back_window)
                except carbonara.InvalidData:
                    LOG.error("Data corruption detected for %s "
                              "unaggregated timeserie, creating a new one",
                              metric.id)
                    ts = None

            if ts is None:
                # This is the first time we treat measures for this
                # metric, or data are corrupted, create a new one
                ts = carbonara.BoundTimeSerie(block_size=block_size,
                                              back_window=back_window)
                current_first_block_timestamp = None
            else:
                current_first_block_timestamp = ts.first_block_timestamp()

            # NOTE(jd) This is Python where you need such
            # hack to pass a variable around a closure,
            # sorry.
            computed_points = {"number": 0}

            def _map_compute_splits_operations(bound_timeserie):
                # NOTE (gordc): bound_timeserie is entire set of
                # unaggregated measures matching largest
                # granularity. the following takes only the points
                # affected by new measures for specific granularity
                try:
                    tstamp = max(bound_timeserie.first, measures['timestamps'][0])
                except Exception as e:
                    LOG.error('measures missing the key timestamps ,take bound_timeserie.first as timestamps')
                    tstamp = bound_timeserie.first
                new_first_block_timestamp = (
                    bound_timeserie.first_block_timestamp()
                )
                computed_points['number'] = len(bound_timeserie)

                aggregations = metric.archive_policy.aggregations

                grouped_timeseries = {
                    granularity: bound_timeserie.group_serie(
                        granularity,
                        carbonara.round_timestamp(tstamp, granularity))
                    for granularity, aggregations
                    # No need to sort the aggregation, they are already
                    in itertools.groupby(aggregations, ATTRGETTER_GRANULARITY)
                }

                aggregations_and_timeseries = {
                    aggregation:
                    carbonara.AggregatedTimeSerie.from_grouped_serie(
                        grouped_timeseries[aggregation.granularity],
                        aggregation)
                    for aggregation in aggregations
                }

                deleted_keys, keys_and_split_to_store = (
                    self._compute_split_operations(
                        metric, aggregations_and_timeseries,
                        current_first_block_timestamp,
                        new_first_block_timestamp)
                )

                return (new_first_block_timestamp,
                        deleted_keys,
                        keys_and_split_to_store)

            with self.statistics.time("aggregated measures compute"):
                (new_first_block_timestamp,
                 deleted_keys,
                 keys_and_splits_to_store) = ts.set_values(
                     measures,
                     before_truncate_callback=_map_compute_splits_operations,
                )

            splits_to_delete[metric] = deleted_keys
            splits_to_update[metric] = (keys_and_splits_to_store,
                                        new_first_block_timestamp)

            new_boundts.append((metric, ts.serialize()))

        with self.statistics.time("splits delete"):
            self._delete_metric_splits(splits_to_delete)
        self.statistics["splits delete"] += len(splits_to_delete)
        with self.statistics.time("splits update"):
            self._update_metric_splits(splits_to_update)
        self.statistics["splits update"] += len(splits_to_update)
        with self.statistics.time("raw measures store"):
            self._store_unaggregated_timeseries(new_boundts)
        self.statistics["raw measures store"] += len(new_boundts)

```
















