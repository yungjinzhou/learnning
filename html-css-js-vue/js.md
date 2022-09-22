## JavaScript学习





### JavaScript嵌入页面的方式

1、行间事件（主要用于事件）

```
<input type="button" name="" onclick="alert('ok！');">
```

2、页面script标签嵌入

```
<script type="text/javascript">        
    alert('ok！');
</script>
```

3、外部引入

```
<script type="text/javascript" src="js/index.js"></script>
```





### 变量、数据类型及基本语法规范

JavaScript 是一种弱类型语言，javascript的变量类型由它的值来决定。 定义变量需要用关键字 'var'

```
 var iNum = 123;
 var sTr = 'asd';

 //同时定义多个变量可以用","隔开，公用一个‘var’关键字

 var iNum = 45,sTr='qwe',sCount='68';
```

**变量类型**

5种基本数据类型：
1、number 数字类型
2、string 字符串类型
3、boolean 布尔类型 true 或 false
4、undefined undefined类型，变量声明未初始化，它的值就是undefined
5、null null类型，表示空对象，如果定义的变量将来准备保存对象，可以将变量初始化为null,在页面上获取不到对象，返回的值就是null

1种复合类型：
object

**javascript语句与注释**

1、javascript语句开始可缩进也可不缩进，缩进是为了方便代码阅读，一条javascript语句应该以“;”结尾;

```
<script type="text/javascript">    
var iNum = 123;
var sTr = 'abc123';
function fnAlert(){
    alert(sTr);
};
fnAlert();
</script>
```

2、javascript注释

```
<script type="text/javascript">    

// 单行注释
var iNum = 123;
/*  
    多行注释
    1、...
    2、...
*/
var sTr = 'abc123';
</script>
```

**变量、函数、属性、函数参数命名规范**

1、区分大小写
2、第一个字符必须是字母、下划线（_）或者美元符号（$）
3、其他字符可以是字母、下划线、美元符或数字

**匈牙利命名风格：**

对象o Object 比如：oDiv
数组a Array 比如：aItems
字符串s String 比如：sUserName
整数i Integer 比如：iItemCount
布尔值b Boolean 比如：bIsComplete
浮点数f Float 比如：fPrice
函数fn Function 比如：fnHandler
正则表达式re RegExp 比如：reEmailCheck







### 函数

函数就是重复执行的代码片。

**函数定义与执行**

```
<script type="text/javascript">
    // 函数定义
    function fnAlert(){
        alert('hello!');
    }
    // 函数执行
    fnAlert();
</script>
```

**变量与函数预解析**
JavaScript解析过程分为两个阶段，先是编译阶段，然后执行阶段，在编译阶段会将function定义的函数提前，并且将var定义的变量声明提前，将它赋值为undefined。

```
<script type="text/javascript">    
    fnAlert();       // 弹出 hello！
    alert(iNum);  // 弹出 undefined
    function fnAlert(){
        alert('hello!');
    }
    var iNum = 123;
</script>
```

**函数传参** javascript的函数中可以传递参数。

```
<script type="text/javascript">
    function fnAlert(a){
        alert(a);
    }
    fnAlert(12345);
</script>
```

**函数'return'关键字**
函数中'return'关键字的作用：
1、返回函数中的值或者对象
2、结束函数的运行

```
<script type="text/javascript">
function fnAdd(iNum01,iNum02){
    var iRs = iNum01 + iNum02;
    return iRs;
    alert('here!');
}

var iCount = fnAdd(3,4);
alert(iCount);  //弹出7
</script>
```





### 条件语句

通过条件来控制程序的走向，就需要用到条件语句。

**条件运算符**
==、===、>、>=、<、<=、!=、&&(而且)、||(或者)、!(否)

**if else**

```
var iNum01 = 3;
var iNum02 = 5;
var sTr;
if(iNum01>iNum02){
    sTr = '大于';
}
else
{
    sTr = '小于';
}
alert(sTr);
```

**多重if else语句**

```
var iNow = 1;
if(iNow==1)
{
    ... ;
}
else if(iNow==2)
{
    ... ;
}
else
{
    ... ;
}
```









### 取元素方法

可以使用内置对象document上的getElementById方法来获取页面上设置了id属性的元素，获取到的是一个html对象，然后将它赋值给一个变量，比如：

```
<script type="text/javascript">
    var oDiv = document.getElementById('div1');
</script>
....
<div id="div1">这是一个div元素</div>
```

上面的语句，如果把javascript写在元素的上面，就会出错，因为页面上从上往下加载执行的，javascript去页面上获取元素div1的时候，元素div1还没有加载，解决方法有两种：

第一种方法：将javascript放到页面最下边

