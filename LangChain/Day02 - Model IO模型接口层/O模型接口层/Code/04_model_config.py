# 文件用途：模型配置与回退
# 演示 temperature/max_tokens/streaming/timeout 参数对比
# .bind() 绑定参数、.with_structured_output() 结构化输出
# .with_fallbacks() 模型回退（GPT-4o → GPT-4o-mini → 本地模型）
# ModelConfig 类封装配置管理

import os
import sys
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# ModelConfig 类：统一管理模型配置
# ============================================================
@dataclass
class ModelConfig:
    """模型配置管理类"""

    model_name: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000
    streaming: bool = False
    timeout: int = 30
    max_retries: int = 2
    stop: list = field(default_factory=list)
    seed: int | None = None

    def to_dict(self) -> dict:
        """转为字典（过滤 None 值）"""
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def to_openai_kwargs(self) -> dict:
        """转为 ChatOpenAI 可用的参数"""
        kwargs = {
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }
        if self.streaming:
            kwargs["streaming"] = True
        if self.stop:
            kwargs["stop"] = self.stop
        if self.seed is not None:
            kwargs["seed"] = self.seed
        return kwargs

    def describe(self) -> str:
        """生成配置描述"""
        lines = [f"ModelConfig 配置："]
        for k, v in self.to_dict().items():
            lines.append(f"  {k}: {v}")
        return "\n".join(lines)


# ============================================================
# 1. 参数对比：temperature
# ============================================================
def demo_temperature():
    """temperature 参数对比"""
    print("=" * 60)
    print("【1】temperature 参数对比")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    prompt = "给'秋天'写一句诗意的描述。"

    # 对比不同温度
    for temp in [0.0, 0.7, 1.5]:
        model = ChatOpenAI(model="gpt-4o-mini", temperature=temp, max_tokens=50)
        result = model.invoke([HumanMessage(content=prompt)])
        print(f"  temperature={temp}: {result.content}")

    print("\n  结论：")
    print("    temperature=0  → 确定性输出，每次相同（适合分类/抽取）")
    print("    temperature=0.7→ 平衡创意与稳定（默认，适合对话）")
    print("    temperature=1.5→ 高随机性，可能不连贯\n")


# ============================================================
# 2. 参数对比：max_tokens
# ============================================================
def demo_max_tokens():
    """max_tokens 参数对比"""
    print("=" * 60)
    print("【2】max_tokens 参数对比")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    prompt = "详细介绍 Python 语言的优点。"

    # 对比不同 max_tokens
    for max_tok in [10, 50, 200]:
        model = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=max_tok)
        result = model.invoke([HumanMessage(content=prompt)])
        print(f"  max_tokens={max_tok}:")
        print(f"    {result.content[:80]}...")
        print(f"    实际输出 Token：{result.usage_metadata['output_tokens']}\n")


# ============================================================
# 3. .bind() 绑定参数
# ============================================================
def demo_bind():
    """.bind() 绑定固定参数"""
    print("=" * 60)
    print("【3】.bind() 绑定固定参数")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 绑定 stop 序列：遇到 "。" 停止
    model_with_stop = model.bind(stop=["。"])

    result = model_with_stop.invoke(
        [HumanMessage(content="写三句话，每句以句号结尾。")]
    )
    print(f"  绑定 stop=['。'] 后：")
    print(f"    {result.content}")
    print(f"    （遇到第一个'。'就停止生成）\n")


# ============================================================
# 4. .with_structured_output() 结构化输出
# ============================================================
def demo_structured_output():
    """.with_structured_output() 结构化输出"""
    print("=" * 60)
    print("【4】.with_structured_output() 结构化输出")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_openai import ChatOpenAI
    from pydantic import BaseModel, Field

    # 定义 Pydantic 模型
    class PersonInfo(BaseModel):
        """人物信息"""
        name: str = Field(description="人物姓名")
        age: int = Field(description="人物年龄")
        occupation: str = Field(description="职业")

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 绑定结构化输出
    structured_model = model.with_structured_output(PersonInfo)

    result = structured_model.invoke("张三今年 28 岁，是一名软件工程师。")

    print(f"  输入：张三今年 28 岁，是一名软件工程师。")
    print(f"  输出类型：{type(result).__name__}（直接是 Pydantic 实例，非 AIMessage）")
    print(f"  name：{result.name}")
    print(f"  age：{result.age}")
    print(f"  occupation：{result.occupation}")
    print(f"\n  （结构化输出详解见 Day04 - Output Parsers）\n")


# ============================================================
# 5. .with_fallbacks() 模型回退
# ============================================================
def demo_fallbacks():
    """.with_fallbacks() 模型回退"""
    print("=" * 60)
    print("【5】.with_fallbacks() 模型回退")
    print("=" * 60)

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    # 模拟主模型（故意用无效模型名触发错误）
    primary = ChatOpenAI(model="gpt-4o-nonexistent", max_retries=0)
    # 备用模型 1
    fallback1 = ChatOpenAI(model="gpt-4o-mini", max_retries=1)

    # 配置回退链
    model_with_fallback = primary.with_fallbacks([fallback1])

    print("  回退链：gpt-4o-nonexistent → gpt-4o-mini")
    print("  （主模型故意用无效名称，会自动切换到备用模型）\n")

    try:
        result = model_with_fallback.invoke(
            [HumanMessage(content="用一句话解释什么是回退机制。")]
        )
        print(f"  回退成功！回复：{result.content}")
        print(f"  实际使用模型：{result.response_metadata.get('model_name', '未知')}\n")
    except Exception as e:
        print(f"  回退也失败了：{e}\n")


# ============================================================
# 6. ModelConfig 类演示
# ============================================================
def demo_model_config_class():
    """ModelConfig 配置管理类演示"""
    print("=" * 60)
    print("【6】ModelConfig 配置管理类")
    print("=" * 60)

    # 创建配置
    config = ModelConfig(
        model_name="gpt-4o-mini",
        temperature=0.3,
        max_tokens=500,
        streaming=True,
        timeout=60,
        max_retries=3,
    )

    print(config.describe())
    print()

    # 转为 ChatOpenAI 参数
    print("  转为 ChatOpenAI 参数：")
    for k, v in config.to_openai_kwargs().items():
        print(f"    {k}: {v}")

    print("\n  使用配置创建模型：")
    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI
        model = ChatOpenAI(**config.to_openai_kwargs())
        print(f"    ✅ 模型创建成功：{type(model).__name__}")
    else:
        print("    ⚠️  未配置 API Key，仅展示配置")
    print()


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    print("🚀 Day02 - 模型配置与回退\n")

    # 1. temperature 参数对比
    demo_temperature()

    # 2. max_tokens 参数对比
    demo_max_tokens()

    # 3. .bind() 绑定参数
    demo_bind()

    # 4. 结构化输出
    demo_structured_output()

    # 5. 模型回退
    demo_fallbacks()

    # 6. ModelConfig 类
    demo_model_config_class()

    print("=" * 60)
    print("✅ 模型配置与回退演示完成")
    print("关键点：")
    print("  - temperature 控制随机性，max_tokens 控制输出长度")
    print("  - .bind() 绑定固定参数（如 stop 序列）")
    print("  - .with_structured_output() 直接输出 Pydantic 对象")
    print("  - .with_fallbacks() 实现模型回退，提升可用性")
    print("  - ModelConfig 类集中管理配置，便于复用")
    print("=" * 60)
