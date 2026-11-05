// 文件用途：演示 & 与 *、用指针交换变量、结构体指针、nil 指针与"Go 无指针运算"
// 运行方式：go run pointers.go
package main

import "fmt"

// Product 表示电商商品。
type Product struct {
	Name  string
	Price float64
	Stock int
}

// discountByValue 修改的是副本，不影响调用方。
func discountByValue(p Product) {
	p.Price = p.Price * 0.8
}

// discountByPointer 通过指针修改原结构体。
func discountByPointer(p *Product) {
	p.Price = p.Price * 0.8
}

// swap 用指针交换两个变量的值。
func swap(a, b *int) {
	*a, *b = *b, *a
}

func main() {
	// 1. & 取地址，* 解引用
	stock := 120
	ptr := &stock
	fmt.Println("=== 取地址与解引用 ===")
	fmt.Printf("stock=%d 地址=%p 指针解引用=%d\n", stock, ptr, *ptr)

	*ptr = 80
	fmt.Printf("通过 *ptr 修改后 stock=%d\n", stock)

	// 2. 用指针交换两个变量
	fmt.Println("\n=== 指针交换 ===")
	a, b := 1, 2
	swap(&a, &b)
	fmt.Printf("a=%d b=%d\n", a, b)

	// 3. 结构体：值传递 vs 指针传递
	fmt.Println("\n=== 结构体指针 ===")
	phone := Product{Name: "iPhone 15", Price: 5999, Stock: 120}
	discountByValue(phone)
	fmt.Printf("值传递后：%s 价格 %.2f（未改变）\n", phone.Name, phone.Price)

	discountByPointer(&phone)
	fmt.Printf("指针传递后：%s 价格 %.2f\n", phone.Name, phone.Price)

	// 指针访问字段可省略 *，Go 自动解引用
	p := &phone
	p.Stock -= 20
	fmt.Printf("%s 剩余库存 %d\n", p.Name, p.Stock)

	// 4. nil 指针：解引用前必须判断
	fmt.Println("\n=== nil 指针 ===")
	var np *Product
	fmt.Printf("nil 指针：%v，是否为 nil：%t\n", np, np == nil)
	if np != nil {
		fmt.Println(np.Name) // 防御性判断，避免 panic
	} else {
		fmt.Println("空指针不可访问字段，已提前拦截")
	}

	// 5. Go 没有指针运算，只能通过索引访问相邻元素
	fmt.Println("\n=== 无指针运算 ===")
	nums := []int{10, 20, 30}
	first := &nums[0]
	fmt.Printf("首个元素地址 %p，值 %d；下一个元素用 nums[1]=%d 访问\n",
		first, *first, nums[1])
}
