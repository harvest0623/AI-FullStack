# 文件用途：语音转文字（Speech-to-Text, STT）
# STTClient 类：封装 OpenAI Whisper API，提供：
#   - transcribe：语音→文字（保留原语言）
#   - translate：多语言语音→英文文字
#   - transcribe_long：长音频分片处理（绕过 25MB 单文件上限）
#   - transcribe_with_timestamps：带时间戳的逐字稿（verbose_json）
# 支持常见音频格式 mp3/wav/m4a/webm/mp4 等。
# 运行前：pip install openai python-dotenv；在 .env 配置 OPENAI_API_KEY

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Whisper 单文件大小上限：25MB（OpenAI 官方限制）
WHISPER_MAX_BYTES = 25 * 1024 * 1024

# 支持的音频扩展名
SUPPORTED_AUDIO_EXT = {".mp3", ".wav", ".m4a", ".webm", ".mp4", ".mpga", ".mpeg", ".ogg"}


class STTClient:
    """
    语音转文字客户端（基于 OpenAI Whisper）。

    使用方式：
        stt = STTClient()
        # 短音频
        text = stt.transcribe("meeting.mp3")
        # 翻译为英文
        en = stt.translate("chinese.mp3")
        # 长音频（自动分片）
        long_text = stt.transcribe_long("1hour.wav")
        # 带时间戳
        ts = stt.transcribe_with_timestamps("podcast.mp3", language="zh")
    """

    def __init__(self, model: str = "whisper-1") -> None:
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
    def _validate_audio(file_path: str | Path) -> Path:
        """校验音频文件存在且格式受支持。"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"音频文件不存在: {path}")
        if path.suffix.lower() not in SUPPORTED_AUDIO_EXT:
            raise ValueError(
                f"不支持的音频格式: {path.suffix}（支持: {sorted(SUPPORTED_AUDIO_EXT)}）"
            )
        return path

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """人类可读的文件大小。"""
        for unit in ("B", "KB", "MB", "GB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"

    # ------------------------- 基础能力 -------------------------
    def transcribe(
        self,
        file_path: str | Path,
        language: str = "",
        prompt: str = "",
        temperature: float = 0.0,
    ) -> str:
        """语音转文字（保留原语言）。

        Args:
            file_path: 音频文件路径。
            language: 语言代码（如 "zh" / "en" / "ja"），留空自动检测。
            prompt: 提示文本（可传入专有名词 / 上下文，提升识别准确率，最长 224 token）。
            temperature: 采样温度，0 最稳定。
        """
        path = self._validate_audio(file_path)
        if path.stat().st_size > WHISPER_MAX_BYTES:
            raise ValueError(
                f"文件过大 ({self._format_size(path.stat().st_size)})，"
                f"单文件上限 25MB，请用 transcribe_long() 分片处理。"
            )

        client = self._get_client()
        kwargs: dict[str, Any] = {"model": self.model, "file": path.open("rb"), "temperature": temperature}
        if language:
            kwargs["language"] = language
        if prompt:
            kwargs["prompt"] = prompt

        resp = client.audio.transcriptions.create(**kwargs)
        return resp.text

    def translate(self, file_path: str | Path, prompt: str = "") -> str:
        """语音翻译：把任意语言语音翻译成英文文字（输出固定为英文）。

        Args:
            prompt: 提示文本（英文，引导风格 / 术语）。
        """
        path = self._validate_audio(file_path)
        if path.stat().st_size > WHISPER_MAX_BYTES:
            raise ValueError("文件过大，请用 transcribe_long() 后再翻译各分片。")

        client = self._get_client()
        kwargs: dict[str, Any] = {"model": self.model, "file": path.open("rb")}
        if prompt:
            kwargs["prompt"] = prompt

        resp = client.audio.translations.create(**kwargs)
        return resp.text

    # ------------------------- 带时间戳 -------------------------
    def transcribe_with_timestamps(
        self,
        file_path: str | Path,
        language: str = "",
    ) -> dict[str, Any]:
        """带时间戳的语音转写，返回 verbose_json 结构。

        返回结构（OpenAI verbose_json）：
            {
              "text": "全文",
              "segments": [
                {"id": 0, "start": 0.0, "end": 2.5, "text": "片段文字", ...},
                ...
              ]
            }
        """
        path = self._validate_audio(file_path)
        if path.stat().st_size > WHISPER_MAX_BYTES:
            raise ValueError("带时间戳模式暂不支持分片，请用 25MB 以内文件。")

        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "file": path.open("rb"),
            "response_format": "verbose_json",
            "timestamp_granularities": ["segment"],
        }
        if language:
            kwargs["language"] = language

        resp = client.audio.transcriptions.create(**kwargs)
        # 转 dict（OpenAI SDK v1 返回对象，可 model_dump）
        if hasattr(resp, "model_dump"):
            return resp.model_dump()
        if hasattr(resp, "to_dict"):
            return resp.to_dict()
        return {"text": str(resp), "segments": []}

    @staticmethod
    def format_timestamps(result: dict[str, Any]) -> str:
        """把 verbose_json 结果格式化为 [mm:ss] 文字 形式。"""
        segments = result.get("segments", [])
        if not segments:
            return result.get("text", "")
        lines = []
        for seg in segments:
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            text = (seg.get("text") or "").strip()
            lines.append(f"[{_fmt_time(start)} - {_fmt_time(end)}] {text}")
        return "\n".join(lines)

    # ------------------------- 长音频分片 -------------------------
    def transcribe_long(
        self,
        file_path: str | Path,
        language: str = "",
        chunk_minutes: float = 20.0,
    ) -> str:
        """长音频分片转写。

        利用 ffmpeg 切分音频（需系统已安装 ffmpeg 并在 PATH 中），
        每片单独调用 Whisper，最后拼接。

        Args:
            chunk_minutes: 每片时长（分钟），默认 20 分钟。
        """
        path = self._validate_audio(file_path)
        if not shutil.which("ffmpeg"):
            raise RuntimeError("未找到 ffmpeg，请先安装并加入 PATH。")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            # 切片：每 chunk_minutes 分钟一个文件
            chunk_pattern = tmp_dir / "chunk_%04d.mp3"
            cmd = (
                f'ffmpeg -y -i "{path}" -f segment -segment_time {int(chunk_minutes * 60)} '
                f'-c copy "{chunk_pattern}" -loglevel error'
            )
            ret = os.system(cmd)
            if ret != 0:
                raise RuntimeError(f"ffmpeg 切分失败（exit={ret}）")

            chunks = sorted(tmp_dir.glob("chunk_*.mp3"))
            if not chunks:
                # 文件太小未触发切片，直接转原文件
                return self.transcribe(path, language=language)

            print(f"[INFO] 切分为 {len(chunks)} 片，开始逐片转写...")
            parts = []
            for i, chunk in enumerate(chunks, 1):
                print(f"  [{i}/{len(chunks)}] {chunk.name} ({self._format_size(chunk.stat().st_size)})")
                text = self.transcribe(chunk, language=language)
                parts.append(text.strip())
            return "\n".join(parts)


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------
def _fmt_time(seconds: float) -> str:
    """秒数 → mm:ss 格式。"""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


# ---------------------------------------------------------------------------
# 演示入口
# ---------------------------------------------------------------------------
def demo() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("[错误] 未配置 OPENAI_API_KEY")
        return

    stt = STTClient()

    # 这里用一个公开示例音频（实际请替换为本地音频文件）
    sample_audio = "sample.mp3"

    if not Path(sample_audio).exists():
        print(f"[提示] 未找到 {sample_audio}，请准备一个音频文件后运行示例。")
        print("       支持格式：mp3 / wav / m4a / webm 等；单文件 < 25MB 用 transcribe()，更大用 transcribe_long()。")
        print("\n--- API 能力速查 ---")
        print("transcribe(file)               语音→文字（保留原语言）")
        print("translate(file)                语音→英文文字")
        print("transcribe_with_timestamps()   带时间戳的逐字稿")
        print("transcribe_long(file)          长音频分片转写（需 ffmpeg）")
        return

    print("=" * 60)
    print("示例 1：语音转文字")
    print("=" * 60)
    text = stt.transcribe(sample_audio, language="zh")
    print(f"识别结果：\n{text}")

    print("\n" + "=" * 60)
    print("示例 2：翻译为英文")
    print("=" * 60)
    en = stt.translate(sample_audio)
    print(f"英文翻译：\n{en}")

    print("\n" + "=" * 60)
    print("示例 3：带时间戳的逐字稿")
    print("=" * 60)
    ts = stt.transcribe_with_timestamps(sample_audio, language="zh")
    print(STTClient.format_timestamps(ts))


if __name__ == "__main__":
    demo()
