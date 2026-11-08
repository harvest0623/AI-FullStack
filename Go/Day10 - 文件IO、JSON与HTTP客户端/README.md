# Day10 - 文件 IO、JSON 与 HTTP 客户端

## 本章简介

服务端程序离开语言语法之后，绝大部分工作都在和"外部世界"打交道：从文件读取配置与种子数据，把结构化数据编码成 JSON 返回给前端，通过 HTTP 客户端调用上游模型服务。Go 把这些能力统一收敛到几个极简接口上——`io.Reader`、`io.Writer` 和 `encoding/json`，再用 `net/http` 把网络 IO 变成同一套抽象的延伸。

在 eshop-gateway 中，这一天的知识会直接落到三个位置：启动时读取 `products.json` 种子数据，处理请求时解析前端传来的 JSON 并序列化响应，生成导购文案时以带超时的 HTTP 客户端调用上游 LLM。任何一处处理不当，都可能造成文件句柄泄漏、响应体未关闭导致连接耗尽，或者请求无限期挂起。

本章先讲清 `io.Reader` / `io.Writer` 的组合哲学，再依次覆盖文件操作、JSON 编解码与 HTTP 客户端的超时控制。所有示例只依赖标准库，HTTP 示例使用 `httptest` 启动本地假上游，不需要联网即可运行。

## 学习目标

- 理解 `io.Reader` / `io.Writer` 两个单方法接口的设计与解耦价值
- 掌握 `os.ReadFile` / `os.WriteFile` 与 `os.Open` / `os.Create` 的使用场景
- 理解文件权限位（`0644`、`0600`、`0755`）与 `defer Close` 的必要性
- 用 `bufio.Scanner` 逐行读取大文件，并处理 `scanner.Err()`
- 用 `os.MkdirTemp` / `os.RemoveAll` 安全管理临时文件
- 掌握结构体 JSON 标签、`Marshal` / `Unmarshal`、`MarshalIndent`
- 理解 `omitempty` 的零值规则与导出字段限制
- 用 `json.Decoder` / `json.Encoder` 处理流式与多对象 JSON
- 掌握 `http.Client` 的 `Timeout` 与 `context` 超时控制
- 正确检查状态码、关闭并读完 `resp.Body`
- 用 `httptest.NewServer` 构建离线可测的假上游
- 用 `io.Copy`、`TeeReader`、`LimitReader` 组合 IO 处理链路

## 理论知识讲解

### 1. io.Reader / io.Writer：统一的 IO 抽象

Go 的 IO 体系建立在一个极其精简的约定上：

```go
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}
```

任何类型，只要实现 `Read` 或 `Write`，就能接入整个标准库生态。文件、网络连接、字符串、内存缓冲区、压缩流、加密流都遵循同一套接口，因此可以像搭积木一样组合：

```
数据源                 中间层                    目的地
strings.Reader ──▶ bufio.Scanner ──▶ 业务解析
os.File        ──▶ io.TeeReader ──▶ bytes.Buffer（审计副本）
http.Response  ──▶ io.LimitReader ──▶ json.Decoder
bytes.Buffer   ──▶ gzip.Writer   ──▶ os.File
```

| 类型 | 实现 | 典型用途 |
|------|------|---------|
| `*os.File` | Reader + Writer | 文件读写 |
| `*bytes.Buffer` | Reader + Writer | 内存缓冲、测试 |
| `*strings.Reader` | Reader | 把字符串当数据源 |
| `*bufio.Reader/Writer` | Reader / Writer | 带缓冲的读写，减少系统调用 |
| `*http.Response.Body` | Reader + Closer | 读取 HTTP 响应体 |
| `io.Pipe` | Reader + Writer | 连接生产者和消费者 |

`io` 包还提供了一批组合函数：`io.Copy` 负责搬运，`io.TeeReader` 边读边复制，`io.LimitReader` 限制读取上限，`io.MultiWriter` 把一次写入广播到多个目标。掌握它们能省掉大量手写循环。

### 2. 文件操作

**一次性读写**适合小文件、配置和种子数据：

```go
data, err := os.ReadFile("products.json")
if err != nil {
    return fmt.Errorf("读取商品数据: %w", err)
}

if err := os.WriteFile("cache.txt", data, 0o644); err != nil {
    return fmt.Errorf("写入缓存: %w", err)
}
```

