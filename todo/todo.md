## todo





### 本季度任务


- 云管相关接口总耗时情况，及处理速度优化
- 原生快照、增强型快照设计、开发、优化（第二季度
- 接口中文化
- 



#### 原生快照接口

1. 原生接口快照改动设计；
    1.1 原来云主机页面的创建快照更换后端接口为增强型快照的接口；
    1.2 原来云主机页面更多里增加 创建备份，后端接口是原生快照的接口生接口；
    1.3 原来云主机快照模块，等底层nova开发完成后，作为实际的云主机快照页面；
    1.4 在计算模块，增加云主机备份，后端对接的是原生快照接口；
2. 增强型快照接口页面与云管设计开发（由于底层nova未开发完成，等底层完成后开发）；





### 新增任务

- 大镜像上传问题处理 
- 新调度策略下，license/celery运行情况（新处理登录时要同步一次，只靠beat有时间间隔）

- 云主机，软删除，恢复，软删除，恢复，然后对该云主机创建原生快照，提示状态为soft_delete，无发创建

- 常用接口压测

- sw适配：主机监控、云主机监控、ceilometer/gnocchi/snmp组件、nova/cinder/neutron组件

- 调研

  - consule监控使用

- 日志info总是两条

- node_info改造

- 负载均衡配额（所有配额使用的地方都要修改），返回数据没有已使用，修改源码或云管代码增加已使用

- 新需求评估（新云平台）

- Nova、cinder (neutron)并发创建资源（）

- libvirt获取磁盘利用率(可靠性)

- 应用中心（编排模板）（先定设计，制定步骤，按照步骤深入研究）

  - 含有nginx的虚拟机编排
  - 能修改nginx配置并启动服务的虚拟机编排
  - 指定网络(网络-子网-dhcp-静态ip地址)的虚拟机编排
  - 含有mysql服务的虚拟机编排
  - 能修改mysql配置并可控制服务启动的虚拟机编排
  - 含有redis服务的虚拟机编排
  - 可修改redis配置并控制服务的虚拟机编排
  - 其他常用服务（先单独研究）
  - 固定组合（nginx-mysql、等）编排
  - 

- 兼容超融合（多云管理）、vmware、华为云（在上层，设计，可选云或者超融合等）（多云管理，云的相互用）
  
- magnum容器编排
  
- rpm包打包(node_info/ceilometer/gnocchi)
  
- openstack tacker
  
- nova主机管理，底层不支持向上分页
  
- nova云主机，查询参数ip，设置
  
- License/license_status，sid重复问题（裁决比对失败，sid相同）
  
- 云管查询数据库相关接口，sid归一处理
  
- 
  
  
  
  
  
  
  
  



#### 大镜像上传问题



分片上传

断点续传

大镜像上传

1.容器创建接口修改，增加创建容器时挂载已有硬盘的情况；
2.大镜像上传问题调研，目前根据搜集的资料有三种方案（可行性需要调研与测试）；
 2.1 nginx接收切片，利用nginx的handler处理或合并请求，然后上传后调用glanceapi上传（可能需要开发nginx模块或者适配，调研中）；
 2.2 改造glance接口，前端处理切片，glance接收后合并，然后调用glanceapi上传（改动代码量大，另外glanceapi改造后需要测试是否影响其他功能）；
 2.3 前端分片上传，在控制节点写一个服务，接收分片，重组后，调用glanceapi上传镜像（增加了服务组件）；
 2.4 基于ftp服务，上传到ftp等服务器，然后控制节点拉取镜像然后上传(需要控制节点写服务)。





1. nginx负责切片功能，保证上传成功，上传后调用glanceapi上传；
2. 改造glance，前端切片，glance接收，然后合并后调用glanceapi上传；
3. 前端分片上传，在控制节点写一个服务，接收分片，重组后，调用glanceapi上传镜像；
4. 





#### 总耗时长的请求日志



