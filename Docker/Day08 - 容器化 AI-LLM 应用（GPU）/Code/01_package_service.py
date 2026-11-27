# -*- coding: utf-8 -*-
"""
Day08 - 01 打包 AI 服务：从裸机到容器

讲清把一个 AI/LLM 推理服务容器化的关键设计：
1. 模型文件不进镜像，用卷挂载（镜像小、模型可换）
2. 依赖与代码分离（层缓存）
3. 环境变量传入模型路径等配置
4. 暴露 API 端口供外部调用

离线可运行（纯讲解）。
"""


def design():
    print("AI 服务容器化的关键决策：\n")
    print("  1. 模型放哪？")
    print("     · 不推荐：打镜（模型几个 GB，镜像暴涨、换模型要重建）")
    print("     · 推荐： 模型放命名卷，镜像只留代码与依赖")
    print("       docker run -v models:/models ...  # 模型从宿主机/卷进来\n")
    print("  2. 依赖怎么装？")
    print("     COPY requirements + RUN pip 在前（层缓存）；代码放后\n")
    print("  3. 配置怎么传？")
    print("     ENV MODEL_PATH=/models/model.bin  # 可用 -e / --env-file 覆盖\n")
    print("  4. 网络怎么开？")
    print("     EXPOSE 8000 + run -p <端口>:8000   # 对外提供推理 API")


def example():
    print("\n封装一个 Python 推理服务的示意：\n")
    print("""  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt ./
  RUN pip install --no-cache-dir -r requirements.txt
  COPY app.py ./
  EXPOSE 8000
  ENV MODEL_PATH=/models/model.bin
  CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
  （模型文件用 -v models:/models 挂载，不放镜像内）
""")
    print("  参考本目录 Dockerfile.service 与 docker-compose.gpu.yml")


def main():
    print(">> 打包 AI 服务\n")
    design()
    example()
    print("  tips: 模型用卷挂载、依赖用层缓存、配置用环境变量。")


if __name__ == "__main__":
    main()