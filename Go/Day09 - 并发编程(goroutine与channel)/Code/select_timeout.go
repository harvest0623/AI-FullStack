// 文件用途：演示 select 多路复用、default 非阻塞、time.After 超时与 done channel 退出
// 运行方式：go run -race select_timeout.go
package main

import (
	"fmt"
	"time"
)

func main() {
	fmt.Println("=== 1. select 多路复用 ===")
	fast := make(chan string)
	slow := make(chan string)
	go func() {
		time.Sleep(30 * time.Millisecond)
		fast <- "商品缓存命中"
	}()
	go func() {
		time.Sleep(80 * time.Millisecond)
		slow <- "数据库查询结果"
	}()
	for i := 0; i < 2; i++ {
		select {
		case msg := <-fast:
			fmt.Println("收到：", msg)
		case msg := <-slow:
			fmt.Println("收到：", msg)
		}
	}

	fmt.Println("\n=== 2. default：非阻塞尝试 ===")
	queue := make(chan string, 1)
	queue <- "待处理订单#1001"
	for i := 0; i < 2; i++ {
		select {
		case order := <-queue:
			fmt.Println("处理：", order)
		default:
			fmt.Println("队列为空，不阻塞，去做别的事")
		}
	}

	fmt.Println("\n=== 3. time.After 超时控制 ===")
	// 给 channel 留 1 个缓冲：即使主协程已超时返回，
	// 上游 goroutine 也能写入后正常退出，不会永久阻塞造成泄漏。
	upstream := make(chan string, 1)
	go func() {
		time.Sleep(120 * time.Millisecond)
		upstream <- "上游 LLM 返回的推荐文案"
	}()
	select {
	case reply := <-upstream:
		fmt.Println("成功：", reply)
	case <-time.After(50 * time.Millisecond):
		fmt.Println("超时：上游 50ms 未响应，返回降级文案")
	}

	fmt.Println("\n=== 4. done channel 通知退出 ===")
	done := make(chan struct{})
	ticks := make(chan int)
	go func() {
		defer close(ticks)
		for i := 1; ; i++ {
			select {
			case <-done:
				fmt.Println("监控协程：收到退出信号，停止采集")
				return
			case ticks <- i:
				// 成功发送一次指标后继续下一次采集
			}
		}
	}()
	for i := 0; i < 3; i++ {
		fmt.Printf("采集到第 %d 个指标\n", <-ticks)
	}
	close(done)
	// 等待监控协程关闭 ticks，确保它干净退出
	for range ticks {
	}
	fmt.Println("主协程：退出流程结束")
}
