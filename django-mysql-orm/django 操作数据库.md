# Django-orm





### Django orm操作

```
1. 取具体数据值
node_info = NodeInfo.objects.get(name=host_name)
node_info.name  # 取出某一项数据

2. 
node_data = NodeInfo.objects.filter(id=node_id).values().first()

3.
data_before = db_table.objects.filter(create_timestamp__gte=start_time, reate_timestamp__lte=end_time, hardware_name=hardware_name, vm_id=vm_id, source_type=source_type)
 d = data_before.filter(create_timestamp=t)
data_dict[t] = {data.source_tag: data.source_usage for data in d.all()}


4.
>>> from django.contrib.auth.models import User  
>>> from django.forms.models import model_to_dict  
>>> u = User.objects.get(id=1)  
>>> u_dict = model_to_dict(u)  

http://www.chenxm.cc/article/350.html
```



### django处理migrations

项目开发一段时间后，在每次部署迁移时候，会遇到多次执行迁移文件的问题，会发生迁移失败的情况，执行下面步骤可以解决。

可以先删除每个app下migrations文件夹下除了`__init__.py`之外的文件，还要删除`__pycache__`文件夹

执行命令，重新生成各个app的initial文件，并同步数据库（针对空数据库）

```
python3 manager.py makemigrations
python3 manager.py migrate
```

如果要进一步清理admin、auth等django自带app的迁移文件，可以执行如下

```
python manage.py makemigrations --empty admin
python manage.py makemigrations --empty auth

python manage.py makemigrations
python manage.py migrate
```

















