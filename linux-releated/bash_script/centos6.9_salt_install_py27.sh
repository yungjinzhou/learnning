#£°/bin/bash
# docker÷–(centos:6.9)
set -e
yum install -y net-tools
yum install -y wget
yum install -y openssh-clients
yum install -y gcc
yum install epel-release
yum install -y vim-enhanced.x86_64

yum install https://repo.saltstack.com/yum/redhat/salt-repo-2017.7-1.el6.noarch.rpm
sed -i "s/^gpgcheck=1$/gpgcheck=0/" /etc/yum.repos.d/salt-2017.7.repo
yum install -y python27 
yum install -y python27-pip 
yum -y install rsyslog




# yum install epel-release
#°°yum install https://repo.saltstack.com/yum/redhat/salt-repo-latest-2.el7.noarch.rpm 