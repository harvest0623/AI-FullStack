// 文件用途：演示 fmt 常用输出函数、格式化动词、宽度精度与 strings.Builder
// 运行方式：go run fmt_demo.go
package main

import (
	"fmt"
	"strings"
)

// Product 表示一个电商商品。
type Product struct {
	Name  string
	Price float64
	Stock int
}

func main() {
	p := Product{Name: "iPhone 15", Price: 5999.0, Stock: 120}

	fmt.Println("=== Print 系列 ===")
	fmt.Println("Println :", p.Name, p.Price, p.Stock)
	fmt.Printf("Printf  : %s 价格 %.2f 库存 %d\n", p.Name, p.Price, p.Stock)

	fmt.Println("\n=== 常用动词 ===")
	fmt.Printf("默认      %%v : %v\n", p)
	fmt.Printf("带字段名  %%+v: %+v\n", p)
	fmt.Printf("Go 语法   %%#v: %#v\n", p)
	fmt.Printf("类型      %%T : %T\n", p)
	fmt.Printf("二进制/八进制/十六进制: %b / %o / %x\n", 42, 42, 42)
	fmt.Printf("字符/Unicode/带引号字符串: %c / %U / %q\n", 'G', 'G', "Go")

	fmt.Println("\n=== 宽度与精度 ===")
	fmt.Printf("|%8s|%-8s|%08.2f|\n", "Go", "Go", 3.14159)
	fmt.Printf("科学计数法: %e，百分比: %.1f%%\n", 1234567.89, 0.856)

	fmt.Println("\n=== 字符串构建 ===")
	var b strings.Builder
	b.WriteString("商品：")
	b.WriteString(p.Name)
	fmt.Fprintf(&b, "，价格：%.2f，库存：%d", p.Price, p.Stock)
	fmt.Println(b.String())

	summary := fmt.Sprintf("%s 有 %d 件库存", p.Name, p.Stock)
	fmt.Println("Sprintf:", summary)
}
