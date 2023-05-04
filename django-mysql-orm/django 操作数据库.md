





# Django-orm相关





## 1. Django orm操作

```
1. 取具体数据值
node_info = NodeInfo.objects.get(name=host_name)
node_info.name  # 取出某一项数据

2. 取出第一条数据
node_data = NodeInfo.objects.filter(id=node_id).values().first()

3.
data_before = db_table.objects.filter(create_timestamp__gte=start_time, reate_timestamp__lte=end_time, hardware_name=hardware_name, vm_id=vm_id, source_type=source_type)
 d = data_before.filter(create_timestamp=t)
data_dict[t] = {data.source_tag: data.source_usage for data in d.all()}


4.取出一条数据
>>> from django.contrib.auth.models import User  
>>> from django.forms.models import model_to_dict  
>>> u = User.objects.get(id=1)  
>>> u_dict = model_to_dict(u)  


多个QuerySet对象,使用循环解析成字典
hot_data_obj = model.objects.filter(xxxxx)
for obj in hot_data_obj.values():
      target_dict = obj
      
http://www.chenxm.cc/article/350.html


保存
hot_data_obj = HotDataStore.objects.filter(uuid=target_uuid, resource_type=resource_type)[0]
hot_data_obj.name = target_name
hot_data_obj.save()




# 批量删除
HotDataStore.objects.filter(in__uuid=target_uuid_list).delete()
# 单独删除
HotDataStore.objects.filter(uuid=target_uuid).delete()

```



## 2. django处理多migrations文件





### 第一步：重置数据库 django_migrations 指定模块的记录

```
python manage.py migrate --fake MODEL_NAME zero
```

这一步主要是根据指定模块下的，migrations 子文件夹下的生成的更改记录，将数据库 django_migrations 中指定模块的（MODEL_NAME）迁移记录进行删除。

但是！这只是删除记录，并不会对已经生成的数据库结构做任何更改。

如果有多个环境，那么在进行下一步之前分别对多环境执行相同操作。

### 第二步：重新生成新的 migrations 文件

手动删除指定模块下的， migrations 子文件夹下的除了 `__init__.py` 文件之外的所有的数据库迁移文件。然后重新执行下面命令生成新的 `0001_initial` 记录。

```
python manage.py makemigrations MODEL_NAME
```

### 第三步：0

通过执行下面命令重新在数据库 django_migrations 中生成新的迁移记录，这时候记录就只有一个了。

```
python manage.py migrate --fake-initial MODEL_NAME
```

如果有多个环境，那么分别对多环境执行相同操作。





如果要进一步清理admin、auth等django自带app的迁移文件，可以执行如下

```
python manage.py makemigrations --empty admin
python manage.py makemigrations --empty auth

python manage.py makemigrations
python manage.py migrate
```





## 3.迁移时报表已存在迁移失败





```
把这个表单独迁移
python manage.py migrate goods --fake
然后再迁移所有的表
python manage.py migrate


由于手动删除数据库表等操作，导致migration与实际table不一致，–fake 不会执行sql操作，只是对migration做标记，生成django_migrations表的内容。 使migration与table重新一致



```



参考链接：https://blog.csdn.net/qq_38992249/article/details/116828497



## 4. 分页查询，优化查询

当遇到数据量大时进行分页查询，不要全部查询出来在切片处理，要先切片处理，在进一步处理数据



比如页数为page

每页个数为limit

```
start=(page-1)*limit
end=start+limit
```



获取总数

```
total = Article.objects.filter(btype=stype).count()
```

获取指定页数的数据（有过滤）

```cobol
target_data = Article.objects.filter(btype=stype)[start:end].values("id","title")
```







