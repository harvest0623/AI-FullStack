// 文件用途：演示四个常用中间件（日志、恢复、CORS、请求 ID）与链式组合的执行顺序
// 运行方式：go run middleware.go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"runtime/debug"
	"sync/atomic"
	"time"
)

const mwAddr = ":8083"

// Middleware 是标准的 Handler 包装函数：接收下一个处理器，返回新的处理器。
type Middleware func(http.Handler) http.Handler

// Chain 按传入顺序包装，第一个参数是最外层（最先执行、最后返回）。
func Chain(h http.Handler, mws ...Middleware) http.Handler {
	for i := len(mws) - 1; i >= 0; i-- {
		h = mws[i](h)
	}
	return h
}

// ctxKey 用自定义类型作为 context 键，避免与其他包冲突。
type ctxKey string

const requestIDKey ctxKey = "requestID"

var requestCounter atomic.Uint64

// RequestID 为每个请求生成唯一 ID，写入响应头与 context。
func RequestID(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		id := fmt.Sprintf("req-%d-%d", time.Now().UnixNano(), requestCounter.Add(1))
		w.Header().Set("X-Request-ID", id)
		ctx := context.WithValue(r.Context(), requestIDKey, id)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// statusRecorder 包装 ResponseWriter，记录实际写出的状态码。
type statusRecorder struct {
	http.ResponseWriter
	status int
}

func (r *statusRecorder) WriteHeader(code int) {
	r.status = code
	r.ResponseWriter.WriteHeader(code)
}

// Logging 记录方法、路径、状态码与耗时。
func Logging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rec := &statusRecorder{ResponseWriter: w, status: http.StatusOK}

		next.ServeHTTP(rec, r)

		reqID, _ := r.Context().Value(requestIDKey).(string)
		log.Printf("[%s] %s %s -> %d (%s)", reqID, r.Method, r.URL.Path, rec.status, time.Since(start))
	})
}

// Recover 捕获下游 panic，转为 500，避免整个进程退出。
func Recover(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				log.Printf("[panic] %v\n%s", rec, debug.Stack())
				writeJSON(w, http.StatusInternalServerError, map[string]string{
					"error": "服务器内部错误",
				})
			}
		}()
		next.ServeHTTP(w, r)
	})
}

// CORS 统一添加跨域头，并直接响应预检请求。
func CORS(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, X-Request-ID")

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}

// writeJSON 写出 JSON 响应。
func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Printf("写入响应失败: %v", err)
	}
}

func main() {
	mux := http.NewServeMux()

	// 处理器可以从 context 中取到上游中间件写入的请求 ID。
	mux.HandleFunc("GET /api/ping", func(w http.ResponseWriter, r *http.Request) {
		reqID, _ := r.Context().Value(requestIDKey).(string)
		writeJSON(w, http.StatusOK, map[string]string{
			"message":    "pong",
			"request_id": reqID,
		})
	})

	// 访问 /api/panic 可观察 Recover 中间件的效果。
	mux.HandleFunc("GET /api/panic", func(w http.ResponseWriter, r *http.Request) {
		panic("演示 panic 被中间件捕获")
	})

	// 执行顺序：RequestID → Logging → Recover → CORS → 业务处理器。
	// 响应阶段则反向回到 Logging，因此日志能拿到真实状态码与耗时。
	handler := Chain(mux, RequestID, Logging, Recover, CORS)

	srv := &http.Server{
		Addr:              mwAddr,
		Handler:           handler,
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       10 * time.Second,
		WriteTimeout:      10 * time.Second,
	}

	log.Printf("中间件示例已启动：http://localhost%s/api/ping", mwAddr)
	if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("服务异常退出: %v", err)
	}
}
