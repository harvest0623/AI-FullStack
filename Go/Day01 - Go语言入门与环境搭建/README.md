# Day01 - Go 语言入门与环境搭建

## 本章简介

Go（又称 Golang）由 Google 于 2009 年正式开源，设计初衷是解决大规模软件工程中的编译速度、依赖管理、并发编程与代码可维护性问题。它语法极简、静态编译、原生支持并发，并自带完整工具链与格式化规范。今天的云原生基础设施——Docker、Kubernetes、etcd、Prometheus、Terraform——几乎都由 Go 编写。

本章作为 Go 学习路线的起点，将从"Go 是什么、为什么需要 Go"讲起，理清静态编译语言的执行模型，完成 Go 1.22+ 的环境搭建，并跑通第一个程序。同时会讲清 Go Modules、`go run` 与 `go build` 的差异、包与入口约定，以及 `gofmt` 这一"强制统一风格"的工程文化。掌握本章后，你将拥有一套可编译、可调试、可格式化的 Go 开发环境。

## 学习目标

- 了解 Go 的诞生背景、设计哲学与典型应用领域
- 理解 Go 静态编译、单一可执行文件、跨平台交叉编译的特点
- 理解"源码 → 编译 → 静态二进制"的执行模型，以及与解释型语言的差异
- 掌握 Go 工具链：`go run` / `go build` / `go install` / `go fmt` / `go vet` / `go test`
- 理解 GOPATH 的历史与 Go Modules 的现代依赖管理方式
- 掌握 `go.mod`、`go.sum`、模块路径与语义化版本的基本概念
- 理解 `package main`、`func main()`、`import` 与包的可见性规则
- 完成 Go 1.22+ 安装、环境变量配置与国内代理设置
- 编写并运行第一个 Go 程序，使用 `fmt` 输出与环境信息检查
- 掌握 `os.Args` 与 `flag` 两种命令行参数解析方式
- 遵循 `gofmt` 风格，配置 VS Code + gopls 开发环境

## 理论知识讲解

### 1. Go 是什么

Go 是一门**静态强类型、编译型、自带垃圾回收、原生支持并发**的通用编程语言。它的三个创始人是 Robert Griesemer、Rob Pike 与 Ken Thompson（Unix 与 UTF-8 的核心作者之一），2007 年开始设计，2009 年 11 月开源，2012 年发布 1.0。

Go 的官方定位不是"更好的 C++"或"更快的 Python"，而是**面向工程的大规模软件开发语言**。它刻意舍弃了大量语言特性（继承、泛型曾长期缺席、异常机制、运算符重载），以换取：

- 学习成本低：核心语法一两天可掌握
- 编译速度快：大型项目也能秒级构建
- 代码风格统一：`gofmt` 让所有代码长得一样
- 部署简单：编译产物是单个静态二进制，无需运行时依赖

### 2. 设计哲学与核心特点

| 特点 | 说明 | 工程价值 |
|------|------|---------|
| 极简语法 | 关键字仅 25 个，没有隐式类型转换 | 阅读成本低，团队协作一致 |
| 静态编译 | 编译为机器码，直接运行 | 启动快、无虚拟机、部署简单 |
| 垃圾回收 | 并发三色标记 GC，无需手动 free | 降低内存管理负担 |
| 原生并发 | goroutine + channel，语言级支持 | 高并发服务开发效率极高 |
| 接口隐式实现 | 类型无需声明"实现了某接口" | 解耦、易测试、易扩展 |
| 显式错误处理 | 错误作为返回值，而非异常 | 错误路径清晰、可控 |
| 单一二进制 | 静态链接，含运行时 | 容器镜像可做到极小 |
| 跨平台交叉编译 | 一条命令生成其他平台产物 | CI/CD 友好 |

> **Go 的取舍**：没有异常、没有继承、没有三元运算符、没有隐式转换。这些"缺失"不是能力不足，而是为了避免大型项目中的隐式行为与理解成本。

