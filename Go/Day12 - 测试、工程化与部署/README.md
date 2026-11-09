# Day12 - 测试、工程化与部署

## 本章简介

写得出功能只是第一步，能证明它正确、可重复构建、可安全交付，才算完成工程闭环。Go 把测试、格式化、静态检查、依赖管理、交叉编译全部内置，配合 `httptest` 与 Docker 多阶段构建，可以用极低的工具链成本达到生产级交付标准。本章围绕示例模块 `eshop/engineering` 展开：先用表驱动测试、示例测试与基准测试覆盖 `calc` 包，再用 `httptest` 测试 HTTP 处理器；随后讲解覆盖率、模糊测试、`pprof`、版本注入与交叉编译；最后用 Dockerfile 与 Makefile 把测试、构建、镜像打包串成流水线。这些知识会直接用于 Day13 的网关项目。

## 学习目标

- 理解 Go 测试的文件约定、包约定与 `go test` 执行流程
- 掌握表驱动测试与 `t.Run` 子测试，能用 `t.Helper` 改善失败定位
- 会使用覆盖率、基准测试与示例测试衡量质量与性能
- 理解基准测试中 `b.N`、`b.ResetTimer` 与防止编译器优化的重要性
- 能编写模糊测试（`Fuzz`）并运行种子语料
- 能用 `httptest.NewRecorder` / `NewRequest` 测试 Handler，无需真实端口
- 掌握 `go vet`、`staticcheck`、`golangci-lint` 的定位与使用时机
- 理解 `go mod tidy` / `vendor` 与 CI 可重复构建
- 会用构建标签区分平台/环境，能用 `-ldflags "-X"` 注入版本
- 掌握 `GOOS/GOARCH` 交叉编译与 `pprof` 性能分析
- 能编写多阶段 Dockerfile，产出非 root 的小体积镜像
- 能用 Makefile 串联测试、构建、镜像与清理命令

## 理论知识讲解

### 1. Go 测试约定

| 约定 | 说明 |
| --- | --- |
| 文件名 `*_test.go` | 只有这种文件会被 `go test` 编译执行 |
| 函数名 `TestXxx(t *testing.T)` | 测试入口，`Xxx` 不能小写开头 |
| 同目录同包 | 测试可直接访问包内未导出标识符 |

- `package calc` 是**白盒测试**，可调用未导出函数；`package calc_test` 是**黑盒测试**，只用导出 API。
- `go test` 默认缓存成功结果，代码未变时输出 `(cached)`，调试用 `-count=1` 绕开。

```bash
go test ./...                  # 运行所有包
go test -v ./calc              # 输出每个测试与子测试
go test -run TestDivide ./calc # 正则筛选
go test -race ./...            # 数据竞争检测
```

### 2. 表驱动测试与子测试

```go
tests := []struct {
	name    string
	a, b    float64
	want    float64
	wantErr error
}{
	{name: "整除", a: 10, b: 2, want: 5},
	{name: "除数为零", a: 1, b: 0, wantErr: ErrDivideByZero},
}
for _, tt := range tests {
	t.Run(tt.name, func(t *testing.T) {
		got, err := Divide(tt.a, tt.b)
		// 断言……
	})
}
```

- 新增场景只需加一行数据；`t.Run` 让每个用例独立报告，可按 `TestDivide/除数为零` 单独执行。
- `t.Helper()` 标记辅助断言函数，失败时报告调用处行号而非辅助函数内部。
- 浮点数用 `math.Abs(got-want) > 1e-9` 判断，不要用 `==`。
- Go 1.22 起循环变量每次迭代复制，子测试闭包捕获 `tt` 不再有共享陷阱。

### 3. 覆盖率

```bash
go test -cover ./...                       # 每个包的语句覆盖率
go test -coverprofile=coverage.out ./...   # 生成数据
go tool cover -func=coverage.out           # 按函数查看
go tool cover -html=coverage.out           # 浏览器可视化
```

