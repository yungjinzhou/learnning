#### rootwrap

1，在/etc/sudoers.d/下新增文件ceilometer_sudoers

vim ceilometer_sudoers

```bash
ceilometer ALL=(root) NOPASSWD: /usr/bin/ceilometer-rootwrap /etc/ceilometer/rootwrap.conf *
```

2,在/etc/ceilometer/下的查看有没有rootwrap.conf文件及rootwrap.d文件夹，没有则创建：

vim rootwrap.conf:

```bash
# Configuration for ceilometer-rootwrap
# This file should be owned by (and only-writeable by) the root user

[DEFAULT]
# List of directories to load filter definitions from (separated by ',').
# These directories MUST all be only writeable by root !
filters_path=/etc/ceilometer/rootwrap.d,/usr/share/ceilometer/rootwrap

# List of directories to search executables in, in case filters do not
# explicitely specify a full path (separated by ',')
# If not specified, defaults to system PATH environment variable.
# These directories MUST all be only writeable by root !
exec_dirs=/sbin,/usr/sbin,/bin,/usr/bin,/usr/local/sbin,/usr/local/bin

# Enable logging to syslog
# Default value is False
use_syslog=False

# Which syslog facility to use.
# Valid values include auth, authpriv, syslog, user0, user1...
# Default value is 'syslog'
syslog_log_facility=syslog

# Which messages to log.
# INFO means log all usage
# ERROR means only log unsuccessful attempts
syslog_log_level=ERROR

```

在/etc/ceilometer/rootwrap.d/下新建文件central.filters

vim central.filters

```bash
# ceilometer-rootwrap command filters for IPMI capable nodes
# This file should be owned by (and only-writeable by) the root user

[Filters]
# ceilometer/polling/data_process.py: 'fdisk' 'pvdisplay' 'libguestfs'
fdisk: CommandFilter, fdisk, root
pvdisplay: CommandFilter, pvdisplay, root
libguestfs: CommandFilter, libguestfs, root

```

3,创建软链接

```bash
x86:
ln -s /usr/lib/python2.7/site-packages/libguestfs-1.40.2/run /usr/bin/libguestfs    
arm:
ln -s /usr/lib/python3/dist-packages/libguestfs-1.40.2/run /usr/bin/libguestfs   
```



