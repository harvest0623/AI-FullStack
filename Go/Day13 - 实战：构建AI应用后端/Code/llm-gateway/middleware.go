// 文件用途：请求 ID、日志、panic 恢复、CORS 与固定窗口限流中间件
package main

import (
	"context"
	"log/slog"
	"net/http"
	"strconv"
	"sync"
	"sync/atomic"
	"time"
)

// contextKey 是自定义 context 键类型，避免与其它包冲突。
type contextKey string

const requestIDKey contextKey = "request_id"

// requestCounter 为每个请求生成递增 ID，进程重启后重新计数。
var requestCounter atomic.Uint64

// requestIDMiddleware 生成请求 ID，写入 context 与响应头。
func requestIDMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		id := "req-" + strconv.FormatUint(requestCounter.Add(1), 10)
		w.Header().Set("X-Request-ID", id)
		ctx := context.WithValue(r.Context(), requestIDKey, id)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// requestIDFromContext 取出请求 ID，不存在时返回空字符串。
func requestIDFromContext(ctx context.Context) string {
	if id, ok := ctx.Value(requestIDKey).(string); ok {
		return id
	}
	return ""
}

// statusRecorder 记录响应状态码，供日志中间件使用。
type statusRecorder struct {
	http.ResponseWriter
	status int
}

// WriteHeader 记录首次写入的状态码。
func (r *statusRecorder) WriteHeader(code int) {
	if r.status == 0 {
		r.status = code
	}
	r.ResponseWriter.WriteHeader(code)
}

// Write 在未显式调用 WriteHeader 时按 200 记录。
func (r *statusRecorder) Write(b []byte) (int, error) {
	if r.status == 0 {
		r.status = http.StatusOK
	}
	return r.ResponseWriter.Write(b)
}

// loggingMiddleware 使用 slog 记录方法、路径、状态码、耗时与请求 ID。
func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rec := &statusRecorder{ResponseWriter: w}
		next.ServeHTTP(rec, r)
		if rec.status == 0 {
			rec.status = http.StatusOK
		}
		slog.Info("http 请求",
			"method", r.Method,
			"path", r.URL.Path,
			"status", rec.status,
			"duration_ms", time.Since(start).Milliseconds(),
			"request_id", requestIDFromContext(r.Context()),
		)
	})
}

// recoverMiddleware 捕获下游 panic，返回 500 并记录日志。
func recoverMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				slog.Error("捕获到 panic",
					"request_id", requestIDFromContext(r.Context()),
					"panic", rec,
				)
				writeError(w, http.StatusInternalServerError, "internal_error", "服务内部错误")
			}
		}()
		next.ServeHTTP(w, r)
	})
}

// corsMiddleware 允许浏览器跨域调用，并直接响应预检请求。
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Request-ID")
		w.Header().Set("Access-Control-Expose-Headers", "X-Request-ID, Retry-After")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}

// rateLimiter 是按分钟固定窗口计数的简单限流器，适用于单实例部署。
type rateLimiter struct {
	mu     sync.Mutex
	limit  int
	window time.Time
	count  int
}

// newRateLimiter 创建限流器，limit <= 0 表示不限制。
func newRateLimiter(limit int) *rateLimiter {
	return &rateLimiter{limit: limit}
}

// Allow 判断当前请求是否放行，并返回建议的重试等待秒数。
func (l *rateLimiter) Allow(now time.Time) (bool, int) {
	if l.limit <= 0 {
		return true, 0
	}

	l.mu.Lock()
	defer l.mu.Unlock()

	if l.window.IsZero() || now.Sub(l.window) >= time.Minute {
		l.window = now
		l.count = 0
	}
	if l.count >= l.limit {
		remain := l.window.Add(time.Minute).Sub(now)
		retry := int((remain + time.Second - 1) / time.Second)
		if retry < 1 {
			retry = 1
		}
		return false, retry
	}
	l.count++
	return true, 0
}

// rateLimitMiddleware 对除健康检查外的请求执行限流。
func rateLimitMiddleware(l *rateLimiter) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path == "/healthz" {
				next.ServeHTTP(w, r)
				return
			}
			ok, retry := l.Allow(time.Now())
			if !ok {
				w.Header().Set("Retry-After", strconv.Itoa(retry))
				writeError(w, http.StatusTooManyRequests, "rate_limited", "请求过于频繁，请稍后重试")
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

// chain 按声明顺序从外到内包装处理器：chain(h, a, b) 等价于 a(b(h))。
func chain(h http.Handler, mw ...func(http.Handler) http.Handler) http.Handler {
	for i := len(mw) - 1; i >= 0; i-- {
		h = mw[i](h)
	}
	return h
}
