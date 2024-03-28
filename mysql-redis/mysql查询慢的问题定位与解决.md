## mysql查询慢的问题定位与解决



### 1. 首先打开慢查询日志

有时候我们需要排查执行缓慢的SQL语句，这就用到了mysql慢查询日志。

开启慢查询日志的方式有两种：临时开启和永久开启。

开启慢查询日志功能可能需要mysql的版本达到5.7，可以通过select VERSION();查看版本号。

看一下当前mysql数据库是否开启了慢查询

show variables like 'slow_query%';

show variables like 'long_query%';

slow_query_log 慢查询开启状态，ON开启，OFF关闭
slow_query_log_file 慢查询日志存放的位置（这个目录需要MySQL的运行帐号的可写权限，一般设置为MySQL的数据存放目录）
long_query_time 查询超过多少秒才记录（才算是慢查询）

#### 1.1、临时开启（数据库服务重启后失效）

set global slow_query_log_file='/var/lib/mysql/tmp_slow.log';
set global long_query_time=1;

set global log_output='FILE,TABLE';  //默认是FILE。如果也有TABLE，则同时输出到mysql库的slow_log表中。
set global slow_query_log='ON';

long_query_time设置后需要打开一个新的查询窗口（会话）才能看到新设置的值。老的查询窗口还是显示之前的值，其实已经改了。

#### 1.2、永久开启（数据库服务重启后不失效）

修改配置文件my.cnf，在[mysqld]下的下方加入
[mysqld]
slow_query_log = ON
slow_query_log_file = /var/lib/mysql/tmp_slow.log     //linux
long_query_time = 1

然后重启mysql服务。



### 2.Explain 查看有问题的SQL语句

当SQL查询速度比较慢的时候，我们可以用explain查看这个SQL语句的相关情况



我们进行数据查询很慢时，可能就会存在索引失效的情况。遇到这种情况不要怕，我们可以使用explain命令对select语句的执行计划进行分析。explain出来的信息有10列，分别是

```sql
id、select_type、table、type、possible_keys、key、key_len、ref、rows、Extra
```

各列的含义

```
id: SELECT 查询的标识符. 每个 SELECT 都会自动分配一个唯一的标识符.
select_type: SELECT 查询的类型.
table: 查询的是哪个表
partitions: 匹配的分区
type: join 类型
possible_keys: 此次查询中可能选用的索引
key: 此次查询中确切使用到的索引.
ref: 哪个字段或常数与 key 一起被使用
rows: 显示此查询一共扫描了多少行. 这个是一个估计值.
filtered: 表示此查询条件所过滤的数据的百分比
extra: 额外的信息
```



#### 2.1 id

每个SELECT语句都会自动分配的一个唯一标识符，表示查询中操作表的顺序，有四种情况：

- id相同：执行顺序由上到下
- id不同：如果是子查询，id号会自增，id越大，优先级越高。
- id相同的不同的同时存在
- id列为null的就表示这是一个结果集，不需要使用它来进行查询。

#### 2.2 select_type

表示查询类型，主要用于区别普通查询、联合查询(union、union all)、子查询等复杂查询。

##### 2.2.1 simple

表示不需要union操作或者不包含子查询的简单select查询。

![img](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/614c97dac620430786cfd06298f0fc12~tplv-k3u1fbpfcp-zoom-in-crop-mark:4536:0:0:0.image)

##### 2.2.2 primary

一个需要union操作或者含有子查询的select，位于最外层的单位查询的select_type即为primary，并且只有有一个  。

![img](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/6eb024bcb6ca48d4a92c4e3bc961cd8b~tplv-k3u1fbpfcp-zoom-in-crop-mark:4536:0:0:0.image)

先执行括号里面的sql语句，再执行外面的sql语句，内层的查询就是subquery。

##### 2.2.3 subquery

除了from字句中包含的子查询外，其他地方出现的子查询都可能是subquery。

##### 2.2.4 dependent subquery

表示这个subquery的查询要受到外部表查询的影响。

![img](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/ce67eb03b63a44d69291d1df0ef45c51~tplv-k3u1fbpfcp-zoom-in-crop-mark:4536:0:0:0.image)

##### union

，它连接的两个select查询，第一个查询是PRIMARY，除了第一个表外，第二个以后的表select_type都是union。

