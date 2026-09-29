# 文件用途：文字转语音（Text-to-Speech, TTS）
# TTSClient 类：封装 OpenAI TTS API，提供：
#   - synthesize：文字→语音，保存为音频文件
#   - synthesize_bytes：文字→语音，返回字节流（适合流式转发 / 内存播放）
#   - list_voices：列出可用声音
#   - compare_voices：同一文本用多个声音合成，便于挑选
#   - estimate_cost：按字符数估算费用
# 运行前：pip install openai python-dotenv；在 .env 配置 OPENAI_API_KEY

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

# 可用声音（OpenAI 官方）
AVAILABLE_VOICES = ("alloy", "echo", "fable", "onyx", "nova", "shimmer")

# 模型与计费（美元 / 1M 字符）
TTS_PRICING = {
    "tts-1": 15.0,       # 标准
    "tts-1-hd": 30.0,    # 高清
}

# 输出格式
OutputFormat = Literal["mp3", "opus", "aac", "flac", "wav", "pcm"]


class TTSClient:
    """
    文字转语音客户端（基于 OpenAI TTS）。

    使用方式：
        tts = TTSClient()
        # 合成并保存
        tts.synthesize("你好，欢迎使用 AISearch。", "out.mp3")
        # 拿字节流
        audio_bytes = tts.synthesize_bytes("你好")
        # 多声音对比
        tts.compare_voices("Hello world", voices=["alloy", "nova"], out_dir="./voices")
    """

    def __init__(self, model: str = "tts-1") -> None:
        if model not in TTS_PRICING:
            raise ValueError(f"不支持的模型: {model}（可选: {list(TTS_PRICING)}）")
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("未配置 OPENAI_API_KEY")
            self._client = OpenAI(api_key=api_key)
        return self._client

    # ------------------------- 工具方法 -------------------------
    @staticmethod
    def _validate_voice(voice: str) -> str:
        if voice not in AVAILABLE_VOICES:
            raise ValueError(f"不支持的声音: {voice}（可选: {list(AVAILABLE_VOICES)}）")
        return voice

    @staticmethod
    def _validate_text(text: str) -> str:
        text = text.strip()
        if not text:
            raise ValueError("文本不能为空")
        if len(text) > 4096:
            raise ValueError(f"文本过长 ({len(text)} 字符)，TTS 单次上限 4096 字符。")
        return text

    # ------------------------- 核心能力 -------------------------
    def synthesize(
        self,
        text: str,
        output_path: str | Path,
        voice: str = "alloy",
        fmt: OutputFormat = "mp3",
        speed: float = 1.0,
    ) -> Path:
        """文字→语音，保存到文件。

        Args:
            output_path: 输出文件路径（扩展名建议与 fmt 一致）。
            voice: 声音，可选 alloy/echo/fable/onyx/nova/shimmer。
            fmt: 输出格式 mp3/opus/aac/flac/wav/pcm。
            speed: 速度倍率 0.25 ~ 4.0，默认 1.0。
        """
        text = self._validate_text(text)
        self._validate_voice(voice)
        if not 0.25 <= speed <= 4.0:
            raise ValueError("speed 须在 0.25 ~ 4.0 之间")

        client = self._get_client()
        response = client.audio.speech.create(
            model=self.model,
            voice=voice,
            input=text,
            response_format=fmt,
            speed=speed,
        )
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        response.write_to_file(str(out))
        return out

    def synthesize_bytes(
        self,
        text: str,
        voice: str = "alloy",
        fmt: OutputFormat = "mp3",
        speed: float = 1.0,
    ) -> bytes:
        """文字→语音，返回字节流（适合流式转发 / 内存播放）。"""
        text = self._validate_text(text)
        self._validate_voice(voice)
        if not 0.25 <= speed <= 4.0:
            raise ValueError("speed 须在 0.25 ~ 4.0 之间")

        client = self._get_client()
        response = client.audio.speech.create(
            model=self.model,
            voice=voice,
            input=text,
            response_format=fmt,
            speed=speed,
        )
        # OpenAI SDK v1：response.content 为字节
        return response.content

    # ------------------------- 多声音对比 -------------------------
    def compare_voices(
        self,
        text: str,
        voices: list[str] | None = None,
        out_dir: str | Path = "./tts_output",
        fmt: OutputFormat = "mp3",
    ) -> dict[str, str]:
        """同一文本用多个声音合成，便于挑选。

        Args:
            voices: 要对比的声音列表，默认全部 6 种。
            out_dir: 输出目录。

        Returns:
            {voice: 文件路径} 映射。
        """
        voices = voices or list(AVAILABLE_VOICES)
        result: dict[str, str] = {}
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"[INFO] 用 {len(voices)} 个声音合成：{text[:30]}...")
        for v in voices:
            self._validate_voice(v)
            out_file = out_dir / f"voice_{v}.{fmt}"
            try:
                self.synthesize(text, out_file, voice=v, fmt=fmt)
                result[v] = str(out_file)
                print(f"  ✓ {v:<8} → {out_file}")
            except Exception as e:  # noqa: BLE001
                print(f"  ✗ {v:<8} 失败：{e}")
        return result

    # ------------------------- 信息查询 -------------------------
    @staticmethod
    def list_voices() -> list[str]:
        """返回可用声音列表。"""
        return list(AVAILABLE_VOICES)

    @staticmethod
    def voice_description() -> dict[str, str]:
        """各声音风格简介（基于 OpenAI 官方描述）。"""
        return {
            "alloy": "中性平衡，男女通用，适合大多数场景",
            "echo": "成熟男声，沉稳有力，适合新闻 / 解说",
            "fable": "中性偏 上扬，讲故事感强，适合儿童内容",
            "onyx": "低沉男声，浑厚权威，适合纪录片 / 旁白",
            "nova": "明亮女声，亲切自然，适合客服 / 语音助手",
            "shimmer": "温暖女声，柔和友好，适合陪伴类应用",
        }

    def estimate_cost(self, text: str) -> dict[str, float]:
        """估算本次合成的费用（美元）。

        Returns:
            {"chars": 字符数, "rate_per_1m": 单价, "cost_usd": 费用}
        """
        chars = len(self._validate_text(text))
        rate = TTS_PRICING[self.model]
        cost = chars / 1_000_000 * rate
        return {"chars": chars, "rate_per_1m": rate, "cost_usd": round(cost, 6)}


