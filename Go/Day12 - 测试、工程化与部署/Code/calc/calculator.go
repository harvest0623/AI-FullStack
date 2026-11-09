// 文件用途：商品金额计算工具包，供单元测试、示例测试与基准测试演示使用
// 运行方式：go test ./calc

// Package calc 提供电商场景下的基础计算函数。
package calc

import "errors"

// ErrDivideByZero 表示除数为零。
var ErrDivideByZero = errors.New("除数不能为零")

// ErrEmptySlice 表示传入的数值切片为空。
var ErrEmptySlice = errors.New("切片不能为空")

// Add 返回两个数的和。
func Add(a, b float64) float64 {
	return a + b
}

// Subtract 返回 a 减 b 的差。
func Subtract(a, b float64) float64 {
	return a - b
}

// Divide 返回 a 除以 b 的商；除数为零时返回 ErrDivideByZero。
func Divide(a, b float64) (float64, error) {
	if b == 0 {
		return 0, ErrDivideByZero
	}
	return a / b, nil
}

// Average 返回切片的平均值；空切片返回 ErrEmptySlice。
func Average(nums []float64) (float64, error) {
	if len(nums) == 0 {
		return 0, ErrEmptySlice
	}
	var sum float64
	for _, n := range nums {
		sum += n
	}
	return sum / float64(len(nums)), nil
}
