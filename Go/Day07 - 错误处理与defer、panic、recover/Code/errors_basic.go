// 文件用途：演示 errors.New、fmt.Errorf、哨兵错误、早返回与 errors.Is 判断
// 运行方式：go run errors_basic.go
package main

import (
	"errors"
	"fmt"
)

// 哨兵错误：包级定义，供调用方用 errors.Is 精确判断。
var (
	ErrNotFound   = errors.New("商品不存在")
	ErrOutOfStock = errors.New("库存不足")
)

// Product 商品。
type Product struct {
	SKU   string
	Stock int
}

// Inventory 简易内存库存。
type Inventory struct {
	items map[string]*Product
}

// NewInventory 构造演示用库存。
func NewInventory() *Inventory {
	return &Inventory{items: map[string]*Product{
		"SKU-1001": {SKU: "SKU-1001", Stock: 5},
		"SKU-1002": {SKU: "SKU-1002", Stock: 0},
	}}
}

// Get 查询商品：早返回，错误路径优先。
func (inv *Inventory) Get(sku string) (*Product, error) {
	p, ok := inv.items[sku]
	if !ok {
		return nil, ErrNotFound
	}
	return p, nil
}

// Deduct 扣减库存，错误中带上足够的上下文。
func (inv *Inventory) Deduct(sku string, count int) error {
	if count <= 0 {
		return fmt.Errorf("扣减数量必须为正数，收到 %d", count)
	}
	p, err := inv.Get(sku)
	if err != nil {
		return err // 直接向上传递，保留原始哨兵错误
	}
	if p.Stock < count {
		return fmt.Errorf("%w：%s 剩余 %d，需要 %d", ErrOutOfStock, sku, p.Stock, count)
	}
	p.Stock -= count
	return nil
}

func main() {
	inv := NewInventory()

	// 1. 成功路径
	p, err := inv.Get("SKU-1001")
	if err != nil {
		fmt.Println("查询失败：", err)
	} else {
		fmt.Printf("查询成功：%s，库存 %d\n", p.SKU, p.Stock)
	}

	// 2. 哨兵错误用 errors.Is 判断，而不是字符串比较
	_, err = inv.Get("SKU-9999")
	fmt.Println("\n=== 哨兵错误 ===")
	fmt.Println("原始错误：", err)
	fmt.Println("errors.Is(err, ErrNotFound)：", errors.Is(err, ErrNotFound))
	fmt.Println("直接比较 err == ErrNotFound：", err == ErrNotFound)

	// 3. fmt.Errorf 包装后仍然可以用 Is 命中
	fmt.Println("\n=== 带上下文的包装错误 ===")
	err = inv.Deduct("SKU-1002", 1)
	fmt.Println("错误信息：", err)
	fmt.Println("是库存不足吗：", errors.Is(err, ErrOutOfStock))

	// 4. 参数错误：没有被哨兵覆盖，只能看文案
	err = inv.Deduct("SKU-1001", 0)
	fmt.Println("\n参数错误：", err)

	// 5. 错误是普通值：可以存入 Map、作为分支依据
	fmt.Println("\n=== 错误作为普通值 ===")
	results := map[string]error{
		"SKU-1001": inv.Deduct("SKU-1001", 2),
		"SKU-1002": inv.Deduct("SKU-1002", 1),
	}
	for sku, e := range results { // Map 遍历顺序随机，输出顺序不固定
		if e != nil {
			fmt.Printf("%s 失败：%v\n", sku, e)
			continue
		}
		fmt.Printf("%s 扣减成功\n", sku)
	}

	// 6. 扣减成功后再次查询，确认库存已被修改
	p, _ = inv.Get("SKU-1001")
	fmt.Printf("\nSKU-1001 剩余库存：%d\n", p.Stock)
}
