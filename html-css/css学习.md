## css学习



### 书写方式

#### 行内式

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>11-CSS书写方式之行内式</title>
</head>
<body>
    <!-- 11-CSS书写方式之行内式
        文字颜色  王宝绿
     -->
     <div style="color:green">CSS书写方式之行内式</div>
     
    
    
</body>
</html>
```



#### 嵌入式

在head标签中指定style标签

指定的div，其他标签不受限制

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>12-CSS书写方式之嵌入式</title>

    <style>
        div{
            color:green;
        }

    </style>
</head>
<body>
        <!-- 12-CSS书写方式之嵌入式 -->
        <div>
                CSS书写方式之嵌入式
        </div>

        <p>段落</p>
</body>
</html>

```



#### 外链式(生产开发常用)

在head标签中指定link标签

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>13-CSS书写方式之外链式</title>

    <!-- 关联文件css  -->
    <link rel="stylesheet" href="css/out.css">

</head>
<body>
    <div>13-CSS书写方式之外链式</div>
</body>
</html>


```

out.css

```css
div{
    color:green
}
```

### 文本属性

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>14-文本属性</title>
    <!-- 
        1.字体大小
        2.字体 种类
        3.字体颜色
        4.去掉下划线
        5.行高
     -->
     <style>
         p{
            /* 1.字体大小  浏览器默认是 16px */
            font-size:30px;
            /* 2.字体 种类 */
            font-family: "Microsoft YaHei"; 
            
            /* 3.字体颜色 */
            color:#af4567;

            /* 4.增加掉下划线 */
            text-decoration: underline;

            /* 5.行高  */
            line-height: 50px;
         }

         a{
             text-decoration: none;
         }

     </style>
</head>
<body>
    <a href="#">连接标签</a>
    <p>
            1.字体大小
            2.字体 种类
            3.字体颜色
            4.去掉下划线
            5.行高
    </p>
    

</body>
</html>
```

宽高和边框属性

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=
    , initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>15-宽高和边框属性</title>

    <style>
        div{
            width: 500px;
            height: 500px;
            
            /* 设置背景颜色
             */
             background-color: red;

             /* 边框 border */
                        /* 粗细  实线  颜色 */
             border-top: 20px solid green;
                                /* 点线 */
             border-bottom: 10px dotted lightblue;
                                /* 虚线 */
             border-left: 20px dashed yellow;
             border-right: 10px double brown;

             /* 四个边 */
             border:10px solid green;
        }
    
    </style>
</head>
<body>
    <div>
            15-宽高和边框属性
    </div>
    
</body>
</html>
```

外边距

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>16-外边距margin</title>

    <style>
        div{
            width: 200px;
            height: 200px;

            background-color: red;
            /* 外边距 */
            margin-top: 40px;
            margin-left: 50px;

            margin-right: 100px;
            margin-bottom: 200px;

            /* 连写 */
            margin: 50px;
                  /* 上下  左右 */
            margin:50px 100px;
                    /* 上  左右  下 */
            margin:50px  100px 200px;
                    /* 顺时针 */
            margin:10px 20px 30px 40px;

            /* 使用技巧div  水平居中*/
            /* margin: 0 540px; */
            margin: 0 auto;
        }
    </style>
</head>
<body>
    <div>
        第一个 div
    </div>
    <div>
            第222个 div
    </div>
    
</body>
</html>
```

padding(内边距)属性

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>17-CSS的属性padding</title>

    <style>
        div{
            width: 230px;
            height: 230px;
            background-color: red;

            /* 内边距 padding  */
            padding-top: 50px;
            padding-left: 50px;

            /* 连写 */
            padding: 30px;
            padding: 30px 50px;
            padding: 30px 50px 100px;
            padding: 30px 50px 100px 40px;
        }
    </style>
</head>
<body>
    <div>div的文字</div>
    <!-- <div>div的文字内容只是一部分div的文字内容只是一部分div的div的文字内容只是一部分div的文字内容只是一部分div的div的文字内容只是一部分div的文字内容只是一部分div的div的文字内容只是一部分div的文字内容只是一部分div的文字内容只是一部分div的文字内容只是一部分div的文字内容只是一部分div的文字内容只是一部分</div> -->
</body>
</html>
```



选择器

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>18-选择器</title>
    <!-- 寻找标签  选择器 -->

    <style>
        /* 1.标签选择器  一般不用 */
        /* div{
            color:red;
        } */

        /* 2. 类选择器  实际*/
        /* .first{
           color:red; 
        } */
        
        /* 3.层级选择器 后代选择器 嵌套 */
        
        /* div p{
            color:green;
        } */

        .second p{
            color:blueviolet;
        }
       

    </style>
</head>
<body>

    <div class="first">div的标签111</div>
    <div>div的标签222</div>
    <div>div的标签333</div>

    <div class="second">
        <p>
            嵌套的标签
        </p>
        <div>
            <p>
                孙子标签
            </p>
        </div>
    </div>

    <p>标签</p>
    
</body>
</html>
```









