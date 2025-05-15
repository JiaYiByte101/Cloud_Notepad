# 使用 Python 3.12 的官方基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有项目文件到容器
COPY . .

# 开放端口（可选）
EXPOSE 8000

# 默认执行启动 Django 服务
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]