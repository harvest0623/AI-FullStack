// 文件用途：演示值传递与指针传递、new 与 make、结构体拷贝以及逃逸分析概念
// 运行方式：go run memory_demo.go
package main

import "fmt"

// Order 表示一笔订单。
type Order struct {
	ID     string
	Amount float64
	Items  []string
}

// mutateOrderByValue 只修改副本；但切片字段共享底层数组，元素仍会联动。
func mutateOrderByValue(o Order) {
	o.Amount = 0
	o.Items[0] = "被修改的商品"
}

// mutateOrderByPointer 通过指针修改原对象。
func mutateOrderByPointer(o *Order) {
	o.Amount = 0
}

// newProduct 返回局部变量的指针，编译器会让它逃逸到堆上。
func newProduct(name string) *Order {
	o := Order{ID: "ORD-001", Amount: 99}
	o.Items = []string{name}
	return &o
}

// BigStruct 用于对比大对象的值传递与指针传递成本。
type BigStruct struct {
	Data [1024]int
}

func sumByValue(b BigStruct) int {
	return b.Data[0]
}

func sumByPointer(b *BigStruct) int {
	return b.Data[0]
}

func main() {
	// 1. 结构体赋值是浅拷贝
	fmt.Println("=== 结构体拷贝 ===")
	order := Order{ID: "ORD-1001", Amount: 2599, Items: []string{"iPhone 15"}}
	orderCopy := order
	orderCopy.Amount = 1
	fmt.Printf("order.Amount=%.2f orderCopy.Amount=%.2f\n", order.Amount, orderCopy.Amount)
	orderCopy.Items[0] = "iPhone 15 Pro"
	fmt.Printf("切片字段共享底层数组：order.Items[0]=%s\n", order.Items[0])

	// 2. 值传递 vs 指针传递
	fmt.Println("\n=== 值传递 vs 指针传递 ===")
	mutateOrderByValue(order)
	fmt.Printf("值传递后 amount=%.2f，首件商品=%s\n", order.Amount, order.Items[0])
	mutateOrderByPointer(&order)
	fmt.Printf("指针传递后 amount=%.2f\n", order.Amount)

	// 3. new 与 make
	fmt.Println("\n=== new vs make ===")
	p := new(int) // 分配零值 int，返回 *int
	*p = 42
	fmt.Printf("new(int) 指针=%p 值=%d\n", p, *p)

	nums := make([]int, 3, 5) // 分配切片底层数组，返回切片
	nums[0] = 1
	fmt.Printf("make([]int,3,5) = %v len=%d cap=%d\n", nums, len(nums), cap(nums))

	m := make(map[string]int) // Map 必须初始化后才能写入
	m["count"] = 1
	fmt.Printf("make(map) = %v\n", m)

	// 4. 大结构体的传递成本
	fmt.Println("\n=== 大结构体传递 ===")
	big := BigStruct{}
	big.Data[0] = 7
	fmt.Printf("按值传递结果=%d，按指针传递结果=%d\n",
		sumByValue(big), sumByPointer(&big))
	fmt.Println("值传递会复制整个数组，指针传递只复制一个地址")

	// 5. 逃逸分析
	fmt.Println("\n=== 逃逸分析 ===")
	prod := newProduct("MacBook Pro")
	fmt.Printf("newProduct 返回指针：%s，首件商品 %s\n", prod.ID, prod.Items[0])
	fmt.Println("局部变量被返回指针引用时会逃逸到堆")
	fmt.Println("可用 go build -gcflags=\"-m\" 查看编译器决策")
}
