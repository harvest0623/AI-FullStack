# Day08 - 泛型与标准库

## 本章简介

Go 1.18 引入泛型，终于可以在不牺牲类型安全的前提下编写"适用于多种类型"的代码。在此之前，通用容器只能基于 `any` + 类型断言，或者为每种类型复制一遍逻辑。泛型让 `Map/Filter/Reduce`、`Stack[T]`、通用分页结果这类代码只需写一次，同时保留编译期检查。本章会讲清类型参数、类型约束、`~` 底层类型、联合约束，以及"什么时候泛型反而不值得用"。

与此同时，标准库本身也在持续进化：`slices` 与 `maps` 包提供了排序、查找、去重、克隆等泛型工具；内置的 `min` / `max` 取代了大量手写比较；`time` 包负责时间解析、时长运算与定时器；`log/slog` 提供结构化日志，是服务可观测性的基础。这些是 `eshop-gateway` 日常开发中使用频率最高的 API。

在项目中的位置：Day06 定义了 `Product`、`Order` 等领域模型，本章用泛型实现通用的 `Paginate[T]`、`Stack[T]` 与集合工具，用 `slices.SortFunc` 对商品按销量排序，用 `time` 控制上游 LLM 调用超时，用 `slog` 输出结构化访问日志。Day09 的并发与 Day11 的 HTTP 服务都会直接复用这些能力。

## 学习目标

- 理解泛型解决的核心问题：在保持类型安全的同时复用代码
- 掌握类型参数声明 `<T any>` 与类型约束的基本语法
- 能编写泛型函数 `Map` / `Filter` / `Reduce` 并理解类型推断
- 能定义泛型类型 `Stack[T]` 并为它编写方法
- 理解 Go 不支持方法自有类型参数这一限制及其影响
- 掌握 `any`、`comparable` 与 `~` 底层类型约束的差异
- 能用联合约束（`~int | ~float64`）与自定义 `Number` 约束
- 明确泛型的使用边界，知道何时应该回到接口或具体类型
- 熟练使用 `slices` 包：`Sort` / `SortFunc` / `Contains` / `Index` / `Compact` / `Clone` / `Reverse`
- 会用 `maps` 包的 `Keys` / `Values` 与内置 `min` / `max`
- 掌握 `time.Now` / `Format` / `Parse` / `Duration` / `Add` / `Sub` 与定时器
- 能用 `select` + `time.After` 实现超时，并用 `slog` 输出结构化日志

## 理论知识讲解

### 1. 泛型解决什么问题

没有泛型时，写一个"取切片第一个元素"的函数有两种做法：

```go
// 方案 A：为每种类型复制一份，代码重复
func FirstInt(items []int) int     { return items[0] }
func FirstString(items []string) string { return items[0] }

// 方案 B：用 any，丢失类型信息，调用方必须断言
func First(items []any) any { return items[0] }
```

泛型把"类型"变成参数：

```go
func First[T any](items []T) T { return items[0] }

n := First([]int{1, 2, 3})        // T 推断为 int
s := First([]string{"a", "b"})    // T 推断为 string
```

| 方案 | 类型安全 | 代码复用 | 运行时开销 |
|------|---------|---------|-----------|
| 复制多份 | 强 | 差 | 无 |
| `any` + 断言 | 弱 | 好 | 断言开销 |
| 泛型 | 强 | 好 | 编译期特化，几乎为零 |

### 2. 类型参数与类型约束

泛型函数在函数名后声明类型参数列表，每个参数都带约束：

```go
func Map[T, R any](items []T, fn func(T) R) []R {
	out := make([]R, 0, len(items))
	for _, it := range items {
		out = append(out, fn(it))
	}
	return out
}
```

- `T`、`R` 是类型参数，只在函数签名与函数体内可见
- `any` 是约束，表示"任意类型"，此时不能对值做 `==` 或算术
- 调用时通常无需显式指定，编译器可从实参推断

```go
names := Map(products, func(p Product) string { return p.Name }) // 自动推断 T=Product, R=string
```

约束本质上是一个**类型集合**：只有属于该集合的类型才能作为类型参数。

### 3. `any`、`comparable` 与 `~` 底层类型

| 约束 | 类型集合 | 能做什么 |
|------|---------|---------|
| `any` | 所有类型 | 只能赋值、传参、取地址 |
| `comparable` | 可比较类型 | 可用 `==`、`!=`，可作为 Map 键 |
| `~int` | 底层类型为 `int` 的所有类型 | 支持整数运算 |
| `int` | 仅 `int` 本身 | 支持整数运算，但不接受自定义类型 |

