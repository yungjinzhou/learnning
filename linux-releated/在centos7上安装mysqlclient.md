在centos7上



创建virtualenv -p python3 venv

venv中pip3 install -y mysqlclient==2.0.1

报错

Command "python setup.py egg_info" failed with error code 1 in /tmp/pip-build-yiqx1ego/mysqlclient/





解决办法

yum install -y python3-devel.x86_64

MySQL-python.x86_64（可不用安装）

mariadb-devel.x86_64

pip3 install mysqlclient==2.0.1

成功