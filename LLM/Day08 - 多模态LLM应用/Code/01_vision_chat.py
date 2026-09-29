# 文件用途：图像理解对话
# VisionClient 类：用 GPT-4o 进行图像对话：图片描述 / OCR 识别 / 图表分析 / 多图对比。
# 支持 URL 和 Base64 两种输入方式。含多个使用示例。
# 运行前：pip install openai python-dotenv；在 .env 配置 OPENAI_API_KEY

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv()


class VisionClient:
    """
    图像理解对话客户端。

    使用方式：
        client = VisionClient(model="gpt-4o")
        # URL 方式
        print(client.describe("https://example.com/img.png"))
        # Base64 方式
        print(client.describe_from_file("local.png"))
        # 多图对比
        print(client.compare_images([url1, url2], "找出差异"))
    """

    def __init__(self, model: str = "gpt-4o") -> None:
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
    def _encode_image(file_path: str | Path) -> tuple[str, str]:
        """把本地图片编码为 base64 data URL。返回 (data_url, mime)。"""
        path = Path(file_path)
        suffix = path.suffix.lower()
        mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
        mime = mime_map.get(suffix, "image/jpeg")
        b64 = base64.b64encode(path.read_bytes()).decode()
        return f"data:{mime};base64,{b64}", mime

    def _build_message(self, text: str, image_urls: list[str], role: str = "user") -> dict:
        """构造含文本 + 多图的消息。"""
        content: list[dict] = [{"type": "text", "text": text}]
        for url in image_urls:
            content.append({"type": "image_url", "image_url": {"url": url}})
        return {"role": role, "content": content}

    def _chat(self, messages: list[dict], max_tokens: int = 1024, temperature: float = 0.3) -> str:
        client = self._get_client()
        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""

    # ------------------------- 基础能力 -------------------------
    def describe(self, image_url: str, question: str = "请详细描述这张图片的内容。") -> str:
        """描述图片（URL 方式）。"""
        msg = self._build_message(question, [image_url])
        return self._chat([msg])

    def describe_from_file(self, file_path: str | Path, question: str = "请详细描述这张图片的内容。") -> str:
        """描述图片（本地文件 → Base64）。"""
        data_url, _ = self._encode_image(file_path)
        msg = self._build_message(question, [data_url])
        return self._chat([msg])

    def ocr(self, image_url: str, hint: str = "") -> str:
        """OCR 文字识别。hint 可告知文档类型以提升准确率。"""
        q = "请提取图片中的所有文字，保持原始排版。"
        if hint:
            q = f"这是一张{hint}。{q}"
        return self.describe(image_url, q)

    def analyze_chart(self, image_url: str, question: str = "") -> str:
        """图表分析。"""
        q = question or "请分析这张图表：说明图表类型、数据趋势、关键数值。"
        return self.describe(image_url, q)

    # ------------------------- 多图对比 -------------------------
    def compare_images(self, image_urls: list[str], task: str = "对比这两张图的差异。") -> str:
        """多图对比。image_urls 可为 URL 或本地路径（自动转 Base64）。"""
        urls: list[str] = []
        for u in image_urls:
            if u.startswith(("http://", "https://", "data:")):
                urls.append(u)
            else:
                data_url, _ = self._encode_image(u)
                urls.append(data_url)
        msg = self._build_message(task, urls)
        return self._chat([msg])

    # ------------------------- 多轮对话 -------------------------
    def chat(self, messages: list[dict], max_tokens: int = 1024) -> str:
        """多轮图像对话。messages 中可混合文本与图像消息。"""
        return self._chat(messages, max_tokens=max_tokens)


# ---------------------------------------------------------------------------
# 演示入口
# ---------------------------------------------------------------------------
def demo() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("[错误] 未配置 OPENAI_API_KEY")
        return

    client = VisionClient(model="gpt-4o")

    # 用一张公开示例图（OpenAI 文档常用图）
    sample_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/240px-Cat03.jpg"

    print("=" * 60)
    print("示例 1：图片描述（URL）")
    print("=" * 60)
    print(client.describe(sample_url))

    print("\n" + "=" * 60)
    print("示例 2：OCR 文字识别")
    print("=" * 60)
    # 用一张含文字的图（这里用数学公式图作为示例）
    ocr_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Quadratic_formula.svg/300px-Quadratic_formula.svg.png"
    print(client.ocr(ocr_url, hint="数学公式图"))

    print("\n" + "=" * 60)
    print("示例 3：图表分析")
    print("=" * 60)
    chart_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Example_of_a_Bar_Chart.png/300px-Example_of_a_Bar_Chart.png"
    print(client.analyze_chart(chart_url))

    print("\n" + "=" * 60)
    print("示例 4：多图对比")
    print("=" * 60)
    url1 = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/240px-Cat03.jpg"
    url2 = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Cat_November_2010-1a.jpg/240px-Cat_November_2010-1a.jpg"
    print(client.compare_images([url1, url2], "对比这两张图中的猫，从颜色、姿态、背景三方面说明差异。"))


if __name__ == "__main__":
    demo()
