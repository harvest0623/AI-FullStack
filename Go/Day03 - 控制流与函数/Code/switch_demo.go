// 文件用途：演示普通 switch、无表达式 switch、fallthrough 与 type switch 预览
// 运行方式：go run switch_demo.go
package main

import "fmt"

// shippingFee 用无表达式 switch 做区间判断，返回运费。
func shippingFee(amount float64, vip bool) float64 {
	switch {
	case amount >= 99:
		return 0
	case vip:
		return 0
	case amount >= 50:
		return 5
	default:
		return 10
	}
}

// typeName 用 type switch 判断动态类型（Day06 会系统讲解接口）。
func typeName(v any) string {
	switch v.(type) {
	case nil:
		return "nil"
	case int:
		return "int"
	case float64:
		return "float64"
	case string:
		return "string"
	case bool:
		return "bool"
	case []string:
		return "[]string"
	default:
		return "未知类型"
	}
}

func main() {
	// 1. 普通 switch：自动 break，多值可合并
	status := "paid"
	fmt.Println("=== 普通 switch ===")
	switch status {
	case "pending":
		fmt.Println("订单待支付")
	case "paid":
		fmt.Println("订单已支付，准备发货")
	case "shipped", "done":
		fmt.Println("订单已发货或已完成")
	default:
		fmt.Println("未知状态")
	}

	// 2. 无表达式 switch：等价于 switch true
	fmt.Println("\n=== 无表达式 switch ===")
	for _, amount := range []float64{30, 60, 120} {
		fmt.Printf("订单金额 %.2f，运费 %.2f\n", amount, shippingFee(amount, false))
	}
	fmt.Printf("VIP 订单 30.00，运费 %.2f\n", shippingFee(30, true))

	// 3. fallthrough：强制执行下一个分支，不再判断条件
	fmt.Println("\n=== fallthrough ===")
	level := 2
	switch level {
	case 1:
		fmt.Println("等级 1：普通会员")
		fallthrough
	case 2:
		fmt.Println("等级 2：银牌会员")
		fallthrough
	case 3:
		fmt.Println("等级 3：金牌会员（附带权益）")
	default:
		fmt.Println("无等级")
	}

	// 4. switch 带初始化语句
	fmt.Println("\n=== 带初始化语句 ===")
	switch total := 5999 * 2; {
	case total >= 10000:
		fmt.Printf("大额订单：%d 元，赠送运费险\n", total)
	case total >= 5000:
		fmt.Printf("中等订单：%d 元\n", total)
	default:
		fmt.Printf("普通订单：%d 元\n", total)
	}

	// 5. type switch 预览
	fmt.Println("\n=== type switch ===")
	values := []any{42, 4.85, "SKU-1001", true, []string{"手机"}, nil}
	for _, v := range values {
		fmt.Printf("值 %-14v 类型 %s\n", v, typeName(v))
	}
}
