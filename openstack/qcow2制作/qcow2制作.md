## qcow2制作





下载 xmanager等软件

https://www.downkuai.com/soft/133269.html



创建一个kvm虚拟机实例



安装



https://codeantenna.com/a/GWD1lCSQAi













```
virt-install --name centos7 --ram 1024 --vcpus 1 --os-type linux --os-variant rhel7-arch=x86_64 --network network=default,model=virtio --disk path=/tmp/centos7_mini.qcow2,format=qcow2 -c /opt/image/CentOS-7-x86_64-Minimal-2003.iso --console pty,target_type=serial   --graphics vnc,listen=0.0.0.0,port=7788



```







```

virt-install --name CentOS7_mini --ram 4096 --vcpus 4 --os-type linux --os-variant rhel7 --arch=x86_64 --network network=default,model=virtio --disk path=/data/CentOS7_mini.qcow2,format=qcow2 --location /data/CentOS-7-x86_64-Minimal-1908.iso --console pty,target_type=serial   --graphics vnc,listen=0.0.0.0,port=7788



执行后，stuck druft init  
```









```
virt-install --virt-type kvm --name centos7 --os-variant generic --ram 1024 --vcpus=2 --disk path=//tmp/centos_mini.qcow2,format=qcow2 --location /opt/image/CentOS-7-x86_64-Minimal-2003.iso  -x "console=ttyS0 dns=192.168.39.2 ip=192.168.39.200::192.168.39.2:255.255.255.0:test.example.com:ens2:none" --network bridge:br1 --graphics none

执行后无法识别网络
```









```
virt-install --virt-type kvm --name centos7 --os-variant generic --ram 1024 --vcpus=2 --disk path=/tmp/centos_mini.qcow2,format=qcow2 --location /opt/image/CentOS-7-x86_64-Minimal-2003.iso  -x "console=ttyS0 dns=192.168.39.2 ip=192.168.39.200::192.168.39.2:255.255.255.0:test.example.com:ens2:none" --network bridge:br1 --console pty,target_type=serial   --graphics vnc,listen=0.0.0.0,port=7788

执行后 ，一直卡在 
probing EDD (edd=off to disable)... ok

```



```
virt-install --virt-type=kvm --name vm02 --ram 2048 --vcpus=2 --disk path=/tmp/centos_mini.qcow2,format=qcow2,bus=virtio,size=10 --os-variant=centos7.0 --network bridge=virbr0 --console pty,target_type=serial --location /opt/image/CentOS-7-x86_64-Minimal-2003.iso --extra-args 'console=ttyS0,115200n8 serial ks=/root/kvm/ks7.cfg' --nographics

```







```
virt-install --name centos7 --ram 4096 --disk path=/var/kvm/images/centos7.img,size=30 --vcpus 2 --os-type linux --os-variant rhel7 --network bridge=virbr0 --graphics none --console pty,target_type=serial --location 'http://ftp.iij.ad.jp/pub/linux/centos/7/os/x86_64/' --extra-args 'console=ttyS0,115200n8 serial'

```







```
--graphics vnc,password=password,listen=0.0.0.0,keymap=en-us


```





```
virt-install --connect qemu:///system  --name centos7 --ram 2048 --vcpus 2  --network network=default,model=virtio  --disk path=/tmp/centos_mini.qcow2,format=qcow2,size=10,device=disk,bus=virtio --cdrom CentOS-7-x86_64-Minimal-2003.iso --disk path=/opt/image/CentOS-7-x86_64-Minimal-2003.iso,device=cdrom \
  --vnc --os-type linux
```





```
virt-install --connect qemu:///system -n centos --vcpus=1 -r 1024 \
--disk path=/tmp/centos7.qcow2,format=qcow2,device=disk,size=16,bus=virtio,cache=none \
--disk path=/opt/image/CentOS-7-x86_64-Minimal-2003.iso,device=cdrom,perms=rw \
--vnc --vnclisten=0.0.0.0  \
--os-type centos --os-variant=centos7.0 \
--accelerate --network=default,model=virtio  \
--disk path=/opt/image/virtio-win-0.1.173.iso,device=cdrom,perms=rw \
--disk=/opt/image/virtio-win-0.1.173_amd64.vfd,device=floppy


```

