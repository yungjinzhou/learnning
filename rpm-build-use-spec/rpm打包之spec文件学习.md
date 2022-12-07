## rpm打包之spec文件学习





Source0: %{name}-%{version}.tar.gz                                               

 #定义用到的source，也就是你的源码包，可以有多个，用Source1、Source2等表示

BuildRoot: %_topdir/BUILDROOT

#这个是安装或编译时使用的“虚拟目录”，该参数非常重要，因为在执行make install的过程中，需要把软件安装到这个路径中，在打包(即%files段)的时候，依赖“虚拟目录”为“根目录”进行操作。这个参数可以不必定义，系统默认此参数为：/root/rpmbuild/BUILDROOT/%{name}-%{version}-%{release}.x86_64，后面引用可以直接使用$RPM_BUILD_ROOT。

BuildRequires: gcc,make

#编译时的包依赖

Requires: python-apscheduler >= 2.1.2-1.el7,python-daemon >= 1.6-1.el7

#软件运行依赖的软件包，也可以指定最低版本如 bash >= 1.1.1







## %files 阶段[#](https://www.cnblogs.com/michael-xiang/p/10480809.html#3874413624)

本段是文件段，主要用来说明会将 `%{buildroot}` 目录下的哪些文件和目录最终打包到rpm包里。定义软件包所包含的文件，分为三类：

- 说明文档（doc）
- 配置文件（config）
- 执行程序

还可定义文件存取权限，拥有者及组别。

这里会在虚拟根目录下进行，千万不要写绝对路径，而应用宏或变量表示相对路径。

在 `%files` 阶段的第一条命令的语法是：

```scss
Copy%defattr(文件权限,用户名,组名,目录权限) 
```

注意点：同时需要在 `%install` 中安装。

```shell
Copy%files
%defattr (-,root,root,0755)                         ← 设定默认权限
%config(noreplace) /etc/my.cnf                      ← 表明是配置文件，noplace表示替换文件
%doc %{src_dir}/Docs/ChangeLog                      ← 表明这个是文档
%attr(644, root, root) %{_mandir}/man8/mysqld.8*    ← 分别是权限，属主，属组
%attr(755, root, root) %{_sbindir}/mysqld
```

`%exclude` 列出不想打包到 rpm 中的文件。注意：如果 `%exclude` 指定的文件不存在，也会出错的。

在安装 rpm 时，会将可执行的二进制文件放在 `/usr/bin` 目录下，动态库放在 `/usr/lib` 或者 `/usr/lib64` 目录下，配置文件放在 `/etc` 目录下，并且多次安装时新的配置文件不会覆盖以前已经存在的同名配置文件。

关于 `%files` 阶段有两个特性：

1. `%{buildroot}` 里的所有文件都要明确被指定是否要被打包到 rpm里。什么意思呢？假如，`%{buildroot}` 目录下有 4 个目录 a、b、c和d，在 `%files` 里仅指定 a 和 b 要打包到 rpm 里，如果不把 c 和 d 用 `exclude` 声明是要报错的；
2. 如果声明了 `%{buildroot}` 里不存在的文件或者目录也会报错。

关于 `%doc` 宏，所有跟在这个宏后面的文件都来自 `%{_builddir}` 目录，当用户安装 rpm 时，由这个宏所指定的文件都会安装到 `/usr/share/doc/name-version/` 目录里。



### 4.总结

1. 如果一个文件在 `%files` 段没有被 `%config` 或 `%config(noreplace)` 指令配置，则执行 rpm -Uvh 时，该文件会无条件被新文件替换。
2. 无论一个文件有没有被 `%config` 或 `%config(noreplace)` 指令配置，只要改文件在本地没有被编辑过，则执行 rpm -Uvh 时，该文件会被新文件替换。
3. 一个被 `%config` 或 `%config(noreplace)` 指令配置的文件，如果被编辑过，那么在 rpm 更新时，如果新的 rpm 包中该文件没有修改，则该文件不会被新 rpm 包中的文件替换，之前做的编辑依然有效。
4. 一个被 `%config` 指令配置的文件，如果被编辑过，且新的 rpm 包中该文件有修改，则该文件会被重命名为 xx.rpmsave，新文件会替代原文件。
5. 一个被 `%config(noreplace)` 指令配置的文件，如果被编辑过，且新的 rpm 包中该文件有修改，则该文件不会被新的 rpm 包中的文件替换，之前做的编辑依然有效；但新 rpm 包中的同名文件会被重命名为 xx.rpmnew。















## 宏[#](https://www.cnblogs.com/michael-xiang/p/10480809.html#190625835)

