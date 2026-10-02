# Day03 - 核心原语：工具 / 资源 / 提示词

> MCP 对外暴露能力的三种标准原语。理解它们『各管什么、长什么样、何时用』，是你写 Server 的根基。

---

## 1. 三大原语总览

| 原语 | 作用 | 方向 | 类比 |
|------|------|------|------|
| **Tools（工具）** | 让模型『动手』——执行动作、产生副作用 | 主动调用 | 「手」 |
| **Resources（资源）** | 让模型『读』——获取上下文数据 | 读取内容 | 「眼睛/资料库」 |
| **Prompts（提示词）** | 复用的提示模板 | 获取模板 | 「模板库」 |

一句话记忆：
> **工具用来做事，资源用来读数据，提示词用来复用话术。**

---

## 2. Tools（工具）

模型通过工具**执行动作**，通常会产生副作用（写文件、发请求、操作数据库）。

### 结构

```json
{
  "name": "write_file",
  "description": "向指定路径写入文本内容",
  "inputSchema": {
    "type": "object",
    "properties": {
      "path": { "type": "string", "description": "文件路径" },
      "content": { "type": "string", "description": "要写入的内容" }
    },
    "required": ["path", "content"]
  }
}
```

### 关键特性
- **name**：唯一标识，供调用
- **inputSchema**：用 JSON Schema 描述参数，让模型知道怎么填
- **description**：让模型判断『何时该用这个工具』——写得越清楚越好
- 调用通过 `tools/call`，带 `arguments`
- **可以有副作用**，因此客户端通常要用户授权

### 适用场景
- 文件系统读写、执行代码、调外部 API、操作数据库、发送消息……

---

## 3. Resources（资源）

资源是被动态**结构化暴露的上下文数据**，通常为 URI 可寻址，保证为只读、粗粒度。

### 结构

```json
{
  "uri": "file:///project/config.json",
  "name": "项目配置",
  "description": "当前项目的配置文件",
  "mimeType": "application/json"
}
```

### 关键特性
- 通过 **URI** 引用（如 `file://`、`memory://`、`db://`）
- 通过 `resources/read` 读取 `contents`
- **只读**：模型读它，但不修改它（修改用工具）
- 支持订阅，内容变化可通知客户端

### 适用场景
- 项目文档、配置文件、数据库 schema、最近的消息、代码仓库结构……

> tools 是『动词』，resources 是『名词』——这个区分很重要。

---

## 4. Prompts（提示词）

提示词是可复用的模板，包含**文本 + 参数插槽**，被用于特定的交互模式。

### 结构

```json
{
  "name": "review_code",
  "description": "生成代码评审提示",
  "arguments": [
    { "name": "language", "description": "编程语言", "required": true }
  ]
}
```

用 `prompts/get` 获取，返回含 `messages`（角色 + 内容），并可含嵌入的资源引用。

### 关键特性
- 定义标准交互流程的入口（如『审查这段代码』『总结这份文档』）
- 参数在请求时填充
- 内容可作为上下文附加到会话

### 适用场景
- 代码评审、文档总结、Bug 分析、入职引导等固定流程

---

## 5. 如何选择

> 用一个简单判断：**需要改变外部世界吗？ → 工具。只需读吗？ → 资源。要复用一段固定话术/流程吗？ → 提示词。**

| 场景 | 用什么 |
|------|--------|
| 写文件、发消息、调 API | Tools |
| 读配置、读文档、查 schema | Resources |
| 生成固定流程的提示 | Prompts |

---

## 6. 本节小结

- **Tools**：动作接口，`name` + `inputSchema` + `description`，`tools/call` 调用
- **Resources**：只读数据，URI 寻址，`resources/read` 读取
- **Prompts**：可复用模板，参数化，`prompts/get` 获取
- 三者共同构成 Server 对外能力面，Client 通过能力发现拿到清单

---

## 代码说明

进入 `Code/` 目录：

| 文件 | 作用 |
|------|------|
| `01_three_primitives.py` | 三大原语总览与区别 |
| `02_tools.py` | 工具详解：结构、JSON Schema、调用 |
| `03_resources_prompts.py` | 资源与提示词的详解 |
| `README.md` | 本目录说明 |

所有脚本**离线可运行**。