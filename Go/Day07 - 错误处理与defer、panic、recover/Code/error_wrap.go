// 文件用途：演示 %w 包装、errors.Is、errors.As、errors.Join 与错误链打印
// 运行方式：go run error_wrap.go
package main

import (
	"errors"
	"fmt"
	"strconv"
)

// 哨兵错误：分别表示格式问题与范围问题。
var (
	ErrInvalidPrice = errors.New("价格格式非法")
	ErrPriceRange   = errors.New("价格超出范围")
)

// ParsePrice 解析价格字符串，用 %w 保留底层错误。
func ParsePrice(raw string) (float64, error) {
	v, err := strconv.ParseFloat(raw, 64)
	if err != nil {
		return 0, fmt.Errorf("解析价格 %q 失败: %w", raw, err)
	}
	if v < 0 || v > 1_000_000 {
		return 0, fmt.Errorf("%w: %v", ErrPriceRange, v)
	}
	return v, nil
}

// LoadPrice 服务层：继续包装，形成两层错误链。
func LoadPrice(sku, raw string) (float64, error) {
	price, err := ParsePrice(raw)
	if err != nil {
		return 0, fmt.Errorf("加载商品 %s 价格失败: %w", sku, err)
	}
	return price, nil
}

// validate 使用 errors.Join 聚合多个校验错误。
func validate(name string, price float64, stock int) error {
	var errs []error
	if name == "" {
		errs = append(errs, errors.New("商品名称不能为空"))
	}
	if price <= 0 {
		errs = append(errs, fmt.Errorf("%w: %.2f", ErrInvalidPrice, price))
	}
	if stock < 0 {
		errs = append(errs, errors.New("库存不能为负数"))
	}
	return errors.Join(errs...) // 没有错误时返回 nil
}

// printChain 逐层打印错误链，直到 Unwrap 返回 nil。
func printChain(err error) {
	for level := 0; err != nil; level++ {
		fmt.Printf("  [%d] %v\n", level, err)
		err = errors.Unwrap(err)
	}
}

func main() {
	fmt.Println("=== 错误链 ===")
	_, err := LoadPrice("SKU-1001", "abc")
	fmt.Println("顶层错误：", err)
	printChain(err)

	// errors.As 提取底层具体类型 *strconv.NumError
	var numErr *strconv.NumError
	if errors.As(err, &numErr) {
		fmt.Printf("提取到 *strconv.NumError：Func=%s Num=%q\n", numErr.Func, numErr.Num)
	}

	fmt.Println("\n=== errors.Is ===")
	_, err = LoadPrice("SKU-1002", "-5")
	fmt.Println("错误：", err)
	fmt.Println("是价格越界吗：", errors.Is(err, ErrPriceRange))
	fmt.Println("是格式非法吗：", errors.Is(err, ErrInvalidPrice))

	fmt.Println("\n=== errors.Join 聚合 ===")
	err = validate("", 0, -3)
	fmt.Println("聚合错误：")
	fmt.Println(err)
	fmt.Println("包含 ErrInvalidPrice：", errors.Is(err, ErrInvalidPrice))
	printChain(err)

	fmt.Println("\n=== 全部合法时返回 nil ===")
	fmt.Println("validate 结果：", validate("机械键盘", 399, 20))
}
