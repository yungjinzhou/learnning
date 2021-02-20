# django 操作数据库





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



