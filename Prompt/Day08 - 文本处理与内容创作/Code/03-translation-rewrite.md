# 翻译与改写模板合集

> 本文件包含 4 个模板：多语言翻译 / 风格化翻译 / 文本润色 / 文本简化。每个模板含完整 Prompt 与对比示例，覆盖客服与营销场景的常见需求。

---

## 模板 1：多语言翻译 - 中英互译含术语表

### 模板说明
- 用途：中英互译，通过术语表保证领域词汇一致性
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{source_text}}`、`{{source_lang}}`、`{{target_lang}}`、`{{glossary}}`

### 完整模板

```text
你是专业翻译，精通 {{source_lang}} 与 {{target_lang}}。请将以下文本从 {{source_lang}} 翻译为 {{target_lang}}。

【源文本】
{{source_text}}

【术语表】（必须严格遵守）
{{glossary}}

【翻译要求】
1. 术语表中的词必须按指定译法，不得自由发挥
2. 保持原文语义，不增删信息
3. 句式符合目标语言习惯，避免翻译腔
4. 数字、日期、单位保留原文格式或按目标语言习惯转换
5. 保留原文中的 HTML/Markdown 标记

【输出格式】
{
  "translation": "译文",
  "glossary_applied": [
    {"source": "原文术语", "target": "译文术语", "occurrences": 次数}
  ],
  "notes": "翻译中需说明的要点（可为空）"
}

约束：只输出 JSON。
```

### 使用示例

#### 输入
```text
你是专业翻译，精通中文与英文。请将以下文本从中文翻译为英文。

【源文本】
我们支持 7 天无理由退货。商品需保持完好，配件齐全。质量问题 15 天内可退换，运费由平台承担。跨境购商品不适用 7 天无理由退货。

【术语表】
- 7 天无理由退货 → 7-day no-reason return
- 质量问题 → quality issue
- 跨境购 → cross-border purchase
- 运费 → shipping fee
- 平台 → the platform

【翻译要求】
1. 术语表必须严格遵守
2. 保持原文语义
3. 句式符合英文习惯

（输出格式同上）
```

#### 预期输出
```json
{
  "translation": "We support the 7-day no-reason return. Items must remain in good condition with all accessories included. Items with quality issues can be returned or exchanged within 15 days, with shipping fees borne by the platform. The 7-day no-reason return does not apply to cross-border purchases.",
  "glossary_applied": [
    {"source": "7 天无理由退货", "target": "7-day no-reason return", "occurrences": 2},
    {"source": "质量问题", "target": "quality issue", "occurrences": 1},
    {"source": "运费", "target": "shipping fee", "occurrences": 1},
    {"source": "平台", "target": "the platform", "occurrences": 1},
    {"source": "跨境购", "target": "cross-border purchase", "occurrences": 1}
  ],
  "notes": "原文'完好'译为'in good condition'，'配件齐全'译为'with all accessories included'，更符合英文表达。"
}
```

### 调优建议
- 温度：0.3
- 术语表建议 10-30 个词为宜，过多会让 LLM 困惑
- 长文本建议分句翻译，再合并校对
- 若术语有歧义，可在术语表中加注释（如"运费（用户承担时）→ shipping fee payable by user"）

---

## 模板 2：风格化翻译 - 商务正式 vs 口语化

### 模板说明
- 用途：将同一文本翻译为不同风格的译文，便于对比选择
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{source_text}}`、`{{source_lang}}`、`{{target_lang}}`

### 完整模板

```text
你是专业翻译。请将以下文本从 {{source_lang}} 翻译为 {{target_lang}}，并分别提供两种风格的译文。

【源文本】
{{source_text}}

【风格要求】
风格 A - 商务正式：
- 词汇：正式、专业
- 句式：完整、严谨
- 适用：商务邮件、官方文档、合同条款

风格 B - 口语化：
- 词汇：日常、亲切
- 句式：简短、灵活
- 适用：社媒、客服对话、用户通知

【输出格式】
{
  "style_a_formal": {
    "translation": "商务正式译文",
    "features": ["该风格的典型特征1", "特征2"]
  },
  "style_b_casual": {
    "translation": "口语化译文",
    "features": ["该风格的典型特征1", "特征2"]
  },
  "comparison": "两种风格的核心差异（≤80 字）"
}

约束：
1. 两版译文语义必须一致
2. 只输出 JSON
```

