# Day02 - 变量、常量与基础类型

## 本章简介

Go 是静态强类型语言：变量类型在编译期确定，且**不存在隐式类型转换**。"变量怎么声明、类型是什么、零值是多少、何时会被遮蔽"必须一开始就弄清楚，否则后续写结构体、接口和并发代码时会被大量编译错误打断。

本章从 `var`、短变量声明与 `const` 讲起，深入零值机制与作用域规则，再梳理整数、浮点、布尔、字符串、`byte` 与 `rune`。Go 的常量可以"无类型"，参与运算时才按上下文确定类型；`iota` 让枚举、位标志与容量单位的书写极为简洁。

在 `eshop-gateway` 中，价格用 `float64` 还是以"分"为单位的 `int64`、库存用 `int` 还是 `int32`、订单状态用 `iota` 还是字符串、日志与 JSON 如何用 `fmt` 对齐，都会影响 Day06 的结构体与 Day13 的对外接口。今天养成的类型习惯会贯穿整个板块。

## 学习目标

- 掌握 `var` 的三种写法与 `:=` 短变量声明的适用场景
- 理解零值机制，能准确说出各基础类型的零值
- 区分包级、函数级与代码块级作用域，识别变量遮蔽
- 掌握 `const` 块与无类型常量的编译期特性
- 能用 `iota` 编写枚举、位标志与 KB/MB/GB 单位
- 熟悉整数家族、溢出回绕与 `uint` 的使用边界
- 理解浮点精度问题，避免用 `==` 比较浮点数
- 掌握显式类型转换与窄化转换的截断规则
- 熟练使用 `strconv` 完成字符串与数值互转
- 区分 `byte` 与 `rune`，知道它们是 `uint8` / `int32` 的别名
- 掌握 `fmt` 常用动词、宽度精度与 `Sprintf` 组装字符串

## 理论知识讲解

### 1. 变量声明的三种写法

| 写法 | 可用位置 | 特点 |
|------|---------|------|
| `var x T = v` | 包级 / 函数内 | 最明确，适合固定宽度类型 |
| `var x = v` | 包级 / 函数内 | 类型由字面量推导 |
| `x := v` | 仅函数内 | 最常用，左侧至少一个新变量 |

```go
var price float64 = 5999.00 // 显式类型
var stock = 120             // 推导为 int
sku := "SKU-1001"           // 短声明
```

同一作用域不能重复声明同名变量；**未使用的局部变量直接编译失败**，包级变量则不受此限制。

### 2. 零值机制

Go 不存在"未初始化变量"，声明即写入该类型的零值：

| 类型 | 零值 | 类型 | 零值 |
|------|------|------|------|
| `int` / `int64` | `0` | `bool` | `false` |
| `uint` / `byte` | `0` | `string` | `""` |
| `float32` / `float64` | `0` | 指针 / 切片 / Map / 接口 / Channel / 函数 | `nil` |

```go
var s string
var n int
var p *int
fmt.Printf("%q %d %v\n", s, n, p) // "" 0 <nil>
```

与 Python 的 `None`、TypeScript 的 `undefined` 不同，Go 的零值是按类型确定的具体值，函数返回值与结构体字段永远有确定语义。

### 3. 短声明、作用域与变量遮蔽

`if`、`for`、`switch` 的初始化语句会创建隐式代码块；内层用 `:=` 声明同名变量时，会**遮蔽**外层变量而不是修改它：

```go
stock := 100
if stock > 0 {
	stock := 50        // 新变量
	fmt.Println(stock) // 50
}
fmt.Println(stock) // 100

var err error
if err := query(); err != nil { // 这里的 err 也是新变量
	fmt.Println(err)
} // 外层的 err 仍为 nil
```

> 常见坑：在代码块内想给外层变量赋值，却误用 `:=` 创建了新变量。赋值请用 `=`。

### 4. 常量与无类型常量

`const` 的值必须在编译期确定，只能是布尔、数值、字符串及其常量表达式：

```go
const MaxRetries = 3

const (
	ServiceName = "eshop-gateway"
	Version     = "0.1.0"
)

const discount = 0.85
var f32 float32 = discount // 无类型常量按上下文适配
var f64 float64 = discount
```

