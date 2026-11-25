# 一个可直接构建的 Python Web 示例镜像
# 用法：在含本文件的目录执行  docker build -t myweb:1.0 .

# 基础镜像：带 Python 3.11 的官方镜像
FROM python:3.11-slim

# 设置工作目录（之后的命令都在此执行）
WORKDIR /app

# 先拷贝依赖清单并安装（放前面，利用层缓存，见 Day02）
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 再拷贝业务代码（变更频繁，放后面）
COPY app.py ./

# 声明容器监听端口（文档性质，真正映射要靠 run -p 或 compose）
EXPOSE 8000

# 环境变量（可通过 -e / compose environment 覆盖）
ENV APP_NAME=myweb

# 容器启动时执行的命令
CMD ["python", "app.py"]