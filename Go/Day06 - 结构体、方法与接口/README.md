# Day06 - 结构体、方法与接口

## 本章简介

Day01-Day05 我们掌握了变量、控制流、切片、Map、字符串与指针，能够写出"能跑"的程序。但从今天开始，代码要从"脚本"升级为"工程"：商品、订单、库存这些概念需要用有名字的类型来表达，而不是散落的 `map[string]any`。结构体（struct）正是 Go 用来组织数据的手段，它把相关字段打包成一个值，并天然支持值语义、嵌套与序列化。

有了数据之后，还需要行为。Go 没有类，方法（method）通过"接收者"绑定到类型上；接口（interface）则描述一组行为，并且是**隐式实现**的——只要类型拥有接口要求的方法，它就自动满足接口，无需 `implements` 声明。这种设计让 `eshop-gateway` 的仓储、支付渠道、通知器等组件可以面向接口编程：上层只依赖抽象，下层随意替换，测试时注入假实现即可。

本章的落点是 `eshop-gateway` 的领域模型层：`Product`、`Order`、`Shipment` 等结构体负责数据，`Payer`、`Notifier`、`Formatter` 等接口负责解耦，嵌入（embedding）负责复用审计字段等通用能力。学完本章，你将能读懂并设计一个真实 Go 服务的数据层骨架。

## 学习目标

- 掌握结构体定义、按字段名初始化与按位置初始化的差异
- 理解结构体零值，以及指针字段、切片字段的零值表现
- 掌握结构体可比较的条件，理解含切片/Map/函数字段时不能使用 `==`
- 会使用嵌套结构体表达组合关系，并正确访问内层字段
- 理解 struct tag 的作用，能用 `encoding/json` 完成序列化与字段重命名
- 掌握值接收者与指针接收者的语义差异，知道何时该用哪一种
- 理解方法集规则：`T` 与 `*T` 的方法集不同，直接影响接口实现
- 能为自定义类型（如 `type Money float64`）定义方法并实现 `fmt.Stringer`
- 掌握接口的隐式实现、多态调用与接口组合
- 会使用 `any`、类型断言 `comma-ok`、`type switch` 安全处理动态类型
- 识别 `nil` 接口陷阱，理解"接口为 nil"与"接口内指针为 nil"的区别
- 掌握匿名字段嵌入带来的字段提升与方法提升，理解嵌入与继承的本质差异

## 理论知识讲解

### 1. 结构体：把相关字段组织成值

结构体是**字段的集合**，是一个值类型。赋值、传参都会复制整个结构体：

```go
type Product struct {
	ID    int
	Name  string
	Price float64
	Stock int
}

p := Product{ID: 1001, Name: "机械键盘", Price: 399, Stock: 25}
q := p        // 完整副本
q.Price = 299 // 不影响 p
```

与 Python 的 `dict`、TypeScript 的 `interface` 对象相比，结构体字段是**编译期固定**的，拼错字段名会直接编译失败，这是大型项目最有效的防线之一。

| 维度 | Go 结构体 | Python dict / class | TypeScript 对象 |
|------|-----------|---------------------|-----------------|
| 字段约束 | 编译期固定 | 运行期随意 | 编译期固定（类型层面） |
| 默认传参 | 值复制 | 引用 | 引用 |
| 零值 | 所有字段零值 | 无 | `undefined` |
| 序列化 | 依靠 struct tag | 手动构造 | JSON.stringify |

### 2. 初始化与零值

两种初始化方式：

```go
// 按字段名：推荐，顺序无关、可只写部分字段
p1 := Product{ID: 1001, Name: "机械键盘"}

// 按位置：必须写全所有字段，顺序与定义一致，字段增减会直接编译报错
p2 := Product{1002, "无线鼠标", 129, 80}
```

| 字段类型 | 零值 |
|---------|------|
| `int` / `float64` | `0` |
| `string` | `""` |
| `bool` | `false` |
| 指针、接口、切片、Map | `nil` |
| 嵌套结构体 | 递归零值 |

```go
var p Product
// p.ID == 0, p.Name == "", p.Price == 0, p.Stock == 0
```

