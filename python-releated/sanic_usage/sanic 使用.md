## Sanic学习





要求：python3.8以上



安装基础环境，在centos7中安装python3.8

```
yum install zlib zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gcc make libffi-devel wget -y
```



安装openssl

```

# 下载openssl安装包
wget http://www.openssl.org/source/openssl-1.1.1.tar.gz 
# 解压
tar -zxvf openssl-1.1.1.tar.gz 
# 进入
cd openssl-1.1.1
# 配置
./config --prefix=/usr/local/openssl shared zlib
# 安装
make && make install

# 修改环境变量
echo "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/openssl/lib" >>  /etc/profile 
source /etc/profile 

```



安装python3.8

```

wget https://www.python.org/ftp/python/3.8.1/Python-3.8.1.tgz
# 解压压缩包
tar -zxvf Python-3.8.1.tgz  

# 进入文件夹
cd Python-3.8.1

# 配置安装位置
./configure --prefix=/usr/local/python3 --with-openssl=/usr/local/openssl 

# 安装
make && make install


#添加python3的软链接 
ln -s /usr/local/python3/bin/python3.8 /usr/bin/python3.8 

#添加 pip3 的软链接 
ln -s /usr/local/python3/bin/pip3.8 /usr/bin/pip3.8

```





安装swagger-py-codegen

```
python3.8 -m venv myenv
source myenv/bin/activate

pip install swagger-py-codegen

swagger_py_codegen -s api.yml example-app -p demo -tlp=sanic

$ cd example-app
$ pip install -r requirements.txt
```

启动服务

```
Start example-app:

$ cd demo
$ python __init__.py


And generate example-app-ui from api.yml with ui:

$ swagger_py_codegen -s api.yml  example-app-ui -p demo-ui --ui --spec
Then you can visit http://127.0.0.1:5000/static/swagger-ui/index.html in a browser.
```





生成基础架构

```
$ swagger_py_codegen -s api.yml example-app -p demo -tlp=sanic
$ tree (sanic-demo)
.
|__ api.yml
|__ example-app
   |__ demo
   |  |__ __init__.py
   |  |__ v1
   |     |__ api
   |     |  |__ __init__.py
   |     |  |__ pets.py
   |     |  |__ pets_petId.py
   |     |__ __init__.py
   |     |__ routes.py
   |     |__ schemas.py
   |     |__ validators.py
   |__ requirements.txt
```





api.yml

```
swagger: "2.0"
info:
  version: 1.0.0
  title: Swagger Petstore
  license:
    name: MIT
host: petstore.swagger.io
basePath: /v1
schemes:
  - http
consumes:
  - application/json
produces:
  - application/json
paths:
  /pets:
    get:
      summary: List all pets
      operationId: listPets
      tags:
        - pets
      parameters:
        - name: limit
          in: query
          description: How many items to return at one time (max 100)
          required: false
          type: integer
          format: int32
      responses:
        "200":
          description: An paged array of pets
          headers:
            x-next:
              type: string
              description: A link to the next page of responses
          schema:
            $ref: '#/definitions/Pets'
        default:
          description: unexpected error
          schema:
            $ref: '#/definitions/Error'
    post:
      summary: Create a pet
      operationId: createPets
      tags:
        - pets
      responses:
        "201":
          description: Null response
        default:
          description: unexpected error
          schema:
            $ref: '#/definitions/Error'
  /pets/{petId}:
    get:
      summary: Info for a specific pet
      operationId: showPetById
      tags:
        - pets
      parameters:
        - name: petId
          in: path
          required: true
          description: The id of the pet to retrieve
          type: string
      responses:
        "200":
          description: Expected response to a valid request
          schema:
            $ref: '#/definitions/Pets'
        default:
          description: unexpected error
          schema:
            $ref: '#/definitions/Error'
definitions:
  Pet:
    required:
      - id
      - name
    properties:
      id:
        type: integer
        format: int64
      name:
        type: string
      tag:
        type: string
  Pets:
    type: array
    items:
      $ref: '#/definitions/Pet'
  Error:
    required:
      - code
      - message
    properties:
      code:
        type: integer
        format: int32
      message:
        type: string
```





参考资料：

1. 生成框架

根据架构生成基础框架

https://github.com/guokr/swagger-py-codegen?tab=readme-ov-file
