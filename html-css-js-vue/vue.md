## vue库的使用



### vue简介

Vue.js是前端三大新框架：Angular.js、React.js、Vue.js之一，Vue.js目前的使用和关注程度在三大框架中稍微胜出，并且它的热度还在递增。

Vue.js可以作为一个js库来使用，也可以用它全套的工具来构建系统界面，这些可以根据项目的需要灵活选择，所以说，Vue.js是一套构建用户界面的渐进式框架。

Vue的核心库只关注视图层，Vue的目标是通过尽可能简单的 API 实现响应的数据绑定，在这一点上Vue.js类似于后台的模板语言。

Vue也可以将界面拆分成一个个的组件，通过组件来构建界面，然后用自动化工具来生成单页面(SPA - single page application)系统。

#### Vue.js使用文档及下载Vue.js

Vue.js使用文档已经写的很完备和详细了，通过以下地址可以查看： https://cn.vuejs.org/v2/guide/
vue.js如果当成一个库来使用，可以通过下面地址下载： https://cn.vuejs.org/v2/guide/installation.html



### VUE.js基本概念

首先通过将vue.js作为一个js库来使用，来学习vue的一些基本概念，我们下载了vue.js后，需要在页面上通过script标签引入vue.js，开发中可以使用开发版本vue.js，产品上线要换成vue.min.js。

```
<script type="text/javascript" src="js/vue.min.js"></script>
```

#### Vue实例

每个 Vue 应用都是通过实例化一个新的 Vue对象开始的：

```
window.onload = function(){
    var vm = new Vue({
        el:'#app',
        data:{message:'hello world!'}
    });
}    
......

<div id="app">{{ message }}</div>
```

其中，el属性对应一个标签，当vue对象创建后，这个标签内的区域就被vue对象接管，在这个区域内就可以使用vue对象中定义的属性和方法。

#### 数据与方法

当一个 Vue 实例被创建时，它向 Vue 的响应式系统中加入了其data对象中能找到的所有的属性。当这些属性的值发生改变时，视图将会产生“响应”，即匹配更新为新的值。还可以在Vue实例中定义方法，通过方法来改变实例中data对象中的数据，数据改变了，视图中的数据也改变。

```
window.onload = function(){
    var vm = new Vue({
        el:'#app',
        data:{message:'hello world!'},
        methods:{
            fnChangeMsg:function(){
                this.message = 'hello Vue.js!';
            }
        }
    });
}    
......

<div id="app">
    <p>{{ message }}</p>
    <button @click="fnChangeMsg">改变数据和视图</button>
</div>
```





### Vue.js模板语法

模板语法指的是如何将数据放入html中，Vue.js使用了基于 HTML的模板语法，允许开发者声明式地将DOM绑定至底层 Vue 实例的数据。所有 Vue.js的模板都是合法的 HTML ，所以能被遵循规范的浏览器和 HTML 解析器解析。

#### 插入值

数据绑定最常见的形式就是使用“Mustache”语法 (双大括号) 的文本插值：

```
<span>Message: {{ msg }}</span>
```

如果是标签的属性要使用值，就不能使用“Mustache”语法，需要写成使用v-bind指令：

```
<a v-bind:href="url" v-bind:title='tip'>百度网</a>
```

插入的值当中还可以写表达式：

```
{{ number + 1 }}
{{ ok ? 'YES' : 'NO' }}
{{ message.split('').reverse().join('') }}
<a v-bind:href="url">链接文字</a>
```

#### 指令

指令 (Directives) 是带有“v-”前缀的特殊属性。指令属性的值预期是单个JavaScript表达式，指令的职责是，当表达式的值改变时，将其产生的连带影响，响应式地作用于DOM。常见的指令有v-bind、v-if、v-on。

```
<!-- 根据ok的布尔值来插入/移除 <p> 元素 -->
<p v-if="ok">是否显示这一段</p>

<!-- 监听按钮的click事件来执行fnChangeMsg方法 -->
<button v-on:click="fnChangeMsg">按钮</button>
```

#### 缩写

v-bind和v-on事件这两个指令会经常用，所以有简写方式：

```
<!-- 完整语法 -->
<a v-bind:href="url">...</a>

<!-- 缩写 -->
<a :href="url">...</a>


<!-- 完整语法 -->
<button v-on:click="fnChangeMsg">按钮</button>

<!-- 缩写 -->
<button @click="fnChangeMsg">按钮</button>
```





### 计算属性和侦听属性

#### 计算属性

模板内的表达式非常便利，但是设计它们的初衷是用于简单运算的。在模板中放入太多的逻辑会让模板过重且难以维护。例如：

```
<div id="example">
  {{ message.split('').reverse().join('') }}
</div>
```

这个表达式的功能是将message字符串进行反转，这种带有复杂逻辑的表达式，我们可以使用计算属性

```
<div id="example">
  <p>Original message: "{{ message }}"</p>
  <p>Computed reversed message: "{{ reversedMessage }}"</p>
</div>

......

var vm = new Vue({
  el: '#example',
  data: {
    message: 'Hello'
  },
  computed: {
    // 计算属性的 getter
    reversedMessage: function () {
      // `this` 指向 vm 实例
      return this.message.split('').reverse().join('')
    }
  }
})
```

#### 侦听属性

侦听属性的作用是侦听某属性值的变化，从而做相应的操作，侦听属性是一个对象，它的键是要监听的对象或者变量，值一般是函数,当你侦听的元素发生变化时，需要执行的函数，这个函数有两个形参，第一个是当前值，第二个是变化后的值。

```
window.onload = function(){
    var vm = new Vue({
        el:'#app',
        data:{
            iNum:1
        },
        watch:{
            iNum:function(newval,oldval){
                console.log(newval + ' | ' + oldval) 
            }
        },
        methods:{
            fnAdd:function(){
                this.iNum += 1;
            }
        }
    });
}
```





