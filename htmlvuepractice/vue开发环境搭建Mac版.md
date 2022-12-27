

# vue开发环境搭建Mac版

[![img](https://p3-passport.byteimg.com/img/user-avatar/95ad21db2447443e1930ae5cbfc9ddcb~100x100.awebp)](https://juejin.cn/user/3412518340662414)

[葱头来过![lv-3](https://lf3-cdn-tos.bytescm.com/obj/static/xitu_juejin_web/img/lv-3.7938ebc.png)](https://juejin.cn/user/3412518340662414)

2021年11月03日 16:18 · 阅读 386

![vue开发环境搭建Mac版](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/5ab0b24fea3545dcb5e5e1c59def8e9f~tplv-k3u1fbpfcp-zoom-crop-mark:3024:3024:3024:1702.awebp?)

如果刚接触vue，mac系统，不妨留下一看

以下是mac开发中涉及的工具和软件

![img](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/f33744b9d758450281957a9e991db0a5~tplv-k3u1fbpfcp-zoom-in-crop-mark:4536:0:0:0.awebp?)

本人使用的各个工具的版本为：
Homebrew 1.2.4
node.js v6.11.1
npm 5.0.3
webpack 3.2.0
Vue 2.8.2

1、安装brew
打开终端运行以下命令：

```bash
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
复制代码
```

安装完成后查看版本信息

```
brew -v
复制代码
```

2.安装node.js

下载地址：[nodejs.org/en/download…](https://link.juejin.cn/?target=https%3A%2F%2Fnodejs.org%2Fen%2Fdownload%2F)

安装后查看版本信息

```
node -v
复制代码
```

3.获得node安装目录访问权限

```bash
sudo chmod -R 777 /usr/local/lib/node_modules/
复制代码
```

4.安装淘宝镜像

```ini
npm install -g cnpm --registry=https://registry.npm.taobao.org
复制代码
```

5.安装webback

```
cnpm install webpack -g
复制代码
```

6.安装vue脚手架

```
cnpm install vue-cli -g
复制代码
```

7.找一个存放项目的目录，根据模板创建项目

```csharp
vue init webpack-simple 工程名字<工程名字不能用中文>
如下
vue init webpack-simple demo1
复制代码
```

碰到的提示可以直接回车默认

8.进入工程，安装依赖

```
cnpm instal
复制代码
```

9.安装路由模块和网络请求模块

```css
cnpm install vue-router vue-resource --save
复制代码
```

10.启动项目

```arduino
npm run dev
复制代码
```

11.结语



参考文档：https://juejin.cn/post/7026255032001495077