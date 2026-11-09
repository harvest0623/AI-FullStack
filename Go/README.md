# Go 语言学习指南

> 系统化掌握 Go 的核心语法、并发模型与工程化实践，构建高并发 AI 后端服务

> 共 13 天，覆盖从环境搭建、语言基础、接口与错误处理，到并发编程、Web 服务与云原生部署的完整知识体系

---

## 目录

- [板块定位](#板块定位)
- [前置要求](#前置要求)
- [学习路线图](#学习路线图)
- [示例项目](#示例项目)
- [每日内容详表](#每日内容详表)
- [目录结构](#目录结构)
- [学习建议](#学习建议)
- [如何运行代码](#如何运行代码)
- [知识点速查](#知识点速查)
- [后续板块](#后续板块)
- [学习资源补充](#学习资源补充)

---

## 板块定位

本板块是 AI 全栈学习系列的**高性能服务端语言**板块。Go 由 Google 于 2009 年开源，凭借极简语法、原生并发、快速编译和单一静态二进制，成为云原生时代的"基础设施语言"。Kubernetes、Docker、etcd、Prometheus、Terraform 等明星项目均以 Go 编写；在 AI 领域，Ollama、MCP 服务端、向量检索网关、模型推理前置服务也大量采用 Go。

**与 Python 板块的关系**：Python 负责模型训练、数据处理与实验迭代，Go 负责把能力包装成高并发、低延迟、易部署的线上服务。二者组合是当前 AI 应用最常见的"Python 做智能，Go 做服务"架构。

**与 Node.js 板块的关系**：两者都适合写 API 服务。Node.js 胜在生态与开发速度，Go 胜在并发性能、内存占用与部署体积。学完两端后，你能根据团队与场景做出技术选型，而不是只会一种技术。

**学习目标**：完成本板块后，你应能：
- 熟练使用 Go 语法编写可维护的命令行工具与服务
- 理解值语义、指针、切片底层结构与接口的隐式实现
- 掌握 Go 的错误处理哲学与 `defer` / `panic` / `recover` 的正确用法
- 用 goroutine、channel、`sync`、`context` 编写并发程序并避免数据竞争
- 用标准库 `net/http` 构建 RESTful API 与中间件
- 用 `go test`、基准测试、`httptest` 完成质量保障
- 用 Go Modules、交叉编译、Docker 多阶段构建交付生产服务
- 独立实现一个可调用大模型的 AI 网关项目

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + 可执行代码 + 实战练习
- 全程围绕统一的**电商 AI 网关 `eshop-gateway`** 项目逐步演进
- 所有代码仅依赖 Go 标准库，可在 Go 1.22+ 直接运行
- 紧扣 AI 全栈视角，为 LLM 服务化、MCP、云原生部署铺垫

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| 编程基础 | 熟练 | 至少掌握一门语言（Python / TypeScript / Java 均可） |
| 命令行操作 | 基础 | 能在终端执行命令、配置环境变量 |
| HTTP 基础 | 了解 | 知道请求方法、状态码、JSON 即可 |
| 并发概念 | 了解 | 线程、锁、异步的基本直觉（没有也可，Day09 从头讲） |
| 操作系统概念 | 基础 | 进程、内存、文件系统 |

**环境准备**：
- Go 1.22 或更高（推荐 1.23+，本板块以 1.22+ 为基准）
- VS Code（安装 Go 扩展，自动获得 gopls、dlv 调试）
- Git
- 可选：Docker（Day12 部署、Day13 实战需要）

> Go 1.22 引入了增强版 `http.ServeMux` 路由（`GET /items/{id}`），本板块 Day11 会直接使用，因此请勿使用更早版本。

---

## 学习路线图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Go 学习路线（13 天）                          │
└─────────────────────────────────────────────────────────────────┘

阶段一：语言基础（Day01-Day05）
┌────────┬────────┬────────┬────────┬────────┐
│ Day01  │ Day02  │ Day03  │ Day04  │ Day05  │
│ 入门与 │ 变量   │ 控制流 │ 数组   │ 字符串 │
│ 环境   │ 常量   │ 与函数 │ 切片   │ 指针   │
│        │ 类型   │        │ Map    │ 内存   │
└───┬────┴───┬────┴───┬────┴───┬────┴───┬────┘
    │        │        │        │        │
    ▼        ▼        ▼        ▼        ▼
阶段二：抽象与工程（Day06-Day08）
┌────────────────┬────────────────┬────────────────┐
│ Day06 结构体   │ Day07 错误处理 │ Day08 泛型与   │
│ 方法与接口     │ defer/panic    │ 标准库         │
└───────┬────────┴───────┬────────┴───────┬────────┘
        │                │                │
        ▼                ▼                ▼
阶段三：并发与服务（Day09-Day11）
┌────────────────┬────────────────┬────────────────┐
│ Day09 并发编程 │ Day10 文件IO   │ Day11 Web 服务 │
│ goroutine/chan │ JSON/HTTP      │ RESTful API    │
└───────┬────────┴───────┬────────┴───────┬────────┘
        │                │                │
        ▼                ▼                ▼
阶段四：工程化与实战（Day12-Day13）
┌──────────────────────────────────────────────────┐
│ Day12 测试、工程化与部署                          │
│ Day13 实战：构建 AI 应用后端（LLM 网关）          │
└──────────────────────────────────────────────────┘
```

**阶段目标**：
- **阶段一**：能写出正确的 Go 程序，理解值语义与切片行为
- **阶段二**：能用结构体/接口组织代码，写出符合 Go 习惯的错误处理
- **阶段三**：能写并发程序与可上线的 HTTP API
- **阶段四**：能测试、构建、容器化并交付一个真实 AI 服务

---

## 示例项目

本板块全程围绕**电商 AI 网关 `eshop-gateway`** 展开。它对外提供商品查询与 AI 导购对话能力，是"传统业务 API + 大模型能力"的典型组合。

### 项目演进路线

| 阶段 | 用到的知识 | 项目能力 |
|------|-----------|---------|
| Day01-Day05 | 语法、切片、Map、字符串 | 商品数据的结构与基础处理 |
| Day06-Day08 | 结构体、接口、错误、泛型 | 商品仓储抽象、统一错误、通用分页 |
| Day09-Day10 | 并发、IO、JSON、HTTP 客户端 | 并发聚合商品信息、调用上游服务 |
| Day11 | `net/http` | 商品 REST API 与中间件 |
| Day12 | 测试、Docker、交叉编译 | 质量保障与部署交付 |
| Day13 | 综合实战 | LLM 对话网关（含超时、重试、限流、SSE） |

### 最终项目结构（Day13）

```
eshop-gateway/
├── go.mod
├── main.go                 ← 服务入口与优雅关闭
├── config.go               ← 环境变量配置
├── client.go               ← 上游 LLM 客户端（超时、重试）
├── handler.go              ← /v1/chat、/healthz 处理器
├── middleware.go           ← 日志、限流、恢复、CORS
├── handler_test.go         ← httptest 单元测试
└── README.md               ← 运行与接口说明
```

> 各天的代码是这个项目的"零件"，Day13 将它们组装为完整服务。所有示例均只使用标准库，便于离线运行与理解。

---

## 每日内容详表

### 阶段一：语言基础

#### Day01 - Go语言入门与环境搭建
- **核心**：Go 的诞生背景与设计哲学、静态编译与执行模型、Go 工具链（`go run/build/install/fmt/vet/test`）、GOPATH 与 Go Modules、`go.mod` / `go.sum`、包与入口 `package main`、`import` 规则、第一个程序、`fmt` 输出、命令行参数 `os.Args` 与 `flag`、`runtime` 环境信息、gofmt 代码风格、VS Code + gopls 配置、Go Playground
- **代码**：`hello.go` / `env_check.go` / `cli_args.go` / `fmt_demo.go` / `README.md`（环境配置指南）
- **重点**：Go Modules、`go run` 与 `go build` 的差异、包结构约定

#### Day02 - 变量、常量与基础类型
- **核心**：`var` 与 `:=` 短变量声明、零值机制、作用域与变量遮蔽、常量与 `const` 块、`iota` 枚举、无类型常量、整数家族（`int/int8…uint64/uintptr`）、浮点与复数、布尔、字符串、`byte` 与 `rune`、类型转换（显式转换、无隐式转换）、`strconv` 字符串转换、`fmt` 格式化动词与宽度精度
- **代码**：`variables.go` / `constants_iota.go` / `types_conversion.go` / `fmt_format.go`
- **重点**：零值、显式类型转换、`byte` vs `rune`、`fmt` 动词

#### Day03 - 控制流与函数
- **核心**：`if`（可带初始化语句、无括号）、`for` 的三种形态、`range` 遍历、`switch`（自动 break、可省略表达式、类型 switch 预览）、`break/continue` 与标签、`goto`、函数定义与调用、多返回值、命名返回值、可变参数、函数作为一等公民、闭包与捕获、递归、`defer` 初识与执行顺序
- **代码**：`control_flow.go` / `functions.go` / `closures.go` / `switch_demo.go`
- **重点**：`for range`、多返回值、闭包捕获、`defer` 执行顺序

#### Day04 - 数组、切片与 Map
- **核心**：数组的值语义与长度是类型的一部分、切片三要素（指针/长度/容量）、`make` 与字面量、`append` 扩容策略、切片共享底层数组的陷阱、`copy`、三索引切片、二维切片、`map` 增删改查、`comma-ok`、`delete`、遍历顺序随机、`map` 作为集合、`nil` 切片与空切片、`slices` / `maps` 标准库初探
- **代码**：`arrays.go` / `slices.go` / `maps.go` / `slice_internals.go`
- **重点**：切片共享与扩容、`append` 陷阱、`map` 并发不安全

#### Day05 - 字符串、指针与内存
- **核心**：字符串不可变与 UTF-8 编码、`len` 与字节/字符的区别、`rune` 与 `range` 遍历、`strings` 常用函数、`strings.Builder` 高效拼接、`strconv` 转换、指针基础（`&` / `*`、无指针运算）、`new` 与 `make` 的区别、值传递与指针传递、结构体指针、逃逸分析与栈/堆、GC 三色标记简介、内存对齐
- **代码**：`strings_demo.go` / `runes_utf8.go` / `pointers.go` / `memory_demo.go`
- **重点**：UTF-8 与 `rune`、指针语义、`new` vs `make`、逃逸分析

---

### 阶段二：抽象与工程

#### Day06 - 结构体、方法与接口
- **核心**：结构体定义与初始化（字段名/位置）、匿名字段与嵌入、结构体标签 `json:"..."`、方法定义、值接收者与指针接收者、方法集与接口实现、接口的隐式实现、空接口 `any`、类型断言与 `comma-ok`、类型 switch、`Stringer` 接口、接口嵌套、嵌入 vs 继承、`nil` 接口陷阱
- **代码**：`structs.go` / `methods.go` / `interfaces.go` / `embedding.go`
- **重点**：值/指针接收者如何影响接口实现、隐式接口、`nil` 接口陷阱

#### Day07 - 错误处理与defer、panic、recover
- **核心**：`error` 接口与 `errors.New`、`fmt.Errorf` 与 `%w` 错误包装、`errors.Is` / `errors.As`、哨兵错误、自定义错误类型、错误链与 `errors.Join`、错误处理最佳实践（早返回、包装上下文、不忽略错误）、`defer` 执行顺序与参数求值时机、`defer` 与命名返回值、`panic` / `recover` 使用边界、`runtime/debug.Stack`
- **代码**：`errors_basic.go` / `error_wrap.go` / `custom_error.go` / `defer_panic.go`
- **重点**：`%w` 与 `errors.Is/As`、`defer` 参数求值、何时该 panic

#### Day08 - 泛型与标准库
- **核心**：类型参数与类型约束、`any` / `comparable`、`~` 底层类型约束、联合约束、泛型函数与泛型类型、类型推断、泛型使用边界、`slices` / `maps` 包（`Sort` / `Contains` / `Index` / `Clone` 等）、`sort` 包、`time` 时间与定时器、`math`、`strings` / `strconv`、`regexp`、`flag`、`log/slog` 结构化日志、`min/max` 内置函数
- **代码**：`generics.go` / `generics_constraints.go` / `stdlib_slices.go` / `stdlib_time.go`
- **重点**：类型约束设计、泛型何时值得用、`slices` / `slog` 实战

---

### 阶段三：并发与服务

#### Day09 - 并发编程（goroutine 与 channel）
- **核心**：并发 vs 并行、goroutine 创建与调度、GMP 模型、`channel` 无缓冲/有缓冲、发送接收与阻塞、`close` 与 `range`、单向 channel、`select` 多路复用与 `default`、超时控制、`sync.WaitGroup` / `Mutex` / `RWMutex` / `Once`、`sync/atomic`、`context` 取消与超时、worker pool、pipeline、扇出/扇入、数据竞争与 `go run -race`、常见并发陷阱（goroutine 泄漏、循环变量捕获）
- **代码**：`goroutines.go` / `channels.go` / `select_timeout.go` / `sync_demo.go` / `worker_pool.go` / `context_demo.go`
- **重点**：channel 通信优于共享内存、`context` 传播、race detector

#### Day10 - 文件 IO、JSON 与 HTTP 客户端
- **核心**：`os` 文件读写与权限、`bufio` 缓冲读写、`io.Reader` / `io.Writer` 接口与组合、`io.Copy`、`embed` 嵌入静态资源、`encoding/json` 序列化与反序列化、结构体标签与 `omitempty`、`json.Decoder` / `Encoder` 流式处理、`net/http` 客户端、超时与 `context`、状态码与响应体处理、重试思路、CSV 读写
- **代码**：`file_io.go` / `json_demo.go` / `http_client.go` / `io_interfaces.go`
- **重点**：`io.Reader/Writer` 抽象、JSON 标签、HTTP 客户端超时

#### Day11 - Web 服务与 RESTful API
- **核心**：`net/http` 服务端、`http.Handler` / `HandlerFunc`、Go 1.22 增强 `ServeMux`（方法 + 路径参数）、RESTful 资源设计、JSON 请求解析与响应、状态码与统一错误结构、中间件（日志/恢复/CORS/鉴权思路）、`http.Server` 超时配置、优雅关闭 `Shutdown`、并发安全的内存仓储、限流基础
- **代码**：`basic_server.go` / `rest_api.go` / `middleware.go` / `graceful_shutdown.go`
- **重点**：Go 1.22 路由语法、中间件链、优雅关闭

---

### 阶段四：工程化与实战

#### Day12 - 测试、工程化与部署
- **核心**：`go test` 与测试文件约定、表驱动测试、子测试 `t.Run`、`t.Helper`、覆盖率、基准测试 `Benchmark`、示例测试 `Example`、模糊测试 `Fuzz`、`httptest` 测试 HTTP 服务、`go vet` / `staticcheck` / `golangci-lint`、`go mod tidy` / `vendor`、构建标签、`-ldflags` 注入版本、交叉编译、`pprof` 性能分析、Makefile、Docker 多阶段构建、最小镜像
- **代码**：`calc/`（含 `calculator.go` / `calculator_test.go` / `benchmark_test.go`）、`httpdemo/`（含 `server.go` / `server_test.go`）、`go.mod` / `Dockerfile` / `Makefile` / `README.md`
- **重点**：表驱动测试、`httptest`、Docker 多阶段构建与交叉编译

#### Day13 - 实战：构建 AI 应用后端（LLM 网关）
- **核心**：需求与架构设计、配置管理（环境变量）、上游 OpenAI 兼容 API 客户端、请求/响应结构、超时与重试、错误映射、限流中间件、日志与请求 ID、SSE 流式响应思路、`httptest` 测试、优雅关闭、部署清单
- **代码**：`llm-gateway/`（`main.go` / `config.go` / `client.go` / `handler.go` / `middleware.go` / `handler_test.go` / `go.mod` / `README.md`）
- **重点**：把语言知识组装为可运行服务、上游依赖的可测试性设计

---

## 目录结构

```
Go/
├── README.md                              ← 本文件（板块总入口）
├── Day01 - Go语言入门与环境搭建/
│   ├── README.md                          ← 当天学习文档
│   └── Code/
│       ├── hello.go
│       ├── env_check.go
│       ├── cli_args.go
│       ├── fmt_demo.go
│       └── README.md                      ← 环境配置详细指南
├── Day02 - 变量、常量与基础类型/
│   ├── README.md
│   └── Code/
│       ├── variables.go
│       ├── constants_iota.go
│       ├── types_conversion.go
│       └── fmt_format.go
├── ...（Day03-Day11 同构，每天 README.md + Code/）...
├── Day12 - 测试、工程化与部署/
│   ├── README.md
│   └── Code/
│       ├── go.mod
│       ├── calc/
│       │   ├── calculator.go
│       │   ├── calculator_test.go
│       │   └── benchmark_test.go
│       ├── httpdemo/
│       │   ├── server.go
│       │   └── server_test.go
│       ├── cmd/
│       │   └── server/
│       │       └── main.go
│       ├── Dockerfile
│       ├── Makefile
│       └── README.md
└── Day13 - 实战：构建AI应用后端/
    ├── README.md
    └── Code/
        └── llm-gateway/
            ├── go.mod
            ├── main.go
            ├── config.go
            ├── client.go
            ├── handler.go
            ├── middleware.go
            ├── handler_test.go
            └── README.md
```

**结构约定**：
- 每个 `DayXX` 文件夹下有**根级** `README.md`（学习文档）
- 代码统一放在 `Code/` 子文件夹内
- Day01-Day11 的每个 `.go` 文件都是**独立可运行**的示例（各自含 `package main` 和 `main` 函数），使用 `go run 文件名.go` 运行
- Day12-Day13 属于同一模块的多个文件，需在对应目录内执行 `go test ./...` 或 `go run .`
- 除 Day12/Day13 的 `go.mod` 外，其余示例均为单文件，不需要初始化模块

> 注意：同一 `Code/` 目录下多个文件都有 `main` 函数，**不能**直接执行 `go run .`，请按文件名单独运行。这是为了让每个示例彼此独立、便于对照阅读。

---

## 学习建议

### 推荐学习节奏

| 节奏 | 适合人群 | 每天投入 | 完成周期 |
|------|---------|---------|---------|
| 激进 | 全职学习 | 4-6 小时 | 约 2 周 |
| 标准 | 业余学习 | 2-3 小时 | 约 4 周 |
| 保守 | 碎片时间 | 1 小时 | 约 2 月 |

### 学习方法论

1. **先读后写**：先通读当天 README，理解设计动机，再逐个运行 `Code/` 中的示例
2. **改坏再修**：主动修改切片容量、channel 缓冲、接口实现等参数，观察报错与行为变化
3. **对照旧语言**：用 Python/TypeScript 的直觉对比 Go 的显式转换、值语义与错误返回
4. **善用工具链**：每次写完代码执行 `gofmt -w .` 与 `go vet ./...`，养成工程习惯
5. **并发必开 race**：Day09 起所有并发示例都用 `go run -race 文件名.go` 验证
6. **完成实战**：每天末尾练习必须动手；Day13 的网关项目建议独立重写一遍

### 阶段性检查点

- **阶段一完成后**：能否解释切片共享底层数组导致的问题？能否写出正确处理 UTF-8 的字符串统计？
- **阶段二完成后**：能否为一组业务类型设计接口，并用 `%w` 包装错误链路？
- **阶段三完成后**：能否用 goroutine + channel + context 实现带超时的并发聚合？能否写出可优雅关闭的 HTTP 服务？
- **阶段四完成后**：能否为 HTTP 服务写表驱动测试与基准测试？能否用 Docker 多阶段构建产出小于 20MB 的镜像？

---

## 如何运行代码

### 安装 Go

1. 从 [go.dev/dl](https://go.dev/dl/) 下载对应平台安装包
2. Windows 安装后确认 `go` 已加入 PATH；macOS 可用 `brew install go`
3. 验证：

```bash
go version          # 输出 go version go1.23.x ...
go env GOPATH       # 查看模块缓存与工作目录
```

国内网络建议配置代理：

```bash
go env -w GOPROXY=https://goproxy.cn,direct
```

### 运行单文件示例（Day01-Day11）

```bash
# 在对应 Day 的 Code 目录下执行
go run hello.go

# 带数据竞争检测运行并发示例
go run -race goroutines.go

# 只检查编译，不运行
go build -o /tmp/demo hello.go
```

### 运行模块化示例（Day12-Day13）

```bash
cd "Day12 - 测试、工程化与部署/Code"
go test ./...                 # 运行全部测试
go test -bench=. -benchmem ./calc
go test -cover ./...

cd "../Day13 - 实战：构建AI应用后端/Code/llm-gateway"
go mod tidy
go test ./...
go run .                      # 启动网关，默认监听 :8080
```

### 使用 Docker

```bash
# 直接用官方镜像运行单文件
docker run --rm -v "$PWD:/app" -w /app golang:1.23 go run hello.go

# 构建 Day12 的多阶段镜像
cd "Day12 - 测试、工程化与部署/Code"
docker build -t eshop-api:dev .
docker run --rm -p 8080:8080 eshop-api:dev
```

### 常用命令速查

| 命令 | 作用 |
|------|------|
| `go run file.go` | 编译并立即运行 |
| `go build -o app` | 编译为可执行文件 |
| `go install` | 安装到 `$GOPATH/bin` |
| `go mod init <module>` | 初始化模块 |
| `go mod tidy` | 补齐/清理依赖 |
| `go fmt ./...` / `gofmt -w .` | 格式化代码 |
| `go vet ./...` | 静态检查 |
| `go test ./...` | 运行测试 |
| `go test -race ./...` | 竞争检测 |
| `go env` | 查看 Go 环境变量 |
| `GOOS=linux GOARCH=amd64 go build` | 交叉编译 |

---

## 知识点速查

### 基础类型零值

| 类型 | 零值 | 说明 |
|------|------|------|
| `int` / `int64` 等 | `0` | 有符号整数默认 0 |
| `uint` 等 | `0` | 无符号整数默认 0 |
| `float32` / `float64` | `0` | 不是 `nil` |
| `bool` | `false` | 布尔零值 |
| `string` | `""` | 空字符串，不是 `nil` |
| `byte` | `0` | `uint8` 别名 |
| `rune` | `0` | `int32` 别名，表示 Unicode 码点 |
| 指针 / 接口 / 切片 / Map / Channel / 函数 | `nil` | 引用类型零值 |

### 复合类型对比

| 类型 | 是否值类型 | 可否比较 | 零值 | 典型用途 |
|------|-----------|---------|------|---------|
| 数组 `[N]T` | 是 | 长度相同即可 `==` | 全零元素 | 固定长度数据 |
| 切片 `[]T` | 否（含指针） | 只能与 `nil` 比较 | `nil` | 动态列表 |
| Map `map[K]V` | 否 | 只能与 `nil` 比较 | `nil` | 键值查找 |
| 结构体 `struct` | 是 | 字段均可比较时可 `==` | 字段零值 | 业务模型 |
| 指针 `*T` | 是（地址值） | 可 `==` | `nil` | 共享修改 |
| 接口 `interface` | 是（类型+值） | 可 `==`（动态值可比较时） | `nil` | 抽象与多态 |

### 并发原语速查

| 原语 | 适用场景 | 注意事项 |
|------|---------|---------|
| `go func()` | 启动并发任务 | 需自行保证生命周期结束 |
| `chan T` | goroutine 间通信 | 无缓冲需双方就绪 |
| `chan T`（带缓冲） | 解耦生产消费 | 缓冲不是无限队列 |
| `select` | 多 channel 多路复用 | 配合 `default` 实现非阻塞 |
| `sync.WaitGroup` | 等待一组任务完成 | `Add` 必须在 `Wait` 前 |
| `sync.Mutex` | 保护共享状态 | 不可复制锁 |
| `sync.RWMutex` | 读多写少 | 写锁独占 |
| `sync.Once` | 只执行一次初始化 | 常用于单例 |
| `sync/atomic` | 简单计数与标志 | 避免复杂逻辑 |
| `context.Context` | 取消、超时、传值 | 只传请求域数据 |

### 标准库速查

| 包 | 用途 | 对应天数 |
|----|------|---------|
| `fmt` | 格式化输入输出 | Day01-Day02 |
| `strings` / `strconv` | 字符串处理与转换 | Day05 |
| `slices` / `maps` | 切片与 Map 泛型工具 | Day08 |
| `sort` | 排序 | Day08 |
| `time` | 时间、定时器、超时 | Day08 |
| `errors` | 错误创建、判断、包装 | Day07 |
| `context` | 取消与超时传播 | Day09 |
| `sync` / `sync/atomic` | 并发同步 | Day09 |
| `os` / `bufio` | 文件与缓冲 IO | Day10 |
| `encoding/json` | JSON 编解码 | Day10 |
| `net/http` | HTTP 客户端与服务端 | Day10-Day11 |
| `testing` / `httptest` | 测试 | Day12 |
| `log/slog` | 结构化日志 | Day08-Day13 |

### 与 Python / TypeScript 对照

| 概念 | Go | Python | TypeScript |
|------|----|--------|-----------|
| 变量声明 | `var x int` / `x := 1` | `x = 1` | `let x = 1` |
| 类型转换 | 显式 `int64(x)` | 构造函数 `int(x)` | 断言/转换函数 |
| 空值 | `nil`（仅引用类型） | `None` | `null` / `undefined` |
| 错误处理 | 返回 `error` 值 | `try/except` | `try/catch` |
| 并发 | goroutine + channel | 线程/asyncio | 事件循环/Promise |
| 接口 | 隐式实现 | 抽象基类/协议 | `interface` 显式实现 |
| 可见性 | 首字母大小写 | 下划线约定 | `public/private` |
| 依赖管理 | Go Modules | pip/Poetry | npm/pnpm |

---

## 后续板块

本板块完成后，推荐按以下顺序继续学习：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **Docker** | 用多阶段构建把 Go 服务打包为极小镜像并部署 |
| **Redis** | 为网关增加缓存、限流计数与分布式锁 |
| **PostgreSQL / MySQL** | 用 `database/sql` 接入持久化存储 |
| **MCP** | Go 适合实现高性能 MCP Server 与工具代理 |
| **LLM / RAG** | 将 Python 侧模型能力通过 HTTP/gRPC 暴露，由 Go 网关统一编排 |
| **Nginx** | Go 服务前置反向代理、TLS 与负载均衡 |

---

## 学习资源补充

> 以下为官方权威资源，遇到疑问时优先查阅

- [Go 官方文档](https://go.dev/doc/) - 语言规范与标准库
- [A Tour of Go](https://go.dev/tour/) - 官方交互式入门教程
- [Effective Go](https://go.dev/doc/effective_go) - 地道 Go 代码写法
- [Go by Example](https://gobyexample.com/) - 按主题的可运行示例
- [Go 标准库文档](https://pkg.go.dev/std) - 包级 API 查询
- [Go Blog](https://go.dev/blog/) - 版本特性与设计思路
- [The Go Programming Language](https://www.gopl.io/) - 经典进阶教材

---

## 贡献与反馈

本学习手册为原创内容，参考 GitHub 优质仓库的文档风格但不复制任何内容。如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，用 Go 构建你的 AI 全栈服务底座！**
