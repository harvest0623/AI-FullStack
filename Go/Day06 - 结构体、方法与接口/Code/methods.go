// 文件用途：演示值接收者与指针接收者、方法集、自定义类型方法与 String() 方法
// 运行方式：go run methods.go
package main

import "fmt"

// Money 表示金额（单位：元），为自定义类型定义方法。
type Money float64

// String 让 Money 实现 fmt.Stringer，打印时自动格式化。
func (m Money) String() string {
	return fmt.Sprintf("¥%.2f", float64(m))
}

// CartItem 购物车条目。
type CartItem struct {
	Name  string
	Price Money
	Count int
}

// Cart 购物车。
type Cart struct {
	Items []CartItem
}

// Add 指针接收者：需要修改 Cart 自身。
func (c *Cart) Add(item CartItem) {
	c.Items = append(c.Items, item)
}

// Total 值接收者：只读，不修改接收者。
func (c Cart) Total() Money {
	var sum Money
	for _, it := range c.Items {
		sum += it.Price * Money(it.Count)
	}
	return sum
}

// ApplyDiscount 指针接收者：直接改写每个条目的价格。
func (c *Cart) ApplyDiscount(rate float64) {
	for i := range c.Items {
		c.Items[i].Price = Money(float64(c.Items[i].Price) * (1 - rate))
	}
}

// Summary 值接收者：只读并返回描述。
func (c Cart) Summary() string {
	return fmt.Sprintf("%d 种商品，合计 %s", len(c.Items), c.Total())
}

// Formatter 只包含值接收者方法，Cart 与 *Cart 都满足。
type Formatter interface {
	Summary() string
}

// Adder 只包含指针接收者方法，只有 *Cart 满足。
type Adder interface {
	Add(item CartItem)
}

// 编译期断言：*Cart 同时满足两个接口。
var _ Formatter = (*Cart)(nil)
var _ Adder = (*Cart)(nil)

func main() {
	cart := &Cart{}
	cart.Add(CartItem{Name: "机械键盘", Price: 399, Count: 1})
	cart.Add(CartItem{Name: "无线鼠标", Price: 129, Count: 2})

	fmt.Println("=== 指针接收者修改状态 ===")
	fmt.Println(cart.Summary())

	fmt.Println("\n=== 值 vs 指针接收者 ===")
	fmt.Printf("原价合计：%s\n", cart.Total())
	cart.ApplyDiscount(0.10)
	fmt.Printf("九折后：%s\n", cart.Total())

	// 方法集：值变量可以调用指针方法（Go 自动取地址）
	cart2 := Cart{}
	cart2.Add(CartItem{Name: "USB-C 扩展坞", Price: 259, Count: 1})
	fmt.Println("\n=== 值变量调用指针方法（自动取址）===")
	fmt.Println(cart2.Summary())

	// 通过接口调用，只依赖行为
	var f Formatter = cart
	fmt.Println("\n=== 通过接口调用 ===")
	fmt.Println(f.Summary())

	// String() 让自定义金额类型拥有可读输出
	fmt.Println("\n=== Stringer ===")
	fmt.Println("单件金额：", cart2.Items[0].Price)
	fmt.Printf("总计：%s，类型：%T\n", cart2.Total(), cart2.Total())

	// 结构体是值类型，但切片字段只复制了切片头，底层数组仍共享
	snapshot := cart2
	snapshot.Items[0].Price = 0
	fmt.Println("\n=== 浅拷贝陷阱 ===")
	fmt.Println("副本改价后，原购物车价格：", cart2.Items[0].Price) // 同样变成 ¥0.00
	fmt.Println("需要独立副本时应使用 slices.Clone 复制元素")
}