无类型常量不会绑定具体类型，因此能同时用于不同精度；而 `var discount = 0.85` 会被推导为 `float64`，赋给 `float32` 就需要显式转换。

### 5. iota 枚举与位标志

`iota` 在每个 `const` 块中从 0 开始，块内每新增一行常量声明就自增 1：

```go
const (
	StatusPending = iota // 0
	StatusPaid           // 1
	StatusShipped        // 2
	StatusDone           // 3
)

const (
	_  = iota
	KB = 1 << (10 * iota) // 1024
	MB                    // 1 << 20
	GB                    // 1 << 30
)

const (
	PermRead   = 1 << iota // 001
	PermWrite              // 010
	PermDelete             // 100
)

perm := PermRead | PermWrite
fmt.Println(perm&PermRead != 0) // true
```

`_ = iota` 可跳过不需要的 0；`1 << iota` 生成 2 的幂，适合位标志；`1 << (10 * iota)` 生成容量单位。Go 没有内置枚举类型，工程上通常配合 `map[int]string` 映射可读名称。

### 6. 基础类型全景

| 类别 | 类型 | 宽度 | 典型用途 |
|------|------|------|---------|
| 布尔 | `bool` | 1 字节 | 开关、状态 |
| 字符串 | `string` | 变长 UTF-8 | 名称、SKU、JSON |
| 有符号整数 | `int` `int8`…`int64` | 平台相关 / 1~8 字节 | 计数、库存、ID |
| 无符号整数 | `uint` `uint8`…`uint64` `uintptr` | 同上 | 位运算、哈希 |
| 浮点 | `float32` `float64` | 4 / 8 字节 | 价格、评分 |
| 别名 | `byte` = `uint8`，`rune` = `int32` | 1 / 4 字节 | 字节流 / 码点 |

工程建议：`int` 宽度与平台相关，跨平台序列化应用 `int64`；金额精确记账用整数"分"，`float64` 只用于展示与统计；`uint` 慎用，`0 - 1` 会回绕成最大值。

### 7. 类型转换与溢出

Go 要求显式转换，窄化转换按补码截断高位，变量整数溢出静默回绕：

```go
var i32 int32 = 5999
var i64 int64 = int64(i32) // 必须显式
// var bad int64 = i32     // 编译错误

var big int32 = 70000
fmt.Println(int16(big)) // 4464

var i8 int8 = 127
i8++ // 变成 -128，不 panic
```

浮点遵循 IEEE 754：溢出得到 `Inf`，`0/0` 得到 `NaN`，`0.1+0.2 == 0.3` 为 `false`。正确比较方式是 `math.Abs(a-b) < 1e-9`；常量溢出则在编译期直接报错。

### 8. strconv：字符串与数值互转

| 函数 | 作用 | 函数 | 作用 |
|------|------|------|------|
| `Atoi` | 字符串 → `int` | `Itoa` | `int` → 字符串 |
| `ParseInt` | → `int64`，可指定进制 | `ParseFloat` | → `float64` |
| `ParseBool` | → `bool` | `FormatFloat` | 浮点 → 字符串 |
| `Quote` | 添加引号与转义 | — | — |

```go
n, err := strconv.Atoi("2024")
if err != nil {
	fmt.Println("解析失败：", err)
}
fmt.Printf("%d %T\n", n, n)
fmt.Println(strconv.Itoa(n + 1))
fmt.Println(strconv.FormatFloat(12345678.9, 'e', 4, 64))
```

`Atoi` 等价于 `ParseInt(s, 10, 0)`。对用户输入必须检查 `error`，不要假设格式正确。

### 9. fmt 格式化动词

| 动词 | 含义 | 动词 | 含义 |
|------|------|------|------|
| `%v` | 默认格式 | `%+v` | 结构体带字段名 |
| `%#v` | Go 语法表示 | `%T` | 类型 |
| `%t` | 布尔 | `%q` | 带引号字符串 |
| `%d` / `%b` / `%x` | 十 / 二 / 十六进制 | `%f` / `%e` | 浮点 / 科学计数 |

