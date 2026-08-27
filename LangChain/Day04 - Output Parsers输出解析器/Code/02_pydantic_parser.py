# 文件用途：Pydantic 模型解析
# 定义 Pydantic 模型(ProductInfo/OrderDetail/CustomerIntent) + Field 描述
# PydanticOutputParser 创建 / get_format_instructions() 生成格式说明
# 解析 LLM 输出为模型实例 / 类型安全访问字段
# 场景：从用户消息提取结构化信息

import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# Pydantic 模型定义
# ============================================================
from pydantic import BaseModel, Field


class ProductInfo(BaseModel):
    """产品信息模型"""
    name: str = Field(description="产品名称")
    price: float = Field(description="产品价格（元）", ge=0)
    category: str = Field(description="产品类别")
    in_stock: bool = Field(description="是否有库存")


class OrderDetail(BaseModel):
    """订单详情模型"""
    order_id: str = Field(description="订单编号")
    product: str = Field(description="商品名称")
    quantity: int = Field(description="购买数量", ge=1)
    total_price: float = Field(description="总价（元）", ge=0)
    status: str = Field(description="订单状态：待付款/已付款/已发货/已完成")


class CustomerIntent(BaseModel):
    """客户意图模型"""
    intent: str = Field(description="意图类别：退款/咨询/投诉/建议")
    confidence: float = Field(description="置信度 0-1", ge=0, le=1)
    keywords: list[str] = Field(description="关键词列表")


# ============================================================
# 1. PydanticOutputParser 基础
# ============================================================
def demo_pydantic_parser_basic():
    """PydanticOutputParser 基础使用"""
    print("=" * 60)
    print("【1】PydanticOutputParser 基础")
    print("=" * 60)

    from langchain_core.output_parsers import PydanticOutputParser

    parser = PydanticOutputParser(pydantic_object=ProductInfo)

    # 查看自动生成的格式指令
    print("  自动生成的格式指令：")
    instructions = parser.get_format_instructions()
    print(f"  {instructions[:400]}...\n")

    # 解析 LLM 输出（JSON 字符串）
    llm_output = """
    {
        "name": "iPhone 15",
        "price": 5999.0,
        "category": "手机",
        "in_stock": true
    }
    """
    result = parser.parse(llm_output)
    print(f"  输出类型：{type(result).__name__}（Pydantic 实例）")
    print(f"  name：{result.name}")
    print(f"  price：{result.price}")
    print(f"  category：{result.category}")
    print(f"  in_stock：{result.in_stock}\n")


# ============================================================
# 2. 类型安全访问演示
# ============================================================
def demo_type_safety():
    """Pydantic 实例的类型安全访问"""
    print("=" * 60)
    print("【2】类型安全访问")
    print("=" * 60)

    from langchain_core.output_parsers import PydanticOutputParser

    parser = PydanticOutputParser(pydantic_object=OrderDetail)

    llm_output = """
    {
        "order_id": "ORD-2024-001",
        "product": "MacBook Pro",
        "quantity": 2,
        "total_price": 29998.0,
        "status": "已付款"
    }
    """
    order = parser.parse(llm_output)

    # 类型安全：IDE 自动补全 order.order_id / order.product 等
    print(f"  订单号：{order.order_id}")
    print(f"  商品：{order.product}")
    print(f"  数量：{order.quantity}（类型：{type(order.quantity).__name__}）")
    print(f"  总价：{order.total_price}（类型：{type(order.total_price).__name__}）")
    print(f"  状态：{order.status}")

    # 类型转换自动完成：quantity 是 int，total_price 是 float
    print(f"\n  类型安全：quantity+1 = {order.quantity + 1}（可直接运算）")
    print()


