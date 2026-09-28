# 文件用途：Prompt 管理器
# PromptManager 类：从 YAML 文件加载多个模板，支持渲染 / 版本管理 / 缓存 /
# 模板继承与组合 / 变更日志记录 / 版本回滚。展示完整的模板生命周期管理。
# 运行前：pip install jinja2 pyyaml

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, meta


@dataclass
class PromptVersion:
    """单个版本记录。"""

    version: str
    date: str
    change: str
    reason: str


@dataclass
class ManagedPrompt:
    """被管理的 Prompt：含模板正文、元数据、版本历史。"""

    name: str
    template: str
    version: str = "1.0.0"
    metadata: dict = field(default_factory=dict)
    changelog: list[PromptVersion] = field(default_factory=list)

    def add_version(self, new_version: str, change: str, reason: str, new_template: str | None = None) -> None:
        """记录一次版本变更。"""
        self.changelog.append(
            PromptVersion(
                version=self.version,
                date=datetime.now().strftime("%Y-%m-%d"),
                change=change,
                reason=reason,
            )
        )
        self.version = new_version
        if new_template is not None:
            self.template = new_template


class PromptManager:
    """
    Prompt 管理器。

    使用方式：
        manager = PromptManager()
        manager.load_from_yaml("prompts/templates.yaml")
        prompt = manager.render("qa", question="怎么退款？")
        manager.update("qa", "1.1.0", "增加 tone", "支持语气", new_template="...")
        manager.rollback("qa")  # 回到上一个版本
    """

    def __init__(self, templates_dir: str | Path | None = None) -> None:
        self._prompts: dict[str, ManagedPrompt] = {}
        self._cache: dict[str, str] = {}  # 内容哈希缓存
        self._templates_dir = Path(templates_dir) if templates_dir else None
        # Jinja2 环境：若指定目录则用 FileSystemLoader 支持继承
        if self._templates_dir:
            self._env = Environment(
                loader=FileSystemLoader(str(self._templates_dir)),
                undefined=StrictUndefined,
                keep_trailing_newline=True,
                autoescape=False,
            )
        else:
            self._env = Environment(undefined=StrictUndefined, autoescape=False)

    # ------------------------- 加载 -------------------------
    def load_from_yaml(self, file_path: str | Path) -> None:
        """从 YAML 文件批量加载模板。结构：
        qa:
          version: "1.0.0"
          model: gpt-4o-mini
          template: |
            你是客服，回答：{{question}}
          changelog:
            - version: "1.0.0"
              date: "2025-01-01"
              change: "初始版本"
              reason: "首次上线"
        """
        data = yaml.safe_load(Path(file_path).read_text(encoding="utf-8"))
        for name, item in (data or {}).items():
            changelog = [
                PromptVersion(
                    version=c.get("version", ""),
                    date=c.get("date", ""),
                    change=c.get("change", ""),
                    reason=c.get("reason", ""),
                )
                for c in item.get("changelog", [])
            ]
            mp = ManagedPrompt(
                name=name,
                template=item.get("template", ""),
                version=item.get("version", "1.0.0"),
                metadata={k: v for k, v in item.items() if k not in {"template", "version", "changelog"}},
                changelog=changelog,
            )
            self._prompts[name] = mp
        # 加载后清缓存
        self._cache.clear()

    def register(self, name: str, template: str, version: str = "1.0.0", metadata: dict | None = None) -> None:
        """直接注册一个模板（不经文件）。"""
        self._prompts[name] = ManagedPrompt(
            name=name, template=template, version=version, metadata=metadata or {}
        )
        self._cache.clear()

    # ------------------------- 渲染（带缓存） -------------------------
    def render(self, name: str, **kwargs) -> str:
        """渲染指定模板，命中缓存则直接返回。"""
        if name not in self._prompts:
            raise KeyError(f"模板 {name!r} 不存在，已注册：{list(self._prompts)}")
        mp = self._prompts[name]
        # 计算缓存 key：模板正文 + 版本 + 变量
        var_key = json.dumps(kwargs, sort_keys=True, ensure_ascii=False, default=str)
        raw = f"{mp.template}|{mp.version}|{var_key}"
        key = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        if key in self._cache:
            return self._cache[key]
        template = self._env.from_string(mp.template)
        result = template.render(**kwargs)
        self._cache[key] = result
        return result

    # ------------------------- 版本管理 -------------------------
    def update(self, name: str, new_version: str, change: str, reason: str, new_template: str | None = None) -> None:
        """更新模板版本，自动记录变更日志。"""
        if name not in self._prompts:
            raise KeyError(f"模板 {name!r} 不存在")
        self._prompts[name].add_version(new_version, change, reason, new_template)
        # 模板变更 → 清缓存
        self._cache.clear()

    def rollback(self, name: str) -> PromptVersion | None:
        """回滚到上一个版本（仅当 changelog 非空）。"""
        if name not in self._prompts:
            raise KeyError(f"模板 {name!r} 不存在")
        mp = self._prompts[name]
        if not mp.changelog:
            return None
        last = mp.changelog.pop()
        mp.version = last.version
        # 注意：仅回滚版本号与日志，模板正文需调用方提供
        self._cache.clear()
        return last

    def diff(self, name: str, other_template: str) -> str:
        """简单 diff：返回模板正文与 other 的差异（按行）。"""
        if name not in self._prompts:
            raise KeyError(f"模板 {name!r} 不存在")
        old_lines = self._prompts[name].template.splitlines()
        new_lines = other_template.splitlines()
        result: list[str] = []
        for i in range(max(len(old_lines), len(new_lines))):
            o = old_lines[i] if i < len(old_lines) else None
            n = new_lines[i] if i < len(new_lines) else None
            if o == n:
                continue
            if o is not None:
                result.append(f"- {o}")
            if n is not None:
                result.append(f"+ {n}")
        return "\n".join(result) if result else "(无差异)"

    # ------------------------- 查询 -------------------------
    def list_prompts(self) -> list[str]:
        return list(self._prompts)

    def get(self, name: str) -> ManagedPrompt:
        return self._prompts[name]

    def cache_stats(self) -> dict:
        return {"size": len(self._cache), "keys": list(self._cache.keys())[:5]}

    def clear_cache(self) -> None:
        self._cache.clear()