### 使用示例

#### 输入
```text
你是专业翻译。请将以下文本从中文翻译为英文，并分别提供两种风格的译文。

【源文本】
您的订单已发货，预计 3 个工作日内送达。如有问题请联系客服。

【风格要求】
风格 A - 商务正式：词汇正式、句式严谨，适用商务邮件
风格 B - 口语化：词汇日常、句式简短，适用社媒 / 客服对话

（输出格式同上）
```

#### 预期输出
```json
{
  "style_a_formal": {
    "translation": "Your order has been dispatched and is expected to be delivered within three business days. Should you have any inquiries, please contact our customer service.",
    "features": [
      "使用 dispatched / expected to be 等正式词汇",
      "Should you have... 虚拟语气句式更显正式",
      "完整句式，无缩写"
    ]
  },
  "style_b_casual": {
    "translation": "Your order's on the way! It should arrive in about 3 business days. Any questions? Just ping our support team.",
    "features": [
      "使用 on the way / ping 等口语词",
      "感叹号与短句增强亲切感",
      "Any questions? 疑问句直接对话"
    ]
  },
  "comparison": "正式版用 dispatched / Should you have 等书面语，句式完整；口语版用 on the way / ping，感叹号与短句营造对话感。"
}
```

### 调优建议
- 温度：0.4（允许一定创造性）
- 可扩展为三风格：正式 / 口语 / 文学
- 若用于品牌传播，追加"品牌调性"约束

---

## 模板 3：文本润色 - 提升客服回复专业度

### 模板说明
- 用途：将口语化、生硬的客服回复润色为专业、共情的版本
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{original_reply}}`、`{{user_message}}`、`{{brand_tone}}`

### 完整模板

```text
你是 SmartCS 客服回复润色引擎。请将以下客服回复润色为更专业的版本。

【用户消息】
{{user_message}}

【原始客服回复】
{{original_reply}}

【品牌调性】
{{brand_tone}}

【润色要求】
1. 保持原意不变（事实信息、承诺、处理方案不得修改）
2. 提升维度：
   - 共情：先认可用户感受
   - 专业：用词准确，避免口头禅
   - 简洁：单次回复 ≤150 字
   - 行动：明确下一步动作
3. 禁止：
   - 承诺原始回复中未提及的事项
   - 使用"亲""小可爱"等过度亲昵称呼
   - 推卸责任的话术
4. 保留关键信息：订单号、时效、金额等数字

【输出格式】
{
  "polished_reply": "润色后的回复",
  "changes": [
    {"type": "共情/专业/简洁/行动", "before": "原文片段", "after": "润色后片段", "reason": "改动原因"}
  ],
  "tone_check": {
    "empathy": "高/中/低",
    "professionalism": "高/中/低",
    "conciseness": "高/中/低"
  }
}

约束：只输出 JSON。
```

### 使用示例

#### 输入
```text
你是 SmartCS 客服回复润色引擎。请将以下客服回复润色为更专业的版本。

【用户消息】
我等的快递都三天了还没到，你们是不是搞丢了？

【原始客服回复】
亲，快递没丢，正在路上，再等等。

【品牌调性】
专业、共情、简洁。品牌名 SmartCS。

【润色要求】
1. 保持原意（快递未丢、正在配送）
2. 提升共情、专业、简洁、行动四维度
3. ≤150 字