覆盖率统计"语句是否被执行"，不代表逻辑正确：100% 覆盖仍可能漏掉边界与错误分支。实用目标是核心业务包 70%-85%，而不是全仓库 100%。

### 4. 基准测试与 benchmem

```go
func BenchmarkAdd(b *testing.B) {
	var total float64
	b.ResetTimer() // 排除准备数据耗时
	for i := 0; i < b.N; i++ {
		total = Add(total, float64(i%100))
	}
	benchSink = total // 防止编译器优化掉整个循环
}
```

```bash
go test -bench=. -benchmem ./calc
go test -bench=BenchmarkAdd -benchtime=3s ./calc
```

| 指标 | 含义 |
| --- | --- |
| `ns/op` | 每次操作平均耗时 |
| `B/op` | 每次操作分配字节数 |
| `allocs/op` | 每次操作分配次数 |

降低 `B/op` 与 `allocs/op` 能减少 GC 压力。基准对比必须在同一台机器、同一负载下进行。

### 5. 示例测试

`ExampleXxx` 既是文档也是测试，`// Output:` 会被逐行比对：

```go
func ExampleAdd() {
	fmt.Println(Add(2, 3))
	// Output: 5
}
```

输出必须完全一致（含空格与换行）；没有 `// Output:` 的示例只编译、不校验。示例函数名与标识符对应时会出现在 `go doc` 中。

### 6. 模糊测试

```go
func FuzzDivide(f *testing.F) {
	f.Add(1.0, 2.0) // 种子语料
	f.Fuzz(func(t *testing.T, a, b float64) {
		_, _ = Divide(a, b) // 只要求不 panic
	})
}
```

`go test -fuzz=FuzzDivide -fuzztime=10s ./calc` 会自动生成随机输入；崩溃输入写入 `testdata/fuzz/`，之后普通 `go test` 会将其作为回归用例。

### 7. httptest

测试 Handler 不需要真的监听端口：

```go
req := httptest.NewRequest(http.MethodPost, "/api/echo", strings.NewReader(`{"message":"hi"}`))
rec := httptest.NewRecorder()
NewHandler().ServeHTTP(rec, req)

if rec.Code != http.StatusOK { /* ... */ }
var body echoResponse
_ = json.NewDecoder(rec.Body).Decode(&body)
```

- `NewRecorder + NewRequest`：单元测试首选，最快，不经过网络。
- `httptest.NewServer`：需要真实 URL、测试客户端或流式响应时使用。
- `NewRequest` 不会校验方法与真实 Host，代理类场景需手动设置字段。

### 8. go vet / staticcheck / golangci-lint

| 工具 | 定位 | 使用 |
| --- | --- | --- |
| `go vet` | 官方静态检查：格式化串、锁复制、可疑循环 | `go vet ./...` |
| `staticcheck` | 更强的第三方静态分析 | `staticcheck ./...` |
| `golangci-lint` | 聚合多种 linter，统一配置与输出 | `golangci-lint run` |

`go vet` 随工具链提供，应纳入 CI 必跑项；第三方工具按团队需要引入，避免规则噪声。

### 9. Go Modules：tidy 与 vendor

```bash
go mod tidy                 # 补齐缺失、移除未使用依赖
go mod verify               # 校验本地依赖是否被篡改
go mod vendor               # 复制依赖到 vendor/
go build -mod=vendor ./...  # 只使用 vendor 中的依赖
```

- `go.sum` 记录校验和，必须提交，否则 CI 无法复现构建。
- `vendor/` 适合完全离线或需审计依赖源码的团队，代价是仓库体积变大。
- CI 可执行 `go mod tidy` 后检查 `git diff --exit-code`，防止漏整理依赖。

### 10. 构建标签与版本注入

构建标签必须位于文件顶部，与 `package` 之间空一行：

```go
//go:build linux && amd64

package main
```

`go build -tags=prod` 可显式启用标签，常用于区分平台实现或调试/生产配置。版本注入利用链接器参数：

