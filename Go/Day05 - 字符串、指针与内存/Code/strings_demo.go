// 文件用途：演示字符串不可变、len 字节数、strings 常用函数与 Builder 高效拼接
// 运行方式：go run strings_demo.go
package main

import (
	"fmt"
	"strings"
)

func main() {
	// 1. 字符串不可变：任何"修改"都会生成新字符串
	title := "  eshop AI  Gateway  "
	fmt.Println("=== 字符串不可变 ===")
	fmt.Printf("原始：%q\n", title)
	lower := strings.ToLower(title)
	fmt.Printf("ToLower：%q\n", lower)
	fmt.Printf("原始仍为：%q\n", title)

	// 2. len 返回字节数，不是字符数
	cn := "商品"
	fmt.Printf("\n=== len 与字符数 ===\n\"%s\" 的 len = %d（UTF-8 字节数），字符数 = %d\n",
		cn, len(cn), len([]rune(cn)))

	// 3. strings 常用函数
	fmt.Println("\n=== strings 常用函数 ===")
	raw := "  eshop-gateway  "
	fmt.Printf("TrimSpace       : %q\n", strings.TrimSpace(raw))
	fmt.Printf("Trim 指定字符   : %q\n", strings.Trim(raw, " "))
	fmt.Printf("HasPrefix/Suffix: %t / %t\n",
		strings.HasPrefix("eshop-gateway", "eshop"),
		strings.HasSuffix("eshop-gateway", "gateway"))
	fmt.Printf("Contains        : %t\n", strings.Contains("eshop-gateway", "shop"))
	fmt.Printf("Index           : %d\n", strings.Index("eshop-gateway", "-"))
	fmt.Printf("Split           : %q\n", strings.Split("SKU-1001-手机", "-"))
	fmt.Printf("Join            : %s\n",
		strings.Join([]string{"iPhone 15", "MacBook Pro"}, " / "))
	fmt.Printf("ReplaceAll      : %s\n", strings.ReplaceAll("a-b-c", "-", "_"))
	fmt.Printf("Fields          : %q\n", strings.Fields("  iPhone   15  Pro  "))
	fmt.Printf("Repeat          : %s\n", strings.Repeat("=", 12))

	// 4. strings.Builder：循环内拼接不会反复复制
	fmt.Println("\n=== strings.Builder ===")
	var b strings.Builder
	b.WriteString("=== 商品清单 ===\n")
	items := []string{"iPhone 15", "MacBook Pro", "AirPods"}
	for i, item := range items {
		fmt.Fprintf(&b, "%d. %s\n", i+1, item)
	}
	b.WriteString("共 ")
	b.WriteString(fmt.Sprint(len(items)))
	b.WriteString(" 件商品")
	fmt.Println(b.String())

	// 5. 对比：字符串加法会在每次拼接时复制
	joined := ""
	for _, item := range items {
		joined += item + ","
	}
	fmt.Printf("\n加法拼接结果：%s\n", strings.TrimSuffix(joined, ","))
}
