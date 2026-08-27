# 文件用途：PromptTemplate 基础
# 演示 5 种 PromptTemplate 使用模式
# 场景：客服问答 / 文本摘要 / 信息抽取
# 包含 from_template 创建 / 显式变量 / format 渲染 / 变量验证 / partial 部分填充

from langchain_core.prompts import PromptTemplate


# ============================================================
# 模式 1：from_template 创建（自动提取变量）
# ============================================================
def demo_from_template():
    """从字符串创建，自动识别 {variable} 变量"""
    print("=" * 60)
    print("【模式 1】from_template 创建（自动提取变量）")
    print("=" * 60)

    # 自动识别 {topic} 变量
    template = PromptTemplate.from_template(
        "请用一句话解释什么是 {topic}。"
    )

    print(f"  输入变量：{template.input_variables}")
    print(f"  模板内容：{template.template}\n")

    # format 渲染
    result = template.format(topic="LangChain")
    print(f"  渲染结果：{result}\n")


# ============================================================
# 模式 2：显式指定变量（严格验证）
# ============================================================
def demo_explicit_variables():
    """显式指定 input_variables，更严格"""
    print("=" * 60)
    print("【模式 2】显式指定变量")
    print("=" * 60)

    template = PromptTemplate(
        template="请将以下文本总结为不超过 {max_words} 字：\n{text}",
        input_variables=["text", "max_words"],
    )

    print(f"  输入变量：{template.input_variables}")

    result = template.format(
        text="LangChain 是一个用于构建 LLM 应用的开源框架，提供模块化组件。",
        max_words="20",
    )
    print(f"  渲染结果：\n  {result}\n")

    # 演示变量验证（缺少变量报错）
    print("  变量验证测试（故意缺少 max_words）：")
    try:
        template.format(text="测试文本")  # 缺少 max_words
    except Exception as e:
        print(f"  ❌ 报错（符合预期）：{type(e).__name__}\n")


# ============================================================
# 模式 3：partial 部分变量填充
# ============================================================
def demo_partial():
    """partial 预填充部分变量，运行时只传剩余变量"""
    print("=" * 60)
    print("【模式 3】partial 部分变量填充")
    print("=" * 60)

    # 场景：客服系统，角色提前设定，问题运行时传入
    template = PromptTemplate.from_template(
        "你是{role}，请用{style}的语气回答：\n{question}"
    )

    # 预填充 role 和 style
    customer_service = template.partial(role="客服助手", style="专业亲切")

    print(f"  预填充后输入变量：{customer_service.input_variables}")

    # 运行时只需提供 question
    result = customer_service.format(question="如何退款？")
    print(f"  渲染结果：\n  {result}\n")


# ============================================================
# 模式 4：场景应用 - 客服问答
# ============================================================
def demo_customer_service():
    """场景：客服问答系统"""
    print("=" * 60)
    print("【模式 4】场景应用 - 客服问答")
    print("=" * 60)

    # 客服 Prompt 模板
    customer_prompt = PromptTemplate.from_template(
        """你是 ChainQA 的客服助手，请遵循以下规范：
1. 语气专业亲切
2. 回答不超过 100 字
3. 如不确定，建议联系人工客服

用户问题：{question}
请回答："""
    )

    questions = [
        "如何注册账号？",
        "支持哪些支付方式？",
        "忘记密码怎么办？",
    ]

    print("  客服问答示例：")
    for q in questions:
        prompt = customer_prompt.format(question=q)
        print(f"\n  【问题】{q}")
        print(f"  【Prompt】\n  {prompt}")


# ============================================================
# 模式 5：场景应用 - 信息抽取
# ============================================================
def demo_extraction():
    """场景：信息抽取"""
    print("\n" + "=" * 60)
    print("【模式 5】场景应用 - 信息抽取")
    print("=" * 60)

    # 信息抽取模板
    extract_prompt = PromptTemplate.from_template(
        """从以下文本中提取关键信息，以 JSON 格式输出：
文本：{text}

提取要求：
- 姓名、年龄、职业
- 输出格式：{{"name": "...", "age": ..., "occupation": "..."}}
"""
    )

    text = "张三今年 28 岁，是一名 Python 后端工程师，在北京工作。"
    prompt = extract_prompt.format(text=text)

    print(f"  输入文本：{text}")
    print(f"  生成的 Prompt：\n  {prompt}")


# ============================================================
# 模式 6：与 ChatModel 配合（LCEL 管道预览）
# ============================================================
def demo_with_model():
    """PromptTemplate 与模型配合使用"""
    print("\n" + "=" * 60)
    print("【模式 6】PromptTemplate 与模型配合")
    print("=" * 60)

    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  未配置 OPENAI_API_KEY，跳过模型调用\n")
        return

    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import StrOutputParser
    from dotenv import load_dotenv
    load_dotenv()

    # 创建模板
    template = PromptTemplate.from_template("用一句话解释什么是 {topic}。")

    # LCEL 管道：template | model | parser
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    parser = StrOutputParser()

    chain = template | model | parser

    result = chain.invoke({"topic": "LangChain"})
    print(f"  结果：{result}\n")


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    print("🚀 Day03 - PromptTemplate 基础\n")

    demo_from_template()
    demo_explicit_variables()
    demo_partial()
    demo_customer_service()
    demo_extraction()
    demo_with_model()

    print("=" * 60)
    print("✅ PromptTemplate 基础演示完成")
    print("总结：")
    print("  - from_template：自动提取变量，最常用")
    print("  - 显式变量：严格验证，适合关键场景")
    print("  - partial：预填充部分变量，灵活复用")
    print("  - format：渲染为字符串")
    print("=" * 60)
