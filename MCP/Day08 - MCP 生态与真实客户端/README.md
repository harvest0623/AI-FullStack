# Day08 - MCP 生态与真实客户端

> 从「自己写的代码」走向「真实世界」：认识官方参考 Server、了解如何在 Claude Desktop / Cline / VS Code 等真实客户端接入你的 Server，并掌握调试手段。

---

## 1. 生态图景

MCP 生态由几类构成：

- **官方参考 Server**（modelcontextprotocol/servers）：filesystem、github、sqlite、fetch 等
- **各框架适配**：LangChain、LlamaIndex、OpenAI/Anthropic 工具调用均可转 MCP
- **真实客户端 Host**：Claude Desktop、Cline、Cursor、VS Code、自研应用……

```
官方/社区 Server ──┬── filesystem（文件系统）
                  ├── github（GitHub 操作）
                  ├── sqlite（数据库）
                  ├── fetch（网页抓取）
                  └── ...（生态持续扩展）
                         │  统一 MCP 协议
  真实客户端 Host ────────┤
   ├── Claude Desktop / Cline / Cursor / VS Code ...
   └── 自研应用（用 Client SDK）
```

---

## 2. 常用官方参考 Server

| Server | 能力 | 场景 |
|--------|------|------|
| `filesystem` | 读写文件系统 | 本地文件操作 |
| `github` | GitHub Repo/Issue/PR | 代码协作 |
| `sqlite` | SQLite 查询操作 | 数据探查 |
| `fetch` | 抓取网页转 Markdown | 网页内容 |
| `memory` | 长期记忆存储 | Agent 记忆 |

> 这些是**参考实现**，也是学习 Server 写法的好样本：`github.com/modelcontextprotocol/servers`。

---

## 3. 把 Server 接入真实客户端

绝大多数客户端的接入方式都是**在配置里声明「命令 + 参数」**。以 JSON 形配置为例（Cline、Cursor 等采用类似结构）：

```json
{
  "mcpServers": {
    "my-docs": {
      "command": "python",
      "args": ["路径/server_resources.py"],
      "env": {}
    }
  }
}
```

- `command` + `args` 定义如何以 stdio 启动你的 Server
- 每个 `mcpServers` 下的键，就是一个 Server 名称
- 客户端启动时会把它们作为子进程拉起并连上

**Claude Desktop** 通常在 `claude_desktop_config.json` 中写类似配置；
**Cline / Cursor** 在应用的 MCP 设置界面里新增「Command + Args」。

---

## 4. 调试手段

官方 CLI `mcp` 提供两个利器：

- **`mcp dev <server.py>`**：启动一个内置测试客户端（Inspector），可视化查看工具/资源/提示词，并直接调用调试
- **`uv run mcp dev ...`**：配合 uv 自动管理依赖

```bash
uv run mcp dev server_resources.py
```

效果：浏览器打开调试面板 → 左侧列工具/资源/提示词 → 右侧调用看返回与日志。

---

## 5. 本节小结

- 生态 = 官方/社区 Server + 框架适配 + 真实客户端
- 参考 Server（filesystem/github/sqlite/fetch/memory）是学习范本
- 接入真实客户端 = 在 `mcpServers` 配置里声明 `command` + `args`
- 调试用 `mcp dev` / Inspector

---

## 代码说明

进入 `Code/` 目录：

| 文件 | 作用 |
|------|------|
| `01_ecosystem.py` | 生态图景与参考 Server（离线） |
| `02_config.py` | 客户端接入配置讲解与模板（离线） |
| `03_debug.py` | mcp dev / Inspector 调试流程（离线） |
| `README.md` | 本目录说明 |

均**离线可运行**。