// 文件用途：演示整数家族与溢出、显式类型转换、浮点精度、strconv 与 byte/rune
// 运行方式：go run types_conversion.go
package main

import (
	"fmt"
	"math"
	"strconv"
)

func main() {
	// 1. 整数家族与定长类型
	var i8 int8 = 127
	var i16 int16 = 32767
	var i32 int32 = 5999
	var i64 int64 = 8999999999
	var u8 uint8 = 255
	fmt.Println("=== 整数类型 ===")
	fmt.Printf("int8=%d int16=%d int32=%d int64=%d uint8=%d\n", i8, i16, i32, i64, u8)
	fmt.Printf("int 在本机占 %d 字节（宽度与平台相关）\n", strconv.IntSize/8)

	// 2. 运行时溢出：静默回绕，不会 panic
	fmt.Println("\n=== 溢出回绕 ===")
	i8++ // 127 + 1 回绕为 -128
	fmt.Printf("int8 127++ → %d\n", i8)
	u8 = 0
	u8-- // 0 - 1 回绕为 255
	fmt.Printf("uint8 0--  → %d\n", u8)

	// 3. 显式类型转换：Go 不允许隐式转换
	fmt.Println("\n=== 显式转换 ===")
	var priceCents int64 = int64(i32) * 100
	var priceYuan float64 = float64(priceCents) / 100
	fmt.Printf("int32 %d 元 → int64 %d 分 → float64 %.2f 元\n", i32, priceCents, priceYuan)
	// var bad int64 = i32 // 取消注释会编译失败：cannot use i32

	// 4. 窄化转换：截断高位
	var big int32 = 70000
	fmt.Printf("int32 70000 → int16 %d\n", int16(big))

	// 5. 浮点精度：不要用 == 比较
	fmt.Println("\n=== 浮点精度 ===")
	var f32a float32 = 0.1
	var f32b float32 = 0.2
	fmt.Printf("float32: 0.1+0.2 = %.10f\n", f32a+f32b)
	var f64a float64 = 0.1
	var f64b float64 = 0.2
	fmt.Printf("float64: 0.1+0.2 = %.17f\n", f64a+f64b)
	fmt.Printf("直接用 == 比较：%t\n", f64a+f64b == 0.3)
	fmt.Printf("用误差比较：%t\n", math.Abs((f64a+f64b)-0.3) < 1e-9)

	// 6. strconv：字符串与数值互转，必须处理 error
	fmt.Println("\n=== strconv ===")
	n, err := strconv.Atoi("2024")
	if err != nil {
		fmt.Println("Atoi 失败：", err)
		return
	}
	fmt.Printf("Atoi(\"2024\") = %d（%T）\n", n, n)
	fmt.Printf("Itoa(%d) = %q\n", n+1, strconv.Itoa(n+1))

	rate, err := strconv.ParseFloat("4.85", 64)
	if err != nil {
		fmt.Println("ParseFloat 失败：", err)
		return
	}
	fmt.Printf("ParseFloat(\"4.85\") = %.2f\n", rate)

	paid, err := strconv.ParseBool("true")
	if err != nil {
		fmt.Println("ParseBool 失败：", err)
		return
	}
	fmt.Printf("ParseBool(\"true\") = %t\n", paid)

	hexValue, err := strconv.ParseInt("ff", 16, 64)
	if err != nil {
		fmt.Println("ParseInt 失败：", err)
		return
	}
	fmt.Printf("ParseInt(\"ff\", 16, 64) = %d\n", hexValue)
	fmt.Printf("FormatFloat 科学计数 = %s\n",
		strconv.FormatFloat(12345678.9, 'e', 4, 64))

	// 7. byte 与 rune：字节与 Unicode 码点
	fmt.Println("\n=== byte 与 rune ===")
	var ascii byte = 'G'
	var chinese rune = '中'
	fmt.Printf("byte 'G' = %c，数值 %d，类型 %T\n", ascii, ascii, ascii)
	fmt.Printf("rune '中' = %c，码点 %U，数值 %d，类型 %T\n",
		chinese, chinese, chinese, chinese)
	fmt.Printf("中文按 UTF-8 占 %d 字节，按 rune 计 %d 个码点\n",
		len(string(chinese)), len([]rune(string(chinese))))
	fmt.Printf("rune 转 byte（仅 ASCII 安全）：%c\n", byte(ascii))
}