```go
var version = "dev" // 可被 -ldflags 覆盖
```

```bash
go build -ldflags "-X main.version=1.2.0 -s -w" -o bin/server ./cmd/server
```

`-X` 只能修改**字符串类型的包级变量**；`-s -w` 去掉符号表与调试信息，可明显减小二进制。

### 11. 交叉编译

设置 `GOOS` 与 `GOARCH` 即可，不依赖目标平台的 C 工具链（前提 `CGO_ENABLED=0`）：

```bash
$env:CGO_ENABLED="0"; $env:GOOS="linux"; $env:GOARCH="amd64"; go build -o bin/server-linux ./cmd/server
go tool dist list      # 查看全部受支持的平台组合
```

常见目标：`linux/amd64`（服务器）、`linux/arm64`（云 ARM 实例）、`darwin/arm64`（Apple Silicon）、`windows/amd64`。纯静态二进制才能放入 `scratch` / `alpine` 最小镜像；依赖 cgo 时需要对应平台的交叉工具链。

### 12. pprof

```go
import _ "net/http/pprof"

go func() { _ = http.ListenAndServe("localhost:6060", nil) }()
```

```bash
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30   # CPU
go tool pprof http://localhost:6060/debug/pprof/heap                 # 堆内存
go tool pprof -http=:8081 cpu.out                                    # 可视化
```

常用命令：`top` 看热点、`list 函数名` 看逐行耗时、`web` 生成调用图。**pprof 端口只能监听 localhost 或加鉴权**，不要暴露公网。基准测试也可用 `-cpuprofile` 采集数据。

### 13. Docker 多阶段构建

```dockerfile
FROM golang:1.23-alpine AS builder
WORKDIR /src
ENV CGO_ENABLED=0 GOOS=linux
COPY go.mod ./
RUN go mod download
COPY . .
RUN go build -trimpath -ldflags="-s -w" -o /out/server ./cmd/server

FROM alpine:3.20
RUN apk add --no-cache ca-certificates \
    && addgroup -S app && adduser -S -g app app
COPY --from=builder /out/server /usr/local/bin/server
USER app
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/server"]
```

- 先 `COPY go.mod` 再 `download`，利用层缓存：依赖不变时不重复下载。
- `CGO_ENABLED=0` + 静态二进制，才能使用 `scratch` 或 `alpine`。
- `ca-certificates` 是调用 HTTPS 上游（如 LLM API）所必需的。
- **非 root 用户**降低容器逃逸风险；`.dockerignore` 排除 `bin/`、`.git/`。
- alpine 镜像可控制在 10-20MB；用 `docker images` 与 `docker history` 检查层大小。

### 14. Makefile

```make
BIN := bin/server
build:
	go build -trimpath -ldflags="-s -w" -o $(BIN) ./cmd/server
test:
	go test ./...
```

命令行必须以 **Tab** 开头（空格会报 `missing separator`）；`.PHONY` 声明伪目标。Windows 默认没有 `make`，可安装 Chocolatey 的 make 或用 Git Bash，也可直接复制目标里的 `go` 命令执行。

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/go.mod` | 模块 `eshop/engineering`，Go 1.22，无第三方依赖 |
| `Code/calc/calculator.go` | `Add` / `Subtract` / `Divide`（除零返回 error）/ `Average`（空切片返回 error） |
| `Code/calc/calculator_test.go` | 表驱动、`t.Run`、`t.Helper`、`ExampleAdd` |
| `Code/calc/benchmark_test.go` | `BenchmarkAdd`、`BenchmarkAverage`，含 `b.ResetTimer` |
| `Code/httpdemo/server.go` | `NewHandler()`，`GET /healthz` 与 `POST /api/echo`，方法错误返回 405 |
| `Code/httpdemo/server_test.go` | `httptest` 覆盖健康检查、回显、非法 JSON、错误方法、404 |
| `Code/cmd/server/main.go` | 读取 `PORT`（默认 8080）、超时配置与优雅关闭 |
| `Code/Dockerfile` | 多阶段构建，非 root 运行 |
| `Code/Makefile` | `build/test/bench/lint/docker/run/clean` 等目标 |
| `Code/README.md` | 工程化操作指南（测试、lint、构建、Docker、常见问题） |

在 `Code` 目录内执行：

```bash
cd "Day12 - 测试、工程化与部署/Code"

