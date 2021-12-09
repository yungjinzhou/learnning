## pecan

### 安装

pip install pecan



### 简单示例

实现Hello World
我们先All in One把代码放到一个文件里。
新建一个app.py文件，代码如下：



```
# /usr/bin/env pytho
# coding=utf-8
from wsgiref import simple_server
import pecan

class RootController(object):
	@pecan.expose()
	def index(self):
    	return "Hello World"



app = pecan.Pecan(RootController())
if __name__ == "__main__":
    sev = simple_server.make_server("127.0.0.1", 5000, app)
    sev.serve_forever()
```







### pecan路由顺序

结果说明
我们访问/book/it和/book/food Pecan是如何处理的呢？

第一步
我们知道这两个路由以book开头，会交给BookController去处理

第二步
BookController开始处理，查找有没有可用_default方法，加入notfound_handlers，发现有，我们的notfound_handlers=[BookController()._default]

第三步
查找有没有可用的_lookup方法，加入notfound_handlers，发现有，我们的notfound_handlers=[BookController()._default, [BookController()._lookup]

第四步
查找BookController同名的属性处理，发现没有，抛出PecanNotFound

第五步
接收到PecanNotFound查看一下notfound_handlers里有没有对象，发现有。接着处理

第六步
前面也提到过，会从notfound_handlers队尾获取一个处理方法，也就是BookController()._lookup（后入先出）。
处理/book/it，也就是BookController()._lookup(“it”)
处理/book/food，也就是BookController()._lookup(“food”)
当是it时，发现_lookup返回了一个两个元素的数组，校验，符合返回要求，把返回的第一个元素作为Controller继续处理。再从第一步开始走。不再赘述。
当food时，发现_lookup没有返回，不符合返回要求，交给notfound_handlers继续处理。注意：只有_lookup返回不合法时，会继续交给notfound_handlers，如果是_default返回不合法将直接报404！

第七步
当是food时，_lookup没处理成功，发现notfound_handlers，还能pop出处理对象，就接着交给_default处理，所以页面显示“This is Book default”。

pecan路由

### expose

pecan默认采用`expose`进行路由的绑定，将需要路由相应控制器类的方法都经过`expose`装饰器装饰，则pecan可以请http请求路径找到对应的处理方法。不同使用方法会有不同的效果：

- `@expose()`, 被装饰的方法需要返回一个字符串，表示HTML响应的body
- `@expose(html_template_name)`，被装饰的方法返回一个字典，字典的key可以在html模板中使用`${key}`的方式引用
- `@expose(route='some-path')`，被装饰方法响应`/some-path`请求
- `@expose(generic=True)`，实现一个请求路径，根据请求方法进行覆盖



### pecan流程分析

参考链接：https://blog.csdn.net/ARPOSPF/article/details/113618174





```
# get measures路径：/v1/metrics/sdfdsfsdfidsf/measures?...



    def _handle_custom_action(self, method, remainder, request=None):
        if request is None:
            self._raise_method_deprecation_warning(self._handle_custom_action)

        remainder = [r for r in remainder if r]
        if remainder:
            if method in ('put', 'delete'):
                # For PUT and DELETE, additional arguments are supplied, e.g.,
                # DELETE /foo/XYZ
                method_name = remainder[0]
                remainder = remainder[1:]
            else:
                method_name = remainder[-1]
                remainder = remainder[:-1]
            if method.upper() in self._custom_actions.get(method_name, []):
                controller = self._find_controller(
                    '%s_%s' % (method, method_name),
                    method_name
                )
                if controller:
                    return controller, remainder

```





