# Day05 Code - Chains 链式调用与 LCEL 代码示例

本目录包含 Day05「Chains 链式调用与 LCEL」的全部可运行 Python 代码，围绕 ChainQA 智能问答助手逐步演示 LCEL 的核心用法。

## 文件说明

| 文件 | 内容 | 核心知识点 |
|------|------|-----------|
| `01_lcel_basics.py` | LCEL 基础语法 | `prompt \| model \| parser` 三步管道、invoke/batch/stream、类型传递、input/output Schema |
| `02_runnable_components.py` | Runnable 核心组件 | RunnablePassthrough / RunnableParallel / RunnableLambda / assign() |
| `03_chain_patterns.py` | 链式调用模式 | 顺序 / 并行 / 混合 / 条件分支 RunnableBranch / 动态路由 |
| `04_advanced_chains.py` | 复杂多步链 | 多步管道、链嵌套、with_retry / with_fallbacks、get_graph 可视化、ChainQA 综合链 |

## 运行方式

```bash
# 1. 确保已安装依赖
pip install langchain langchain-openai langchain-community python-dotenv pydantic

# 2. 在 LangChain 根目录创建 .env 文件
# OPENAI_API_KEY=sk-xxxxxxxx
# OPENAI_MODEL=gpt-4o-mini

# 3. 运行单个示例
cd "Day05 - Chains链式调用与LCEL/Code"
python 01_lcel_basics.py

# 4. 依次运行全部
python 01_lcel_basics.py
python 02_runnable_components.py
python 03_chain_patterns.py
python 04_advanced_chains.py
```

## LCEL 语法速查

### 基本管道
```python
chain = prompt | model | parser
chain.invoke({"question": "..."})
```

### Runnable 组件
```python
# 传递原始输入
RunnablePassthrough()

# 添加字段
RunnablePassthrough().assign(context=lambda x: retrieve(x["question"]))

# 并行执行
RunnableParallel({"a": chain_a, "b": chain_b})

# 包装函数
RunnableLambda(my_func)

# 条件分支
RunnableBranch(
    (condition_func, chain_a),
    (condition_func, chain_b),
    default_chain,
)
```

### 三种调用方式
```python
chain.invoke(input)           # 单次
chain.batch([input1, input2]) # 批量
chain.stream(input)           # 流式
```

### 错误处理
```python
robust = model.with_retry(stop_after_attempt=3)
robust = model.with_fallbacks([backup_model])
```

## 模式选择决策表

| 需求 | 推荐模式 | 关键组件 |
|------|---------|---------|
| 单一流水线 | 顺序 `a \| b \| c` | 管道符 |
| 多任务无依赖 | 并行 `RunnableParallel` | RunnableParallel |
| 需要上下文 + 问题 | 混合 | RunnablePassthrough + Parallel |
| 根据输入分发 | 分支 | RunnableBranch |
| 补充中间字段 | 传递 | RunnablePassthrough.assign() |

## 常见错误排查

| 错误现象 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `KeyError: 'question'` | Prompt 变量与输入字段不匹配 | 检查输入 dict 的 key 与模板变量一致 |
| 类型不匹配报错 | 管道符前后类型不衔接 | 用 RunnableLambda 做类型转换 |
| `RunnableBranch` 不触发 | 条件函数返回 False | 检查条件 lambda 逻辑，确保有默认分支 |
| 并行链报错 | 某个分支抛异常 | 给该分支加 with_fallbacks |

## 从 Legacy Chain 迁移指南

| Legacy 写法 | LCEL 等价写法 |
|------------|--------------|
| `LLMChain(llm=m, prompt=p).run(q)` | `(p \| m \| parser).invoke(q)` |
| `SequentialChain(chains=[...])` | `chain_a \| chain_b \| chain_c` |
| `TransformChain(transform=fn)` | `RunnableLambda(fn)` |
| `RouterChain` | `RunnableBranch(...)` |