`~` 是关键：`type OrderID int` 的底层类型是 `int`，但 `OrderID` **不是** `int`。若约束写成 `int`，`Sum([]OrderID{...})` 无法编译；写成 `~int` 则可以。

```go
type OrderID int

func Sum[T ~int](nums []T) T { ... }

Sum([]int{1, 2})            // OK
Sum([]OrderID{1001, 1002})  // OK，底层类型是 int
```

### 4. 联合约束与自定义约束

多个类型可以用 `|` 组成联合约束，并抽成命名约束复用：

```go
type Number interface {
	~int | ~int64 | ~float32 | ~float64
}

func Sum[T Number](nums []T) T {
	var total T
	for _, n := range nums {
		total += n
	}
	return total
}

func Avg[T Number](nums []T) float64 {
	return float64(Sum(nums)) / float64(len(nums))
}
```

注意点：

- 联合中的每个成员都必须支持约束体内用到的运算（`+`、`<` 等）
- 类型参数值可以转换到联合中所有成员都能转到的目标类型，因此 `float64(x)` 合法
- 约束不能包含方法以外无法满足的条件；`comparable` 常与联合组合

```go
type Key interface {
	comparable
	~string | ~int64
}
```

### 5. 泛型类型与"泛型方法"的限制

泛型类型在类型名后声明参数，方法沿用类型的参数：

```go
type Stack[T any] struct {
	items []T
}

func (s *Stack[T]) Push(v T)          { s.items = append(s.items, v) }
func (s *Stack[T]) Pop() (T, bool)    { ... }
func (s *Stack[T]) Size() int         { return len(s.items) }
```

**Go 不支持方法自有的类型参数**，下面这种写法无法编译：

```go
// func (s *Stack[T]) MapTo[R any](fn func(T) R) []R { ... } // 编译错误
```

如果需要"在方法上引入新类型参数"，标准做法是改成普通泛型函数：

```go
func MapStack[T, R any](s *Stack[T], fn func(T) R) []R { ... }
```

| 能力 | 泛型函数 | 泛型类型 |
|------|---------|---------|
| 声明类型参数 | 支持 | 支持 |
| 方法引入新的类型参数 | 不支持 | 不支持 |
| 类型推断 | 调用时推断 | 构造时推断 |

### 6. 类型推断与使用边界

类型推断可以从实参与返回值上下文推导参数，但不会"猜"约束之外的东西：

```go
Map(products, func(p Product) string { return p.Name }) // 推断成功
Reduce(products, 0.0, func(acc float64, p Product) float64 { ... }) // A 推断为 float64
```

推断失败时可以显式指定部分或全部类型实参：

```go
nums := Map[Product, int](products, func(p Product) int { return p.Stock })
```

| 适合用泛型 | 不适合用泛型 |
|-----------|-------------|
| 容器：Stack、Queue、Set | 只有一两种具体类型 |
| 集合算法：Map/Filter/Reduce | 逻辑依赖具体字段（如按 Price 排序） |
| 通用结果包装：`Result[T]` | 需要运行时类型判断 |
| 避免 `any` 断言的工具函数 | 会显著降低可读性的复杂约束 |

> Go 社区的共识是"**先写具体类型，出现第三次重复再抽象**"。泛型是工具，不是目标；过度泛型化的代码往往比重复代码更难读。

### 7. `slices` 与 `maps`：泛型标准库

Go 1.21 起标准库提供了 `slices` 与 `maps`，覆盖最常见的集合操作：

| 函数 | 作用 | 是否修改原切片 |
|------|------|--------------|
| `slices.Sort(s)` | 升序排序 | 是（原地） |
| `slices.SortFunc(s, cmp)` | 自定义比较器排序 | 是 |
| `slices.Contains(s, v)` | 是否包含 | 否 |
| `slices.Index(s, v)` | 首次出现的下标，找不到为 -1 | 否 |
| `slices.Compact(s)` | 去除**相邻**重复元素 | 是 |
| `slices.Clone(s)` | 浅拷贝新切片 | 否 |
| `slices.Reverse(s)` | 原地反转 | 是 |
| `slices.Min` / `slices.Max` | 最小/最大值 | 否 |

```go
slices.SortFunc(products, func(a, b Product) int {
	return cmp.Compare(b.Price, a.Price) // 价格降序
})
```