### 3. 编译执行模型

Go 是编译型语言，执行过程为：

```
源码 .go
   │  go build / go run
   ▼
编译（类型检查 → 中间表示 → 机器码）
   │
   ▼
静态链接（运行时 + 标准库 + 业务代码）
   │
   ▼
单一可执行文件 → 操作系统直接加载运行
```

与 Python、Node.js 的对比：

| 维度 | Go | Python | Node.js |
|------|----|--------|---------|
| 执行方式 | 编译为机器码 | 解释字节码 | V8 JIT |
| 运行依赖 | 无（静态二进制） | Python 解释器 | Node 运行时 |
| 启动速度 | 毫秒级 | 较慢 | 中等 |
| 类型检查 | 编译期 | 运行期（可选 mypy） | 编译期（TS） |
| 并发模型 | goroutine（M:N 调度） | 线程/asyncio | 事件循环 |
| 部署体积 | 几 MB ~ 几十 MB | 需基础镜像 | 需 Node 镜像 |

`go run` 本质上也是"先编译到临时目录再执行"，因此它既能快速验证，又保留了完整的编译期检查。

### 4. Go 工具链

Go 把常用工程能力全部内置，不需要额外安装构建工具：

| 命令 | 作用 | 典型用法 |
|------|------|---------|
| `go run` | 编译并运行 | `go run hello.go` |
| `go build` | 编译为可执行文件 | `go build -o app .` |
| `go install` | 编译并安装到 `$GOPATH/bin` | `go install example.com/tool@latest` |
| `go fmt` / `gofmt` | 格式化代码 | `gofmt -w .` |
| `go vet` | 静态检查可疑代码 | `go vet ./...` |
| `go test` | 运行测试 | `go test ./...` |
| `go mod` | 模块与依赖管理 | `go mod tidy` |
| `go env` | 查看/设置环境变量 | `go env -w GOPROXY=...` |
| `go doc` | 查看包文档 | `go doc fmt.Println` |
| `go clean` | 清理构建缓存 | `go clean -cache` |

工具链的设计原则是"**约定优于配置**"：测试文件必须以 `_test.go` 结尾，包必须放在目录中，格式化没有可选项。这些约定消除了团队间的无谓争论。

### 5. GOPATH 与 Go Modules

**GOPATH 时代（Go 1.11 之前）**：所有项目必须放在 `$GOPATH/src` 下，依赖也统一放在 GOPATH 中，无法为不同项目锁定不同版本，被称为"依赖地狱"。

**Go Modules（Go 1.11 引入，1.16 默认开启）**：每个项目拥有独立的 `go.mod`，可以放在磁盘任意位置，依赖版本精确锁定。

```bash
# 初始化模块（模块路径通常与代码仓库地址一致）
go mod init eshop/gateway

# 添加依赖（自动写入 go.mod 与 go.sum）
go get github.com/google/uuid@v1.6.0

# 清理未使用依赖、补齐缺失依赖
go mod tidy

# 下载依赖到本地缓存
go mod download
```

一个最小的 `go.mod`：

```
module eshop/gateway

go 1.22
```

| 文件 | 作用 |
|------|------|
| `go.mod` | 声明模块路径、Go 版本、直接依赖及版本 |
| `go.sum` | 记录依赖内容的校验和，保证可重复构建 |
| `go.work` | 多模块工作区（本地联调多个模块时使用） |

> **模块路径不是网址**，它只是依赖的全局唯一标识。发布到公共仓库时通常写成 `github.com/用户名/项目名`。

### 6. 包、入口与项目结构

Go 以**包（package）**为最小组织单元，一个目录就是一个包：

- 同目录下的 `.go` 文件必须声明**同一个包名**
- `package main` 是可执行程序的入口包，必须包含 `func main()`
- 其他包名（如 `package product`）是可被导入的库包
- **首字母大写**的标识符可导出（public），小写仅包内可见（private）

