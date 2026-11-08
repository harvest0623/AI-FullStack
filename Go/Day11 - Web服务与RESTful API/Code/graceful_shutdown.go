// 文件用途：演示 http.Server 超时配置、signal.NotifyContext 与 Shutdown 优雅关闭
// 运行方式：go run graceful_shutdown.go
package main

import (
	"context"
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

const shutdownAddr = ":8084"

// shutdownTimeout 是关闭时等待在途请求的最长时间，超时则强制退出。
const shutdownTimeout = 10 * time.Second

// writeMessage 写出形如 {"message":"..."} 的 JSON 响应。
func writeMessage(w http.ResponseWriter, status int, msg string) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(map[string]string{"message": msg}); err != nil {
		log.Printf("写入响应失败: %v", err)
	}
}

func main() {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) {
		writeMessage(w, http.StatusOK, "ok")
	})

	// 模拟耗时 3 秒的请求：关闭期间它应被允许执行完，而不是被直接切断。
	mux.HandleFunc("GET /slow", func(w http.ResponseWriter, r *http.Request) {
		select {
		case <-time.After(3 * time.Second):
			writeMessage(w, http.StatusOK, "处理完成")
		case <-r.Context().Done():
			log.Println("客户端提前断开连接")
		}
	})

	// 关键超时参数：分别约束请求头、整个读、整个写与空闲连接。
	srv := &http.Server{
		Addr:              shutdownAddr,
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       15 * time.Second,
		WriteTimeout:      15 * time.Second,
		IdleTimeout:       60 * time.Second,
	}

	// NotifyContext 把 SIGINT/SIGTERM 转换为 context 取消信号。
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	// ListenAndServe 会阻塞，放到 goroutine 中，主 goroutine 负责等待信号。
	errCh := make(chan error, 1)
	go func() {
		errCh <- srv.ListenAndServe()
	}()

	log.Printf("服务已启动：http://localhost%s/healthz（Ctrl+C 优雅退出）", shutdownAddr)

	select {
	case err := <-errCh:
		if err != nil && !errors.Is(err, http.ErrServerClosed) {
			log.Printf("服务异常退出: %v", err)
			os.Exit(1)
		}
		log.Println("服务已停止")
	case <-ctx.Done():
		// 恢复默认信号处理：再次按 Ctrl+C 可立即强制结束进程。
		stop()
		log.Println("收到退出信号，开始优雅关闭...")

		shutdownCtx, cancel := context.WithTimeout(context.Background(), shutdownTimeout)
		defer cancel()

		if err := srv.Shutdown(shutdownCtx); err != nil {
			log.Printf("优雅关闭超时（%s），强制退出: %v", shutdownTimeout, err)
			_ = srv.Close()
			os.Exit(1)
		}
		log.Println("在途请求处理完毕，服务正常退出")
	}
}