# ---------------------------------------------------------------------------
# 演示入口
# ---------------------------------------------------------------------------
def demo() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("[错误] 未配置 OPENAI_API_KEY")
        return

    tts = TTSClient(model="tts-1")
    sample_text = "你好，欢迎使用 AISearch 智能问答服务。今天我们将一起探索多模态 LLM 的能力。"

    print("=" * 60)
    print("TTS 信息速查")
    print("=" * 60)
    print(f"可用声音：{tts.list_voices()}")
    print("声音风格：")
    for v, desc in tts.voice_description().items():
        print(f"  - {v:<8} {desc}")

    print("\n" + "=" * 60)
    print("示例 1：单次合成（alloy 声音）")
    print("=" * 60)
    cost = tts.estimate_cost(sample_text)
    print(f"文本：{sample_text}")
    print(f"字符数：{cost['chars']}，预估费用：${cost['cost_usd']:.6f}")
    out_file = tts.synthesize(sample_text, "tts_output/sample_alloy.mp3", voice="alloy")
    print(f"已保存：{out_file}")

    print("\n" + "=" * 60)
    print("示例 2：多声音对比")
    print("=" * 60)
    result = tts.compare_voices(
        sample_text,
        voices=["alloy", "nova", "shimmer", "onyx"],
        out_dir="tts_output",
    )
    print(f"\n生成 {len(result)} 个音频文件，可逐个试听挑选最合适的声音。")

    print("\n" + "=" * 60)
    print("示例 3：拿到字节流（流式转发场景）")
    print("=" * 60)
    audio_bytes = tts.synthesize_bytes("这是一段测试音频。", voice="nova")
    print(f"字节流大小：{len(audio_bytes)} bytes（可用于 HTTP 流式响应 / 内存播放）")

    print("\n" + "=" * 60)
    print("费用对比（1 万字符）")
    print("=" * 60)
    for m in ("tts-1", "tts-1-hd"):
        c = TTSClient(model=m).estimate_cost("字" * 10000)
        print(f"  {m:<10} ${c['cost_usd']:.4f}")


if __name__ == "__main__":
    demo()
