# 文件用途：Day12 示例服务的多阶段构建，产出小体积、非 root 运行的生产镜像
# 构建方式：docker build -t eshop-api:dev .
# 运行方式：docker run --rm -p 8080:8080 -e PORT=8080 eshop-api:dev

# ---------- 构建阶段 ----------
FROM golang:1.23-alpine AS builder
WORKDIR /src
ENV CGO_ENABLED=0 GOOS=linux
COPY go.mod ./
RUN go mod download
COPY . .
# -trimpath 去除本机路径，-s -w 去掉符号表与调试信息，进一步缩小体积
RUN go build -trimpath -ldflags="-s -w" -o /out/server ./cmd/server

# ---------- 运行阶段 ----------
FROM alpine:3.20
RUN apk add --no-cache ca-certificates \
    && addgroup -S app \
    && adduser -S -g app app
COPY --from=builder /out/server /usr/local/bin/server
USER app
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/server"]