// 文件用途：演示 fmt 常用动词、%+v/%#v/%T/%q、宽度精度与 Sprintf 组装 JSON
// 运行方式：go run fmt_format.go
package main

import "fmt"

// Order 表示一笔订单。
type Order struct {
	ID     string
	Amount float64
	Paid   bool
}

func main() {
	o := Order{ID: "ORD-20241022-001", Amount: 2599.5, Paid: true}

	fmt.Println("=== 结构体动词 ===")
	fmt.Printf("%%v   → %v\n", o)
	fmt.Printf("%%+v  → %+v\n", o)
	fmt.Printf("%%#v  → %#v\n", o)
	fmt.Printf("%%T   → %T\n", o)

	fmt.Println("\n=== 基础动词 ===")
	fmt.Printf("十进制 %d，二进制 %b，八进制 %o，十六进制 %x\n", 42, 42, 42, 42)
	fmt.Printf("字符 %c，Unicode %U，带引号字符串 %q\n", 'G', 'G', "Go")
	fmt.Printf("布尔 %t，浮点 %f，科学计数 %e，紧凑 %g\n",
		true, 3.14159, 1234567.89, 3.14159)
	fmt.Printf("指针地址 %p\n", &o)

	fmt.Println("\n=== 宽度与精度 ===")
	fmt.Printf("|%10s|%-10s|\n", "商品", "商品")
	fmt.Printf("|%10.2f|%-10.2f|\n", 5999.0, 5999.0)
	fmt.Printf("|%08d|%+.2f|%08.2f|\n", 42, 88.5, 3.14159)
	fmt.Printf("截断字符串：%.3s\n", "eshop-gateway")

	fmt.Println("\n=== Sprintf 组装 JSON ===")
	item := fmt.Sprintf(`{"sku":%q,"price":%.2f,"stock":%d}`, "SKU-1001", 5999.0, 120)
	fmt.Println(item)
	order := fmt.Sprintf(`{"id":%q,"amount":%.2f,"paid":%t}`, o.ID, o.Amount, o.Paid)
	fmt.Println(order)

	summary := fmt.Sprintf("订单 %s：%.2f 元，支付状态 %t", o.ID, o.Amount, o.Paid)
	fmt.Println(summary)

	fmt.Println("\n=== 百分号与重复利用参数 ===")
	fmt.Printf("折扣 15%% → 实付 %.2f 元\n", o.Amount*0.85)
	fmt.Printf("%[1]s 的订单号是 %[1]s\n", o.ID)

	fmt.Println("\n=== 表格对齐 ===")
	goods := []string{"iPhone 15", "MacBook Pro", "AirPods"}
	prices := []float64{5999, 12999, 899}
	for i, name := range goods {
		fmt.Printf("%-12s %10.2f\n", name, prices[i])
	}
}
