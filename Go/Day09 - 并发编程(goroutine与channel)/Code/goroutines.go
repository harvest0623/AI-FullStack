// 文件用途：演示 goroutine 启动、sync.WaitGroup 等待、闭包捕获循环变量与参数传递
// 运行方式：go run -race goroutines.go
package main

import (
	"fmt"
	"sync"
	"time"
)

// fetchProduct 模拟一次商品信息查询，耗时随商品编号变化。
func fetchProduct(id int) string {
	time.Sleep(time.Duration(20+id*10) * time.Millisecond)
	return fmt.Sprintf("商品#%d 价格 %.2f 元", id, float64(99+id*50))
}

func main() {
	fmt.Println("=== 1. 最简单的 goroutine ===")
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		fmt.Println("后台任务：正在刷新 eshop 商品缓存...")
		time.Sleep(50 * time.Millisecond)
		fmt.Println("后台任务：缓存刷新完成")
	}()
	fmt.Println("主 goroutine：继续处理请求")
	wg.Wait()
	fmt.Println("主 goroutine：后台任务已结束，安全退出")
	fmt.Println()

	fmt.Println("=== 2. 并发查询多个商品（WaitGroup 等待） ===")
	start := time.Now()
	ids := []int{1, 2, 3, 4, 5}
	results := make([]string, len(ids))
	for i, id := range ids {
		wg.Add(1)
		// 通过参数显式传入下标与商品 ID，是跨版本都安全的写法。
		go func(idx, productID int) {
			defer wg.Done()
			results[idx] = fetchProduct(productID)
		}(i, id)
	}
	wg.Wait()
	for _, r := range results {
		fmt.Println(r)
	}
	fmt.Printf("并发耗时：%v\n", time.Since(start).Round(time.Millisecond))
	fmt.Println()

	fmt.Println("=== 3. Go 1.22 循环变量语义 ===")
	// Go 1.22 起，for 循环的每次迭代都会创建独立的循环变量，
	// 因此下面直接闭包捕获 i 也是安全的；旧版本必须写成
	// go func(n int) { ... }(i)。
	var wg22 sync.WaitGroup
	for i := 1; i <= 3; i++ {
		wg22.Add(1)
		go func() {
			defer wg22.Done()
			time.Sleep(time.Duration(i*10) * time.Millisecond)
			fmt.Printf("协程 %d 完成\n", i)
		}()
	}
	wg22.Wait()
	fmt.Println("全部协程结束")
}