**流式读取**适合大文件：`os.Open` 返回 `*os.File`，配合 `bufio.Scanner` 逐行处理，内存占用与文件大小无关：

```go
f, err := os.Open("products.csv")
if err != nil {
    return err
}
defer f.Close()

scanner := bufio.NewScanner(f)
for scanner.Scan() {
    line := scanner.Text()
    // 处理每一行
}
if err := scanner.Err(); err != nil { // 不能忽略扫描错误
    return err
}
```

`Scanner` 单行默认上限为 64KB，超长行需要用 `scanner.Buffer(buf, maxSize)` 扩大缓冲。

**文件权限**以八进制表示，遵循 Unix 语义（Windows 上部分位不生效）：

| 权限 | 含义 | 适用场景 |
|------|------|---------|
| `0644` | 属主读写，其他只读 | 普通数据文件、种子 JSON |
| `0600` | 仅属主读写 | 密钥、令牌、用户隐私数据 |
| `0755` | 属主读写执行，其他读执行 | 目录、可执行脚本 |
| `0777` | 所有人可读写执行 | 不建议在生产使用 |

`os.Create` 等价于 `OpenFile(name, O_RDWR|O_CREATE|O_TRUNC, 0666)`，会截断已有内容；追加写入应使用 `os.OpenFile(name, os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0o644)`。

**临时文件**用 `os.MkdirTemp` 创建独立目录，结束时 `defer os.RemoveAll(dir)` 清理，避免污染工作目录：

```go
dir, err := os.MkdirTemp("", "eshop-*")
if err != nil {
    return err
}
defer os.RemoveAll(dir)
```

### 3. 资源释放与错误处理

文件句柄、HTTP 响应体、数据库连接都属于有限资源，必须显式释放：

- 打开后立即 `defer f.Close()`，保证异常路径也能关闭
- 只读文件的 `Close` 错误通常可以忽略；**写入文件**的 `Close` 错误必须检查，因为缓冲数据可能在关闭时才落盘
- `os.IsNotExist(err)` 或 `errors.Is(err, os.ErrNotExist)` 用于区分"文件不存在"与"权限不足/磁盘错误"
- 返回错误时用 `%w` 包装上下文，调用方仍可用 `errors.Is` / `errors.As` 判断根因

```go
if _, err := os.ReadFile(path); err != nil {
    if errors.Is(err, os.ErrNotExist) {
        return defaultConfig(), nil // 首次启动，使用默认配置
    }
    return nil, fmt.Errorf("读取配置 %s: %w", path, err)
}
```

### 4. JSON 编解码

Go 的 `encoding/json` 通过结构体标签映射字段名，只有**导出字段**（首字母大写）才会参与编解码：

```go
type Product struct {
    ID       string   `json:"id"`
    Name     string   `json:"name"`
    Price    float64  `json:"price"`
    Tags     []string `json:"tags,omitempty"`
    Discount float64  `json:"discount,omitempty"`
}
```

常用 API：

| API | 用途 |
|-----|------|
| `json.Marshal(v)` | 结构体 → 紧凑 JSON 字节 |
| `json.MarshalIndent(v, "", "  ")` | 结构体 → 带缩进的可读 JSON |
| `json.Unmarshal(data, &v)` | JSON 字节 → 结构体 |
| `json.NewDecoder(r).Decode(&v)` | 从流中解码一个 JSON 值 |
| `json.NewEncoder(w).Encode(v)` | 编码并写入流，自动追加换行 |

关键细节：

- `omitempty` 会省略零值字段（`0`、`""`、`nil`、空切片/Map），但**不会**省略未加标签的 `0`
- JSON 数字默认解码为 `float64`，大整数会丢精度；需要精确金额时使用 `json.Number` 或整数字段（以分为单位）
- 未知字段默认被忽略；严格模式可调用 `dec.DisallowUnknownFields()`
- 编码时默认转义 `<`、`>`、`&`，嵌入 HTML 的场景可用 `enc.SetEscapeHTML(false)` 关闭
- 多个 JSON 对象连续排列（NDJSON）时，用 `for dec.More()` 循环解码，而不是一次性 `Unmarshal`

### 5. HTTP 客户端

`net/http` 的客户端核心是三步：构造请求、执行请求、处理响应。