```go
fmt.Printf("|%8s|%-8s|%08.2f|\n", "Go", "Go", 3.14159)
item := fmt.Sprintf(`{"sku":%q,"price":%.2f}`, "SKU-1001", 5999.0)
fmt.Println(item)
```

宽度格式为 `%[宽度][.精度][动词]`；`Sprintf` 返回字符串而不是打印，适合组装日志与 JSON 片段；字面量中的 `%` 必须写成 `%%`。

### 10. 与 Python / TypeScript 的差异

| 维度 | Go | Python | TypeScript |
|------|----|--------|-----------|
| 变量声明 | `var` / `:=` | 赋值即声明 | `let` / `const` |
| 类型转换 | 必须显式 | 构造函数 | 较宽松 |
| 空值 | 各类型确定零值 | `None` | `undefined` |

从 Python/TS 转来最容易踩的三个坑：忘记显式转换、声明了变量却没用、在 `if` 块里 `:=` 遮蔽了外层变量。

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/variables.go` | `var` 三种写法、短声明、零值、多重赋值、作用域与遮蔽 |
| `Code/constants_iota.go` | `const` 块、`iota` 枚举、位标志、容量单位、枚举转字符串 |
| `Code/types_conversion.go` | 整数溢出、显式转换、浮点精度、`strconv`、`byte` 与 `rune` |
| `Code/fmt_format.go` | 常用动词、`%+v`/`%#v`/`%T`/`%q`、宽度精度、`Sprintf` 组装 JSON |

```bash
cd "Day02 - 变量、常量与基础类型/Code"
go run variables.go
go run constants_iota.go
go run types_conversion.go
go run fmt_format.go
```

> 同目录多个文件都有 `main` 函数，不要执行 `go run .`。

## 关键知识点总结

1. **三种声明**：`var x T = v`、`var x = v`、`x := v`；短声明仅限函数内。
2. **零值**：数值为 0、布尔为 false、字符串为 `""`、引用类型为 `nil`。
3. **遮蔽**：内层 `:=` 创建新变量，不会修改外层同名变量。
4. **常量**：编译期可求值；无类型常量按上下文适配为不同精度。
5. **iota**：`const` 块内逐行自增，`_` 跳值，`1 << iota` 生成位标志。
6. **整数宽度与溢出**：`int` 与平台相关，跨平台用定长类型；变量溢出静默回绕，常量溢出编译报错。
7. **转换**：Go 无隐式转换，窄化转换截断高位。
8. **strconv**：字符串与数值互转必须检查 `error`。
9. **fmt**：`%v` 调试、`%+v` 看字段名、`%#v` 看完整类型、`%T` 查类型、`%q` 看不可见字符。
10. **金额**：精确记账用整数"分"，展示统计才用 `float64`。

## 实战练习

### 练习 1：商品变量与零值

新建 `product_vars.go`：用三种写法声明商品名、价格、库存、是否在售；再声明未赋值的 `int`、`float64`、`bool`、`string`、`*int`，用一次 `Printf` 输出值与类型。

```text
iPhone 15 5999.00 120 true
零值：0 0.00 false "" <nil>
```

### 练习 2：订单状态枚举

在 `order_status.go` 中用 `iota` 定义五个订单状态，编写 `statusText(code int) (string, bool)` 用 `map[int]string` 映射；遍历 0 到 5，未知状态输出兜底文案；再用位标志表示加急、送礼、需要发票。

```text
4 → 已取消
5 → 未知状态
标记值 5：加急=true 送礼=false 需要发票=true
```

### 练习 3：金额报表

编写 `price_report.go`：用 `Sprintf` 生成左对齐 12 字符、价格右对齐 10 字符、保留两位小数的报表；计算总价并转换为"分"（`int64`）；最后用 `strconv.FormatFloat` 输出科学计数法。

```text
iPhone 15      5999.00
MacBook Pro   12999.00
总价：18998.00 元，合计 1899800 分
```

### 练习 4：JSON 风格字符串

编写 `json_snippet.go`，不使用 `encoding/json`，仅用 `fmt.Sprintf` 生成下文，并用 `%#v` 打印同样字段的结构体作对比。

```json
{"sku":"SKU-1001","name":"iPhone 15","price":5999.00,"stock":120,"on_sale":true}
```
