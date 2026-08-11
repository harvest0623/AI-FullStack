# 文件用途：环境检查与配置工具
# EnvironmentChecker 类：检查 Python 版本、已安装包、API Key 配置
# 生成 requirements.txt 和 .env 模板文件
# 运行：python 02_environment_setup.py

import sys
import os
import importlib
import platform
from pathlib import Path
from datetime import datetime

# 核心依赖清单（名称, 导入名）
CORE_PACKAGES = [
    ("langchain", "langchain"),
    ("langchain-core", "langchain_core"),
    ("langchain-openai", "langchain_openai"),
    ("langchain-community", "langchain_community"),
    ("python-dotenv", "dotenv"),
    ("pydantic", "pydantic"),
]

# 可选依赖清单
OPTIONAL_PACKAGES = [
    ("langchain-anthropic", "langchain_anthropic"),
    ("langchain-google-genai", "langchain_google_genai"),
    ("openai", "openai"),
    ("anthropic", "anthropic"),
    ("requests", "requests"),
]

# 需要检查的 API Key
API_KEYS = [
    ("OPENAI_API_KEY", "OpenAI GPT 系列模型"),
    ("ANTHROPIC_API_KEY", "Anthropic Claude 系列模型（可选）"),
    ("GOOGLE_API_KEY", "Google Gemini 系列模型（可选）"),
    ("LANGCHAIN_API_KEY", "LangSmith 追踪平台（可选）"),
    ("LANGCHAIN_TRACING_V2", "LangSmith 追踪开关（可选）"),
]


class EnvironmentChecker:
    """环境检查与配置工具类"""

    def __init__(self):
        self.results = {}      # 检查结果
        self.warnings = []      # 警告信息
        self.errors = []        # 错误信息

    # ============================================================
    # 1. 检查 Python 版本
    # ============================================================
    def check_python_version(self, min_version=(3, 10)):
        """检查 Python 版本是否满足最低要求"""
        print("【1】检查 Python 版本")
        print("-" * 50)

        version_info = sys.version_info
        current = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
        required = f"{min_version[0]}.{min_version[1]}"

        print(f"  当前版本：Python {current}")
        print(f"  最低要求：Python {required}+")
        print(f"  实现路径：{sys.executable}")
        print(f"  平台：{platform.platform()}")

        if version_info < min_version:
            self.errors.append(
                f"Python 版本过低：当前 {current}，需要 {required}+"
            )
            print(f"  ❌ 版本过低，请升级到 Python {required}+")
        else:
            print("  ✅ Python 版本满足要求")

        self.results["python_version"] = current
        print()

    # ============================================================
    # 2. 检查已安装的包
    # ============================================================
    def check_packages(self):
        """检查核心依赖和可选依赖是否安装"""
        print("【2】检查已安装的包")
        print("-" * 50)

        installed = {}
        missing_core = []

        # 检查核心依赖
        print("  核心依赖：")
        for pkg_name, import_name in CORE_PACKAGES:
            version = self._get_package_version(import_name)
            installed[pkg_name] = version
            if version:
                print(f"    ✅ {pkg_name:<25} {version}")
            else:
                print(f"    ❌ {pkg_name:<25} 未安装")
                missing_core.append(pkg_name)

        if missing_core:
            self.errors.append(
                f"缺少核心依赖：{', '.join(missing_core)}"
            )

        # 检查可选依赖
        print("\n  可选依赖：")
        for pkg_name, import_name in OPTIONAL_PACKAGES:
            version = self._get_package_version(import_name)
            installed[pkg_name] = version
            if version:
                print(f"    ✅ {pkg_name:<25} {version}")
            else:
                print(f"    ⚠️  {pkg_name:<25} 未安装（可选）")

        self.results["packages"] = installed
        print()

    def _get_package_version(self, import_name):
        """获取已安装包的版本号"""
        try:
            module = importlib.import_module(import_name)
            return getattr(module, "__version__", "已安装（无版本号）")
        except ImportError:
            return None

    # ============================================================
    # 3. 检查 API Key 配置
    # ============================================================
    def check_api_keys(self):
        """检查环境变量中的 API Key 配置"""
        print("【3】检查 API Key 配置")
        print("-" * 50)

        # 尝试从 .env 加载
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("  已从 .env 文件加载环境变量\n")
        except ImportError:
            print("  ⚠️  未安装 python-dotenv，仅检查系统环境变量\n")

        key_status = {}
        for key_name, description in API_KEYS:
            value = os.getenv(key_name)
            if value:
                # 只显示前 8 位，保护密钥安全
                masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "****"
                print(f"  ✅ {key_name:<25} 已配置（{masked}）")
                key_status[key_name] = True
            else:
                print(f"  ⚠️  {key_name:<25} 未配置 — {description}")
                key_status[key_name] = False

        if not key_status.get("OPENAI_API_KEY"):
            self.errors.append("未配置 OPENAI_API_KEY，无法调用 OpenAI 模型")

        self.results["api_keys"] = key_status
        print()

    # ============================================================
    # 4. 检查 LangChain 版本特性
    # ============================================================
    def check_langchain_features(self):
        """检查 LangChain 关键特性是否可用"""
        print("【4】检查 LangChain 关键特性")
        print("-" * 50)

        try:
            from langchain_core.runnables import Runnable
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser

            print(f"  ✅ Runnable 统一接口可用")
            print(f"  ✅ ChatPromptTemplate 可用")
            print(f"  ✅ StrOutputParser 可用")

            # 验证 LCEL 管道功能
            prompt = ChatPromptTemplate.from_template("测试 {topic}")
            model_placeholder = None  # 仅验证管道符语法，不真正实例化模型
            parser = StrOutputParser()

            # 验证 Runnable 的核心方法
            runnable_methods = ["invoke", "batch", "stream", "ainvoke"]
            for method in runnable_methods:
                assert hasattr(prompt, method), f"缺少 {method} 方法"
            print(f"  ✅ Runnable 四大方法（invoke/batch/stream/ainvoke）均存在")
            self.results["langchain_features"] = True

        except ImportError as e:
            self.errors.append(f"LangChain 核心组件导入失败：{e}")
            print(f"  ❌ 导入失败：{e}")
            self.results["langchain_features"] = False

        print()

    # ============================================================
    # 5. 生成 requirements.txt
    # ============================================================
    def generate_requirements(self, output_path="requirements.txt"):
        """生成 requirements.txt 文件"""
        print("【5】生成 requirements.txt")
        print("-" * 50)

        content = """# LangChain 学习项目依赖
# 生成时间：{timestamp}
# Python 版本要求：3.10+

# ===== 核心依赖 =====
langchain>=0.3.0
langchain-core>=0.3.0
langchain-openai>=0.2.0
langchain-community>=0.3.0
python-dotenv>=1.0.0
pydantic>=2.0.0

# ===== 可选依赖 =====
# langchain-anthropic>=0.2.0    # Claude 模型
# langchain-google-genai>=2.0.0  # Gemini 模型
# openai>=1.0.0                  # 直接调用 OpenAI SDK（对比用）
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        output_file = Path(output_path)
        output_file.write_text(content, encoding="utf-8")
        print(f"  ✅ 已生成：{output_file.resolve()}")
        print(f"     安装命令：pip install -r {output_path}")
        print()

    # ============================================================
    # 6. 生成 .env 模板
    # ============================================================
    def generate_env_template(self, output_path=".env.template"):
        """生成 .env 模板文件"""
        print("【6】生成 .env 模板")
        print("-" * 50)

        content = """# LangChain 项目环境变量配置