```
# 接口增删改查都要确认下
[2022-11-25 09:43:52,004] - [task_id:api] - [base.py:222] - [INFO][request: /api/auth/change_project -method: POST -total time consuming: 4] (只有登录接口请求)

[2022-11-25 09:44:30,776] - [task_id:api] - [base.py:222] - [INFO][request: /api/project_manager/domain_users -method: PUT -total time consuming: 3] (串联请求改成并发)



[2022-11-25 09:56:03,298] - [task_id:api] - [base.py:222] - [INFO][request: /api/auth/change_domain -method: GET -total time consuming: 2] （有删除后重试查询的逻辑，）



[2022-11-25 10:37:45,232] - [task_id:api] - [base.py:222] - [INFO][request: /api/operate/order_async -method: POST -total time consuming: 3]  (创建资源)

[2022-11-25 10:54:17,579] - [task_id:api] - [base.py:222] - [INFO][request: /api/compute/servers -method: GET -total time consuming: 2]


[2022-11-25 13:46:41,119] - [task_id:api] - [base.py:222] - [INFO][request: /api/project_manager/projects -method: PUT -total time consuming: 3]

```





#### 拟态开关

1、mimic数据库configurable_mimic_config表增加一条拟态开关配置项 mimic_switch，
配置默认为on，即拟态开关打开状态，需在部署阶段初始化为默认值
sql语句如下：
INSERT INTO configurable_mimic_config (`conf_key`, `conf_value`) VALUES ('mimic_switch', 'on');

2、前端页面拟态态势页面增加一个按钮，全局管理云管、云控、keystone拟态是否开启

3、拟态开关关闭状态，即非拟态状态，前端拟态态势页面上下线清洗操作需要置灰不能操作，上下线清洗只针对拟态开关打开状态有效

4、拟态开关配置接口
POST https://192.168.232.107/api/manual
header头增加
manual: config_mimic_switch

请求body如下：
{"mimic_switch": "off"}

mimic_switch只有两个值，on/off，代表拟态开关的打开/关闭状态

返回值：
{
    "code": 200,
    "msg": "",
    "success": true,
    "data": {}
}

5、拟态开关状态查询接口
GET https://192.168.232.107/api/manual
header头增加
manual: get_mimic_switch

返回值如下：

{
    "code": 200,
    "msg": "",
    "success": true,
    "data": {
        "mimic_switch": "on"
    }
}

mimic_switch只有两个值，on/off，代表拟态开关的打开/关闭状态



#### 裁决日志详情



- 页面需要修改的地方：
  执行体日志:
  1，执行体动作列，需从translate接口获取，根据当前列字段和接口字段进行替换，可为多个，逗号分隔；
  2，新增日志详情列，用于查看日志详情，每个条目有查看按钮；
  3，详情弹出一个模式框，内容为json，框体设定一定大小，可上下滑动。
  裁决日志：
  1，裁决策略列，需从translate接口获取，根据当前列字段和接口字段进行替换；
  2，异常原因列，需从translate接口获取，根据当前列字段和接口字段进行替换，可为多个，逗号分隔
  3，详情弹出一个模式框，内容为json，框体设定一定大小，可上下滑动。

- 弹出json内容，要根据用户角色过滤，只有云管理员可以显示所有详情，其他用户，找需要的显示就行

- 云管需要修改：
  新增一个mimic_log_translate表，新增一个translate接口，返回mimic_log_translate表英文中文对照表

  

![企业微信截图_16697066785228](./企业微信截图_16697066785228.png)

![企业微信截图_16697047701338](./执行体状态日志详情.png)



![企业微信截图_16697048808840](./裁决日志详情.png)







### 本周任务

- 网络列表、路由列表分页（待完成）

- 云管数据库，缓存热数据（通用方法已构建，优化工程量大，持续优化）

- 云管技术文档，

- 珠海云 监控数据断电重启后，没有正常获取数据（todo）

- 云主机创建，过滤云硬盘和云硬盘快照（创建快照时，增加元数据，过滤元数据），

- 云主机迁移文件，自带的auth/session如何处理迁移记录（todo）

- Horizon  ci/cd处理

- aodh  ci/cd处理

- heat编排，接口获取模板调研

- heat编排，stack查询模板名称，做的marker标记，优化

- Monitor-cache，自动化部署后，启动问题处理

- 

- 

- k8s界面问题
  - 非完全中文化，未处理，看是否升级及以后处理
  - 如何运行pod容器，或如何查看dashobar代码，定制dashboard镜像（kubernetes-dashboard二次开发）
  
  
  
