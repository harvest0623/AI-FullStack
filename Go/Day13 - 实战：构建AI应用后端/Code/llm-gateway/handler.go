// 文件用途：HTTP 处理器与路由注册，负责请求校验、调用上游与错误映射
package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"net"
	"net/http"
)

// Server 持有网关运行所需的依赖。
type Server struct {
	cfg     Config
	client  *Client
	limiter *rateLimiter
}

// NewServer 根据配置构造网关服务。
func NewServer(cfg Config) *Server {
	return &Server{
		cfg:     cfg,
		client:  NewClient(cfg),
		limiter: newRateLimiter(cfg.RateLimitPerMinute),
	}
}

// Routes 注册路由并包装中间件链。
func (s *Server) Routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", s.handleHealth)
	mux.HandleFunc("POST /v1/chat", s.handleChat)

	// 声明顺序即执行顺序：请求 ID → panic 恢复 → 日志 → CORS → 限流 → 业务。
	return chain(mux,
		requestIDMiddleware,
		recoverMiddleware,
		loggingMiddleware,
		corsMiddleware,
		rateLimitMiddleware(s.limiter),
	)
}

// handleHealth 返回服务名、默认模型与健康状态。
func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{
		"service": "llm-gateway",
		"status":  "ok",
		"model":   s.cfg.Model,
	})
}

// handleChat 校验请求后转发给上游，并把上游错误映射为网关状态码。
func (s *Server) handleChat(w http.ResponseWriter, r *http.Request) {
	// 限制请求体大小，防止大报文打满内存。
	r.Body = http.MaxBytesReader(w, r.Body, s.cfg.MaxBodyBytes)

	var req ChatRequest
	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()
	if err := dec.Decode(&req); err != nil {
		var maxErr *http.MaxBytesError
		if errors.As(err, &maxErr) {
			writeError(w, http.StatusRequestEntityTooLarge, "request_too_large", "请求体超过大小限制")
			return
		}
		writeError(w, http.StatusBadRequest, "invalid_json", "请求体不是合法的 JSON: "+err.Error())
		return
	}

	if len(req.Messages) == 0 {
		writeError(w, http.StatusBadRequest, "invalid_messages", "messages 不能为空")
		return
	}
	for i, msg := range req.Messages {
		if msg.Role == "" || msg.Content == "" {
			writeError(w, http.StatusBadRequest, "invalid_messages",
				fmt.Sprintf("messages[%d] 的 role 与 content 不能为空", i))
			return
		}
	}

	resp, err := s.client.Chat(r.Context(), req)
	if err != nil {
		s.writeUpstreamError(w, r, err)
		return
	}
	writeJSON(w, http.StatusOK, resp)
}

// writeUpstreamError 将客户端错误映射为对调用方友好的状态码与统一错误结构。
func (s *Server) writeUpstreamError(w http.ResponseWriter, r *http.Request, err error) {
	var upErr *UpstreamError
	if errors.As(err, &upErr) {
		status := http.StatusBadGateway
		code := "upstream_error"
		switch {
		case upErr.StatusCode == http.StatusTooManyRequests:
			status = http.StatusTooManyRequests
			code = "upstream_rate_limited"
			w.Header().Set("Retry-After", "1")
		case upErr.StatusCode == http.StatusUnauthorized || upErr.StatusCode == http.StatusForbidden:
			// 上游鉴权失败属于网关配置问题，不把 401 直接透传给业务方。
			code = "upstream_auth_failed"
		case upErr.StatusCode >= 400 && upErr.StatusCode < 500:
			status = http.StatusBadRequest
			code = "upstream_bad_request"
		}
		slog.Warn("上游返回错误",
			"request_id", requestIDFromContext(r.Context()),
			"upstream_status", upErr.StatusCode,
			"message", upErr.Message,
		)
		writeError(w, status, code, upErr.Message)
		return
	}

	var netErr net.Error
	if errors.As(err, &netErr) && netErr.Timeout() {
		writeError(w, http.StatusGatewayTimeout, "upstream_timeout", "上游请求超时或已取消")
		return
	}

	if errors.Is(err, context.DeadlineExceeded) || errors.Is(err, context.Canceled) {
		writeError(w, http.StatusGatewayTimeout, "upstream_timeout", "上游请求超时或已取消")
		return
	}

	slog.Error("调用上游失败",
		"request_id", requestIDFromContext(r.Context()),
		"error", err,
	)
	writeError(w, http.StatusBadGateway, "upstream_unavailable", "上游服务不可用")
}

// errorResponse 是网关统一的错误响应结构。
type errorResponse struct {
	Error apiError `json:"error"`
}

// apiError 描述一个可被客户端识别的错误。
type apiError struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}

// writeJSON 输出 JSON 响应。
func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

// writeError 输出统一错误结构。
func writeError(w http.ResponseWriter, status int, code, message string) {
	writeJSON(w, status, errorResponse{
		Error: apiError{Code: code, Message: message},
	})
}
