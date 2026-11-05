// 文件用途：演示数组的值语义、长度属于类型、数组比较、遍历与二维数组
// 运行方式：go run arrays.go
package main

import "fmt"

func main() {
	// 1. 数组的声明与初始化
	var zeros [3]int                     // 零值数组
	names := [2]string{"iPhone", "iPad"} // 指定长度
	auto := [...]int{10, 20, 30}         // 由元素个数推断长度
	fmt.Println("=== 初始化 ===")
	fmt.Printf("zeros=%v names=%v auto=%v\n", zeros, names, auto)

	// 2. 长度是类型的一部分
	var a [3]int
	var b [3]int
	a[0], b[0] = 1, 1
	fmt.Println("\n=== 长度与比较 ===")
	fmt.Printf("[3]int 之间可以直接比较：%t\n", a == b)
	fmt.Printf("auto 的长度：%d\n", len(auto))
	// var c [4]int = a // 取消注释会编译失败：类型不同

	// 3. 值语义：赋值与传参都是完整复制
	original := [3]int{1, 2, 3}
	copied := original
	copied[0] = 100
	fmt.Println("\n=== 值语义 ===")
	fmt.Printf("original=%v copied=%v\n", original, copied)

	modify := func(arr [3]int) {
		arr[2] = 999 // 只修改副本
	}
	modify(original)
	fmt.Printf("函数内修改后 original=%v（不受影响）\n", original)

	// 4. 遍历数组：range 返回索引与元素副本
	fmt.Println("\n=== 遍历 ===")
	prices := [4]float64{5999, 12999, 899, 3499}
	total := 0.0
	for i, p := range prices {
		fmt.Printf("第 %d 件：%.2f\n", i+1, p)
		total += p
	}
	fmt.Printf("总价：%.2f，均价：%.2f\n", total, total/float64(len(prices)))

	// 5. 二维数组：两个维度都必须是常量
	fmt.Println("\n=== 二维数组 ===")
	grid := [2][3]int{
		{1, 2, 3},
		{4, 5, 6},
	}
	for _, row := range grid {
		for _, v := range row {
			fmt.Printf("%d ", v)
		}
		fmt.Println()
	}
}
