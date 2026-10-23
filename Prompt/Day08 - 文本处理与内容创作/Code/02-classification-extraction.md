# 分类与抽取模板合集

> 本文件包含 4 个模板：情感分类 / 主题分类 / 实体抽取 / 事件抽取。全部输出 JSON 格式并含 Schema 定义，便于下游系统集成。

---

## 模板 1：情感分类 - 三分类（正/负/中）含置信度

### 模板说明
- 用途：对文本进行三分类情感分析，输出标签 + 置信度 + 理由
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{text}}`

### 完整模板

```text
你是 SmartCS 智能客服的情感分析引擎。请对以下文本进行情感分类。

【文本】
{{text}}

【类别定义】
- positive：明确表达满意、赞赏、感谢等正面情感
- negative：明确表达不满、愤怒、失望等负面情感
- neutral：陈述事实、询问信息、正负并存且无法判断主导情感

【Few-Shot 示例】
输入：质量很好，物流也快，非常满意！
输出：{"label": "positive", "confidence": 0.97, "reason": "明确表达满意与赞赏"}

输入：包装破损，但客服处理很快。
输出：{"label": "neutral", "confidence": 0.7, "reason": "正负情感并存，无法判断主导"}

输入：简直垃圾，再也不会买了！
输出：{"label": "negative", "confidence": 0.98, "reason": "强烈负面表达"}

【输出 Schema】
{
  "label": "positive | negative | neutral",
  "confidence": 0.0-1.0,
  "reason": "分类依据（≤30 字）"
}

约束：
1. 只能从给定 3 个类别中选择
2. confidence 反映分类把握程度：
   - ≥0.9：情感明确
   - 0.6-0.9：情感较明确但有少量歧义
   - <0.6：情感模糊或并存
3. 若 confidence < 0.6，reason 必须说明模糊点
4. 只输出 JSON，不输出额外文本
```

### 使用示例

#### 输入
```text
你是 SmartCS 智能客服的情感分析引擎。请对以下文本进行情感分类。

【文本】
我下单的耳机终于到了，音质比预期好很多，但是包装有点压扁了，希望下次注意。

（类别定义、Few-Shot、Schema 同上模板）
```

#### 预期输出
```json
{
  "label": "neutral",
  "confidence": 0.65,
  "reason": "音质满意（正面）与包装压扁（负面）并存，正面略主导但未达 positive 阈值"
}
```

### 调优建议
- 温度：0.0（分类需稳定）
- 若需更细粒度（5 分类：强烈正 / 正 / 中 / 负 / 强烈负），可扩展类别定义
- 三分类置信度 < 0.6 的样本建议人工复核

---

## 模板 2：主题分类 - 给定 5 个主题分类

### 模板说明
- 用途：将用户咨询分类到 5 个预设主题之一
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{text}}`、`{{topics}}`

### 完整模板

```text
你是 SmartCS 智能客服的主题分类引擎。请将以下用户咨询分类到最匹配的主题。

【主题列表】
{{topics}}

【分类规则】
1. 只能从给定主题中选择
2. 一条咨询只归入 1 个最匹配的主题
3. 若多个主题都相关，取最主要的一个
4. 若都不匹配，归入 other

【输出 Schema】
{
  "topic": "主题标识",
  "confidence": 0.0-1.0,
  "matched_keywords": ["命中的关键词"],
  "reason": "分类依据（≤30 字）"
}

约束：
1. 不得编造主题列表外的类别
2. matched_keywords 必须来自原文
3. 只输出 JSON
```

### 使用示例

#### 输入
```text
你是 SmartCS 智能客服的主题分类引擎。请将以下用户咨询分类到最匹配的主题。

【主题列表】
- order_query：订单查询（查物流、查状态、查详情）
- refund：退换货（退货、换货、退款）
- logistics：物流咨询（快递公司、配送时间、地址修改）
- product：产品咨询（规格、参数、库存、价格）
- complaint：投诉（服务态度、商品质量、虚假宣传）
- other：其他

【用户咨询】
我的订单 20251031-001 显示已签收但我没收到，是不是送错地方了？我要申请退款。

（分类规则、Schema 同上）
```

#### 预期输出
```json
{
  "topic": "refund",
  "confidence": 0.85,
  "matched_keywords": ["申请退款"],
  "reason": "用户明确表达申请退款，虽涉及物流签收异常但主要诉求是退款"
}
```

### 调优建议
- 温度：0.0
- 若主题边界模糊，可在主题定义中追加"不属于本主题的典型情况"
- 多主题相关时，可改为多标签分类：输出 `topics: [...]` 数组

---

## 模板 3：实体抽取 - 从客服对话抽取订单号 / 产品名 / 金额 / 日期

### 模板说明
- 用途：从客服对话中抽取关键业务实体
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{conversation}}`

### 完整模板

```text
你是 SmartCS 智能客服的实体抽取引擎。请从以下客服对话中抽取关键实体。

【对话】
{{conversation}}

【实体 Schema】
{
  "order_id": {
    "type": "string | null",
    "description": "订单号，格式多为 YYYYMMDD-XXX 或纯数字",
    "multiple": false
  },
  "product_name": {
    "type": "array[string]",
    "description": "提及的产品名称",
    "multiple": true
  },
  "amount": {
    "type": "object | null",
    "description": "金额",
    "fields": {"value": "number", "currency": "CNY|USD|..."}
  },
  "dates": {
    "type": "array[object]",
    "description": "提及的日期",
    "fields": {"raw": "原文表述", "normalized": "ISO 8601 格式"}
  },
  "user_phone": {
    "type": "string | null",
    "description": "用户手机号（11 位）",
    "multiple": false
  }
}

