## k8s常用命令





```
# 命令行创建
kubectl run net-test --image=alpine --replicas=2 sleep 36000　　#创建名称为net-test的应用，镜像指定为alpine，副本数为2个
# 修改镜像，升级
kubectl set image deployment/nginx-deployment nginx=nginx:1.15.2 --record    #nginx的版本升级，由1.13.2升级为1.15.2，记录需要加参数--record

# yaml文件创建
kubectl create -f nginx-deployment.yaml
kubectl apply -f nginx-deployment.yaml


#查看更新历史记录
kubectl rollout history deployment/nginx-deployment 
查看具体某一个版本的升级历史
kubectl rollout history deployment/nginx-deployment --revision=1


# 回滚上一个版本
kubectl rollout undo deployment/nginx-deployment   



# 扩容，对应用的副本数进行扩容，直接指定副本数为5
kubectl scale deployment nginx-deployment --replicas 5


# 删除资源
如果要删除这些资源，执行 kubectl delete deployment nginx-deployment 或者 kubectl delete -f nginx-deployment.yaml



#查看部署服务的信息。
kubectl get deployment

# 查看详细信息
kubectl describe deployment net-test  




#获取副本集信息
kubectl get replicaset　　

#查看副本集的详细信息
kubectl describe replicaset net-test-5767cb94df　　




# pod信息
kubectl get pod　　#获取Pod信息，可以看到2个副本都处于Running状态
kubectl get pod -o wide
kubect lget pod --output wide # 指定输出格式
kubectl describe pod net-test-5767cb94df-djt98 #查看pod的详细信息


 






# 不执行查看定义方式，--dry-run

kubectl explain sa   使用kebectl explain对资源进行解释，详细信息，有哪些参数等信息
kubectl create serviceaccount mysa -o yaml --dry-run #不执行查看定义方式
kubectl create serviceaccount mysa -o yaml --dry-run > serviceaccount.yaml  #直接导出为yaml定义文件，可以节省敲键盘的时间


kubectl create serviceaccount admin
kubectl describe sa/admin


kubectl config view

kubectl config use-context magedu@kubernetes


kubectl create role -h   

kubectl create role pods-reader --verb=get,list,watch --resource=pods --dry-run -o yaml #干跑模式查看role的定义


kubectl create rolebinding -h 


kubectl describe rolebinding magedu-read-pods #查看角色绑定的信息，这里可以看到user：magedu绑定到了pods-reader这个角色上


kubectl config use-context magedu@kubernetes #切换magedu这个用户，并使用get获取pods资源信息
Switched to context "magedu@kubernetes".


kubectl config use-context kubernetes-admin@kubernetes  #切换会kubernetes-admin用户
Switched to context "kubernetes-admin@kubernetes".

kubectl get rolebinding  #获取角色绑定信息


kubectl delete rolebinding magedu-read-pods #删除前面的绑定


kubectl create clusterrolebinding magedu-read-all-pods --clusterrole=cluster-read --user=magedu --dry-run -o yaml > clusterrolebinding-demo.yaml  #创建角色绑定，将magedu绑定到clusterrole：magedu-read-all-pods上



```

