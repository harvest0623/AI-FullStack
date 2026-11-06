// 文件用途：演示 time 时间格式化/解析、Duration、Timer/Ticker、超时模式与 slog 结构化日志
// 运行方式：go run stdlib_time.go
package main

import (
	"fmt"
	"log/slog"
	"os"
	"time"
)

// layout 是自定义布局：Go 用固定参考时间 2006-01-02 15:04:05 表达格式。
const layout = "2006-01-02 15:04:05"

// Order 订单。
type Order struct {
	ID        string
	Amount    float64
	CreatedAt time.Time
}

// callUpstream 模拟调用 LLM 上游，超过 timeout 返回超时错误。
func callUpstream(timeout time.Duration) (string, error) {
	done := make(chan string, 1)
	go func() {
		time.Sleep(100 * time.Millisecond) // 模拟慢服务
		done <- "模型回复：推荐机械键盘"
	}()

	select {
	case reply := <-done:
		return reply, nil
	case <-time.After(timeout):
		return "", fmt.Errorf("上游调用超时（%s）", timeout)
	}
}

func main() {
	// 1. 当前时间与格式化
	now := time.Now()
	fmt.Println("=== 时间格式化 ===")
	fmt.Println("默认输出：", now.Format(layout))
	fmt.Println("仅日期：", now.Format("2006-01-02"))
	fmt.Println("RFC3339：", now.Format(time.RFC3339))

	// 2. 解析字符串时间
	parsed, err := time.Parse(layout, "2026-10-22 09:30:00")
	if err != nil {
		fmt.Println("解析失败：", err)
		return
	}
	fmt.Println("解析结果：", parsed.Format(time.RFC3339))

	// 3. Duration 与 Add / Sub / Until / Since
	fmt.Println("\n=== Duration 与时间运算 ===")
	order := Order{ID: "ORD-001", Amount: 899, CreatedAt: now}
	deadline := order.CreatedAt.Add(30 * time.Minute)
	fmt.Printf("下单：%s，支付截止：%s\n",
		order.CreatedAt.Format(layout), deadline.Format(layout))
	fmt.Printf("距截止还有：%s（约 %.1f 分钟）\n",
		time.Until(deadline), time.Until(deadline).Minutes())

	timeout := 1500 * time.Millisecond
	fmt.Println("超时配置：", timeout, "=", timeout.Milliseconds(), "ms")
	expired := now.Add(-time.Minute)
	fmt.Println("是否已过期：", time.Since(expired) > 0)

	// 4. Timer：单次定时
	fmt.Println("\n=== Timer ===")
	timer := time.NewTimer(60 * time.Millisecond)
	<-timer.C
	fmt.Println("Timer 触发：60ms 到达")

	// 5. Ticker：周期任务，例如定时刷新库存缓存
	fmt.Println("\n=== Ticker ===")
	ticker := time.NewTicker(50 * time.Millisecond)
	defer ticker.Stop() // 必须停止，否则定时器泄漏
	for i := 1; i <= 3; i++ {
		<-ticker.C
		fmt.Printf("第 %d 次刷新库存缓存\n", i)
	}

	// 6. 超时模式：慢上游 + 短超时 = 失败；足够超时 = 成功
	fmt.Println("\n=== 超时模式 ===")
	if reply, err := callUpstream(30 * time.Millisecond); err != nil {
		fmt.Println("调用失败：", err)
	} else {
		fmt.Println("调用成功：", reply)
	}
	if reply, err := callUpstream(200 * time.Millisecond); err != nil {
		fmt.Println("调用失败：", err)
	} else {
		fmt.Println("调用成功：", reply)
	}

	// 7. slog：结构化日志，字段化输出便于采集
	fmt.Println("\n=== slog 结构化日志 ===")
	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))
	logger.Info("订单创建",
		"order_id", order.ID,
		"amount", order.Amount,
		"created_at", order.CreatedAt.Format(time.RFC3339),
	)
	logger.Warn("库存偏低", "sku", "SKU-1001", "stock", 3)

	jsonLogger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	jsonLogger.Info("网关请求",
		"path", "/v1/chat",
		"latency_ms", 128,
		"upstream", "llm",
	)
}
