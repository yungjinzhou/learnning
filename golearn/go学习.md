## go学习









### 基础语法



#### 占位符

```
%v：默认格式输出变量的值
%d：将变量格式化为十进制整数
%b：将变量格式化为二进制整数
%o：将变量格式化为八进制整数
%x：将变量格式化为十六进制整数（小写字母）
%X：将变量格式化为十六进制整数（大写字母）
%f：将变量格式化为浮点数
%e：将变量格式化为科学计数法表示的浮点数（小写字母 e）
%E：将变量格式化为科学计数法表示的浮点数（大写字母 E）
%g：根据变量的值自动选择 %f 或 %e 格式输出浮点数
%s：将变量格式化为字符串
%p：将变量格式化为指针的地址
%T：输出变量的类型
%t：将变量格式化为布尔型
%c：将变量格式化为对应的 Unicode 字符
%U：将变量格式化为对应的 Unicode 字符的格式化表示方式
%q: 用于将变量格式化为带有双引号的字符串。这个占位符会将字符串中的特殊字符转义，例如换        行符、回车符、制表符等，以便输出的字符串可以直接用于代码中
 
```



#### 写入器io.Writer

在 Go 语言中，`io.Writer` 接口表示一个写入器，它可以向某个输出流写入数据。`io.Writer` 接口定义了 `Write` 方法，用于写入数据。任何实现了 `Write` 方法的类型都可以实现 `io.Writer` 接口。

`io.Writer` 接口常用的实现包括文件、网络连接、内存缓冲区等。通过使用 `io.Writer` 接口，程序可以将数据写入不同的输出流，而无需考虑底层实现的细节。



#### case用法







```
package main

import "fmt"

func main() {
    num := 2

    switch num {
    case 1:
        fmt.Println("one")
    case 2:
        fmt.Println("two")
    case 3:
        fmt.Println("three")
    default:
        fmt.Println("unknown")
    }
}



func main() {
    num := 42

    switch {
    case num < 0:
        fmt.Println("negative")
    case num >= 0 && num < 10:
        fmt.Println("single-digit")
    case num >= 10 && num < 100:
        fmt.Println("double-digit")
    default:
        fmt.Println("large number")
    }
}
```



#### type

```
type 关键字可以用于定义新的数据类型。这些新类型可以是基本数据类型的组合、结构体或接口的实现等。通过定义新的数据类型，可以提高代码的可读性和可维护性。

type 关键字还可以用于定义类型别名。
```





#### struct(类)及继承

##### 类

以及指针与非指针的区别

```
package main

import "fmt"

/*

class Person():
   name = None
   xxxxx

*/

// struct类似python的class

type Person struct {
	name   string
	age    int
	gender string
	score  float64
}

// 在类外绑定方法

func (p *Person) Eat() {
	fmt.Sprintln("Person is eating")
	fmt.Sprintln(p.name + "is eating")
	p.name = "Duck"

}

func (p Person) Eat2() {
	fmt.Sprintln("Person is eating")
	fmt.Sprintln(p.name + "is eating")
	p.name = "duke"
}

func main() {
	lily := Person{
		name:   "lily",
		age:    30,
		gender: "女",
		score:  10,
	}
	lily2 := lily
	fmt.Println("Eat, 使用p  *Persion，使用指针....")
	fmt.Println("修改前，lily", lily) //lily
	lily.Eat()
	fmt.Println("修改后lily", lily) // duke

	fmt.Println("Eat2, 使用p Persion，不使用指针....")
	fmt.Println("修改前， lily2....", lily2) // lily
	lily2.Eat2()
	fmt.Println("修改后，lily2....", lily2) // lily

}

```

##### 类的继承

包名不同，包中变量只有大写字母开头的，属于public，外部包可访问，

```
package main

import "fmt"

type Human struct {
	name   string
	age    int
	gender string
}

func (h *Human) Eat() {
	fmt.Println("this is  : ,", h.name)
}

// 类的嵌套

type Student struct {
	hum    Human //属于类的嵌套
	school string
	score  float64
}

//类的继承

type Teacher struct {
	subject string
	Human   // 直接写类，没有字段名字
}

func main() {
	s1 := Student{
		hum: Human{
			name:   "lily",
			age:    18,
			gender: "女",
		},
		school: "sss",
		score:  10,
	}
	fmt.Println(s1.hum.name)
	fmt.Println(s1.school)

	t1 := Teacher{}
	t1.subject = "数学"
	t1.age = 80
	t1.gender = "女"
	t1.name = "闫老师"
	fmt.Println(t1.subject)
	// 子类默认会创建和类同名字段，为了在子类中能操作父类
	fmt.Println(t1.name)
	fmt.Println(t1.Human.name)
}

```



#### Interface(接口)

接口可以接收任意数据类型

```
package main

import "fmt"

func main() {
	var i, j, k interface{}
	names := []string{"duke", "lily"}
	i = names
	fmt.Println("爱表切片数组：", i)
	age := 20
	j = age
	fmt.Println("j代表数字", j)

	str := "字符串"
	k = str
	fmt.Println("k代表数字", k)

	//具体类型判断
	kvalue, ok := k.(int)
	if !ok {
		fmt.Println("不是int")
	} else {
		fmt.Println("是int", kvalue)
	}
	// 使用switch判断用户输入的不同类型，根据不同类型做相应的处理
	array := make([]interface{}, 3)
	array[0] = 1
	array[1] = "hello world"
	array[2] = true
	for _, v := range array {
		switch v.(type) {
		case string:
			fmt.Printf("类型是字符串，内容为 %s\n", v)
		case int:
			fmt.Printf("类型是字符串，内容为 %d\n", v)
		case bool:
			fmt.Printf("类型为bool，内容为 %v\n", v)
		default:
			fmt.Println("不合理的数据类型")
		}
	}

}

```







##### 多态

多态性是 : 一个接口,多种实现

```
package main

import "fmt"

//定义一个类型，类型是interface，接口中的函数是虚函数，不能有实现

type IAttack interface {
	Attack()
}

type HumanLowLevel struct {
	name  string
	level int
}

type HumanHighLevel struct {
	name  string
	level int
}

func (a *HumanLowLevel) Attack() {
	fmt.Println("我是：", a.name, "我的等级是：", a.level)
}

func (a *HumanHighLevel) Attack() {
	fmt.Println("我是：", a.name, "我的等级是：", a.level)
}

// 传入不同的对象，调用同样的方法，实现多态

func DoAttack(a IAttack) {
	a.Attack()

}

func main() {
	lowLevel := HumanLowLevel{
		name:  "David",
		level: 1,
	}
	lowLevel.Attack()

	var player IAttack // 定义一个接口变量

	highLevel := HumanHighLevel{
		name:  "lily",
		level: 10,
	}
	highLevel.Attack()

	player = &lowLevel
	player.Attack()

	player = &highLevel
	player.Attack()

	// 多态
	DoAttack(&lowLevel)
	DoAttack(&highLevel)

}
```









