## python库操作linux



> 对比os模块的函数和shutil模块中包含的函数，会发现它们有一些重复。那么为什么会存在两个模块提供相同功能的情况呢？这就涉及到了标准库模块的定位问题了。**os模块**是对操作系统的接口进行封装，**主要作用是跨平台**，**shutil模块**包含复制、移动、重命名、删除文件目录以及压缩包的函数，**主要作用是管理文件和目录**，因此它们并不冲突，并且是互补的关系。
>
> 对于常见的文件操作，shutil更易于使用。优先使用shutil，shutil里面没有提供相应功能的情况下再使用os模块下的函数。



### os模块使用

```
os.sep    可以取代操作系统特定的路径分隔符。windows下为 '\\'
os.name    字符串指示你正在使用的平台。比如对于Windows，它是'nt'，而对于Linux/Unix用户，它是 'posix'
os.getcwd()    函数得到当前工作目录，即当前Python脚本工作的目录路径
os.getenv()    获取一个环境变量，如果没有返回none
os.putenv(key, value)    设置一个环境变量值
os.listdir(path)    返回指定目录下的所有文件和目录名
os.remove(path)    函数用来删除一个文件
os.system(command)    函数用来运行shell命令
os.linesep    字符串给出当前平台使用的行终止符。例如，Windows使用 '\r\n'，Linux使用 '\n' 而Mac使用 '\r'
os.path.split(path)        函数返回一个路径的目录名和文件名
os.path.isfile()    和os.path.isdir()函数分别检验给出的路径是一个文件还是目录
os.path.exists()    函数用来检验给出的路径是否真地存在
os.curdir        返回当前目录 ('.')
os.mkdir(path)    创建一个目录
os.makedirs(path)    递归的创建目录
os.chdir(dirname)    改变工作目录到dirname          
os.path.getsize(name)    获得文件大小，如果name是目录返回0L
os.path.abspath(name)    获得绝对路径
os.path.normpath(path)    规范path字符串形式
os.path.splitext()        分离文件名与扩展名
os.path.join(path,name)    连接目录与文件名或目录
os.path.basename(path)    返回文件名
os.path.dirname(path)    返回文件路径
os.walk(top,topdown=True,onerror=None)        遍历迭代目录
os.rename(src, dst)        重命名file或者directory src到dst 如果dst是一个存在的directory, 将抛出OSError. 在Unix, 如果dst在存且是一个file, 如果用户有权限的话，它将被安静的替换. 操作将会失败在某些Unix 中如果src和dst在不同的文件系统中. 如果成功, 这命名操作将会是一个原子操作 (这是POSIX 需要). 在 Windows上, 如果dst已经存在, 将抛出OSError，即使它是一个文件. 在unix，Windows中有效。
os.renames(old, new)    递归重命名文件夹或者文件。像rename()




```





### shutil模块使用

```

查找命令绝对路径
shutil.which('cmd') 


复制文件
shutil.copyfile( src, dst, follow_symlinks=True)  前提是目标地址是具备可写权限，从源src复制到dst中去数据。如果当前的dst已存在的话就会被覆盖掉，抛出的异常信息为IOException。
shutil.copy( src, dst, follow_symlinks=True)      复制一个文件到一个文件或一个目录,相当于cp src dst，会同时复制文件的mode（权限、所有者）；(follow_symlinks为True,则链接会被拷贝)
shutil.copy2( src, dst, follow_symlinks=True)     在copy上的基础上再复制文件最后访问时间与修改时间也复制过来了，类似于cp –p的东西;如果两个位置的文件系统是一样的话相当于是rename操作，只是改名；如果是不在相同的文件系统的话就是做move操作


复制权限
shutil.copymode(src, dst)    只是会复制其权限其他的东西是不会被复制的
shutil.copystat( src, dst)    复制权限、最后访问时间、最后修改时间


复制目录
shutil.copytree( olddir, newdir, True/Flase)
把olddir拷贝一份newdir，如果第3个参数是True，则复制目录时将保持文件夹下的符号连接，如果第3个参数是False，则将在复制的目录下生成物理副本来替代符号连接


移动文件、目录或重命名
shutil.move( src, dst)        移动文件或重命名


更改属主及属组
shutil.chown('path','user','group') 

删除目录
shutil.rmtree('path') 递归删除一个目录以及目录内的所有内容


获取磁盘使用空间
total, used, free = shutil.disk_usage("path")
print("当前磁盘共: %iGB, 已使用: %iGB, 剩余: %iGB"%(total / 1073741824, used / 1073741824, free / 1073741824))
注：默认单位是字节，所以转换为了GB，公式如下：
1KB= 1024字节，1MB= 1024KB，1GB= 1024MB； 所以：1G=1073741824字节。也就是上面为什么要除以1073741824



归档和解包
1）获取当前系统支持的解包文件格式（后缀）
shutil.get_unpack_formats()   

2）获取当前系统支持的压缩文件格式（后缀）
shutil.get_archive_formats()

3）压缩
shutil.make_archive('test','gztar','./')    
#将当前目录下所有文件打包为test.tar.gz
参数解释如下（从左往右开始）：
base_name： 目标压缩包的文件名，也可以是压缩包的路径。只是文件名时，则保存至当前目录，否则保存至指定路径。 如：/Users/wupeiqi/www =>保存至/Users/wupeiqi/
gztar： 压缩包种类，可选值有：“zip”, “tar”, “bztar”，“gztar”
./： 要压缩的文件夹路径（默认当前目录）

4）解压缩
shutil.unpack_archive(filename,extract_dir=None,format=None)
# 栗子：
shutil.unpack_archive('test.tar.gz','/opt/tlv')
filename：文件路径；
extract_dir：解压至的文件夹路径。文件夹可以不存在，会自动生成；
format：解压格式，默认为None，会根据扩展名自动选择解压格式。

```







参考链接：https://www.cnblogs.com/funsion/p/4017989.html

参考链接：https://www.huaweicloud.com/articles/7de24c56faf04eb53593e37999896606.html