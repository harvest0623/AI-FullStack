// 文件用途：演示多返回值、命名返回值、可变参数、递归与函数作为参数/返回值
// 运行方式：go run functions.go
package main

import "fmt"

// applyDiscount 返回折后价与优惠金额。
func applyDiscount(price, rate float64) (float64, float64) {
	discount := price * rate
	return price - discount, discount
}

// splitOrder 使用命名返回值表示"每人应付"与"最后一人应付"。
func splitOrder(total float64, n int) (per float64, remainder float64) {
	if n <= 0 {
		return 0, total
	}
	per = total / float64(n)
	remainder = total - per*float64(n-1)
	return
}

// sumAll 使用可变参数，nums 在函数内部是 []int。
func sumAll(label string, nums ...int) int {
	total := 0
	for _, n := range nums {
		total += n
	}
	fmt.Printf("%s：共 %d 项，合计 %d\n", label, len(nums), total)
	return total
}

// factorial 递归计算阶乘，n <= 1 时为终止条件。
func factorial(n int) int {
	if n <= 1 {
		return 1
	}
	return n * factorial(n-1)
}

// filter 接收函数作为参数，返回满足条件的元素。
func filter(nums []int, keep func(int) bool) []int {
	result := make([]int, 0, len(nums))
	for _, n := range nums {
		if keep(n) {
			result = append(result, n)
		}
	}
	return result
}

// multiplier 返回一个乘以固定系数的函数。
func multiplier(factor int) func(int) int {
	return func(n int) int {
		return n * factor
	}
}

func main() {
	// 1. 多返回值
	final, saved := applyDiscount(5999, 0.15)
	fmt.Printf("=== 多返回值 ===\n原价 5999.00，折后 %.2f，优惠 %.2f\n", final, saved)

	// 2. 命名返回值
	per, remainder := splitOrder(100, 3)
	fmt.Printf("\n=== 命名返回值 ===\n每人 %.2f 元，最后一人 %.2f 元\n", per, remainder)

	// 3. 可变参数：传值、传切片展开
	fmt.Println("\n=== 可变参数 ===")
	total := sumAll("订单金额", 5999, 899, 3499)
	extra := []int{120, 80}
	fmt.Printf("合计 %d，追加后 %d\n", total, sumAll("追加金额", extra...))

	// 4. 递归
	fmt.Printf("\n=== 递归 ===\n5! = %d\n", factorial(5))

	// 5. 函数作为参数
	fmt.Println("\n=== 函数作为参数 ===")
	nums := []int{120, 35, 88, 200, 15}
	lowStock := filter(nums, func(n int) bool { return n < 50 })
	even := filter(nums, func(n int) bool { return n%2 == 0 })
	fmt.Printf("低库存：%v\n偶数：%v\n", lowStock, even)

	// 6. 函数作为返回值
	fmt.Println("\n=== 函数作为返回值 ===")
	double := multiplier(2)
	triple := multiplier(3)
	fmt.Printf("double(21)=%d triple(21)=%d\n", double(21), triple(21))
}