![img](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/f4bd91ebb8494a15ba70adf461eca046~tplv-k3u1fbpfcp-zoom-in-crop-mark:4536:0:0:0.image)

##### 2.2.6 dependent union

它与union一样，出现在union 或union all语句中，但是这个查询要受到外部查询的影响。

![img](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/72552fff32974a70956064ab6dc72b78~tplv-k3u1fbpfcp-zoom-in-crop-mark:4536:0:0:0.image)

##### 2.2.7 union result

它包含union的结果集，在union和union all语句中,因为它不需要参与查询，所以id字段为null。

##### 2.2.8 derived

from字句中出现的子查询，也叫做派生表，其他数据库中可能叫做内联视图或嵌套select。

![img](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/e0d06df2003d4f57b883739ca1bb99a7~tplv-k3u1fbpfcp-zoom-in-crop-mark:4536:0:0:0.image)

可以理解为就是from字句后面出现子查询，取个别名，叫派生表。

#### 2.3 table

显示查询的表名，如果查询使用了别名，那么这里显示的是别名。

#### 2.4 type

它会显示很多参数类型，性能依次从好到坏显示为这样：

```sql
system，const，eq_ref，ref，fulltext，ref_or_null，unique_subquery，index_subquery，range，index_merge，index，ALL

通常来说, 不同的 type 类型的性能关系如下:
ALL < index < range ~ index_merge < ref < eq_ref < const < system
ALL 类型因为是全表扫描, 因此在相同的查询条件下, 它是速度最慢的.
而 index 类型的查询虽然不是全表扫描, 但是它扫描了所有的索引, 因此比 ALL 类型的稍快.
后面的几种类型都是利用了索引来查询数据, 因此可以过滤部分或大部分数据, 因此查询效率就比较高了

```

除了all之外，其他的type都可以使用到索引，除了index_merge之外，其他的type只可以用到一个索引，优化器会选用最优索引一个，最少要索引使用到range级别。 老刘只讲这个重要的，有些内容也没搞清楚。

##### 2.4.1 system

可遇不可求，表中只有一行数据或是空表。

##### 2.4.2 const

使用唯一索引或主键，返回记录一定是1行记录的等值where条件。

##### 2.4.3 eq_ref

一般是连接字段主键或者唯一性索引。

此类型通常出现在多表的 join 查询，表示对于前表的每一个结果，都只能匹配到后表的一行结果。并且查询的比较操作通常是 '='，查询效率较高。

##### 2.4.4 ref

针对非唯一性索引，使用等值（=）查询非主键。或者是使用了最左前缀规则索引的查询。

##### 2.4.5 range

索引范围扫描，常见于使用>,<,is null,between ,in ,like等运算符的查询中。

##### 2.4.6 index

关键字：条件是出现在索引树中的节点的，可能没有完全匹配索引。

索引全表扫描，把索引从头到尾扫一遍，常见于使用索引列就可以处理不需要读取数据文件的查询、可以使用索引排序或者分组的查询。

##### 2.4.7 all

这个就是全表扫描数据文件，然后再在server层进行过滤返回符合要求的记录。

possible_keys、key、key_len、ref、rows就不讲了，直接讲最后一个extra。

#### 2.5 possible_keys

`possible_keys` 表示 MySQL 在查询时, 能够使用到的索引. 注意, 即使有些索引在 `possible_keys` 中出现, 但是并不表示此索引会真正地被 MySQL 使用到. MySQL 在查询时具体使用了哪些索引, 由 `key` 字段决定.

#### 2.6 key

此字段是 MySQL 在当前查询时所真正使用到的索引.

#### 2.7 key_len

表示查询优化器使用了索引的字节数. 这个字段可以评估组合索引是否完全被使用, 或只有最左部分字段被使用到.
key_len 的计算规则如下:

- 字符串
  - char(n): n 字节长度
  - 字符串
    - char(n): n 字节长度
    - varchar(n): 如果是 utf8 编码, 则是 3 *n + 2字节; 如果是 utf8mb4 编码, 则是 4* n + 2 字节.
  - 数值类型:
    - TINYINT: 1字节
    - SMALLINT: 2字节
    - MEDIUMINT: 3字节
    - INT: 4字节
    - BIGINT: 8字节
  - 时间类型
    - DATE: 3字节
    - TIMESTAMP: 4字节
    - DATETIME: 8字节
  - 字段属性: NULL 属性 占用一个字节. 如果一个字段是 NOT NULL 的, 则没有此属性.

