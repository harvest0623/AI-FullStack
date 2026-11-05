# Day05 - 字符串、指针与内存

## 本章简介

字符串是业务代码中出现最多的类型，也是 Go 初学者最容易误判的类型。Go 的字符串是**不可变的字节序列**，采用 UTF-8 编码：`len(s)` 返回字节数而不是字符数，`s[i]` 取到的是字节而不是字符，只有 `for range` 才会按 `rune` 解码。一个中文字符通常占 3 个字节，这直接影响截断、分页、字数统计与数据库字段设计。

指针是 Go 保留的底层能力，但被刻意简化：只有 `&` 取地址与 `*` 解引用，**没有指针运算**，也不能做类型双关。指针的价值只有两件事：让函数修改调用方的数据，以及避免复制大对象。理解值传递与指针传递的边界，是写出正确且高效 Go 代码的关键。

内存部分会解释 `new` 与 `make` 的分工、结构体拷贝的深浅语义、逃逸分析如何决定变量分配在栈还是堆，以及 GC 的基本工作方式。在 `eshop-gateway` 中，标题清洗、SKU 解析、限流计数器的共享状态、请求结构体的传递方式，都依赖本章知识。

## 学习目标

- 理解字符串的不可变性与 UTF-8 编码模型
- 区分 `len` 的字节数与 `utf8.RuneCountInString` 的字符数
- 掌握 `[]byte` 与 `[]rune` 的转换及各自适用场景
- 能用 `for range` 正确遍历中文并按字符截取
- 熟练使用 `strings` 包的裁剪、分割、拼接、替换、前后缀判断
- 会用 `strings.Builder` 高效拼接大量字符串
- 掌握 `&` 取地址与 `*` 解引用，理解 Go 没有指针运算
- 能解释值传递与指针传递对调用方数据的影响
- 掌握结构体指针的字段访问与 `nil` 指针的防御性判断
- 区分 `new(T)` 与 `make(T, ...)` 的返回值与适用类型
- 理解逃逸分析的基本规则，知道何时变量会分配到堆
- 了解 GC 三色标记与内存对齐对性能的影响

## 理论知识讲解

### 1. 字符串不可变与 UTF-8

`string` 是只读的字节序列，底层由"数据指针 + 长度"描述。任何"修改"都会生成新字符串：

```go
s := "eshop"
// s[0] = 'E' // 编译错误：cannot assign to s[0]
upper := "E" + s[1:] // 生成新字符串
```

不可变带来两个好处：字符串可在多个 goroutine 间安全共享，作为 Map 键时哈希值可缓存；代价是频繁拼接会产生大量临时对象。Go 源文件与字符串字面量默认都是 UTF-8：`"电"` 是 `E7 94 B5` 三个字节。

### 2. len 返回字节数

| 表达式 | 结果 | 含义 |
|--------|------|------|
| `len("eshop")` | 5 | ASCII 每字符 1 字节 |
| `len("商品")` | 6 | 中文每字符 3 字节 |
| `len([]rune("商品"))` | 2 | 码点个数 |
| `utf8.RuneCountInString("商品")` | 2 | 码点个数，无额外分配 |

```go
cn := "商品"
fmt.Println(len(cn), utf8.RuneCountInString(cn)) // 6 2
```

业务影响：数据库 `VARCHAR(20)` 通常按字符计数，直接用 `len` 校验中文长度会误判，应使用 `utf8.RuneCountInString`。

### 3. rune、byte 与 range

`rune` 是 `int32` 的别名，表示 Unicode 码点；`byte` 是 `uint8` 的别名，表示一个字节。

```go
for i, r := range "电商 eshop" {
	fmt.Println(i, r) // i 是字节偏移，r 是 rune
}

b := []byte("商品") // 6 个字节
r := []rune("商品") // 2 个码点
fmt.Println(string(b), string(r))
```

按下标 `for i := 0; i < len(s); i++` 遍历拿到的是字节，切分中文会产生乱码。`[]byte` 适合网络传输、文件写入、哈希；`[]rune` 适合按字符截取、字数统计。

### 4. strings 常用函数

| 函数 | 作用 | 函数 | 作用 |
|------|------|------|------|
| `TrimSpace` | 去首尾空白 | `Trim` | 去指定字符 |
| `HasPrefix` | 前缀判断 | `HasSuffix` | 后缀判断 |
| `Contains` | 子串判断 | `Index` | 子串位置，找不到为 -1 |
| `Split` | 分割为切片 | `Join` | 拼接切片 |
| `ReplaceAll` | 全部替换 | `Repeat` | 重复字符串 |
| `Fields` | 按空白分词 | `ToLower` | 转小写 |