```go
client := &http.Client{Timeout: 5 * time.Second}

req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
if err != nil {
    return err
}
req.Header.Set("Content-Type", "application/json")

resp, err := client.Do(req)
if err != nil {
    return fmt.Errorf("调用上游: %w", err)
}
defer resp.Body.Close()

if resp.StatusCode != http.StatusOK {
    msg, _ := io.ReadAll(io.LimitReader(resp.Body, 4<<10))
    return fmt.Errorf("上游状态码 %d: %s", resp.StatusCode, msg)
}
```

必须注意的工程细节：

| 问题 | 正确做法 |
|------|---------|
| 请求无限期挂起 | 设置 `Client.Timeout`，并用 `context` 控制单次请求预算 |
| 连接无法复用 | 读完并关闭 `resp.Body`，小响应可用 `io.Copy(io.Discard, resp.Body)` |
| 上游返回超大响应 | 用 `io.LimitReader` 限制读取字节数 |
| 把 4xx/5xx 当成成功 | 显式检查 `StatusCode`，解析统一错误结构 |
| 使用 `http.DefaultClient` | 它没有超时，生产环境应创建带超时的独立 Client |
| 错误信息丢失 | 用 `%w` 包装，保留底层错误类型 |

`http.Client` 可以安全地被多个 goroutine 并发使用，应该复用同一个实例，而不是每次请求都新建。底层 `Transport` 会维护连接池。

### 6. 超时、重试与可测试性

超时应该分层设置：客户端总超时、单次请求 `context` 超时、上游服务自身的处理超时。网关的总预算要略大于下游各步骤之和，否则会出现"客户端已放弃、服务端还在算"的浪费。

重试只适用于**幂等**请求（GET、带幂等键的写入），并且要满足：

- 限制最大次数（如 3 次），使用指数退避 + 抖动
- 只重试网络错误、429、502、503、504，不重试 400、401、403
- 每次重试都重新检查 `ctx.Err()`，避免整体预算耗尽后继续等待

可测试性方面，`httptest.NewServer` 能在进程内启动一个真实 HTTP 服务，返回其 `URL` 供客户端访问。这样可以覆盖成功、错误状态码、慢响应、非法 JSON 等分支，而完全不依赖外网。

### 7. io 组合技巧

| 组合 | 效果 |
|------|------|
| `io.Copy(dst, src)` | 把 Reader 全部写入 Writer，返回字节数 |
| `io.CopyN(dst, src, n)` | 只搬运前 n 字节 |
| `io.TeeReader(src, w)` | 读取时同步写入 w，适合审计与日志 |
| `io.LimitReader(src, n)` | 最多读取 n 字节，防止超大响应 |
| `io.MultiWriter(w1, w2)` | 一次写入广播到多个 Writer |
| `io.ReadAll(r)` | 读取全部内容，注意大小可控 |
| `io.WriteString(w, s)` | 向 Writer 写入字符串，避免手动转 `[]byte` |

自定义 `io.Writer` 也很简单：实现一个 `Write(p []byte) (int, error)` 方法即可，然后可以套在 `bytes.Buffer`、文件或网络连接外面，完成大写转换、计数、脱敏等处理。

### 8. 在 eshop-gateway 中的位置

