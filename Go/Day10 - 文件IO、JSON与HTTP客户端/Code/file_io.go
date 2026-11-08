// 文件用途：演示文件读写、bufio 逐行扫描、文件权限、临时目录与错误处理
// 运行方式：go run file_io.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

func main() {
	fmt.Println("=== 1. os.WriteFile：一次写入整个文件 ===")
	content := "p1001,iPhone 15,5999\np1002,MacBook Pro,12999\n"
	if err := os.WriteFile("products.csv", []byte(content), 0o644); err != nil {
		fmt.Println("写入失败：", err)
		return
	}
	fmt.Println("已写入 products.csv（权限 0644）")

	fmt.Println("\n=== 2. os.ReadFile：一次读回全部内容 ===")
	data, err := os.ReadFile("products.csv")
	if err != nil {
		fmt.Println("读取失败：", err)
		return
	}
	fmt.Printf("文件大小：%d 字节\n", len(data))
	fmt.Print(string(data))

	fmt.Println("\n=== 3. os.Open + bufio.Scanner：逐行处理大文件 ===")
	f, err := os.Open("products.csv")
	if err != nil {
		fmt.Println("打开失败：", err)
		return
	}
	defer f.Close() // 文件句柄必须关闭，defer 保证异常路径也执行

	scanner := bufio.NewScanner(f)
	lineNo := 0
	total := 0.0
	for scanner.Scan() {
		lineNo++
		fields := strings.Split(scanner.Text(), ",")
		if len(fields) != 3 {
			fmt.Printf("第 %d 行格式错误，跳过\n", lineNo)
			continue
		}
		var price float64
		if _, err := fmt.Sscanf(fields[2], "%f", &price); err != nil {
			fmt.Printf("第 %d 行价格解析失败：%v\n", lineNo, err)
			continue
		}
		total += price
		fmt.Printf("第 %d 行：%s / %s / %.2f\n", lineNo, fields[0], fields[1], price)
	}
	if err := scanner.Err(); err != nil {
		fmt.Println("扫描出错：", err)
	}
	fmt.Printf("共 %d 行，商品总价 %.2f\n", lineNo, total)

	fmt.Println("\n=== 4. os.MkdirTemp：创建临时目录 ===")
	dir, err := os.MkdirTemp("", "eshop-*")
	if err != nil {
		fmt.Println("创建临时目录失败：", err)
		return
	}
	defer os.RemoveAll(dir)

	tmpFile := filepath.Join(dir, "cache.txt")
	if err := os.WriteFile(tmpFile, []byte("cache warm\n"), 0o600); err != nil {
		fmt.Println("写临时文件失败：", err)
		return
	}
	info, err := os.Stat(tmpFile)
	if err != nil {
		fmt.Println("读取文件信息失败：", err)
		return
	}
	fmt.Printf("临时目录：%s\n", dir)
	fmt.Printf("文件：%s，权限：%v，大小：%d 字节\n", info.Name(), info.Mode(), info.Size())

	fmt.Println("\n=== 5. 错误处理：读取不存在的文件 ===")
	if _, err := os.ReadFile("not_exist.json"); err != nil {
		if os.IsNotExist(err) {
			fmt.Println("文件不存在，使用默认配置，错误详情：", err)
		} else {
			fmt.Println("其他错误：", err)
		}
	}
}
