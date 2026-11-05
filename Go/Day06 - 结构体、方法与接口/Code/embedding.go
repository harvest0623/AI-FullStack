// 文件用途：演示匿名字段嵌入、方法提升、字段提升、嵌入接口以及与继承的差异
// 运行方式：go run embedding.go
package main

import "fmt"

// Audit 审计信息，作为通用能力被嵌入到其他结构体。
type Audit struct {
	CreatedBy string
	CreatedAt string
}

// Summary 返回审计摘要。
func (a Audit) Summary() string {
	return fmt.Sprintf("%s 于 %s 创建", a.CreatedBy, a.CreatedAt)
}

// Order 订单，嵌入 Audit 后自动获得 Summary 方法与审计字段。
type Order struct {
	ID     string
	Amount float64
	Audit  // 匿名字段（嵌入），字段名即类型名 Audit
}

// OrderDetail 在外层定义同名方法，覆盖被提升的 Summary。
type OrderDetail struct {
	Order
	Channel string
}

func (o OrderDetail) Summary() string {
	return fmt.Sprintf("订单 %s 来自 %s，原审计：%s", o.ID, o.Channel, o.Order.Summary())
}

// Notifier 通知能力，作为接口被嵌入。
type Notifier interface {
	Notify(msg string) string
}

// ConsoleNotifier 控制台通知实现。
type ConsoleNotifier struct{}

func (ConsoleNotifier) Notify(msg string) string { return "[console] " + msg }

// OrderService 嵌入接口，调用时转发到运行时注入的实现。
type OrderService struct {
	Notifier
	Prefix string
}

// NotifyAll 组合前缀与通知结果。
func (s OrderService) NotifyAll(msg string) string {
	return s.Prefix + s.Notify(msg)
}

func main() {
	fmt.Println("=== 匿名字段嵌入与方法提升 ===")
	o := Order{
		ID:     "ORD-20241022-001",
		Amount: 899,
		Audit:  Audit{CreatedBy: "system", CreatedAt: "2026-10-22 10:00"},
	}
	fmt.Println("方法提升：", o.Summary()) // 等价于 o.Audit.Summary()
	fmt.Println("字段提升：", o.CreatedBy)  // 等价于 o.Audit.CreatedBy

	// 字段名就是类型名，也可以显式访问内层
	fmt.Println("显式访问：", o.Audit.CreatedBy)
	o.CreatedBy = "operator" // 提升字段可直接赋值
	fmt.Println("修改后：", o.Summary())

	fmt.Println("\n=== 外层方法覆盖 ===")
	d := OrderDetail{
		Order:   Order{ID: "ORD-002", Amount: 1299, Audit: Audit{CreatedBy: "ai", CreatedAt: "2026-10-22 11:30"}},
		Channel: "小程序",
	}
	fmt.Println(d.Summary())
	fmt.Println("仍可调用被覆盖的方法：", d.Order.Summary())

	fmt.Println("\n=== 嵌入接口 ===")
	svc := OrderService{Notifier: ConsoleNotifier{}, Prefix: "eshop | "}
	fmt.Println(svc.NotifyAll("订单已支付"))
	if svc.Notifier == nil {
		fmt.Println("未注入 Notifier，调用会 panic")
	}

	fmt.Println("\n=== 与继承的差异 ===")
	// 嵌入是组合：Order 拥有一个 Audit，而不是 is-a Audit
	var a Audit = o.Audit
	fmt.Println("可以取出内层值：", a.Summary())
	// 注意：不能写 var a Audit = o，Order 并不是 Audit 的子类型。
}