```go
raw := "  eshop-gateway  "
clean := strings.TrimSpace(raw)
parts := strings.Split("SKU-1001-手机", "-")
fmt.Println(clean, parts, strings.Join(parts, "/"))
```

这些函数都返回新字符串，不会修改原值。

### 5. strings.Builder 高效拼接

字符串不可变，`s += x` 每次都会分配新内存并复制旧内容，循环中的复杂度是 O(n²)。`Builder` 内部维护可增长的 `[]byte`，追加是摊还 O(1)：

```go
var b strings.Builder
b.WriteString("商品：")
fmt.Fprintf(&b, "%s，价格 %.2f", "iPhone 15", 5999.0)
fmt.Println(b.String())
```

| 方式 | 复杂度 | 适用场景 |
|------|--------|---------|
| `+` / `+=` | O(n²) | 少量、确定次数的拼接 |
| `strings.Join` | O(n) | 已有切片，一次性拼接 |
| `strings.Builder` | 摊还 O(n) | 循环内大量追加 |

`Builder` 不能复制，`String()` 之后不要再写入。

### 6. 指针基础：& 与 *

```go
stock := 120
p := &stock     // & 取地址，类型 *int
fmt.Println(*p) // * 解引用：120
*p = 80         // 等价于 stock = 80
```

Go 的指针是类型安全的，并且**没有指针运算**：不能 `p++`，也不能把 `*int` 强转为 `*float64`。指针零值是 `nil`，解引用 nil 会 panic，访问前必须判断。

### 7. 值传递与指针传递

Go 只有值传递：参数永远是副本。"指针传递"传递的是地址的副本，通过它可以修改原变量。

```go
func discountByValue(p Product)   { p.Price *= 0.8 } // 改副本，无效
func discountByPointer(p *Product) { p.Price *= 0.8 } // 改原对象
```

| 传递方式 | 复制内容 | 能否修改调用方 | 适用场景 |
|---------|---------|--------------|---------|
| 值传递 | 整个值 | 否 | 小结构体、值语义 |
| 指针传递 | 一个地址 | 是 | 大结构体、需修改 |
| 切片 / Map | 描述符 | 元素可改，重新赋值不可见 | 集合数据 |

切片虽然按值传递，但内部指针指向同一底层数组，修改元素对调用方可见；若函数内 `append` 扩容，调用方的长度不会改变。

### 8. 结构体指针与 nil

Go 允许用指针直接访问字段，编译器自动解引用：

```go
p := &Product{Name: "iPhone 15", Price: 5999}
p.Price = 5499 // 等价于 (*p).Price

var np *Product
if np != nil {
	fmt.Println(np.Name) // 防御性判断，避免 panic
}
```

需要修改状态或结构体较大时用指针接收者；需要值语义或结构体很小时用值接收者，Day06 会展开。

### 9. new 与 make

| 表达式 | 返回类型 | 作用 | 适用类型 |
|--------|---------|------|---------|
| `new(T)` | `*T` | 分配零值并返回指针 | 任意类型 |
| `make([]T, len, cap)` | `[]T` | 初始化切片底层数组 | 切片 |
| `make(map[K]V)` | `map[K]V` | 初始化哈希表 | Map |
| `make(chan T, n)` | `chan T` | 初始化通道 | Channel |

```go
p := new(int) // *int，指向 0
*p = 42
nums := make([]int, 3, 5) // 切片本身，不是指针
m := make(map[string]int) // 可直接写入
```

`new` 在业务代码中很少用，结构体字面量 `&Product{...}` 更直观；`make` 则是切片、Map、Channel 的必需初始化手段。

### 10. 逃逸分析与 GC

编译器通过**逃逸分析**决定变量分配在栈还是堆：只在函数内使用、生命周期不超过函数 → 栈；被返回指针引用、被闭包捕获、装箱到接口 → 堆。

```go
func newProduct(name string) *Order {
	o := Order{Name: name}
	return &o // 取局部变量地址返回，o 逃逸到堆
}
```

```bash
go build -gcflags="-m" main.go
# ./main.go:10:2: moved to heap: o
```

常见逃逸原因：返回局部变量指针、闭包捕获、装箱到接口、切片容量在编译期不确定。高频路径应避免不必要的闭包与接口装箱。

GC 采用**并发三色标记清除**：从根对象标记可达对象，白色对象被回收；标记与用户代码并发，用写屏障保证正确性。`GOGC` 控制触发阈值（默认 100，即堆增长一倍触发一次）。内存对齐方面，把大字段放前面、相同大小字段聚在一起，通常能减少填充。