#### rows

rows 也是一个重要的字段. MySQL 查询优化器根据统计信息, 估算 SQL 要查找到结果集需要扫描读取的数据行数.
这个值非常直观显示 SQL 的效率好坏, 原则上 rows 越少越好.

#### 2.9 extra

这个列包含不适合在其他列中显示单十分重要的额外的信息，这个列可以显示的信息非常多，有几十种，这里写常见的几种。

##### no tables used

表示不带from字句的查询，使用not in()形式子查询或not exists运算符的连接查询，这种叫做反连接。一般连接查询是先查询内表，再查询外表，反连接就是先查询外表，再查询内表。

##### using filesort(重要)

排序时无法使用到索引时，就会出现这个，常见于order by和group by语句中。

##### using index(重要)

查询时不需要回表查询，直接通过索引就可以获取查询的数据。

##### using where(重要)

通常type类型为all，记录并不是所有的都满足查询条件，通常有where条件，并且一般没索引或者索引失效。

讲完分析索引的参数后，现在老刘讲一些索引失效的情况，大家一定要用心记住，老刘也记了好几遍！





### 3.show profile使用

```
elect  @@profiling;   --查看profile的开启情况
set profiling=1;  --开启profile
show profiles; 查看执行的mysql列表
show profile;--查询最近一条sql的执行详细信息
show profile for query 143; --查询指定id的sql执行详细信息
show profile cpu;--获取执行sql语句时的CPU信息  show  profile cpu for query queryid;
show profile all;--显示所有性能信息
show profile block io; 显示快io操作的次数
show profile ipc;显示发送和接收的消息数量
show profile source;--显示源码中的函数和位置
show profile cpu,block io,memory,swaps,context switches,source for query Query_ID;--cpu bliock块 内存 显示swap次数 上下文切换册数
```





参考链接：

https://www.cnblogs.com/zouhong/p/14295250.html













定位与分析

参考文献：https://www.cnblogs.com/bigdatalaoliu/p/14384680.html



























**1）使用ALTER TABLE语句创建索引。**
语法如下：
alter table table_name add index index_name (column_list) ;
alter table table_name add unique (column_list) ;
alter table table_name add primary key (column_list) ;
其中包括普通索引、UNIQUE索引和PRIMARY KEY索引3种创建索引的格式，table_name是要增加索引的表名，column_list指出对哪些列进行索引，多列时各列之间用逗号分隔。索引名index_name可选，缺省时，MySQL将根据第一个索引列赋一个名称。另外，ALTER TABLE允许在单个语句中更改多个表，因此可以同时创建多个索引。
创建索引的示例如下：
mysql> use tpsc
Database changed
mysql> alter table tpsc add index shili (tpmc ) ;
Query OK, 2 rows affected (0.08 sec)
Records: 2 Duplicates: 0 Warnings: 0

**（2）使用CREATE INDEX语句对表增加索引。**
能够增加普通索引和UNIQUE索引两种。其格式如下：
create index index_name on table_name (column_list) ;
create unique index index_name on table_name (column_list) ;
说明：table_name、index_name和column_list具有与ALTER TABLE语句中相同的含义，索引名不可选。另外，不能用CREATE INDEX语句创建PRIMARY KEY索引。

**（3）删除索引。**
删除索引可以使用ALTER TABLE或DROP INDEX语句来实现。DROP INDEX可以在ALTER TABLE内部作为一条语句处理，其格式如下：
drop index index_name on table_name ;
alter table table_name drop index index_name ;
alter table table_name drop primary key ;
其中，在前面的两条语句中，都删除了table_name中的索引index_name。而在最后一条语句中，只在删除PRIMARY KEY索引中使用，因为一个表只可能有一个PRIMARY KEY索引，因此不需要指定索引名。如果没有创建PRIMARY KEY索引，但表具有一个或多个UNIQUE索引，则MySQL将删除第一个UNIQUE索引。
如果从表中删除某列，则索引会受影响。对于多列组合的索引，如果删除其中的某列，则该列也会从索引中删除。如果删除组成索引的所有列，则整个索引将被删除。
删除索引的操作，如下面的代码：
mysql> drop index shili on tpsc ;
Query OK, 2 rows affected (0.08 sec)
Records: 2 Duplicates: 0 Warnings: 0
该语句删除了前面创建的名称为“shili”的索引。

