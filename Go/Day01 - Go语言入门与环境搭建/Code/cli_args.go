// 文件用途：演示 os.Args 与 flag 包解析命令行参数
// 运行方式：go run cli_args.go -name 张三 -count 3 -v
package main

import (
	"flag"
	"fmt"
	"os"
)

func main() {
	// 1. os.Args：原始参数切片，第 0 个是程序路径
	fmt.Println("原始参数 os.Args:", os.Args)
	if len(os.Args) > 1 {
		fmt.Println("第一个业务参数:", os.Args[1])
	}

	// 2. flag：声明命名参数（返回指针）
	name := flag.String("name", "guest", "用户名称")
	count := flag.Int("count", 1, "商品数量")
	verbose := flag.Bool("v", false, "是否输出详细信息")

	// 3. 解析参数，必须显式调用
	flag.Parse()

	fmt.Printf("\n解析结果：name=%s, count=%d, verbose=%t\n", *name, *count, *verbose)

	// 4. flag.Args()：解析后剩余的非 flag 参数
	if *verbose {
		fmt.Println("剩余位置参数:", flag.Args())
	}

	// 5. 业务逻辑：参数校验 + 循环输出
	if *count <= 0 {
		fmt.Fprintln(os.Stderr, "错误：count 必须大于 0")
		os.Exit(1)
	}
	for i := 1; i <= *count; i++ {
		fmt.Printf("第 %d 件商品：iPhone 15 Pro\n", i)
	}
}
