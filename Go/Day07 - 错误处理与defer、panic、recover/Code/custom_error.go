// 文件用途：演示自定义 error 结构体、ValidationError、错误码映射与批量错误聚合
// 运行方式：go run custom_error.go
package main

import (
	"errors"
	"fmt"
	"strings"
)

// ErrorCode 业务错误码。
type ErrorCode int

const (
	CodeInvalidArgument ErrorCode = 40001
	CodeNotFound        ErrorCode = 40401
	CodeInternal        ErrorCode = 50001
)

// AppError 带错误码的应用错误，可包装底层错误。
type AppError struct {
	Code    ErrorCode
	Message string
	Err     error
}

func (e *AppError) Error() string {
	if e.Err != nil {
		return fmt.Sprintf("[%d] %s: %v", e.Code, e.Message, e.Err)
	}
	return fmt.Sprintf("[%d] %s", e.Code, e.Message)
}

// Unwrap 让 errors.Is / errors.As 能继续向下查找。
func (e *AppError) Unwrap() error { return e.Err }

// ValidationError 字段级校验错误。
type ValidationError struct {
	Field   string
	Value   any
	Message string
}

func (e ValidationError) Error() string {
	return fmt.Sprintf("字段 %s 校验失败（值 %v）：%s", e.Field, e.Value, e.Message)
}

// CheckProduct 校验商品，用 AppError 包装 ValidationError。
func CheckProduct(name string, price float64) error {
	if strings.TrimSpace(name) == "" {
		return &AppError{
			Code:    CodeInvalidArgument,
			Message: "商品参数非法",
			Err:     ValidationError{Field: "name", Value: name, Message: "名称不能为空"},
		}
	}
	if price <= 0 {
		return &AppError{
			Code:    CodeInvalidArgument,
			Message: "商品参数非法",
			Err:     ValidationError{Field: "price", Value: price, Message: "价格必须大于 0"},
		}
	}
	return nil
}

// MultiError 手写批量错误聚合，可自定义输出格式。
type MultiError struct {
	Errors []error
}

func (m *MultiError) Error() string {
	parts := make([]string, 0, len(m.Errors))
	for _, e := range m.Errors {
		parts = append(parts, e.Error())
	}
	return fmt.Sprintf("%d 个错误：%s", len(m.Errors), strings.Join(parts, "；"))
}

// Unwrap 返回全部分支，供 errors.Is / errors.As 遍历。
func (m *MultiError) Unwrap() []error { return m.Errors }

// HTTPStatus 把业务错误码映射为 HTTP 状态码。
func HTTPStatus(err error) int {
	var appErr *AppError
	if errors.As(err, &appErr) {
		switch appErr.Code {
		case CodeInvalidArgument:
			return 400
		case CodeNotFound:
			return 404
		default:
			return 500
		}
	}
	return 500
}

func main() {
	fmt.Println("=== 自定义错误 + errors.As ===")
	err := CheckProduct("", 199)
	fmt.Println("错误：", err)

	var appErr *AppError
	if errors.As(err, &appErr) {
		fmt.Printf("错误码：%d，消息：%s，HTTP 状态：%d\n",
			appErr.Code, appErr.Message, HTTPStatus(err))
	}

	var valErr ValidationError
	if errors.As(err, &valErr) {
		fmt.Printf("字段：%s，值：%v，原因：%s\n", valErr.Field, valErr.Value, valErr.Message)
	}

	fmt.Println("\n=== 批量校验与聚合 ===")
	items := []struct {
		name  string
		price float64
	}{
		{"机械键盘", 399},
		{"", 129},
		{"显示器", -1},
	}
	var all []error
	for _, it := range items {
		if e := CheckProduct(it.name, it.price); e != nil {
			all = append(all, e)
		}
	}
	multi := &MultiError{Errors: all}
	fmt.Println(multi)

	var target *AppError
	if errors.As(multi, &target) {
		fmt.Println("聚合中首个 AppError 错误码：", target.Code)
	}
	fmt.Println("映射后的 HTTP 状态：", HTTPStatus(multi))
}
