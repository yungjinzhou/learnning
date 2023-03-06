# 数据库操作常用命令



登录

```
mysql -u username -p password

```





数据库操作

```
显示数据库列表
show databases;

创建数据库 
create database name; 



创建数据库并指定字符集
CREATE DATABASE `wangzy_table` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
CREATE DATABASE db2 IF NOT EXISTS db2 DEFAULT CHARACTER SET utf8 COLLATE utf_general_ci;
码区别：（说明：新建数据库时一般选用 utf8_general_ci 就可以）
utf8_bin:将字符串中的每一个字符用二进制数据存储，区分大小写。
utf8_genera_ci:不区分大小写，即大小写不敏感。
utf8_general_cs:区分大小写，即大小写敏感
utf8_unicode_ci:不能完全支持组合的记号。




选择数据库 
use databasename; 


直接删除数据库，不提醒 
drop database database_name;
```





表操作

```


```





创建用户

```
```





设置权限

```


-- 3、创建用户并授权
grant all privileges on database_name.* to database_user@host_ip identified by 'database_password';

grant all privileges on database_name.* to database_user@’%‘ identified by 'database_password'; # 所有ip


-- 4、刷新权限 
flush privileges;


mysql> use mysql;
mysql> select * from user where user='root' and host='localhost'\G;  #所有权限都是Y ，就是什么权限都有
mysql> select * from db where user='root' and host='localhost'\G;  # 没有此条记录
mysql> select * from tables_priv where user='root' and host='localhost';  # 没有此条记录
 
mysql> select * from columns_priv where user='root' and host='localhost'; # 没有此条记录
 
mysql> select * from procs_priv where user='root' and host='localhost'; # 没有此条记录



查看root@’localhost’用户的权限
show grants for root@localhost;




```

