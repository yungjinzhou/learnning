## 1. pecan



Pecan的介绍：

　　 Pecan是一个路由对象分发的oython web框架。本质上可以将url通过分割为每一部分，然后对每一部分查找对应处理该URL部分的处理类，处理后，继续交给后面部分的URL处理，直到所有URL部分都被处理后，调用最后分割的URL对应的处理函数处理。

本文以Xshall为主在其进行操作

Pecan的安装

ecan的安装

![img](https://ask.qcloudimg.com/http-save/yehe-3043586/zy1dw2cuap.png?imageView2/2/w/1620)

创建项目

![img](https://ask.qcloudimg.com/http-save/yehe-3043586/0a3rx0v3rv.png?imageView2/2/w/1620)

项目创建好之后目录结构如下

![img](https://ask.qcloudimg.com/http-save/yehe-3043586/7mg57clfe7.png?imageView2/2/w/1620)

![img](https://ask.qcloudimg.com/http-save/yehe-3043586/g4w3ua0mrh.png?imageView2/2/w/1620)

app.py：一般包含了Pecan应用的入口，包含初始化代码。

Config.py ： 包含Pecan的应用配置，会被 app.py使用。

Controllersl ： 这个目录包含所有的控制器，也就是API具体逻辑的地方 。

Cotrollers/root.py ： 这个包含根路径对应的控制器。

Controllers/v1/ 这个目录放的是版本的API的。

Public : 文件夹存放一些Web应用所需的Image，Css或者JavaScript。

setup.py和setup.cfg用于Web应用的安装部署。

templates：存储Html或者Json的末班文件。

tests：存放测试用例。

参考文档：https://cloud.tencent.com/developer/article/1333878



## 2. wsme

### 2.1 用WSME来做什么？

上面两节已经说明了Pecan可以比较好的处理HTTP请求中的参数以及控制HTTP返回值。那么为什么我们还需要WSME呢？因为Pecan在做下面这个事情的时候比较麻烦：**请求参数和响应内容的类型检查**（英文简称就是**typing**）。当然，做是可以做的，不过你需要自己访问pecan.request和pecan.response，然后检查指定的值的类型。WSME就是为解决这个问题而生的，而且适用场景就是RESTful API。

### 2.2  WSME简介

WSME的全称是**Web Service Made Easy**，是专门用于实现REST服务的typing库，让你不需要直接操作请求和响应，而且刚好和Pecan结合得非常好，所以OpenStack的很多项目都使用了Pecan + WSME的组合来实现API（好吧，我看过的项目，用了Pecan的都用了WSME）。WSME的理念是：在大部分情况下，Web服务的输入和输出对数据类型的要求都是严格的。所以它就专门解决了这个事情，然后把其他事情都交给其他框架去实现。因此，一般WSME都是和其他框架配合使用的，支持Pecan、Flask等。WSME的文档地址是[http://wsme.readthedocs.org/en/latest/index.html](https://link.segmentfault.com/?url=http%3A%2F%2Fwsme.readthedocs.org%2Fen%2Flatest%2Findex.html)。

### 2.3 WSME的使用

用了WSME后的好处是什么呢？WSME会自动帮你检查HTTP请求和响应中的数据是否符合预先设定好的要求。WSME的主要方式是通过装饰器来控制controller方法的输入和输出。WSME中主要使用两个控制器：

- **@signature**: 这个装饰器用来描述一个函数的输入和输出。
- **@wsexpose**: 这个装饰器包含@signature的功能，同时会把函数的路由信息暴露给Web框架，效果就像Pecan的expose装饰器。

这里我们结合Pecan来讲解WSME的使用。先来看一个原始类型的例子：

```
from wsmeext.pecan import wsexpose

class RootController(rest.RestController):
    _custom_actions = {
        'test': ['GET'],
    }

    @wsexpose(int, int)
    def test(self, number):
        return number
```

如果不提供参数，访问会失败：

```
$ curl http://localhost:8080/test
{"debuginfo": null, "faultcode": "Client", "faultstring": "Missing argument: \"number\""}% 
```

如果提供的参数不是整型，访问也会失败：

```
$ curl http://localhost:8080/test\?number\=a
{"debuginfo": null, "faultcode": "Client", "faultstring": "Invalid input for field/attribute number. Value: 'a'. unable to convert to int"}% 
```

上面这些错误信息都是由WSME框架直接返回的，还没有执行到你写的方法。如果请求正确，那么会是这样的：

```
$ curl -v http://localhost:8080/test\?number\=1
* Hostname was NOT found in DNS cache
*   Trying 127.0.0.1...
* Connected to localhost (127.0.0.1) port 8080 (#0)
> GET /test?number=1 HTTP/1.1
> User-Agent: curl/7.38.0
> Host: localhost:8080
> Accept: */*
>
* HTTP 1.0, assume close after body
< HTTP/1.0 200 OK
< Date: Wed, 16 Sep 2015 15:06:35 GMT
< Server: WSGIServer/0.1 Python/2.7.9
< Content-Length: 1
< Content-Type: application/json; charset=UTF-8
<
* Closing connection 0
1% 
```

请注意返回的content-type,这里返回JSON是因为我们使用的`wsexpose`设置的返回类型是XML和JSON，并且JSON是默认值。上面这个例子就是WSME最简单的应用了。

那么现在有下面这些问题需要思考一下：

- 如果想用POST的方式来传递参数，要怎么做呢？提示：要阅读WSME中@signature装饰器的文档。
- 如果我希望使用*/test/1*这种方式来传递参数要怎么做呢？提示：要阅读Pecan文档中关于路由的部分。
- WSME中支持对哪些类型的检查呢？WSME支持整型、浮点型、字符串、布尔型、日期时间等，甚至还支持用户自定义类型。提示：要阅读WSME文档中关于类型的部分。
- WSME支持数组类型么？支持。

上面的问题其实也是很多人使用WSME的时候经常问的问题。我们将在下一篇文章中使用Pecan + WSME来继续开发我们的demo，并且用代码来回答上面所有的问题。



参考链接：https://segmentfault.com/a/1190000003810294





## 3.用pecan和wsme的案例demo

### 3.1设计REST API

要开发REST API服务，我们首先需要设计一下这个服务。设计包括要实现的功能，以及接口的具体规范。我们这里要实现的是一个简单的用户管理接口，包括增删改查等功能。如果读者对REST API不熟悉，可以先从[Wiki页面](https://link.segmentfault.com/?url=https%3A%2F%2Fen.wikipedia.org%2Fwiki%2FRepresentational_state_transfer)了解一下。

另外，为了方便大家阅读和理解，本系列的代码会放在github上，[diabloneo/webdemo](https://link.segmentfault.com/?url=https%3A%2F%2Fgithub.com%2Fdiabloneo%2Fwebdemo)。

### 3.2Version of REST API

在OpenStack的项目中，都是在URL中表明这个API的版本号的，比如Keystone的API会有**/v2.0**和**/v3**的前缀，表明两个不同版本的API；Magnum项目目前的API则为**v1**版本。因为我们的webdemo项目才刚刚开始，所以我们也把我们的API版本设置为**v1**，下文会说明怎么实现这个version号的设置。

### 3.3REST API of Users

我们将要设计一个管理用户的API，这个和Keystone的用户管理的API差不多，这里先列出每个API的形式，以及简要的内容说明。这里我们会把上面提到的version号也加入到URL path中，让读者能更容易联系起来。

> **GET /v1/users** 获取所有用户的列表。
>
> **POST /v1/users** 创建一个用户
>
> **GET /v1/users/** 获取一个特定用户的详细信息。
>
> **PUT /v1/users/** 修改一个用户的详细信息。
>
> **DELETE /v1/users/** 删除一个用户。

这些就是我们要实现的用户管理的API了。其中，****表示使用一个UUID字符串，这个是OpenStack中最经常被用来作为各种资源ID的形式，如下所示：

```
In [5]: import uuid
In [6]: print uuid.uuid4()
adb92482-baab-4832-84bc-f842f3eabd66
In [7]: print uuid.uuid4().hex
29520c88de6b4c76ae8deb48db0a71e7
```

因为是个demo，所以我们设置一个用户包含的信息会比较简单，只包含name和age。

### 3.4使用Pecan搭建API服务的框架

接下来就要开始编码工作了。首先要把整个服务的框架搭建起来。我们会在[软件包管理](http://segmentfault.com/a/1190000002940724)这篇文件中的代码基础上继续我们的demo（所有这些代码在github的仓库里都能看到）。

### 3.5代码目录结构

一般来说，OpenStack项目中，使用Pecan来开发API服务时，都会在代码目录下有一个专门的API目录，用来保存API相关的代码。比如Magnum项目的*magnum/api*，或者Ceilometer项目的*ceilometer/api*等。我们的代码也遵守这个规范，让我们直接来看下我们的代码目录结构（#后面的表示注释）：

```
➜ ~/programming/python/webdemo/webdemo/api git:(master) ✗ $ tree .
.
├── app.py           # 这个文件存放WSGI application的入口
├── config.py        # 这个文件存放Pecan的配置
├── controllers/     # 这个目录用来存放Pecan控制器的代码
├── hooks.py         # 这个文件存放Pecan的hooks代码（本文中用不到）
└── __init__.py
```

这个在[API服务(3)](http://segmentfault.com/a/1190000003810294)这篇文章中已经说明过了。

### 3.6先让我们的服务跑起来

为了后面更好的开发，我们需要先让我们的服务在本地跑起来，这样可以方便自己做测试，看到代码的效果。不过要做到这点，还是有些复杂的。

### 3.7必要的代码

首先，先创建config.py文件的内容：

```
app = {
    'root': 'webdemo.api.controllers.root.RootController',
    'modules': ['webdemo.api'],
    'debug': False,
}
```

就是包含了Pecan的最基本配置，其中指定了root controller的位置。然后看下app.py文件的内容，主要就是读取config.py中的配置，然后创建一个WSGI application：

```
import pecan

from webdemo.api import config as api_config


def get_pecan_config():
    filename = api_config.__file__.replace('.pyc', '.py')
    return pecan.configuration.conf_from_file(filename)


def setup_app():
    config = get_pecan_config()

    app_conf = dict(config.app)
    app = pecan.make_app(
        app_conf.pop('root'),
        logging=getattr(config, 'logging', {}),
        **app_conf
    )

    return app
```

然后，我们至少还需要实现一下root controller，也就是*webdemo/api/controllers/root.py*这个文件中的`RootController`类：

```
from pecan import rest
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan


class RootController(rest.RestController):

    @wsme_pecan.wsexpose(wtypes.text)
    def get(self):
        return "webdemo"
```

### 3.8本地测试服务器

为了继续开放的方便，我们要先创建一个Python脚本，可以启动一个单进程的API服务。这个脚本会放在*webdemo/cmd/*目录下，名称是**api.py**（这目录和脚本名称也是惯例），来看看我们的api.py吧：

```
from wsgiref import simple_server

from webdemo.api import app


def main():
    host = '0.0.0.0'
    port = 8080

    application = app.setup_app()
    srv = simple_server.make_server(host, port, application)

    srv.serve_forever()


if __name__ == '__main__':
    main()
```

### 3.9运行测试服务器的环境

要运行这个测试服务器，首先需要安装必要的包，并且设置正确的路径。在后面的文章中，我们将会知道，这个可以通过**tox**这个工具来实现。现在，我们先做个简单版本的，就是手动创建这个运行环境。

首先，完善一下**requirements.txt**这个文件，包含我们需要的包：

```
pbr<2.0,>=0.11
pecan
WSME
```

然后，我们手动创建一个virtualenv环境，并且安装requirements.txt中要求的包：

```
➜ ~/programming/python/webdemo git:(master) ✗ $ virtualenv .venv
New python executable in .venv/bin/python
Installing setuptools, pip, wheel...done.
➜ ~/programming/python/webdemo git:(master) ✗ $ source .venv/bin/activate
(.venv)➜ ~/programming/python/webdemo git:(master) ✗ $ pip install -r requirement.txt
...
Successfully installed Mako-1.0.3 MarkupSafe-0.23 WSME-0.8.0 WebOb-1.5.1 WebTest-2.0.20 beautifulsoup4-4.4.1 logutils-0.3.3 netaddr-0.7.18 pbr-1.8.1 pecan-1.0.3 pytz-2015.7 simplegeneric-0.8.1 singledispatch-3.4.0.3 six-1.10.0 waitress-0.8.10
```

### 3.10启动我们的服务

启动服务需要技巧，因为我们的webdemo还没有安装到系统的Python路径中，也不在上面创建virtualenv环境中，所以我们需要通过指定**PYTHONPATH**这个环境变量来为Python程序增加库的查找路径：

```
(.venv)➜ ~/programming/python/webdemo git:(master) ✗ $ PYTHONPATH=. python webdemo/cmd/api.py
```

现在测试服务器已经起来了，可以通过浏览器访问*[http://localhost](https://link.segmentfault.com/?url=http%3A%2F%2Flocalhost):8080/* 这个地址来查看结果。（你可能会发现，返回的是XML格式的结果，而我们想要的是JSON格式的。这个是WSME的问题，我们后面再来处理）。

到这里，我们的REST API服务的框架已经搭建完成，并且测试服务器也跑起来了。

###  3.11用户管理API的实现

现在我们来实现我们在第一章设计的API。这里先说明一下：**我们会直接使用Pecan的RestController来实现REST API，这样可以不用为每个接口指定接受的method**。

### 3.12让API返回JSON格式的数据

现在，所有的OpenStack项目的REST API的返回格式都是使用JSON标准，所以我们也要这么做。那么有什么办法能够让WSME框架返回JSON数据呢？可以通过设置`wsmeext.pecan.wsexpose()`的*rest_content_types*参数来是先。这里，我们借鉴一段Magnum项目中的代码，把这段代码存放在文件*webdemo/api/expose.py*中：

```
import wsmeext.pecan as wsme_pecan


def expose(*args, **kwargs):
    """Ensure that only JSON, and not XML, is supported."""
    if 'rest_content_types' not in kwargs:
        kwargs['rest_content_types'] = ('json',)

    return wsme_pecan.wsexpose(*args, **kwargs)
```

这样我们就封装了自己的`expose`装饰器，每次都会设置响应的content-type为JSON。上面的root controller代码也就可以修改为：

```
from pecan import rest
from wsme import types as wtypes

from webdemo.api import expose


class RootController(rest.RestController):

    @expose.expose(wtypes.text)
    def get(self):
        return "webdemo"
```

再次运行我们的测试服务器，就可以返现返回值为JSON格式了。

### 3.13实现 GET /v1

这个其实就是实现v1这个版本的API的路径前缀。在Pecan的帮助下，我们很容易实现这个，只要按照如下两步做即可：

- 先实现v1这个controller
- 把v1 controller加入到root controller中

按照OpenStack项目的规范，我们会先建立一个*webdemo/api/controllers/v1/*目录，然后将v1 controller放在这个目录下的一个文件中，假设我们就放在*v1/controller.py*文件中，效果如下:

```
from pecan import rest
from wsme import types as wtypes

from webdemo.api import expose


class V1Controller(rest.RestController):

    @expose.expose(wtypes.text)
    def get(self):
        return 'webdemo v1controller'
```

然后把这个controller加入到root controller中：

```
...
from webdemo.api.controllers.v1 import controller as v1_controller
from webdemo.api import expose


class RootController(rest.RestController):
    v1 = v1_controller.V1Controller()

    @expose.expose(wtypes.text)
    def get(self):
        return "webdemo"
```

此时，你访问[http://localhost](https://link.segmentfault.com/?url=http%3A%2F%2Flocalhost):8080/v1就可以看到结果了。

### 3.14实现 GET /v1/users

### 3.15添加users controller

这个API就是返回所有的用户信息，功能很简单。首先要添加users controller到上面的v1 controller中。为了不影响阅读体验，这里就不贴代码了，请看github上的示例代码。

### 3.16使用WSME来规范API的响应值

上篇文章中，我们已经提到了WSME可以用来规范API的请求和响应的值，这里我们就要用上它。首先，我们要参考OpenStack的惯例来设计这个API的返回值：

```
{
  "users": [
    {
      "name": "Alice",
      "age": 30
    },
    {
      "name": "Bob",
      "age": 40
    }
  ]
}
```

其中*users*是一个列表，列表中的每个元素都是一个user。那么，我们要如何使用WSME来规范我们的响应值呢？**答案就是使用WSME的自定义类型**。我们可以利用WSME的类型功能定义出一个user类型，然后再定义一个user的列表类型。最后，我们就可以使用上面的expose方法来规定这个API返回的是一个user的列表类型。

#### 定义user类型和user列表类型

这里我们需要用到WSME的Complex types的功能，请先看一下文档[Types](https://link.segmentfault.com/?url=http%3A%2F%2Fwsme.readthedocs.org%2Fen%2Flatest%2Ftypes.html)。简单说，就是我们可以把WSME的基本类型组合成一个复杂的类型。我们的类型需要继承自*wsme.types.Base*这个类。因为我们在本文只会实现一个user相关的API，所以这里我们把所有的代码都放在*webdemo/api/controllers/v1/users.py*文件中。来看下和user类型定义相关的部分：

```
from wsme import types as wtypes


class User(wtypes.Base):
    name = wtypes.text
    age = int


class Users(wtypes.Base):
    users = [User]
```

这里我们定义了`class User`，表示一个用户信息，包含两个字段，name是一个文本，age是一个整型。`class Users`表示一组用户信息，包含一个字段users，是一个列表，列表的元素是上面定义的`class User`。完成这些定义后，我们就使用WSME来检查我们的API是否返回了合格的值；另一方面，只要我们的API返回了这些类型，那么就能通过WSME的检查。我们先来完成利用WSME来检查API返回值的代码：

```
class UsersController(rest.RestController):

    # expose方法的第一个参数表示返回值的类型
    @expose.expose(Users)
    def get(self):
        pass
```

这样就完成了API的返回值检查了。

### 3.17实现API逻辑

我们现在来完成API的逻辑部分。不过为了方便大家理解，我们直接返回一个写好的数据，就是上面贴出来的那个。

```
class UsersController(rest.RestController):

    @expose.expose(Users)
    def get(self):
        user_info_list = [
            {
                'name': 'Alice',
                'age': 30,
            },
            {
                'name': 'Bob',
                'age': 40,
            }
        ]
        users_list = [User(**user_info) for user_info in user_info_list]
        return Users(users=users_list)
```

代码中，会先根据user信息生成User实例的列表`users_list`，然后再生成Users实例。此时，重启测试服务器后，你就可以从浏览器访问[http://localhost](https://link.segmentfault.com/?url=http%3A%2F%2Flocalhost):8080/v1/users，就能看到结果了。

### 实现 POST /v1/users

这个API会接收用户上传的一个JSON格式的数据，然后打印出来（实际中一般是存到数据库之类的），要求用户上传的数据符合User类型的规范，并且返回的状态码为201。代码如下：

```
class UsersController(rest.RestController):

    @expose.expose(None, body=User, status_code=201)
    def post(self, user):
        print user
```

可以使用curl程序来测试：

```
 ~/programming/python/webdemo git:(master) ✗ $ curl -X POST http://localhost:8080/v1/users -H "Content-Type: application/json" -d '{"name": "Cook", "age": 50}' -v
*   Trying 127.0.0.1...
* Connected to localhost (127.0.0.1) port 8080 (#0)
> POST /v1/users HTTP/1.1
> Host: localhost:8080
> User-Agent: curl/7.43.0
> Accept: */*
> Content-Type: application/json
> Content-Length: 27
>
* upload completely sent off: 27 out of 27 bytes
* HTTP 1.0, assume close after body
< HTTP/1.0 201 Created
< Date: Mon, 16 Nov 2015 15:18:24 GMT
< Server: WSGIServer/0.1 Python/2.7.10
< Content-Length: 0
<
* Closing connection 0
```

同时，服务器上也会打印出：

```
127.0.0.1 - - [16/Nov/2015 23:16:28] "POST /v1/users HTTP/1.1" 201 0
<webdemo.api.controllers.v1.users.User object at 0x7f65e058d550>
```

我们用3行代码就实现了这个POST的逻辑。现在来说明一下这里的秘密。`expose`装饰器的第一个参数表示这个方法没有返回值；第三个参数表示这个API的响应状态码是201，如果不加这个参数，在没有返回值的情况下，默认会返回204。第二个参数要说明一下，这里用的是`body=User`，你也可以直接写`User`。使用`body=User`这种形式，你可以直接发送符合User规范的JSON字符串；如果是用`expose(None, User, status_code=201)`那么你需要发送下面这样的数据：

```
{ "user": {"name": "Cook", "age": 50} }
```

你可以自己测试一下区别。要更多的了解本节提到的expose参数，请参考WSM文档[Functions](https://link.segmentfault.com/?url=http%3A%2F%2Fwsme.readthedocs.org%2Fen%2Flatest%2Ffunctions.html)。

最后，你接收到一个创建用户请求时，一般会为这个用户分配一个id。本文前面已经提到了OpenStack项目中一般使用UUID。你可以修改一下上面的逻辑，为每个用户分配一个UUID。

### 实现 GET /v1/users/<UUID>

要实现这个API，需要两个步骤：

1. 在UsersController中解析出<UUID>的部分，然后把请求传递给这个一个新的UserController。从命名可以看出，UsersController是针对多个用户的，UserController是针对一个用户的。
2. 在UserController中实现`get()`方法。

### 使用_lookup()方法

Pecan的`_lookup()`方法是controller中的一个特殊方法，Pecan会在特定的时候调用这个方法来实现更灵活的URL路由。Pecan还支持用户实现`_default()`和`_route()`方法。这些方法的具体说明，请阅读Pecan的文档：[routing](https://link.segmentfault.com/?url=https%3A%2F%2Fpecan.readthedocs.org%2Fen%2Flatest%2Frouting.html)。

我们这里只用到`_lookup()`方法，这个方法会在controller中没有其他方法可以执行且没有`_default()`方法的时候执行。比如上面的UsersController中，没有定义*/v1/users/*如何处理，它只能返回404；如果你定义了`_lookup()`方法，那么它就会调用该方法。

`_lookup()`方法需要返回一个元组，元组的第一个元素是下一个controller的实例，第二个元素是URL path中剩余的部分。

在这里，我们就需要在`_lookup()`方法中解析出UUID的部分并传递给新的controller作为新的参数，并且返回剩余的URL path。来看下代码：

```
class UserController(rest.RestController):

    def __init__(self, user_id):
        self.user_id = user_id


class UsersController(rest.RestController):

    @pecan.expose()
    def _lookup(self, user_id, *remainder):
        return UserController(user_id), remainder
```

`_lookup()`方法的形式为`_lookup(self, user_id, *remainder)`，意思就是会把/v1/users/<UUID>中的<UUID>部分作为user_id这个参数，剩余的按照**"/"**分割为一个数组参数（这里remainder为空）。然后，`_lookup()`方法里会初始化一个UserController实例，使用user_id作为初始化参数。这么做之后，这个初始化的控制器就能知道是要查找哪个用户了。然后这个控制器会被返回，作为下一个控制被调用。请求的处理流程就这么转移到UserController中了。

### 实现API逻辑

实现前，我们要先修改一下我们返回的数据，里面需要增加一个id字段。对应的User定义如下：

```
class User(wtypes.Base):
    id = wtypes.text
    name = wtypes.text
    age = int
```

现在，完整的UserController代码如下：

```
class UserController(rest.RestController):

    def __init__(self, user_id):
        self.user_id = user_id

    @expose.expose(User)
    def get(self):
        user_info = {
            'id': self.user_id,
            'name': 'Alice',
            'age': 30,
        }
        return User(**user_info)
```

使用curl来检查一下效果：

```
➜ ~/programming/python/webdemo git:(master) ✗ $ curl http://localhost:8080/v1/users/29520c88de6b4c76ae8deb48db0a71e7
{"age": 30, "id": "29520c88de6b4c76ae8deb48db0a71e7", "name": "Alice"}
```

### 定义WSME类型的技巧

你可能会有疑问：这里我们修改了User类型，增加了一个id字段，那么前面实现的*POST /v1/users*会不会失效呢？你可以自己测试一下。（答案是不会，因为这个类型里的字段都是可选的）。这里顺便讲两个技巧。

**如何设置一个字段为强制字段**

像下面这样做就可以了（你可以测试一下，改成这样后，不传递id的*POST /v1/users*会失败）：

```
class User(wtypes.Base):
    id = wtypes.wsattr(wtypes.text, mandatory=True)
    name = wtypes.text
    age = int
```

**如何检查一个可选字段的值是否存在**

检查这个值是否为None是肯定不行的，需要检查这个值是否为**wsme.Unset**。

### 实现 PUT /v1/users/<UUID>

这个和上一个API一样，不过`_lookup()`方法已经实现过了，直接添加方法到UserController中即可：

```
class UserController(rest.RestController):

    @expose.expose(User, body=User)
    def put(self, user):
        user_info = {
            'id': self.user_id,
            'name': user.name,
            'age': user.age + 1,
        }
        return User(**user_info)
```

通过curl来测试：

```
➜ ~/programming/python/webdemo git:(master) ✗ $ curl -X PUT http://localhost:8080/v1/users/29520c88de6b4c76ae8deb48db0a71e7 -H "Content-Type: application/json" -d '{"name": "Cook", "age": 50}'
{"age": 51, "id": "29520c88de6b4c76ae8deb48db0a71e7", "name": "Cook"}% 
```

### 实现 DELETE /v1/users/<UUID>

同上，没有什么新的内容：

```
class UserController(rest.RestController):

    @expose.expose()
    def delete(self):
        print 'Delete user_id: %s' % self.user_id
```

## 4.总结

到此为止，我们已经完成了我们的API服务了，虽然没有实际的逻辑，但是本文搭建起来的框架也是OpenStack中API服务的一个常用框架，很多大项目的API服务代码都和我们的webdemo长得差不多。最后再说一下，本文的代码在github上托管着：[diabloneo/webdemo](https://link.segmentfault.com/?url=https%3A%2F%2Fgithub.com%2Fdiabloneo%2Fwebdemo)。

现在我们已经了解了包管理和API服务了，那么接下来就要开始数据库相关的操作了。大部分OpenStack的项目都是使用非常著名的sqlalchemy库来实现数据库操作的，本系列接下来的文章就是要来说明数据库的相关知识和应用。

参考链接：https://segmentfault.com/a/1190000004004179

