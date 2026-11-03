// 文件用途：演示 if 初始化语句、for 三种形态、range 遍历与标签 break/continue
// 运行方式：go run control_flow.go
package main

import "fmt"

func main() {
	// 1. if 带初始化语句：stock 只在该 if/else 内可见
	if stock := 8; stock > 0 {
		fmt.Printf("=== if ===\n有货，剩余 %d 件\n", stock)
	} else {
		fmt.Println("=== if ===\n已售罄")
	}

	// 2. for 的三种形态
	fmt.Println("\n=== for 三种形态 ===")
	sum := 0
	for i := 1; i <= 5; i++ { // 三段式
		sum += i
	}
	fmt.Printf("1+2+...+5 = %d\n", sum)

	count := 3
	for count > 0 { // 条件式，相当于 while
		fmt.Printf("倒计时 %d\n", count)
		count--
	}

	for { // 无限循环，必须自行退出
		fmt.Println("无限循环执行一次后 break")
		break
	}

	// 3. range 遍历切片
	fmt.Println("\n=== range 遍历 ===")
	prices := []float64{5999, 12999, 899}
	for i, p := range prices {
		fmt.Printf("索引 %d，价格 %.2f\n", i, p)
	}

	// range 遍历 Map：顺序随机，不能依赖
	stockMap := map[string]int{"iPhone 15": 120, "MacBook Pro": 15}
	for name, qty := range stockMap {
		fmt.Printf("%s 库存 %d\n", name, qty)
	}

	// 4. 标签 break：一次跳出两层循环
	fmt.Println("\n=== 标签 break ===")
	matrix := [][]int{{1, 2, 3}, {4, 5, 6}, {7, 8, 9}}
	target := 5
found:
	for row := 0; row < len(matrix); row++ {
		for col := 0; col < len(matrix[row]); col++ {
			if matrix[row][col] == target {
				fmt.Printf("在 (%d,%d) 找到 %d\n", row, col, target)
				break found
			}
		}
	}

	// 5. 标签 continue：跳过外层的本次迭代
	fmt.Println("\n=== 标签 continue ===")
rowLoop:
	for row := 0; row < len(matrix); row++ {
		line := ""
		for _, v := range matrix[row] {
			if v%2 == 0 {
				fmt.Printf("第 %d 行出现偶数 %d，跳过整行\n", row, v)
				continue rowLoop
			}
			line += fmt.Sprintf("%d ", v)
		}
		fmt.Printf("第 %d 行的奇数：%s\n", row, line)
	}
}
