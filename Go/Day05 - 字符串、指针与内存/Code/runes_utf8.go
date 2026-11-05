// 文件用途：演示 UTF-8 字节表示、[]byte 与 []rune、中文遍历与 utf8 计数
// 运行方式：go run runes_utf8.go
package main

import (
	"fmt"
	"unicode/utf8"
)

func main() {
	text := "电商 eshop"

	fmt.Println("=== UTF-8 字节表示 ===")
	fmt.Printf("文本：%s\n", text)
	fmt.Printf("len(text) = %d 字节\n", len(text))
	fmt.Printf("utf8.RuneCountInString = %d 个字符\n", utf8.RuneCountInString(text))

	// 1. 逐字节查看 UTF-8 编码
	bytes := []byte(text)
	fmt.Printf("逐字节（十六进制）：")
	for _, b := range bytes {
		fmt.Printf("%02X ", b)
	}
	fmt.Println()

	// 2. []rune 按字符查看
	runes := []rune(text)
	fmt.Printf("逐字符（rune）：")
	for _, r := range runes {
		fmt.Printf("%c ", r)
	}
	fmt.Println()

	// 3. 按字节截断可能切坏中文
	fmt.Println("\n=== 按字节截断的坑 ===")
	fmt.Printf("前 3 字节：%q（合法 UTF-8？%t）\n",
		string(bytes[:3]), utf8.Valid(bytes[:3]))
	fmt.Printf("前 3 个字符：%q\n", string(runes[:3]))

	// 4. range 遍历字符串会按 rune 解码
	fmt.Println("\n=== range 遍历 ===")
	for i, r := range text {
		fmt.Printf("字节偏移 %2d → 字符 %q（码点 U+%04X，占 %d 字节）\n",
			i, r, r, utf8.RuneLen(r))
	}

	// 5. 按字符统计数字个数
	fmt.Println("\n=== rune 操作 ===")
	count := 0
	for _, r := range "iPhone 15 手机" {
		if r >= '0' && r <= '9' {
			count++
		}
	}
	fmt.Printf("文本中的数字字符个数：%d\n", count)

	// 6. 用 []rune 做 ASCII 字母转大写
	upper := make([]rune, 0, len(runes))
	for _, r := range runes {
		if r >= 'a' && r <= 'z' {
			r -= 32
		}
		upper = append(upper, r)
	}
	fmt.Printf("大写转换：%s\n", string(upper))
}