```go
package main

import (
	"fmt"
	"strings"
)

func main() {
	fmt.Println(strings.ToUpper("hello"))
}
```

标准项目布局（社区约定，非强制）：

```
eshop-gateway/
├── go.mod
├── main.go              ← package main，程序入口
├── internal/            ← 私有代码，外部模块不可导入
│   ├── handler/
│   └── service/
├── pkg/                 ← 可被外部复用的公共包
└── cmd/                 ← 多入口时按命令拆分子目录
    └── server/main.go
```

> 本教程的 Day01-Day11 示例为了"单文件可运行"，全部使用 `package main`。真实项目应按职责拆分包与目录。

### 7. 第一个程序

```go
package main

import "fmt"

func main() {
	fmt.Println("Hello, Go!")
}
```

运行：

```bash
go run hello.go
```

程序结构说明：

1. `package main`：声明入口包
2. `import "fmt"`：导入标准库格式化包
3. `func main()`：程序唯一入口，无参数、无返回值
4. `fmt.Println`：输出并换行

### 8. 命令行参数：os.Args 与 flag

**方式一：`os.Args`**，原始字符串切片，第 0 个是程序路径：

```go
// go run cli_args.go apple banana
// os.Args = [临时程序路径 apple banana]
```

**方式二：`flag` 包**，支持命名参数、默认值、类型解析与自动帮助：

```go
name := flag.String("name", "guest", "用户名称")
count := flag.Int("count", 1, "商品数量")
flag.Parse()
fmt.Println(*name, *count)
```

```bash
go run cli_args.go -name 张三 -count 3 -v
go run cli_args.go -h          # 自动打印帮助
```

> `flag` 返回的是指针，取值需要解引用 `*name`。这是 Go 中"用指针表达可选值"的常见写法。

### 9. gofmt 与代码风格

Go 把格式化做成强制标准，没有配置项：

```bash
gofmt -w .            # 格式化当前目录所有 Go 文件
go fmt ./...          # 等价于 gofmt，但作用于包
```

核心风格约定：

- 使用 **Tab** 缩进（gofmt 自动处理）
- 左大括号 `{` **不能另起一行**
- `if` / `for` 条件**不加括号**
- 导入分组：标准库、第三方库、本地包，组间空行
- 导出标识符必须有文档注释，注释以标识符名开头
- 命名简洁：`userID` 而非 `userIdentifier`，包内避免重复包名

```go
// Product 表示电商商品。
type Product struct {
	Name  string  `json:"name"`
	Price float64 `json:"price"`
}
```

### 10. 与 Python / Node.js 的关键差异

| 维度 | Go | Python | Node.js |
|------|----|--------|---------|
| 变量声明 | `var x int` / `x := 1` | `x = 1` | `let x = 1` |
| 类型转换 | 必须显式 `int64(x)` | 构造函数 | 隐式/显式 |
| 错误处理 | 返回值 `error` | 异常 | 异常 |
| 空值 | `nil`（仅引用类型） | `None` | `null`/`undefined` |
| 并发 | goroutine + channel | 线程/asyncio | 事件循环 |
| 依赖管理 | go.mod | requirements/Poetry | package.json |
| 格式化 | gofmt 强制 | black（可选） | prettier（可选） |

对已有 Python/TS 经验的学习者，最容易踩的坑是：**Go 没有隐式类型转换**、**未使用的变量/导入会直接编译失败**、**循环变量与闭包捕获在旧版本有陷阱（1.22 已修复）**。

## 环境搭建

完整的三平台安装步骤、代理配置、VS Code 配置与常见问题见 [Code/README.md](./Code/README.md)。

快速验证：

