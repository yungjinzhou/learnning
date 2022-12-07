## 构建任务
> 以下为需要构建的模块，1表示优先级高，必须完成；2表示优先级低，有余力做一下

最终产出结果为：
  debian相关文件（debian目录下的rules、control等）、rpm相关文件（SOURCE、SPECS等），
  自动构建容器以及自动构建说明

|项目|rpm/py2|deb/py3|
|---|---|---|
|nova|1|1|
oslo-context|1|1
oslo-messaging|1|1
cinder|1|2
neutron|1|1
neutron-lib|1|1
neutron-fwaas|1|1
neutron-vpnaas|1|1
octavia|1|2
ceilometer|1|1
gnocchi|1|1
zun|1|1
python_rpc_script|1|2
mimic|1|2
horizon|1|2
libguestfs|1|1
qemu|1|1
libvirt|1|1




以下以neutron为例，进行rpm、deb包构建，最后给出自动化构建的实例，其他组件可以参考
## 构建文件下载地址:
  - deb相关依赖
      ubuntu源：http://ubuntu-cloud.archive.canonical.com/ubuntu/pool/main/
  - rpm相关依赖：
      centos源：https://vault.centos.org/centos/7/cloud/Source/openstack-stein/
      如果centos找不到对应版本的包，可以尝试从fedora中查找
      fedora源：https://archives.fedoraproject.org/pub/archive/fedora/linux/
> 注意：从官方下载的构建文件可能不满足需求我们的代码，需要自行修改

## 构建示例

  以neutron为例，说明构建过程：

### Rpm构建过程：

#### 1. 安装基础环境：
```shell
yum -y install centos-release-openstack-stein
yum -y install vim wget rpm-build
```

#### 2. 下载安装neutron.src.rpm包：
```shell
wget https://vault.centos.org/centos/7/cloud/Source/openstack-stein/openstack-neutron-14.4.2-1.el7.src.rpm
rpm -ivh openstack-neutron-14.4.2-1.el7.src.rpm
```
```
# 安装完成后，会在/root/rpmbuild目录下生成SOURCES，SPECS目录，目录结构如下：
[root@216962edbbca rpmbuild]# tree /root/rpmbuild/
/root/rpmbuild/
|-- SOURCES
|   |-- 0001-Create-executable-for-removing-patch-ports.patch
|   |-- 0002-Destroy-patch-ports-only-if-canary-flow-is-not-prese.patch
|   |-- 0003-use-plugin-utils-from-neutron-lib.patch
|   |-- conf.README
|   |-- neutron-14.4.2.tar.gz
|   |-- neutron-destroy-patch-ports.service
|   |-- neutron-dhcp-agent.service
|   |-- neutron-dist.conf
|   |-- neutron-enable-bridge-firewall.sh
|   |-- neutron-l2-agent-sysctl.conf
|   |-- neutron-l2-agent.modules
|   |-- neutron-l3-agent.service
|   |-- neutron-linuxbridge-agent.service
|   |-- neutron-linuxbridge-cleanup.service
|   |-- neutron-macvtap-agent.service
|   |-- neutron-metadata-agent.service
|   |-- neutron-metering-agent.service
|   |-- neutron-netns-cleanup.service
|   |-- neutron-openvswitch-agent.service
|   |-- neutron-ovs-cleanup.service
|   |-- neutron-rpc-server.service
|   |-- neutron-server.service
|   |-- neutron-sriov-nic-agent.service
|   |-- neutron-sudoers
|   `-- neutron.logrotate
`-- SPECS
    `-- openstack-neutron.spec
