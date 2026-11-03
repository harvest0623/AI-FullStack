# Day01/Code - Go 环境配置详细指南

本文件给出 Go 1.22+ 开发环境的完整搭建步骤，覆盖三平台安装、国内代理、模块初始化、IDE 配置与常见问题。

## 一、安装 Go

### 1. Windows

1. 访问 [go.dev/dl](https://go.dev/dl/)，下载 `go1.23.x.windows-amd64.msi`
2. 双击安装，默认路径为 `C:\Program Files\Go`
3. 安装器会自动把 `C:\Program Files\Go\bin` 写入 PATH
4. **关闭并重新打开终端**，执行验证：

```powershell
go version
go env GOPATH
```

若提示 `go 不是内部或外部命令`，手动把 `C:\Program Files\Go\bin` 加入系统环境变量 `Path`。

### 2. macOS

```bash
# 方式一：Homebrew（推荐）
brew install go

# 方式二：官方 pkg 安装包
# 从 go.dev/dl 下载 go1.23.x.darwin-arm64.pkg 并安装

go version
```

### 3. Linux

```bash
# 下载官方压缩包
wget https://go.dev/dl/go1.23.4.linux-amd64.tar.gz

# 解压到 /usr/local（会覆盖旧版本）
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go1.23.4.linux-amd64.tar.gz

# 配置 PATH（写入 ~/.bashrc 或 ~/.zshrc）
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc

go version
```

## 二、配置国内代理

Go Modules 默认从 `proxy.golang.org` 拉取依赖，国内网络经常超时。建议配置：

```bash
go env -w GOPROXY=https://goproxy.cn,direct
go env -w GOSUMDB=sum.golang.google.cn
go env -w GO111MODULE=on
```

验证：

```bash
go env GOPROXY
# https://goproxy.cn,direct
```

> `direct` 表示代理不可用时直连源站。企业内网可配置私有 Athens 或 Nexus 代理。

## 三、GOPATH 与模块缓存

```bash
go env GOPATH          # 默认：Windows C:\Users\<用户>\go，Linux/macOS ~/go
go env GOMODCACHE      # 依赖缓存目录，默认 $GOPATH/pkg/mod
go env GOCACHE         # 构建缓存目录
```

从 Go 1.16 起，**项目不再需要放在 GOPATH 下**。GOPATH 现在主要存放：

- `pkg/mod`：下载的依赖模块
- `bin`：`go install` 安装的可执行文件

清理缓存：

```bash
go clean -cache        # 清理构建缓存
go clean -modcache     # 清理依赖缓存（会重新下载）
```

## 四、初始化第一个模块

```bash
mkdir eshop-hello
cd eshop-hello

# 初始化模块，模块路径可自定义（发布到仓库时用仓库地址）
go mod init eshop/hello

# 查看 go.mod
cat go.mod
```

生成的 `go.mod`：

```
module eshop/hello

go 1.23
```

创建 `main.go` 并运行：

```bash
go run .
```

## 五、常用命令

| 命令 | 作用 |
|------|------|
| `go run .` | 运行当前包 |
| `go run main.go` | 运行单个文件 |
| `go build -o app .` | 编译为可执行文件 |
| `go build ./...` | 编译所有包（不产出文件） |
| `go install` | 安装到 `$GOPATH/bin` |
| `go mod init <path>` | 初始化模块 |
| `go get <pkg>@<ver>` | 添加/升级依赖 |
| `go mod tidy` | 清理并补齐依赖 |
| `go list -m all` | 查看依赖树 |
| `gofmt -w .` | 格式化 |
| `go vet ./...` | 静态检查 |
| `go test ./...` | 运行测试 |
| `go test -race ./...` | 数据竞争检测 |
| `go doc fmt.Println` | 查看文档 |
| `GOOS=linux GOARCH=amd64 go build` | 交叉编译 |

## 六、VS Code 配置

1. 安装扩展 **Go**（Go Team at Google 官方维护）
2. 首次打开 `.go` 文件时，VS Code 会提示安装工具（`gopls`、`dlv`、`staticcheck` 等），点击 **Install All**
3. 若安装失败，手动执行：

```bash
go install golang.org/x/tools/gopls@latest
go install github.com/go-delve/delve/cmd/dlv@latest
go install honnef.co/go/tools/cmd/staticcheck@latest
```

推荐设置（`settings.json`）：

```json
{
  "go.formatTool": "gofmt",
  "go.useLanguageServer": true,
  "editor.formatOnSave": true,
  "go.lintTool": "staticcheck",
  "go.testFlags": ["-v"]
}
```

调试：在 `main.go` 中按 `F5`，选择 `Go` 调试器，VS Code 会自动生成 `.vscode/launch.json`。

## 七、Go Playground

不想本地安装时，可使用官方在线环境：[go.dev/play](https://go.dev/play/)。

限制：
- 只支持标准库
- 无法访问网络与文件系统
- 适合验证语法与小段逻辑，不适合真实项目

## 八、常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `go: command not found` | PATH 未配置 | 将 Go 的 `bin` 目录加入 PATH 并重开终端 |
| `missing go.sum entry` | 依赖校验缺失 | 执行 `go mod tidy` |
| `dial tcp ... timeout` | 无法访问默认代理 | 配置 `GOPROXY=https://goproxy.cn,direct` |
| `declared and not used` | 声明了未使用的变量 | 删除变量或使用 `_` 忽略 |
| `imported and not used` | 导入了未使用的包 | 删除导入 |
| `cannot use x (type int) as type int64` | 无隐式类型转换 | 显式转换 `int64(x)` |
| `package main has multiple main functions` | 同目录多个 `main` | 按文件单独 `go run file.go`，不要 `go run .` |
| 拉取私有仓库失败 | 未配置 SSH / token | 配置 `GOPRIVATE` 与 Git 凭据 |

## 九、验证清单

完成配置后逐项确认：

```bash
go version                                   # 1.22+
go env GOPROXY                               # 已配置代理
cd "Day01 - Go语言入门与环境搭建/Code"
go run hello.go                              # Hello, Go!
go run env_check.go                          # 输出运行时信息
go run cli_args.go -name 张三 -count 3 -v     # 参数解析正常
gofmt -l .                                   # 无输出表示格式规范
go vet ./...                                 # 无报错
```