```
....
<div id="div1">这是一个div元素</div>
....

<script type="text/javascript">
    var oDiv = document.getElementById('div1');
</script>
</body>
```

第二种方法：将javascript语句放到window.onload触发的函数里面,获取元素的语句会在页面加载完后才执行，就不会出错了。

```
<script type="text/javascript">
    window.onload = function(){
        var oDiv = document.getElementById('div1');
    }
</script>

....

<div id="div1">这是一个div元素</div>
```





### 操作元素属性

获取的页面元素，就可以对页面元素的属性进行操作，属性的操作包括属性的读和写。

**操作元素属性**
var 变量 = 元素.属性名 读取属性
元素.属性名 = 新属性值 改写属性

**属性名在js中的写法**
1、html的属性和js里面属性写法一样
2、“class” 属性写成 “className”
3、“style” 属性里面的属性，有横杠的改成驼峰式，比如：“font-size”，改成”style.fontSize”

```
<script type="text/javascript">

    window.onload = function(){
        var oInput = document.getElementById('input1');
        var oA = document.getElementById('link1');
        // 读取属性值
        var sValue = oInput.value;
        var sType = oInput.type;
        var sName = oInput.name;
        var sLinks = oA.href;
        // 写(设置)属性
        oA.style.color = 'red';
        oA.style.fontSize = sValue;
    }

</script>

......

<input type="text" name="setsize" id="input1" value="20px">
<a href="http://www.itcast.cn" id="link1">传智播客</a>
```

**innerHTML**
innerHTML可以读取或者写入标签包裹的内容

```
<script type="text/javascript">
    window.onload = function(){
        var oDiv = document.getElementById('div1');
        //读取
        var sTxt = oDiv.innerHTML;
        alert(sTxt);
        //写入
        oDiv.innerHTML = '<a href="http://www.itcast.cn">传智播客<a/>';
    }
</script>

......

<div id="div1">这是一个div元素</div>
```





### 事件属性及匿名函数

**事件属性**
元素上除了有样式，id等属性外，还有事件属性，常用的事件属性有鼠标点击事件属性(onclick)，鼠标移入事件属性(mouseover),鼠标移出事件属性(mouseout),将函数名称赋值给元素事件属性，可以将事件和函数关联起来。

```
<script type="text/javascript">

window.onload = function(){
    var oBtn = document.getElementById('btn1');

    oBtn.onclick = myalert;

    function myalert(){
        alert('ok!');
    }
}

</script>
```

**匿名函数**
定义的函数可以不给名称，这个叫做匿名函数，可以将匿名函数的定义直接赋值给元素的事件属性来完成事件和函数的关联，这样可以减少函数命名，并且简化代码。函数如果做公共函数，就可以写成匿名函数的形式。

```
<script type="text/javascript">

window.onload = function(){
    var oBtn = document.getElementById('btn1');
    /*
    oBtn.onclick = myalert;
    function myalert(){
        alert('ok!');
    }
    */
    // 直接将匿名函数赋值给绑定的事件

    oBtn.onclick = function (){
        alert('ok!');
    }
}

</script>
```





### 数组及操作方法

数组就是一组数据的集合，javascript中，数组里面的数据可以是不同类型的。

**定义数组的方法**

```
//对象的实例创建
var aList = new Array(1,2,3);

//直接量创建
var aList2 = [1,2,3,'asd'];
```

**操作数组中数据的方法**
1、获取数组的长度：aList.length;

```
var aList = [1,2,3,4];
alert(aList.length); // 弹出4
```

2、用下标操作数组的某个数据：aList[0];

```
var aList = [1,2,3,4];
alert(aList[0]); // 弹出1
```

3、join() 将数组成员通过一个分隔符合并成字符串

```
var aList = [1,2,3,4];
alert(aList.join('-')); // 弹出 1-2-3-4
```

4、push() 和 pop() 从数组最后增加成员或删除成员

```
var aList = [1,2,3,4];
aList.push(5);
alert(aList); //弹出1,2,3,4,5
aList.pop();
alert(aList); // 弹出1,2,3,4
```

5、reverse() 将数组反转

```
var aList = [1,2,3,4];
aList.reverse();
alert(aList);  // 弹出4,3,2,1
```

6、indexOf() 返回数组中元素第一次出现的索引值

```
var aList = [1,2,3,4,1,3,4];
alert(aList.indexOf(1));
```

7、splice() 在数组中增加或删除成员

```
var aList = [1,2,3,4];
aList.splice(2,1,7,8,9); //从第2个元素开始，删除1个元素，然后在此位置增加'7,8,9'三个元素
alert(aList); //弹出 1,2,7,8,9,4
```

**多维数组**
多维数组指的是数组的成员也是数组的数组。

