# html学习



### 基本结构

```html
<!DOCTYPE html>
<html>
<!--   <html lang="en"> 注释  -->

    <head>
        <meta charset="utf-8">
        <title>基本结构</title>
    </head>

    <body>
        hi guys! 欢迎!
    </body>

</html>

```



### 标题标签

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>03-标题标签</title>
</head>
<body>
    <!-- 03-标题标签
    h1最大的 h6最小的
    -->
    <h1>标题标签</h1>
    <h2>标题标签</h2>
    <h3>标题标签</h3>
    <h4>标题标签</h4>
    <h5>标题标签</h5>
    <h6>标题标签</h6>

</body>
</html>

```

### 链接标签

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>04-链接标签</title>
</head>
<body>
    <!-- 04-链接标签 
        锚 点
        anchor point

        a
        href: 网址
              本地的路径

        target:目标
                新开页面  "_blank"
                默认 "_self"
    -->

    <a href="http://www.baidu.com" target="_blank">百度链接标签</a>
    <a href="./03-标题标签.html">标题标签</a>

    <!-- 了解 空链接 -->
    <a href="">空链接 " "刷新整个页面</a>
    <a href="#">空链接 #</a>


</body>
</html>
```



### 图片链接

```html

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>05-图片的链接</title>
</head>
<body>
    <!-- 05-图片的链接
    image
    img: 
        src :source 图片的路径

        alt:1.如果图片不存在, 提示用户
            2.爬虫, 图片,alt
    -->
    <img src="./images/test333.png" alt="美女的图片">
</body>
</html>

```



### 段落标签

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>07-段落标签</title>
</head>
<body>
    <!-- 换行的标签 br 单标签也是有关闭
    分割线 hr

    07-段落标签  p pragraph
    -->
    <p>
                人工智能（Artificial Intelligence），英文缩<br />
            为AI。它是研究、开发用于模拟、延伸和扩展人的智能的<br />
            理论、方法、技术及应用系统的一门新的技术科学。 人工<br />
            智能是计算机科学的一个分支，它企图了解智能的实质，并<br>
            生产出一种新的能以人类智能相似的方式做出反应的智能机<br>
            器，该领域的研究包括机器人、语言识别、图像识别、自然<br>
            语言处理和专家系统等.

    </p>
    
</body>
</html>
```



### 字符实体

```htm
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>08-字符实体</title>
</head>
<body>
        <!-- 08-字符实体
        空格: &nbsp;
        >: &gt;
        <: &lt;
        -->
        技术博客: 今天学习了 段落标签 &lt;p&gt;&lt;/p&gt;
        <p>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  人工智能（Artificial Intelligence），英文缩<br />
            为AI。它是研究、开发用于模拟、>>>>>延伸和扩展人的智能的<br />
            理论、方法、技术及应用系统的一门新的技术科学。 人工<br />
            智能是计算机科学的一个分支，它企图了解智能的实质，并<br>
            生产出一种新的能以人类智能相似的方式做出反应的智能机<br>
            器，该领域的研究包括机器人、语言识别、图像识别、自然<br>
            语言处理和专家系统等.

    </p>
</body>
</html>
```



### div和span标签

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>09-div和span标签</title>
    
</head>
<body>
    <!-- 09-div和span标签 
    
    span 一段话中 某一部分
    -->
    <div>
        包裹标签用的 封装布局
    </div>

    <p>
            <span>苹果</span> （学名：Malus pumila）是水果的一种，是蔷薇科苹果亚科苹果属植物，其树为落叶乔木。苹果的果实富含矿物质和维生素，是人们经常食用的水果之一。苹果是一种低热量食物，每...
    </p>
    
</body>
</html>
```



### 综合使用实例

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>10-今日头条</title>
</head>
<body>
    <!-- 1.最外侧 div -->
    <div>
        <!-- 2.头部 div > h3 + a -->
        <div>
            <h3>今日头条</h3>
            <a href="#">更多&gt;</a>
        </div>
        <!-- 3.img -->
        <img src="images/banner.jpg" alt="计算机">
        <!-- 4.p -->
        <p>
                人工智能（Artificial Intelligence），英文缩写为AI。它是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的一门新的技术科学。 人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器，该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等.
        </p>

    </div>
    
</body>
</html>
```



























