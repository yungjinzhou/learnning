django项目，用python   构建rpm包







环境：python3.6.8      centos7

依赖：在服务器上安装

yum -y install rpmdevtools

yum -y install rpm-build



rpmdev-setuptree

生成rpm需要的环境，在/root/目录（/home）下生成rpmbuild目录，目录下各个文件夹解释参考



| 默认位置                 | 宏代码         | 名称              | 用途                                              |
| ------------------------ | -------------- | ----------------- | ------------------------------------------------- |
| /root/rpmbuild/SPECS     | %_specdir      | Spec 文件目录     | 保存 RPM 包配置（.spec）文件                      |
| /root/rpmbuild/SOURCES   | %_sourcedir    | 源代码目录        | 保存源码包（如 .tar 包、tar.gz）和所有 patch 补丁 |
| /root/rpmbuild/BUILD     | %_builddir     | 构建目录          | 源码包被解压至此，并在该目录的子目录完成编译      |
| /root/rpmbuild/BUILDROOT | %_buildrootdir | 最终安装目录      | 保存 %install 阶段安装的文件                      |
| /root/rpmbuild/RPMS      | %_rpmdir       | 标准 RPM 包目录   | 生成/保存二进制 RPM 包                            |
| /root/rpmbuild/SRPMS     | %_srcrpmdir    | 源代码 RPM 包目录 | 生成/保存源码 RPM 包(SRPM)                        |





创建目录：makerpmfile

目录结构

./makerpmfile/setup.py

./makerpmfile/django_project



setup.py文件内容  # django_project内都是python3文件

```
from setuptools import setup, find_packages


setup(name='test',
      version='test',    
      description='test make rpm',    
      author='author',    
      author_email='author@gmail.com',    
      url='http://author.github.io/',    
      license='GPL',
      packages=find_packages(),  # 自动发现有__init__.py的python包
      package_data = {'django_project': ['deploy/*', 'requirements.txt', 'README.txt', 'static/*', 'script/*']},  # 输入没有__init__.py的文件或文件夹，不要有中文名的文件，会报错 
      zip_file=False,
    #  data_files=[('/etc/maerd',['maerd.conf'])],  # 放在该django_project包之外的文件
)

```

具体setup函数参数解释参考：https://blog.konghy.cn/2018/04/29/setup-dot-py/





在该目录下执行python3 setup.py bdist_rpm，

（或者  python3  setup.py bdist_rpm --force-arch x86_64，具体原因看后面）

在本目录下会生成

./makerpmfile/setup.py

./makerpmfile/build/   # 新生成

./makerpmfile/dist/   # 新生成 ，有.rpm文件

./makerpmfile/django_project

./makerpmfile/django_project.egg-info





一般到这一步就完成rpm包制作了，测试在另一台机器安装，安装后，代码在/usr/lib/python3.6/site-packages/django_project/下







如果报错error: Arch dependent binaries in noarch package，是因为默认noarch架构，有冲突

方法1. 在makerpmfile/build/bdist.linux-x86_64/rpm/SPECS/django_project.spec中修改

```bash
%define _binaries_in_noarch_packages_terminate_build   0
```

rpmbuild -bs test1.spec



方法2. BuildArch:noarch这一行

然后执行rpmbuild -bs test1.spec



方法3.  python setup.py bdist_rpm --force-arch x86_64












补充spec文件

```
%define name test
%define version test
%define unmangled_version test
%define unmangled_version test
%define release 1

Summary: test make rpm 1.0
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
License: GPL
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: x86_64
Vendor: yungjinzhou <yungjinzhou@gmail.com>
Url: http://yungjinzhou.github.io/

%description
UNKNOWN

%prep
%setup -n %{name}-%{unmangled_version} -n %{name}-%{unmangled_version}

%build
python3 setup.py build

%install
python3 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
```













