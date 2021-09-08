### openstack-stein版heat部署指南

#### 创建Heat数据库

1. 使用数据库访问客户端以root用户身份连接到数据库服务器。

   ```
   mysql -u root -p
   ```

2. 创建heat数据库。

   ```
   CREATE DATABASE heat;
   ```

3. 授予对Heat数据库的适当访问权限。

   ```
   GRANT ALL PRIVILEGES ON heat.* TO 'heat'@'localhost' IDENTIFIED BY 'comleader@123'; 
   GRANT ALL PRIVILEGES ON heat.* TO 'heat'@'%' IDENTIFIED BY 'comleader@123';
   ```

4. 退出数据库。

#### 先决环境配置

1. 来源admin凭据来访问仅管理员CLI命令。

   ```
   source /root/admin-openrc
   ```

   

2. 创建服务凭据。

   

   1. 创建Heat用户；将admin角色添加到heat用户；创建heat和heat-cfn服务实体。

   ```
   openstack user create --domain default --password-prompt heat
   openstack role add --project service --user heat admin
   openstack service create --name heat --description "Orchestration" orchestration 
   openstack service create --name heat-cfn --description "Orchestration" cloudformation
   ```

   

   1. 创建Orchestration服务API端点。

      ```
      
      openstack endpoint create --region RegionOne orchestration public http://controller:8004/v1/%\(tenant_id\)s 
      
      openstack endpoint create --region RegionOne orchestration internal http://controller:8004/v1/%\(tenant_id\)s 
      
      openstack endpoint create --region RegionOne orchestration admin http://controller:8004/v1/%\(tenant_id\)s 
      
      openstack endpoint create --region RegionOne cloudformation public http://controller:8000/v1 
      
      openstack endpoint create --region RegionOne cloudformation internal http://controller:8000/v1 
      
      openstack endpoint create --region RegionOne cloudformation admin http://controller:8000/v1
      ```

      

      

3. Orchestration需要Identity Service中的其他信息来管理堆栈。要添加此信息，请完成以下步骤：

   

   1. 创建Heat包含堆栈项目和用户的域。创建heat_domain_admin用户以管理heat域中的项目和用户并设置密码；将admin角色添加到域中的heat_domain_admin用户heat以启用用户的管理堆栈管理权限heat_domain_admin；在Heat域中创建常规项目demo和常规用户demo；创建heat_stack_owner角色；将heat_stack_owner角色添加到demo项目和用户以启用用户的堆栈管理demo；创建heat_stack_user角色。

   ```
   openstack domain create --description "Stack projects and users" heat
   openstack user create --domain heat --password-prompt heat_domain_admin
   openstack role add --domain heat --user-domain heat --user heat_domain_admin admin
   openstack project create --domain heat --description "Demo Project" demo 
   openstack user create --domain heat --password-prompt demo
   openstack role create heat_stack_owner
   openstack role add --project demo --user demo heat_stack_owner
   openstack role create heat_stack_user
   ```

   

#### 安装和配置Heat

1. 安装软件包。

   ```
   yum -y install openstack-heat-api openstack-heat-api-cfn openstack-heat-engine
   ```

   

2. 修改“/etc/rabbitmq/rabbitmq.config”。

   ```
   {delegate_count, 96}
   ```

3. 编辑“/etc/heat/heat.conf”文件并完成以下配置：

   sed -i.default -e "/^#/d" -e "/^$/d" /etc/heat/heat.conf

   1. 在default中配置消息列队访问端口以及stack基本管理认证。

      ```
      [DEFAULT]
      transport_url = rabbit://openstack:openstack@controller
      heat_metadata_server_url = http://controller:8000
      heat_waitcondition_server_url = http://controller:8000/v1/waitcondition
      stack_domain_admin = heat_domain_admin
      stack_domain_admin_password = comleader@123
      stack_user_domain_name = heat
      num_engine_workers = 4
      [heat_api]
      workers = 4
      [database]
      connection = mysql+pymysql://heat:comleader@123@controller/heat
      [keystone_authtoken]
      www_authenticate_uri = http://controller:5000
      auth_url = http://controller:5000
      memcached_servers = controller:11211
      auth_type = password
      project_domain_name = default
      user_domain_name = default
      project_name = service
      username = heat
      password = comleader@123
      [trustee]
      auth_type = password
      auth_url = http://controller:5000
      username = heat
      password = comleader@123
      user_domain_name = default
      [clients_keystone]
      auth_uri = http://controller:5000
      ```

      

4. 填充Orchestration数据库。

   ```
   su -s /bin/sh -c "heat-manage db_sync" heat
   ```

#### 完成安装

1. 启动Orchestration服务并将其配置为在系统引导时启动。

   

   ```
   systemctl enable openstack-heat-api.service openstack-heat-api-cfn.service openstack-heat-engine.service
   systemctl start openstack-heat-api.service openstack-heat-api-cfn.service openstack-heat-engine.service
   systemctl status openstack-heat-api.service openstack-heat-api-cfn.service openstack-heat-engine.service
   ```

   

#### 验证操作

1. 使用admin用户登录OpenStack 命令行。

   

2. 列出服务组件以验证每个进程的成功启动和注册。

   ```
   openstack orchestration service list
   ```

#### heat-dashboard安装



安装

```
pip install heat-dashboard==2.0.2
```

拷贝配置文件

```
cp /usr/lib/python2.7/site-packages/heat_dashboard/enabled/_[1-9]*.py \
      /usr/share/openstack-dashboard/openstack_dashboard/local/enabled
```

<heat-dashboard-dir>是目录，centos7中:/usr/lib/python2.7/site-packages/heat-dashboard/

修改配置 **local_settings.py** 

```
POLICY_FILES['orchestration'] = '<heat-dashboard-dir>/conf/heat_policy.json'

```

编译heat-dashboard

```
$ cd <heat-dashboard-dir>
$ python ./manage.py compilemessages
```

执行更新

```
$ cd <horizon-dir>
$ DJANGO_SETTINGS_MODULE=openstack_dashboard.settings python manage.py collectstatic --noinput
$ DJANGO_SETTINGS_MODULE=openstack_dashboard.settings python manage.py compress --force
```

重启server

````
systemctl restart httpd
````

