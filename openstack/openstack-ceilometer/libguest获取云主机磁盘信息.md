

### libguest使用

#### centos-x86_64

```
https://libguestfs.org/guestfs-building.1.html
https://download.libguestfs.org/1.40-stable/
下载源码包libguestfs-1.40.2.tar.gz
解压后进入目录
./configure
 make
 发现缺少依赖包
 安装
 yum install -y pcre2-devel  augeas augeas-devel file-libs file-devel  jansson jansson-devel libcap libcap-devel hivex hivex-devel  supermin5 supermin5-devel supermin ocaml ocaml-findlib-devel  ocaml-findlib  ocaml-hivex.x86_64 ocaml-hivex-devel.x86_64 erlang-erl_interface.x86_64 gperf ncurses ncurses-devel
rm -rf  /usr/bin/supermin
ln -s /usr/bin/supermin5 /usr/bin/supermin
/.configure  --dis
运行 ./run virt-df -d instance-uuid





```

#### hg-x86_64

```
yum install -y pcre2-devel  augeas augeas-devel file-libs file-devel  jansson jansson-devel libcap libcap-devel hivex hivex-devel  supermin5 supermin5-devel supermin  ocaml-findlib-devel  ocaml-findlib  ocaml-hivex ocaml-hivex-devel erlang-erl_interface gperf ncurses ncurses-devel 
rm -rf  /usr/bin/supermin
ln -s /usr/bin/supermin5 /usr/bin/supermin

运行 ./run virt-df -d instance-uuid


```

#### arm64（kp机器）

```
下载源码包libguestfs-1.40.2.tar.gz
解压后进入目录
 
apt install -y gperf flex bison ncurses-dev pkg-config augeas-tools augeas-doc python-augeas libaugeas-dev libmagic-dev libjansson-dev libhivex-dev libhivex-ocaml libhivex-ocaml-dev supermin gdisk

./configure --with-default-backend="libvirt"
 make
 # export LIBGUESTFS_BACKEND=direct
 # export LIBGUESTFS_BACKEND=libvirt
 
 

```



#### arm64(uos系统)

```
apt install python3-augeas libaugeas-dev libpcre2-8-0=10.32-5


```





### 注意事项

在./configure后，make报错

```
File "daemon_config.ml", line 1:
Error: The files /usr/lib64/ocaml/hivex/hivex.cmi and daemon_config.cmi
       make inconsistent assumptions over interface Hivex
make[3]: *** [daemon_config.cmx] Error 2
```



解决办法

```
make clean
然后在/configure
make
```



