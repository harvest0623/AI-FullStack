// 文件用途：演示无缓冲/有缓冲 channel、阻塞、close、range、单向 channel 与简单 pipeline
// 运行方式：go run -race channels.go
package main

import (
	"fmt"
	"time"
)

// generate 返回一个只读 channel，依次发送商品编号。
func generate(ids ...int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out) // 发送方负责关闭，range 才能正常结束
		for _, id := range ids {
			out <- id
		}
	}()
	return out
}

// priceOf 是 pipeline 的第二段：接收商品编号，发送模拟价格。
func priceOf(in <-chan int) <-chan float64 {
	out := make(chan float64)
	go func() {
		defer close(out)
		for id := range in {
			out <- float64(id * 100)
		}
	}()
	return out
}

func main() {
	fmt.Println("=== 1. 无缓冲 channel：发送与接收必须同时就绪 ===")
	ch := make(chan string)
	go func() {
		fmt.Println("发送方：准备发送订单状态")
		ch <- "订单已支付"
		fmt.Println("发送方：接收方已取走，可以继续")
	}()
	fmt.Println("接收方：收到", <-ch)
	time.Sleep(20 * time.Millisecond)

	fmt.Println("\n=== 2. 有缓冲 channel：缓冲未满不阻塞 ===")
	buf := make(chan int, 3)
	buf <- 101
	buf <- 102
	fmt.Printf("缓冲区中已有 %d 条商品消息（容量 3），发送方未阻塞\n", len(buf))
	fmt.Println("接收：", <-buf, <-buf)
	close(buf)
	// 关闭后仍可接收完剩余数据，再接收得到零值且 ok == false
	v, ok := <-buf
	fmt.Printf("关闭后接收：value=%d ok=%v\n", v, ok)

	fmt.Println("\n=== 3. close + range 消费 ===")
	nums := make(chan int, 4)
	for i := 1; i <= 4; i++ {
		nums <- i
	}
	close(nums)
	sum := 0
	for n := range nums {
		sum += n
	}
	fmt.Println("range 遍历完毕，累加结果：", sum)

	fmt.Println("\n=== 4. 单向 channel 与 pipeline ===")
	// generate 只写、priceOf 只读，类型系统约束了数据流向。
	// 编号 -> 价格 -> 打印，形成一条流水线。
	prices := priceOf(generate(1, 2, 3))
	total := 0.0
	for p := range prices {
		fmt.Printf("流水线输出价格：%.2f\n", p)
		total += p
	}
	fmt.Printf("总价：%.2f\n", total)
}
