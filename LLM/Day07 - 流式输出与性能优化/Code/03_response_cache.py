# 文件用途：响应缓存实现
# ResponseCache 类：内存 LRU 缓存 + 文件缓存。内容哈希缓存（相同输入→缓存输出）。
# 缓存命中率统计。支持 TTL 过期和手动清除。
# 运行前：pip install openai python-dotenv；在 .env 配置 OPENAI_API_KEY

from __future__ import annotations

import hashlib
import json
import os
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class CacheEntry:
    """单条缓存。"""

    output: str
    timestamp: float  # 写入时间戳，用于 TTL
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass
class CacheStats:
    """缓存统计。"""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    errors: int = 0

    @property
    def total(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        return self.hits / max(self.total, 1)

    def __str__(self) -> str:
        return (
            f"hits={self.hits} misses={self.misses} sets={self.sets} "
            f"hit_rate={self.hit_rate:.1%}"
        )


class ResponseCache:
    """
    响应缓存：内存 LRU + 文件持久化。

    使用方式：
        cache = ResponseCache(max_size=1000, ttl_sec=3600, cache_dir=".cache")
        # 命中则直接返回，未命中调 fetch_fn 并写入缓存
        output = cache.get_or_fetch(prompt, model="gpt-4o-mini", fetch_fn=my_llm_call)
        print(cache.stats)
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_sec: int | None = 3600,
        cache_dir: str | Path | None = None,
    ) -> None:
        self.max_size = max_size
        self.ttl_sec = ttl_sec
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        # OrderedDict 实现 LRU：最近访问的放末尾，超容量时弹头部
        self._mem: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = CacheStats()

    # ------------------------- Key 计算 -------------------------
    @staticmethod
    def _make_key(prompt: str, model: str, **params) -> str:
        """内容哈希：prompt + model + 关键参数 → sha256。"""
        raw = json.dumps(
            {"prompt": prompt, "model": model, **params},
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _file_path(self, key: str) -> Path | None:
        if not self.cache_dir:
            return None
        return self.cache_dir / f"{key}.json"

    # ------------------------- 过期检查 -------------------------
    def _is_expired(self, entry: CacheEntry) -> bool:
        if self.ttl_sec is None:
            return False
        return (time.time() - entry.timestamp) > self.ttl_sec

    # ------------------------- 读 -------------------------
    def get(self, prompt: str, model: str, **params) -> str | None:
        """查询缓存。命中返回输出，未命中返回 None。"""
        key = self._make_key(prompt, model, **params)
        # 1. 内存
        if key in self._mem:
            entry = self._mem[key]
            if self._is_expired(entry):
                del self._mem[key]
            else:
                # LRU：移到末尾
                self._mem.move_to_end(key)
                self.stats.hits += 1
                return entry.output
        # 2. 文件
        fp = self._file_path(key)
        if fp and fp.exists():
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                entry = CacheEntry(**data)
                if not self._is_expired(entry):
                    # 回填内存
                    self._set_mem(key, entry)
                    self.stats.hits += 1
                    return entry.output
                fp.unlink(missing_ok=True)
            except Exception:  # noqa: BLE001
                self.stats.errors += 1
        self.stats.misses += 1
        return None

    def _set_mem(self, key: str, entry: CacheEntry) -> None:
        self._mem[key] = entry
        self._mem.move_to_end(key)
        # LRU 淘汰
        while len(self._mem) > self.max_size:
            self._mem.popitem(last=False)

    # ------------------------- 写 -------------------------
    def set(self, prompt: str, model: str, output: str, prompt_tokens: int = 0, completion_tokens: int = 0, **params) -> None:
        key = self._make_key(prompt, model, **params)
        entry = CacheEntry(
            output=output,
            timestamp=time.time(),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        self._set_mem(key, entry)
        # 写文件
        fp = self._file_path(key)
        if fp:
            try:
                fp.write_text(json.dumps(entry.__dict__, ensure_ascii=False), encoding="utf-8")
            except Exception:  # noqa: BLE001
                self.stats.errors += 1
        self.stats.sets += 1

    # ------------------------- 高级接口 -------------------------
    def get_or_fetch(self, prompt: str, model: str, fetch_fn, **params) -> str:
        """
        命中缓存返回；未命中调 fetch_fn(prompt, model) 获取并写入。
        fetch_fn 应返回 (output, prompt_tokens, completion_tokens) 或 output。
        """
        cached = self.get(prompt, model, **params)
        if cached is not None:
            return cached
        result = fetch_fn(prompt, model)
        if isinstance(result, tuple):
            output, pt, ct = result
        else:
            output, pt, ct = result, 0, 0
        self.set(prompt, model, output, pt, ct, **params)
        return output

    # ------------------------- 管理 -------------------------
    def clear(self) -> None:
        """清空内存与文件缓存。"""
        n_files = 0
        if self.cache_dir and self.cache_dir.exists():
            for fp in self.cache_dir.glob("*.json"):
                fp.unlink(missing_ok=True)
                n_files += 1
        self._mem.clear()
        print(f"已清空缓存：内存 + {n_files} 个文件")

    def size(self) -> dict:
        """返回当前缓存规模。"""
        file_count = 0
        if self.cache_dir and self.cache_dir.exists():
            file_count = len(list(self.cache_dir.glob("*.json")))
        return {"memory": len(self._mem), "files": file_count}


# ---------------------------------------------------------------------------
# 演示
# ---------------------------------------------------------------------------
def _mock_llm_call(prompt: str, model: str) -> tuple[str, int, int]:
    """模拟 LLM 调用（演示用，不真实调用 API）。"""
    time.sleep(1.0)  # 模拟延迟
    output = f"[{model}] 回答：{prompt[:30]}..."
    return output, 50, 100


def _real_llm_call(prompt: str, model: str) -> tuple[str, int, int]:
    """真实调用 OpenAI。"""
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    output = resp.choices[0].message.content or ""
    usage = resp.usage
    return output, usage.prompt_tokens if usage else 0, usage.completion_tokens if usage else 0


def demo() -> None:
    cache = ResponseCache(max_size=100, ttl_sec=60, cache_dir=".cache_demo")

    print("=" * 60)
    print("演示 1：mock 模式（不调真实 API）")
    print("=" * 60)
    prompts = [
        "什么是 RAG？",
        "什么是 Embedding？",
        "什么是 RAG？",  # 重复，应命中缓存
        "什么是 Token？",
        "什么是 Embedding？",  # 重复，应命中缓存
    ]
    for p in prompts:
        start = time.perf_counter()
        out = cache.get_or_fetch(p, "gpt-4o-mini", _mock_llm_call)
        elapsed = time.perf_counter() - start
        # 命中缓存耗时极短（<0.01s），未命中约 1s
        tag = "命中" if elapsed < 0.1 else "未命中"
        print(f"  [{tag}] {elapsed:.3f}s | {out[:40]}")

    print(f"\n缓存统计：{cache.stats}")
    print(f"缓存规模：{cache.size()}")

    # 清缓存演示
    print("\n--- 清空缓存 ---")
    cache.clear()
    print(f"清空后统计：{cache.stats}")

    # 真实调用演示（需 API Key）
    print("\n" + "=" * 60)
    print("演示 2：真实 LLM 调用 + 缓存")
    print("=" * 60)
    if not os.getenv("OPENAI_API_KEY"):
        print("[跳过] 未配置 OPENAI_API_KEY")
        return
    cache2 = ResponseCache(max_size=100, ttl_sec=300, cache_dir=".cache_real")
    for p in ["用一句话解释 RAG", "用一句话解释 RAG"]:  # 第二次应命中
        start = time.perf_counter()
        out = cache2.get_or_fetch(p, "gpt-4o-mini", _real_llm_call)
        elapsed = time.perf_counter() - start
        tag = "命中" if elapsed < 0.1 else "未命中"
        print(f"  [{tag}] {elapsed:.3f}s | {out[:50]}")
    print(f"\n缓存统计：{cache2.stats}")

    # 清理演示目录
    import shutil
    shutil.rmtree(".cache_demo", ignore_errors=True)
    shutil.rmtree(".cache_real", ignore_errors=True)


if __name__ == "__main__":
    demo()
