// 文件用途：封装对上游 OpenAI 兼容 Chat Completions 接口的调用，含超时与重试
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

const (
	maxRetries  = 2                      // 首次请求失败后最多再重试 2 次
	baseBackoff = 100 * time.Millisecond // 指数退避基数
)

// ChatMessage 表示一条对话消息。
type ChatMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// ChatRequest 兼容 OpenAI Chat Completions 的请求体。
// Stream 字段暂时保留：本项目只实现非流式响应，流式扩展见 README。
type ChatRequest struct {
	Model       string        `json:"model,omitempty"`
	Messages    []ChatMessage `json:"messages"`
	Temperature float64       `json:"temperature,omitempty"`
	Stream      bool          `json:"stream,omitempty"`
}

// ChatChoice 表示上游返回的一个候选结果。
type ChatChoice struct {
	Index   int         `json:"index"`
	Message ChatMessage `json:"message"`
}

// Usage 表示 token 使用量。
type Usage struct {
	PromptTokens     int `json:"prompt_tokens"`
	CompletionTokens int `json:"completion_tokens"`
	TotalTokens      int `json:"total_tokens"`
}

// ChatResponse 兼容 OpenAI 的响应结构。
// Error 用于兼容上游把错误信息放在 200 响应体中的少数实现。
type ChatResponse struct {
	ID      string         `json:"id"`
	Object  string         `json:"object"`
	Model   string         `json:"model"`
	Choices []ChatChoice   `json:"choices"`
	Usage   Usage          `json:"usage"`
	Error   *UpstreamError `json:"error,omitempty"`
}

// UpstreamError 表示上游返回的非 2xx 错误，携带状态码便于上层映射。
type UpstreamError struct {
	StatusCode int    `json:"-"`
	Type       string `json:"type,omitempty"`
	Code       string `json:"code,omitempty"`
	Message    string `json:"message"`
}

// Error 实现 error 接口。
func (e *UpstreamError) Error() string {
	return fmt.Sprintf("upstream error: status=%d type=%s code=%s message=%s",
		e.StatusCode, e.Type, e.Code, e.Message)
}

// upstreamErrorBody 对应 OpenAI 的错误响应体：{"error": {...}}。
type upstreamErrorBody struct {
	Error struct {
		Type    string `json:"type"`
		Code    string `json:"code"`
		Message string `json:"message"`
	} `json:"error"`
}

// Client 封装对上游 LLM 的 HTTP 调用。
type Client struct {
	httpClient  *http.Client
	upstreamURL string
	apiKey      string
	model       string
}

// NewClient 根据配置创建上游客户端，超时由 http.Client 统一控制。
func NewClient(cfg Config) *Client {
	return &Client{
		httpClient:  &http.Client{Timeout: cfg.Timeout},
		upstreamURL: cfg.UpstreamURL,
		apiKey:      cfg.APIKey,
		model:       cfg.Model,
	}
}

// Chat 调用上游对话接口。仅对 429、5xx 与网络错误做指数退避重试。
func (c *Client) Chat(ctx context.Context, req ChatRequest) (*ChatResponse, error) {
	if req.Model == "" {
		req.Model = c.model
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("编码上游请求失败: %w", err)
	}

	var lastErr error
	for attempt := 0; attempt <= maxRetries; attempt++ {
		if attempt > 0 {
			// 指数退避：100ms、200ms，等待期间响应 context 取消。
			backoff := baseBackoff << (attempt - 1)
			select {
			case <-ctx.Done():
				return nil, fmt.Errorf("等待重试时请求已取消: %w", ctx.Err())
			case <-time.After(backoff):
			}
		}

		resp, retryable, err := c.doOnce(ctx, body)
		if err == nil {
			return resp, nil
		}
		lastErr = err
		if !retryable {
			return nil, err
		}
	}
	return nil, fmt.Errorf("上游请求重试 %d 次后仍失败: %w", maxRetries, lastErr)
}

// doOnce 发起一次上游请求，返回响应、是否可重试以及错误。
func (c *Client) doOnce(ctx context.Context, body []byte) (*ChatResponse, bool, error) {
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, c.upstreamURL, bytes.NewReader(body))
	if err != nil {
		return nil, false, fmt.Errorf("构造上游请求失败: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")
	if c.apiKey != "" {
		httpReq.Header.Set("Authorization", "Bearer "+c.apiKey)
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		// context 已取消或超时属于调用方主动结束，不再重试。
		if ctx.Err() != nil {
			return nil, false, fmt.Errorf("上游请求已取消: %w", err)
		}
		return nil, true, fmt.Errorf("调用上游失败: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		raw, _ := io.ReadAll(io.LimitReader(resp.Body, 64<<10))
		upErr := &UpstreamError{
			StatusCode: resp.StatusCode,
			Message:    strings.TrimSpace(string(raw)),
		}
		if upErr.Message == "" {
			upErr.Message = http.StatusText(resp.StatusCode)
		}
		var parsed upstreamErrorBody
		if json.Unmarshal(raw, &parsed) == nil && parsed.Error.Message != "" {
			upErr.Type = parsed.Error.Type
			upErr.Code = parsed.Error.Code
			upErr.Message = parsed.Error.Message
		}
		// 仅 429 与 5xx 值得重试，其余 4xx 是请求本身的问题。
		retryable := resp.StatusCode == http.StatusTooManyRequests || resp.StatusCode >= 500
		return nil, retryable, upErr
	}

	var out ChatResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, false, fmt.Errorf("解析上游响应失败: %w", err)
	}
	return &out, false, nil
}