```
#### 3. 替换SOURCES目录下面的neutron源码文件neutron-14.4.2.tar.gz，将gitlab上修改后的代码打包：
```shell
tar -xcvf neutron-14.4.2.tar.gz neutron-14.4.2/*
```
#### 4.安装依赖，进行构建
```shell
[root@216962edbbca SPECS]# cd /root/rpmbuild/SPECS/
[root@216962edbbca SPECS]# rpmbuild -bb openstack-neutron.spec
error: Failed build dependencies:
        git is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        openstack-macros is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-devel is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-babel is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-keystoneauth1 >= 3.4.0 is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-keystonemiddleware is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-neutron-lib is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-novaclient is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-os-xenapi is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-oslo-cache is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-oslo-concurrency is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-oslo-config is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-oslo-db is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-oslo-log is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-oslo-messaging is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-oslo-policy is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-oslo-privsep is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-oslo-rootwrap is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-oslo-service is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-oslo-upgradecheck is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-oslo-versionedobjects is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-osprofiler >= 1.3.0 is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-ovsdbapp is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-pbr >= 4.0.0 is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-psutil >= 3.2.2 is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-pyroute2 >= 0.4.21 is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-pecan >= 1.3.2 is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-tenacity >= 4.4.0 is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python-d2to1 is needed by openstack-neutron-1:14.4.2-1.el7.noarch
        python2-weakrefmethod >= 1.0.2 is needed by openstack-neutron-1:14.4.2-1.el7.noarch
# 依赖不满足，安装相关依赖
    yum install -y git openstack-macros python2-devel python2-babel python2-keystoneauth1 \
python2-keystonemiddleware python2-neutron-lib python2-novaclient python2-os-xenapi \
python2-oslo-cache python2-oslo-concurrency python2-oslo-config python2-oslo-db python2-oslo-log \
python2-oslo-messaging python2-oslo-policy python2-oslo-privsep python2-oslo-rootwrap \
python2-oslo-service python2-oslo-upgradecheck python2-oslo-versionedobjects \
python2-osprofiler python2-ovsdbapp python2-pbr python2-psutil python2-pyroute2 \
python2-pecan python2-tenacity python-d2to1 python2-weakrefmethod
# 再执行构建
    rpmbuild  -bb openstack-neutron.spec
```
最后完成构建，生成rpm包
```shell
[root@216962edbbca noarch]# ls -ahl /root/rpmbuild/RPMS/noarch/
total 5.1M
drwxr-xr-x. 2 root root 4.0K Dec  6 08:51 .
drwxr-xr-x. 3 root root   20 Dec  6 08:48 ..
-rw-r--r--. 1 root root  22K Dec  6 08:50 openstack-neutron-14.4.2-1.el7.noarch.rpm
-rw-r--r--. 1 root root 198K Dec  6 08:50 openstack-neutron-common-14.4.2-1.el7.noarch.rpm
-rw-r--r--. 1 root root  13K Dec  6 08:50 openstack-neutron-linuxbridge-14.4.2-1.el7.noarch.rpm
-rw-r--r--. 1 root root 9.0K Dec  6 08:50 openstack-neutron-macvtap-agent-14.4.2-1.el7.noarch.rpm
-rw-r--r--. 1 root root  12K Dec  6 08:50 openstack-neutron-metering-agent-14.4.2-1.el7.noarch.rpm
-rw-r--r--. 1 root root  12K Dec  6 08:50 openstack-neutron-ml2-14.4.2-1.el7.noarch.rpm
-rw-r--r--. 1 root root  14K Dec  6 08:50 openstack-neutron-openvswitch-14.4.2-1.el7.noarch.rpm
-rw-r--r--. 1 root root 8.2K Dec  6 08:50 openstack-neutron-rpc-server-14.4.2-1.el7.noarch.rpm
-rw-r--r--. 1 root root  12K Dec  6 08:50 openstack-neutron-sriov-nic-agent-14.4.2-1.el7.noarch.rpm
-rw-r--r--. 1 root root 2.3M Dec  6 08:50 python2-neutron-14.4.2-1.el7.noarch.rpm
-rw-r--r--. 1 root root 2.5M Dec  6 08:50 python2-neutron-tests-14.4.2-1.el7.noarch.rpm
```




### Deb构建过程：
#### 1. 安装基础环境：
```shell
apt-get update
apt-get install -y software-properties-common && add-apt-repository cloud-archive:stein
apt-get update && apt-get -y dist-upgrade
apt install -y vim dpkg-dev wget
```
#### 2.下载debian构建文件：
```shell
wget http://ubuntu-cloud.archive.canonical.com/ubuntu/pool/main/n/neutron/neutron_14.4.2-0ubuntu1~cloud2.debian.tar.xz
```
#### 3.准备代码：
准备代码，放到指定目录，如下：
```
root@3ab290b0d664:~# ls -l /root/neutron-14.4.2/
total 736
-rw-rw-r--.  1 1000 1000  43851 Nov 26  2020 AUTHORS
-rw-rw-r--.  1 1000 1000    425 Nov 26  2020 CONTRIBUTING.rst
-rw-rw-r--.  1 1000 1000 588435 Nov 26  2020 ChangeLog
-rw-rw-r--.  1 1000 1000   2526 Nov 26  2020 HACKING.rst
-rw-rw-r--.  1 1000 1000  10143 Nov 26  2020 LICENSE
-rw-rw-r--.  1 1000 1000   1653 Nov 26  2020 PKG-INFO
-rw-rw-r--.  1 1000 1000    692 Nov 26  2020 README.rst
-rw-rw-r--.  1 1000 1000  30076 Nov 26  2020 TESTING.rst
drwxrwxr-x.  2 1000 1000     24 Nov 26  2020 api-ref
-rw-rw-r--.  1 1000 1000     17 Nov 26  2020 babel.cfg
drwxrwxr-x.  2 1000 1000     39 Nov 26  2020 bin
-rw-rw-r--.  1 1000 1000   1044 Nov 26  2020 bindep.txt
drwxrwxr-x.  3 1000 1000     50 Nov 26  2020 devstack
drwxrwxr-x.  3 1000 1000     60 Nov 26  2020 doc
drwxrwxr-x.  5 1000 1000    169 Nov 26  2020 etc
-rw-rw-r--.  1 1000 1000   2708 Nov 26  2020 lower-constraints.txt
drwxrwxr-x. 24 1000 1000   4096 Nov 26  2020 neutron
drwxrwxr-x.  2 1000 1000    170 Nov 26  2020 neutron.egg-info
drwxrwxr-x.  3 1000 1000    163 Nov 26  2020 playbooks
drwxrwxr-x.  4 1000 1000     77 Nov 26  2020 rally-jobs
drwxrwxr-x.  4 1000 1000     33 Nov 26  2020 releasenotes
-rw-rw-r--.  1 1000 1000   1827 Nov 26  2020 requirements.txt
drwxrwxr-x.  5 1000 1000     85 Nov 26  2020 roles
-rw-rw-r--.  1 1000 1000  14363 Nov 26  2020 setup.cfg
-rw-rw-r--.  1 1000 1000   1030 Nov 26  2020 setup.py
-rw-rw-r--.  1 1000 1000    990 Nov 26  2020 test-requirements.txt
drwxrwxr-x.  2 1000 1000   4096 Nov 26  2020 tools
-rw-rw-r--.  1 1000 1000   8104 Nov 26  2020 tox.ini
```
把debian目录解压到代码目录里：
```
tar -xvf neutron_14.4.2-0ubuntu1~cloud2.debian.tar.xz -C /root/neutron-14.4.2/
```
#### 4.安装依赖，执行构建：
```shell
cd /root/neutron-14.4.2/
root@3ab290b0d664:~/neutron-14.4.2# dpkg-buildpackage -us -uc -b
dpkg-buildpackage: info: source package neutron
dpkg-buildpackage: info: source version 2:14.4.2-0ubuntu1~cloud2
dpkg-buildpackage: info: source distribution bionic-stein
dpkg-buildpackage: info: source changed by Hemanth Nakkina <hemanth.nakkina@canonical.com>
dpkg-buildpackage: info: host architecture arm64
 dpkg-source --before-build neutron-14.4.2
dpkg-source: info: using options from neutron-14.4.2/debian/source/options: --extend-diff-ignore=^[^/]*[.]egg-info/
dpkg-source: info: applying revert-keepalived-use-no-track-default.patch
dpkg-source: info: applying skip-iptest.patch
dpkg-source: info: applying flake8-legacy.patch
dpkg-source: info: applying fix-dvr-source-mac-flows.patch
dpkg-source: info: applying 0001-Fix-deletion-of-rfp-interfaces-when-router-is-re-ena.patch
dpkg-checkbuilddeps: error: Unmet build dependencies: debhelper (>= 10~) dh-python openstack-pkg-tools (>= 85ubuntu3~) python-all python-pbr (>= 2.0.0) python-setuptools python3-all python3-pbr (>= 2.0.0) python3-setuptools crudini python3-alembic (>= 0.8.10) python3-coverage (>= 4.0) python3-ddt (>= 1.0.1) python3-debtcollector (>= 1.2.0) python3-designateclient (>= 2.7.0) python3-eventlet (>= 0.18.2) python3-fixtures (>= 3.0.0) python3-hacking (>= 0.12.0) python3-httplib2 (>= 0.9.1) python3-jinja2 (>= 2.10) python3-keystoneauth1 (>= 3.4.0) python3-keystonemiddleware (>= 4.17.0) python3-mock (>= 2.0.0) python3-netaddr (>= 0.7.18) python3-netifaces (>= 0.10.4) python3-neutron-lib (>= 1.25.0) python3-neutronclient (>= 1:6.7.0) python3-novaclient (>= 2:9.1.0) python3-openstackdocstheme (>= 1.18.1) python3-openvswitch (>= 2.8.0) python3-os-ken (>= 0.3.0) python3-os-testr (>= 1.0.0) python3-os-xenapi (>= 0.3.1) python3-oslo.cache (>= 1.26.0) python3-oslo.concurrency (>= 3.26.0) python3-oslo.config (>= 1:5.2.0) python3-oslo.context (>= 1:2.19.2) python3-oslo.db (>= 4.37.0) python3-oslo.i18n (>= 3.15.3) python3-oslo.log (>= 3.36.0) python3-oslo.messaging (>= 5.29.0) python3-oslo.middleware (>= 3.31.0) python3-oslo.policy (>= 1.30.0) python3-oslo.privsep (>= 1.32.0) python3-oslo.reports (>= 1.18.0) python3-oslo.rootwrap (>= 5.8.0) python3-oslo.serialization (>= 2.18.0) python3-oslo.service (>= 1.24.0) python3-oslo.upgradecheck (>= 0.1.0) python3-oslo.utils (>= 3.33.0) python3-oslo.versionedobjects (>= 1.35.1) python3-oslotest (>= 1:3.2.0) python3-osprofiler (>= 1.4.0) python3-ovsdbapp (>= 0.9.1) python3-paste (>= 2.0.2) python3-pastedeploy (>= 1.5.0) python3-pecan (>= 1.3.2) python3-pep8 python3-psutil (>= 3.2.2) python3-pymysql (>= 0.7.6) python3-pyroute2 (>= 0.5.3) python3-requests (>= 2.14.2) python3-routes (>= 2.3.1) python3-six (>= 1.10.0) python3-sphinx (>= 1.6.2) python3-sqlalchemy (>= 1.2.0) python3-stestr (>= 1.0.0) python3-stevedore (>= 1:1.20.0) python3-subunit (>= 1.0.0) python3-tempest (>= 1:16.1.0) python3-tenacity (>= 3.2.1) python3-testrepository (>= 0.0.18) python3-testresources (>= 2.0.0) python3-testscenarios (>= 0.4) python3-testtools (>= 2.2.0) python3-webob (>= 1:1.8.2) python3-webtest (>= 2.0.27) rename
dpkg-buildpackage: warning: build dependencies/conflicts unsatisfied; aborting
dpkg-buildpackage: warning: (Use -d flag to override.)

# 依赖不满足，安装相关依赖：
    apt install -y debhelper dh-python openstack-pkg-tools python-all python-pbr \
python-setuptools python3-all python3-pbr python3-setuptools crudini \
python3-alembic python3-coverage python3-ddt python3-debtcollector \
python3-designateclient python3-eventlet python3-fixtures python3-hacking python3-httplib2 \
python3-jinja2 python3-keystoneauth1 python3-keystonemiddleware python3-mock \
python3-netaddr python3-netifaces python3-neutron-lib python3-neutronclient \
python3-novaclient python3-openstackdocstheme python3-openvswitch python3-os-ken \
python3-os-testr  python3-os-xenapi  python3-oslo.cache  python3-oslo.concurrency \
python3-oslo.config python3-oslo.context python3-oslo.db python3-oslo.i18n python3-oslo.log \
python3-oslo.messaging  python3-oslo.middleware  python3-oslo.policy  python3-oslo.privsep \
python3-oslo.reports python3-oslo.rootwrap python3-oslo.serialization python3-oslo.service \
python3-oslo.upgradecheck python3-oslo.utils python3-oslo.versionedobjects python3-oslotest \
python3-osprofiler python3-ovsdbapp python3-paste python3-pastedeploy python3-pecan \
python3-pep8 python3-psutil python3-pymysql python3-pyroute2 python3-requests python3-routes \
python3-six python3-sphinx python3-sqlalchemy python3-stestr python3-stevedore python3-subunit \
python3-tempest python3-tenacity python3-testrepository python3-testresources python3-testscenarios \
python3-testtools python3-webob python3-webtest rename
# 再次执行构建
    dpkg-buildpackage -us -uc -b
```
最后完成构建，生成deb包：
```
root@3ab290b0d664:~# ls -alh /root
total 2.0M
drwx------.  1 root root 4.0K Dec  6 17:43 .
drwxr-xr-x.  1 root root   96 Dec  6 15:19 ..
-rw-r--r--.  1 root root 3.1K Apr  9  2018 .bashrc
-rw-r--r--.  1 root root  148 Aug 17  2015 .profile
drwxrwxr-x. 16 1000 1000 4.0K Dec  6 17:43 neutron-14.4.2
-rw-r--r--.  1 root root  53K Dec  6 17:42 neutron-common_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  26K Dec  6 17:42 neutron-dhcp-agent_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  26K Dec  6 17:42 neutron-l3-agent_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  27K Dec  6 17:42 neutron-linuxbridge-agent_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  26K Dec  6 17:42 neutron-macvtap-agent_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  26K Dec  6 17:42 neutron-metadata-agent_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  26K Dec  6 17:42 neutron-metering-agent_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  27K Dec  6 17:42 neutron-openvswitch-agent_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  23K Dec  6 17:42 neutron-plugin-ml2_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  26K Dec  6 17:42 neutron-server_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  26K Dec  6 17:42 neutron-sriov-agent_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  33K Apr  6  2021 neutron_14.4.2-0ubuntu1~cloud2.debian.tar.xz
-rw-r--r--.  1 root root  18K Dec  6 17:43 neutron_14.4.2-0ubuntu1~cloud2_arm64.buildinfo
-rw-r--r--.  1 root root 6.1K Dec  6 17:43 neutron_14.4.2-0ubuntu1~cloud2_arm64.changes
-rw-r--r--.  1 root root 1.6M Dec  6 17:43 python3-neutron_14.4.2-0ubuntu1~cloud2_all.deb
```


## 自动化构建参考
1、构建rpm自动打包容器镜像
dockerfile如下：
```dockerfile
FROM centos:7
ENV https_proxy=http://192.168.66.77:3128 \
    http_proxy=http://192.168.66.77:3128 \
    no_proxy=192.168.*.*,*.local,localhost,127.0.0.1

COPY ./openstack-macros-2021.1.5-1.noarch.rpm /home
COPY ./openstack-neutron-14.4.2-1.el7.src.rpm /home

RUN yum -y install centos-release-openstack-stein \
  && yum -y install vim wget rpm-build \
  && yum -y install git openstack-macros python2-devel python2-babel \
  python2-keystoneauth1 python2-keystonemiddleware python2-neutron-lib \
  python2-novaclient python2-os-xenapi python2-oslo-cache \
  python2-oslo-concurrency python2-oslo-config python2-oslo-db python2-oslo-log \
  python2-oslo-messaging python2-oslo-policy python2-oslo-privsep python2-oslo-rootwrap \
  python2-oslo-service python2-oslo-upgradecheck python2-oslo-versionedobjects \
  python2-osprofiler python2-ovsdbapp python2-pbr python2-psutil python2-pyroute2 \
  python2-pecan python2-tenacity python-d2to1 python2-weakrefmethod \
  && yum -y install epel-release && yum -y install python-d2to1 \
  && rpm -ivh /home/*.rpm

CMD ["/usr/bin/rpmbuild", "-bb", "/root/rpmbuild/SPECS/openstack-neutron.spec"]
```
构建容器镜像
```shell
docker build -t neutron-rpm-build .
```
自动化构建：
```shell
mkdir -p /home/neutron_build/
rm -rf /root/rpmbuild/
rpm -ihv openstack-neutron-14.4.2-1.el7.src.rpm
mv /root/rpmbuild/ /home/neutron_build/
# 替换/home/neutron_build/rpmbuild/SOURCES中的代码
tar -xcvf /home/neutron_build/neutron-14.4.2.tar.gz ${code_path}/neutron-14.4.2/*

docker ps -a -qf name=neutron-build  | xargs docker rm -f 
docker run \
  -v /home/neutron_build/rpmbuild:/root/rpmbuild:rw  \
  --name neutron-build \
  neutron-rpm-build:latest
```
```
# 容器执行完毕，生成rpm包
[root@controller neutron_build]# ls -alh /home/neutron_build/rpmbuild/RPMS/noarch/
total 5.1M
drwxr-xr-x 2 root root 4.0K Dec  7 09:46 .
drwxr-xr-x 3 root root   20 Dec  7 09:46 ..
-rw-r--r-- 1 root root  22K Dec  7 09:46 openstack-neutron-14.4.2-1.el7.noarch.rpm
-rw-r--r-- 1 root root 198K Dec  7 09:46 openstack-neutron-common-14.4.2-1.el7.noarch.rpm
-rw-r--r-- 1 root root  13K Dec  7 09:46 openstack-neutron-linuxbridge-14.4.2-1.el7.noarch.rpm
-rw-r--r-- 1 root root 9.0K Dec  7 09:46 openstack-neutron-macvtap-agent-14.4.2-1.el7.noarch.rpm
-rw-r--r-- 1 root root  12K Dec  7 09:46 openstack-neutron-metering-agent-14.4.2-1.el7.noarch.rpm
-rw-r--r-- 1 root root  12K Dec  7 09:46 openstack-neutron-ml2-14.4.2-1.el7.noarch.rpm
-rw-r--r-- 1 root root  14K Dec  7 09:46 openstack-neutron-openvswitch-14.4.2-1.el7.noarch.rpm
-rw-r--r-- 1 root root 8.2K Dec  7 09:46 openstack-neutron-rpc-server-14.4.2-1.el7.noarch.rpm
-rw-r--r-- 1 root root  12K Dec  7 09:46 openstack-neutron-sriov-nic-agent-14.4.2-1.el7.noarch.rpm
-rw-r--r-- 1 root root 2.3M Dec  7 09:46 python2-neutron-14.4.2-1.el7.noarch.rpm
-rw-r--r-- 1 root root 2.5M Dec  7 09:46 python2-neutron-tests-14.4.2-1.el7.noarch.rpm

```


2、构建deb自动打包容器镜像
```dockerfile
FROM ubuntu:18.04
ENV https_proxy=http://192.168.66.77:3128 \
    http_proxy=http://192.168.66.77:3128 \
    no_proxy=192.168.*.*,*.local,localhost,127.0.0.1


RUN apt-get update \
  && apt-get install -y software-properties-common && add-apt-repository cloud-archive:stein \
  && apt-get update && apt-get -y dist-upgrade \
  && apt install -y vim dpkg-dev wget \
  && DEBIAN_FRONTEND=noninteractive apt install -y debhelper dh-python openstack-pkg-tools python-all python-pbr \
    python-setuptools python3-all python3-pbr python3-setuptools crudini \
    python3-alembic python3-coverage python3-ddt python3-debtcollector \
    python3-designateclient python3-eventlet python3-fixtures python3-hacking python3-httplib2 \
    python3-jinja2 python3-keystoneauth1 python3-keystonemiddleware python3-mock \
    python3-netaddr python3-netifaces python3-neutron-lib python3-neutronclient \
    python3-novaclient python3-openstackdocstheme python3-openvswitch python3-os-ken \
    python3-os-testr  python3-os-xenapi  python3-oslo.cache  python3-oslo.concurrency \
    python3-oslo.config python3-oslo.context python3-oslo.db python3-oslo.i18n python3-oslo.log \
    python3-oslo.messaging  python3-oslo.middleware  python3-oslo.policy  python3-oslo.privsep \
    python3-oslo.reports python3-oslo.rootwrap python3-oslo.serialization python3-oslo.service \
    python3-oslo.upgradecheck python3-oslo.utils python3-oslo.versionedobjects python3-oslotest \
    python3-osprofiler python3-ovsdbapp python3-paste python3-pastedeploy python3-pecan \
    python3-pep8 python3-psutil python3-pymysql python3-pyroute2 python3-requests python3-routes \
    python3-six python3-sphinx python3-sqlalchemy python3-stestr python3-stevedore python3-subunit \
    python3-tempest python3-tenacity python3-testrepository python3-testresources python3-testscenarios \
    python3-testtools python3-webob python3-webtest rename

WORKDIR /home/build/neutron/
CMD ["/usr/bin/dpkg-buildpackage", "-us", "-uc", "-b"]
```
构建容器镜像：
```shell
docker build -t neutron-deb-build .
```
自动化构建：
```shell
mkdir -p /home/neutron_build/
# 将代码复制到该路径：cp -r neutron /home/neutron_build/neutron
# 解压debian文件到代码目录中
tar -xvf neutron_14.4.2-0ubuntu1~cloud2.debian.tar.xz -C /home/neutron_build/neutron/

docker ps -a -qf name=neutron-build  | xargs docker rm -f 
docker run \
  -v /home/neutron_build/:/home/build:rw  \
  --name neutron-build \
  neutron-deb-build:latest 
```
```
容器执行完，生成deb包：
[root@docker_build_aarch64 ~]# ls  -alh /home/neutron_build
total 2.0M
drwxr-xr-x.  3 root root 4.0K Dec  7 01:56 .
drwxr-xr-x.  7 root root  173 Dec  6 12:33 ..
drwxrwxr-x. 16 root root 4.0K Dec  7 01:56 neutron
-rw-r--r--.  1 root root  18K Dec  7 01:56 neutron_14.4.2-0ubuntu1~cloud2_arm64.buildinfo
-rw-r--r--.  1 root root 6.1K Dec  7 01:56 neutron_14.4.2-0ubuntu1~cloud2_arm64.changes
-rw-r--r--.  1 root root  53K Dec  7 01:56 neutron-common_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  26K Dec  7 01:56 neutron-dhcp-agent_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  26K Dec  7 01:56 neutron-l3-agent_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  27K Dec  7 01:56 neutron-linuxbridge-agent_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  26K Dec  7 01:56 neutron-macvtap-agent_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  26K Dec  7 01:56 neutron-metadata-agent_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  26K Dec  7 01:56 neutron-metering-agent_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  27K Dec  7 01:56 neutron-openvswitch-agent_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  23K Dec  7 01:56 neutron-plugin-ml2_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  26K Dec  7 01:56 neutron-server_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root  26K Dec  7 01:56 neutron-sriov-agent_14.4.2-0ubuntu1~cloud2_all.deb
-rw-r--r--.  1 root root 1.6M Dec  7 01:56 python3-neutron_14.4.2-0ubuntu1~cloud2_all.deb
```