比较器返回负数表示 `a` 在前，正数表示 `b` 在前，0 表示相等。`slices.Compact` 只去除相邻重复，**去重前必须先排序**。

`maps` 包提供 `Clone`、`Equal`、`Copy` 等工具。需要注意 `maps.Keys` / `maps.Values` 在 Go 1.23 起返回迭代器 `iter.Seq`，与 1.22 的切片返回不兼容。为了保持 1.22 基准，本教程采用手动收集键再排序的写法：

```go
keys := make([]string, 0, len(stock))
for sku := range stock {
	keys = append(keys, sku)
}
slices.Sort(keys)
```

> 若使用 Go 1.23+，可以写成 `for sku := range maps.Keys(stock) { ... }`；跨版本库代码建议避免直接依赖该 API。

### 8. 内置 `min` / `max`

Go 1.21 把 `min`、`max` 提升为内置函数，支持有序类型与可变参数：

```go
fmt.Println(min(3, 8, 1)) // 1
fmt.Println(max(3, 8, 1)) // 8
fmt.Println(min(2.5, 1.5)) // 1.5
```

| 写法 | 说明 |
|------|------|
| `min(a, b, c)` | 多个参数取最小 |
| `max(a, b)` | 两个参数取最大 |
| `slices.Max(nums)` | 切片最大，空切片会 panic |

内置 `min/max` 只接受**有序类型**（整数、浮点、字符串），不支持自定义结构体；需要按字段比较时用 `slices.MaxFunc`。

### 9. `time`：时间、时长与定时器

Go 的时间格式化不使用 `yyyy-MM-dd`，而是用一个**固定参考时间**表示布局：

```go
now := time.Now()
now.Format("2006-01-02 15:04:05") // 参考时间：2006-01-02 15:04:05
now.Format(time.RFC3339)          // 2006-01-02T15:04:05Z07:00
```

| 布局片段 | 含义 |
|---------|------|
| `2006` / `06` | 四位/两位年份 |
| `01` / `1` | 两位/一位月份 |
| `02` / `2` | 两位/一位日期 |
| `15` / `03` | 24 小时制 / 12 小时制 |
| `04` / `05` | 分 / 秒 |
| `MST` / `-0700` | 时区名 / 时区偏移 |

时长用 `time.Duration`（`int64` 纳秒）：

```go
d := 1500 * time.Millisecond
fmt.Println(d, d.Seconds(), d.Milliseconds()) // 1.5s 1.5 1500

deadline := now.Add(30 * time.Minute)
fmt.Println(time.Until(deadline)) // 距离截止还有多久
fmt.Println(time.Since(now))      // 从某时刻到现在
```

| API | 用途 | 注意事项 |
|-----|------|---------|
| `time.NewTimer(d)` | 单次定时 | 触发一次后即失效 |
| `time.NewTicker(d)` | 周期定时 | 必须 `Stop()`，否则泄漏 |
| `time.After(d)` | 一次性通道 | 高频调用会积累定时器 |
| `time.Sleep(d)` | 阻塞当前 goroutine | 无法被 context 取消 |

### 10. 超时模式与 `log/slog`

给"可能很慢的上游调用"加时限，标准写法是 `select` 两个通道：

```go
select {
case reply := <-done:
	return reply, nil
case <-time.After(timeout):
	return "", fmt.Errorf("上游调用超时（%s）", timeout)
}
```

`log/slog` 是 Go 1.21 引入的结构化日志包，输出键值对，便于日志系统检索：

```go
logger := slog.New(slog.NewTextHandler(os.Stdout, nil))
logger.Info("订单创建", "order_id", "ORD-001", "amount", 899)
// time=... level=INFO msg="订单创建" order_id=ORD-001 amount=899

jsonLogger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
jsonLogger.Warn("库存偏低", "sku", "SKU-1001", "stock", 3)
```

| 对比 | `log` | `log/slog` |
|------|-------|-----------|
| 输出格式 | 纯文本 | 文本 / JSON 可切换 |
| 字段 | 需自己拼 | 原生键值对 |
| 级别 | 无 | Debug/Info/Warn/Error |
| 适用场景 | 脚本、调试 | 线上服务、日志采集 |

