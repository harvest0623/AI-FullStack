# Day04 - 数组、切片与 Map

## 本章简介

数组、切片与 Map 是 Go 最常用的三种复合类型，也是初学者最容易误解的地方。数组是**值类型**且长度是类型的一部分；切片不是数组，而是一个包含"指针、长度、容量"三要素的描述符；Map 是哈希表，遍历顺序被刻意设计为随机。理解底层结构，才能解释"为什么改了一个切片，另一个也跟着变"。

切片是 Go 出场率最高的数据结构：HTTP 请求体、JSON 数组、查询结果、日志缓冲几乎都以 `[]T` 出现。共享与扩容既带来零拷贝的高性能，也埋下"修改联动"的陷阱；Map 则承担去重、索引与聚合统计。

在 `eshop-gateway` 中，商品列表用切片承载，SKU 索引用 Map 建立，分类聚合用嵌套 Map 完成。Day06 的结构体切片、Day10 的 JSON 数组、Day13 的批量去重，都建立在本章之上。

## 学习目标

- 理解数组是值类型，赋值与传参都会完整复制
- 掌握"长度是数组类型的一部分"这一规则
- 会用 `==` 比较元素可比较、长度相同的数组
- 掌握切片的三个要素：底层数组指针、长度、容量
- 会用 `copy` 复制切片并切断与原切片的关联
- 掌握三索引切片 `[low:high:max]` 限制容量的作用
- 能解释共享底层数组的修改联动与扩容后的脱钩
- 区分 `nil` 切片与空切片，知道何时用哪一种
- 掌握 Map 的增删改查、`comma-ok` 与 `delete`
- 理解 Map 遍历随机，会用 Map 实现集合与嵌套聚合

## 理论知识讲解

### 1. 数组：值语义与长度属于类型

长度在声明时确定，**长度是类型的一部分**，`[3]int` 与 `[4]int` 互不兼容；赋值、传参、返回都会复制整个数组，因此大数组传参代价很高。

```go
var zeros [3]int             // [0 0 0]
auto := [...]int{10, 20, 30} // 推断长度为 3

original := [3]int{1, 2, 3}
copied := original
copied[0] = 100
fmt.Println(original) // [1 2 3]，不受影响
```

| 操作 | 数组 | 切片 |
|------|------|------|
| 赋值 | 复制全部元素 | 复制描述符，共享底层数组 |
| 比较 | 长度相同即可 `==` | 只能与 `nil` 比较 |

### 2. 数组比较、遍历与二维数组

元素可比较、长度相同的数组可以直接用 `==` 逐元素比较；`range` 返回索引与**元素副本**。二维数组的两个维度都必须是常量，`[2][3]int` 与 `[3][2]int` 不同：

```go
a, b := [3]int{1, 2, 3}, [3]int{1, 2, 3}
fmt.Println(a == b) // true

for i, p := range [3]float64{5999, 12999, 899} {
	fmt.Println(i, p)
}

grid := [2][3]int{{1, 2, 3}, {4, 5, 6}}
for _, row := range grid {
	fmt.Println(row) // [1 2 3] 与 [4 5 6]
}
```

### 3. 切片三要素

切片运行时是一个结构体：指针指向底层数组起始元素，`len` 是当前可访问元素个数，`cap` 是从起点到底层数组末尾的空间。切片按值传递时复制的只是这三个字段，但**底层数组仍是同一块内存**，这是所有"联动修改"的根源。

```go
nums := []int{10, 20, 30, 40, 50} // len=5 cap=5
view := nums[1:3]                 // len=2 cap=4，指针指向 20
fmt.Println(len(view), cap(view))
```

### 4. make、字面量与 nil

| 创建方式 | 写法 | 结果 |
|---------|------|------|
| 字面量 | `[]int{1, 2, 3}` | len=3 cap=3 |
| `make` 指定长度 | `make([]int, 3)` | len=3 cap=3，元素为零值 |
| `make` 长度与容量 | `make([]int, 2, 5)` | len=2 cap=5 |
| 仅声明 | `var s []int` | nil 切片，len=0 cap=0 |

`make` 只用于切片、Map、Channel；数组用 `new` 或直接声明。

