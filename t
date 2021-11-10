[1mdiff --git "a/kubernetes/\346\267\261\345\205\245\345\211\226\346\236\220kubernetes.md" "b/kubernetes/\346\267\261\345\205\245\345\211\226\346\236\220kubernetes.md"[m
[1mindex 34d83f6..d58ef7b 100644[m
[1m--- "a/kubernetes/\346\267\261\345\205\245\345\211\226\346\236\220kubernetes.md"[m
[1m+++ "b/kubernetes/\346\267\261\345\205\245\345\211\226\346\236\220kubernetes.md"[m
[36m@@ -555,6 +555,10 @@[m [msystemctl enable kubelet[m
 [m
 ```apache[m
 kubeadm init --apiserver-advertise-address=10.0.0.7 --image-repository registry.aliyuncs.com/google_containers --kubernetes-version v1.18.0 --service-cidr=10.96.0.0/12 --pod-network-cidr=10.244.0.0/16[m
[32m+[m
[32m+[m
[32m+[m[32mkubeadm init --apiserver-advertise-address=192.168.23.232 --image-repository registry.aliyuncs.com/google_containers --kubernetes-version v1.18.0 --service-cidr=10.96.0.0/12 --pod-network-cidr=10.244.0.0/16[m
[32m+[m
 ```[m
 [m
 得到token[m
[1mdiff --git "a/openstack-stein-mugnum/\345\234\250\345\256\236\344\276\213centos\344\270\255\345\256\211\350\243\205kube\347\216\257\345\242\203.md" "b/openstack-stein-mugnum/\345\234\250\345\256\236\344\276\213centos\344\270\255\345\256\211\350\243\205kube\347\216\257\345\242\203.md"[m
[1mindex 1bb20cd..5ad24b7 100644[m
[1m--- "a/openstack-stein-mugnum/\345\234\250\345\256\236\344\276\213centos\344\270\255\345\256\211\350\243\205kube\347\216\257\345\242\203.md"[m
[1m+++ "b/openstack-stein-mugnum/\345\234\250\345\256\236\344\276\213centos\344\270\255\345\256\211\350\243\205kube\347\216\257\345\242\203.md"[m
[36m@@ -39,6 +39,20 @@[m [mDNS2=114.114.114.114[m
 hostnamectl set-hostname k8smaster[m
 ```[m
 [m
[32m+[m[41m[m
[32m+[m[41m[m
[32m+[m[32m```[m[41m[m
[32m+[m[32mvim /etc/hostname[m[41m[m
[32m+[m[41m[m
[32m+[m[41m[m
[32m+[m[32m```[m[41m[m
[32m+[m[41m[m
[32m+[m[41m[m
[32m+[m[41m[m
[32m+[m[41m[m
[32m+[m[41m[m
[32m+[m[41m[m
[32m+[m[41m[m
 配置nameserver[m
 [m
 ```[m
[36m@@ -217,7 +231,7 @@[m [msystemctl enable kubelet[m
 kubeadm init --apiserver-advertise-address=10.0.0.7 --image-repository registry.aliyuncs.com/google_containers --kubernetes-version v1.18.0 --service-cidr=10.96.0.0/12 --pod-network-cidr=10.244.0.0/16[m
 [m
 [m
[31m-kubeadm init --apiserver-advertise-address=192.168.204.82 --image-repository registry.aliyuncs.com/google_containers --kubernetes-version v1.18.0 --service-cidr=10.96.0.0/12 --pod-network-cidr=10.244.0.0/16[m
[32m+[m[32mkubeadm init --apiserver-advertise-address=192.168.204.142 --image-repository registry.aliyuncs.com/google_containers --kubernetes-version v1.18.0 --service-cidr=10.96.0.0/12 --pod-network-cidr=10.244.0.0/16[m[41m[m
 [m
 ```[m
 [m
[36m@@ -604,6 +618,7 @@[m [mTo see the stack trace of this error execute with --v=5 or higher[m
 [m
 ```[m
 [m
[32m+[m[41m[m
 ```[m
 [m
 [m