> 生产环境推荐 JSON handler，并统一字段名（如 `request_id`、`latency_ms`、`upstream`），这样日志平台才能按字段聚合与告警。

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/generics.go` | 泛型 `Map` / `Filter` / `Reduce`、泛型 `Stack[T]`、类型推断 |
| `Code/generics_constraints.go` | `any` / `comparable` / `~int`、联合约束、自定义 `Number` 约束 |
| `Code/stdlib_slices.go` | `slices` 排序/查找/去重/克隆/反转、Map 键收集与排序、`maps.Clone/Equal`、内置 `min/max` |
| `Code/stdlib_time.go` | 时间格式化与解析、`Duration`、Timer/Ticker、超时模式、`slog` |

执行方式（每个文件独立运行）：

```bash
cd "Day08 - 泛型与标准库/Code"
go run generics.go
go run generics_constraints.go
go run stdlib_slices.go
go run stdlib_time.go
```

> 示例采用 Go 1.22 兼容写法；Go 1.23+ 可用迭代器形式的 `maps.Keys` / `maps.Values`。

## 关键知识点总结

1. **泛型三要素**：类型参数、类型约束、类型推断；目标是复用代码同时保留类型安全。
2. **约束即类型集合**：`any` 最大但能力最少，`comparable` 支持 `==`，`~T` 接受底层类型为 `T` 的自定义类型。
3. **联合约束**：用 `|` 组合多种底层类型，可抽成 `Number` 这样的命名约束复用。
4. **泛型类型**：`Stack[T]` 的方法共享类型参数；Go 不允许方法自带新的类型参数。
5. **类型推断**：多数调用无需显式写 `[T]`，推断失败时再手动指定。
6. **泛型边界**：重复出现三次以上再抽象；依赖具体字段的逻辑优先用 `SortFunc` 等回调。
7. **`slices` 常用**：`Sort`/`SortFunc`/`Contains`/`Index`/`Compact`/`Clone`/`Reverse`。
8. **`Compact` 前提**：只去相邻重复，先去重必须先排序；`Clone` 是浅拷贝。
9. **Map 键排序**：先手动收集键到切片，再用 `slices.Sort`；1.23 的 `maps.Keys` 返回迭代器，跨版本代码慎用。
10. **时间布局**：用参考时间 `2006-01-02 15:04:05` 表达格式，不是 `yyyy-MM-dd`。
11. **定时器必停**：`Ticker.Stop()` 不可遗漏；超时用 `select` + `time.After`。
12. **结构化日志**：`slog` 输出键值对，生产建议 JSON handler 并统一字段名。

## 实战练习

### 练习 1：通用分页结果

定义泛型类型 `Page[T any]`，字段包括 `Items []T`、`Total int`、`Page int`、`Size int`，并实现：

1. `NewPage[T any](items []T, page, size int) Page[T]`，处理越界与空切片
2. 方法 `TotalPages() int` 与 `HasNext() bool`
3. 用 `Page[Product]` 与 `Page[string]` 各构造一个实例，验证同一份代码可服务不同领域类型
4. 思考：为什么 `Page[T]` 的方法不能写成 `func (p Page[T]) Convert[R any]() Page[R]`？

### 练习 2：商品排序与去重

在 `stdlib_slices.go` 基础上：

1. 用 `slices.SortFunc` 实现按"销量降序、价格升序"的二级排序
2. 对 SKU 列表先 `Sort` 再 `Compact`，对比不排序直接 `Compact` 的结果差异
3. 用 `slices.Clone` 保留原始顺序，验证排序不影响副本
4. 用 `slices.IndexFunc` 查找第一个库存为 0 的商品，找不到时返回 -1

### 练习 3：仓储泛型约束

定义约束 `type SKU interface { ~string }` 与泛型函数 `IndexBySKU[T SKU](items []T, target T) int`：

1. 用 `string` 与自定义类型 `type ProductCode string` 分别调用，验证 `~` 的作用
2. 把约束改成 `string`（去掉 `~`），观察自定义类型调用时的编译错误
3. 总结 `any`、`comparable`、`~string` 三者在"能否比较"和"能否接受自定义类型"上的区别

### 练习 4：上游超时与结构化日志

在 `stdlib_time.go` 基础上：

1. 写 `CallLLM(prompt string, timeout time.Duration) (string, error)`，用 goroutine 模拟 120ms 的模型响应
2. 分别用 50ms 与 200ms 超时调用，记录返回结果与耗时
3. 用 `slog.NewJSONHandler` 输出一条包含 `request_id`、`prompt_len`、`latency_ms`、`timeout` 的日志
4. 把 `time.After` 换成可复用的 `time.NewTimer`，说明在高频调用下为什么更可控
