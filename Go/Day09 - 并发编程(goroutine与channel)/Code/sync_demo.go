// 文件用途：演示 Mutex 保护计数器、RWMutex 缓存、sync.Once 单例与 atomic.Int64 计数
// 运行方式：go run -race sync_demo.go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// ProductCache 是读多写少的商品缓存，用 RWMutex 保护 map。
type ProductCache struct {
	mu    sync.RWMutex
	items map[string]string
}

// NewProductCache 创建空缓存。
func NewProductCache() *ProductCache {
	return &ProductCache{items: make(map[string]string)}
}

// Get 读取商品，读锁允许多个读者并发进入。
func (c *ProductCache) Get(key string) (string, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	v, ok := c.items[key]
	return v, ok
}

// Set 写入商品，写锁独占。
func (c *ProductCache) Set(key, value string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.items[key] = value
}

// Len 返回当前缓存条目数。
func (c *ProductCache) Len() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return len(c.items)
}

// Config 表示网关配置。
type Config struct {
	Endpoint string
}

var (
	configOnce sync.Once
	configInst *Config
)

// GetConfig 使用 sync.Once 保证配置只初始化一次，并发调用也安全。
func GetConfig() *Config {
	configOnce.Do(func() {
		time.Sleep(10 * time.Millisecond) // 模拟读取配置文件的耗时
		configInst = &Config{Endpoint: "https://llm.internal/v1"}
		fmt.Println("配置初始化：只执行一次")
	})
	return configInst
}

func main() {
	fmt.Println("=== 1. Mutex 保护共享计数器 ===")
	var mu sync.Mutex
	var plainCount int
	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			mu.Lock()
			plainCount++
			mu.Unlock()
		}()
	}
	wg.Wait()
	fmt.Println("Mutex 计数结果：", plainCount, "（必定为 100）")

	fmt.Println("\n=== 2. RWMutex 保护商品缓存 ===")
	cache := NewProductCache()
	cache.Set("p1001", "iPhone 15")
	var wgRW sync.WaitGroup
	for i := 1; i <= 5; i++ {
		wgRW.Add(1)
		go func(n int) {
			defer wgRW.Done()
			if v, ok := cache.Get("p1001"); ok {
				fmt.Printf("读者#%d 命中：%s\n", n, v)
			}
		}(i)
	}
	wgRW.Wait()
	cache.Set("p1002", "MacBook Pro")
	fmt.Println("缓存条目数：", cache.Len())

	fmt.Println("\n=== 3. sync.Once 单例初始化 ===")
	var wgOnce sync.WaitGroup
	for i := 1; i <= 3; i++ {
		wgOnce.Add(1)
		go func(n int) {
			defer wgOnce.Done()
			cfg := GetConfig()
			fmt.Printf("协程#%d 获取配置：%s\n", n, cfg.Endpoint)
		}(i)
	}
	wgOnce.Wait()

	fmt.Println("\n=== 4. atomic.Int64 无锁计数 ===")
	var hits atomic.Int64
	var wgAtomic sync.WaitGroup
	for i := 0; i < 200; i++ {
		wgAtomic.Add(1)
		go func() {
			defer wgAtomic.Done()
			hits.Add(1)
		}()
	}
	wgAtomic.Wait()
	fmt.Println("原子计数结果：", hits.Load())
}
