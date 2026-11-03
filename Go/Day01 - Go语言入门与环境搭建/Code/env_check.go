// 文件用途：检查 Go 运行时、操作系统、CPU 与常用环境变量
// 运行方式：go run env_check.go
package main

import (
	"fmt"
	"os"
	"runtime"
)

func main() {
	fmt.Println("=== Go 运行时信息 ===")
	fmt.Println("Go 版本       :", runtime.Version())
	fmt.Println("操作系统      :", runtime.GOOS)
	fmt.Println("处理器架构    :", runtime.GOARCH)
	fmt.Println("GOROOT        :", runtime.GOROOT())
	fmt.Println("CPU 逻辑核心数:", runtime.NumCPU())
	fmt.Println("GOMAXPROCS    :", runtime.GOMAXPROCS(0))

	fmt.Println("\n=== 进程与环境 ===")
	fmt.Println("程序路径      :", os.Args[0])
	fmt.Println("命令行参数    :", os.Args[1:])
	fmt.Println("GOPATH        :", os.Getenv("GOPATH"))
	fmt.Println("GOPROXY       :", os.Getenv("GOPROXY"))
	if home, err := os.UserHomeDir(); err == nil {
		fmt.Println("用户主目录    :", home)
	}
}
