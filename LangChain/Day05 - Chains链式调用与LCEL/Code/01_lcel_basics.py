# 文件用途：LCEL 基础语法演示
# 演示 prompt | model | parser 三步管道、StrOutputParser 基础链，
# 以及 invoke / batch / stream 三种调用方式，展示管道符的类型传递。
# 场景：ChainQA 基础问答链

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 加载 .env 中的 API Key
load_dotenv()


def build_basic_chain() -> object:
    """构建最基础的 LCEL 三步管道：prompt | model | parser。

    类型传递流程：
        ChatPromptTemplate.invoke(dict) -> ChatPromptValue
        ChatModel.invoke(ChatPromptValue) -> BaseMessage
        StrOutputParser.invoke(BaseMessage) -> str
    """
    # 1. 定义 Prompt 模板（接收 dict，输出 ChatPromptValue）
    prompt = ChatPromptTemplate.from_template(
        "你是 ChainQA 智能问答助手。请用一句话简洁地回答：\n问题：{question}"
    )

    # 2. 创建 ChatModel（接收 ChatPromptValue，输出 BaseMessage）
    model = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    # 3. 创建字符串解析器（接收 BaseMessage，输出 str）
    parser = StrOutputParser()

    # 4. 用管道符 | 组合为一条链
    chain = prompt | model | parser
    return chain


def demo_invoke(chain: object) -> None:
    """演示单次调用 invoke。"""
    print("=" * 60)
    print("【invoke 单次调用】")
    result = chain.invoke({"question": "什么是 LangChain？"})
    print(f"回答：{result}\n")


def demo_batch(chain: object) -> None:
    """演示批量调用 batch：并行处理多个输入。"""
    print("=" * 60)
    print("【batch 批量调用】")
    questions = [
        {"question": "什么是 LCEL？"},
        {"question": "什么是 Runnable 接口？"},
        {"question": "什么是管道符？"},
    ]
    results = chain.batch(questions)
    for q, r in zip(questions, results):
        print(f"问题：{q['question']}")
        print(f"回答：{r}\n")


def demo_stream(chain: object) -> None:
    """演示流式输出 stream：逐 token 返回，适合实时展示。"""
    print("=" * 60)
    print("【stream 流式输出】")
    print("回答：", end="", flush=True)
    for chunk in chain.stream({"question": "用 30 字介绍 Python 的优点"}):
        print(chunk, end="", flush=True)
    print("\n")


def demo_type_passing() -> None:
    """展示管道符每一步的类型传递，理解 LCEL 的数据流。"""
    print("=" * 60)
    print("【管道符类型传递演示】")

    prompt = ChatPromptTemplate.from_template("解释：{topic}")
    model = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    parser = StrOutputParser()

    # 第 1 步：dict -> ChatPromptValue
    prompt_value = prompt.invoke({"topic": "LangChain"})
    print(f"第 1 步 prompt 输出类型：{type(prompt_value).__name__}")

    # 第 2 步：ChatPromptValue -> BaseMessage
    message = model.invoke(prompt_value)
    print(f"第 2 步 model 输出类型：{type(message).__name__}")

    # 第 3 步：BaseMessage -> str
    text = parser.invoke(message)
    print(f"第 3 步 parser 输出类型：{type(text).__name__}")
    print(f"最终结果：{text[:50]}...\n")


def demo_input_output_schema(chain: object) -> None:
    """展示链的输入/输出 Schema，LCEL 自带类型推断。"""
    print("=" * 60)
    print("【链的输入输出 Schema】")
    print(f"输入 Schema：{chain.input_schema.model_json_schema()}")
    print(f"输出 Schema：{chain.output_schema.model_json_schema()}\n")


def main() -> None:
    """主函数：依次演示 LCEL 基础用法。"""
    chain = build_basic_chain()

    # 单次调用
    demo_invoke(chain)

    # 批量调用
    demo_batch(chain)

    # 流式输出
    demo_stream(chain)

    # 类型传递演示
    demo_type_passing()

    # 输入输出 Schema
    demo_input_output_schema(chain)

    print("=" * 60)
    print("LCEL 基础语法演示完成。")


if __name__ == "__main__":
    main()