> 实战建议：对外构造结构体时优先按字段名初始化。位置初始化在字段增加或重排时会静默错位，是重构时的隐患。

### 3. 结构体比较与嵌套

结构体可以用 `==` 比较，前提是**所有字段都可比较**：

| 字段类型 | 可否比较 |
|---------|---------|
| 数值、字符串、布尔、指针、接口 | 可 |
| 数组（元素可比较） | 可 |
| 结构体（字段均可比较） | 可 |
| 切片、Map、函数 | 不可（只能与 `nil` 比较） |

```go
type StockRecord struct {
	SKU   string
	Count int
}

fmt.Println(StockRecord{"SKU-1001", 25} == StockRecord{"SKU-1001", 25}) // true

// Product 含 Tags []string，p1 == p2 直接编译失败
```

嵌套结构体表达"整体-部分"关系，访问时逐层点号：

```go
type Dimensions struct {
	Length, Width, Height float64
}

type Shipment struct {
	SKU        string
	Dimensions Dimensions
}

s := Shipment{SKU: "SKU-1001", Dimensions: Dimensions{Length: 40, Width: 20, Height: 8}}
s.Dimensions.Height = 10 // 修改内层字段
```

### 4. struct tag 与 JSON

struct tag 是写在字段后面的元信息，由反射读取，最常见用途是 JSON 字段名与 `omitempty`：

```go
type Product struct {
	ID    int      `json:"id"`
	Name  string   `json:"name"`
	Price float64  `json:"price"`
	Tags  []string `json:"tags,omitempty"`
}
```

| tag 写法 | 作用 |
|---------|------|
| `json:"name"` | 序列化字段名改为 `name` |
| `json:"-"` | 完全忽略该字段 |
| `json:"tags,omitempty"` | 零值时省略输出 |
| `json:"price,string"` | 以字符串形式输出数值 |

```go
raw, err := json.MarshalIndent(p, "", "  ")
if err != nil {
	return
}
fmt.Println(string(raw))
```

> tag 只是字符串，编译器不会校验拼写。字段名写错（如 `jsom:"name"`）不会报错，只会导致序列化结果不符合预期，因此接口联调时要重点核对。

### 5. 方法：把行为绑定到类型

方法就是带接收者的函数。接收者有两种：

```go
// 值接收者：操作副本，不会修改原值
func (p Product) Total() float64 { return p.Price * float64(p.Stock) }

// 指针接收者：可以修改原值，也避免大结构体复制
func (p *Product) Discount(rate float64) { p.Price *= 1 - rate }
```

| 维度 | 值接收者 `func (p T)` | 指针接收者 `func (p *T)` |
|------|----------------------|--------------------------|
| 是否复制 | 复制整个值 | 只复制指针 |
| 能否修改原值 | 否 | 是 |
| 方法集归属 | `T` 和 `*T` 都拥有 | 仅 `*T` 拥有 |
| 适用场景 | 只读、小对象、值语义类型 | 需要修改、大对象、含锁字段 |

调用规则很宽松：**可寻址**的值变量调用指针方法时，Go 会自动取地址 `(&p).Discount(0.1)`；但不可寻址的值（如函数返回值、Map 元素）不能调用指针方法。

### 6. 方法集与接口实现

方法集决定了类型能否满足接口：

```go
type Adder interface{ Add(item CartItem) }

func (c *Cart) Add(item CartItem) { c.Items = append(c.Items, item) }

var _ Adder = &Cart{} // 编译期断言：*Cart 满足 Adder
// var _ Adder = Cart{} // 编译错误：Cart 的方法集不含 Add
```

| 类型 | 值接收者方法 | 指针接收者方法 |
|------|-------------|---------------|
| `T` | 有 | 无 |
| `*T` | 有（自动解引用） | 有 |

> 经验法则：**同一个类型的方法尽量统一接收者形式**。混用会造成"值能满足接口 A、指针能满足接口 B"的混乱。需要修改状态或结构体较大时，一律用指针接收者。

### 7. 接口：隐式实现与多态

Go 的接口是**结构化**的：不声明实现关系，只看方法签名是否匹配。

