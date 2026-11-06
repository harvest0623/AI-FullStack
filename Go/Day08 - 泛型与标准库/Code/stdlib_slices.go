// 文件用途：演示 slices 泛型工具、Map 键排序、maps.Clone/Equal 与内置 min/max
// 运行方式：go run stdlib_slices.go
package main

import (
	"cmp"
	"fmt"
	"maps"
	"slices"
)

// Product 商品。
type Product struct {
	Name  string
	Price float64
	Stock int
}

func main() {
	prices := []int{399, 129, 1499, 259, 129}
	original := slices.Clone(prices) // 先克隆，保留原始顺序

	fmt.Println("=== slices.Sort / Clone / Reverse ===")
	fmt.Println("原始：", original)
	slices.Sort(prices)
	fmt.Println("升序：", prices)
	slices.Reverse(prices)
	fmt.Println("反转：", prices)

	fmt.Println("\n=== slices.Contains / Index ===")
	fmt.Println("包含 259：", slices.Contains(original, 259))
	fmt.Println("259 的下标：", slices.Index(original, 259))
	fmt.Println("包含 999：", slices.Contains(original, 999))

	fmt.Println("\n=== slices.Compact 去重 ===")
	dup := []string{"A", "A", "B", "C", "C", "C"}
	before := slices.Clone(dup)
	slices.Sort(dup) // Compact 只去相邻重复，先排序才能去干净
	sortedView := slices.Clone(dup)
	compacted := slices.Compact(dup)
	fmt.Println("去重前：", before)
	fmt.Println("排序后：", sortedView)
	fmt.Println("Compact 结果：", compacted)

	fmt.Println("\n=== slices.SortFunc 多字段排序 ===")
	products := []Product{
		{Name: "机械键盘", Price: 399, Stock: 25},
		{Name: "无线鼠标", Price: 129, Stock: 0},
		{Name: "显示器", Price: 1499, Stock: 8},
		{Name: "扩展坞", Price: 259, Stock: 25},
	}
	slices.SortFunc(products, func(a, b Product) int {
		if n := cmp.Compare(b.Stock, a.Stock); n != 0 {
			return n // 库存降序
		}
		return cmp.Compare(a.Price, b.Price) // 库存相同则价格升序
	})
	for _, p := range products {
		fmt.Printf("%s 库存 %d 价格 %.2f\n", p.Name, p.Stock, p.Price)
	}

	fmt.Println("\n=== Map 键的收集与排序（Go 1.22 兼容写法）===")
	stock := map[string]int{
		"SKU-1001": 25,
		"SKU-1002": 0,
		"SKU-1003": 8,
	}
	// Go 1.22 没有迭代器形式的 maps.Keys，手动收集键后再排序。
	keys := make([]string, 0, len(stock))
	for sku := range stock {
		keys = append(keys, sku)
	}
	slices.Sort(keys)
	for _, sku := range keys {
		fmt.Printf("%s=%d ", sku, stock[sku])
	}
	fmt.Println()

	counts := make([]int, 0, len(stock))
	for _, count := range stock {
		counts = append(counts, count)
	}
	slices.Sort(counts)
	fmt.Println("库存值升序：", counts)

	// maps.Clone 是浅拷贝；maps.Equal 按键值逐一比较。
	copyStock := maps.Clone(stock)
	fmt.Println("maps.Clone 副本：", copyStock)
	fmt.Println("maps.Equal 比较：", maps.Equal(stock, copyStock))

	fmt.Println("\n=== 内置 min / max ===")
	fmt.Println("min(3, 8, 1)：", min(3, 8, 1))
	fmt.Println("max(3, 8, 1)：", max(3, 8, 1))
	nums := []float64{12.5, 3.2, 99.9}
	fmt.Printf("切片最小 %.1f，最大 %.1f\n", slices.Min(nums), slices.Max(nums))
}
