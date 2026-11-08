// 文件用途：演示 JSON 序列化/反序列化、结构体标签、omitempty 与 json.Decoder 流式解析
// 运行方式：go run json_demo.go
package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

// Product 表示一个电商商品，标签决定 JSON 字段名。
type Product struct {
	ID       string   `json:"id"`
	Name     string   `json:"name"`
	Price    float64  `json:"price"`
	Stock    int      `json:"stock"`
	Tags     []string `json:"tags,omitempty"`
	Discount float64  `json:"discount,omitempty"`
}

// ProductList 表示带总数的商品列表响应。
type ProductList struct {
	Total int       `json:"total"`
	Items []Product `json:"items"`
}

func main() {
	p := Product{
		ID:    "p1001",
		Name:  "iPhone 15",
		Price: 5999,
		Stock: 120,
		Tags:  []string{"新品", "手机"},
	}

	fmt.Println("=== 1. MarshalIndent：结构体 -> JSON ===")
	pretty, err := json.MarshalIndent(p, "", "  ")
	if err != nil {
		fmt.Println("序列化失败：", err)
		return
	}
	fmt.Println(string(pretty))

	fmt.Println("\n=== 2. omitempty：零值字段被省略 ===")
	empty := Product{ID: "p1002", Name: "MacBook Pro", Price: 12999, Stock: 0}
	// Tags 为 nil、Discount 为 0，因 omitempty 被省略；
	// Stock 的标签没有 omitempty，所以 0 仍会输出。
	b, err := json.Marshal(empty)
	if err != nil {
		fmt.Println("序列化失败：", err)
		return
	}
	fmt.Println(string(b))

	fmt.Println("\n=== 3. Unmarshal：JSON -> 结构体 ===")
	raw := `{"id":"p1003","name":"AirPods Pro","price":1899,"stock":50,"tags":["耳机"],"unknown":"忽略我"}`
	var parsed Product
	if err := json.Unmarshal([]byte(raw), &parsed); err != nil {
		fmt.Println("反序列化失败：", err)
		return
	}
	fmt.Printf("解析结果：%+v\n", parsed)
	// 未知字段默认被忽略；如需严格校验可用 Decoder.DisallowUnknownFields()。

	fmt.Println("\n=== 4. 嵌套结构与类型错误 ===")
	listRaw := `{"total":1,"items":[{"id":"p1001","name":"iPhone 15","price":5999,"stock":120}]}`
	var list ProductList
	if err := json.Unmarshal([]byte(listRaw), &list); err != nil {
		fmt.Println("反序列化失败：", err)
		return
	}
	fmt.Printf("商品列表：total=%d, items=%d\n", list.Total, len(list.Items))

	var bad Product
	if err := json.Unmarshal([]byte(`{"price":"not-a-number"}`), &bad); err != nil {
		fmt.Println("类型不匹配错误：", err)
	}

	fmt.Println("\n=== 5. json.Decoder：流式解析多个对象 ===")
	stream := `{"id":"p2001","name":"机械键盘","price":499,"stock":30}
{"id":"p2002","name":"显示器","price":1599,"stock":18}
{"id":"p2003","name":"鼠标","price":199,"stock":88}`
	dec := json.NewDecoder(strings.NewReader(stream))
	count := 0
	for dec.More() {
		var item Product
		if err := dec.Decode(&item); err != nil {
			fmt.Println("流式解码失败：", err)
			break
		}
		count++
		fmt.Printf("第 %d 条：%s 价格 %.2f\n", count, item.Name, item.Price)
	}
	fmt.Println("流式解析完成，共", count, "条")

	fmt.Println("\n=== 6. json.Encoder：编码到 Writer ===")
	var buf strings.Builder // strings.Builder 实现了 io.Writer
	enc := json.NewEncoder(&buf)
	enc.SetIndent("", "  ")
	if err := enc.Encode(list); err != nil {
		fmt.Println("编码失败：", err)
		return
	}
	fmt.Printf("Encoder 输出长度：%d 字节\n", buf.Len())
}
