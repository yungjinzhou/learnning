rpm包制作



安装rpm包制作工具

$ yum install rpmdevtools

生成目录

$ rpmdev-setuptree



https://blog.csdn.net/get_set/article/details/53453320









用法：`rpm -ivh rpm_name`

> 参数解释：
>
> - -i（install）：安装软件包。
> - -v（verbose）：显示安装的过程信息。可视化。







**4.查询一个包是否安装：**

命令：`rpm -q rpm包名` (这里的包名，是不带有平台信息以及后缀名的)





**5.得到一个已安装rpm包的相关信息：**

命令：`rpm -qi b包名` （同样不需要加平台信息与后缀名）



**6.列出一个rpm包安装的文件：**

命令 `rpm -ql 包名`

> -l（list）：列出软件包中的文件。
>
> -s（state）：显示列出文件的状态。





**7.列出某一个文件属于哪个rpm包：**

命令 `rpm -qf 文件的绝对路径`

-f（file）： 查询/验证文件属于的软件包



rpm使用

https://blog.csdn.net/qq_38265137/article/details/80793212