【抽取规则】
1. 若实体在对话中未出现，对应字段填 null（单值）或空数组（多值）
2. 日期必须同时给出原文表述与 ISO 标准化（YYYY-MM-DD）
3. 金额必须区分数值与币种
4. 不得编造对话中未提及的实体
5. 同一实体多次出现只保留首次

【输出格式】
{
  "entities": { ...符合上述 Schema },
  "confidence": {
    "order_id": 0.0-1.0,
    "product_name": 0.0-1.0,
    "amount": 0.0-1.0,
    "dates": 0.0-1.0,
    "user_phone": 0.0-1.0
  }
}

约束：只输出 JSON，不输出任何解释。
```

### 使用示例

#### 输入
```text
你是 SmartCS 智能客服的实体抽取引擎。请从以下客服对话中抽取关键实体。

【对话】
用户：你好，我 10 月 28 日下的订单 20251028-009，买的是索尼 WH-1000XM5 耳机和一根 USB-C 数据线，总共花了 2399 元。现在还没收到货，我的手机 13812345678。
客服：好的，我帮您查一下。订单 20251028-009 显示已发货，预计 10 月 31 日送达。

（Schema、抽取规则同上）
```

#### 预期输出
```json
{
  "entities": {
    "order_id": "20251028-009",
    "product_name": ["索尼 WH-1000XM5 耳机", "USB-C 数据线"],
    "amount": {"value": 2399, "currency": "CNY"},
    "dates": [
      {"raw": "10 月 28 日", "normalized": "2025-10-28"},
      {"raw": "10 月 31 日", "normalized": "2025-10-31"}
    ],
    "user_phone": "13812345678"
  },
  "confidence": {
    "order_id": 0.98,
    "product_name": 0.95,
    "amount": 0.95,
    "dates": 0.9,
    "user_phone": 0.95
  }
}
```

### 调优建议
- 温度：0.0
- 实体类型可按业务扩展（如增加地址、SKU、优惠券码）
- 抽取后建议用正则二次校验订单号 / 手机号格式
- 多轮对话抽取时，注意实体可能跨轮次补充

---

## 模板 4：事件抽取 - 提取投诉事件要素

### 模板说明
- 用途：从投诉文本中提取事件五要素（时间 / 地点 / 人物 / 事件 / 结果）
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{complaint_text}}`

### 完整模板

```text
你是 SmartCS 智能客服的事件抽取引擎。请从以下投诉文本中提取事件要素。

【投诉文本】
{{complaint_text}}

【事件 Schema】
{
  "event_type": "complaint | refund_dispute | quality_issue | logistics_issue | service_issue",
  "time": {
    "raw": "原文时间表述",
    "normalized": "ISO 8601 或相对时间"
  },
  "location": "事件发生地点（线上/线下/具体地址），可为 null",
  "persons": [
    {"role": "complainant | staff | third_party", "name_or_id": "姓名或标识"}
  ],
  "description": "事件简述（≤80 字）",
  "root_cause": "用户认为的原因（≤50 字），可为 null",
  "demands": ["用户诉求1", "用户诉求2"],
  "current_status": "pending | processing | resolved | escalated",
  "severity": "low | medium | high"
}

【抽取规则】
1. 严格基于原文，不得编造
2. 字段在原文中未体现时填 null
3. severity 判断标准：
   - high：涉及人身安全、重大金额（>1000 元）、媒体曝光风险
   - medium：涉及退款、产品质量、服务态度
   - low：一般咨询性投诉
4. demands 必须来自用户原话或显式表达

【输出格式】
{
  "event": { ...符合上述 Schema },
  "confidence": 0.0-1.0,
  "missing_fields": ["未能抽取的字段列表"]
}

约束：只输出 JSON。
```

### 使用示例

#### 输入
```text
你是 SmartCS 智能客服的事件抽取引擎。请从以下投诉文本中提取事件要素。

【投诉文本】
我 11 月 5 日在你们上海浦东门店买了一台戴尔笔记本，型号 XPS 15，花了 12999 元。回家第三天发现屏幕有坏点，11 月 9 日拿回门店要求退换，店员小王说只能维修不能退换，态度很差。我要求全额退款，并且要求店长出面道歉。我的订单号是 20251105-SH-208。

（Schema、抽取规则同上）
```

#### 预期输出
```json
{
  "event": {
    "event_type": "quality_issue",
    "time": {
      "raw": "11 月 5 日购买 / 11 月 9 日投诉",
      "normalized": "2025-11-05 / 2025-11-09"
    },
    "location": "上海浦东门店",
    "persons": [
      {"role": "complainant", "name_or_id": "用户（未具名）"},
      {"role": "staff", "name_or_id": "店员小王"}
    ],
    "description": "用户 11 月 5 日于上海浦东门店购买戴尔 XPS 15 笔记本，11 月 9 日发现屏幕坏点要求退换，店员仅同意维修且态度差，用户要求全额退款与店长道歉。",
    "root_cause": "用户认为产品质量有问题（屏幕坏点）且店员服务态度差",
    "demands": ["全额退款", "店长出面道歉"],
    "current_status": "pending",
    "severity": "high"
  },
  "confidence": 0.92,
  "missing_fields": []
}
```

### 调优建议
- 温度：0.0
- 事件类型可根据业务扩展（如增加"虚假宣传""隐私泄露"）
- severity 判断标准建议按业务调优，并附"金额阈值"
- 抽取后可自动派单：high → 立即转高级客服
