# -*- coding: utf-8 -*-
"""
文件用途：LlamaIndex 环境检查工具
---------------------------------
用于检查当前环境是否满足 LlamaIndex 开发要求：
1. Python 版本是否满足 3.10+
2. llama_index 核心包是否安装及其版本
3. 已安装的常用集成包
4. API Key 是否配置
5. 自动生成 requirements.txt 与 .env 模板
6. 验证 llama_index 可正常导入并打印版本

EnvironmentChecker 类封装了全部检查逻辑。

运行：
    python 02_environment_setup.py
"""
import os
import sys
import platform
from pathlib import Path

# 检测 dotenv 是否可用；若不可用则不加载，仅提示
try:
    from dotenv import load_dotenv

    load_dotenv()
    HAS_DOTENV = True
except ImportError:  # pragma: no cover
    HAS_DOTENV = False

# .env 模板（供用户新建 API Key 配置时参考）
ENV_TEMPLATE = """# -------------------------------
# LlamaIndex API Key 配置模板
# -------------------------------
# 复制此文件为 .env 并填写你的 Key
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
# 可选：使用代理时配置
# OPENAI_BASE_URL=https://api.openai.com/v1
"""

# 建议安装的依赖清单
REQUIREMENTS_TXT = """# LlamaIndex 阶段一：数据基础 依赖清单
# 安装：pip install -r requirements.txt
llama-index
llama-index-readers-file
llama-index-readers-web
llama-index-llms-openai
llama-index-embeddings-openai
python-dotenv
pydantic
"""

# 需要探测的常用集成包
PACKAGES_TO_CHECK = [
    "llama_index",
    "llama_index.readers.file",
    "llama_index.readers.web",
    "llama_index.llms.openai",
    "llama_index.embeddings.openai",
    "llama_index.vector_stores.chroma",
    "dotenv",
    "pydantic",
]


class EnvironmentChecker:
    """LlamaIndex 环境检查器：逐项检查环境并输出报告。"""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir  # 生成文件的目标目录

    # ---------- 1. Python 版本检查 ----------
    @staticmethod
    def check_python() -> dict:
        version = platform.python_version()
        major, minor, *_ = sys.version_info
        ok = (major, minor) >= (3, 10)
        return {"name": "Python 版本", "value": version, "ok": ok,
                "detail": "需 >= 3.10"}

    # ---------- 2. llama_index 导入与版本 ----------
    @staticmethod
    def check_llama_index() -> dict:
        try:
            import llama_index
            version = getattr(llama_index, "__version__", "未知")
            return {"name": "llama_index", "value": version, "ok": True,
                    "detail": "导入成功"}
        except Exception as e:  # noqa: BLE001
            return {"name": "llama_index", "value": "未安装", "ok": False,
                    "detail": str(e)}

    # ---------- 3. 集成包检查 ----------
    @staticmethod
    def check_integrations() -> dict:
        checks = {}
        for pkg in PACKAGES_TO_CHECK:
            try:
                __import__(pkg)
                checks[pkg] = True
            except Exception:  # noqa: BLE001
                checks[pkg] = False
        return checks

    # ---------- 4. API Key 检查 ----------
    @staticmethod
    def check_api_key() -> dict:
        keys = ["OPENAI_API_KEY"]
        found = {k: bool(os.getenv(k)) for k in keys}
        return {
            "name": "API Key",
            "configured": found,
            "ok": any(found.values()),
            "detail": "至少配置一个 LLM 服务的 API Key",
        }

    # ---------- 5. 生成 requirements.txt ----------
    def generate_requirements(self) -> Path:
        path = self.project_dir / "requirements.txt"
        path.write_text(REQUIREMENTS_TXT, encoding="utf-8")
        print(f"  ✔ 已生成 {path.name}（{len(REQUIREMENTS_TXT.splitlines())} 行）")
        return path

    # ---------- 6. 生成 .env 模板 ----------
    def generate_env_template(self) -> Path:
        path = self.project_dir / ".env.example"
        # 仅当文件不存在时生成，避免覆盖已有配置
        if not path.exists():
            path.write_text(ENV_TEMPLATE, encoding="utf-8")
            print(f"  ✔ 已生成 {path.name}（请复制为 .env 并填写 Key）")
        else:
            print(f"  - {path.name} 已存在，跳过。")
        return path

    # ---------- 汇总运行 ----------
    def run(self) -> None:
        print("=" * 64)
        print("LlamaIndex 环境检查报告")
        print("=" * 64)

        # 1) Python
        py = self.check_python()
        print(f"\n[1] {py['name']}: {py['value']} （要求 {py['detail']}）"
              f" => {'✔ 通过' if py['ok'] else '✘ 不满足'}")

        # 2) llama_index
        li = self.check_llama_index()
        if not li["ok"]:
            print(f"\n[2] {li['name']}: {li['value']} => ✘ 未安装")
            print("    请执行：pip install llama-index")
        else:
            print(f"\n[2] {li['name']} 版本: {li['value']} => ✔ 已安装")

        # 3) 集成包
        print("\n[3] 常用集成包探测：")
        integ = self.check_integrations()
        for pkg, ok in integ.items():
            print(f"    - {pkg:<40} {'✔' if ok else '—'}")
        missing = [p for p, ok in integ.items() if not ok]
        if missing:
            print(f"    提示：缺失部分包，可按 by requirements 安装。")

        # 4) API Key
        key = self.check_api_key()
        print(f"\n[4] {key['name']}: {key['configured']}")
        print(f"    => {'✔ 已配置' if key['ok'] else '✘ 未配置（仅影响在线联网功能）'}")

        # 5) 生成模板文件
        print("\n[5] 生成必需的配置文件：")
        print(f"    项目目录：{self.project_dir}")
        self.generate_requirements()
        self.generate_env_template()

        # 6) 汇总结论
        print("\n" + "-" * 64)
        issues = []
        if not py["ok"]:
            issues.append("Python 版本需 >= 3.10")
        if not li["ok"]:
            issues.append("未安装 llama_index")
        if not key["ok"]:
            issues.append("未配置 API Key")
        if issues:
            print("发现待处理项：")
            for it in issues:
                print(f"  - {it}")
        else:
            print("环境整体检查通过，可以开始 LlamaIndex 之旅！🎉")
        print("-" * 64)


if __name__ == "__main__":
    if not HAS_DOTENV:
        print("[提示] 未检测到 python-dotenv，无法自动加载 .env。")
        print("       建议安装：pip install python-dotenv")
    checker = EnvironmentChecker(project_dir=Path(__file__).parent)
    checker.run()