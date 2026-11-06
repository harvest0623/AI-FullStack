// 文件用途：演示 defer 执行顺序、参数求值时机、defer 修改命名返回值与 panic/recover
// 运行方式：go run defer_panic.go
package main

import (
	"errors"
	"fmt"
)

// trace 打印注册与执行时机，用于观察 defer 的 LIFO 顺序。
func trace(name string) func() {
	fmt.Println("注册 defer：", name)
	return func() { fmt.Println("执行 defer：", name) }
}

// calcTotal 命名返回值 + defer 统一追加服务费。
func calcTotal(prices []float64) (total float64, err error) {
	defer func() {
		if err == nil { // 只有成功时才加服务费
			total *= 1.01
			fmt.Printf("defer 追加 1%% 服务费后：%.2f\n", total)
		}
	}()
	for _, p := range prices {
		if p < 0 {
			return 0, fmt.Errorf("价格不能为负：%.2f", p)
		}
		total += p
	}
	return total, nil
}

// safeDivide 用 recover 捕获除零 panic，转为普通错误返回。
func safeDivide(a, b float64) (result float64, err error) {
	defer func() {
		if r := recover(); r != nil {
			// recover 后不会回到 panic 点，而是从这里返回到调用方
			err = fmt.Errorf("recover 捕获 panic: %v", r)
		}
	}()
	if b == 0 {
		panic("除数为 0")
	}
	return a / b, nil
}

// mustSKU 演示"编程错误"才使用 panic 的场景。
func mustSKU(sku string) string {
	if sku == "" {
		panic(errors.New("SKU 不能为空"))
	}
	return sku
}

func main() {
	fmt.Println("=== defer 的 LIFO 顺序 ===")
	func() {
		defer trace("first")()
		defer trace("second")()
		defer trace("third")()
		fmt.Println("函数体执行中")
	}()

	fmt.Println("\n=== defer 参数立即求值 ===")
	stock := 10
	func() {
		defer func(n int) {
			fmt.Println("defer 看到的库存：", n)
		}(stock)
		stock = 3
		fmt.Println("函数体修改后的库存：", stock)
	}()

	fmt.Println("\n=== defer 修改命名返回值 ===")
	total, err := calcTotal([]float64{100, 200})
	fmt.Printf("返回：total=%.2f err=%v\n", total, err)
	_, err = calcTotal([]float64{100, -1})
	fmt.Println("失败路径：", err)

	fmt.Println("\n=== panic / recover ===")
	r, err := safeDivide(10, 0)
	fmt.Printf("10 / 0 结果：%.2f，错误：%v\n", r, err)
	fmt.Println("recover 之后，main 继续执行")

	r, err = safeDivide(10, 4)
	fmt.Printf("10 / 4 = %.2f，错误：%v\n", r, err)

	fmt.Println("\n=== 合法输入不应 panic ===")
	fmt.Println("合法 SKU：", mustSKU("SKU-1001"))
	fmt.Println("业务错误请返回 error，而不是 panic")
}