# 复制此文件为 .env 并填入真实的 API Key
# 生成时间：{timestamp}

# ===== OpenAI（必填）=====
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ===== Anthropic Claude（可选）=====
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx

# ===== Google Gemini（可选）=====
# GOOGLE_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx

# ===== 本地 Ollama（无需 Key，需先启动 ollama serve）=====
# OLLAMA_BASE_URL=http://localhost:11434/v1

# ===== LangSmith 追踪（可选，推荐生产环境开启）=====
# LANGCHAIN_API_KEY=lsv2_xxxxxxxx
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_PROJECT=chainqa
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        output_file = Path(output_path)
        output_file.write_text(content, encoding="utf-8")
        print(f"  ✅ 已生成：{output_file.resolve()}")
        print(f"     使用方法：复制为 .env 并填入真实 Key")
        print()

    # ============================================================
    # 7. 打印环境信息汇总
    # ============================================================
    def print_summary(self):
        """打印环境检查汇总报告"""
        print("=" * 60)
        print("环境检查汇总报告")
        print("=" * 60)

        # Python 版本
        print(f"\n📌 Python：{self.results.get('python_version', '未知')}")

        # 包安装情况
        packages = self.results.get("packages", {})
        installed_count = sum(1 for v in packages.values() if v)
        print(f"📌 已安装包：{installed_count}/{len(packages)}")

        # API Key 情况
        keys = self.results.get("api_keys", {})
        configured_count = sum(1 for v in keys.values() if v)
        print(f"📌 API Key：{configured_count}/{len(keys)} 已配置")

        # 特性支持
        features = self.results.get("langchain_features", False)
        print(f"📌 LangChain 核心特性：{'✅ 可用' if features else '❌ 不可用'}")

        # 警告与错误
        if self.warnings:
            print(f"\n⚠️  警告（{len(self.warnings)} 条）：")
            for w in self.warnings:
                print(f"   - {w}")

        if self.errors:
            print(f"\n❌ 错误（{len(self.errors)} 条）：")
            for e in self.errors:
                print(f"   - {e}")
            print("\n请修复以上错误后再运行 LangChain 程序。")
        else:
            print("\n✅ 环境检查通过，可以开始 LangChain 开发！")

        print("=" * 60)

    # ============================================================
    # 主运行方法
    # ============================================================
    def run_all_checks(self):
        """执行全部环境检查"""
        print("=" * 60)
        print("🔧 LangChain 开发环境检查工具")
        print(f"   检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        self.check_python_version()
        self.check_packages()
        self.check_api_keys()
        self.check_langchain_features()
        self.generate_requirements()
        self.generate_env_template()
        self.print_summary()


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    checker = EnvironmentChecker()
    checker.run_all_checks()
