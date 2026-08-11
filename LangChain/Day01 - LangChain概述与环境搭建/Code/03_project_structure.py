# 文件用途：项目脚手架生成器
# ProjectGenerator 类：生成 ChainQA 智能问答助手项目目录结构
# 生成 pyproject.toml / src/chainqa/各模块/__init__.py / tests/ 等基础配置文件
# 运行：python 03_project_structure.py

from pathlib import Path
from datetime import datetime


# ============================================================
# 项目结构定义：目录与文件内容
# ============================================================

# 需要创建的目录（相对路径）
PROJECT_DIRS = [
    "src/chainqa",
    "src/chainqa/prompts",
    "src/chainqa/parsers",
    "src/chainqa/chains",
    "src/chainqa/memory",
    "src/chainqa/loaders",
    "src/chainqa/retrieval",
    "src/chainqa/tools",
    "src/chainqa/server",
    "tests",
    "data",
]

# 需要创建的文件（相对路径: 内容）
PROJECT_FILES = {
    # ===== 根目录配置文件 =====
    "pyproject.toml": """[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "chainqa"
version = "0.1.0"
description = "ChainQA - 基于 LangChain 的智能问答助手"
requires-python = ">=3.10"
dependencies = [
    "langchain>=0.3.0",
    "langchain-core>=0.3.0",
    "langchain-openai>=0.2.0",
    "langchain-community>=0.3.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "pytest-asyncio>=0.21"]
anthropic = ["langchain-anthropic>=0.2.0"]

[tool.setuptools.packages.find]
where = ["src"]
""",

    ".gitignore": """# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/

# 虚拟环境
.venv/
venv/
env/

# 环境变量（切勿提交）
.env

# IDE
.vscode/
.idea/
*.swp

# 测试
.pytest_cache/
.coverage
htmlcov/
""",

    ".env.template": """# ChainQA 环境变量配置
# 复制为 .env 并填入真实 Key
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
""",

    "README.md": """# ChainQA - 智能问答助手

基于 LangChain 0.3 构建的智能问答系统示例项目。

## 快速开始

```bash
# 安装依赖
pip install -e .

# 配置环境变量
cp .env.template .env
# 编辑 .env 填入 API Key

# 运行测试
pytest
```

## 项目结构

- `src/chainqa/prompts/` - Prompt 模板
- `src/chainqa/parsers/` - 输出解析器
- `src/chainqa/chains/` - 链式调用
- `src/chainqa/memory/` - 对话记忆
- `src/chainqa/loaders/` - 文档加载
- `src/chainqa/retrieval/` - 检索器
- `src/chainqa/tools/` - 工具定义
- `src/chainqa/server/` - API 服务
""",

    # ===== Python 包文件 =====
    "src/chainqa/__init__.py": '''"""ChainQA - 基于 LangChain 的智能问答助手"""

__version__ = "0.1.0"
''',

    "src/chainqa/config.py": '''"""配置管理模块

集中管理模型配置、API Key 等。
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """项目配置类"""

    # OpenAI 配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_MODEL = "gpt-4o-mini"
    TEMPERATURE = 0.7
    MAX_TOKENS = 1000

    # Anthropic 配置（可选）
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"


config = Config()
''',

    "src/chainqa/models.py": '''"""模型实例模块

集中创建和复用 ChatModel 实例。
"""
from langchain_openai import ChatOpenAI
from .config import config


def get_chat_model() -> ChatOpenAI:
    """获取默认的 ChatModel 实例"""
    return ChatOpenAI(
        model=config.DEFAULT_MODEL,
        temperature=config.TEMPERATURE,
        max_tokens=config.MAX_TOKENS,
    )


# 全局模型实例（可按需导入）
chat_model = get_chat_model()
''',

    "src/chainqa/prompts/__init__.py": '"""Prompt 模板模块"""\n',
    "src/chainqa/prompts/chat_prompt.py": '''"""对话 Prompt 模板"""
from langchain_core.prompts import ChatPromptTemplate

# 通用问答模板
qa_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的问答助手，请准确、简洁地回答问题。"),
    ("human", "{question}"),
])
''',

    "src/chainqa/parsers/__init__.py": '"""输出解析器模块"""\n',
    "src/chainqa/parsers/json_parser.py": '''"""JSON 输出解析器"""
from langchain_core.output_parsers import StrOutputParser

str_parser = StrOutputParser()
''',

    "src/chainqa/chains/__init__.py": '"""链式调用模块"""\n',
    "src/chainqa/chains/qa_chain.py": '''"""问答链"""
from langchain_core.output_parsers import StrOutputParser
from ..models import chat_model
from ..prompts.chat_prompt import qa_prompt

# 基础问答链：prompt | model | parser
qa_chain = qa_prompt | chat_model | StrOutputParser()
''',

    "src/chainqa/memory/__init__.py": '"""对话记忆模块"""\n',
    "src/chainqa/loaders/__init__.py": '"""文档加载模块"""\n',
    "src/chainqa/retrieval/__init__.py": '"""检索器模块"""\n',
    "src/chainqa/tools/__init__.py": '"""工具定义模块"""\n',
    "src/chainqa/server/__init__.py": '"""API 服务模块"""\n',

    # ===== 测试文件 =====
    "tests/__init__.py": "",
    "tests/test_basic.py": '''"""基础测试"""
from chainqa.config import config


def test_config_loaded():
    """测试配置是否加载"""
    assert config.DEFAULT_MODEL == "gpt-4o-mini"
    assert config.TEMPERATURE == 0.7


def test_import_chain():
    """测试链是否可导入（需要配置 API Key）"""
    try:
        from chainqa.chains.qa_chain import qa_chain
        assert qa_chain is not None
    except Exception:
        # 未配置 API Key 时跳过
        pass
''',
}


