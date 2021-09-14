## ovs配置：todo



```
 # 计算节点
 yum install -y ebtables ipset
  yum install -y openstack-neutron-openvswitch 
  OPENVSWITCH_CONF_FILE=/etc/neutron/plugins/ml2/openvswitch_agent.ini
  \# [ovs]
  crudini --set $OPENVSWITCH_CONF_FILE ovs local_ip $LOCAL_IP
  crudini --set $OPENVSWITCH_CONF_FILE ovs bridge_mappings $BRIDGE_MAPPINGS
  crudini --set $OPENVSWITCH_CONF_FILE ovs tunnel_id_ranges $TUNNEL_ID_RANGES

  \# [securitygroup]
  \# crudini --set $OPENVSWITCH_CONF_FILE securitygroup firewall_driver iptables_hybrid
  crudini --set $OPENVSWITCH_CONF_FILE securitygroup enable_security_group True
  crudini --set $OPENVSWITCH_CONF_FILE securitygroup firewall_driver neutron.agent.linux.iptables_firewall.OVSHybridIptablesFirewallDriver

  \# [agent]
  crudini --set $OPENVSWITCH_CONF_FILE agent tunnel_types vxlan
  crudini --set $OPENVSWITCH_CONF_FILE agent l2_population True
  crudini --set $OPENVSWITCH_CONF_FILE agent arp_responder True

  systemctl enable neutron-openvswitch-agent
  systemctl restart neutron-openvswitch-agent

里面有变量，注意修改一下
```



 

