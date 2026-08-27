# 文件用途：模板序列化与文件加载
# 将 PromptTemplate 保存为 JSON/YAML 文件 / load_prompt 加载
# 从 Hub 加载（hub.pull）/ 模板版本管理
# 展示 Prompt 即代码实践

import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 临时文件目录
TEMP_DIR = Path("./prompt_templates")


# ============================================================
# 1. 保存为 JSON 文件
# ============================================================
def demo_save_json():
    """将 PromptTemplate 保存为 JSON"""
    print("=" * 60)
    print("【1】保存为 JSON 文件")
    print("=" * 60)

    from langchain_core.prompts import PromptTemplate

    template = PromptTemplate.from_template(
        "你是{role}，请{style}地回答：\n{question}"
    )

    # 保存为 JSON 文件
    TEMP_DIR.mkdir(exist_ok=True)
    json_path = TEMP_DIR / "qa_prompt.json"

    template_dict = template.dict()
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(template_dict, f, ensure_ascii=False, indent=2)

    print(f"  模板已保存：{json_path}")
    print(f"  模板内容：{template.template}")
    print(f"  输入变量：{template.input_variables}\n")

    # 展示 JSON 内容
    print("  JSON 文件内容：")
    with open(json_path, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"  {content}\n")


# ============================================================
# 2. 从 JSON 加载
# ============================================================
def demo_load_json():
    """从 JSON 文件加载 PromptTemplate"""
    print("=" * 60)
    print("【2】从 JSON 文件加载")
    print("=" * 60)

    from langchain_core.prompts import load_prompt

    json_path = TEMP_DIR / "qa_prompt.json"

    # load_prompt 加载
    template = load_prompt(str(json_path))

    print(f"  已加载：{json_path}")
    print(f"  模板内容：{template.template}")
    print(f"  输入变量：{template.input_variables}")

    # 渲染测试
    result = template.format(
        role="客服",
        style="专业",
        question="如何退款？",
    )
    print(f"  渲染结果：{result}\n")


# ============================================================
# 3. 保存为 YAML 文件
# ============================================================
def demo_save_yaml():
    """将 PromptTemplate 保存为 YAML"""
    print("=" * 60)
    print("【3】保存为 YAML 文件")
    print("=" * 60)

    from langchain_core.prompts import PromptTemplate

    template = PromptTemplate.from_template("总结以下文本，不超过 {max_words} 字：\n{text}")

    # 手动构建 YAML（LangChain 的 load_prompt 支持 YAML 格式）
    yaml_path = TEMP_DIR / "summary_prompt.yaml"
    yaml_content = f"""_type: prompt
template: |
  总结以下文本，不超过 {{max_words}} 字：
  {{text}}
input_variables:
  - max_words
  - text
"""
    yaml_path.write_text(yaml_content, encoding="utf-8")

    print(f"  模板已保存：{yaml_path}")
    print(f"  YAML 内容：\n{yaml_content}")


# ============================================================
# 4. 从 YAML 加载
# ============================================================
def demo_load_yaml():
    """从 YAML 文件加载"""
    print("=" * 60)
    print("【4】从 YAML 文件加载")
    print("=" * 60)

    from langchain_core.prompts import load_prompt

    yaml_path = TEMP_DIR / "summary_prompt.yaml"
    template = load_prompt(str(yaml_path))

    print(f"  已加载：{yaml_path}")
    print(f"  模板内容：{template.template}")
    print(f"  输入变量：{template.input_variables}\n")


# ============================================================
# 5. ChatPromptTemplate 序列化
# ============================================================
def demo_chat_prompt_serialize():
    """ChatPromptTemplate 序列化"""
    print("=" * 60)
    print("【5】ChatPromptTemplate 序列化")
    print("=" * 60)

    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是{role}，用{style}语气回答。"),
        ("human", "{question}"),
    ])

    # 保存
    chat_path = TEMP_DIR / "chat_prompt.json"
    with open(chat_path, "w", encoding="utf-8") as f:
        json.dump(prompt.dict(), f, ensure_ascii=False, indent=2)

    print(f"  ChatPromptTemplate 已保存：{chat_path}")

    # 加载
    from langchain_core.prompts import load_prompt
    loaded = load_prompt(str(chat_path))
    print(f"  加载后类型：{type(loaded).__name__}")
    print(f"  输入变量：{loaded.input_variables}\n")


