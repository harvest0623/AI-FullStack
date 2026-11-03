// 文件用途：演示 var 三种写法、短变量声明、零值、多重赋值与作用域遮蔽
// 运行方式：go run variables.go
package main

import "fmt"

// 包级变量：可以在声明后暂不使用（局部变量则不行）
var serviceName = "eshop-gateway"

var (
	defaultPageSize = 20
	defaultCurrency = "CNY"
)

func main() {
	// 1. var 的三种写法
	var productName string = "iPhone 15" // 显式类型
	var price = 5999.00                  // 类型推导为 float64
	var stock int                        // 仅声明，稍后赋值
	var (
		category = "手机数码"
		onSale   = true
	)
	stock = 120

	fmt.Println("=== var 声明 ===")
	fmt.Printf("商品：%s｜分类：%s｜价格：%.2f｜库存：%d｜在售：%t\n",
		productName, category, price, stock, onSale)
	fmt.Printf("服务：%s，默认分页：%d，默认币种：%s\n",
		serviceName, defaultPageSize, defaultCurrency)

	// 2. 短变量声明：只能出现在函数内部
	sku := "SKU-1001"
	rating := 4.8
	fmt.Printf("\n=== 短变量声明 ===\nSKU：%s，评分：%.1f（类型 %T）\n", sku, rating, rating)

	// 3. 零值：声明不赋值时，Go 自动写入该类型的零值
	var (
		zeroInt     int
		zeroFloat   float64
		zeroBool    bool
		zeroString  string
		zeroPointer *int
	)
	fmt.Println("\n=== 零值 ===")
	fmt.Printf("int=%d float64=%.2f bool=%t string=%q pointer=%v\n",
		zeroInt, zeroFloat, zeroBool, zeroString, zeroPointer)

	// 4. 多重赋值：右侧先全部求值，再依次赋给左侧
	a, b := 10, 20
	a, b = b, a
	fmt.Printf("\n=== 多重赋值 ===\na=%d b=%d\n", a, b)

	// 5. 作用域与变量遮蔽
	stock = 88
	fmt.Printf("\n=== 作用域 ===\n外层 stock = %d\n", stock)
	{
		stock := 5 // 新变量，遮蔽外层 stock
		fmt.Printf("内层 stock = %d（新变量）\n", stock)
	}
	fmt.Printf("离开代码块后 stock = %d\n", stock)

	if stock > 50 {
		stock := stock / 2 // 右边的 stock 先求值，再声明同名新变量
		fmt.Printf("if 块内 stock = %d\n", stock)
	}
	fmt.Printf("if 结束后 stock 仍为 %d\n", stock)

	// 6. 同一作用域内 := 至少要有新变量
	stock, note := 60, "补货中"
	fmt.Printf("\n=== 混合声明 ===\nstock=%d note=%s\n", stock, note)
}
