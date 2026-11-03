// 文件用途：演示闭包计数器、闭包共享状态、Go 1.22 循环变量语义与 defer 执行顺序
// 运行方式：go run closures.go
package main

import "fmt"

// newCounter 返回带独立状态的计数器闭包。
func newCounter() func() int {
	count := 0
	return func() int {
		count++
		return count
	}
}

// accumulate 返回两个共享同一变量的闭包：累加与读取。
func accumulate(base int) (func(int) int, func() int) {
	total := base
	add := func(n int) int {
		total += n
		return total
	}
	get := func() int {
		return total
	}
	return add, get
}

// trace 返回一个延迟执行的收尾函数，模拟函数级 defer 的典型用法。
func trace(name string) func() {
	fmt.Printf("→ 进入 %s\n", name)
	return func() {
		fmt.Printf("← 退出 %s\n", name)
	}
}

func main() {
	// 1. 闭包计数器：每次调用 newCounter 都得到独立状态
	fmt.Println("=== 闭包计数器 ===")
	c1 := newCounter()
	c2 := newCounter()
	fmt.Printf("c1: %d %d %d\n", c1(), c1(), c1())
	fmt.Printf("c2: %d（与 c1 互不影响）\n", c2())

	// 2. 闭包共享外部变量
	fmt.Println("\n=== 闭包共享状态 ===")
	add, get := accumulate(100)
	add(50)
	add(25)
	fmt.Printf("累计结果：%d\n", get())

	// 3. 循环变量捕获：Go 1.22 起每次迭代都是新变量
	fmt.Println("\n=== 循环变量捕获（Go 1.22+） ===")
	funcs := make([]func() int, 0, 3)
	for i := 0; i < 3; i++ {
		funcs = append(funcs, func() int { return i })
	}
	for idx, f := range funcs {
		fmt.Printf("funcs[%d]() = %d\n", idx, f())
	}

	// 4. defer 后进先出
	fmt.Println("\n=== defer 执行顺序 ===")
	defer fmt.Println("main 结束")
	for i := 1; i <= 3; i++ {
		defer fmt.Printf("第 %d 个 defer\n", i)
	}
	fmt.Println("defer 注册完毕，准备返回")

	// 5. defer 的参数在注册时求值
	fmt.Println("\n=== defer 参数求值时机 ===")
	price := 100.0
	defer fmt.Printf("defer 注册时捕获 price = %.2f\n", price)
	price = 200.0
	fmt.Printf("price 已改为 %.2f\n", price)

	// 6. 函数级 defer：成对出现的进入/退出日志
	done := trace("queryProducts")
	defer done()
	fmt.Println("查询商品中...")
}
