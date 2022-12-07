Name: node-info		
Version: 1.0.0	
Release: 1%{?dist}
Summary: collect node monitor info	

Group: Development	
License: GPL

Source0: /home/yang/node_info_rpm/rpm_mode/node-info-1.0.0.tar.gz	
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root


Requires: python-paramiko >= 2.1.1
Requires: python-memcached >= 1.58	
Requires: memcached >= 1.5.6	
Requires: python2-PyMySQL >= 0.9.3	

%description

%prep

%setup -n %{name}-%{version}


%build


%install
mkdir -p %{buildroot}/etc/logrotate.d/
mkdir -p %{buildroot}/usr/lib/python2.7/site-packages/
mkdir -p %{buildroot}/var/log/nodeinfo/
mkdir -p %{buildroot}/etc/nodeinfo/
mkdir -p %{buildroot}/usr/lib/systemd/system/
mkdir -p %{buildroot}/%{_bindir}/

install -m 0666 %{_builddir}/%{name}-%{version}/node-info %{buildroot}/etc/logrotate.d/
install -m 0666 %{_builddir}/%{name}-%{version}/node_info.log %{buildroot}/var/log/nodeinfo/
install -m 0666 %{_builddir}/%{name}-%{version}/node_info.py %{buildroot}/usr/lib/python2.7/site-packages/
install -m 0644 %{_builddir}/%{name}-%{version}/openstack-node-info.service %{buildroot}/usr/lib/systemd/system/
install -m 0666 %{_builddir}/%{name}-%{version}/node_info.conf %{buildroot}/etc/nodeinfo/
install -m 0777 %{_builddir}/%{name}-%{version}/check_user.sh %{buildroot}/%{_bindir}/
chmod 0777 %{buildroot}/%{_bindir}/check_user.sh
/bin/bash %{buildroot}/%{_bindir}/check_user.sh
 

%pre



%post 
systemctl daemon-reload


%postun

%clean
#rm -rf /usr/lib/systemd/system/openstack-node-info.service
#rm -rf /var/log/nodeinfo/
#rm -rf /etc/nodeinfo/
#rm -rf /etc/logrotate.d/node-info
#rm -rf /usr/lib/python2.7/site-packages/node-info.py*
#rm -rf %{_bindir}/check_user

%files
%attr(777, root, root) %{_bindir}/check_user.sh
%attr (644, root, root) %{_sysconfdir}/logrotate.d/node-info
%dir %attr(766, nova, nova) /var/log/nodeinfo/
%attr(766, nova, nova) /var/log/nodeinfo/node_info.log
%attr (644, root, root)/usr/lib/systemd/system/openstack-node-info.service
#%config(noreplace) /etc/nodeinfo/node_info.conf
%attr(666, nova, nova) /etc/nodeinfo/node_info.conf
/usr/lib/python2.7/site-packages/node_info.py*

%doc

%changelog

