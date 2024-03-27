# mysql 容器化



dockerfile

```
FROM mysql:5.7
COPY my.cnf /etc/my.cnf
RUN cd /docker-entrypoint-initdb.d && rm -rf *
# COPY mail.sql /docker-entrypoint-initdb.d/mail.sql

#ENV MYSQL_ALLOW_EMPTY_PASSWORD yes
#COPY setup.sh /mysql/setup.sh
#COPY privileges.sql /mysql/privileges.sql

ENV MYSQL_ROOT_PASSWORD=eetrust123 MYSQL_DATABASE=mail
ENV LANG=en_US.UTF-8
EXPOSE 3306
RUN echo lower_case_table_names=1 >> /etc/mysql/conf.d/docker.cnf

```



my.cnf

```
# For advice on how to change settings please see
# http://dev.mysql.com/doc/refman/5.7/en/server-configuration-defaults.html

[mysqld]
#
# Remove leading # and set to the amount of RAM for the most important data
# cache in MySQL. Start at 70% of total RAM for dedicated server, else 10%.
# innodb_buffer_pool_size = 128M
#
# Remove leading # to turn on a very important data integrity option: logging
# changes to the binary log between backups.
# log_bin
#
# Remove leading # to set options mainly useful for reporting servers.
# The server defaults are faster for transactions and fast SELECTs.
# Adjust sizes as needed, experiment to find the optimal values.
# join_buffer_size = 128M
# sort_buffer_size = 2M
# read_rnd_buffer_size = 2M
skip-host-cache
skip-name-resolve
datadir=/var/lib/mysql
socket=/var/run/mysqld/mysqld.sock
secure-file-priv=/var/lib/mysql-files
#user=mysql
bind-address=0.0.0.0

# Disabling symbolic-links is recommended to prevent assorted security risks
symbolic-links=0

#log-error=/var/log/mysqld.log
pid-file=/var/run/mysqld/mysqld.pid
[client]
socket=/var/run/mysqld/mysqld.sock

!includedir /etc/mysql/conf.d/
!includedir /etc/mysql/mysql.conf.d/
```



运行docker

```
docker rm -f mysqltest
docker rmi mysqltest:v1
docker build -t mysqltest:v1 .
docker run -itd --name mysqltest -p 33060:3306 mysqltest:v1
#mysql -uroot -peetrust123 -P 33060:3306 -h 10.201.4.31
```

