// 文件用途：第一个 Go 程序，演示包声明、导入、常量、函数与 main 入口
// 运行方式：go run hello.go
package main

import "fmt"

const (
	ServiceName = "eshop-gateway"
	Version     = "0.1.0"
)

// greet 返回带服务名与版本的欢迎语。
func greet(name string) string {
	return fmt.Sprintf("Hello, %s! 欢迎使用 %s v%s", name, ServiceName, Version)
}

func main() {
	// 1. 最基础的输出
	fmt.Println("Hello, Go!")

	// 2. 调用自定义函数
	fmt.Println(greet("AI 全栈学习者"))

	// 3. 短变量声明 + Printf 格式化
	shopName := "eshop 电商平台"
	productCount := 128
	fmt.Printf("店铺：%s，在售商品：%d 件\n", shopName, productCount)

	// 4. 多变量赋值
	name, price, stock := "iPhone 15", 5999.00, 120
	fmt.Printf("商品：%s，价格：%.2f 元，库存：%d 件\n", name, price, stock)

	// 5. 查看变量类型（%T）
	fmt.Printf("name 的类型是 %T，price 的类型是 %T\n", name, price)
}
