# 使用多阶段构建，首先构建前端
# 基础镜像包括node以构建前端
FROM node:16 AS web-builder

# 复制前端代码
COPY web /web

# 安装依赖并构建前端
WORKDIR /web
RUN npm install && npm run build

# 接下来，构建Python环境
FROM python:3.10.13-slim-bullseye

WORKDIR /app

# 从web-builder阶段复制构建好的前端dist目录
COPY --from=web-builder /web/dist /app/web/dist

# 复制后端Python代码和依赖文件
COPY ./free_one_api /app/free_one_api
COPY ./requirements.txt ./main.py /app/

RUN /bin/sh -c pip install

CMD ["python", "main.py"]
