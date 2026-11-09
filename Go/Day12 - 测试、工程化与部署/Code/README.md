# Day12/Code - 工程化操作指南

本目录是一个可直接运行的 Go 模块 `eshop/engineering`，包含可测试的计算包、HTTP 示例服务、Dockerfile 与 Makefile。本文件给出从测试、检查、构建到容器化的完整操作步骤与常见问题。

## 一、目录结构

```
Code/
├── go.mod                    ← module eshop/engineering，go 1.22
├── calc/
│   ├── calculator.go         ← Add / Subtract / Divide / Average
│   ├── calculator_test.go    ← 表驱动测试、子测试、示例测试
│   └── benchmark_test.go     ← 基准测试
├── httpdemo/
│   ├── server.go             ← NewHandler()：/healthz、/api/echo
│   └── server_test.go        ← httptest 单元测试
├── cmd/server/main.go        ← 服务入口：PORT、超时、优雅关闭
├── Dockerfile                ← 多阶段构建
├── Makefile                  ← 常用命令封装
└── README.md                 ← 本文件
```

## 二、测试

在 `Code` 目录执行：

```bash
go test ./...                          # 全部测试
go test -v ./calc                      # 输出子测试名称
go test -run 'TestDivide/除数为零' ./calc
go test -count=1 ./...                 # 禁用缓存，强制重跑
go test -race ./...                    # 数据竞争检测
```

覆盖率：

```bash
go test -cover ./...
go test -coverprofile=coverage.out ./...
go tool cover -func=coverage.out
go tool cover -html=coverage.out       # 生成 HTML 并在浏览器打开
```

基准测试：

```bash
go test -bench=. -benchmem ./calc
go test -bench=BenchmarkAdd -benchtime=3s ./calc
```

只跑某一个基准并对比分配情况时，可把结果重定向到文件后用 `benchstat`（需额外安装）比较。

模糊测试（本项目未内置 Fuzz，可按 README 练习添加）：

```bash
go test -fuzz=FuzzDivide -fuzztime=10s ./calc
```

## 三、静态检查与格式化

```bash
gofmt -l .            # 列出未格式化的文件
gofmt -w .            # 直接格式化
go vet ./...          # 官方静态检查，CI 必跑
```

可选安装更强的检查工具：

```bash
go install honnef.co/go/tools/cmd/staticcheck@latest
staticcheck ./...

# golangci-lint 见 https://golangci-lint.run/usage/install/
golangci-lint run
```

> `gofmt -l` 有输出就说明风格不一致；提交前应保证输出为空。

## 四、构建与运行

```bash
# 直接运行（默认 :8080）
go run ./cmd/server

# 指定端口（PowerShell）
$env:PORT="9090"; go run ./cmd/server

# 构建
go build -trimpath -ldflags="-s -w" -o bin/server ./cmd/server
```

产物在 `bin/server`（Windows 为 `bin/server.exe`）。版本注入示例：

```bash
go build -ldflags "-X main.version=1.0.0 -s -w" -o bin/server ./cmd/server
```

前提是 `cmd/server/main.go` 中定义了可导出的字符串变量 `version`；本项目未定义，仅作命令示范。

交叉编译：

```bash
$env:CGO_ENABLED="0"; $env:GOOS="linux"; $env:GOARCH="amd64"; go build -o bin/server-linux ./cmd/server
go tool dist list    # 查看支持的目标平台
```

## 五、Docker

```bash
docker build -t eshop-api:dev .
docker run --rm -p 8080:8080 eshop-api:dev
docker run --rm -e PORT=9090 -p 9090:9090 eshop-api:dev
docker stop <container-id>       # 观察优雅关闭日志
```

镜像特点：

- 构建阶段使用 `golang:1.23-alpine`，运行阶段仅保留静态二进制。
- `CGO_ENABLED=0` + `-trimpath -ldflags="-s -w"`，体积小且路径可复现。
- 运行时为非 root 用户 `app`，并安装了 `ca-certificates` 以支持 HTTPS。
- 未使用 `scratch` 是因为示例需要 CA 证书；若上游均为内网 HTTP，可换成 `scratch` 进一步瘦身。

检查镜像：

```bash
docker images eshop-api:dev
docker history eshop-api:dev
docker run --rm eshop-api:dev --help   # 若程序不支持参数，会直接启动，可忽略
```

> `.dockerignore` 建议包含 `.git`、`bin`、`coverage.out`，避免把构建产物与历史记录打进上下文。

## 六、Makefile

```bash
make build      # 构建到 bin/
make test       # go test ./...
make bench      # 基准测试
make cover      # 覆盖率
make lint       # go vet ./...
make docker     # 构建镜像，可覆盖 IMAGE
make run        # go run ./cmd/server
make tidy       # go mod tidy
make clean      # go clean
```

自定义镜像标签：

```bash
make docker IMAGE=eshop-api:1.0.0
```

Windows 说明：

- 原生 PowerShell 没有 `make`，可安装 Chocolatey 的 `make`、使用 Git Bash，或直接复制目标中的命令执行。
- Makefile 中构建目标已通过 `go env GOOS` 自动补 `.exe` 后缀。
- 命令行缩进必须是 **Tab**，从网页复制时容易变成空格，可用编辑器显示不可见字符检查。

## 七、常见问题

**1. `go: cannot find main module`**
当前目录不在模块内。先 `cd "Day12 - 测试、工程化与部署/Code"`，确认能看到 `go.mod`。

**2. `package eshop/engineering/httpdemo is not in std`**
`cmd/server/main.go` 的导入路径必须与 `go.mod` 的 `module` 完全一致；修改模块名后需同步更新导入。

**3. `go test` 显示 `(cached)`**
结果来自缓存。用 `go test -count=1 ./...` 强制重跑；修改测试或源码后缓存会自动失效。

**4. Windows 下 `make` 报 `missing separator`**
命令行的缩进不是 Tab。用支持显示空白的编辑器把缩进改为 Tab。

**5. `docker build` 很慢**
首次拉取基础镜像较慢属正常；后续依赖未变时会命中 `COPY go.mod` + `RUN go mod download` 的层缓存。国内可配置镜像加速器。

**6. 容器启动后立刻退出**
检查 `PORT` 是否被占用、`docker logs <container>` 是否提示 `address already in use`；容器内端口需与 `-p` 映射一致。

**7. 覆盖率报告找不到文件**
`-coverprofile` 生成在当前工作目录，`go tool cover -html` 的相对路径要与之一致。

**8. `-X` 注入版本不生效**
确认变量是**包级字符串**、包路径写法正确（`main.version` 或 `完整模块路径/pkg.version`），且没有被常量替代。