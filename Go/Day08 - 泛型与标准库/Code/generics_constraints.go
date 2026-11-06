// 文件用途：演示 any、comparable、~ 底层类型约束、联合约束与自定义 Number 约束
// 运行方式：go run generics_constraints.go
package main

import "fmt"

// Number 约束：允许底层类型为整型或浮点型的任意自定义类型。
type Number interface {
	~int | ~int64 | ~float64
}

// Sum 泛型求和，累加器使用 T 的零值。
func Sum[T Number](nums []T) T {
	var total T
	for _, n := range nums {
		total += n
	}
	return total
}

// Avg 返回 float64；类型集合内所有类型都能转换为 float64。
func Avg[T Number](nums []T) float64 {
	if len(nums) == 0 {
		return 0
	}
	return float64(Sum(nums)) / float64(len(nums))
}

// Contains 使用 comparable 约束，支持 == 比较的类型。
func Contains[T comparable](items []T, target T) bool {
	for _, it := range items {
		if it == target {
			return true
		}
	}
	return false
}

// IndexOf 返回目标首次出现的下标，找不到返回 -1。
func IndexOf[T comparable](items []T, target T) int {
	for i, it := range items {
		if it == target {
			return i
		}
	}
	return -1
}

// Len 只要求 any：能遍历计数，但不能比较或运算。
func Len[T any](items []T) int { return len(items) }

// OrderID 自定义类型，底层是 int，满足 ~int。
type OrderID int

// Price 自定义类型，底层是 float64，满足 ~float64。
type Price float64

func main() {
	fmt.Println("=== 基础类型求和 ===")
	ints := []int{1, 2, 3, 4}
	fmt.Println("Sum([]int)：", Sum(ints))
	fmt.Printf("Avg([]int)：%.2f\n", Avg(ints))

	// 类型推断：T 由实参推断，无需写 Sum[int]
	floats := []float64{19.9, 29.9, 39.9}
	fmt.Printf("Sum([]float64)：%.2f，Avg：%.2f\n", Sum(floats), Avg(floats))

	fmt.Println("\n=== 自定义类型满足 ~ 约束 ===")
	ids := []OrderID{1001, 1002, 1003}
	fmt.Println("Sum([]OrderID)：", Sum(ids))

	prices := []Price{99.5, 199.0}
	fmt.Printf("Sum([]Price)：%.2f\n", float64(Sum(prices)))

	fmt.Println("\n=== comparable 约束 ===")
	skus := []string{"SKU-1001", "SKU-1002"}
	fmt.Println("包含 SKU-1002：", Contains(skus, "SKU-1002"))
	fmt.Println("SKU-1003 下标：", IndexOf(skus, "SKU-1003"))
	fmt.Println("包含订单 1002：", Contains(ids, OrderID(1002)))

	fmt.Println("\n=== any 约束 ===")
	mixed := []any{"键盘", 399, 2.5, true}
	fmt.Println("任意类型元素个数：", Len(mixed))
	// 注意：any 约束下不能写 items[0] == items[1]，编译不通过。

	fmt.Println("\n=== 约束选择的差异 ===")
	fmt.Println("comparable 支持 ==，~string 支持字符串拼接，any 什么都不保证")
}
