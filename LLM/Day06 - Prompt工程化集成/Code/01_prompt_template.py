# 文件用途：Prompt 模板系统
# PromptTemplate 类：基于 Jinja2 实现，支持变量插值 / 条件逻辑 / 循环 / 默认值。
# 支持从字符串、文件加载模板。包含模板渲染示例与元数据管理。
# 运行前：pip install jinja2

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template, meta


@dataclass
class PromptTemplate:
    """
    Prompt 模板封装。

    使用方式：
        t = PromptTemplate.from_string("你是 {{role}}，回答：{{question}}")
        prompt = t.render(role="客服", question="怎么退款？")

        t = PromptTemplate.from_file("prompts/qa.j2")
        prompt = t.render(question="怎么退款？")
    """

    template_str: str
    name: str = ""
    # 元数据：可记录 model / temperature / variables 等
    metadata: dict = field(default_factory=dict)
    # Jinja2 环境（用于继承 / include）
    _env: Environment | None = None

    def __post_init__(self) -> None:
        if self._env is None:
            # 默认环境：允许未定义变量（用 default 过滤器兜底）
            self._env = Environment(
                undefined=StrictUndefined,  # 严格模式：未定义变量直接报错，便于发现 bug
                keep_trailing_newline=True,
                autoescape=False,
            )

    # ------------------------- 工厂方法 -------------------------
    @classmethod
    def from_string(cls, template_str: str, name: str = "", metadata: dict | None = None) -> "PromptTemplate":
        return cls(template_str=template_str, name=name, metadata=metadata or {})

    @classmethod
    def from_file(cls, file_path: str | Path, name: str | None = None, metadata: dict | None = None) -> "PromptTemplate":
        """从文件加载模板。若文件包含 frontmatter（--- ... ---），自动解析元数据。"""
        path = Path(file_path)
        content = path.read_text(encoding="utf-8")
        meta_dict = dict(metadata or {})
        # 简单 frontmatter 解析
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                front = parts[1].strip()
                body = parts[2].lstrip("\n")
                # 解析 key: value 形式
                for line in front.splitlines():
                    if ":" in line:
                        k, _, v = line.partition(":")
                        meta_dict[k.strip()] = v.strip()
                content = body
        return cls(template_str=content, name=name or path.stem, metadata=meta_dict)

    # ------------------------- 渲染 -------------------------
    def render(self, **kwargs) -> str:
        """渲染模板，传入变量。"""
        template = self._env.from_string(self.template_str)
        return template.render(**kwargs)

    def render_safe(self, **kwargs) -> str:
        """宽松渲染：未定义变量用默认值或空串，不报错。"""
        env = Environment(autoescape=False, keep_trailing_newline=True)
        template = env.from_string(self.template_str)
        return template.render(**kwargs)

    # ------------------------- 变量分析 -------------------------
    def required_variables(self) -> set[str]:
        """返回模板中引用的所有变量名（静态分析）。"""
        ast = self._env.parse(self.template_str)
        return meta.find_undeclared_variables(ast)

    def validate_variables(self, provided: dict) -> list[str]:
        """检查必需变量是否都提供，返回缺失变量列表。"""
        required = self.required_variables()
        # 排除带 default 过滤的变量（粗略判断）
        missing = []
        for var in required:
            if var not in provided and f"{var}|default" not in self.template_str:
                missing.append(var)
        return missing

    # ------------------------- 元数据访问 -------------------------
    @property
    def model(self) -> str:
        return self.metadata.get("model", "")

    @property
    def temperature(self) -> float:
        return float(self.metadata.get("temperature", "0.7"))


# ---------------------------------------------------------------------------
# 演示入口
# ---------------------------------------------------------------------------
def demo() -> None:
    print("=" * 60)
    print("示例 1：基础变量插值 + 默认值")
    print("=" * 60)
    t1 = PromptTemplate.from_string(
        "你是{{role}}，请用{{tone | default('专业')}}的语气回答：{{question}}"
    )
    print(t1.render(role="客服", question="怎么退款？"))
    print("必需变量：", t1.required_variables())

    print("\n" + "=" * 60)
    print("示例 2：条件逻辑（VIP / 普通用户）")
    print("=" * 60)
    t2 = PromptTemplate.from_string(
        "{% if is_vip %}您是 VIP 用户，享受 7x24 专属服务。\n"
        "{% else %}您好，请描述您的问题。\n{% endif %}"
        "问题：{{question}}"
    )
    print("【VIP】")
    print(t2.render(is_vip=True, question="退款"))
    print("【普通】")
    print(t2.render(is_vip=False, question="退款"))

    print("\n" + "=" * 60)
    print("示例 3：循环（Few-Shot 示例）")
    print("=" * 60)
    t3 = PromptTemplate.from_string(
        "请对用户输入进行情感分类。\n"
        "{% for ex in examples %}"
        "输入：{{ex.input}}\n标签：{{ex.label}}\n"
        "{% endfor %}"
        "输入：{{input}}\n标签："
    )
    print(t3.render(
        examples=[
            {"input": "今天很开心", "label": "正面"},
            {"input": "快递丢了", "label": "负面"},
        ],
        input="一般般",
    ))

    print("=" * 60)
    print("示例 4：变量校验")
    print("=" * 60)
    t4 = PromptTemplate.from_string("角色：{{role}}，问题：{{question}}，语气：{{tone}}")
    missing = t4.validate_variables({"role": "客服"})  # 缺 question / tone
    print("缺失变量：", missing)


if __name__ == "__main__":
    demo()