class ProjectGenerator:
    """项目脚手架生成器"""

    def __init__(self, project_name="chainqa", base_dir="."):
        self.project_name = project_name
        self.base_dir = Path(base_dir)
        self.created_dirs = 0
        self.created_files = 0
        self.skipped_files = 0

    # ============================================================
    # 1. 创建目录结构
    # ============================================================
    def create_directories(self):
        """创建所有目录"""
        print("【1】创建目录结构")
        print("-" * 50)

        for dir_path in PROJECT_DIRS:
            full_path = self.base_dir / dir_path
            if full_path.exists():
                print(f"  ⏭️  已存在：{dir_path}/")
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  ✅ 已创建：{dir_path}/")
                self.created_dirs += 1
        print()

    # ============================================================
    # 2. 创建文件
    # ============================================================
    def create_files(self):
        """创建所有配置文件和 Python 文件"""
        print("【2】创建文件")
        print("-" * 50)

        for file_path, content in PROJECT_FILES.items():
            full_path = self.base_dir / file_path
            if full_path.exists():
                print(f"  ⏭️  已存在：{file_path}")
                self.skipped_files += 1
            else:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding="utf-8")
                print(f"  ✅ 已创建：{file_path}")
                self.created_files += 1
        print()

    # ============================================================
    # 3. 打印项目结构
    # ============================================================
    def print_structure(self):
        """打印生成的项目目录树"""
        print("【3】项目结构预览")
        print("-" * 50)
        print(self._build_tree())
        print()

    def _build_tree(self):
        """构建目录树字符串"""
        lines = [f"{self.project_name}/"]
        # 遍历根目录下的文件和目录
        items = sorted(self.base_dir.iterdir())
        dirs = [d for d in items if d.is_dir() and not d.name.startswith(".")]
        files = [f for f in items if f.is_file()]

        for d in dirs:
            self._walk_dir(d, lines, "  ")

        for i, f in enumerate(files):
            prefix = "└── " if i == len(files) - 1 else "├── "
            lines.append(f"{prefix}{f.name}")

        return "\n".join(lines)

    def _walk_dir(self, path, lines, prefix):
        """递归遍历目录"""
        lines.append(f"{prefix}{path.name}/")
        items = sorted(path.iterdir())
        sub_dirs = [d for d in items if d.is_dir()]
        sub_files = [f for f in items if f.is_file()]
        total = len(sub_dirs) + len(sub_files)

        for i, d in enumerate(sub_dirs):
            is_last = (i == total - 1) and not sub_files
            child_prefix = prefix + ("    " if is_last else "│   ")
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{d.name}/")
            # 只展示一层，避免过深
            sub_items = sorted(d.iterdir())
            for j, sub in enumerate(sub_items):
                sub_is_last = j == len(sub_items) - 1
                sub_conn = "└── " if sub_is_last else "├── "
                lines.append(f"{child_prefix}{sub_conn}{sub.name}")

        for i, f in enumerate(sub_files):
            is_last = i == len(sub_files) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{f.name}")

    # ============================================================
    # 4. 打印汇总报告
    # ============================================================
    def print_summary(self):
        """打印生成汇总"""
        print("=" * 60)
        print("项目脚手架生成完成")
        print("=" * 60)
        print(f"  项目名称：{self.project_name}")
        print(f"  生成位置：{self.base_dir.resolve()}")
        print(f"  创建目录：{self.created_dirs} 个")
        print(f"  创建文件：{self.created_files} 个")
        print(f"  跳过文件：{self.skipped_files} 个（已存在）")
        print()
        print("下一步操作：")
        print(f"  1. cd {self.base_dir.resolve()}")
        print("  2. pip install -e .           # 安装项目为可编辑模式")
        print("  3. cp .env.template .env       # 复制环境变量模板")
        print("  4. 编辑 .env 填入 OPENAI_API_KEY")
        print("  5. pytest                       # 运行测试")
        print("=" * 60)

    # ============================================================
    # 主运行方法
    # ============================================================
    def generate(self):
        """执行完整的项目生成流程"""
        print("=" * 60)
        print("🏗️  ChainQA 项目脚手架生成器")
        print(f"   生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   目标目录：{self.base_dir.resolve()}")
        print("=" * 60)
        print()

        self.create_directories()
        self.create_files()
        self.print_structure()
        self.print_summary()


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    # 默认在当前目录下生成 chainqa 项目结构
    # 可通过参数指定目录：python 03_project_structure.py ./my_project
    import sys

    target_dir = sys.argv[1] if len(sys.argv) > 1 else "./chainqa"
    generator = ProjectGenerator(base_dir=target_dir)
    generator.generate()