在定义文件的安装路径时，通常会使用类似 `%_sharedstatedir` 的宏，这些宏一般会在 `/usr/lib/rpm/macros` 中定义。关于宏的语法，可以查看 [Macro syntax](https://rpm.org/user_doc/macros.html)

RPM 内建宏定义在 `/usr/lib/rpm/redhat/macros` 文件中，这些宏基本上定义了目录路径或体系结构等等；同时也包含了一组用于调试 spec 文件的宏。

所有宏都可以在 `/usr/lib/rpm/macros` 找到，附录一些常见的宏：

```ruby
%{_sysconfdir}        /etc
%{_prefix}            /usr
%{_exec_prefix}       %{_prefix}
%{_bindir}            %{_exec_prefix}/bin
%{_lib}               lib (lib64 on 64bit systems)
%{_libdir}            %{_exec_prefix}/%{_lib}
%{_libexecdir}        %{_exec_prefix}/libexec
%{_sbindir}           %{_exec_prefix}/sbin
%{_sharedstatedir}    /var/lib
%{_datadir}           %{_prefix}/share
%{_includedir}        %{_prefix}/include
%{_oldincludedir}     /usr/include
%{_infodir}           /usr/share/info
%{_mandir}            /usr/share/man
%{_localstatedir}     /var
%{_initddir}          %{_sysconfdir}/rc.d/init.d 
%{_topdir}            %{getenv:HOME}/rpmbuild
%{_builddir}          %{_topdir}/BUILD
%{_rpmdir}            %{_topdir}/RPMS
%{_sourcedir}         %{_topdir}/SOURCES
%{_specdir}           %{_topdir}/SPECS
%{_srcrpmdir}         %{_topdir}/SRPMS
%{_buildrootdir}      %{_topdir}/BUILDROOT
%{_var}               /var
%{_tmppath}           %{_var}/tmp
%{_usr}               /usr
%{_usrsrc}            %{_usr}/src
%{_docdir}            %{_datadir}/doc
%{buildroot}          %{_buildrootdir}/%{name}-%{version}-%{release}.%{_arch}
$RPM_BUILD_ROOT       %{buildroot}
```

利用 rpmbuild 构建 rpm 安装包时，通过命令 `rpm --showrc|grep prefix` 查看。

通过 `rpm --eval "%{macro}"` 来查看具体对应路径。

比如我们要查看 `%{_bindir}` 的路径，就可以使用命令 `rpm --eval "%{ _bindir}"` 来查看。

```perl
%{_topdir}            %{getenv:HOME}/rpmbuild
%{_builddir}          %{_topdir}/BUILD
%{_rpmdir}            %{_topdir}/RPMS
%{_sourcedir}         %{_topdir}/SOURCES
%{_specdir}           %{_topdir}/SPECS
%{_srcrpmdir}         %{_topdir}/SRPMS
%{_buildrootdir}      %{_topdir}/BUILDROOT

Note: On releases older than Fedora 10 (and EPEL), %{_buildrootdir} does not exist.
Build flags macros

%{_global_cflags}     -O2 -g -pipe
%{_optflags}          %{__global_cflags} -m32 -march=i386 -mtune=pentium4 # if redhat-rpm-config is installed  
```

## 变量[#](https://www.cnblogs.com/michael-xiang/p/10480809.html#3990544866)

`define` 定义的变量类似于局部变量，只在 `%{!?foo: ... }` 区间有效，不过 SPEC 并不会自动清除该变量，只有再次遇到 `%{}` 时才会清除

### define vs. global[#](https://www.cnblogs.com/michael-xiang/p/10480809.html#2279024057)

两者都可以用来进行变量定义，不过在细节上有些许差别，简单列举如下：

- `define` 用来定义宏，`global` 用来定义变量；
- 如果定义带参数的宏 (类似于函数)，必须要使用 `define`；
- 在 `%{}` 内部，必须要使用 `global` 而非 `define`；
- `define` 在使用时计算其值，而 `global` 则在定义时就计算其值；

可以简单参考如下的示例。

```perl
Copy#--- %prep之前的参数是必须要有的
Name:           mysql
Version:        5.7.17
Release:        1%{?dist}
Summary:        MySQL from FooBar.
License:        GPLv2+ and BSD

%description
It is a MySQL from FooBar.

%prep
#--- 带参数时，必须使用%define定义
%define myecho() echo %1 %2
%{!?bar: %define bar defined}

echo 1: %{bar}
%{myecho 2: %{bar}}
echo 3: %{bar}

# 如下是输出内容
#1: defined
#2: defined
#3: %{bar}
```

3 的输出是不符合预期的，可以将 `%define` 修改为 `global` 即可



global示例（openstack-ceilometer.spec）





```
# Macros for py2/py3 compatibility
%if 0%{?fedora} || 0%{?rhel} > 7
%global pyver %{python3_pkgversion}
%else
%global pyver 2
%endif

%global pyver_bin python%{pyver}
%global pyver_sitelib %python%{pyver}_sitelib
%global pyver_install %py%{pyver}_install
%global pyver_build %py%{pyver}_build
# End of macros for py2/py3 compatibility
%global _without_doc 1
%global with_doc %{!?_without_doc:1}%{?_without_doc:0}
%global pypi_name ceilometer
%{!?upstream_version: %global upstream_version %{version}%{?milestone}}

%global common_desc \
OpenStack ceilometer provides services to measure and \
collect metrics from OpenStack components.

Name:             openstack-ceilometer
# Liberty semver reset
# https://review.openstack.org/#/q/I6a35fa0dda798fad93b804d00a46af80f08d475c,n,z
Epoch:            1
Version:          12.0.0
Release:          1%{?dist}
Summary:          OpenStack measurement collection service

Group:            Applications/System
License:          ASL 2.0
URL:              https://wiki.openstack.org/wiki/Ceilometer
Source0:          https://tarballs.openstack.org/%{pypi_name}/%{pypi_name}-%{upstream_version}.tar.gz
Source1:          %{pypi_name}-dist.conf
Source2:          %{pypi_name}.logrotate
Source4:          ceilometer-rootwrap-sudoers

Source11:         %{name}-compute.service
Source12:         %{name}-central.service
Source13:         %{name}-notification.service
Source14:         %{name}-ipmi.service
Source15:         %{name}-polling.service

#
Patch0001:        0001-Add-dummy-skip-metering-database-temporarily.patch

BuildArch:        noarch
BuildRequires:    intltool
BuildRequires:    openstack-macros
BuildRequires:    python%{pyver}-cotyledon
BuildRequires:    python%{pyver}-sphinx
BuildRequires:    python%{pyver}-setuptools
BuildRequires:    python%{pyver}-pbr >= 1.10.0
BuildRequires:    git
BuildRequires:    python%{pyver}-devel
# Required to compile translation files
BuildRequires:    python%{pyver}-babel

BuildRequires:    systemd

%description
%{common_desc}

%package -n       python%{pyver}-ceilometer
Summary:          OpenStack ceilometer python libraries
%{?python_provide:%python_provide python%{pyver}-ceilometer}
Group:            Applications/System

Requires:         python%{pyver}-babel
Requires:         python%{pyver}-cachetools >= 1.1.0
Requires:         python%{pyver}-eventlet
Requires:         python%{pyver}-futurist >= 0.11.0
Requires:         python%{pyver}-cotyledon
Requires:         python%{pyver}-greenlet
Requires:         python%{pyver}-iso8601
Requires:         python%{pyver}-keystoneauth1 >= 2.1.0
Requires:         python%{pyver}-jsonpath-rw-ext
Requires:         python%{pyver}-stevedore >= 1.9.0
Requires:         python%{pyver}-pbr
Requires:         python%{pyver}-six >= 1.9.0
Requires:         python%{pyver}-tenacity >= 3.2.1

Requires:         python%{pyver}-alembic

Requires:         python%{pyver}-oslo-config >= 2:3.22.0
Requires:         python%{pyver}-netaddr
Requires:         python%{pyver}-oslo-rootwrap >= 2.0.0
Requires:         python%{pyver}-oslo-vmware >= 0.6.0
Requires:         python%{pyver}-requests >= 2.8.1

Requires:         python%{pyver}-pytz
Requires:         python%{pyver}-croniter

Requires:         python%{pyver}-werkzeug

Requires:         python%{pyver}-oslo-context
Requires:         python%{pyver}-oslo-concurrency >= 3.5.0
Requires:         python%{pyver}-oslo-i18n  >= 2.1.0
Requires:         python%{pyver}-oslo-log  >= 1.14.0
Requires:         python%{pyver}-oslo-reports >= 0.6.0
Requires:         python%{pyver}-monotonic

# Handle python2 exception
%if %{pyver} == 2
Requires:         pysnmp
Requires:         PyYAML
Requires:         python-lxml
Requires:         python-anyjson
Requires:         python-jsonpath-rw
Requires:         python-msgpack >= 0.4.0
Requires:         python-retrying
Requires:         python%{pyver}-futures
%else
Requires:         python%{pyver}-pysnmp
Requires:         python%{pyver}-PyYAML
Requires:         python%{pyver}-lxml
Requires:         python%{pyver}-anyjson
Requires:         python%{pyver}-jsonpath-rw
Requires:         python%{pyver}-msgpack >= 0.4.0
Requires:         python%{pyver}-retrying
%endif


%description -n   python%{pyver}-ceilometer
%{common_desc}

This package contains the ceilometer python library.


%package common
Summary:          Components common to all OpenStack ceilometer services
Group:            Applications/System

# Collector service has been removed but not replaced
Provides:         openstack-ceilometer-collector = %{epoch}:%{version}-%{release}
Obsoletes:        openstack-ceilometer-collector < %{epoch}:%{version}-%{release}
# api service has been removed
Obsoletes:        openstack-ceilometer-api

Requires:         python%{pyver}-ceilometer = %{epoch}:%{version}-%{release}
Requires:         python%{pyver}-oslo-messaging >= 5.12.0
Requires:         python%{pyver}-oslo-serialization >= 1.10.0
Requires:         python%{pyver}-oslo-utils >= 3.5.0
Requires:         python%{pyver}-tooz
Requires:         python%{pyver}-gnocchiclient
Requires:         python%{pyver}-os-xenapi >= 0.1.1
Requires:         python%{pyver}-novaclient >= 1:2.29.0
Requires:         python%{pyver}-keystoneclient >= 1:1.6.0
Requires:         python%{pyver}-neutronclient >= 4.2.0
Requires:         python%{pyver}-glanceclient >= 1:2.0.0
Requires:         python%{pyver}-swiftclient
Requires:         python%{pyver}-cinderclient >= 1.7.1

# Handle python2 exception
%if %{pyver} == 2
Requires:         python-posix_ipc
%else
Requires:         python%{pyver}-posix_ipc
%endif


%if 0%{?rhel} && 0%{?rhel} < 8
%{?systemd_requires}
%else
%{?systemd_ordering} # does not exist on EL7
%endif
Requires(pre):    shadow-utils

# Config file generation
BuildRequires:    python%{pyver}-os-xenapi
BuildRequires:    python%{pyver}-oslo-config >= 2:3.7.0
BuildRequires:    python%{pyver}-oslo-concurrency
BuildRequires:    python%{pyver}-oslo-log
BuildRequires:    python%{pyver}-oslo-messaging
BuildRequires:    python%{pyver}-oslo-reports
BuildRequires:    python%{pyver}-oslo-vmware >= 0.6.0
BuildRequires:    python%{pyver}-glanceclient >= 1:2.0.0
BuildRequires:    python%{pyver}-neutronclient
BuildRequires:    python%{pyver}-novaclient  >= 1:2.29.0
BuildRequires:    python%{pyver}-swiftclient
BuildRequires:    python%{pyver}-croniter
BuildRequires:    python%{pyver}-jsonpath-rw-ext
BuildRequires:    python%{pyver}-tooz
BuildRequires:    python%{pyver}-werkzeug
BuildRequires:    python%{pyver}-gnocchiclient
BuildRequires:    python%{pyver}-cinderclient >= 1.7.1

# Handle python2 exception
%if %{pyver} == 2
BuildRequires:    python-d2to1
BuildRequires:    python-jsonpath-rw
BuildRequires:    python-lxml
%else
BuildRequires:    python%{pyver}-d2to1
BuildRequires:    python%{pyver}-jsonpath-rw
BuildRequires:    python%{pyver}-lxml
%endif

%description common
%{common_desc}

This package contains components common to all OpenStack
ceilometer services.


%package compute
Summary:          OpenStack ceilometer compute agent
Group:            Applications/System

Requires:         %{name}-common = %{epoch}:%{version}-%{release}
Requires:         %{name}-polling = %{epoch}:%{version}-%{release}

%if %{pyver} == 2
Requires:         libvirt-python
%else
Requires:         python%{pyver}-libvirt
%endif


%description compute
%{common_desc}

This package contains the ceilometer agent for
running on OpenStack compute nodes.


%package central
Summary:          OpenStack ceilometer central agent
Group:            Applications/System

Requires:         %{name}-common = %{epoch}:%{version}-%{release}
Requires:         %{name}-polling = %{epoch}:%{version}-%{release}

%description central
%{common_desc}

This package contains the central ceilometer agent.


%package notification
Summary:          OpenStack ceilometer notification agent
Group:            Applications/System

Requires:         %{name}-common = %{epoch}:%{version}-%{release}

%description notification
%{common_desc}

This package contains the ceilometer notification agent
which pushes metrics to the collector service from the
various OpenStack services.


%package ipmi
Summary:          OpenStack ceilometer ipmi agent
Group:            Applications/System

Requires:         %{name}-common = %{epoch}:%{version}-%{release}
Requires:         %{name}-polling = %{epoch}:%{version}-%{release}

Requires:         ipmitool

%description ipmi
%{common_desc}

This package contains the ipmi agent to be run on OpenStack
nodes from which IPMI sensor data is to be collected directly,
by-passing Ironic's management of baremetal.


%package polling
Summary:          OpenStack ceilometer polling agent
Group:            Applications/System

Requires:         %{name}-common = %{epoch}:%{version}-%{release}

%if %{pyver} == 2
Requires:         libvirt-python
%else
Requires:         python%{pyver}-libvirt
%endif

%description polling
Ceilometer aims to deliver a unique point of contact for billing systems to
acquire all counters they need to establish customer billing, across all
current and future OpenStack components. The delivery of counters must
be tracable and auditable, the counters must be easily extensible to support
new projects, and agents doing data collections should be
independent of the overall system.

This package contains the polling service.

%package -n python%{pyver}-ceilometer-tests
Summary:        Ceilometer tests
%{?python_provide:%python_provide python%{pyver}-ceilometer-tests}
Requires:       python%{pyver}-ceilometer = %{epoch}:%{version}-%{release}
Requires:       python%{pyver}-gabbi >= 1.30.0

%description -n python%{pyver}-ceilometer-tests
%{common_desc}

This package contains the Ceilometer test files.

%if 0%{?with_doc}
%package doc
Summary:          Documentation for OpenStack ceilometer
Group:            Documentation

# Required to build module documents
BuildRequires:    python%{pyver}-eventlet
BuildRequires:    python%{pyver}-openstackdocstheme
# while not strictly required, quiets the build down when building docs.
BuildRequires:    python%{pyver}-iso8601

%description      doc
%{common_desc}

This package contains documentation files for ceilometer.
%endif

%prep
%autosetup -n ceilometer-%{upstream_version} -S git

find . \( -name .gitignore -o -name .placeholder \) -delete

find ceilometer -name \*.py -exec sed -i '/\/usr\/bin\/env python/{d;q}' {} +

# TODO: Have the following handle multi line entries
sed -i '/setup_requires/d; /install_requires/d; /dependency_links/d' setup.py

# Remove the requirements file so that pbr hooks don't add it
# to distutils requires_dist config
%py_req_cleanup

%build
# Generate config file
PYTHONPATH=. oslo-config-generator-%{pyver} --config-file=etc/ceilometer/ceilometer-config-generator.conf

%{pyver_build}

# Generate i18n files
%{pyver_bin} setup.py compile_catalog -d build/lib/%{pypi_name}/locale

# Programmatically update defaults in sample config
# which is installed at /etc/ceilometer/ceilometer.conf
# TODO: Make this more robust
# Note it only edits the first occurrence, so assumes a section ordering in sample
# and also doesn't support multi-valued variables.
while read name eq value; do
  test "$name" && test "$value" || continue
  sed -i "0,/^# *$name=/{s!^# *$name=.*!#$name=$value!}" etc/ceilometer/ceilometer.conf
done < %{SOURCE1}

%install
%{pyver_install}

%if 0%{?with_doc}
# docs generation requires everything to be installed first

%{pyver_build}
# Fix hidden-file-or-dir warnings
rm -fr doc/build/html/.doctrees doc/build/html/.buildinfo

%endif

# Setup directories
install -d -m 755 %{buildroot}%{_sharedstatedir}/ceilometer
install -d -m 755 %{buildroot}%{_sharedstatedir}/ceilometer/tmp
install -d -m 750 %{buildroot}%{_localstatedir}/log/ceilometer

# Install config files
install -d -m 755 %{buildroot}%{_sysconfdir}/ceilometer
install -d -m 755 %{buildroot}%{_sysconfdir}/ceilometer/rootwrap.d
install -d -m 755 %{buildroot}%{_sysconfdir}/sudoers.d
install -d -m 755 %{buildroot}%{_sysconfdir}/sysconfig
install -d -m 755 %{buildroot}%{_sysconfdir}/ceilometer/meters.d
install -p -D -m 640 %{SOURCE1} %{buildroot}%{_datadir}/ceilometer/ceilometer-dist.conf
install -p -D -m 440 %{SOURCE4} %{buildroot}%{_sysconfdir}/sudoers.d/ceilometer
install -p -D -m 640 etc/ceilometer/ceilometer.conf %{buildroot}%{_sysconfdir}/ceilometer/ceilometer.conf
install -p -D -m 640 ceilometer/pipeline/data/pipeline.yaml %{buildroot}%{_sysconfdir}/ceilometer/pipeline.yaml
install -p -D -m 640 etc/ceilometer/polling.yaml %{buildroot}%{_sysconfdir}/ceilometer/polling.yaml
install -p -D -m 640 ceilometer/pipeline/data/event_pipeline.yaml %{buildroot}%{_sysconfdir}/ceilometer/event_pipeline.yaml
install -p -D -m 640 ceilometer/pipeline/data/event_definitions.yaml %{buildroot}%{_sysconfdir}/ceilometer/event_definitions.yaml
install -p -D -m 640 etc/ceilometer/rootwrap.conf %{buildroot}%{_sysconfdir}/ceilometer/rootwrap.conf
install -p -D -m 640 etc/ceilometer/rootwrap.d/ipmi.filters %{buildroot}/%{_sysconfdir}/ceilometer/rootwrap.d/ipmi.filters
install -p -D -m 640 ceilometer/publisher/data/gnocchi_resources.yaml %{buildroot}%{_sysconfdir}/ceilometer/gnocchi_resources.yaml
install -p -D -m 640 ceilometer/data/meters.d/meters.yaml %{buildroot}%{_sysconfdir}/ceilometer/meters.d/meters.yaml

# Install systemd units for services
install -p -D -m 644 %{SOURCE11} %{buildroot}%{_unitdir}/%{name}-compute.service
install -p -D -m 644 %{SOURCE12} %{buildroot}%{_unitdir}/%{name}-central.service
install -p -D -m 644 %{SOURCE13} %{buildroot}%{_unitdir}/%{name}-notification.service
install -p -D -m 644 %{SOURCE14} %{buildroot}%{_unitdir}/%{name}-ipmi.service
install -p -D -m 644 %{SOURCE15} %{buildroot}%{_unitdir}/%{name}-polling.service

# Install logrotate
install -p -D -m 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}

# Install i18n .mo files (.po and .pot are not required)
install -d -m 755 %{buildroot}%{_datadir}
rm -f %{buildroot}%{pyver_sitelib}/%{pypi_name}/locale/*/LC_*/%{pypi_name}*po
rm -f %{buildroot}%{pyver_sitelib}/%{pypi_name}/locale/*pot
mv %{buildroot}%{pyver_sitelib}/%{pypi_name}/locale %{buildroot}%{_datadir}/locale

# Find language files
%find_lang %{pypi_name} --all-name

# Remove unneeded in production stuff
rm -f %{buildroot}/usr/share/doc/ceilometer/README*

# Remove unused files
rm -fr %{buildroot}/usr/etc

%pre common
getent group ceilometer >/dev/null || groupadd -r ceilometer --gid 166
if ! getent passwd ceilometer >/dev/null; then
  # Id reservation request: https://bugzilla.redhat.com/923891
  useradd -u 166 -r -g ceilometer -G ceilometer,nobody -d %{_sharedstatedir}/ceilometer -s /sbin/nologin -c "OpenStack ceilometer Daemons" ceilometer
fi
exit 0

%post compute
%systemd_post %{name}-compute.service

%post notification
%systemd_post %{name}-notification.service

%post central
%systemd_post %{name}-central.service

%post ipmi
%systemd_post %{name}-alarm-ipmi.service

%post polling
%systemd_post %{name}-polling.service

%preun compute
%systemd_preun %{name}-compute.service

%preun notification
%systemd_preun %{name}-notification.service

%preun central
%systemd_preun %{name}-central.service

%preun ipmi
%systemd_preun %{name}-ipmi.service

%preun polling
%systemd_preun %{name}-polling.service

%postun compute
%systemd_postun_with_restart %{name}-compute.service

%postun notification
%systemd_postun_with_restart %{name}-notification.service

%postun central
%systemd_postun_with_restart %{name}-central.service

%postun ipmi
%systemd_postun_with_restart %{name}-ipmi.service


%postun polling
%systemd_postun_with_restart %{name}-polling.service


%files common -f %{pypi_name}.lang
%license LICENSE
%dir %{_sysconfdir}/ceilometer
%attr(-, root, ceilometer) %{_datadir}/ceilometer/ceilometer-dist.conf
%config(noreplace) %attr(-, root, ceilometer) %{_sysconfdir}/ceilometer/ceilometer.conf
%config(noreplace) %attr(-, root, ceilometer) %{_sysconfdir}/ceilometer/pipeline.yaml
%config(noreplace) %attr(-, root, ceilometer) %{_sysconfdir}/ceilometer/polling.yaml
%config(noreplace) %attr(-, root, ceilometer) %{_sysconfdir}/ceilometer/gnocchi_resources.yaml
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}

%dir %attr(0750, ceilometer, root) %{_localstatedir}/log/ceilometer

%{_bindir}/ceilometer-send-sample
%{_bindir}/ceilometer-upgrade

%defattr(-, ceilometer, ceilometer, -)
%dir %{_sharedstatedir}/ceilometer
%dir %{_sharedstatedir}/ceilometer/tmp


%files -n python%{pyver}-ceilometer
%{pyver_sitelib}/ceilometer
%{pyver_sitelib}/ceilometer-*.egg-info
%exclude %{pyver_sitelib}/ceilometer/tests

%files -n python%{pyver}-ceilometer-tests
%license LICENSE
%{pyver_sitelib}/ceilometer/tests

%if 0%{?with_doc}
%files doc
%doc doc/build/html
%endif


%files compute
%{_unitdir}/%{name}-compute.service


%files notification
%config(noreplace) %attr(-, root, ceilometer) %{_sysconfdir}/ceilometer/event_pipeline.yaml
%config(noreplace) %attr(-, root, ceilometer) %{_sysconfdir}/ceilometer/event_definitions.yaml
%dir %{_sysconfdir}/ceilometer/meters.d
%config(noreplace) %attr(-, root, ceilometer) %{_sysconfdir}/ceilometer/meters.d/meters.yaml
%{_bindir}/ceilometer-agent-notification
%{_unitdir}/%{name}-notification.service


%files central
%{_unitdir}/%{name}-central.service


%files ipmi
%config(noreplace) %attr(-, root, ceilometer) %{_sysconfdir}/ceilometer/rootwrap.conf
%config(noreplace) %attr(-, root, ceilometer) %{_sysconfdir}/ceilometer/rootwrap.d/ipmi.filters
%{_bindir}/ceilometer-rootwrap
%{_sysconfdir}/sudoers.d/ceilometer
%{_unitdir}/%{name}-ipmi.service

%files polling
%{_bindir}/ceilometer-polling
%{_unitdir}/%{name}-polling.service


%changelog
* Wed Apr 10 2019 RDO <dev@lists.rdoproject.org> 1:12.0.0-1
- Update to 12.0.0

* Fri Mar 22 2019 RDO <dev@lists.rdoproject.org> 1:12.0.0-0.1.0rc1
- Update to 12.0.0.0rc1

```













### %{?dist} 表示什么含义？[#](https://www.cnblogs.com/michael-xiang/p/10480809.html#434157306)

不加问号，如果 `dist` 有定义，那么就会用定义的值替换，否则就会保 `%{dist}`;
加问好，如果 `dist` 有定义，那么也是会用定义的值替换，否则就直接移除这个tag `%{?dist}`

举例：

```ruby
Copy$ rpm -E 'foo:%{foo}'$'\n''bar:%{?bar}'
foo:%{foo}
bar:

$ rpm -D'foo foov' -E 'foo:%{foo}'$'\n''bar:%{?bar}'
foo:foov
bar:

$ rpm -D'foo foov' -D'bar barv' -E 'foo:%{foo}'$'\n''bar:%{?bar}'
foo:foov
bar:barv
```



参考：https://www.cnblogs.com/michael-xiang/p/10480809.html







































以下为目录所对应存放文件的解释：

> - BUILD：源码解压以后放的目录
> - RPMS：制作完成后的rpm包存放目录
> - SOURCES：存放源文件，配置文件，补丁文件等放置的目录【常用】
> - SPECS：存放spec文件，作为制作rpm包的文件，即：nginx.spec……【常用】
> - SRPMS：src格式的rpm包目录
> - BuiltRoot：虚拟安装目录，即在整个install的过程中临时安装到这个目录，把这个目录当作根来用的，所以在这个目录下的文件，才是真正的目录文件。最终，Spec文件中最后有清理阶段，这个目录中的内容将被删除


Spec文件的宏定义：

> rpmbuild --showrc | grep topdir #工作车间目录：_topdir /root/rpmbuild
> -14: _builddir %{_topdir}/BUILD
> -14: _buildrootdir %{_topdir}/BUILDROOT
> -14: _rpmdir %{_topdir}/RPMS
> -14: _sourcedir %{_topdir}/SOURCES
> -14: _specdir %{_topdir}/SPECS
> -14: _srcrpmdir %{_topdir}/SRPMS
> -14: _topdir /root/rpmbuild


rpmbuild --showrc显示所有的宏，以下划线开头：

- 一个下划线：定义环境的使用情况，
- 二个下划线：通常定义的是命令，
  为什么要定义宏，因为不同的系统，命令的存放位置可能不同，所以通过宏的定义找到命令的真正存放位置



参考链接：https://blog.csdn.net/weixin_34161032/article/details/92825511?spm=1001.2101.3001.6650.1&utm_medium=distribute.pc_relevant.none-task-blog-2%7Edefault%7ECTRLIST%7ERate-1-92825511-blog-115461583.pc_relevant_aa2&depth_1-utm_source=distribute.pc_relevant.none-task-blog-2%7Edefault%7ECTRLIST%7ERate-1-92825511-blog-115461583.pc_relevant_aa2&utm_relevant_index=1







# 从rpm包提取rpm spec 的几种方法

 原创



从rpm包提取rpm spec 的几种方法
包含了源码包
先安装，然后在rpmbuild 目录直接可以查看文件
不用安装 ，使用rpm2cpio

```
rpm2cpio myrpm.src.rpm | cpio -civ '*.spec
```


1.
没有源码
使用rpmrebuild
说明：不太好，那个只是基于从rpm包获取到的信息，生成的，实际运行可能会有问题
安装rpmrebuild 的方法yum install -y rpmrebuild

参考命令

```
rpmrebuild --package --notest-install --spec-only=mysql.spec mysql57-community-release-el7-8.noarch.rpm
```



https://blog.51cto.com/rongfengliang/3128091











yum info 包名：查询执行软件包的详细信息。例如：



根据链接汇总yum常用操作命令

参考链接： http://c.biancheng.net/view/825.html















%description: 软件的详细说明

​      %define: 预定义的变量，例如定义日志路径: _logpath /var/log/weblog

​      %prep: 预备参数，通常为 %setup -q

​      %build: 编译参数 ./configure --user=nginx --group=nginx --prefix=/usr/local/nginx/……

​      %install: 安装步骤,此时需要指定安装路径，创建编译时自动生成目录，复制配置文件至所对应的目录中（这一步比较重要！）

​      %pre: 安装前需要做的任务，如：创建用户

​      %post: 安装后需要做的任务 如：自动启动的任务

​      %preun: 卸载前需要做的任务 如：停止任务

​      %postun: 卸载后需要做的任务 如：删除用户，删除/备份业务数据

​      %clean: 清除上次编译生成的临时文件，就是上文提到的虚拟目录

​      %files: 设置文件属性，包含编译文件需要生成的目录、文件以及分配所对应的权限

​      %changelog: 修改历史

​      1.3 制作开始RPM包







nodeinfo.spec

```
Name: node-info		
Version: 1.0.0	
Release: 1%{?dist}
Summary: collect node monitor info	

Group: Development	
License: GPL

Source0: /home/yang/node_info_rpm/rpm_mode/node-info-1.0.0.tar.gz	
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root


Requires: python-paramiko>=2.1.1-9.el7	

%description

%prep

%setup -n %{name}-%{version}


%build


%install
mkdir -p %{buildroot}/etc/logrotate.d/
mkdir -p %{buildroot}/usr/lib/python2.7/site-packages/
mkdir -p %{buildroot}/var/log/nodeinfo/
mkdir -p %{buildroot}/etc/nodeinfo/
mkdir -p %{buildroot}/usr/lib/systemd/system/
mkdir -p %{buildroot}/%{_bindir}/

install -m 0666 %{_builddir}/%{name}-%{version}/node-info %{buildroot}/etc/logrotate.d/
install -m 0666 %{_builddir}/%{name}-%{version}/node_info.log %{buildroot}/var/log/nodeinfo/
install -m 0666 %{_builddir}/%{name}-%{version}/node_info.py %{buildroot}/usr/lib/python2.7/site-packages/
install -m 0766 %{_builddir}/%{name}-%{version}/openstack-node-info.service %{buildroot}/usr/lib/systemd/system/
install -m 0666 %{_builddir}/%{name}-%{version}/node_info.conf %{buildroot}/etc/nodeinfo/
install -m 0777 %{_builddir}/%{name}-%{version}/check_user.sh %{buildroot}/%{_bindir}/
chmod 0777 %{buildroot}/%{_bindir}/check_user.sh
/bin/bash %{buildroot}/%{_bindir}/check_user.sh
 

%pre



%post 
systemctl daemon-reload


%postun

%clean
#rm -rf /usr/lib/systemd/system/openstack-node-info.service
#rm -rf /var/log/nodeinfo/
#rm -rf /etc/nodeinfo/
#rm -rf /etc/logrotate.d/node-info
#rm -rf /usr/lib/python2.7/site-packages/node-info.py*
#rm -rf %{_bindir}/check_user

%files
%defattr (-,root,root,0666)
%attr(777, root, root) %{_bindir}/check_user.sh
%{_sysconfdir}/logrotate.d/node-info
%dir %attr(666, nova, nova) /var/log/nodeinfo/
%attr(666, nova, nova) /var/log/nodeinfo/node_info.log
/usr/lib/systemd/system/openstack-node-info.service
#%config(noreplace) /etc/nodeinfo/node_info.conf
%attr(666, nova, nova) /etc/nodeinfo/node_info.conf
/usr/lib/python2.7/site-packages/node_info.py*

%doc

%changelog

```









nodeinfo.spec最终版

```
Name: node-info		
Version: 1.0.0	
Release: 1%{?dist}
Summary: collect node monitor info	

Group: Development	
License: GPL

Source0: /home/yang/node_info_rpm/rpm_mode/node-info-1.0.0.tar.gz	
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root


Requires: python-paramiko >= 2.1.1
Requires: python-memcached >= 1.58	
Requires: memcached >= 1.5.6	
Requires: python2-PyMySQL >= 0.9.3	

%description

%prep

%setup -n %{name}-%{version}


%build


%install
mkdir -p %{buildroot}/etc/logrotate.d/
mkdir -p %{buildroot}/usr/lib/python2.7/site-packages/
mkdir -p %{buildroot}/var/log/nodeinfo/
mkdir -p %{buildroot}/etc/nodeinfo/
mkdir -p %{buildroot}/usr/lib/systemd/system/
mkdir -p %{buildroot}/%{_bindir}/

install -m 0666 %{_builddir}/%{name}-%{version}/node-info %{buildroot}/etc/logrotate.d/
install -m 0666 %{_builddir}/%{name}-%{version}/node_info.log %{buildroot}/var/log/nodeinfo/
install -m 0666 %{_builddir}/%{name}-%{version}/node_info.py %{buildroot}/usr/lib/python2.7/site-packages/
install -m 0644 %{_builddir}/%{name}-%{version}/openstack-node-info.service %{buildroot}/usr/lib/systemd/system/
install -m 0666 %{_builddir}/%{name}-%{version}/node_info.conf %{buildroot}/etc/nodeinfo/
install -m 0777 %{_builddir}/%{name}-%{version}/check_user.sh %{buildroot}/%{_bindir}/
chmod 0777 %{buildroot}/%{_bindir}/check_user.sh
/bin/bash %{buildroot}/%{_bindir}/check_user.sh
 

%pre



%post 
systemctl daemon-reload


%postun

%clean
#rm -rf /usr/lib/systemd/system/openstack-node-info.service
#rm -rf /var/log/nodeinfo/
#rm -rf /etc/nodeinfo/
#rm -rf /etc/logrotate.d/node-info
#rm -rf /usr/lib/python2.7/site-packages/node-info.py*
#rm -rf %{_bindir}/check_user

%files
%attr(777, root, root) %{_bindir}/check_user.sh
%attr (644, root, root) %{_sysconfdir}/logrotate.d/node-info
%dir %attr(766, nova, nova) /var/log/nodeinfo/
%attr(766, nova, nova) /var/log/nodeinfo/node_info.log
%attr (644, root, root)/usr/lib/systemd/system/openstack-node-info.service
#%config(noreplace) /etc/nodeinfo/node_info.conf
%attr(666, nova, nova) /etc/nodeinfo/node_info.conf
/usr/lib/python2.7/site-packages/node_info.py*

%doc

%changelog

```