# ============================================================
# 3. 完整 Chain：产品信息抽取
# ============================================================
def demo_product_extraction_chain():
    """完整 Chain：从文本提取产品信息"""
    print("=" * 60)
    print("【3】完整 Chain：产品信息抽取")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import PydanticOutputParser

    # 创建 Parser
    parser = PydanticOutputParser(pydantic_object=ProductInfo)

    # 创建 Prompt，注入格式指令
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是信息抽取助手，从文本中提取产品信息。"),
        ("human", "请提取以下文本的产品信息：\n{text}\n\n{format_instructions}"),
    ]).partial(format_instructions=parser.get_format_instructions())

    # 组成 Chain
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = prompt | model | parser

    # 测试
    texts = [
        "iPhone 15 Pro 售价 7999 元，属于手机类别，目前有货。",
        "MacBook Air M3 价格 8999 元，是笔记本电脑，暂时缺货。",
    ]

    for text in texts:
        result = chain.invoke({"text": text})
        print(f"  输入：{text}")
        print(f"  提取结果：")
        print(f"    名称：{result.name}")
        print(f"    价格：{result.price} 元")
        print(f"    类别：{result.category}")
        print(f"    库存：{'有' if result.in_stock else '无'}\n")


# ============================================================
# 4. 客户意图识别
# ============================================================
def demo_intent_extraction_chain():
    """客户意图识别 Chain"""
    print("=" * 60)
    print("【4】客户意图识别")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import PydanticOutputParser

    parser = PydanticOutputParser(pydantic_object=CustomerIntent)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是客服意图识别系统，分析用户消息。"),
        ("human", "用户消息：{message}\n\n{format_instructions}"),
    ]).partial(format_instructions=parser.get_format_instructions())

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = prompt | model | parser

    messages = [
        "我买的手机有质量问题，要退款！",
        "请问你们几点下班？",
    ]

    for msg in messages:
        result = chain.invoke({"message": msg})
        print(f"  用户：{msg}")
        print(f"  意图：{result.intent}（置信度：{result.confidence}）")
        print(f"  关键词：{result.keywords}\n")


# ============================================================
# 5. PydanticOutputParser vs with_structured_output 对比
# ============================================================
def demo_comparison():
    """两种结构化输出方式对比"""
    print("=" * 60)
    print("【5】PydanticOutputParser vs with_structured_output")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import PydanticOutputParser

    text = "iPad Pro 11 寸 售价 6799 元，平板电脑，有货"

    # 方式 A：PydanticOutputParser（传统，代码多但可控）
    print("  方式 A：PydanticOutputParser")
    parser = PydanticOutputParser(pydantic_object=ProductInfo)
    prompt_a = ChatPromptTemplate.from_template(
        "提取信息：{text}\n\n{format_instructions}"
    ).partial(format_instructions=parser.get_format_instructions())
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain_a = prompt_a | model | parser
    result_a = chain_a.invoke({"text": text})
    print(f"    结果：{result_a.name} / {result_a.price}\n")

    # 方式 B：with_structured_output（简洁，推荐）
    print("  方式 B：with_structured_output")
    structured_model = model.with_structured_output(ProductInfo)
    prompt_b = ChatPromptTemplate.from_template("提取信息：{text}")
    chain_b = prompt_b | structured_model
    result_b = chain_b.invoke({"text": text})
    print(f"    结果：{result_b.name} / {result_b.price}\n")

    print("  对比：")
    print("    A 代码多但可控性高，B 代码少推荐日常使用")
    print()


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    print("🚀 Day04 - Pydantic 模型解析\n")

    demo_pydantic_parser_basic()
    demo_type_safety()
    demo_product_extraction_chain()
    demo_intent_extraction_chain()
    demo_comparison()

    print("=" * 60)
    print("✅ Pydantic 模型解析演示完成")
    print("总结：")
    print("  - PydanticOutputParser 将 LLM 输出解析为 Pydantic 实例")
    print("  - Field description 指导 LLM 输出正确格式")
    print("  - 类型安全：IDE 自动补全，可直接运算")
    print("  - with_structured_output 是更简洁的替代方案")
    print("=" * 60)