### 11. 与 Python / TypeScript 对比

| 维度 | Go | Python | TypeScript |
|------|----|--------|-----------|
| 字符串 | 不可变 UTF-8 字节序列 | 不可变码点序列 | 不可变 UTF-16 |
| `len` 语义 | 字节数 | 字符数 | UTF-16 码元数 |
| 参数传递 | 值传递 | 对象引用 | 对象引用 |
| 内存管理 | 栈/堆 + 三色 GC | 引用计数 | 引擎 GC |

最大的认知冲击是：`len("中文")` 不是 2 而是 6；切片传参后 `append` 不会改变调用方长度。

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/strings_demo.go` | 字符串不可变、`len` 字节数、`strings` 常用函数与 `Builder` |
| `Code/runes_utf8.go` | UTF-8 字节、`[]byte` 与 `[]rune`、中文遍历、`utf8` 计数 |
| `Code/pointers.go` | `&` 与 `*`、指针交换、结构体指针、`nil` 指针、无指针运算 |
| `Code/memory_demo.go` | 值传递与指针传递、`new` 与 `make`、结构体拷贝、逃逸分析 |

```bash
cd "Day05 - 字符串、指针与内存/Code"
go run strings_demo.go
go run runes_utf8.go
go run pointers.go
go run memory_demo.go
```

> 同目录多个文件都有 `main` 函数，不要执行 `go run .`。

## 关键知识点总结

1. **字符串不可变**：底层是只读字节序列，任何修改都产生新字符串。
2. **len 是字节数**：ASCII 1 字节，中文通常 3 字节；字符数用 `utf8.RuneCountInString`。
3. **rune 与 byte**：`rune` 是 `int32` 码点，`byte` 是 `uint8` 字节。
4. **range 解码**：遍历字符串按 UTF-8 解码，返回字节偏移与 `rune`。
5. **strings 工具**：`TrimSpace`、`Split`、`Join`、`HasPrefix`、`ReplaceAll` 覆盖大部分文本清洗。
6. **Builder**：循环内大量拼接用 `strings.Builder`，避免 O(n²) 复制。
7. **指针操作**：`&` 取地址、`*` 解引用，类型安全且无指针运算。
8. **只有值传递**：指针传递也是复制地址；切片可改元素但 `append` 不影响调用方长度。
9. **new vs make**：`new(T)` 返回 `*T`；`make` 用于切片、Map、Channel。
10. **逃逸分析**：返回局部指针、闭包捕获、装箱到接口通常导致变量分配到堆。
11. **GC 与对齐**：三色标记并发回收；结构体字段顺序影响填充。

## 实战练习

### 练习 1：商品标题清洗

编写 `title_clean.go`，输入 `"  【限时】iPhone 15 Pro MAX 256G  "`：去空白、去前缀 `【限时】`、生成小写搜索标题，输出字节数与字符数，并用 `strings.Fields` 统计单词数。

```text
清洗后：iPhone 15 Pro MAX 256G
小写：iphone 15 pro max 256g
字节数：22，字符数：22，单词数：5
```

### 练习 2：SKU 解析与字符截取

编写 `sku_parse.go`，输入 `"SKU-1001-手机-黑色"`：用 `Split` 拆出四段；用 `[]rune` 安全截取分类首字；用 `[]byte` 截取前 8 字节并用 `utf8.Valid` 校验；输出整串字符数。

```text
前缀=SKU 编号=1001 分类=手机 颜色=黑色
分类首字：手
前 8 字节："SKU-1001" 合法=true
字符数：12
```

### 练习 3：指针修改库存

编写 `stock_pointer.go`：定义 `Product`，实现 `deduct(p *Product, n int) error` 与 `applyDiscount(p *Product, rate float64)`；再写一个值传递版本证明无法修改原对象；演示 `nil` 指针判断。

```text
扣减 30 后库存：90
折后价格：5099.15
值传递无法修改：库存仍为 90
nil 指针已拦截
```

### 练习 4：值传递、指针传递与逃逸观察

编写 `memory_escape.go`：定义含 `[1024]int` 的大结构体，分别用值传递与指针传递求和并计时；实现 `newOrder() *Order` 返回局部指针；用 `new(int)` 与 `make([]int, 3, 5)` 对比。最后执行 `go build -gcflags="-m" memory_escape.go` 记录逃逸结果。

```text
值传递耗时：约 1.2ms，指针传递耗时：约 0.05ms
new(int) 值：42
make 切片：len=3 cap=5
逃逸分析：newOrder 中的 o 被移动到堆
```
