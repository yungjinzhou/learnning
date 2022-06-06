

##### libguest使用

centos-x86_64

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

hg-x86_64

```
yum install -y pcre2-devel  augeas augeas-devel file-libs file-devel  jansson jansson-devel libcap libcap-devel hivex hivex-devel  supermin5 supermin5-devel supermin ocaml ocaml-findlib-devel  ocaml-findlib  ocaml-hivex.x86_64 ocaml-hivex-devel.x86_64 erlang-erl_interface.x86_64 gperf ncurses ncurses-devel 
rm -rf  /usr/bin/supermin
ln -s /usr/bin/supermin5 /usr/bin/supermin

运行 ./run virt-df -d instance-uuid




```



arm64







