# 文件用途：Day12 常用工程命令。Windows 需安装 make（如通过 Chocolatey / Git Bash），
# 也可以直接复制目标中的 go 命令手动执行。

GOOS := $(shell go env GOOS)
APP  := server
BIN  := bin/server
IMAGE ?= eshop-api:dev

ifeq ($(GOOS),windows)
BIN := bin/server.exe
endif

.PHONY: build test bench cover lint docker run clean tidy

build:
	go build -trimpath -ldflags="-s -w" -o $(BIN) ./cmd/server

test:
	go test ./...

bench:
	go test -bench=. -benchmem ./calc

cover:
	go test -cover ./...

lint:
	go vet ./...

docker:
	docker build -t $(IMAGE) .

run:
	go run ./cmd/server

tidy:
	go mod tidy

clean:
	go clean