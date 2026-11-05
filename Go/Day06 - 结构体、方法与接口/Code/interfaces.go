// 文件用途：演示接口隐式实现、多态、空接口、类型断言、type switch、Stringer 与 nil 接口陷阱
// 运行方式：go run interfaces.go
package main

import "fmt"

// Payer 支付渠道接口：定义行为，不关心具体实现。
type Payer interface {
	Name() string
	Pay(amount float64) (string, error)
}

// Alipay 支付宝，用值接收者实现接口。
type Alipay struct {
	Account string
}

func (a Alipay) Name() string { return "支付宝" }

func (a Alipay) Pay(amount float64) (string, error) {
	if amount <= 0 {
		return "", fmt.Errorf("%s 支付金额非法：%.2f", a.Name(), amount)
	}
	return fmt.Sprintf("%s（%s）支付 %.2f 元成功", a.Name(), a.Account, amount), nil
}

// Wechat 微信支付，用指针接收者实现接口。
type Wechat struct {
	OpenID string
}

func (w *Wechat) Name() string { return "微信支付" }

func (w *Wechat) Pay(amount float64) (string, error) {
	if w.OpenID == "" {
		return "", fmt.Errorf("%s 缺少 openid", w.Name())
	}
	return fmt.Sprintf("%s（%s）支付 %.2f 元成功", w.Name(), w.OpenID, amount), nil
}

// Checkout 多态：只面向 Payer 编程。
func Checkout(p Payer, amount float64) {
	msg, err := p.Pay(amount)
	if err != nil {
		fmt.Println("下单失败：", err)
		return
	}
	fmt.Println(msg)
}

// SKU 商品编号，实现 fmt.Stringer。
type SKU string

func (s SKU) String() string { return "SKU-" + string(s) }

// describe 用 type switch 识别动态类型。
func describe(v any) string {
	switch x := v.(type) {
	case nil:
		return "nil"
	case int:
		return fmt.Sprintf("整数 %d", x)
	case float64:
		return fmt.Sprintf("浮点数 %.2f", x)
	case string:
		return fmt.Sprintf("字符串 %q", x)
	case SKU:
		return fmt.Sprintf("商品编号 %s", x)
	case Payer:
		return fmt.Sprintf("支付渠道 %s", x.Name())
	default:
		return fmt.Sprintf("未知类型 %T", x)
	}
}

func main() {
	fmt.Println("=== 隐式实现与多态 ===")
	payers := []Payer{
		Alipay{Account: "user@eshop.com"},
		&Wechat{OpenID: "openid-42"},
	}
	for _, p := range payers {
		Checkout(p, 199.00)
	}
	Checkout(Alipay{Account: "user@eshop.com"}, 0)

	fmt.Println("\n=== any + comma-ok 类型断言 ===")
	values := []any{42, 3.14, "eshop", SKU("1001"), Alipay{Account: "vip@eshop.com"}, nil, true}
	for _, v := range values {
		if s, ok := v.(string); ok {
			fmt.Printf("断言成功：%q，长度 %d\n", s, len(s))
			continue
		}
		fmt.Println("断言失败，改用 type switch：", describe(v))
	}

	fmt.Println("\n=== Stringer ===")
	fmt.Printf("%v / %s\n", SKU("1001"), SKU("1001"))

	fmt.Println("\n=== nil 接口陷阱 ===")
	var wx *Wechat // nil 指针
	var p Payer = wx
	fmt.Println("p == nil：", p == nil) // false：接口里还装着类型信息
	if w, ok := p.(*Wechat); ok {
		fmt.Println("断言成功，但底层指针为 nil：", w == nil)
	}
	// 此时直接调用 p.Pay(1) 会在 w.OpenID 处 panic，必须先判空。
	if w, ok := p.(*Wechat); ok && w != nil {
		Checkout(w, 1)
	} else {
		fmt.Println("渠道未初始化，拒绝调用 Pay")
	}

	// 真正的 nil 接口：类型和值都为空
	var empty Payer
	fmt.Println("未赋值的接口 == nil：", empty == nil)
}