```
var aList = [[1,2,3],['a','b','c']];

alert(aList[0][1]); //弹出2;
```

批量操作数组中的数据，需要用到循环语句



### 循环语句

程序中进行有规律的重复性操作，需要用到循环语句。

**for循环**

```
for(var i=0;i<len;i++)
{
    ......
}
```

**课堂练习**
1、数组去重

```
var aList = [1,2,3,4,4,3,2,1,2,3,4,5,6,5,5,3,3,4,2,1];

var aList2 = [];

for(var i=0;i<aList.length;i++)
{
    if(aList.indexOf(aList[i])==i)
    {
        aList2.push(aList[i]);
    }
}

alert(aList2);
```

2、将数组数据放入页面











### 字符串处理方法

1、字符串合并操作：“ + ”

```
var iNum01 = 12;
var iNum02 = 24;
var sNum03 = '12';
var sTr = 'abc';
alert(iNum01+iNum02);  //弹出36
alert(iNum01+sNum03);  //弹出1212 数字和字符串相加等同于字符串相加
alert(sNum03+sTr);     // 弹出12abc
```

2、parseInt() 将数字字符串转化为整数

```
var sNum01 = '12';
var sNum02 = '24';
var sNum03 = '12.32';
alert(sNum01+sNum02);  //弹出1224
alert(parseInt(sNum01)+parseInt(sNum02))  //弹出36
alert(parseInt(sNum03))   //弹出数字12 将字符串小数转化为数字整数
```

3、parseFloat() 将数字字符串转化为小数

```
var sNum03 = '12.32'
alert(parseFloat(sNum03));  //弹出 12.32 将字符串小数转化为数字小数
```

4、split() 把一个字符串分隔成字符串组成的数组

```
var sTr = '2017-4-22';
var aRr = sTr.split("-");
var aRr2= sTr.split("");

alert(aRr);  //弹出['2017','4','2']
alert(aRr2);  //弹出['2','0','1','7','-','4','-','2','2']
```

5、indexOf() 查找字符串是否含有某字符

```
var sTr = "abcdefgh";
var iNum = sTr.indexOf("c");
alert(iNum); //弹出2
```

6、substring() 截取字符串 用法： substring(start,end)（不包括end）

```
var sTr = "abcdefghijkl";
var sTr2 = sTr.substring(3,5);
var sTr3 = sTr.substring(1);

alert(sTr2); //弹出 de
alert(sTr3); //弹出 bcdefghijkl
```

**字符串反转**

```
var str = 'asdfj12jlsdkf098';
var str2 = str.split('').reverse().join('');

alert(str2);
```



### 定时器

**定时器在javascript中的作用**
1、定时调用函数
2、制作动画

定时器类型及语法

```
/*
    定时器：
    setTimeout  只执行一次的定时器 
    clearTimeout 关闭只执行一次的定时器
    setInterval  反复执行的定时器
    clearInterval 关闭反复执行的定时器

*/

var time1 = setTimeout(myalert,2000);
var time2 = setInterval(myalert,2000);
/*
clearTimeout(time1);
clearInterval(time2);
*/
function myalert(){
    alert('ok!');
}
```





### 变量作用域

变量作用域指的是变量的作用范围，javascript中的变量分为全局变量和局部变量。

1、全局变量：在函数之外定义的变量，为整个页面公用，函数内部外部都可以访问。
2、局部变量：在函数内部定义的变量，只能在定义该变量的函数内部访问，外部无法访问。

```
<script type="text/javascript">
    // 定义全局变量
    var a = 12;
    function myalert()
    {
        // 定义局部变量
        var b = 23;
        alert(a);
        // 修改全局变量
        a++;
        alert(b);
    }
    myalert(); // 弹出12和23
    alert(a);  // 弹出13    
    alert(b);  // 出错
</script>
```





### 封闭函数

封闭函数是javascript中匿名函数的另外一种写法，创建一个一开始就执行而不用命名的函数。

一般定义的函数和执行函数：

```
function myalert(){
    alert('hello!');
};

myalert();
```

封闭函数：

```
(function(){
    alert('hello!');
})();
```

还可以在函数定义前加上“~”和“!”等符号来定义匿名函数

```
!function(){
    alert('hello!');
}()
```

**封闭函数的作用**
封闭函数可以创造一个独立的空间，在封闭函数内定义的变量和函数不会影响外部同名的函数和变量，可以避免命名冲突，在页面上引入多个js文件时，用这种方式添加js文件比较安全，比如：

```
var iNum01 = 12;
function myalert(){
    alert('hello!');
}

(function(){
    var iNum01 = 24;
    function myalert(){
        alert('hello!world');
    }
    alert(iNum01);
    myalert()
})()

alert(iNum01);
myalert();
```







