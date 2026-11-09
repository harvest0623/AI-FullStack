// 文件用途：可测试的最小 HTTP 服务，提供健康检查与 JSON 回显接口
// 运行方式：go run ./cmd/server（由 cmd/server 调用本包）
package httpdemo

import (
	"encoding/json"
	"net/http"
	"time"
)

type healthResponse struct {
	Status string `json:"status"`
	Time   string `json:"time"`
}

type echoRequest struct {
	Message string `json:"message"`
}

type echoResponse struct {
	Message string `json:"message"`
	Length  int    `json:"length"`
}

type errorResponse struct {
	Error string `json:"error"`
}

// NewHandler 构建路由并返回 http.Handler，便于测试时直接交给 httptest。
func NewHandler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", handleHealth)
	mux.HandleFunc("/api/echo", handleEcho)
	return mux
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "仅支持 GET")
		return
	}
	writeJSON(w, http.StatusOK, healthResponse{
		Status: "ok",
		Time:   time.Now().Format(time.RFC3339),
	})
}

func handleEcho(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "仅支持 POST")
		return
	}

	var req echoRequest
	dec := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20))
	if err := dec.Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "请求体不是合法 JSON")
		return
	}
	if req.Message == "" {
		writeError(w, http.StatusBadRequest, "message 不能为空")
		return
	}
	writeJSON(w, http.StatusOK, echoResponse{
		Message: req.Message,
		Length:  len([]rune(req.Message)),
	})
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func writeError(w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, errorResponse{Error: msg})
}
