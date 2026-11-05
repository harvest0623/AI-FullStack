// 文件用途：演示 map 增删改查、comma-ok、delete、随机遍历、集合用法与嵌套 map
// 运行方式：go run maps.go
package main

import "fmt"

func main() {
	// 1. 创建与增改查
	stock := map[string]int{
		"iPhone 15":   120,
		"MacBook Pro": 15,
	}
	stock["AirPods"] = 300   // 新增
	stock["iPhone 15"] = 110 // 更新

	fmt.Println("=== 增改查 ===")
	fmt.Printf("iPhone 15 库存：%d\n", stock["iPhone 15"])
	fmt.Printf("Map 长度：%d\n", len(stock))

	// 2. comma-ok：区分"键不存在"与"值为零"
	fmt.Println("\n=== comma-ok ===")
	if qty, ok := stock["iPad"]; ok {
		fmt.Printf("iPad 库存 %d\n", qty)
	} else {
		fmt.Printf("iPad 不存在，返回零值 %d，ok=%t\n", qty, ok)
	}

	// 3. delete：删除不存在的键是安全的
	delete(stock, "AirPods")
	delete(stock, "不存在的键")
	fmt.Printf("\n删除 AirPods 后长度：%d\n", len(stock))

	// 4. 遍历顺序随机，每次运行都可能不同
	fmt.Println("\n=== 遍历（顺序随机） ===")
	stock["AirPods"] = 300
	stock["iPad"] = 40
	for name, qty := range stock {
		fmt.Printf("%-14s %d\n", name, qty)
	}

	// 5. 用 Map 当集合：值用 bool 或 struct{}
	fmt.Println("\n=== Map 当集合 ===")
	visited := map[string]bool{}
	for _, sku := range []string{"SKU-1", "SKU-2", "SKU-1"} {
		if !visited[sku] {
			visited[sku] = true
			fmt.Println("首次访问：", sku)
		}
	}
	fmt.Printf("去重后共 %d 个 SKU\n", len(visited))

	// 6. 嵌套 Map：分类 → SKU → 库存
	fmt.Println("\n=== 嵌套 Map ===")
	catalog := map[string]map[string]int{
		"手机": {"SKU-1001": 120, "SKU-1002": 30},
		"电脑": {"SKU-2001": 15},
	}
	catalog["配件"] = map[string]int{"SKU-3001": 500}
	for category, skus := range catalog {
		total := 0
		for _, qty := range skus {
			total += qty
		}
		fmt.Printf("%s：%d 个 SKU，合计库存 %d\n", category, len(skus), total)
	}
}
