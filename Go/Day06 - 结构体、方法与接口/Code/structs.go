// 文件用途：演示结构体定义、两种初始化方式、零值、比较、嵌套结构体与 struct tag
// 运行方式：go run structs.go
package main

import (
	"encoding/json"
	"fmt"
)

// Product 表示电商商品。
type Product struct {
	ID    int      `json:"id"`
	Name  string   `json:"name"`
	Price float64  `json:"price"`
	Stock int      `json:"stock"`
	Tags  []string `json:"tags,omitempty"`
}

// Dimensions 表示包裹三边尺寸（单位：厘米）。
type Dimensions struct {
	Length float64 `json:"length_cm"`
	Width  float64 `json:"width_cm"`
	Height float64 `json:"height_cm"`
}

// Shipment 表示一个待发货包裹，嵌套 Dimensions。
type Shipment struct {
	SKU        string     `json:"sku"`
	WeightKG   float64    `json:"weight_kg"`
	Dimensions Dimensions `json:"dimensions"`
}

// StockRecord 只包含可比较字段，可用于 == 比较。
type StockRecord struct {
	SKU   string
	Count int
}

func main() {
	// 1. 按字段名初始化（推荐：顺序无关、可只写部分字段）
	p1 := Product{
		ID:    1001,
		Name:  "机械键盘",
		Price: 399.00,
		Stock: 25,
	}

	// 2. 按位置初始化（必须写全所有字段，顺序与定义一致）
	p2 := Product{1002, "无线鼠标", 129.00, 80, nil}

	// 3. 只初始化部分字段，其余取零值
	p3 := Product{ID: 1003, Name: "USB-C 扩展坞"}

	fmt.Println("=== 两种初始化方式 ===")
	fmt.Printf("p1 = %+v\n", p1)
	fmt.Printf("p2 = %+v\n", p2)
	fmt.Printf("p3 = %+v，Tags 为 nil：%v\n", p3, p3.Tags == nil)

	// 4. 零值：声明后不初始化，所有字段均为零值
	var p4 Product
	fmt.Printf("\n零值 p4 = %+v\n", p4)

	// 5. 结构体比较：字段全部可比较时可用 ==
	a := StockRecord{SKU: "SKU-1001", Count: 25}
	b := StockRecord{SKU: "SKU-1001", Count: 25}
	c := StockRecord{SKU: "SKU-1001", Count: 30}
	fmt.Println("\n=== 结构体比较 ===")
	fmt.Println("a == b:", a == b, "| a == c:", a == c)
	// 注意：Product 含 Tags 切片字段，p1 == p2 会编译失败。

	// 6. 嵌套结构体：值语义，点号逐层访问
	s := Shipment{
		SKU:      "SKU-1001",
		WeightKG: 1.2,
		Dimensions: Dimensions{
			Length: 40,
			Width:  20,
			Height: 8,
		},
	}
	s.Dimensions.Height = 10 // 直接修改嵌套字段
	fmt.Println("\n=== 嵌套结构体 ===")
	fmt.Printf("包裹 %s 体积 %.1f cm³，重量 %.1f kg\n",
		s.SKU,
		s.Dimensions.Length*s.Dimensions.Width*s.Dimensions.Height,
		s.WeightKG,
	)

	// 7. struct tag 决定 JSON 字段名，omitempty 在零值时省略
	p1.Tags = []string{"热销", "包邮"}
	raw, err := json.MarshalIndent(p1, "", "  ")
	if err != nil {
		fmt.Println("序列化失败：", err)
		return
	}
	fmt.Println("\n=== struct tag 与 JSON ===")
	fmt.Println(string(raw))
}