go test ./...                          # 全部测试
go test -v ./calc                      # 查看子测试
go test -bench=. -benchmem ./calc      # 基准测试
go test -cover ./...                   # 覆盖率
go test -race ./...                    # 竞争检测

go run ./cmd/server                    # 默认 :8080
$env:PORT="9090"; go run ./cmd/server  # 指定端口

docker build -t eshop-api:dev .
docker run --rm -p 8080:8080 eshop-api:dev
```

接口验证：

```bash
curl.exe -i http://localhost:8080/healthz
curl.exe -i -X POST http://localhost:8080/api/echo -H "Content-Type: application/json" -d "{\"message\":\"你好，Go\"}"
curl.exe -i http://localhost:8080/api/echo     # 405
```

## 关键知识点总结

1. **测试三约定**：`*_test.go`、`TestXxx(t *testing.T)`、与被测包同目录。
2. **表驱动 + 子测试**：数据与逻辑分离，`t.Run` 提供独立报告与筛选能力。
3. **`t.Helper`**：让断言失败指向调用处，是自定义断言函数的标准写法。
4. **浮点断言**：用差值小于 epsilon，不使用 `==`。
5. **覆盖率**：衡量"执行到"而非"正确性"，核心包 70%-85% 是务实目标。
6. **基准测试**：`b.N` 由框架调整，`b.ResetTimer` 排除准备阶段，`benchSink` 防止优化。
7. **示例与模糊**：`// Output:` 逐字匹配；`f.Add` 提供种子，崩溃输入自动归档。
8. **`httptest`**：`NewRecorder` 直接测 Handler，`NewServer` 适合真实 URL 场景。
9. **静态检查**：`go vet` 必跑，`staticcheck` / `golangci-lint` 按需引入。
10. **可重复构建**：提交 `go.sum`，CI 校验 `go mod tidy` 是否产生 diff。
11. **构建与部署**：`-X` 注入版本、`CGO_ENABLED=0` 交叉编译、多阶段 Docker + 非 root 运行。

## 实战练习

### 练习 1：补全计算器测试

为 `Add` / `Subtract` 增加 `NaN`、极大值、正负零用例；把 `TestDivide` 改成表驱动并补充 `0/0`；再写一个 `ExampleAverage`，输出保留两位小数（`fmt.Printf("%.2f\n", ...)`）。

### 练习 2：为商品接口写 httptest 测试

新建 `httpdemo/product_test.go`，定义 `POST /api/products` 与 `GET /api/products`（内存切片即可），用 `httptest` 覆盖创建成功（201）、空名称（400）、非法 JSON（400）、错误方法（405），并断言 `Content-Type` 与响应字段。最后运行 `go test -race ./...` 确认无数据竞争。

### 练习 3：基准对比与优化

为 `Average` 实现两个版本（循环累加 / 先复制再计算），用 `go test -bench=. -benchmem -benchtime=3s ./calc` 比较 `B/op`；再为 `Divide` 增加 `BenchmarkDivide`，观察 `ns/op` 与误差范围。

### 练习 4：构建与部署流水线

1. `make build` 生成 `bin/server`（Windows 为 `server.exe`），记录文件大小。
2. 添加构建标签文件 `version_debug.go`，`-tags=debug` 时打印额外调试信息。
3. `docker build -t eshop-api:dev .` 后用 `docker images` 观察体积；再改用 `scratch` 基础镜像，验证 HTTPS 请求是否仍可用。
4. `docker run --rm -e PORT=9090 -p 9090:9090 eshop-api:dev` 启动并验证 `/healthz`，最后 `docker stop` 观察优雅关闭日志。