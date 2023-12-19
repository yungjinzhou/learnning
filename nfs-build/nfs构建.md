

### 文件共享nfs

#### 1.1 搭建nfs

搭建环境Centos7.9-x86_64，可联网

```javascript
yum install rpcbind nfs-utils
mkdir /home/test
chmod -R 777 /home/test/
cd /home/test/


vim /etc/exports
写入 /home/test 10.21.16.43/24(rw)   

# 以下未测试
写入 /home/test *(rw,sync,insecure,no_subtree_check,no_root_squash)




```

是配置生效

```
exportfs -r
```



开启服务

```javascript
systemctl start rpcbind nfs
```

设置开机自启 

```
mkdir /nfs
echo "10.21.16.43:/home/test /nfs nfs4 defaults 0 0" >> /etc/fstab 
mount -av
```

查看共享信息

```
showmount -e 10.21.16.43  (此处ip地址为搭建服务器主机地址)
```



参考链接：

搭建

https://cloud.tencent.com/developer/article/1711894











