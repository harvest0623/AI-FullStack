# Day03 - 控制流与函数

## 本章简介

Go 的控制流关键字只有 `if`、`for`、`switch`，没有 `while`、`do-while` 和三元运算符。这种"减法"让代码形态高度一致；`if` 与 `switch` 支持初始化语句，使临时变量的作用域自然收敛到分支内部。

函数是 Go 的基本工作单元：多返回值、命名返回值、可变参数齐全，函数本身也是一等公民，可赋值、传参、返回。闭包因此能封装带状态的行为，`defer` 则把资源清理写在申请资源的下一行。

在 `eshop-gateway` 中，`if err != nil` 早返回、`for range` 遍历商品、`switch` 分发订单状态、多返回值返回"结果 + error"、闭包封装计数器、`defer` 关闭连接，都是本章知识的直接应用。

## 学习目标

- 掌握 `if` 无括号、可带初始化语句的写法与作用域规则
- 熟练使用 `for` 的三种形态：三段式、条件式、无限循环
- 理解 `range` 对切片、Map、字符串的不同返回语义
- 掌握带标签的 `break` / `continue`，能跳出多层嵌套
- 理解 `switch` 自动 `break`、多值匹配与无表达式写法
- 正确使用 `fallthrough`，了解 `type switch` 的用途
- 能定义多返回值函数，遵循"结果 + error"的返回约定
- 掌握命名返回值与裸 `return` 的适用场景
- 会用可变参数 `...T`，理解其本质是切片
- 能把函数作为参数与返回值，编写高阶函数与递归
- 理解闭包捕获，掌握 Go 1.22 的循环变量语义
- 掌握 `defer` 的后进先出顺序与参数注册时求值规则

## 理论知识讲解

### 1. if：无括号与初始化语句

条件不加圆括号，分支必须用大括号；初始化变量只在 `if/else` 内可见，因此错误处理常写成 `if err := f(); err != nil {}`。Go 没有三元运算符，分支赋值直接用 `if`。

```go
if stock := queryStock("SKU-1001"); stock > 0 {
	fmt.Printf("库存 %d\n", stock)
}
```

### 2. for 的三种形态

| 形态 | 写法 | 等价概念 |
|------|------|---------|
| 三段式 | `for i := 0; i < n; i++ {}` | C/Java 的 for |
| 条件式 | `for count > 0 {}` | while |
| 无限循环 | `for {}` | 需自行 break |
| 遍历 | `for k, v := range x {}` | foreach |

```go
for i := 1; i <= 5; i++ { sum += i }

count := 3
for count > 0 { count-- }

for {
	break // 无限循环必须有退出条件
}
```

### 3. range 的返回语义

```go
for i, p := range []float64{5999, 12999} {
	fmt.Println(i, p)
}
for _, p := range prices { // _ 丢弃索引
	fmt.Println(p)
}
```

切片返回索引与元素副本；字符串返回字节偏移与 `rune`；Map 返回键值且顺序随机。切片遍历拿到的是副本，改它不影响原数据。

### 4. 标签 break / continue

默认 `break` 只跳出最内层循环，标签可以指定跳出哪一层：

```go
found:
	for row := 0; row < len(matrix); row++ {
		for col := 0; col < len(matrix[row]); col++ {
			if matrix[row][col] == target {
				break found // 直接跳出两层
			}
		}
	}
```

`continue rowLoop` 同理，表示跳过外层循环的本次迭代。`goto` 语法存在，但业务代码应避免。

### 5. switch：自动 break

匹配成功后自动结束，不需要 `break`，多个值用逗号合并：

```go
switch status {
case "pending":
	fmt.Println("待支付")
case "paid":
	fmt.Println("已支付，准备发货")
case "shipped", "done":
	fmt.Println("已发货或已完成")
default:
	fmt.Println("未知状态")
}
```

`case` 不必是常量，可以是任意可比较表达式，自上而下匹配。

### 6. 无表达式 switch、fallthrough 与 type switch

省略表达式等价于 `switch true`，适合区间判断；`fallthrough` 会强制执行下一个分支：

```go
switch {
case amount >= 99, vip:
	fee = 0
case amount >= 50:
	fee = 5
default:
	fee = 10
}
```

`type switch` 用 `switch v := x.(type)` 判断动态类型，Day06 会系统讲解。`fallthrough` 只能出现在 case 末尾，且不能用于最后一个分支。

### 7. 多返回值与命名返回值

"结果 + error"是 Go 最典型的返回约定：

```go
func applyDiscount(price, rate float64) (float64, float64) {
	discount := price * rate
	return price - discount, discount
}

final, saved := applyDiscount(5999, 0.15)
final, _ := applyDiscount(5999, 0.15) // 忽略优惠金额
```

返回值可以命名，函数内直接赋值，最后裸 `return`；命名返回值便于文档化与 `defer` 修改，但函数较长时建议写显式返回值。

### 8. 可变参数与高阶函数

`...T` 本质是 `[]T`，必须位于参数末尾，传切片时用 `xs...` 展开：

