# 笔记格式规范（note-format）

每个主题一个 markdown 文件。本规范是**权威格式定义**，`add-topic` skill 起草、人工润色、完成检查都以此为准。设计背景见 `@design.md` 第 5 节。

---

## 1. 文件位置与命名

- 路径：`topics/<domain>/NN-slug.md`，`domain` 为 `llm` 或 `systems`。
- 命名：**数字前缀 + 英文 slug**，如 `02-attention.md`、`07-rag-basics.md`。
- **禁止日期前缀**：不要 `2026-06-14-attention.md`。
- 编号与 `syllabus.md` 看板一致。

---

## 2. Frontmatter（YAML，必填）

```yaml
---
topic: Attention 机制          # 中文主题名
domain: llm                    # llm | systems
difficulty: 基础               # 基础 | 进阶 | 高阶
status: drafted                # planned | drafted | polished
prerequisites: [tokenization]  # 前置主题的 slug 数组，可空 []
tags: [transformer, attention, self-attention]
---
```

| 字段 | 取值 | 用途 |
|------|------|------|
| `topic` | 中文主题名 | 显示 |
| `domain` | `llm` / `systems` | 分类、看板分组 |
| `difficulty` | `基础` / `进阶` / `高阶` | 出题难度筛选 |
| `status` | `planned` / `drafted` / `polished` | 产出生命周期 |
| `prerequisites` | slug 数组 | 学习顺序、依赖 |
| `tags` | 关键词数组 | 检索、未来 RAG 过滤 |

---

## 3. 正文结构（六个区块，顺序固定）

```markdown
# <主题中文名>

## 一句话概览
> 是什么 + 为什么重要（一两句，中文）

## 概念讲解
（中文，供学习，由浅入深：直觉 → 原理 → 关键细节/公式；初学者能读懂。
 可分小节、用类比、配简单公式。）

## 面试问答卡
（供复习 / 模拟面试。每张卡自包含，是干净的 RAG 切块；由基础到进阶排列。）

### Q1. <English question?> / <中文问题？>
**难度:** 基础
**Answer (EN):** 简单词 + 保留术语，面试能直接说出口
- point 1
- point 2
**核心答案 (中):**
- 要点 1
- 要点 2
**追问 / 深入 (中):**
- 面试官可能追问 X → 思路怎么答（讲评用中文，可附一句简单英文示范）
**常见误区 (中):**
- 容易答错/混淆的点

### Q2. ...

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文，便于背诵和对照
- (EN) "Self-attention means each word can look at every other word..."
  (中) 每个词都能看句子里其他所有词……

## 延伸阅读
- 论文 / 文档链接（可标注是否核实过）
```

---

## 4. 语言规则

- **概念讲解**：中文（理解优先）。
- **问题、核心答案、口述版**：中英对照。
  - 问题写成 `English question? / 中文问题？`。
  - 答案给 `Answer (EN)` + `核心答案 (中)` 两段。
  - 口述版英文短稿，每句紧跟一行中文。
- **追问 / 误区**：讲评用中文，可附一句简单英文示范答法。
- **英文一律用词简单**：短句、常用词、避免生僻表达；只有**专业术语**保留英文标准写法（self-attention、KV cache、quantization、embedding 等），不硬译成中文。

---

## 5. 问答卡规则

- 每张卡必须含四段：**Answer (EN) + 核心答案(中) + 追问/深入 + 常见误区**。
- 一张卡聚焦一个问题，自包含（不依赖上下文也能读懂）→ 便于将来 RAG 切块。
- 难度标注用 `基础 / 进阶 / 高阶`，同一文件内由易到难排列。
- 核心答案用要点 bullet，不要长段落（面试是口述，要点化便于记忆）。

---

## 6. 准确性要求（详见 `@design.md` 第 7 节）

- 稳定核心知识正常陈述；**版本 / 具体数字 / 最新进展**相关内容标 `⚠️待核实` 或注明时间点。
- 不确定就留空或标注，**不编造**。
- 必要时用 `context7` / web 查证再写。

---

## 7. status 生命周期

```
planned ──add-topic 起草──▶ drafted ──人工润色 + 核验──▶ polished
```

- `planned`：仅在 syllabus 列出，未写。
- `drafted`：Claude 已按本规范起草，待人工润色。
- `polished`：人工已校验技术点、补充理解、确认格式，可用于正式复习/面试。

---

## 8. 完整最小样例

```markdown
---
topic: 解码与采样策略
domain: llm
difficulty: 基础
status: drafted
prerequisites: []
tags: [decoding, sampling, temperature, top-p]
---

# 解码与采样策略

## 一句话概览
> LLM 每步输出的是下一个 token 的概率分布，"采样策略"决定怎么从这个分布里挑词，直接影响生成的随机性和质量。

## 概念讲解
模型每一步算出词表上所有 token 的概率。怎么选下一个 token，就是 decoding：
- **贪心 / greedy**：每步选概率最高的，确定但单调。
- **temperature**：调整分布的"尖锐"程度，越高越随机。
- **top-k / top-p**：只在最可能的几个候选里采样，平衡多样性与相关性。

## 面试问答卡

### Q1. What is temperature in decoding? / 解码里的 temperature 是什么？
**难度:** 基础
**Answer (EN):**
- Temperature scales the logits before softmax.
- Higher temperature makes the output more random; lower makes it more focused.
**核心答案 (中):**
- temperature 在 softmax 之前缩放 logits。
- 越高输出越随机，越低越确定、越聚焦。
**追问 / 深入 (中):**
- 追问"temperature=0 等于什么？" → 约等于 greedy decoding，每步选最大概率的词。
**常见误区 (中):**
- 以为 temperature 改变模型权重；其实只改采样这一步。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿
- (EN) "Temperature controls randomness. Low temperature gives safe, focused answers; high temperature gives diverse, creative ones."
  (中) temperature 控制随机性。低温给稳妥聚焦的答案，高温给多样有创意的答案。

## 延伸阅读
- The Curious Case of Neural Text Degeneration（top-p / nucleus sampling 原论文）
```