- - k8s问题
  - k8s挂载卷问题（持久化存储，使用cinder https://blog.csdn.net/jiangmingfei/article/details/85294863     ,  使用cephfs， nfs方式挂载）
  - k8s -dashboard高可用实现（修改访问方式等 访问方式nodeport/apiserver(需要能直接访访问到，并不适用内网环境)/loadbalance(针对的是访问入口nginx高可用，并不是后面的服务)，调研nodeport问题（当dashboard所在节点异常后，重新拉起来的服务，不可用），ingress调研）
  - quay.io/kubernetes-ingress-controller/nginx-ingress-controller:0.30.0
  - prometheus监控部署调研、日志调研（涉及helm部署、持久化存储存储监控数据、日志等）
  - 
  - 
  - api请求（类似horizon/rainbond设计）
  - k8s云管接口设计（已完成）
  - k8s云管接口模板获取，编辑，删除开发
  - k8s云管接口栈获取，编辑，删除开发
  - 需要和产品讨论，指定类似magnum界面的，k8s模板独立出来，不依赖heat原有接口，需要开发新接口
  - k8s传输安全性问题
  - 
  - 
  
- 优化
  - 云主机，增加ip查询的方式
  - 网络列表分页处理，网络列表（名称、ip查询）暂不处理
  
- 网卡状态（kp-compute在线没有网卡）

- 

- 





新需求

```
1. mangum k8s部署调研中，
	1.1 制作centos7镜像；
	1.2 先用已有脚本运行，继续测试；
	1.3 看第二步进度，确定是否更新版本信息，用新的方法测试。
有调研方案和方向，时间没法评估，现在部署还没成功（让邱军婷老师评估吧，他也在做这个，个人觉得顺利的话估计得1个月左右）
2. 多云管理平台
	2.1 简单设计云页面，可以切换两个云，前端、设计未协调
	2.2 用户归一问题上，对超融合用户管理改动较大，需要他们评估下，他们现在没有用户管理，用户直接是写到配置文件的
3. heat容器编排，（让晓伟开始按照这个顺序调研了）
	3.1 含有nginx的虚拟机编排
	3.2 能修改nginx配置并启动服务的虚拟机编排
	3.3 指定网络(网络-子网-dhcp-静态ip地址)的虚拟机编排
	3.4 含有mysql服务的虚拟机编排
	3.5 能修改mysql配置并可控制服务启动的虚拟机编排
	3.6 含有redis服务的虚拟机编排
	3.7 可修改redis配置并控制服务的虚拟机编排
	3.8 其他常用服务（先单独研究）
	3.9 固定组合（nginx-mysql、等）编排
4. 监控高并发方案
4.1 在集群部署完，现有方案预估问题不大，
4.2 libvirt获取磁盘利用率不准的问题，还没跟宗华协调，看有没有时间做一下，
4.3 还有个windows系统监控不准的问题，处于调研中
5. 非拟态云管验证，前端改造中，下周能完成

```







### docker配置代理

```
docker服务配代理的方法，配上代理后就可以下载dockerhub镜像：
mkdir -p /etc/systemd/system/docker.service.d
cat >   /etc/systemd/system/docker.service.d/http-proxy.conf << eof
[Service]
Environment="HTTP_PROXY=192.168.66.77:3128"
Environment="HTTPS_PROXY=192.168.66.77:3128"
Environment="NO_PROXY=192.168.*.*,*.local,localhost,127.0.0.1"
eof

systemctl daemon-reload
systemctl restart docker
```





centos配置代理



```
export proxy="http://192.168.66.77:3128"
export http_proxy=$proxy
export https_proxy=$proxy
export ftp_proxy=$proxy
export no_proxy="localhost, 127.0.0.1, ::1"
```





### 镜像制作，处理



```

执行
dd if=/dev/zero of=/home/junk_files
， 把剩余空间全部占满之后
执行
rm -f /home/junk_files

关机

# 压缩镜像
qemu-img convert -c -O qcow2 CentOS-7-x86_64-GenericCloud.qcow2 CentOS7v6.qcow2
```









### 脚本处理僵尸云主机、云硬盘

#### 云主机 实例删除，日志报错，找不到实例id 

```
 File "/usr/lib/python2.7/site-packages/nova/db/sqlalchemy/api.py", line 1904, in _instance_get_by_uuid
  raise exception.InstanceNotFound(instance_id=uuid)

InstanceNotFound: Instance 654720ca-3b17-41a2-9abf-d6fd4d9ccee3 could not be found.
: InstanceNotFound_Remote: Instance 654720ca-3b17-41a2-9abf-d6fd4d9ccee3 could not be found.
```

操作如下：

