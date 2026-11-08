// 文件用途：最小 HTTP 服务，演示 ServeMux、HandlerFunc、查询参数与 JSON 响应
// 运行方式：go run basic_server.go
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"strconv"
	"time"
)

const addr = ":8081"

// helloResponse 是 GET /hello 的响应结构，字段标签决定 JSON 键名。
type helloResponse struct {
	Message string `json:"message"`
	Name    string `json:"name"`
	Count   int    `json:"count"`
	Time    string `json:"time"`
}

// writeJSON 是所有处理器共用的响应工具：先写头，再写状态码，最后编码响应体。
func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Printf("写入响应失败: %v", err)
	}
}

// handleHello 处理 GET /hello，支持 name 与 count 两个查询参数。
func handleHello(w http.ResponseWriter, r *http.Request) {
	name := r.URL.Query().Get("name")
	if name == "" {
		name = "AI 全栈学习者"
	}

	// 查询参数都是字符串，需要自行转换；非法值回退默认值，而不是报错。
	count, err := strconv.Atoi(r.URL.Query().Get("count"))
	if err != nil || count <= 0 {
		count = 1
	}
	if count > 5 {
		count = 5 // 简单限幅，避免示例服务被滥用
	}

	writeJSON(w, http.StatusOK, helloResponse{
		Message: "Hello, Go Web!",
		Name:    name,
		Count:   count,
		Time:    time.Now().Format(time.RFC3339),
	})
}

// handleHealth 演示“函数 → HandlerFunc → Handler”的显式转换过程。
func handleHealth(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{
		"status": "ok",
		"method": r.Method,
	})
}

func main() {
	// 1. Go 1.22 的 ServeMux 支持“方法 + 路径”模式。
	mux := http.NewServeMux()
	mux.HandleFunc("GET /hello", handleHello)

	// 2. 普通函数签名与 HandlerFunc 一致，显式转换后即可作为 Handler 注册。
	var health http.Handler = http.HandlerFunc(handleHealth)
	mux.Handle("GET /healthz", health)

	// 3. 兜底路由：区分“路径存在但方法错误”与“路径不存在”。
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/hello" || r.URL.Path == "/healthz" {
			writeJSON(w, http.StatusMethodNotAllowed, map[string]string{
				"error": "方法不允许，请使用 GET",
			})
			return
		}
		writeJSON(w, http.StatusNotFound, map[string]string{
			"error": "路由不存在，请访问 GET /hello 或 GET /healthz",
		})
	})

	srv := &http.Server{
		Addr:              addr,
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second, // 防止慢速请求头长期占用连接
	}

	log.Printf("基础服务已启动：http://localhost%s/hello", addr)
	// ListenAndServe 在正常关闭时返回 ErrServerClosed，需要排除该情况。
	if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("服务异常退出: %v", err)
	}
}