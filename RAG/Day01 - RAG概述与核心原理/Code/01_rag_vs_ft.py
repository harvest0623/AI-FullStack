# -*- coding: utf-8 -*-
"""
文件用途：Day01 - 01 RAG 与微调/直答对比
演示"模型直答" vs "RAG 注入上下文后回答"的差异，
直观理解 RAG 为什么能减少幻觉、引入私有数据。

场景：DataIQ 企业知识库。员工问"我们每天最多可以远程办公几天？"
  - 仅 LLM：模型训练数据里没有这家虚构公司的政策，只能编。
  - RAG：检索到《远程办公政策》文档，基于原文回答，有依据。

运行：python 01_rag_vs_ft.py
依赖：openai python-dotenv（或任意 OpenAI 兼容的 LLM）
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------- 1. 一份"只有知识库里才有的"私有文档 ----------
POLICY_DOC = """
DataIQ 公司《远程办公政策》
第一条：员工每周最多可以在家办公三天。
第二条：在家办公需保障上午 10 点至下午 4 点在线，并参加团队周会。
第三条：如需长期远程，需书面申请并经部门经理批准。
"""

QUESTION = "我们 DataIQ 的员工每周最多可以远程办公几天？"


# ---------- 2. 极简 LLM 调用（仅用于演示，生产请用封装好的客户端） ----------
def call_llm(system_prompt: str, user_prompt: str) -> str:
    """调用 OpenAI 兼容接口。无 Key 时优雅降级返回说明文字。"""
    try:
        from openai import OpenAI

        client = OpenAI()
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"[!] 未配置有效 OPENAI_API_KEY，跳过真实调用（原因：{e}）"


def answer_without_rag() -> str:
    """方式一：把问题直接丢给模型，不提供任何私有上下文。"""
    sys_prompt = "你是一个乐于助人的助手。若不知道答案就坦白说不知道，不要编造。"
    return call_llm(sys_prompt, QUESTION)


def answer_with_rag() -> str:
    """方式二：先用关键词在私有文档中"检索"，把命中段落拼进 Prompt 再回答。"""
    # 模拟一次最简单的检索：命中包含"远程/三天"的段落
    retrieved = [line.strip() for line in POLICY_DOC.splitlines() if line.strip()]
    context = "\n".join(retrieved)

    sys_prompt = (
        "你是一个企业知识库问答助手。请严格**只依据**下面提供的资料回答，"
        "资料中没有的内容不要臆测。回答时附上依据的原文要点。"
    )
    user_prompt = f"=== 检索到的资料 ===\n{context}\n\n=== 问题 ===\n{QUESTION}"
    return call_llm(sys_prompt, user_prompt)


def main() -> None:
    print("========== 问题 ==========")
    print(QUESTION)
    print("\n========== 方式一：模型直答（无私有数据） ==========")
    print(answer_without_rag())
    print("\n========== 方式二：RAG 注入检索上下文 ==========")
    print(answer_with_rag())
    print("\n========== 对比小结 ==========")
    print(
        "· 方式一依赖模型记忆，对私有数据无能为力，易编造；\n"
        "· 方式二先检索私有文档，再基于原文作答，准确且可溯源。\n"
        "· 这正是 RAG 的核心价值：连接 LLM 与你的私有数据。"
    )


if __name__ == "__main__":
    main()