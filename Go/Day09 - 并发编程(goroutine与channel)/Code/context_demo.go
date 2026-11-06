// 文件用途：演示 context.WithTimeout 模拟上游调用、WithCancel 手动取消、Value 传递 requestID
// 运行方式：go run -race context_demo.go
package main

import (
	"context"
	"fmt"
	"time"
)

// ctxKey 使用自定义类型作为 key，避免与其他包的 key 冲突。
type ctxKey string

const requestIDKey ctxKey = "requestID"

// callLLM 模拟调用上游大模型，同时监听 ctx 的取消与超时。
func callLLM(ctx context.Context, prompt string) (string, error) {
	reqID, _ := ctx.Value(requestIDKey).(string)
	fmt.Printf("[%s] 开始调用上游 LLM：%s\n", reqID, prompt)

	select {
	case <-time.After(30 * time.Millisecond):
		return "推荐文案：这款商品适合日常通勤", nil
	case <-ctx.Done():
		return "", ctx.Err()
	}
}

func main() {
	fmt.Println("=== 1. WithTimeout：预算充足，调用成功 ===")
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()
	ctx = context.WithValue(ctx, requestIDKey, "req-1001")
	reply, err := callLLM(ctx, "为 iPhone 15 写一句推荐语")
	if err != nil {
		fmt.Println("调用失败：", err)
	} else {
		fmt.Println("调用成功：", reply)
	}

	fmt.Println("\n=== 2. WithTimeout：预算过短，触发 DeadlineExceeded ===")
	ctx2, cancel2 := context.WithTimeout(context.Background(), 10*time.Millisecond)
	defer cancel2()
	ctx2 = context.WithValue(ctx2, requestIDKey, "req-1002")
	if _, err := callLLM(ctx2, "为 MacBook Pro 写推荐语"); err != nil {
		fmt.Println("调用失败：", err)
	}

	fmt.Println("\n=== 3. WithCancel：用户断开连接，主动取消 ===")
	ctx3, cancel3 := context.WithCancel(context.Background())
	ctx3 = context.WithValue(ctx3, requestIDKey, "req-1003")
	done := make(chan struct{})
	go func() {
		defer close(done)
		_, err := callLLM(ctx3, "生成 100 条商品描述")
		fmt.Println("后台任务收到错误：", err)
	}()
	time.Sleep(10 * time.Millisecond)
	cancel3() // 模拟客户端关闭连接
	<-done
	fmt.Println("主协程：已确认后台任务退出")

	// WithValue 只传请求域数据：requestID、traceID、租户 ID、鉴权主体；
	// 不要传数据库连接、配置对象等长生命周期依赖。
	fmt.Println("\n当前 requestID：", ctx.Value(requestIDKey))
}
