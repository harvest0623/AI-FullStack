// 文件用途：演示切片的 make、append、len/cap、copy、区间切片与三索引切片
// 运行方式：go run slices.go
package main

import "fmt"

func main() {
	// 1. 切片的创建方式
	var nilSlice []string      // nil 切片
	lit := []int{1, 2, 3}      // 字面量
	made := make([]int, 2, 5)  // len=2 cap=5
	fmt.Println("=== 创建 ===")
	fmt.Printf("nilSlice=%v len=%d cap=%d isNil=%t\n",
		nilSlice, len(nilSlice), cap(nilSlice), nilSlice == nil)
	fmt.Printf("lit=%v len=%d cap=%d\n", lit, len(lit), cap(lit))
	fmt.Printf("made=%v len=%d cap=%d\n", made, len(made), cap(made))

	// 2. append 与容量增长
	fmt.Println("\n=== append 与容量 ===")
	var list []int
	for i := 1; i <= 6; i++ {
		list = append(list, i)
		fmt.Printf("添加 %d 后 len=%d cap=%d\n", i, len(list), cap(list))
	}
	list = append(list, 7, 8, 9) // 一次追加多个元素
	fmt.Printf("批量追加后：%v len=%d cap=%d\n", list, len(list), cap(list))

	// 3. copy：复制数量取两者长度的较小值
	fmt.Println("\n=== copy ===")
	src := []string{"iPhone 15", "MacBook Pro", "AirPods"}
	dst := make([]string, len(src))
	n := copy(dst, src)
	fmt.Printf("复制了 %d 个元素：%v\n", n, dst)

	// 4. 区间切片：左闭右开，共享底层数组
	fmt.Println("\n=== 区间切片 ===")
	nums := []int{10, 20, 30, 40, 50}
	fmt.Printf("nums[1:3] = %v\n", nums[1:3])
	fmt.Printf("nums[:2]  = %v\n", nums[:2])
	fmt.Printf("nums[3:]  = %v\n", nums[3:])
	fmt.Printf("nums[:0]  = %v len=%d cap=%d\n", nums[:0], len(nums[:0]), cap(nums[:0]))

	// 5. 三索引切片：限制容量，避免 append 覆盖原数据
	fmt.Println("\n=== 三索引切片 ===")
	full := nums[:]
	limited := nums[1:3:3]
	fmt.Printf("full    len=%d cap=%d\n", len(full), cap(full))
	fmt.Printf("limited len=%d cap=%d\n", len(limited), cap(limited))
	limited = append(limited, 999)
	fmt.Printf("append 后 limited=%v\n", limited)
	fmt.Printf("原 nums 未被覆盖：%v\n", nums)
}