### 5. append、扩容与 len/cap

容量足够时 `append` 直接写入底层数组；容量不足时**分配新数组、复制旧元素、返回新切片**，因此必须接收返回值：

```go
list = append(list, 4) // 正确
// append(list, 4)     // 编译错误：返回值被丢弃

var grow []int
for i := 1; i <= 6; i++ {
	grow = append(grow, i)
	fmt.Println(len(grow), cap(grow)) // 1/1 2/2 3/4 4/4 5/8 6/8
}
```

扩容策略大致是小切片倍增、大切片约 1.25 倍。扩容后新切片拥有独立数组；未扩容的 append 会写入共享数组，可能覆盖其他切片看到的内容。

### 6. copy、区间切片与三索引切片

`copy(dst, src)` 复制的个数是 `min(len(dst), len(src))`，不会自动扩容；`s[low:high]` 左闭右开并共享底层数组；三索引 `s[low:high:max]` 把容量限制为 `max-low`：

```go
src := []string{"iPhone 15", "MacBook Pro"}
dst := make([]string, len(src))
n := copy(dst, src) // n = 2，dst 与 src 独立

nums := []int{10, 20, 30, 40, 50}
limited := nums[1:3:3] // len=2 cap=2
limited = append(limited, 999)
fmt.Println(nums) // [10 20 30 40 50]，未被覆盖
```

| 写法 | len | cap |
|------|-----|-----|
| `nums[1:3]` | 2 | 4 |
| `nums[1:3:3]` | 2 | 2 |
| `nums[:0]` | 0 | 5 |

三索引切片的用途是把子切片的"可写窗口"限制住，防止后续 `append` 意外覆盖原数据。

### 7. 共享底层数组与脱钩

```go
base := []int{1, 2, 3, 4, 5}
view := base[1:4]
view[0] = 20
fmt.Println(base) // [1 20 3 4 5]，base 被改了
```

更隐蔽的是 `append` 未扩容时写入共享数组：

```go
s1 := make([]int, 2, 4) // len=2 cap=4
s2 := append(s1, 3)     // 写入 s1 之后的空位
s2[0] = 100
fmt.Println(s1)         // [100 2]，s1 也被改了
```

规避方式：用 `copy` 建立独立副本、用三索引切片限制容量、或 `append([]T(nil), s...)` 复制。

### 8. nil 切片与空切片

| 写法 | 是否 nil | len | cap | 可否 append |
|------|---------|-----|-----|------------|
| `var s []int` | 是 | 0 | 0 | 可以 |
| `[]int{}` | 否 | 0 | 0 | 可以 |
| `make([]int, 0)` | 否 | 0 | 0 | 可以 |

```go
var nilSlice []int
empty := []int{}
fmt.Println(nilSlice == nil, empty == nil) // true false
```

两者在 `len`、`range`、`append` 上行为一致，区别在序列化：`encoding/json` 把 nil 切片编码为 `null`，空切片编码为 `[]`。

### 9. Map 增删改查与 comma-ok

Map 是引用类型，必须初始化后才能写入；读取不存在的键返回**值类型的零值**，容易与"库存为 0"混淆：

```go
stock := map[string]int{"iPhone 15": 120}
stock["AirPods"] = 300   // 新增
stock["iPhone 15"] = 110 // 更新

if qty, ok := stock["iPad"]; ok {
	fmt.Println("库存", qty)
} else {
	fmt.Println("商品不存在") // qty 为 0，ok 为 false
}

delete(stock, "AirPods") // 删除不存在的键也安全
```

| 操作 | 写法 | 说明 |
|------|------|------|
| 新增 / 更新 | `m[k] = v` | 键存在则覆盖 |
| 安全读取 | `v, ok := m[k]` | 推荐写法 |
| 删除 | `delete(m, k)` | 键不存在也安全 |
| 判空 | `len(m) == 0` | Map 不能直接比较大小 |

### 10. 遍历随机、集合与嵌套 Map

Map 遍历顺序**随机**，需要固定顺序时先取键排序（Day08 的 `slices.Sort`）。用 Map 当集合，值为 `bool` 或 `struct{}`；嵌套 Map 的内层必须初始化，否则赋值会 panic：