（输出格式同上）
```

#### 预期输出
```json
{
  "polished_reply": "理解您的着急，让您久等了。我已核实您的订单，快递仍在正常配送中，未丢失。我为您加急备注，预计明天送达。如有进一步问题，请随时联系 SmartCS。",
  "changes": [
    {"type": "共情", "before": "亲", "after": "理解您的着急，让您久等了", "reason": "用共情开头替代亲昵称呼，更专业"},
    {"type": "专业", "before": "正在路上", "after": "仍在正常配送中，未丢失", "reason": "用准确表述替代口语化表达"},
    {"type": "行动", "before": "再等等", "after": "我为您加急备注，预计明天送达", "reason": "给出明确下一步与时效"}
  ],
  "tone_check": {
    "empathy": "高",
    "professionalism": "高",
    "conciseness": "高"
  }
}
```

### 调优建议
- 温度：0.4
- changes 字段便于客服培训，可定期归纳常见改动模式
- 若品牌调性偏活泼，可在 brand_tone 中说明（如"活泼、亲切、年轻化"）

---

## 模板 4：文本简化 - 将复杂政策简化为用户易懂的语言

### 模板说明
- 用途：把复杂政策文本转为用户友好的简化版
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{policy_text}}`、`{{target_audience}}`、`{{max_words}}`

### 完整模板

```text
你是用户沟通专家。请将以下政策文本简化为用户易懂的版本。

【政策原文】
{{policy_text}}

【目标读者】
{{target_audience}}

【简化要求】
1. 字数限制：不超过 {{max_words}} 字
2. 必须保留：
   - 关键时间节点（天数 / 日期）
   - 关键金额 / 比例
   - 用户的核心权利与义务
3. 必须做到：
   - 用短句，每句 ≤25 字
   - 避免法律术语，转为日常表达
   - 用"你可以...""你需要..."等用户视角表述
   - 关键信息用列表呈现
4. 不得丢失重要条件（如"商品需保持完好"）

【输出格式】
{
  "simplified_text": "简化版正文",
  "key_points": ["关键点1", "关键点2", "..."],
  "glossary": [
    {"original": "原文术语", "simplified": "简化后表达"}
  ],
  "readability_check": {
    "avg_sentence_length": "平均句长",
    "jargon_removed": ["去除的术语1", "..."]
  }
}

约束：
1. 不得添加原文没有的信息
2. 只输出 JSON
```

### 使用示例

#### 输入
```text
你是用户沟通专家。请将以下政策文本简化为用户易懂的版本。

【政策原文】
本平台所售实物商品，自消费者签收之日起 7 个自然日内，享有无理由退货权利，但商品应当保持完好，配件、说明书、赠品齐全，且不属于定制类、鲜活易腐类、数字化内容、已拆封个人卫生用品等不适用情形。跨境购商品因涉及海关清关与税务，不适用 7 天无理由退货。质量问题自签收起 15 个自然日内可主张退换货，相关运费由平台承担。

【目标读者】
普通消费者，无法律背景

【简化要求】
1. 不超过 150 字
2. 保留关键时间、金额、条件
3. 短句、用户视角、列表化

（输出格式同上）
```

#### 预期输出
```json
{
  "simplified_text": "你可以 7 天内无理由退货，但需要：\n- 商品完好，配件齐全\n- 不是定制、生鲜、数字内容、已拆封卫生用品\n- 不是跨境购商品\n\n如果是质量问题，15 天内可以退换，运费我们承担。",
  "key_points": [
    "7 天无理由退货（商品完好）",
    "质量问题 15 天内可退换，运费平台承担",
    "定制 / 生鲜 / 数字内容 / 跨境购不适用 7 天无理由"
  ],
  "glossary": [
    {"original": "自然日", "simplified": "天"},
    {"original": "签收之日起", "simplified": "收到货后"},
    {"original": "主张退换货", "simplified": "可以退换"},
    {"original": "不适用情形", "simplified": "不适用"}
  ],
  "readability_check": {
    "avg_sentence_length": "18 字",
    "jargon_removed": ["自然日", "签收之日起", "主张", "不适用情形", "数字化内容"]
  }
}
```

### 调优建议
- 温度：0.3
- 简化后建议让真实用户测试理解度
- 若政策极长，先用分块摘要切分，再分别简化
- 可追加"附原文条款编号便于核对"
