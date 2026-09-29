# 文件用途：图像分析工具
# ImageAnalyzer 类：在 GPT-4o 之上封装 OCR / 表格提取 / 字段抽取 / 图表分析 /
#                   UI 转代码 / 图像分类 / 多图对比等结构化分析能力。
# 所有方法返回字符串（结构化场景建议要求 JSON / Markdown，便于程序消费）。
# 运行前：pip install openai python-dotenv；在 .env 配置 OPENAI_API_KEY

from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class ImageAnalyzer:
    """
    图像结构化分析工具。

    使用方式：
        analyzer = ImageAnalyzer(model="gpt-4o")
        # OCR
        print(analyzer.ocr("https://example.com/invoice.png", doc_type="发票"))
        # 表格提取
        print(analyzer.extract_table("sheet.png", fmt="json"))
        # 字段抽取
        print(analyzer.extract_fields("invoice.png", ["发票号", "金额", "日期"]))
        # UI 转代码
        print(analyzer.ui_to_code("login.png", framework="html-css"))
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
    def _to_data_url(file_path: str | Path) -> str:
        """本地图片转 base64 data URL。"""
        path = Path(file_path)
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime = mime_map.get(path.suffix.lower(), "image/jpeg")
        b64 = base64.b64encode(path.read_bytes()).decode()
        return f"data:{mime};base64,{b64}"

    def _normalize_image(self, image: str) -> str:
        """统一图像输入：URL 原样返回；本地路径转 data URL。"""
        if image.startswith(("http://", "https://", "data:")):
            return image
        return self._to_data_url(image)

    def _build_message(self, prompt: str, images: list[str], system: str | None = None) -> list[dict]:
        """构造 messages，支持 system + 多图。"""
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        content: list[dict] = [{"type": "text", "text": prompt}]
        for img in images:
            content.append({"type": "image_url", "image_url": {"url": self._normalize_image(img)}})
        messages.append({"role": "user", "content": content})
        return messages

    def _analyze(
        self,
        prompt: str,
        images: list[str],
        system: str | None = None,
        max_tokens: int = 1500,
        temperature: float = 0.1,
    ) -> str:
        """通用分析入口：低温度 + 结构化系统提示，追求稳定输出。"""
        client = self._get_client()
        messages = self._build_message(prompt, images, system)
        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""

    # ------------------------- OCR 文字识别 -------------------------
    def ocr(self, image: str, doc_type: str = "", keep_layout: bool = True) -> str:
        """OCR 文字识别。

        Args:
            image: 图像 URL 或本地路径。
            doc_type: 文档类型提示（如 "发票" / "合同" / "身份证"），提升准确率。
            keep_layout: 是否保留原始排版。
        """
        sys_prompt = "你是精准的 OCR 引擎，只提取图中文字，不臆测、不补充。"
        q = "请提取图片中的所有文字。"
        if doc_type:
            q = f"这是一张{doc_type}。{q}"
        if keep_layout:
            q += "保留原始排版与换行，按从上到下、从左到右顺序输出。"
        else:
            q += "按连续文本输出，忽略排版。"
        return self._analyze(q, [image], system=sys_prompt)

    # ------------------------- 表格提取 -------------------------
    def extract_table(
        self,
        image: str,
        fmt: str = "markdown",
        sheet_name: str = "",
    ) -> str:
        """表格提取，输出 Markdown / JSON / CSV。

        Args:
            fmt: 输出格式，可选 "markdown" / "json" / "csv"。
            sheet_name: 表名（仅 JSON 格式作为 key 提示）。
        """
        sys_prompt = "你是表格结构化提取专家，严格按指定格式输出，不要解释。"
        fmt = fmt.lower()
        if fmt == "markdown":
            q = "请把图中的表格转为 Markdown 表格，保留表头与合并单元格语义，不要额外说明。"
        elif fmt == "json":
            key = f'"{sheet_name or "table"}"'
            q = (
                f"请把图中的表格转为 JSON，格式为 {{'columns': [...], 'rows': [[...], ...]}}，"
                f"最外层 key 为 {key}。仅输出 JSON，不要 markdown 代码块。"
            )
        elif fmt == "csv":
            q = "请把图中的表格转为 CSV，第一行为表头，字段用半角逗号分隔，文本含逗号请加双引号。仅输出 CSV。"
        else:
            raise ValueError(f"不支持的格式: {fmt}（可选 markdown / json / csv）")
        return self._analyze(q, [image], system=sys_prompt, temperature=0.0)

    # ------------------------- 字段抽取 -------------------------
    def extract_fields(
        self,
        image: str,
        fields: list[str],
        doc_type: str = "",
    ) -> dict[str, Any]:
        """字段抽取，返回 dict。

        Args:
            fields: 要抽取的字段名列表，如 ["发票号", "金额", "日期"]。
            doc_type: 文档类型提示。
        """
        sys_prompt = "你是文档字段抽取引擎，只输出 JSON，不输出任何解释或多余文字。"
        fields_json = json.dumps(fields, ensure_ascii=False)
        q = (
            f"这是一张{doc_type or '文档'}。请提取以下字段：{fields_json}。"
            "要求：1) 严格输出 JSON，key 为字段名，value 为字符串；"
            "2) 找不到的字段值填空字符串；3) 金额去掉货币符号保留数字；"
            "4) 日期统一为 YYYY-MM-DD；5) 不要输出 markdown 代码块。"
        )
        raw = self._analyze(q, [image], system=sys_prompt, temperature=0.0)
        return self._parse_json(raw)

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        """从 LLM 输出中鲁棒地解析 JSON（兼容 markdown 代码块 / 前后多余文字）。"""
        # 去掉 markdown 代码块
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        # 尝试直接解析
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        # 兜底：截取第一个 {...}
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return {"_raw": text}

    # ------------------------- 图表分析 -------------------------
    def analyze_chart(
        self,
        image: str,
        question: str = "",
    ) -> str:
        """图表分析：识别图表类型 / 数据趋势 / 关键数值。"""
        sys_prompt = "你是数据可视化分析专家，回答简洁、数值准确。"
        q = question or (
            "请分析这张图表：\n"
            "1. 图表类型（柱状图/折线图/饼图/散点图等）\n"
            "2. 坐标轴含义与单位\n"
            "3. 主要数据趋势\n"
            "4. 关键数值（峰值、谷值、平均值）\n"
            "用 Markdown 分点输出。"
        )
        return self._analyze(q, [image], system=sys_prompt)

    # ------------------------- UI 转代码 -------------------------
    def ui_to_code(
        self,
        image: str,
        framework: str = "html-css",
        requirements: str = "",
    ) -> str:
        """UI 截图转前端代码。

        Args:
            framework: "html-css" / "tailwind" / "react" / "vue"。
            requirements: 额外要求（如 "响应式 / 暗色模式"）。
        """
        sys_prompt = "你是资深前端工程师，按截图还原代码，结构语义化、样式贴近原图。"
        fw_desc = {
            "html-css": "语义化 HTML + 内联 CSS（<style> 标签）",
            "tailwind": "HTML + Tailwind CSS（通过 CDN 引入）",
            "react": "React 函数组件 + Tailwind CSS",
            "vue": "Vue 3 单文件组件 + Tailwind CSS",
        }
        fw_text = fw_desc.get(framework, fw_desc["html-css"])
        q = (
            f"请把这张 UI 截图转为代码，技术栈：{fw_text}。\n"
            "要求：\n"
            "1. 还原布局、颜色、字号、间距；\n"
            "2. 文字、图标位置准确；\n"
            "3. 只输出代码，不要解释；\n"
            "4. 用注释标出可替换的图片占位符。"
        )
        if requirements:
            q += f"\n额外要求：{requirements}"
        return self._analyze(q, [image], system=sys_prompt, max_tokens=2500)

    # ------------------------- 图像分类 / 打标签 -------------------------
    def classify(self, image: str, candidates: list[str] | None = None) -> str:
        """图像分类，输出类别标签。"""
        sys_prompt = "你是图像分类器，只输出类别名，不输出解释。"
        if candidates:
            cand = " / ".join(candidates)
            q = f"请从以下类别中选择最匹配的一个：{cand}。只输出类别名。"
        else:
            q = "请用 1-3 个词概括图片类别（如：风景 / 人物 / 文档 / 图表 / 商品）。"
        return self._analyze(q, [image], system=sys_prompt, temperature=0.0).strip()

    # ------------------------- 多图对比 -------------------------
    def compare(
        self,
        images: list[str],
        dimensions: list[str] | None = None,
        task: str = "",
    ) -> str:
        """多图对比。

        Args:
            images: 2 张及以上图像（URL 或本地路径）。
            dimensions: 对比维度（如 ["颜色", "布局", "文字"]）。
            task: 自定义任务描述。
        """
        sys_prompt = "你是图像对比分析专家，按维度逐项对比，结论清晰。"
        if task:
            q = task
        elif dimensions:
            dim = "、".join(dimensions)
            q = f"请从以下维度对比这 {len(images)} 张图：{dim}。用 Markdown 表格输出。"
        else:
            q = f"请对比这 {len(images)} 张图的异同。用 Markdown 分点输出。"
        return self._analyze(q, images, system=sys_prompt)


# ---------------------------------------------------------------------------
# 演示入口
# ---------------------------------------------------------------------------
def demo() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("[错误] 未配置 OPENAI_API_KEY")
        return

    analyzer = ImageAnalyzer(model="gpt-4o")

    # 公开示例图
    invoice_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Example_of_a_Bar_Chart.png/300px-Example_of_a_Bar_Chart.png"
    chart_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Example_of_a_Bar_Chart.png/300px-Example_of_a_Bar_Chart.png"
    ui_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Cat_November_2010-1a.jpg/240px-Cat_November_2010-1a.jpg"

    print("=" * 60)
    print("示例 1：图表分析")
    print("=" * 60)
    print(analyzer.analyze_chart(chart_url))

    print("\n" + "=" * 60)
    print("示例 2：表格提取（Markdown）")
    print("=" * 60)
    print(analyzer.extract_table(chart_url, fmt="markdown"))

    print("\n" + "=" * 60)
    print("示例 3：字段抽取（JSON）")
    print("=" * 60)
    fields = analyzer.extract_fields(invoice_url, ["标题", "数值", "单位"], doc_type="图表")
    print(json.dumps(fields, ensure_ascii=False, indent=2))

    print("\n" + "=" * 60)
    print("示例 4：图像分类")
    print("=" * 60)
    print(analyzer.classify(ui_url, candidates=["人物", "动物", "风景", "文档"]))

    print("\n" + "=" * 60)
    print("示例 5：OCR 文字识别")
    print("=" * 60)
    ocr_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Quadratic_formula.svg/300px-Quadratic_formula.svg.png"
    print(analyzer.ocr(ocr_url, doc_type="数学公式图"))


if __name__ == "__main__":
    demo()
