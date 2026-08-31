# 文件用途：LangSmith 追踪集成
# 配置 LANGCHAIN_API_KEY / 自动追踪 Chain 执行 / 查看 Trace 可视化 / 评估 Chain 质量
# 如无 Key 则展示配置方法和预期效果
# 运行：python 04_langsmith_trace.py
# 依赖：pip install langchain langchain-openai python-dotenv
# 可选：在 .env 中配置 LANGCHAIN_API_KEY 开启真实追踪

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

load_dotenv()


# ============================================================
# LangSmith 配置检查
# ============================================================

def check_langsmith_config() -> dict:
    """检查 LangSmith 相关环境变量配置情况"""
    config = {
        "api_key": os.getenv("LANGCHAIN_API_KEY", ""),
        "tracing_v2": os.getenv("LANGCHAIN_TRACING_V2", ""),
        "project": os.getenv("LANGCHAIN_PROJECT", "default"),
        "endpoint": os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"),
    }
    config["enabled"] = bool(config["api_key"]) and config["tracing_v2"].lower() == "true"
    return config


def print_langsmith_setup_guide() -> None:
    """打印 LangSmith 配置指南"""
    print("""
╔══════════════════════════════════════════════════════════╗
║           LangSmith 配置与使用指南                        ║
╚══════════════════════════════════════════════════════════╝

【第1步】注册 LangSmith 账号
  访问 https://smith.langchain.com 注册（免费版每月 5000 次追踪）

【第2步】获取 API Key
  登录后进入 Settings → API Keys → Create API Key
  复制 API Key（格式：ls_xxxxxxxx）

【第3步】配置 .env 文件
  在项目根目录 .env 中添加：
  ┌────────────────────────────────────────────┐
  │ LANGCHAIN_API_KEY=ls_xxxxxxxx              │
  │ LANGCHAIN_TRACING_V2=true                  │
  │ LANGCHAIN_PROJECT=chainqa                  │
  └────────────────────────────────────────────┘

【第4步】运行本脚本
  配置完成后无需修改代码，LangChain 会自动上报所有 Chain 执行

【第5步】查看 Trace
  访问 https://smith.langchain.com
  选择你的项目 → 查看每次执行的完整链路：
    - 每一步的输入/输出
    - 每一步的耗时
    - Token 消耗与成本
    - 错误堆栈（如有）

【预期效果】
  开启 LangSmith 后，本脚本的每次 Chain 调用都会在 LangSmith 界面
  生成一条 trace 记录，可视化展示执行链路。
""")


# ============================================================
# 构建 ChainQA 评估链
# ============================================================

def build_chainqa_chain():
    """构建 ChainQA 问答链"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是 ChainQA 智能问答助手，请用准确简洁的中文回答。"),
        ("human", "{question}"),
    ])
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    parser = StrOutputParser()
    return prompt | model | parser


def build_eval_chain():
    """构建评估链：给回答打分（1-5）"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个回答质量评估员。请根据问题和回答，给出 1-5 分的评分。
评分标准：
- 5分：完全准确、清晰、完整
- 4分：基本准确，有小瑕疵
- 3分：部分正确，有遗漏
- 2分：不太准确
- 1分：完全错误

只输出 JSON：{{"score": 数字, "reason": "评分理由"}}"""),
        ("human", "问题：{question}\n回答：{answer}"),
    ])
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    parser = StrOutputParser()
    return prompt | model | parser


# ============================================================
# 主流程
# ============================================================

def main() -> None:
    print("=" * 60)
    print("Day10 - 04 LangSmith 追踪集成演示")
    print("=" * 60)

    # 检查 LangSmith 配置
    config = check_langsmith_config()

    if config["enabled"]:
        print(f"\n✅ LangSmith 已启用")
        print(f"   项目: {config['project']}")
        print(f"   Endpoint: {config['endpoint']}")
        print(f"   本脚本的执行将自动上报到 LangSmith")
    else:
        print(f"\n⚠️  LangSmith 未启用（未检测到完整配置）")
        print(f"   API Key: {'已配置' if config['api_key'] else '未配置'}")
        print(f"   Tracing V2: {config['tracing_v2'] or '未配置'}")
        print_langsmith_setup_guide()
        print("\n本脚本将继续运行演示（不会上报到 LangSmith），")
        print("配置 Key 后重跑即可在 LangSmith 界面看到 trace。\n")

    # 检查 OpenAI Key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ 未检测到 OPENAI_API_KEY，请在 .env 中配置后运行。")
        return

    # 构建 ChainQA 链
    chain = build_chainqa_chain()

    # 评估测试集
    test_cases = [
        {"question": "什么是 LangChain？", "expected": "LLM 应用开发框架"},
        {"question": "LCEL 是什么？", "expected": "LangChain 表达式语言"},
        {"question": "解释 Memory 的作用", "expected": "管理多轮对话历史"},
    ]

    print("\n" + "=" * 60)
    print("📋 运行 ChainQA 评估测试集")
    print("=" * 60)

    results = []
    for i, tc in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] 问题：{tc['question']}")
        # 给本次调用命名（在 LangSmith 中显示）
        run_name = f"ChainQA-Eval-{i}"
        answer = chain.invoke(
            {"question": tc["question"]},
            config={"run_name": run_name},
        )
        print(f"    回答：{answer[:100]}{'...' if len(answer) > 100 else ''}")
        results.append({"question": tc["question"], "answer": answer, "expected": tc["expected"]})

    # 用评估链打分
    print("\n" + "=" * 60)
    print("📊 用评估链给回答打分")
    print("=" * 60)

    eval_chain = build_eval_chain()
    for i, r in enumerate(results, 1):
        eval_result = eval_chain.invoke(
            {"question": r["question"], "answer": r["answer"]},
            config={"run_name": f"ChainQA-Score-{i}"},
        )
        print(f"\n[{i}] 评分结果：{eval_result[:150]}")

    print("\n" + "=" * 60)
    print("✅ LangSmith 追踪集成演示完成")
    if config["enabled"]:
        print(f"\n🎉 请访问 https://smith.langchain.com")
        print(f"   在项目 '{config['project']}' 中查看本次执行的完整 trace！")
        print(f"   你将看到：")
        print(f"   - 每次 Chain 调用的输入输出")
        print(f"   - 每一步的耗时和 Token 消耗")
        print(f"   - 评估链的打分过程")
    else:
        print(f"\n💡 配置 LangSmith API Key 后重跑，即可在界面看到可视化追踪。")
    print("=" * 60)


if __name__ == "__main__":
    main()
