# -*- coding: utf-8 -*-
"""
Day04 - 02 多阶段构建原理

把"编译产物"和"运行时"分开：builder 阶段准备工具链产出产物，
runtime 阶段只要产物，从而把镜像做小。

用体积对比模拟来讲解。离线可运行。
"""


def single_stage() -> dict:
    """单阶段：装编译工具 + 编译 + 运行混在一个镜像，体积大"""
    base = 50          # 基础系统
    build_tools = 350  # gcc/make/git 等编译工具
    src = 5
    deps = 300         # 编译期依赖
    binary = 20        # 编译产物
    return {"镜像总大小(MB)": base + build_tools + src + deps + binary,
            "无用于运行的文件(MB)": build_tools + deps}


def multi_stage() -> dict:
    """多阶段：builder 出二进制，runtime 只用基础系统 + 二进制"""
    base = 50
    binary = 20
    return {"镜像总大小(MB)": base + binary,
            "无用于运行的文件(MB)": 0}


def main():
    print(">> 多阶段构建原理\n")
    single = single_stage()
    multi = multi_stage()

    print("单阶段构建（一个镜像从头到尾）：")
    print(f"  镜像总大小：{single['镜像总大小(MB)']} MB")
    print(f"  其中用不到的残留：{single['无用于运行的文件(MB)']} MB\n")

    print("多阶段构建（builder 出产物，runtime 只要产物）：")
    print(f"  最终 runtime 镜像大小：{multi['镜像总大小(MB)']} MB")
    print(f"  无用于运行的残留：{multi['无用于运行的文件(MB)']} MB\n")

    print("代码形态（示意）：")
    print("""  # ---- builder 阶段 ----
  FROM golang:1.22 AS builder
  WORKDIR /src
  COPY . .
  RUN go build -o /app/svr .      # 编译出二进制

  # ---- runtime 阶段 ----
  FROM alpine:latest              # 极小的运行时
  COPY --from=builder /app/svr /svr
  CMD ["/svr"]
""")
    print(f"  ⇒ 体积从 {single['镜像总大小(MB)']}MB 降到 {multi['镜像总大小(MB)']}MB，"
          "且有 From builder 标志关键行")
    print("  tips: 编译型语言（Go/Rust/C）最受益；解释型语言也可用多阶段剔除构建期工具。")


if __name__ == "__main__":
    main()