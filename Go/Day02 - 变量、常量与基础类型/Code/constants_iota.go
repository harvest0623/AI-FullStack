// 文件用途：演示 const 块、iota 枚举、位标志、容量单位与枚举字符串映射
// 运行方式：go run constants_iota.go
package main

import "fmt"

// 1. 普通常量块
const (
	ServiceName = "eshop-gateway"
	MaxRetries  = 3
)

// 2. iota 从 0 开始，块内每行自增 1
const (
	StatusPending = iota // 0
	StatusPaid           // 1
	StatusShipped        // 2
	StatusDone           // 3
)

// 3. iota 跳值与表达式：_ 占位跳过 0
const (
	_  = iota
	KB = 1 << (10 * iota) // 1 << 10 = 1024
	MB                    // 1 << 20
	GB                    // 1 << 30
	TB                    // 1 << 40
)

// 4. 位标志：每个常量独占一个二进制位
const (
	PermRead   = 1 << iota // 001
	PermWrite              // 010
	PermDelete             // 100
)

// 5. 枚举码值到中文名称的映射
var statusNames = map[int]string{
	StatusPending: "待支付",
	StatusPaid:    "已支付",
	StatusShipped: "已发货",
	StatusDone:    "已完成",
}

// statusName 把状态码翻译为可读文本，未知状态返回兜底文案。
func statusName(code int) string {
	if name, ok := statusNames[code]; ok {
		return name
	}
	return "未知状态"
}

func main() {
	fmt.Println("=== 基础常量 ===")
	fmt.Printf("%s 最多重试 %d 次\n", ServiceName, MaxRetries)

	fmt.Println("\n=== iota 枚举 ===")
	for _, code := range []int{StatusPending, StatusPaid, StatusShipped, StatusDone} {
		fmt.Printf("状态码 %d → %s\n", code, statusName(code))
	}

	fmt.Println("\n=== 容量单位 ===")
	fmt.Printf("KB=%d MB=%d GB=%d TB=%d\n", int64(KB), int64(MB), int64(GB), int64(TB))
	fmt.Printf("5 GB = %d 字节\n", int64(5*GB))

	fmt.Println("\n=== 位标志 ===")
	perm := PermRead | PermWrite
	fmt.Printf("权限值=%d 二进制=%b\n", perm, perm)
	fmt.Printf("可读=%t 可写=%t 可删除=%t\n",
		perm&PermRead != 0, perm&PermWrite != 0, perm&PermDelete != 0)

	fmt.Println("\n=== 无类型常量 ===")
	const discount = 0.85 // 无具体类型，按上下文适配
	var price32 float32 = 5999 * discount
	var price64 float64 = 5999 * discount
	fmt.Printf("float32 折后价=%.2f，float64 折后价=%.2f\n", price32, price64)
}