```python
import pymysql


HOST = '192.168.232.107'
PORT = 3306
USER = "root"
PASSWORD = "comleader@123"
db = "nova"

db = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, database=db)


def execute_sql(sql_code, action="execute"):
    global db
    while True:
        try:
            cursor = db.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql_code)
            if action == "query":
                data = cursor.fetchall()
                return data
            else:
                print(sql_code)
                excute_ret = db.commit()
                print(excute_ret)
                return
        except Exception as e:
            print(str(e))
            try:
                db = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, database=db)

                db.ping(reconnect=True)
            except Exception as e:
                print(str(e))
                break


def clean_nova_instance_from_db(target_uuid):
    sql1 = f'select id from instance_actions where instance_uuid="{target_uuid}";'
    sql = ''
    action_ids = execute_sql(sql1, action="query")
    for action_id_item in action_ids:
        action_id = action_id_item.get("id")
        tmp_sql = f"delete from instance_actions_events where action_id='{action_id}';"
        sql += tmp_sql
        print(action_id)

    total_sqls = f"{sql}delete from block_device_mapping where instance_uuid='{target_uuid}';delete from instance_actions where instance_uuid='{target_uuid}';delete from instance_extra where instance_uuid='{target_uuid}';delete from instance_faults where instance_uuid='{target_uuid}';delete from instance_groups where uuid='{target_uuid}';delete from instance_id_mappings where uuid='{target_uuid}';delete from instance_info_caches where instance_uuid='{target_uuid}';delete from instance_metadata where instance_uuid='{target_uuid}';delete from instance_system_metadata where instance_uuid='{target_uuid}';delete from migrations where instance_uuid='{target_uuid}';delete from virtual_interfaces where instance_uuid='{target_uuid}';delete from instances where uuid='{target_uuid}';"

    sql_list = total_sqls.split(";")[:-1]
    for sql in sql_list:
        execute_sql(sql)


target_uuid = "955a2154-75b6-4910-ac49-5b14d02c2a10
"
clean_nova_instance_from_db(target_uuid)


db = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, database="nova_api")


execute_sql(f"delete from instance_mappings where instance_uuid='{target_uuid}';")
execute_sql(f"delete from request_specs where instance_uuid='{target_uuid}';")
execute_sql(f"delete from instance_group_member where instance_uuid='{target_uuid}';")



db = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, database="nova_cell0")
execute_sql(f'delete from instances where uuid="{target_uuid}";')
execute_sql(f'delete from block_device_mapping where instance_uuid="{target_uuid}";')
execute_sql(f'delete from instance_actions where instance_uuid="{target_uuid}";')
execute_sql(f'delete from instance_id_mappings where uuid="{target_uuid}";')
execute_sql(f'delete from instance_system_metadata where instance_uuid="{target_uuid}";')



```



#### 删除僵尸卷

```


# 更改状态后删除


# 删除本地或者远端实际的卷
rbd rm volumes/volume-01fe7a5c-df4b-42c0-9b22-f4004d99235c


# 删除数据库卷相关数据


```







master执行脚本时命令及错误

```



+ _prefix=192.168.66.29:80/openstack_magnum/
+ atomic install --storage ostree --system --system-package no --set REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt --name heat-container-agent 192.168.66.29:80/openstack_magnum/heat-container-agent:stein-dev
time="2022-04-28T02:03:24Z" level=fatal msg="Error determining manifest MIME type for docker://192.168.66.29:80/openstack_magnum/heat-container-agent:stein-dev: pinging docker registry returned: Get https://192.168.66.29:80/v2/: http: server gave HTTP response to HTTPS client" 



```





#### Node info 服务，nova配置免密

```
 su nova -s /bin/bash -c "ssh-keygen -m PEM -t rsa -b 2048 -N '' -q -f /var/lib/nova/.ssh/id_rsa"
    log_info "Put nova's public key to controller and compute node"
    for node in `cat /etc/hosts | grep -E "controller|compute" | awk '{print $1}'`
    do
        su nova -s /usr/bin/expect -c "spawn ssh-copy-id root@$node
            expect {
                \"*yes/no\" { send \"yes\r\"; exp_continue }
                \"*password:\" { send \"comleader@123\r\" }
            }
            expect eof"
    done
```





### 修改qcow2镜像密码

```
virt-sysprep --root-password password:comleader@123 -a CentOS-7-x86_64-GenericCloud1.qcow2
```





### tolearn

