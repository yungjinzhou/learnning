## Deployment





```
[root@linux-node1 ~]# vim nginx-deployment.yaml　　#使用yaml的方式进行创建应用
apiVersion: apps/v1　　#apiVersion是当前配置格式的版本
kind: Deployment　　　　#kind是要创建的资源类型，这里是Deploymnet
metadata:　　　　　　　　#metadata是该资源的元数据，name是必须的元数据项
  name: nginx-deployment
  labels:
    app: nginx
spec:　　　　　　　　　　#spec部分是该Deployment的规则说明
  replicas: 3　　　　　 #relicas指定副本数量，默认为1
  selector:
    matchLabels:
      app: nginx
  template:　　　　　　#template定义Pod的模板，这是配置的重要部分
    metadata:　　　　  #metadata定义Pod的元数据，至少要顶一个label，label的key和value可以任意指定
      labels:
        app: nginx
    spec:　　　　　　　#spec描述的是Pod的规则，此部分定义pod中每一个容器的属性，name和image是必需的
      containers:
      - name: nginx
        image: nginx:1.13.12
        ports:
        - containerPort: 80





```

