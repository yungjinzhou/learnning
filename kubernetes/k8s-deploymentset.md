## DeploymentSet





```

kubectl run net-test --image=alpine --replicas=2 sleep 36000　　#创建名称为net-test的应用，镜像指定为alpine，副本数为2个


kubectl create -f nginx-deployment.yaml


kubectl get replicaset　　#获取副本集信息



kubectl describe replicaset net-test-5767cb94df　　#查看副本集的详细信息



kubectl get deployment命令可以查看net-test的状态，输出显示两个副本正常运行。


还可以在创建的过程中，通过kubectl describe deployment net-test了解详细的信息。  



kubectl get pod　　#获取Pod信息，可以看到2个副本都处于Running状态



kubectl describe pod net-test-5767cb94df-djt98 #查看pod的详细信息





```