| 场景 | 使用的 API | 注意点 |
|------|-----------|--------|
| 启动时加载商品种子数据 | `os.ReadFile` + `json.Unmarshal` | 文件缺失时使用默认数据，错误要包装 |
| 导出商品报表 | `os.WriteFile` / `bufio.Writer` | 权限 `0644`，写入后检查 Close |
| 解析前端请求 | `json.NewDecoder(r.Body)` | 限制 Body 大小，校验必填字段 |
| 返回统一 JSON | `json.NewEncoder(w).Encode` | 设置 `Content-Type`，错误结构一致 |
| 调用上游 LLM | `http.Client` + `NewRequestWithContext` | 超时、状态码、响应体关闭 |
| 记录上游原始响应 | `io.TeeReader` + 日志缓冲 | 注意脱敏与体积上限 |

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/file_io.go` | `os.WriteFile/ReadFile`、`os.Open` + `bufio.Scanner` 逐行读取、权限、临时目录与错误处理 |
| `Code/json_demo.go` | 结构体标签、`MarshalIndent`、`Unmarshal`、`omitempty`、`json.Decoder` 流式解析 |
| `Code/http_client.go` | `httptest` 假上游、GET/POST JSON、状态码检查、`Client.Timeout` 与 `context` 超时 |
| `Code/io_interfaces.go` | `strings.Reader`、`bytes.Buffer`、`io.Copy`、`TeeReader`、`LimitReader`、自定义 Writer |

执行方式（每个文件独立运行，均不需要联网）：

```bash
cd "Day10 - 文件IO、JSON与HTTP客户端/Code"
go run file_io.go
go run json_demo.go
go run http_client.go
go run io_interfaces.go
```

> 同一目录下多个文件都含 `main` 函数，不要执行 `go run .`，请按文件名单独运行。

## 关键知识点总结

1. **接口极简**：`io.Reader` / `io.Writer` 各只有一个方法，却能统一文件、网络、内存与压缩流。
2. **组合优于继承**：`TeeReader`、`LimitReader`、`MultiWriter` 通过包装 Reader/Writer 扩展能力。
3. **小文件一次性读写**：`os.ReadFile` / `os.WriteFile` 简洁，但大文件应使用流式处理。
4. **流式读取三件套**：`os.Open` + `defer Close` + `bufio.Scanner`，循环后必须检查 `scanner.Err()`。
5. **权限最小化**：普通数据 `0644`，敏感文件 `0600`，目录 `0755`，不要随手 `0777`。
6. **临时目录要清理**：`os.MkdirTemp` 配合 `defer os.RemoveAll`，避免残留文件。
7. **错误要带上下文**：用 `%w` 包装路径与操作，配合 `errors.Is(err, os.ErrNotExist)` 判断根因。
8. **JSON 只编码导出字段**：标签决定键名，`omitempty` 只省略零值，金额等精确数值避免用 `float64`。
9. **流式 JSON 用 Decoder**：`Decode` 适合大响应与 NDJSON，`for dec.More()` 可逐个处理对象。
10. **HTTP 客户端必须有超时**：不要直接用无超时的 `http.DefaultClient`，应复用带 `Timeout` 的实例。
11. **响应体必须关闭**：`defer resp.Body.Close()`，并读完内容以复用连接；错误响应也要读取并限制长度。
12. **httptest 让上游可测**：本地假服务能稳定覆盖成功、错误码、慢响应与非法 JSON，不依赖外网。

## 实战练习

### 练习 1：商品数据导入与报表导出

准备一个 `products.csv`（字段：id、name、price、stock），实现：

- 用 `bufio.Scanner` 逐行解析，跳过表头与格式错误的行，统计跳过的行号
- 解析失败时打印行号与原因，不中断整个文件
- 汇总总库存与总货值，按价格降序输出前 3 名
- 将结果写成 `report.json`（权限 `0644`），使用 `MarshalIndent` 保证可读
- 用 `os.MkdirTemp` 存放中间文件，结束后清理

### 练习 2：带超时与降级的上游 LLM 客户端

实现 `ChatClient`：

- 基于 `http.Client`，`Timeout` 设为 3 秒，复用同一实例
- 方法 `Chat(ctx, prompt)` 使用 `NewRequestWithContext`，POST JSON 到 `/v1/chat`
- 检查状态码，非 200 时读取最多 4KB 响应体并返回带状态码的错误
- 上游超时或 5xx 时，返回本地降级文案，而不是把错误直接抛给用户
- 用 `httptest.NewServer` 编写三个假上游：正常、返回 500、故意 sleep 200ms；再用 `context.WithTimeout(50ms)` 验证慢上游会被正确取消

### 练习 3：流式处理大 JSON 响应

构造一个包含 1000 个商品的 NDJSON 字符串（每行一个对象），要求：

- 用 `json.Decoder` 逐个解码，而不是 `ReadAll` 后整体 `Unmarshal`
- 用 `io.LimitReader` 限制最多读取 1MB，超出时返回明确错误
- 统计商品总数、平均价格、最贵商品名称
- 用 `io.TeeReader` 把原始字节同时写入一个 `bytes.Buffer`，模拟审计日志
- 思考：如果响应体是单个大数组而不是 NDJSON，应该如何流式解析？

### 练习 4：实现一个自定义 Writer

实现 `MaskWriter`，包装任意 `io.Writer`：

- 写入时把手机号中间四位替换为 `****`，再转发给底层 Writer
- 正确处理跨 `Write` 调用被截断的敏感字符串（提示：保留尾部缓冲）
- 用 `io.MultiWriter` 同时写入文件和 `bytes.Buffer`，验证两份内容一致
- 统计原始字节数与脱敏后字节数，解释为什么两者可能不同