```bash
go version                     # go version go1.23.x windows/amd64
go env GOPROXY                 # 国内建议 https://goproxy.cn,direct
cd "Day01 - Go语言入门与环境搭建/Code"
go run hello.go                # 输出 Hello, Go!
```

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/hello.go` | 第一个 Go 程序：包声明、导入、常量、函数、`main` 入口与 `fmt` 输出 |
| `Code/env_check.go` | 环境检查：`runtime.Version`、`GOOS/GOARCH`、CPU 核数、`GOMAXPROCS`、`GOPATH` |
| `Code/cli_args.go` | 命令行参数：`os.Args` 与 `flag` 包（字符串/整数/布尔参数、默认值、帮助） |
| `Code/fmt_demo.go` | `fmt` 格式化：`Print/Printf/Sprintf`、常用动词、宽度精度、`strings.Builder` |
| `Code/README.md` | 环境配置详细指南（三平台安装、代理、IDE、模块初始化、常见问题） |

执行方式（每个文件独立运行）：

```bash
cd "Day01 - Go语言入门与环境搭建/Code"
go run hello.go
go run env_check.go
go run cli_args.go -name 张三 -count 3 -v
go run fmt_demo.go
```

> 同一目录下多个文件都有 `main` 函数，因此不要执行 `go run .`，请按文件名单独运行。

## 关键知识点总结

1. **Go 定位**：静态编译、原生并发、工程友好的通用语言，是云原生基础设施的主流选择。
2. **执行模型**：源码编译为静态单一二进制，运行时无需解释器或虚拟机。
3. **工具链**：`go run/build/install/fmt/vet/test/mod/env/doc` 覆盖开发全流程。
4. **Go Modules**：`go.mod` 声明模块与依赖，`go.sum` 保证校验，项目可放在任意目录。
5. **包与入口**：`package main` + `func main()`；首字母大小写决定导出可见性。
6. **第一个程序**：`package` → `import` → `func main()`，结构固定且极简。
7. **命令行参数**：`os.Args` 取原始参数，`flag` 提供类型化命名参数与帮助。
8. **格式化**：`gofmt` 是强制标准，没有配置项；Tab 缩进、左括号不换行。
9. **常见编译错误**：未使用变量、未使用导入、隐式类型转换、包名不一致。
10. **环境验证**：`go version` 输出 1.22+、`go run hello.go` 正常输出即环境就绪。

## 实战练习

### 练习 1：环境就绪验证

1. 安装 Go 1.22+，执行 `go version` 与 `go env GOPATH`，记录输出。
2. 执行 `go env -w GOPROXY=https://goproxy.cn,direct`，再用 `go env GOPROXY` 确认。
3. 创建任意目录，执行 `go mod init eshop/hello`，查看生成的 `go.mod` 内容。
4. 运行 `env_check.go`，记录你的 `GOOS`、`GOARCH`、CPU 核数与 `GOMAXPROCS` 默认值，并解释 `GOMAXPROCS` 的含义。

### 练习 2：第一个 eshop 程序

新建 `eshop_hello.go`，要求：

- 定义常量 `ServiceName = "eshop-gateway"` 与 `Version = "0.1.0"`
- 定义函数 `banner(name string) string`，返回形如 `=== eshop-gateway v0.1.0 ===` 的字符串
- 在 `main` 中打印 banner，并输出当前 Go 版本
- 用 `go run` 运行，再用 `go build -o eshop_hello.exe eshop_hello.go` 生成可执行文件并直接运行

### 练习 3：命令行小工具

编写 `product_cli.go`，使用 `flag` 解析：

- `-name`：商品名称，默认 `iPhone 15`
- `-price`：单价（`float64`），默认 `5999`
- `-count`：数量（`int`），默认 `1`

输出总价，保留两位小数，并在 `-count <= 0` 时输出友好错误。示例：

```bash
go run product_cli.go -name "MacBook Pro" -price 12999 -count 2
# 商品：MacBook Pro
# 单价：12999.00 × 2
# 总价：25998.00
```

### 练习 4：交叉编译体验

在 Windows 上执行：

```bash
$env:GOOS="linux"; $env:GOARCH="amd64"; go build -o hello_linux hello.go
```

观察生成的文件名与大小，思考：为什么 Go 编译出的程序不需要目标机器安装 Go？