aiohttp/asyncio/webserver
rpc服务构建/aysncio/aiohttp
network analysis
go/k8s
vue/html/css





### 修改

#### 监控部署修改部分

控制节点

gnocchi-api、gnocchi-metricd（gnocchi服务在控制节点可以不启动，只做负载均衡）；ceilometer-notification、ceilometer-central，snmp

计算节点

gnocchi-api、gnocchi-metricd、ceilometer-notification、ceilometer-central、ceilometer-compute/snmp，libguestfs

gnocchi.conf配置文件更新

日志切割处理

/etc/logrotate.d/gnocchi；/etc/logrotate.d/ceilometer； (部分可以打到rpm包里执行)

ngiix配置，/api/aodh/,/api/ceilometer/,等配置

kp节点 sysstat安装

gnocchi负载均衡，













#### 前端需要改的

```
未处理：
1. 在新部门下的，新项目，修改时，默认值是1(需要确认修改)， 提示云因盘大小不能小于1，切换成TB，也是错误（继续观察复现）
3、云主机，限制条件、云物理机在某种状态下可进行操作的逻辑修改（）
9. 增强型快照接口
10. 原生快照接口修改

24. 云主机列表，过滤字段增加ip，name ,镜像名称，透传到后端过滤
25. 主机管理-主机列表(个数)，只有下一页，刷新返回第一页
29. 创建实例，除了镜像、云主机快照，新增云硬盘快照、可启动的云硬盘，对应的source_type和image_id为所选类型的id
镜像
source_type: image
dest_type: volume
uuid: image_id
云主机快照
source_type: snapshot
dest_type: volume
uuid: snapshot_id
云硬盘（可启动）
source_type: volume
dest_type: volume
uuid: volume_id
云硬盘快照（可启动）
source_type: volume
dest_type: volume
uuid: snapshot_id


32. 镜像详情、云主机快照详情、云硬盘详情、云硬盘快照详情页
39. 禁止修改编排模板名称，
41. 所有列表页，名称显示不全的问题，不能调整列宽度
43. 浮动ip ，端口处理，显示端口的设备信息
44. 点击编辑云硬盘，退出，然后点击创建云硬盘，标题提示是编辑云硬盘
45. 监控中心-主机监控-物理网卡状态，在线、所有，过滤的数据不对





```



### 定位网络问题的命令

```javascript
tracert ip
route -n
ip netns 
ip route
ip  a
brctl show
ovs-vsctl
bridge fdb # bridge fdb展示的是隧道信息
bridge fdb shwo dev vxlan-3
tcpdump -i eth0 -nnvvv
tcpdump -i dev icmp -nnvvv
vrish edit domain-id  # 查看虚拟机xml信息，有网卡信息
virsh dumpxml domain-id
```











### manum相关问题



harbor登录

```
docker login 192.168.66.29:80 -u admin -p comleader@123
```

配置daemon.json里的地址，应该与登录的地址一致，包括端口





```
$ atomic --debug pull --storage ostree http:internal-url/namespace/image:tag
```



atomic install --system-package no --system --storage docker--name=etcd 192.168.66.29:80/openstack_magnum/etcd:v3.2.7



atomic --debug install --system-package no --system --storage docker  --name=etcd 192.168.66.29:80/openstack_magnum/etcd:v3.2.7



docker run -id  --name=etcd 192.168.66.29:80/openstack_magnum/etcd:v3.2.7



http://192.168.66.33/guoqiuxia/MCS-horizon/-/archive/master/MCS-horizon-master.tar.gz





生产云上有这两个虚拟机，之前用来制作执行体镜像的，gitlab-runner调试好了，可以迁上去，x86:192.168.67.45  arm：192.168.67.146









```
2022.10 之后云管改动较大的代码总结

1. 通过云硬盘、云硬盘快照创建云主机
2. 编排删除修改限制
3. k8s部分代码
4. 操作日志、监控服务等模块中文化显示
5. 迁移文件优化
6. 证书问题（现场生成证书）
7. 热数据缓存问题（云主机、容器、云硬盘、云硬盘快照）
8. 项目配额模块优化
9. 监控网卡状态优化
10. 
```





k8s新增



https://github.com/aylei/kubectl-debug/releases/download/v0.2.0-rc/kubectl-debug_0.2.0-rc_linux_amd64.tar.gz

/usr/local/bin/

镜像：aylei/debug-agent:latest

192.168.66.29:80/google_containers/debug-agent:latest



