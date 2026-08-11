# Day01 Code - 环境搭建指南

本目录包含 Day01「LangChain 概述与环境搭建」的全部代码文件，帮助你从零完成 LangChain 开发环境搭建，并运行第一个程序。

## 文件清单

| 文件 | 用途 | 是否需要 API Key |
|------|------|-----------------|
| `01_hello_langchain.py` | 第一个 LangChain 程序，含四种调用方式对比 | ✅ 需要 OPENAI_API_KEY |
| `02_environment_setup.py` | 环境检查工具，生成配置模板 | ❌ 不需要 |
| `03_project_structure.py` | ChainQA 项目脚手架生成器 | ❌ 不需要 |

---

## 详细安装步骤

### 步骤 1：确认 Python 版本

```bash
python --version
# 要求 Python 3.10+，推荐 3.11 或 3.12
```

若版本低于 3.10，请前往 [python.org](https://www.python.org/downloads/) 下载安装。

### 步骤 2：创建虚拟环境

```bash
# 在 LangChain 板块根目录执行
python -m venv .venv

# 激活虚拟环境
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Windows CMD
.venv\Scripts\activate.bat
# Linux/macOS
source .venv/bin/activate
```

### 步骤 3：安装核心依赖

```bash
# 核心依赖（必装）
pip install langchain langchain-openai langchain-community python-dotenv pydantic

# 可选依赖
pip install langchain-anthropic       # Claude 模型支持
pip install openai                     # 直接调用 OpenAI SDK（对比用）
```

### 步骤 4：配置 API Key

在 `LangChain/` 目录下创建 `.env` 文件：

```bash
# OpenAI（必填）
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Anthropic（可选）
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
```

> 也可运行 `python 02_environment_setup.py` 自动生成 `.env.template` 模板文件。

### 步骤 5：运行代码

```bash
# 进入本目录
cd "Day01 - LangChain概述与环境搭建/Code"

# 1. 运行环境检查（推荐首先运行）
python 02_environment_setup.py

# 2. 运行第一个 LangChain 程序
python 01_hello_langchain.py

# 3. 生成 ChainQA 项目脚手架
python 03_project_structure.py
```

---

## 常见问题排查

### 问题 1：`ModuleNotFoundError: No module named 'langchain'`

**原因**：未安装 langchain 或未激活虚拟环境。

**解决**：
```bash
# 确认虚拟环境已激活
.venv\Scripts\activate      # Windows
source .venv/bin/activate    # Linux/macOS

# 重新安装
pip install langchain langchain-openai langchain-community
```

### 问题 2：`AuthenticationError: Invalid API Key`

**原因**：`.env` 文件中的 API Key 无效或未加载。

**解决**：
1. 检查 `.env` 文件是否在项目根目录（`LangChain/` 下）
2. 检查 Key 格式是否正确（OpenAI 以 `sk-` 开头）
3. 确认代码中调用了 `load_dotenv()`

### 问题 3：`RateLimitError: Rate limit reached`

**原因**：API 调用频率超过限制。

**解决**：
- 降低调用频率
- 在 [OpenAI 后台](https://platform.openai.com/account/billing) 检查额度
- 使用 `.with_retry()` 配置重试（Day02 详讲）

### 问题 4：Windows PowerShell 执行策略报错

**原因**：PowerShell 默认禁止运行脚本。

**解决**：
```powershell
# 以管理员身份运行 PowerShell，执行
Set-ExecutionPolicy -ExecutionPolicy RemoteSignIn -Scope CurrentUser
```

### 问题 5：代理/网络问题

**原因**：国内访问 OpenAI API 需要代理。

**解决**：
- 配置 HTTP 代理环境变量
- 或使用兼容 OpenAI 接口的国内模型服务（如通义千问、智谱）
- 或使用本地 Ollama 模型（Day02 详讲）

---

## IDE 配置建议

### VS Code 推荐配置

1. 安装扩展：
   - Python（Microsoft 官方）
   - Pylance（类型检查）
   - Jupyter（可选，便于交互式调试）

2. 配置 Python 解释器：
   - 按 `Ctrl+Shift+P` → 输入 `Python: Select Interpreter`
   - 选择 `.venv` 中的 Python

3. `.vscode/settings.json` 推荐配置：
   ```json
   {
     "python.defaultInterpreterPath": ".venv\\Scripts\\python.exe",
     "python.terminal.activateEnvironment": true,
     "python.analysis.typeCheckingMode": "basic"
   }
   ```

### PyCharm 推荐配置

1. 打开项目 → File → Settings → Project → Python Interpreter
2. 选择 `.venv` 中的解释器
3. 安装 `.env` 支持插件：EnvFile

---

## 依赖版本兼容性说明

| 包名 | 最低版本 | 推荐版本 | 说明 |
|------|---------|---------|------|
| Python | 3.10 | 3.11+ | LCEL 需要类型注解支持 |
| langchain | 0.3.0 | 最新 0.3.x | 本手册基于 0.3 编写 |
| langchain-core | 0.3.0 | 最新 0.3.x | 核心 Runnable/Prompt/Parser |
| langchain-openai | 0.2.0 | 最新 0.2.x | OpenAI 集成 |
| langchain-community | 0.3.0 | 最新 0.3.x | 第三方集成 |
| python-dotenv | 1.0.0 | 1.0+ | .env 加载 |
| pydantic | 2.0.0 | 2.x | 结构化输出（Day04） |

> **注意**：LangChain 0.3 与 0.1/0.2 存在 Breaking Change，Legacy Chains（如 LLMChain）已废弃。本手册全部使用 LCEL 语法。

---

## 项目结构说明

运行 `03_project_structure.py` 后生成的 ChainQA 项目结构：

```
chainqa/
├── pyproject.toml          # 项目配置与依赖
├── .gitignore              # Git 忽略规则
├── .env.template           # 环境变量模板
├── README.md               # 项目说明
├── src/
│   └── chainqa/
│       ├── __init__.py     # 包入口
│       ├── config.py        # 配置管理
│       ├── models.py        # 模型实例
│       ├── prompts/         # Prompt 模板
│       ├── parsers/         # 输出解析器
│       ├── chains/          # 链式调用
│       ├── memory/          # 对话记忆
│       ├── loaders/         # 文档加载
│       ├── retrieval/       # 检索器
│       ├── tools/           # 工具定义
│       └── server/          # API 服务
├── tests/                  # 测试目录
└── data/                   # 数据目录
```

**目录职责说明**：

| 目录 | 对应天数 | 职责 |
|------|---------|------|
| `prompts/` | Day03 | 管理 Prompt 模板 |
| `parsers/` | Day04 | 输出解析器 |
| `chains/` | Day05 | LCEL 链式调用 |
| `memory/` | Day06 | 对话记忆管理 |
| `loaders/` | Day07 | 文档加载 |
| `retrieval/` | Day08 | 向量检索 |
| `tools/` | Day09 | 工具定义 |
| `server/` | Day11 | LangServe API |

---

## 运行验证清单

完成环境搭建后，确认以下各项通过：

- [ ] `python --version` 显示 3.10+
- [ ] `pip list` 能看到 langchain、langchain-openai 等
- [ ] `.env` 文件已创建且填入有效 API Key
- [ ] `python 02_environment_setup.py` 显示「环境检查通过」
- [ ] `python 01_hello_langchain.py` 能正常返回 LLM 回复
- [ ] `python 03_project_structure.py` 成功生成 chainqa 目录

---

> 环境搭建完成后，进入 Day02 学习 Model I/O 模型接口层。
