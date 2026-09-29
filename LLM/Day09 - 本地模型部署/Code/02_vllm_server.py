# 文件用途：vLLM 服务部署脚本
# 封装 VLLMManager 类，生成 vLLM 启动命令、管理服务配置、生成 Docker 部署配置
# 含性能测试脚本，测量吞吐量、延迟、并发能力
# Python 3.10+ 可运行
# 依赖：pip install openai requests（性能测试需要可连接的 vLLM 服务）

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore


@dataclass
class VLLMConfig:
    """vLLM 服务配置。"""

    model: str = "Qwen/Qwen2-7B-Instruct"
    port: int = 8000
    host: str = "0.0.0.0"
    tensor_parallel_size: int = 1
    quantization: str | None = None  # awq / gptq / None
    gpu_memory_utilization: float = 0.9
    max_model_len: int = 4096
    dtype: str = "auto"  # auto / float16 / bfloat16
    trust_remote_code: bool = True
    extra_args: list[str] = field(default_factory=list)

    def to_args(self) -> list[str]:
        """转换为命令行参数列表。"""
        args = [
            f"--model {self.model}",
            f"--host {self.host}",
            f"--port {self.port}",
            f"--tensor-parallel-size {self.tensor_parallel_size}",
            f"--gpu-memory-utilization {self.gpu_memory_utilization}",
            f"--max-model-len {self.max_model_len}",
            f"--dtype {self.dtype}",
        ]
        if self.quantization:
            args.append(f"--quantization {self.quantization}")
        if self.trust_remote_code:
            args.append("--trust-remote-code")
        args.extend(self.extra_args)
        return args


class VLLMManager:
    """vLLM 服务部署与性能测试管理器。"""

    def __init__(self, config: VLLMConfig | None = None) -> None:
        self.config = config or VLLMConfig()

    def generate_serve_command(self) -> str:
        """生成 vLLM 启动命令。"""
        args = self.config.to_args()
        return "vllm serve " + " \\\n  ".join(args)

    def generate_docker_config(self, image: str = "vllm/vllm-openai:latest") -> str:
        """生成 Docker 部署配置（docker-compose 片段）。"""
        gpu_count = self.config.tensor_parallel_size
        command = " ".join(
            [
                f"--model {self.config.model}",
                f"--host 0.0.0.0",
                f"--port {self.config.port}",
                f"--tensor-parallel-size {gpu_count}",
                f"--gpu-memory-utilization {self.config.gpu_memory_utilization}",
                f"--max-model-len {self.config.max_model_len}",
                f"--dtype {self.config.dtype}",
            ]
        )
        if self.config.quantization:
            command += f" --quantization {self.config.quantization}"
        if self.config.trust_remote_code:
            command += " --trust-remote-code"

        return f"""version: "3.9"

services:
  vllm:
    image: {image}
    container_name: vllm-server
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: {gpu_count}
              capabilities: [gpu]
    volumes:
      - huggingface_cache:/root/.cache/huggingface
    command: {command}
    ports:
      - "{self.config.port}:8000"
    restart: unless-stopped

volumes:
  huggingface_cache:
"""

    def benchmark_latency(
        self,
        prompt: str = "请用三句话介绍一下量子计算。",
        rounds: int = 10,
        base_url: str | None = None,
        api_key: str = "EMPTY",
    ) -> dict[str, Any]:
        """延迟基准测试：单请求多次调用，统计平均/P50/P95/P99 延迟。"""
        if OpenAI is None:
            return {"error": "未安装 openai 包"}
        url = base_url or f"http://localhost:{self.config.port}/v1"
        client = OpenAI(base_url=url, api_key=api_key)

        latencies: list[float] = []
        for i in range(rounds):
            start = time.time()
            try:
                client.chat.completions.create(
                    model=self.config.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=256,
                )
                latencies.append(time.time() - start)
            except Exception as exc:  # noqa: BLE001
                print(f"[benchmark] 第 {i+1} 次请求失败: {exc}")
                latencies.append(-1)

        valid = sorted([x for x in latencies if x > 0])
        if not valid:
            return {"error": "所有请求均失败，请检查 vLLM 服务是否启动"}

        def percentile(data: list[float], p: float) -> float:
            idx = max(0, min(len(data) - 1, int(len(data) * p) - 1))
            return round(data[idx], 3)

        return {
            "rounds": rounds,
            "success": len(valid),
            "avg_latency": round(sum(valid) / len(valid), 3),
            "p50": percentile(valid, 0.5),
            "p95": percentile(valid, 0.95),
            "p99": percentile(valid, 0.99),
            "min": round(valid[0], 3),
            "max": round(valid[-1], 3),
        }

    def benchmark_throughput(
        self,
        prompt: str = "请用一段话介绍深度学习的基本原理。",
        concurrency: int = 8,
        total_requests: int = 32,
        base_url: str | None = None,
        api_key: str = "EMPTY",
    ) -> dict[str, Any]:
        """吞吐量基准测试：并发请求，统计 QPS 与总耗时。"""
        if OpenAI is None:
            return {"error": "未安装 openai 包"}
        url = base_url or f"http://localhost:{self.config.port}/v1"
        client = OpenAI(base_url=url, api_key=api_key)

        def one_request(_idx: int) -> float:
            start = time.time()
            try:
                client.chat.completions.create(
                    model=self.config.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=128,
                )
                return time.time() - start
            except Exception as exc:  # noqa: BLE001
                print(f"[throughput] 请求失败: {exc}")
                return -1

        start = time.time()
        latencies: list[float] = []
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(one_request, i) for i in range(total_requests)]
            for fut in as_completed(futures):
                latencies.append(fut.result())
        total_time = time.time() - start

        valid = [x for x in latencies if x > 0]
        return {
            "concurrency": concurrency,
            "total_requests": total_requests,
            "success": len(valid),
            "total_time": round(total_time, 3),
            "qps": round(len(valid) / total_time, 3) if total_time > 0 else 0,
            "avg_latency": round(sum(valid) / len(valid), 3) if valid else 0,
        }

    def print_report(self) -> None:
        """打印部署配置与命令报告。"""
        print("=" * 60)
        print("vLLM 部署配置")
        print("=" * 60)
        print(f"模型: {self.config.model}")
        print(f"端口: {self.config.port}")
        print(f"张量并行: {self.config.tensor_parallel_size}")
        print(f"量化: {self.config.quantization or '无'}")
        print(f"显存利用率: {self.config.gpu_memory_utilization}")
        print(f"最大上下文: {self.config.max_model_len}")
        print("\n--- 启动命令 ---")
        print(self.generate_serve_command())
        print("\n--- Docker Compose 配置 ---")
        print(self.generate_docker_config())


def demo_vllm() -> None:
    """演示 VLLMManager 的用法。"""
    config = VLLMConfig(
        model="Qwen/Qwen2-7B-Instruct",
        port=8000,
        tensor_parallel_size=1,
        quantization=None,
        gpu_memory_utilization=0.9,
        max_model_len=4096,
    )
    manager = VLLMManager(config)
    manager.print_report()

    print("\n--- 延迟基准测试（需 vLLM 服务已启动） ---")
    latency = manager.benchmark_latency(rounds=5)
    print(latency)

    print("\n--- 吞吐量基准测试 ---")
    throughput = manager.benchmark_throughput(concurrency=4, total_requests=16)
    print(throughput)


if __name__ == "__main__":
    demo_vllm()
