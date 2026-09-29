# Day08 Code - 多模态 LLM 应用代码

本目录提供 4 个 Python 脚本，覆盖图像理解、图像结构化分析、语音转文字（STT）、文字转语音（TTS）四大多模态能力。所有脚本围绕 `AISearch` 项目的"多模态扩展"环节展开，让问答服务从"只能打字"升级为"能看能听能说"。

---

## 环境准备

```bash
pip install openai python-dotenv
```

`.env` 配置：

```
OPENAI_API_KEY=sk-xxxxxxxx
```

> 多模态 API（GPT-4o / Whisper / TTS）均由 OpenAI 提供，只需一个 `OPENAI_API_KEY`。
> 长音频分片转写需系统安装 `ffmpeg` 并加入 PATH。

---

## 文件清单

### `01_vision_chat.py` — 图像理解对话

**核心类**：`VisionClient`

**能力**：
- 图片描述（URL / Base64 两种输入）
- OCR 文字识别（含文档类型 hint）
- 图表分析（类型 / 趋势 / 关键数值）
- 多图对比（一条消息传多张图）
- 多轮图像对话（混合文本与图像消息）

**示例**：

```python
client = VisionClient(model="gpt-4o")
# URL 方式
print(client.describe("https://example.com/img.png"))
# 本地文件 → Base64
print(client.describe_from_file("local.png"))
# 多图对比
print(client.compare_images([url1, url2], "从颜色、姿态、背景三方面对比"))
# OCR
print(client.ocr(url, hint="增值税发票"))
```

直接运行：`python 01_vision_chat.py`

---

### `02_image_analysis.py` — 图像结构化分析

**核心类**：`ImageAnalyzer`

**能力**：
- `ocr`：OCR 文字识别（保留排版 / 连续文本两种模式）
- `extract_table`：表格提取，输出 Markdown / JSON / CSV
- `extract_fields`：字段抽取，返回 dict（含鲁棒 JSON 解析，兼容代码块 / 多余文字）
- `analyze_chart`：图表分析（类型 / 坐标轴 / 趋势 / 关键数值）
- `ui_to_code`：UI 截图转代码（支持 html-css / tailwind / react / vue）
- `classify`：图像分类（开放类别或候选标签）
- `compare`：多图对比（按维度逐项输出）

**示例**：

```python
analyzer = ImageAnalyzer(model="gpt-4o")

# 发票字段抽取 → JSON
fields = analyzer.extract_fields(
    "invoice.png",
    ["发票号", "开票日期", "金额", "卖方名称"],
    doc_type="增值税发票",
)
print(fields)  # {"发票号": "...", "金额": "12345.67", ...}

# 表格 → Markdown
print(analyzer.extract_table("sheet.png", fmt="markdown"))

# UI 截图 → HTML + Tailwind
code = analyzer.ui_to_code("login.png", framework="tailwind", requirements="响应式")
Path("out.html").write_text(code, encoding="utf-8")
```

**鲁棒 JSON 解析**：`extract_fields` 内部用 `_parse_json`，依次尝试：
1. 去掉 markdown 代码块后直接 `json.loads`
2. 正则截取第一个 `{...}` 再解析
3. 全部失败则返回 `{"_raw": 原文}`，不会抛异常

直接运行：`python 02_image_analysis.py`

---

### `03_whisper_stt.py` — 语音转文字（STT）

**核心类**：`STTClient`

**能力**：
- `transcribe`：语音→文字（保留原语言，支持 language / prompt / temperature）
- `translate`：多语言语音→英文文字
- `transcribe_with_timestamps`：带时间戳的逐字稿（verbose_json）
- `transcribe_long`：长音频分片转写（ffmpeg 切片，绕过 25MB 单文件上限）
- `format_timestamps`：把 verbose_json 格式化为 `[mm:ss - mm:ss] 文字`

**示例**：

```python
stt = STTClient()

# 短音频
text = stt.transcribe("meeting.mp3", language="zh")
print(text)

# 带时间戳
result = stt.transcribe_with_timestamps("podcast.mp3", language="zh")
print(STTClient.format_timestamps(result))
# [00:00 - 00:03] 大家好
# [00:03 - 00:07] 欢迎收听本期节目

# 长音频（>25MB 自动分片）
long_text = stt.transcribe_long("1hour.wav", chunk_minutes=20)
```

**约束**：
- 单文件上限 25MB（OpenAI 官方限制），超出请用 `transcribe_long`
- 支持格式：mp3 / wav / m4a / webm / mp4 / mpga / mpeg / ogg
- `prompt` 参数可传入专有名词提升识别准确率（最长 224 token）
- `translate` 输出固定为英文

直接运行：`python 03_whisper_stt.py`（需准备 `sample.mp3`）

---

### `04_tts_demo.py` — 文字转语音（TTS）

**核心类**：`TTSClient`

**能力**：
- `synthesize`：文字→语音，保存为文件
- `synthesize_bytes`：文字→语音，返回字节流（适合流式转发 / 内存播放）
- `compare_voices`：同一文本用多个声音合成，便于挑选
- `list_voices` / `voice_description`：声音列表与风格简介
- `estimate_cost`：按字符数估算费用

**示例**：

```python
tts = TTSClient(model="tts-1")

# 合成并保存
tts.synthesize("你好，欢迎使用 AISearch。", "out.mp3", voice="nova")

# 拿字节流（HTTP 流式响应场景）
audio_bytes = tts.synthesize_bytes("测试音频", voice="alloy")

# 多声音对比
result = tts.compare_voices(
    "Hello world",
    voices=["alloy", "nova", "shimmer", "onyx"],
    out_dir="./voices",
)

# 估算费用
print(tts.estimate_cost("一万字测试" * 1000))
# {"chars": 6000, "rate_per_1m": 15.0, "cost_usd": 0.09}
```

