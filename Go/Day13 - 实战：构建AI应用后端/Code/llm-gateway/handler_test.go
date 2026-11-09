// 文件用途：使用 httptest 测试网关的健康检查、对话转发与错误映射
package main

import (
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

// fakeChatResponse 是假上游返回的固定成功响应。
const fakeChatResponse = `{
  "id": "chatcmpl-test",
  "object": "chat.completion",
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "你好，我是测试助手。"}
    }
  ],
  "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18}
}`

// newFakeUpstream 启动一个固定返回指定状态码与响应体的假上游。
func newFakeUpstream(t *testing.T, status int, body string) *httptest.Server {
	t.Helper()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(status)
		_, _ = io.WriteString(w, body)
	}))
	t.Cleanup(srv.Close)
	return srv
}

// newTestGateway 使用假上游地址构造网关测试服务。
func newTestGateway(t *testing.T, upstreamURL string) *httptest.Server {
	t.Helper()
	cfg := Config{
		Port:               8080,
		UpstreamURL:        upstreamURL,
		APIKey:             "test-key",
		Model:              "gpt-4o-mini",
		Timeout:            2 * time.Second,
		MaxBodyBytes:       1 << 20,
		RateLimitPerMinute: 1000,
		LogLevel:           "error",
	}
	srv := httptest.NewServer(NewServer(cfg).Routes())
	t.Cleanup(srv.Close)
	return srv
}

// TestHealthz 验证健康检查返回 200 与模型信息。
func TestHealthz(t *testing.T) {
	gateway := newTestGateway(t, "http://127.0.0.1:1")

	resp, err := http.Get(gateway.URL + "/healthz")
	if err != nil {
		t.Fatalf("请求 /healthz 失败: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Fatalf("状态码 = %d，期望 200", resp.StatusCode)
	}
	body, _ := io.ReadAll(resp.Body)
	if !strings.Contains(string(body), "llm-gateway") {
		t.Fatalf("响应缺少服务名: %s", body)
	}
	if !strings.Contains(string(body), "gpt-4o-mini") {
		t.Fatalf("响应缺少模型信息: %s", body)
	}
}

// TestChatSuccess 验证正常对话请求被转发并返回上游内容。
func TestChatSuccess(t *testing.T) {
	upstream := newFakeUpstream(t, http.StatusOK, fakeChatResponse)
	gateway := newTestGateway(t, upstream.URL)

	reqBody := `{"messages":[{"role":"user","content":"你好"}],"temperature":0.2}`
	resp, err := http.Post(gateway.URL+"/v1/chat", "application/json", strings.NewReader(reqBody))
	if err != nil {
		t.Fatalf("请求 /v1/chat 失败: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Fatalf("状态码 = %d，期望 200", resp.StatusCode)
	}
	var got ChatResponse
	if err := json.NewDecoder(resp.Body).Decode(&got); err != nil {
		t.Fatalf("解析响应失败: %v", err)
	}
	if len(got.Choices) != 1 {
		t.Fatalf("choices 数量 = %d，期望 1", len(got.Choices))
	}
	if !strings.Contains(got.Choices[0].Message.Content, "测试助手") {
		t.Fatalf("响应内容不符: %q", got.Choices[0].Message.Content)
	}
}

// TestChatInvalidJSON 验证非法 JSON 返回 400。
func TestChatInvalidJSON(t *testing.T) {
	gateway := newTestGateway(t, "http://127.0.0.1:1")

	resp, err := http.Post(gateway.URL+"/v1/chat", "application/json", strings.NewReader("{invalid"))
	if err != nil {
		t.Fatalf("请求失败: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusBadRequest {
		t.Fatalf("状态码 = %d，期望 400", resp.StatusCode)
	}
}

// TestChatEmptyMessages 验证 messages 为空返回 400。
func TestChatEmptyMessages(t *testing.T) {
	gateway := newTestGateway(t, "http://127.0.0.1:1")

	resp, err := http.Post(gateway.URL+"/v1/chat", "application/json", strings.NewReader(`{"messages":[]}`))
	if err != nil {
		t.Fatalf("请求失败: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusBadRequest {
		t.Fatalf("状态码 = %d，期望 400", resp.StatusCode)
	}
}

// TestChatUpstreamError 验证上游 500 被映射为网关 502。
func TestChatUpstreamError(t *testing.T) {
	upstream := newFakeUpstream(t, http.StatusInternalServerError, `{"error":{"message":"boom","type":"server_error"}}`)
	gateway := newTestGateway(t, upstream.URL)

	reqBody := `{"messages":[{"role":"user","content":"你好"}]}`
	resp, err := http.Post(gateway.URL+"/v1/chat", "application/json", strings.NewReader(reqBody))
	if err != nil {
		t.Fatalf("请求失败: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusBadGateway {
		t.Fatalf("状态码 = %d，期望 502", resp.StatusCode)
	}
	var got errorResponse
	if err := json.NewDecoder(resp.Body).Decode(&got); err != nil {
		t.Fatalf("解析错误响应失败: %v", err)
	}
	if got.Error.Code != "upstream_error" {
		t.Fatalf("错误码 = %q，期望 upstream_error", got.Error.Code)
	}
}

// TestChatMethodNotAllowed 验证错误方法返回 405。
func TestChatMethodNotAllowed(t *testing.T) {
	gateway := newTestGateway(t, "http://127.0.0.1:1")

	resp, err := http.Get(gateway.URL + "/v1/chat")
	if err != nil {
		t.Fatalf("请求失败: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusMethodNotAllowed {
		t.Fatalf("状态码 = %d，期望 405", resp.StatusCode)
	}
}