# ============================================================
# 6. 从 PromptHub 加载
# ============================================================
def demo_hub_pull():
    """从 LangChain PromptHub 加载"""
    print("=" * 60)
    print("【6】从 PromptHub 加载")
    print("=" * 60)

    try:
        from langchain import hub
    except ImportError:
        print("  ⚠️  无法导入 langchain hub，跳过")
        print("  （需要安装 langchain 并配置网络）\n")
        return

    try:
        # 从 Hub 拉取社区共享的 Prompt
        prompt = hub.pull("rlm/rag-prompt")
        print(f"  已从 Hub 加载：rlm/rag-prompt")
        print(f"  类型：{type(prompt).__name__}")
        print(f"  输入变量：{prompt.input_variables}\n")
    except Exception as e:
        print(f"  ⚠️  Hub 加载失败（需网络）：{e}\n")
        print("  Hub 用法示例：")
        print("    from langchain import hub")
        print('    prompt = hub.pull("rlm/rag-prompt")')
        print('    # 推送自己的 Prompt')
        print('    # hub.push("username/my-prompt", prompt)\n')


# ============================================================
# 7. 模板版本管理
# ============================================================
def demo_version_management():
    """模板版本管理实践"""
    print("=" * 60)
    print("【7】模板版本管理")
    print("=" * 60)

    from langchain_core.prompts import PromptTemplate

    # 模拟两个版本的 Prompt
    versions = {
        "v1.0": PromptTemplate.from_template("翻译：{text}"),
        "v2.0": PromptTemplate.from_template("请将以下文本翻译成英文，只输出翻译结果：\n{text}"),
    }

    # 保存两个版本
    for version, template in versions.items():
        path = TEMP_DIR / f"translate_prompt_{version}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(template.dict(), f, ensure_ascii=False, indent=2)
        print(f"  已保存 {version}：{path.name}")

    print("\n  版本管理实践：")
    print("    1. Prompt 文件与代码分离")
    print("    2. 用版本号命名文件（v1.0 / v2.0）")
    print("    3. 用 Git 管理 Prompt 变更")
    print("    4. 可做 A/B 测试对比效果\n")


# ============================================================
# 8. 与模型配合（从文件加载并调用）
# ============================================================
def demo_with_model():
    """从文件加载模板并与模型配合"""
    print("=" * 60)
    print("【8】从文件加载并与模型配合")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_core.prompts import load_prompt
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import StrOutputParser

    # 从 JSON 加载模板
    template = load_prompt(str(TEMP_DIR / "qa_prompt.json"))

    # 转为 ChatPromptTemplate
    from langchain_core.prompts import ChatPromptTemplate
    chat_prompt = ChatPromptTemplate.from_template(template.template)

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    parser = StrOutputParser()

    chain = chat_prompt | model | parser

    result = chain.invoke({
        "role": "客服助手",
        "style": "专业亲切",
        "question": "如何注册账号？",
    })
    print(f"  结果：{result}\n")


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    print("🚀 Day03 - 模板序列化与文件加载\n")

    demo_save_json()
    demo_load_json()
    demo_save_yaml()
    demo_load_yaml()
    demo_chat_prompt_serialize()
    demo_hub_pull()
    demo_version_management()
    demo_with_model()

    # 清理临时文件（可选）
    print("=" * 60)
    print("✅ 模板序列化演示完成")
    print(f"  模板文件保存在：{TEMP_DIR.resolve()}")
    print("总结：")
    print("  - JSON/YAML 序列化实现 Prompt 即代码")
    print("  - load_prompt 统一加载接口")
    print("  - PromptHub 可共享和复用社区 Prompt")
    print("  - 版本管理便于 A/B 测试和迭代")
    print("=" * 60)