# ---------------------------------------------------------------------------
# 演示入口：完整生命周期
# ---------------------------------------------------------------------------
DEMO_YAML = """
qa:
  version: "1.0.0"
  model: gpt-4o-mini
  temperature: 0.3
  template: |
    你是 AISearch 客服，请用专业的语气回答：{{question}}
  changelog:
    - version: "1.0.0"
      date: "2025-01-01"
      change: "初始版本"
      reason: "首次上线"

summarize:
  version: "1.0.0"
  model: gpt-4o
  temperature: 0.2
  template: |
    请用 100 字总结以下文本：{{text}}
  changelog: []
"""


def demo() -> None:
    # 1. 写出 demo YAML 到临时文件
    tmp = Path("demo_prompts.yaml")
    tmp.write_text(DEMO_YAML.strip(), encoding="utf-8")

    try:
        manager = PromptManager()
        manager.load_from_yaml(tmp)

        print("=" * 60)
        print("已加载模板：", manager.list_prompts())

        # 2. 渲染
        print("\n--- 渲染 qa ---")
        out1 = manager.render("qa", question="怎么退款？")
        print(out1)
        # 第二次相同输入 → 命中缓存
        out2 = manager.render("qa", question="怎么退款？")
        print(f"\n第二次渲染相同（命中缓存）：{out1 == out2}")
        print("缓存统计：", manager.cache_stats())

        # 3. 版本更新
        print("\n--- 版本更新：qa 升到 1.1.0，新增 tone 变量 ---")
        new_tpl = "你是 AISearch 客服，请用{{tone | default('专业')}}的语气回答：{{question}}"
        manager.update("qa", "1.1.0", "新增 tone 变量", "支持多语气切换", new_template=new_tpl)
        print("新版本号：", manager.get("qa").version)
        print("渲染：", manager.render("qa", question="退款", tone="亲切"))

        # 4. diff
        print("\n--- diff 对比 ---")
        print(manager.diff("qa", "你是 AISearch 客服，回答：{{question}}"))

        # 5. 回滚
        print("\n--- 回滚到上一版本 ---")
        last = manager.rollback("qa")
        print(f"回滚到：{last.version if last else None}")
        print("当前版本：", manager.get("qa").version)
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    demo()
