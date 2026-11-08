// 文件用途：演示 HTTP 客户端：GET/POST JSON、状态码检查、超时与 context 控制（本地 httptest 假上游）
// 运行方式：go run http_client.go
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"time"
)

// ChatRequest 是调用上游 LLM 的请求体。
type ChatRequest struct {
	Model     string `json:"model"`
	Prompt    string `json:"prompt"`
	MaxTokens int    `json:"max_tokens"`
}

// ChatResponse 是上游 LLM 的响应体。
type ChatResponse struct {
	Reply string `json:"reply"`
	Usage int    `json:"usage"`
}

func main() {
	// 1. 用 httptest 启动本地假上游，完全离线。
	mux := http.NewServeMux()
	mux.HandleFunc("GET /v1/products/{id}", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{
			"id":    r.PathValue("id"),
			"name":  "iPhone 15",
			"price": 5999,
		})
	})
	mux.HandleFunc("POST /v1/chat", func(w http.ResponseWriter, r *http.Request) {
		var req ChatRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusBadRequest)
			json.NewEncoder(w).Encode(map[string]string{"error": "invalid json"})
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(ChatResponse{
			Reply: fmt.Sprintf("关于「%s」：这款商品性价比不错", req.Prompt),
			Usage: len(req.Prompt),
		})
	})
	mux.HandleFunc("GET /v1/slow", func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(200 * time.Millisecond)
		io.WriteString(w, `{"reply":"迟到的响应"}`)
	})
	server := httptest.NewServer(mux)
	defer server.Close()

	// 2. 复用同一个带超时的 Client，它可被多个 goroutine 并发使用。
	client := &http.Client{Timeout: 2 * time.Second}

	fmt.Println("=== 1. GET 请求并解码 JSON ===")
	resp, err := client.Get(server.URL + "/v1/products/p1001")
	if err != nil {
		fmt.Println("请求失败：", err)
		return
	}
	defer resp.Body.Close() // 必须关闭，否则连接无法复用
	if resp.StatusCode != http.StatusOK {
		fmt.Println("非预期状态码：", resp.Status)
		return
	}
	var product map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&product); err != nil {
		fmt.Println("解码失败：", err)
		return
	}
	fmt.Printf("商品信息：%v\n", product)

	fmt.Println("\n=== 2. POST JSON 并检查响应 ===")
	body, err := json.Marshal(ChatRequest{
		Model:     "eshop-llm",
		Prompt:    "推荐一款降噪耳机",
		MaxTokens: 128,
	})
	if err != nil {
		fmt.Println("序列化失败：", err)
		return
	}
	req, err := http.NewRequest(http.MethodPost, server.URL+"/v1/chat", bytes.NewReader(body))
	if err != nil {
		fmt.Println("构造请求失败：", err)
		return
	}
	req.Header.Set("Content-Type", "application/json")
	resp2, err := client.Do(req)
	if err != nil {
		fmt.Println("请求失败：", err)
		return
	}
	defer resp2.Body.Close()
	fmt.Println("上游状态码：", resp2.StatusCode)
	var chat ChatResponse
	if err := json.NewDecoder(resp2.Body).Decode(&chat); err != nil {
		fmt.Println("解码失败：", err)
		return
	}
	fmt.Printf("LLM 回复：%s（用量 %d）\n", chat.Reply, chat.Usage)

	fmt.Println("\n=== 3. context 超时：提前放弃慢请求 ===")
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()
	req3, err := http.NewRequestWithContext(ctx, http.MethodGet, server.URL+"/v1/slow", nil)
	if err != nil {
		fmt.Println("构造请求失败：", err)
		return
	}
	start := time.Now()
	resp3, err := client.Do(req3)
	elapsed := time.Since(start).Round(time.Millisecond)
	if err != nil {
		// context 超时返回 *url.Error，其内部错误为 context.DeadlineExceeded。
		fmt.Printf("请求被取消（耗时 %v）：%v\n", elapsed, err)
	} else {
		resp3.Body.Close()
		fmt.Printf("意外成功（耗时 %v）：%v\n", elapsed, resp3.Status)
	}

	fmt.Println("\n=== 4. 非 200 响应：读取错误体 ===")
	req4, err := http.NewRequest(http.MethodPost, server.URL+"/v1/chat", bytes.NewReader([]byte("not-json")))
	if err != nil {
		fmt.Println("构造请求失败：", err)
		return
	}
	req4.Header.Set("Content-Type", "application/json")
	resp4, err := client.Do(req4)
	if err != nil {
		fmt.Println("请求失败：", err)
		return
	}
	defer resp4.Body.Close()
	msg, err := io.ReadAll(io.LimitReader(resp4.Body, 4<<10))
	if err != nil {
		fmt.Println("读取错误体失败：", err)
		return
	}
	fmt.Printf("状态码 %d，错误信息：%s\n", resp4.StatusCode, string(msg))
}