```go
func sumAll(label string, nums ...int) int {
	total := 0
	for _, n := range nums {
		total += n
	}
	return total
}

sumAll("订单金额", 100, 200)
sumAll("展开切片", xs...)
```

函数可作参数与返回值（如 `multiplier(2)` 返回"乘以 2"的函数）；递归必须有终止条件，如 `factorial(n)` 在 `n <= 1` 时返回 1。

### 9. 闭包与循环变量捕获

闭包引用外部变量，只要闭包存活，变量就存活：

```go
func newCounter() func() int {
	count := 0
	return func() int {
		count++
		return count
	}
}

c1, c2 := newCounter(), newCounter()
fmt.Println(c1(), c1(), c2()) // 1 2 1，状态独立
```

闭包捕获变量本身。Go 1.22 起每次迭代创建新的循环变量，因此以下代码输出 `0 1 2`（旧版本为 `2 2 2`）：

```go
funcs := make([]func() int, 0, 3)
for i := 0; i < 3; i++ {
	funcs = append(funcs, func() int { return i })
}
```

### 10. defer 与语言对比

`defer` 在函数返回前执行，多个 `defer` 后进先出；参数在注册时求值：

```go
for i := 1; i <= 3; i++ {
	defer fmt.Printf("第 %d 个\n", i) // 输出 3、2、1
}

price := 100.0
defer fmt.Println(price) // 捕获 100
price = 200.0
```

与 Python/TypeScript 相比：Go 的条件与循环不需要括号、`switch` 自动 break、多返回值是语言级能力、资源清理用 `defer` 而非 `with` 或 `try-finally`。

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/control_flow.go` | `if` 初始化语句、`for` 三种形态、`range`、标签跳转 |
| `Code/functions.go` | 多返回值、命名返回值、可变参数、递归、函数作为参数与返回值 |
| `Code/closures.go` | 闭包计数器、共享状态、Go 1.22 循环变量、`defer` 顺序 |
| `Code/switch_demo.go` | 普通与无表达式 `switch`、`fallthrough`、`type switch` 预览 |

```bash
cd "Day03 - 控制流与函数/Code"
go run control_flow.go
go run functions.go
go run closures.go
go run switch_demo.go
```

> 同目录多个文件都有 `main` 函数，不要执行 `go run .`。

## 关键知识点总结

1. **if 无括号**：条件不加圆括号，分支必须加大括号，初始化变量只在分支内可见。
2. **只有 for**：三段式、条件式、无限循环覆盖全部循环需求。
3. **range 语义**：切片返回索引与元素副本；字符串返回字节偏移与 `rune`；Map 顺序随机。
4. **标签跳转**：`break label` 跳出多层循环，`continue label` 跳过外层本次迭代。
5. **switch 不贯穿**：默认自动结束，多值用逗号合并，`fallthrough` 才进入下一个分支。
6. **无表达式 switch**：等价于 `switch true`，是替代长 `if-else` 链的清晰写法。
7. **多返回值**：典型约定是"结果 + error"，可用 `_` 忽略不关心的值。
8. **命名返回值**：便于文档化与 `defer` 修改，长函数中慎用裸 `return`。
9. **可变参数**：`...T` 本质是 `[]T`，必须在参数末尾，传切片用 `xs...`。
10. **闭包**：捕获变量本身；Go 1.22 起循环变量每次迭代独立。
11. **defer**：后进先出，参数注册时求值，延迟读取最新值需用闭包。

## 实战练习

### 练习 1：订单运费

编写 `order_pricing.go`，用无表达式 `switch` 实现：金额 ≥ 99 或 VIP 免运费，≥ 50 收 5 元，其余 10 元。

```text
订单 30.00 元，运费 10.00 元
订单 60.00 元，运费 5.00 元
订单 120.00 元，运费 0.00 元
VIP 订单 30.00 元，运费 0.00 元
```

### 练习 2：分页与标签跳出

编写 `pagination.go`：23 件商品、每页 5 件，逐页打印区间；用二维切片与标签 `break` 找到第一个包含 `Pro` 的商品并输出行列位置。

```text
共 23 件商品，分 5 页
第 1 页：商品 1-5
第 5 页：商品 21-23
在第 2 个分类的第 1 个位置找到 MacBook Pro
```

### 练习 3：订单统计函数

编写 `order_stats.go`，实现可变参数 `sumAll`、带 error 的 `avg` 与递归 `fib`，并检查 `n <= 0` 的错误分支。

```text
订单合计：3 笔，共 5200.00 元
平均：1733.33 元
斐波那契：0 1 1 2 3 5 8 13 21 34
空订单平均值错误：订单数量必须大于 0
```

### 练习 4：闭包购物车

编写 `cart_closure.go`：用闭包维护购物车与总价，添加 3 件商品；用 `defer` 按后进先出打印清理日志，并输出退出时的最终总价。

```text
加入 iPhone 15：5999.00
加入 AirPods：899.00
加入 iPad：3499.00
购物车合计：10397.00
退出时总价：10397.00
清理：关闭日志
```
