// 文件用途：演示泛型 Map/Filter/Reduce、泛型 Stack[T]、类型推断与泛型方法限制
// 运行方式：go run generics.go
package main

import "fmt"

// Map 把 []T 逐元素转换为 []R。
func Map[T, R any](items []T, fn func(T) R) []R {
	out := make([]R, 0, len(items))
	for _, it := range items {
		out = append(out, fn(it))
	}
	return out
}

// Filter 保留满足条件的元素。
func Filter[T any](items []T, keep func(T) bool) []T {
	out := make([]T, 0, len(items))
	for _, it := range items {
		if keep(it) {
			out = append(out, it)
		}
	}
	return out
}

// Reduce 把 []T 聚合为单个值 A。
func Reduce[T, A any](items []T, init A, fn func(A, T) A) A {
	acc := init
	for _, it := range items {
		acc = fn(acc, it)
	}
	return acc
}

// Stack 泛型栈：方法沿用类型参数 T。
type Stack[T any] struct {
	items []T
}

// Push 入栈。
func (s *Stack[T]) Push(v T) {
	s.items = append(s.items, v)
}

// Pop 出栈，第二个返回值表示是否成功。
func (s *Stack[T]) Pop() (T, bool) {
	var zero T
	if len(s.items) == 0 {
		return zero, false
	}
	v := s.items[len(s.items)-1]
	s.items = s.items[:len(s.items)-1]
	return v, true
}

// Size 返回栈内元素数量。
func (s *Stack[T]) Size() int { return len(s.items) }

// Product 商品。
type Product struct {
	Name  string
	Price float64
	Stock int
}

func main() {
	products := []Product{
		{Name: "机械键盘", Price: 399, Stock: 25},
		{Name: "无线鼠标", Price: 129, Stock: 0},
		{Name: "显示器", Price: 1499, Stock: 8},
	}

	fmt.Println("=== Map：结构体切片 → 名称切片 ===")
	names := Map(products, func(p Product) string { return p.Name })
	fmt.Println(names)

	fmt.Println("\n=== Filter：筛选有货商品 ===")
	inStock := Filter(products, func(p Product) bool { return p.Stock > 0 })
	fmt.Println(Map(inStock, func(p Product) string { return p.Name }))

	fmt.Println("\n=== Reduce：计算库存总值 ===")
	total := Reduce(products, 0.0, func(acc float64, p Product) float64 {
		return acc + p.Price*float64(p.Stock)
	})
	fmt.Printf("库存总值：%.2f 元\n", total)

	// 显式指定类型参数：推断失败或需要强制类型时使用
	count := Reduce(products, 0, func(acc int, _ Product) int { return acc + 1 })
	fmt.Println("商品种类：", count)

	fmt.Println("\n=== 泛型 Stack ===")
	var skuStack Stack[string]
	skuStack.Push("SKU-1001")
	skuStack.Push("SKU-1002")
	fmt.Println("栈大小：", skuStack.Size())
	for skuStack.Size() > 0 {
		v, ok := skuStack.Pop()
		fmt.Printf("出栈：%s（ok=%v）\n", v, ok)
	}
	_, ok := skuStack.Pop()
	fmt.Println("空栈出栈 ok：", ok)

	// 同一个泛型定义换类型参数即可复用
	var priceStack Stack[float64]
	priceStack.Push(399)
	priceStack.Push(129)
	top, _ := priceStack.Pop()
	fmt.Printf("价格栈顶：%.2f\n", top)

	// Go 不支持方法自有类型参数，需要跨类型转换时用普通泛型函数
	fmt.Println("\n=== 泛型函数转换 ===")
	fmt.Println("名称长度：", Map(names, func(s string) int { return len(s) }))
}