```go
visited := map[string]bool{}
for _, sku := range []string{"SKU-1", "SKU-2", "SKU-1"} {
	visited[sku] = true // 重复键自动去重
}

catalog := map[string]map[string]int{
	"手机": {"SKU-1001": 120},
}
```

> 内置 Map **不是并发安全的**，多个 goroutine 同时读写会触发 `fatal error: concurrent map writes`。Day09 会介绍 `sync.RWMutex` 与 `sync.Map`。

### 11. 与 Python / TypeScript 对比

| 维度 | Go | Python | TypeScript |
|------|----|--------|-----------|
| 列表切片 | 共享底层数组 | 复制 | 复制 |
| 键值结构 | `map[K]V` | `dict` | `Map` |
| 键不存在 | 返回零值，需 comma-ok | `KeyError` | `undefined` |

最容易踩的差异：Python/TS 的切片是**复制**，Go 的切片是**共享**。

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/arrays.go` | 数组值语义、长度属于类型、数组比较、遍历与二维数组 |
| `Code/slices.go` | `make`、`append`、`len`/`cap`、`copy`、区间切片与三索引切片 |
| `Code/slice_internals.go` | 共享底层数组、`append` 扩容脱钩、`nil` 与空切片对比 |
| `Code/maps.go` | Map 增删改查、`comma-ok`、`delete`、随机遍历、集合与嵌套 Map |

```bash
cd "Day04 - 数组、切片与Map/Code"
go run arrays.go
go run slices.go
go run slice_internals.go
go run maps.go
```

> 同目录多个文件都有 `main` 函数，不要执行 `go run .`。

## 关键知识点总结

1. **数组是值类型**：赋值与传参复制全部元素，大数组传参应改用切片或指针。
2. **长度属于类型**：`[3]int` 与 `[4]int` 不兼容；长度相同且元素可比较时可用 `==`。
3. **切片三要素**：指针、长度、容量；切片赋值只复制描述符。
4. **make 与字面量**：`make([]T, len, cap)` 预留容量，减少扩容次数。
5. **append 必须接收返回值**：容量不足时分配新数组，旧切片保持不变。
6. **扩容脱钩**：扩容后拥有独立数组；未扩容的 append 会写入共享数组。
7. **copy 复制**：复制数量为两者长度的较小值，可切断共享关系。
8. **三索引切片**：`s[low:high:max]` 限制容量，防止后续 append 覆盖原数据。
9. **nil 与空切片**：行为基本一致，JSON 编码分别为 `null` 与 `[]`。
10. **Map 读取返回零值**：必须用 `comma-ok` 区分"不存在"与"值为零"；遍历随机，并发场景必须加锁。

## 实战练习

### 练习 1：商品数组统计

编写 `product_array.go`：定义 `[5]float64` 价格数组，计算总价、均价、最高与最低价；复制后修改副本首元素，输出原数组证明值语义；再用 `[2][3]string` 表示两个货架并遍历。

```text
总价：24396.00，均价：4879.20，原数组首元素 5999.00
```

### 练习 2：切片扩容与复制

编写 `slice_grow.go`：从 nil 切片连续 append 10 个整数并输出 `len`/`cap`；用 `make([]int, 0, 4)` 再 append 10 个，对比扩容次数；用 `copy` 复制后修改副本。

```text
append 3: len=3 cap=4；append 5: len=5 cap=8
复制后 origin[0]=1，clone[0]=99
```

### 练习 3：购物车 Map

编写 `cart_map.go`：用 `map[string]int` 完成新增、更新、删除；用 `comma-ok` 查询不存在的商品；遍历输出并统计种类与件数；再用 `map[string]map[string]int` 按分类统计库存。

```text
iPhone 15 x2；共 2 种商品，3 件
手机类库存合计：150
```

### 练习 4：共享底层数组实验

编写 `slice_share.go`，依次验证：`base[1:3]` 改元素后 `base` 联动；`make([]int,2,4)` 后 append 再改元素导致 `s1` 被改；继续 append 扩容后脱钩；最后用 `copy` 复制并修改。

```text
base 被修改：[1 99 3 4 5]；s1 被修改：[100 0]
扩容后 s2 不变：[100 0 3]
```
