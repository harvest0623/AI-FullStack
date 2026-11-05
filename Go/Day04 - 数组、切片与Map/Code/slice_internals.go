// 文件用途：演示切片共享底层数组、append 扩容后脱钩以及 nil 切片与空切片的区别
// 运行方式：go run slice_internals.go
package main

import "fmt"

func main() {
	// 1. 共享底层数组：修改子切片会反映到原切片
	base := []int{1, 2, 3, 4, 5}
	view := base[1:4] // len=3 cap=4，与 base 共享数组
	fmt.Println("=== 共享底层数组 ===")
	fmt.Printf("base=%v view=%v len=%d cap=%d\n", base, view, len(view), cap(view))

	view[0] = 20
	fmt.Printf("修改 view[0] 后 base=%v\n", base)

	base[3] = 40
	fmt.Printf("修改 base[3] 后 view=%v\n", view)

	// 2. append 未扩容时仍共享，扩容后脱钩
	fmt.Println("\n=== append 与扩容 ===")
	s1 := make([]int, 2, 4)
	s1[0], s1[1] = 1, 2
	s2 := append(s1, 3) // 容量足够，写入共享数组
	s2[0] = 100
	fmt.Printf("cap 足够时：s1=%v s2=%v\n", s1, s2)

	s3 := append(s2, 4, 5, 6) // 超过容量，分配新数组
	s3[0] = 999
	fmt.Printf("扩容后：s2=%v s3=%v（已脱钩）\n", s2, s3)

	// 3. 用 copy 切断与原始数据的关联
	fmt.Println("\n=== 用 copy 切断关联 ===")
	origin := []string{"iPhone", "iPad", "Mac"}
	clone := make([]string, len(origin))
	copy(clone, origin)
	clone[0] = "Pixel"
	fmt.Printf("origin=%v clone=%v\n", origin, clone)

	// 4. nil 切片与空切片
	fmt.Println("\n=== nil 切片 vs 空切片 ===")
	var nilSlice []int
	emptySlice := []int{}
	emptyMade := make([]int, 0)

	fmt.Printf("nilSlice   == nil ? %t, len=%d, cap=%d\n",
		nilSlice == nil, len(nilSlice), cap(nilSlice))
	fmt.Printf("emptySlice == nil ? %t, len=%d, cap=%d\n",
		emptySlice == nil, len(emptySlice), cap(emptySlice))
	fmt.Printf("emptyMade  == nil ? %t, len=%d, cap=%d\n",
		emptyMade == nil, len(emptyMade), cap(emptyMade))

	fmt.Printf("三者都可以 append：%v %v %v\n",
		append(nilSlice, 1), append(emptySlice, 2), append(emptyMade, 3))
}
