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









