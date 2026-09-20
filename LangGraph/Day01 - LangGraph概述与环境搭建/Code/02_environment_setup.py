# 文件用途：环境检查工具
# EnvironmentChecker 类用于：
#   1) 检查 Python 版本是否满足 3.10+
#   2) 检查 langgraph / langchain-openai 等依赖是否已安装及其版本
#   3) 触发一次真实导入，验证 langgraph 可正常 import
#   4) 检查 .env 中是否配置了 API Key
#   5) 生成 requirements.txt 与 .env 模板（方便快速搭环境）

import importlib
import platform
import sys
from pathlib import Path

# 用 python-dotenv 加载 .env；若未安装则给出友好提示而不崩溃
try:
    from dotenv import load_dotenv, find_dotenv
except ImportError:
    load_dotenv, find_dotenv = None, None

BASE_DIR = Path(__file__).resolve().parent

# 核心依赖清单（名称 -> 环境变量名 -> 是否需要 Key）
DEPENDENCY_CHECKS = [
    ("langgraph", "LangGraph 核心", False),
    ("langgraph.checkpoint", "LangGraph Checkpoint", False),
    ("langchain", "LangChain 核心", False),
    ("langchain_openai", "LangChain OpenAI", False),
    ("pydantic", "Pydantic", False),
    ("dotenv", "python-dotenv", False),
]

API_KEY_ENVS = [
    ("OPENAI_API_KEY", "OpenAI"),
    ("ANTHROPIC_API_KEY", "Anthropic"),
    ("DASHSCOPE_API_KEY", "DashScope（通义）"),
    ("MOONSHOT_API_KEY", "Moonshot（Kimi）"),
]


class EnvironmentChecker:
    """环境校验器：汇总打印版本、依赖、Key 状态，并可生成配置文件。"""

    def check_python(self) -> bool:
        """检查 Python 版本，要求 3.10+。"""
        v = sys.version_info
        ok = v >= (3, 10)
        print(f"[Python] {platform.python_version()}，{'满足 >=3.10 要求' if ok else '低于 3.10，请升级'}（推荐 3.11/3.12）")
        return ok

    def check_dependencies(self) -> dict:
        """逐个检查核心依赖是否可导入，返回 {包名: 版本|None}。"""
        print("\n[依赖检查]")
        results = {}
        for module, label, _ in DEPENDENCY_CHECKS:
            try:
                mod = importlib.import_module(module)
                version = getattr(mod, "__version__", "OK(无版本号)")
                print(f"  ✓ {label:<24} {version}")
                results[module] = str(version)
            except ImportError as exc:
                print(f"  ✗ {label:<24} 未安装/导入失败：{exc}")
                results[module] = None
        return results

    def check_api_keys(self) -> dict:
        """检查 .env 中是否配置了常见 API Key。"""
        print("\n[API Key 检查]")
        state = {}
        for env_name, label in API_KEY_ENVS:
            # 优先从 os.environ 读取；若 load_dotenv 可用则先加载 .env
            import os
            value = os.getenv(env_name)
            ok = bool(value and value.strip() not in ("", "sk-xxxx", "sk-your-key-here"))
            print(f"  {'✓' if ok else '✗'} {env_name:<24}（{label}）{'已配置' if ok else '未配置'}")
            state[env_name] = ok
        return state

    def load_env_file(self) -> None:
        """尝试加载 .env 文件。"""
        if load_dotenv is None:
            print("\n[.env 加载] python-dotenv 未安装，跳过。请先 pip install python-dotenv")
            return
        dotenv_path = find_dotenv()
        if dotenv_path:
            load_dotenv(dotenv_path)
            print(f"\n[.env 加载] 已加载 {dotenv_path}")
        else:
            print("\n[.env 加载] 未找到 .env 文件（可通过 generate_env_template 生成模板）")

    def generate_requirements(self, path: Path | None = None) -> Path:
        """生成 requirements.txt。"""
        target = path or (BASE_DIR.parent / "requirements.txt")
        content = (
            "langgraph>=0.2.0\n"
            "langgraph-checkpoint>=0.0.10\n"
            "langchain>=0.1.0\n"
            "langchain-openai>=0.1.0\n"
            "python-dotenv>=1.0.0\n"
            "pydantic>=2.0.0\n"
        )
        target.write_text(content, encoding="utf-8")
        print(f"[生成] {target}")
        return target

    def generate_env_template(self, path: Path | None = None) -> Path:
        """生成 .env 模板（含注释，填写后重命名为 .env 即可）。"""
        target = path or (BASE_DIR.parent / ".env")
        if target.exists():
            print(f"[跳过] {target} 已存在，为避免覆盖不重新生成。")
            return target
        content = (
            "# 至少配置一个 LLM API Key。把本文件另存为 .env（与 .env 模板同级的项目根目录）\n"
            "# OpenAI\n"
            "OPENAI_API_KEY=sk-xxxx\n"
            "# Anthropic（可选）\n"
            "# ANTHROPIC_API_KEY=sk-ant-xxxx\n"
            "# 阿里云通义千问（可选）：OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1\n"
            "# DASHSCOPE_API_KEY=sk-xxxx\n"
        )
        target.write_text(content, encoding="utf-8")
        print(f"[生成] {target}")
        return target


def main() -> None:
    print("=" * 56)
    print("GraphFlow - LangGraph 环境检查工具 (Day01)")
    print("=" * 56)

    checker = EnvironmentChecker()
    checker.load_env_file()
    checker.check_python()
    checker.check_dependencies()
    checker.check_api_keys()

    print("\n" + "=" * 56)
    print("生成配置文件")
    print("=" * 56)
    checker.generate_requirements()
    checker.generate_env_template()

    print("\n" + "=" * 56)
    print("验证 langgraph 可导入：")
    print("=" * 56)
    import langgraph
    print(f"  langgraph 导入成功，版本 = {langgraph.__version__}")

    print("\n完成。若所有依赖均为 ✓ 且已配置 Key，即可开始 Day01 后续示例。")


if __name__ == "__main__":
    main()