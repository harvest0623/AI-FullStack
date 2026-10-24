# -*- coding: utf-8 -*-
"""
Day02 - 03 模型管理器（ModelManager）

把模型管理封装成 Python 类：
  - list()            列出所有模型
  - search(keyword)   按关键词过滤
  - show(name)        查看详情
  - disk_summary()    磁盘占用汇总
  - remove(name)      删除模型（模拟）

双模式：有 Ollama 走真实 API，无则用内置示例数据。
"""

import os
import sys
import json
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(__file__))
from ollama_util import is_ollama_available, list_local_models


# ---------------- 示例数据（无环境时） ----------------
DEMO_MODELS = [
    {"name": "llama3.1:latest", "size": 4693779555, "parameter": "8.0B", "quant": "Q4_K_M", "family": "llama"},
    {"name": "qwen2.5:latest", "size": 4693779555, "parameter": "7.6B", "quant": "Q4_K_M", "family": "qwen2"},
    {"name": "nomic-embed-text:latest", "size": 274000000, "parameter": "137M", "quant": "F16", "family": "bert"},
    {"name": "tinyllama:latest", "size": 637000000, "parameter": "1.1B", "quant": "Q4_0", "family": "llama"},
]


def _fmt(n):
    if n >= 1 << 30:
        return f"{n / (1 << 30):.2f}GB"
    if n >= 1 << 20:
        return f"{n / (1 << 20):.1f}MB"
    return f"{n}B"


@dataclass
class ModelManager:
    """模型管理器：环境无关（真实 API / 示例数据自动切换）"""

    def _all(self) -> list[dict]:
        if is_ollama_available("llama3.1"):
            # 真实：从 /api/tags 取，缺少字段填充未知
            return [{"name": m, "size": -1, "parameter": "?", "quant": "?", "family": "?"}
                    for m in list_local_models()]
        return DEMO_MODELS

    def list(self) -> None:
        print(f"{'模型名称':<28}{'大小':<10}{'参数量':<10}{'量化':<8}{'家族'}")
        print("-" * 68)
        for m in self._all():
            print(f"{m['name']:<28}{_fmt(m['size']):<10}{m['parameter']:<10}"
                  f"{m['quant']:<8}{m['family']}")
        total = sum(m['size'] for m in self._all() if m['size'] > 0)
        print(f"\n共 {len(self._all())} 个模型，合计约 {_fmt(total)}")

    def search(self, keyword: str) -> None:
        hits = [m for m in self._all() if keyword.lower() in m["name"].lower()
                or keyword.lower() in m["family"].lower()]
        print(f"关键词「{keyword}」匹配到 {len(hits)} 个模型：")
        for m in hits:
            print(f"   - {m['name']}  {_fmt(m['size'])}  ({m['parameter']}, {m['quant']})")
        if not hits:
            print("   （无匹配）")

    def show(self, name: str) -> None:
        info = next((m for m in self._all() if m["name"].split(":")[0] == name.split(":")[0]), None)
        if not info:
            print(f"  未找到模型 {name}")
            return
        print(f"  详情：{info['name']}")
        for k, v in info.items():
            if v in ("?", 0):
                v = "未知"
            print(f"     {k:<10} {v if k!='size' else _fmt(v)}")

    def disk_summary(self) -> dict:
        """按家族/量化汇总磁盘占用"""
        total = 0
        by_family: dict[str, int] = {}
        for m in self._all():
            if m["size"] <= 0:
                continue
            total += m["size"]
            by_family[m["family"]] = by_family.get(m["family"], 0) + m["size"]
        print("磁盘占用汇总：")
        for fam, sz in sorted(by_family.items(), key=lambda x: -x[1]):
            print(f"   {fam:<10} {_fmt(sz)}")
        print(f"   合计：{_fmt(total)}")
        return {"total": total, "by_family": by_family}

    def remove(self, name: str) -> str:
        if is_ollama_available(name):
            return f"真实环境：请用命令 `ollama rm {name}` 完成删除（保留教学程序无副作用）"
        print(f"   [模拟] 删除模型 {name} ...")
        return f"    -> 已删除（模拟）。真实环境用 `ollama rm {name}`"


def main():
    print(">>> ModelManager 演示（真实/模拟双模式）\n")
    mgr = ModelManager()

    print("=" * 60)
    print("01 列表 list()")
    print("=" * 60)
    mgr.list()

    print("\n" + "=" * 60)
    print("02 搜索 search('qwen')")
    print("=" * 60)
    mgr.search("qwen")

    print("\n" + "=" * 60)
    print("03 详情 show('llama3.1')")
    print("=" * 60)
    mgr.show("llama3.1")

    print("\n" + "=" * 60)
    print("04 磁盘汇总 disk_summary()")
    print("=" * 60)
    mgr.disk_summary()

    print("\n" + "=" * 60)
    print("05 删除 remove('tinyllama')")
    print("=" * 60)
    print(mgr.remove("tinyllama"))


if __name__ == "__main__":
    main()