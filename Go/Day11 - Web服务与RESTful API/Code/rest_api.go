// 文件用途：内存商品仓储 + RESTful CRUD 接口，演示路径参数、统一错误与状态码
// 运行方式：go run rest_api.go
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"
)

// Product 是电商商品的资源模型，字段标签决定 JSON 键名。
type Product struct {
	ID    int     `json:"id"`
	Name  string  `json:"name"`
	Price float64 `json:"price"`
	Stock int     `json:"stock"`
}

// ProductStore 用读写锁保护的内存仓储。
type ProductStore struct {
	mu     sync.RWMutex
	items  map[int]Product
	nextID int
}
// store 是进程内的商品仓储，写入两条种子数据。
var store = &ProductStore{items: map[int]Product{
	1: {ID: 1, Name: "iPhone 15", Price: 5999, Stock: 120},
	2: {ID: 2, Name: "MacBook Pro", Price: 12999, Stock: 36},
}, nextID: 3}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Printf("写入响应失败: %v", err)
	}
}
// 统一错误结构：{"code": ..., "message": ...}。
func writeError(w http.ResponseWriter, status int, code, message string) {
	writeJSON(w, status, map[string]string{"code": code, "message": message})
}
// 解析路径参数 {id}，非法时直接写 400。
func pathID(w http.ResponseWriter, r *http.Request) (int, bool) {
	id, err := strconv.Atoi(r.PathValue("id"))
	if err != nil || id <= 0 {
		writeError(w, http.StatusBadRequest, "invalid_id", "id 必须是正整数")
		return 0, false
	}
	return id, true
}
// 解析并校验请求体，失败时已写好 400 响应。
func readProduct(w http.ResponseWriter, r *http.Request) (Product, bool) {
	var p Product
	dec := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&p); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_body", err.Error())
		return p, false
	}
	if strings.TrimSpace(p.Name) == "" || p.Price < 0 || p.Stock < 0 {
		writeError(w, http.StatusBadRequest, "invalid_body", "name 必填，price 与 stock 不得为负")
		return p, false
	}
	return p, true
}

func (s *ProductStore) list(w http.ResponseWriter, r *http.Request) {
	s.mu.RLock()
	out := make([]Product, 0, len(s.items))
	for _, p := range s.items {
		out = append(out, p)
	}
	s.mu.RUnlock()
	writeJSON(w, http.StatusOK, out)
}
func (s *ProductStore) get(w http.ResponseWriter, r *http.Request) {
	id, ok := pathID(w, r)
	if !ok {
		return
	}
	s.mu.RLock()
	p, ok := s.items[id]
	s.mu.RUnlock()
	if !ok {
		writeError(w, http.StatusNotFound, "not_found", "商品不存在")
		return
	}
	writeJSON(w, http.StatusOK, p)
}
func (s *ProductStore) create(w http.ResponseWriter, r *http.Request) {
	p, ok := readProduct(w, r)
	if !ok {
		return
	}
	s.mu.Lock()
	p.ID = s.nextID
	s.nextID++
	s.items[p.ID] = p
	s.mu.Unlock()
	w.Header().Set("Location", "/api/products/"+strconv.Itoa(p.ID))
	writeJSON(w, http.StatusCreated, p)
}
func (s *ProductStore) update(w http.ResponseWriter, r *http.Request) {
	id, ok := pathID(w, r)
	if !ok {
		return
	}
	p, ok := readProduct(w, r)
	if !ok {
		return
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, exists := s.items[id]; !exists {
		writeError(w, http.StatusNotFound, "not_found", "商品不存在")
		return
	}
	p.ID = id
	s.items[id] = p
	writeJSON(w, http.StatusOK, p)
}
func (s *ProductStore) delete(w http.ResponseWriter, r *http.Request) {
	id, ok := pathID(w, r)
	if !ok {
		return
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, exists := s.items[id]; !exists {
		writeError(w, http.StatusNotFound, "not_found", "商品不存在")
		return
	}
	delete(s.items, id)
	w.WriteHeader(http.StatusNoContent)
}

func (s *ProductStore) routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/products", s.list)
	mux.HandleFunc("POST /api/products", s.create)
	mux.HandleFunc("GET /api/products/{id}", s.get)
	mux.HandleFunc("PUT /api/products/{id}", s.update)
	mux.HandleFunc("DELETE /api/products/{id}", s.delete)
	return mux
}
func main() {
	srv := &http.Server{
		Addr:              ":8082",
		Handler:           store.routes(),
		ReadHeaderTimeout: 5 * time.Second,
		WriteTimeout:      10 * time.Second,
	}
	log.Println("REST API 已启动：http://localhost:8082/api/products")
	if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("服务异常退出: %v", err)
	}
}