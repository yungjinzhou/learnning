# heat源码解析









**对基础架构的编排**

对于不同的资源，Heat 都提供了对应的资源类型。比如对于VM，Heat 提供了OS::Nova::Server。OS::Nova::Server 有一些参数，比如key、image、flavor 等，这些参数可以直接指定，可以由客户在创建Stack 时提供，也可以由上下文其它的参数获得。创建一个VM的部分模板如下:

```
resources:
  server:
    type: OS::Nova::Server
    properties:
      key＿name: ｛ get＿param: key＿name ｝
      image: ｛ get＿param: image ｝
      flavor: ｛ get＿param: flavor ｝
      user＿data: ｜
       ＃！/bin/bash
       echo “10.10.10.10 testvm”＞＞ /etc/hosts
```

在上面创建VM 的例子中，我们选择从输入参数获得OS::Nova::Server 所需的值。其中利用user＿data 做了一些简单的配置。

**对软件配置和部署的编排**

Heat提供了多种资源类型来支持对于软件配置和部署的编排，如下所列:
OS::Heat::CloudConfig:VM 引导程序启动时的配置，由OS::Nova::Server 引用
OS::Heat::SoftwareConfig:描述软件配置
OS::Heat::SoftwareDeployment:执行软件部署
OS::Heat::SoftwareDeploymentGroup:对一组VM 执行软件部署
OS::Heat::SoftwareComponent:针对软件的不同生命周期部分，对应描述软件配置
OS::Heat::StructuredConfig:和OS::Heat::SoftwareConfig 类似，但是用Map 来表述配置
OS::Heat::StructuredDeployment:执行OS::Heat::StructuredConfig 对应的配置
OS::Heat::StructuredDeploymentsGroup:对一组VM 执行OS::Heat::StructuredConfig 对应的配置

其中最常用的是OS::Heat::SoftwareConfig 和OS::Heat::SoftwareDeployment。

**OS::Heat::SoftwareConfig**

下面是OS::Heat::SoftwareConfig 的用法，它指定了配置细节。

```
resources:  install＿db＿sofwareconfig
  type: OS::Heat::SoftwareConfig
  properties:
    group: script
  outputs:
   － name: result
  config: ｜
    ＃！/bin/bash －v
    yum －y install mariadb mariadb－server httpd [WordPress](https://www.ucloud.cn/yun/tag/WordPress/)
    touch /var/log/mariadb/mariadb.log
    chown mysql.mysql /var/log/mariadb/mariadb.log
    systemctl start mariadb.service
```



**OS::Heat::SoftwareDeployment**

下面是OS::Heat::SoftwareDeployment 的用法，它指定了在哪台服务器上做哪项配置。另外SofwareDeployment 也指定了以何种信号传输类型来和Heat 进行通信。

```
sw＿deployment:
type: OS::Heat::SoftwareDeployment
properties:
config: { get＿resource: install＿db＿sofwareconfig }
server: { get＿resource: server }
signal＿transport: HEAT＿SIGNAL
```



**OS::Heat::SoftwareConfig 和OS::Heat::SoftwareDeployment 执行流程**

OS::Heat::SoftwareConfig和OS::Heat::SoftwareDeployment协同工作，需要一系列Heat工具的自持。这些工具都是OpenStack的子项目。
首先，os－collect－config调用Heat API拿到对应VM的metadata。当metadata更新完毕后os－refresh－config开始工作了，它主要是运行下面目录所包含的脚本:

```
/opt/stack/os－config－refresh/pre－configure.d
/opt/stack/os－config－refresh/configure.d
/opt/stack/os－config－refresh/post－configure.d
/opt/stack/os－config－refresh/migration.d
/opt/stack/os－config－refresh/error.d
```



每个文件夹都应对了软件不同的阶段，比如预先配置阶段、配置阶段、后配置阶段和迁移阶段。如果任一阶段的脚本执行出现问题，它会运行error.d目录里的错误处理脚本。os－refresh－config 在配置阶段会调用一定预先定义的工具，比如heat－config，这样就触发了heat－config的应用，调用完heat－config后，又会调用os－apply－config。存在在heat－config或者os－apply－config里的都是一些脚本，也叫钩子。Heat对于各种不同的工具提供了不同的钩子脚本。用户也可以自己定义这样的脚本。

等一切调用完成无误后，heat－config－notify 会被调用，它用来发信号给Heat，告诉这个软件部署的工作已经完成。当Heat 收到heat－config－notify 发来的信号后，它会把OS::Heat::SoftwareConfig 对应资源的状态改为Complete。如果有任何错误发生，就会改为CREATE＿FAILED 状态。

**OS::Heat::SoftwareConfig 和OS::Heat::SoftwareDeployment 执行流程如下:**

![深度解码超实用的OpenStack Heat](.\1554185458727023821.jpg)