```go
type Payer interface {
	Name() string
	Pay(amount float64) (string, error)
}

type Alipay struct{ Account string }

func (a Alipay) Name() string { return "支付宝" }
func (a Alipay) Pay(amount float64) (string, error) {
	return fmt.Sprintf("%s 支付 %.2f 元", a.Name(), amount), nil
}
// 这里没有写任何 "implements Payer"，但 Alipay 已经满足 Payer
```

多态体现在函数参数上——`Checkout(p Payer, amount float64)` 不关心具体渠道；新增支付方式时，`Checkout` 一行都不用改。这正是"开闭原则"在 Go 里的自然表达。

接口还可以嵌套组合：

```go
type Reader interface{ Read() ([]byte, error) }
type Closer interface{ Close() error }
type ReadCloser interface {
	Reader
	Closer
}
```

标准库的 `io.ReadCloser` 就是这种写法，Day10 会大量使用。

### 8. 空接口、类型断言与 type switch

`any` 是 `interface{}` 的别名，表示"任意类型"。取出具体值需要断言：

```go
var v any = "eshop"

// 不安全断言：失败直接 panic
s := v.(string)

// comma-ok：失败返回零值与 false，不 panic
s, ok := v.(string)
```

批量判断使用 type switch：

```go
switch x := v.(type) {
case int:
	fmt.Println("整数", x)
case string:
	fmt.Println("字符串", x)
case Payer:
	fmt.Println("支付渠道", x.Name())
case nil:
	fmt.Println("nil")
default:
	fmt.Printf("未知类型 %T\n", x)
}
```

| 写法 | 失败行为 | 使用场景 |
|------|---------|---------|
| `v.(T)` | panic | 确定类型时（极少） |
| `v, ok := v.(T)` | `ok=false` | 常规判断 |
| `switch v.(type)` | 走 default | 多分支分发 |

### 9. Stringer 与 nil 接口陷阱

实现 `String() string` 即满足 `fmt.Stringer`，打印时自动调用：

```go
type SKU string

func (s SKU) String() string { return "SKU-" + string(s) }

fmt.Println(SKU("1001")) // SKU-1001
```

**nil 接口陷阱**是初学者最常见的坑：

```go
var wx *Wechat        // 类型 *Wechat，值为 nil
var p Payer = wx      // 接口 = (类型: *Wechat, 值: nil)
fmt.Println(p == nil) // false！
```

接口只有在**类型和值都为 nil** 时才等于 `nil`。把一个 nil 指针赋给接口后，接口本身非 nil；此时调用会解引用字段的方法就会 panic。正确做法是断言后检查底层指针：

```go
if w, ok := p.(*Wechat); ok && w != nil {
	// 安全使用
}
```

### 10. 嵌入：组合优于继承

Go 没有继承，但支持**匿名字段嵌入**，被嵌入类型的方法与字段会被"提升"到外层：

```go
type Audit struct {
	CreatedBy string
	CreatedAt string
}

func (a Audit) Summary() string { return a.CreatedBy + " 创建" }

type Order struct {
	ID string
	Audit // 匿名字段，字段名就是 Audit
}

o.Summary() // 方法提升，等价于 o.Audit.Summary()
o.CreatedBy // 字段提升，等价于 o.Audit.CreatedBy
```

也可以嵌入接口，把实现延迟到运行时注入：

```go
type OrderService struct {
	Notifier // 嵌入接口
}
```

| 维度 | 嵌入（组合） | 面向对象继承 |
|------|-------------|-------------|
| 关系 | has-a（拥有） | is-a（是） |
| 类型替换 | 外层不能当内层用 | 子类可替换父类 |
| 方法覆盖 | 外层同名方法优先 | override |
| 耦合度 | 低，可自由替换内嵌实现 | 高，受父类约束 |

