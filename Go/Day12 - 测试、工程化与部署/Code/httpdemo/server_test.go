// 文件用途：使用 httptest 对 NewHandler 做表驱动式的接口测试
// 运行方式：go test ./httpdemo
package httpdemo

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// doRequest 用 httptest 构造请求并执行，避免真的监听端口。
func doRequest(t *testing.T, method, path, body string) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(method, path, strings.NewReader(body))
	rec := httptest.NewRecorder()
	NewHandler().ServeHTTP(rec, req)
	return rec
}

func TestHealthz(t *testing.T) {
	rec := doRequest(t, http.MethodGet, "/healthz", "")

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d", rec.Code, http.StatusOK)
	}
	if ct := rec.Header().Get("Content-Type"); !strings.Contains(ct, "application/json") {
		t.Fatalf("Content-Type = %q, want application/json", ct)
	}

	var body healthResponse
	if err := json.NewDecoder(rec.Body).Decode(&body); err != nil {
		t.Fatalf("解码响应失败: %v", err)
	}
	if body.Status != "ok" {
		t.Fatalf("status = %q, want ok", body.Status)
	}
	if body.Time == "" {
		t.Fatal("time 不应为空")
	}
}

func TestEcho(t *testing.T) {
	tests := []struct {
		name        string
		body        string
		wantStatus  int
		wantMessage string
		wantLength  int
	}{
		{name: "普通消息", body: `{"message":"hello"}`, wantStatus: http.StatusOK, wantMessage: "hello", wantLength: 5},
		{name: "中文按字符计数", body: `{"message":"你好，Go"}`, wantStatus: http.StatusOK, wantMessage: "你好，Go", wantLength: 5},
		{name: "空消息", body: `{"message":""}`, wantStatus: http.StatusBadRequest},
		{name: "非法 JSON", body: `{"message":`, wantStatus: http.StatusBadRequest},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rec := doRequest(t, http.MethodPost, "/api/echo", tt.body)
			if rec.Code != tt.wantStatus {
				t.Fatalf("status = %d, want %d", rec.Code, tt.wantStatus)
			}
			if tt.wantStatus != http.StatusOK {
				var errBody errorResponse
				if err := json.NewDecoder(rec.Body).Decode(&errBody); err != nil {
					t.Fatalf("解码错误响应失败: %v", err)
				}
				if errBody.Error == "" {
					t.Fatal("错误响应不应为空")
				}
				return
			}

			var body echoResponse
			if err := json.NewDecoder(rec.Body).Decode(&body); err != nil {
				t.Fatalf("解码响应失败: %v", err)
			}
			if body.Message != tt.wantMessage || body.Length != tt.wantLength {
				t.Fatalf("got %+v, want message=%q length=%d", body, tt.wantMessage, tt.wantLength)
			}
		})
	}
}

func TestMethodNotAllowed(t *testing.T) {
	tests := []struct {
		name   string
		method string
		path   string
	}{
		{name: "健康检查只允许 GET", method: http.MethodPost, path: "/healthz"},
		{name: "回显只允许 POST", method: http.MethodGet, path: "/api/echo"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rec := doRequest(t, tt.method, tt.path, "")
			if rec.Code != http.StatusMethodNotAllowed {
				t.Fatalf("status = %d, want %d", rec.Code, http.StatusMethodNotAllowed)
			}
		})
	}
}

func TestNotFound(t *testing.T) {
	rec := doRequest(t, http.MethodGet, "/not-exist", "")
	if rec.Code != http.StatusNotFound {
		t.Fatalf("status = %d, want %d", rec.Code, http.StatusNotFound)
	}
}