**参数说明**：

| 参数 | 取值 | 说明 |
|------|------|------|
| `model` | `tts-1` / `tts-1-hd` | 标准 / 高清 |
| `voice` | alloy / echo / fable / onyx / nova / shimmer | 6 种声音 |
| `fmt` | mp3 / opus / aac / flac / wav / pcm | 输出格式 |
| `speed` | 0.25 ~ 4.0 | 速度倍率，默认 1.0 |

**声音风格**：

| 声音 | 风格 | 适合场景 |
|------|------|---------|
| alloy | 中性平衡 | 通用 |
| echo | 成熟男声 | 新闻 / 解说 |
| fable | 上扬讲故事 | 儿童内容 |
| onyx | 低沉男声 | 纪录片 / 旁白 |
| nova | 明亮女声 | 客服 / 助手 |
| shimmer | 温暖女声 | 陪伴类应用 |

**约束**：单次文本上限 4096 字符；更长文本需自行分段合成后拼接。

直接运行：`python 04_tts_demo.py`

---

## 多模态应用指南

### 图像输入方式选择

| 方式 | 何时用 | 注意 |
|------|--------|------|
| URL | 图像已在线上（CDN / OSS） | 需公网可访问；不增加请求体积 |
| Base64 | 本地图片 / 隐私敏感 | 体积膨胀 33%；大图建议先压缩 |
| 文件上传 | 大文件 / 复用 | 多一步上传，但可复用 file_id |

本目录代码统一用 `_normalize_image` 自动判断：URL 原样返回，本地路径自动转 Base64。

### 图像 Token 消耗估算

OpenAI 按分辨率 tile 计算图像 Token：

| 图像尺寸 | 大致 Token | 单次成本（gpt-4o） |
|---------|-----------|-------------------|
| 512×512 | ~170 | ~$0.0017 |
| 1024×1024 | ~340 | ~$0.0034 |
| 2048×2048 | ~580+ | ~$0.0058+ |

**控制策略**：
1. 上传前压缩到必要分辨率（建议 ≤ 1024×1024）
2. 优先用 URL 而非 Base64（减少请求体积）
3. 重复图像缓存识别结果
4. 批量用 Batch API（50% 折扣）

### 音频成本计算

| 资源 | 计费单位 | 单价 | 示例 |
|------|---------|------|------|
| Whisper STT | 分钟 | $0.006 | 10 分钟 = $0.06 |
| TTS (tts-1) | 字符 | $15 / 1M | 1 万字 = $0.15 |
| TTS-HD | 字符 | $30 / 1M | 1 万字 = $0.30 |

### 多模态 Prompt 技巧

1. **明确关注点**：指出关注图像哪个部分（"请只关注左上角的表格"）
2. **引导结构化输出**：要求 JSON / Markdown 表格，便于程序消费
3. **多图对比时明确维度**：说清对比什么（"从颜色、布局、文字三方面对比"）
4. **OCR 任务给上下文**：告知文档类型（"这是一张增值税发票"）
5. **限制输出长度**：避免冗长描述，用 `max_tokens` 控制
6. **低温度追求稳定**：结构化任务用 `temperature=0`，创作类任务可调高

### 语音问答闭环（练习 3 完整链路）

```python
from Day02.Code.04_unified_client import UnifiedClient   # 复用 Day02 的统一客户端
from Day08.Code.03_whisper_stt import STTClient
from Day08.Code.04_tts_demo import TTSClient

stt = STTClient()
llm = UnifiedClient()
tts = TTSClient()

# 1. 语音 → 文字
question = stt.transcribe("question.mp3", language="zh")
# 2. 文字 → LLM 回答
answer = llm.chat(question)
# 3. 回答 → 语音
tts.synthesize(answer, "answer.mp3", voice="nova")
```

---

## 常见问题

**Q1：调用 GPT-4o 图像 API 报 `image_url is invalid`？**
A：检查 URL 是否公网可访问；本地路径必须转 Base64 data URL（本目录代码已自动处理）。

**Q2：Base64 图像请求体过大被拒？**
A：压缩图像到 1024×1024 以内；或改用 Files API 上传后引用 file_id。

**Q3：Whisper 报 `file too large`？**
A：单文件超 25MB，改用 `transcribe_long(file, chunk_minutes=20)`，需系统安装 ffmpeg。

**Q4：TTS 报 `text too long`？**
A：单次上限 4096 字符，长文本需分段合成。可用 `estimate_cost` 先算字符数与费用。

**Q5：OCR 识别不准？**
A：1) 用 `doc_type` 告知文档类型；2) 用 `prompt` 传入专有名词；3) 确保图像清晰、文字区域占比足够。

**Q6：`extract_fields` 返回的 JSON 解析失败？**
A：代码已内置鲁棒解析（去代码块 + 正则截取），若仍返回 `{"_raw": ...}`，可在 Prompt 中加强约束（如"只输出 JSON，不要任何前后文字"），或换用 `gpt-4o` 而非 `gpt-4o-mini`。

**Q7：TTS 中文声音哪个好？**
A：`nova` 和 `shimmer` 中文效果较好，`alloy` 中性通用；建议用 `compare_voices` 一次合成多个声音试听挑选。
