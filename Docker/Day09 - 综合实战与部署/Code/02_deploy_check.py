# -*- coding: utf-8 -*-
"""
Day09 - 02 上线自检清单

把前面所有要点收敛成一份"上线前 checklist"，逐项确认即可降低翻车率。
也包含生产最佳实践回顾。

离线可运行（纯清单）。
"""


def checklist():
    print("上线前自检清单：\n")
    checks = [
        ("镜像体积", "多阶段构建？.dockerignore 在用？基础镜像最小？"),
        ("依赖/版本", "依赖版本锁死（而非 latest）；基础镜像用具体 tag？"),
        ("配置", "敏感信息走环境变量 / secret，不写进镜像？默认端口合理？"),
        ("持久化", "数据库/模型/向量数据都用了卷，不随容器删除丢失？"),
        ("网络", "服务用 compose 网络按名互联？对外只暴露必要端口？"),
        ("安全", "容器用非 root 运行？暴露的端口用回环/防火墙隔离？"),
        ("资源", "Ollama/推理服务设了内存与 CPU/GPU 上限，防吃光主机？"),
        ("可观测", "有 HEALTHCHECK？日志能被统一采集（docker logs）？"),
        ("容错", "启动顺序 depends_on 合理？服务重启策略配置了？"),
        ("构建可复现", "镜像 tag 固定版本，构建流程可重复、可回滚？"),
    ]
    for i, (title, q) in enumerate(checks, 1):
        ok = "☐"
        print(f"  {ok} {i}. {title}\n     质询：{q}\n")


def best_practice():
    print("\n" + "=" * 60)
    print("生产最佳实践回顾：\n")
    print("  · 镜像瘦身：多阶段 + slim/alpine + --no-cache-dir")
    print("  · 安全：非 root、最小暴露、敏感信息用 secret")
    print("  · 可靠：HEALTHCHECK + 资源限制 + 固定版本 tag")
    print("  · 可观测：统一日志 + 健康检查 + 端口规划")
    print("  · 持久化：数据一律进卷（Day07）")


def main():
    print(">> 上线自检清单\n")
    checklist()
    best_practice()
    print("\n  tips: 打勾过程就是一次「code review」，循清单可显著降低上线事故。")


if __name__ == "__main__":
    main()