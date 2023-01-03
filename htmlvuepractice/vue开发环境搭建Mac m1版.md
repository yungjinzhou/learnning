

## vue开发环境搭建Mac m1 arm64版





### 首先安装nvm

````
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.37.2/install.sh | bash
````



安装完成后

```
source .bash_profile
nvm -v  # 0.37.2

```

### 安装node和vue、vue-cli



```
nvm install node
nvm list  #  v19.3.0
npm -v    # 9.2.0
npm install vue
vue --version   # 2.9.6
npm install vue-cli -g

```



### 构建工程目录

```
vue init webpack projectname
```













