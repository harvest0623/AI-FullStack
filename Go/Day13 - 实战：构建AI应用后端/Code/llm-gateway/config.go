// 文件用途：从环境变量加载网关配置，提供默认值并校验必填项
package main

import (
	"fmt"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"
)

// Config 网关运行配置，全部来自环境变量。
type Config struct {
	Port               int           // 监听端口
	UpstreamURL        string        // 上游 OpenAI 兼容接口地址
	APIKey             string        // 上游 API Key
	Model              string        // 请求未指定模型时的默认模型
	Timeout            time.Duration // 单次上游调用超时
	MaxBodyBytes       int64         // 请求体最大字节数
	RateLimitPerMinute int           // 每个固定窗口（1 分钟）允许的请求数
	LogLevel           string        // 日志级别：debug/info/warn/error
}

// LoadConfig 读取环境变量并构造配置，解析失败或校验不通过时返回 error。
func LoadConfig() (Config, error) {
	port, err := envInt("PORT", 8080)
	if err != nil {
		return Config{}, err
	}
	if port < 1 || port > 65535 {
		return Config{}, fmt.Errorf("PORT 必须在 1-65535 之间，当前为 %d", port)
	}

	timeout, err := envDuration("TIMEOUT", 30*time.Second)
	if err != nil {
		return Config{}, err
	}

	maxBodyBytes, err := envInt64("MAX_BODY_BYTES", 1<<20) // 1MB
	if err != nil {
		return Config{}, err
	}
	if maxBodyBytes <= 0 {
		return Config{}, fmt.Errorf("MAX_BODY_BYTES 必须大于 0，当前为 %d", maxBodyBytes)
	}

	rateLimit, err := envInt("RATE_LIMIT_PER_MINUTE", 60)
	if err != nil {
		return Config{}, err
	}
	if rateLimit < 0 {
		return Config{}, fmt.Errorf("RATE_LIMIT_PER_MINUTE 不能为负数，当前为 %d", rateLimit)
	}

	logLevel := strings.ToLower(envOrDefault("LOG_LEVEL", "info"))
	switch logLevel {
	case "debug", "info", "warn", "error":
	default:
		return Config{}, fmt.Errorf("LOG_LEVEL 只能是 debug/info/warn/error，当前为 %q", logLevel)
	}

	cfg := Config{
		Port:               port,
		UpstreamURL:        envOrDefault("UPSTREAM_URL", "https://api.openai.com/v1/chat/completions"),
		APIKey:             envOrDefault("API_KEY", ""),
		Model:              envOrDefault("MODEL", "gpt-4o-mini"),
		Timeout:            timeout,
		MaxBodyBytes:       maxBodyBytes,
		RateLimitPerMinute: rateLimit,
		LogLevel:           logLevel,
	}
	if err := cfg.Validate(); err != nil {
		return Config{}, err
	}
	return cfg, nil
}

// Validate 校验配置中的必填项与地址格式。
func (c Config) Validate() error {
	if c.UpstreamURL == "" {
		return fmt.Errorf("UPSTREAM_URL 不能为空")
	}
	u, err := url.Parse(c.UpstreamURL)
	if err != nil {
		return fmt.Errorf("UPSTREAM_URL 不合法: %w", err)
	}
	if (u.Scheme != "http" && u.Scheme != "https") || u.Host == "" {
		return fmt.Errorf("UPSTREAM_URL 必须是 http/https 地址，当前为 %q", c.UpstreamURL)
	}
	if c.Model == "" {
		return fmt.Errorf("MODEL 不能为空")
	}
	if c.APIKey == "" {
		return fmt.Errorf("API_KEY 不能为空")
	}
	return nil
}

// envOrDefault 读取字符串环境变量，空值或全空白时返回默认值。
func envOrDefault(key, def string) string {
	if v := strings.TrimSpace(os.Getenv(key)); v != "" {
		return v
	}
	return def
}

// envInt 读取整数环境变量，未设置时返回默认值。
func envInt(key string, def int) (int, error) {
	v := strings.TrimSpace(os.Getenv(key))
	if v == "" {
		return def, nil
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return 0, fmt.Errorf("%s 必须是整数: %w", key, err)
	}
	return n, nil
}

// envInt64 读取 int64 环境变量，未设置时返回默认值。
func envInt64(key string, def int64) (int64, error) {
	v := strings.TrimSpace(os.Getenv(key))
	if v == "" {
		return def, nil
	}
	n, err := strconv.ParseInt(v, 10, 64)
	if err != nil {
		return 0, fmt.Errorf("%s 必须是整数: %w", key, err)
	}
	return n, nil
}

// envDuration 读取时长环境变量（如 30s、1m），未设置时返回默认值。
func envDuration(key string, def time.Duration) (time.Duration, error) {
	v := strings.TrimSpace(os.Getenv(key))
	if v == "" {
		return def, nil
	}
	d, err := time.ParseDuration(v)
	if err != nil {
		return 0, fmt.Errorf("%s 必须是合法时长（如 30s）: %w", key, err)
	}
	if d <= 0 {
		return 0, fmt.Errorf("%s 必须大于 0", key)
	}
	return d, nil
}
