// 文件用途：演示 worker pool：jobs/results channel、固定 worker 数、WaitGroup 收尾与结果收集
// 运行方式：go run -race worker_pool.go
package main

import (
	"fmt"
	"sync"
	"time"
)

// Job 表示一个待查询价格的商品任务。
type Job struct {
	ProductID int
	Name      string
}

// Result 表示任务的处理结果，嵌入 Job 以复用字段。
type Result struct {
	Job
	Price float64
	Err   error
}

// priceFor 模拟调用价格服务，商品#4 固定返回错误。
func priceFor(id int) (float64, error) {
	time.Sleep(time.Duration(20+id%3*15) * time.Millisecond)
	if id == 4 {
		return 0, fmt.Errorf("商品#%d 价格服务超时", id)
	}
	return float64(100 + id*10), nil
}

// worker 从 jobs 读取任务，处理后写入 results。
func worker(id int, jobs <-chan Job, results chan<- Result, wg *sync.WaitGroup) {
	defer wg.Done()
	for job := range jobs {
		price, err := priceFor(job.ProductID)
		fmt.Printf("worker#%d 处理 %s\n", id, job.Name)
		results <- Result{Job: job, Price: price, Err: err}
	}
}

func main() {
	jobs := make([]Job, 0, 8)
	for i := 1; i <= 8; i++ {
		jobs = append(jobs, Job{ProductID: i, Name: fmt.Sprintf("商品#%d", i)})
	}

	const workerCount = 3
	// 任务与结果都带足够缓冲，避免主协程尚未开始接收时 worker 阻塞。
	jobCh := make(chan Job, len(jobs))
	resultCh := make(chan Result, len(jobs))

	var wg sync.WaitGroup
	for w := 1; w <= workerCount; w++ {
		wg.Add(1)
		go worker(w, jobCh, resultCh, &wg)
	}

	for _, job := range jobs {
		jobCh <- job
	}
	close(jobCh) // 关闭任务队列，worker 的 range 会自然结束

	// 所有 worker 退出后再关闭结果 channel，主协程才能安全地 range。
	go func() {
		wg.Wait()
		close(resultCh)
	}()

	total := 0.0
	success, failed := 0, 0
	for r := range resultCh {
		if r.Err != nil {
			failed++
			fmt.Println("失败：", r.Err)
			continue
		}
		success++
		total += r.Price
		fmt.Printf("完成：%s 价格 %.2f\n", r.Name, r.Price)
	}
	fmt.Printf("\n汇总：成功 %d 个，失败 %d 个，总价 %.2f\n", success, failed, total)
}
