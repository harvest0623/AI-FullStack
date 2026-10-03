# Day01/Code - 环境配置详细指南

本文件给出 Python 3.10+ 开发环境的完整搭建步骤，覆盖三平台安装、版本管理、虚拟环境、包管理与 VS Code 配置。

## 一、Windows 安装

### 1. 下载安装包

访问 [python.org/downloads](https://www.python.org/downloads/)，下载 Python 3.12+ 的 Windows 安装包（64 位）。

### 2. 安装时的关键选项

- 勾选 **Add python.exe to PATH**（必须，否则命令行无法直接调用 `python`）
- 选择 **Customize installation**，确认勾选 `pip`、`py launcher`
- 安装路径建议不含中文与空格，例如 `C:\Python312`

### 3. 验证

```powershell
python --version     # 输出 Python 3.12.x
pip --version        # 输出 pip 版本
```

### 4. PowerShell 执行策略

若激活虚拟环境时遇到 `无法加载文件 Activate.ps1，因为在此系统上禁止运行脚本`，执行：

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## 二、macOS 安装

### 1. 使用 Homebrew（推荐）

```bash
# 安装 Homebrew（若未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Python 3.12
brew install python@3.12

# 验证
python3 --version
```

### 2. 系统自带 Python 说明

macOS 自带的 `python3` 版本较旧，建议通过 Homebrew 安装新版本，并使用 `pyenv` 管理多版本。

## 三、Linux 安装

以 Ubuntu/Debian 为例：

```bash
# 更新包索引
sudo apt update

# 安装 Python 3.12 与 pip
sudo apt install python3.12 python3.12-venv python3-pip

# 验证
python3 --version
```

CentOS/RHEL 使用 `yum install python3` 或 `dnf install python3`。

## 四、pyenv 安装与使用

`pyenv` 用于在同一台机器上管理多个 Python 版本，适合需要在不同项目间切换版本的开发者。

### 1. 安装 pyenv（macOS/Linux）

```bash
# 一键安装
curl https://pyenv.run | bash
```

将以下内容加入 shell 配置（`~/.bashrc` 或 `~/.zshrc`）：

```bash
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

### 2. 常用命令

```bash
# 查看可安装的版本
pyenv install --list | grep 3.12

# 安装指定版本
pyenv install 3.12.4

# 设置全局默认版本
pyenv global 3.12.4

# 为某个项目设置本地版本（写入 .python-version 文件）
pyenv local 3.12.4
```

### 3. Windows 说明

Windows 推荐 `pyenv-win`，安装命令：

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
```

## 五、venv 虚拟环境

每个项目应使用独立的虚拟环境，避免全局包污染与版本冲突。

### 1. 创建虚拟环境

```bash
# 在项目根目录执行
python -m venv .venv
```

### 2. 激活虚拟环境

| 平台 | 命令 |
| --- | --- |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows CMD | `.venv\Scripts\activate.bat` |
| macOS / Linux | `source .venv/bin/activate` |

激活后命令行提示符前会出现 `(.venv)`。

### 3. 退出虚拟环境

```bash
deactivate
```

### 4. .gitignore 配置

虚拟环境目录不应提交到版本库，在项目根目录 `.gitignore` 添加：

```
.venv/
__pycache__/
*.pyc
```

## 六、pip 常用命令

```bash
# 安装包
pip install requests

# 安装指定版本
pip install requests==2.31.0

# 升级包
pip install --upgrade requests

# 卸载包
pip uninstall requests

# 列出已安装包
pip list

# 查看包详细信息
pip show requests

# 导出依赖清单（生成 requirements.txt）
pip freeze > requirements.txt

# 根据清单批量安装
pip install -r requirements.txt
```

### 使用国内镜像加速

```bash
# 临时使用清华镜像
pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple

# 永久配置（写入 pip.ini / pip.conf）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

## 七、VS Code 扩展推荐与配置

### 1. 推荐扩展

| 扩展名 | 作用 |
| --- | --- |
| Python（Microsoft） | Python 语言支持、调试、IntelliSense |
| Pylance（Microsoft） | 高性能类型检查与代码补全 |
| Black Formatter | 代码格式化（自动遵循 PEP 8） |
| Ruff | 极速的 linter（可替代 flake8/pylint） |
| Code Runner | 一键运行当前文件 |
| Chinese Language Pack | 中文界面 |

### 2. settings.json 推荐配置

在 VS Code 中按 `Ctrl+,` 打开设置，点击右上角图标进入 `settings.json`，添加：

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true,
        "editor.tabSize": 4,
        "editor.insertSpaces": true
    },
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.autoImportCompletions": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/.venv": true
    }
}
```

### 3. 选择解释器

按 `Ctrl+Shift+P`，输入 `Python: Select Interpreter`，选择项目虚拟环境 `.venv` 中的解释器。

## 八、运行第一个程序

```bash
# 进入 Day01/Code 目录
cd d:\Coding\AI-FullStack\Python\Day01\Code

# 运行 hello.py
python hello.py

# 运行 basics.py
python basics.py
```
