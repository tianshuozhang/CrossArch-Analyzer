FROM python:3.9-slim

# 安装系统依赖（包含clang和libclang）
RUN apt-get update && apt-get install -y \
    clang-13 \
    libclang-13-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /LLM

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 暴露端口（若后端为Flask API）
EXPOSE 5000

# 启动命令（根据实际入口调整，例如demo2.py）
CMD ["python", "demo2.py"]