> 嵌入不是继承：`Order` 不是 `Audit` 的子类型，不能把 `Order` 赋给 `Audit` 变量。它只是语法糖，帮你少写转发方法。

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/structs.go` | 结构体定义、字段名/位置初始化、零值、比较、嵌套、struct tag 与 JSON |
| `Code/methods.go` | 值/指针接收者、修改语义、方法集、自定义类型方法、`String()` |
| `Code/interfaces.go` | 隐式实现、多态、`any`、comma-ok 断言、type switch、Stringer、nil 接口 |
| `Code/embedding.go` | 匿名字段嵌入、方法提升、字段提升、嵌入接口、与继承的差异 |

执行方式（每个文件独立运行）：

```bash
cd "Day06 - 结构体、方法与接口/Code"
go run structs.go
go run methods.go
go run interfaces.go
go run embedding.go
```

> 同一目录下每个文件都有自己的 `main` 函数，不能执行 `go run .`，请按文件名单独运行。

## 关键知识点总结

1. **结构体是值类型**：赋值与传参复制整份数据，需要共享修改时用 `*T`。
2. **初始化优先按字段名**：位置初始化在字段变动时容易静默错位。
3. **零值可用**：结构体零值即所有字段零值，切片/Map/指针为 `nil`。
4. **可比较条件**：字段全部可比较才能用 `==`；含切片、Map、函数则不可比较。
5. **struct tag**：控制 JSON 字段名与 `omitempty`，写错不会编译报错，需联调核对。
6. **接收者选择**：要修改状态或结构体较大用指针接收者，只读小对象用值接收者。
7. **方法集规则**：`T` 只有值接收者方法，`*T` 拥有全部方法，直接决定接口能否满足。
8. **接口隐式实现**：方法签名匹配即满足接口，实现方与接口方可以互不知晓。
9. **类型断言**：常规场景一律用 comma-ok，避免 panic；多分支用 type switch。
10. **nil 接口陷阱**：接口等于 `nil` 要求类型和值都为 nil，nil 指针装入接口后不再等于 nil。
11. **嵌入是组合**：字段与方法提升减少转发代码，但外层并不是内层的子类型。

## 实战练习

### 练习 1：完善商品领域模型

在 `structs.go` 基础上扩展：

1. 为 `Product` 增加 `Category`、`CreatedAt`（`time.Time`）与 `Attributes map[string]string` 字段，并补上合适的 json tag。
2. 构造一个商品列表，用 `json.MarshalIndent` 输出，确认 `omitempty` 的效果。
3. 思考并验证：为什么含 `Attributes` 的 `Product` 不能用 `==` 比较？如果一定要比较，应怎么写比较函数？

### 练习 2：购物车方法与接口

新建 `cart_exercise.go`：

- 定义 `Cart` 结构体与方法：`Add`（指针接收者）、`Remove(sku string)`、`Total() Money`、`Summary() string`
- 定义 `type Money float64` 并实现 `String()`，输出形如 `¥1,299.00`
- 定义接口 `Pricer interface { Total() Money }`，用编译期断言 `var _ Pricer = (*Cart)(nil)` 验证
- 分别用值变量与指针变量调用方法，观察哪些调用合法、哪些编译失败，并记录原因

### 练习 3：多支付渠道与类型分发

在 `interfaces.go` 基础上：

1. 新增 `BankCard` 渠道，实现 `Payer`，在 `Pay` 中对金额做上限校验（单笔不超过 50000）。
2. 写函数 `Audit(records []any)`，用 type switch 统计各渠道成功笔数，遇到未知类型输出告警而不是 panic。
3. 复现 nil 接口陷阱：声明 `var c *BankCard`，赋给 `Payer` 后打印 `p == nil`，再解释为什么。

### 练习 4：订单审计与嵌入重构

在 `embedding.go` 基础上：

1. 为 `Audit` 增加 `UpdatedBy`、`UpdatedAt` 字段与 `Touch(user string)` 方法（指针接收者）。
2. 让 `Order` 与 `Refund` 都嵌入 `Audit`，验证 `Touch` 方法提升后可直接调用，并确认调用会修改到内层字段。
3. 给 `OrderService` 增加第二个通知实现 `SMSNotifier`，通过构造函数注入，体会"面向接口编程 + 运行时替换"的收益。
4. 思考：如果改用继承实现同样的复用，父类改动会如何影响两个子类？
