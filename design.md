# AIE 知识库 — 设计文档

> AI Engineer 面试备考知识库。本文件是项目的设计说明书（spec），定义目标、结构、格式规范与工作流。

最后更新：2026-06-14

---

## 1. 目标与背景

构建一个**本地、问答式的 AI Engineer 面试知识库**，用于：

1. **自己复习** —— 以"问题 / 答案"卡片形式刷知识点；
2. **Claude 模拟面试** —— 让 Claude Code 拿这些笔记给我做模拟面试、追问、评分、找薄弱点。

定位是**学习 + 备考**双用途。内容聚焦现代以 LLM 为核心的 AI Engineer 画像。

---

## 2. 关键决策记录

| 维度 | 决策 |
|------|------|
| 系统形态 | **Phase 1：Claude Code 当引擎**（不开发额外软件）。内容是结构化 markdown 问答笔记；靠 `CLAUDE.md` + skill 驱动出题/模拟面试/评分 |
| 内容范围 | **LLM/GenAI** + **AI 系统工程**（不含传统 ML/DL 理论、不含刷题 / 通用系统设计）|
| 使用者水平 | **初学 / 系统入门** → 笔记从概念讲起、由浅入深；模拟面试从基础难度起步 |
| 内容产出 | **混合：Claude 起草 → 用户润色**（status 流转体现）|
| 内容组织 | **方案 A：主题文件内嵌问答卡** —— 每主题一个 md = 简短讲解 + 一组问答卡 |
| 语言约定 | **概念讲解用中文**（便于理解）；**面试要开口的部分——问题 / 核心答案 / 口述版——做中英对照**。英文一律**用词简单 + 保留专业术语**（面试是英文，但用户英文基础弱）|
| 模拟面试语言 | **英文进行 + 中文讲评**：考官英文问、用户英文答；答完用中文讲评（好在哪 / 漏了什么）+ 教更简单的英文说法；卡壳可用中文兜底 |
| 未来演进 | 内容格式对 RAG 友好；**Phase 2（可选）**：内容够丰富后升级为真正的检索问答系统 |

---

## 3. 范围

**In scope（Phase 1）**
- 仓库骨架、笔记格式规范、CLAUDE.md、syllabus 看板
- 两个项目级 skill：`add-topic`、`interview`
- 初始大纲（约 21 个主题，见第 10 节）

**Out of scope（Phase 1）**
- 任何独立软件 / 后端 / 前端 / 向量检索实现
- 传统 ML/DL 数学理论、LeetCode 刷题、通用系统设计
- Anki 导出（可作为 Phase 2 增量）

---

## 4. 仓库结构

```
AIE/
├── CLAUDE.md                    # 项目仪表盘：铁律表、准确性协议、完成清单、导航
├── README.md                    # 这是什么 + 怎么用（命令速查）
├── design.md                    # 本设计文档
├── syllabus.md                  # 大纲 + 进度看板（一张表）
├── cards.html                   # 生成的 Anki 风格抽认卡查看器（视图，勿手改）
├── tools/build_cards.py         # 从 topics/ 生成 cards.html
├── topics/
│   ├── llm/                     # 01-transformer.md, 02-attention.md ...
│   └── systems/                 # 01-serving.md, 02-latency.md ...
├── interviews/                  # 模拟面试记录 + 评分，如 2026-06-14-rag.md
└── .claude/
    ├── rules/
    │   └── note-format.md       # 详细笔记格式规范（CLAUDE.md 用 @ 引用）
    └── skills/
        ├── add-topic/SKILL.md   # 起草一篇新主题笔记
        └── interview/SKILL.md   # 模拟面试 / 快速复习
```

**设计原则**：CLAUDE.md 保持精简、当"仪表盘"，详细规范拆到 `.claude/rules/` 并用 `@` 引用（借鉴 JobPin AI CLAUDE.md 的导航模式）。一张 `syllabus.md` 同时充当大纲和进度看板，避免多个追踪文件互相打架。

---

## 5. 笔记格式规范

每个主题一个 markdown 文件，结构如下（详细版落在 `.claude/rules/note-format.md`）：

```markdown
---
topic: Attention 机制
domain: llm                 # llm | systems
difficulty: 基础            # 基础 | 进阶 | 高阶
status: drafted             # planned | drafted | polished
prerequisites: [tokenization]
tags: [transformer, attention, self-attention]
---

# Attention 机制

## 一句话概览
> 是什么 + 为什么重要（一两句，中文）

## 概念讲解
（中文，供学习，由浅入深：直觉 → 原理 → 关键细节/公式；初学者能读懂）

## 面试问答卡
（供复习 / 模拟面试，每张卡自包含，是干净的 RAG 切块；问题与答案中英对照）

### Q1. What is self-attention and why does a Transformer need it? / 什么是 self-attention？为什么 Transformer 需要它？
**难度:** 基础
**Answer (EN):** （简单词 + 保留术语，面试能直接说）
- point 1
- point 2
**核心答案 (中):**
- 要点 1
- 要点 2
**追问 / 深入 (中):**
- 面试官可能追问 X → 思路怎么答（讲评用中文，可附一句简单英文示范）
**常见误区 (中):**
- …

### Q2. ...

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文，便于背诵和对照
- (EN) "..."
  (中) ……

## 延伸阅读
- 论文 / 文档链接
```

**frontmatter 字段**

| 字段 | 取值 | 用途 |
|------|------|------|
| `topic` | 中文主题名 | 显示 |
| `domain` | `llm` / `systems` | 分类、看板分组 |
| `difficulty` | `基础` / `进阶` / `高阶` | 出题难度筛选 |
| `status` | `planned` / `drafted` / `polished` | 产出生命周期 |
| `prerequisites` | 主题文件名数组 | 学习顺序、依赖 |
| `tags` | 关键词数组 | 检索、未来 RAG 过滤 |

**关键约束**
- 每张问答卡必须含 **Answer (EN) + 核心答案(中) + 追问/深入 + 常见误区** 四段。
- **中英对照范围**：问题、核心答案、口述版做中英对照；概念讲解用中文；追问/误区的讲评用中文（可附简单英文示范答法）。
- **英文一律用词简单**：短句、常用词、避免生僻表达；只有**专业术语**保留英文标准写法（如 self-attention、KV cache、quantization），不硬译。
- 文件名用**数字前缀、不加日期**：`02-attention.md`（不要 `2026-06-14-attention.md`）。
- 卡片设计为自包含切块，便于将来 RAG。

---

## 6. CLAUDE.md 内容

CLAUDE.md 当"仪表盘"，包含以下区块：

### 6.1 项目目的与语言约定
一句话说明项目用途；概念讲解用中文，面试要开口的部分（问题/核心答案/口述版）中英对照，英文用词简单 + 保留专业术语；模拟面试英文进行 + 中文讲评。

### 6.2 仓库结构（精简版）
放一份第 4 节那样的精简目录树，让 Claude 每次会话都知道文件该放哪、各目录干什么。权威/带原则的完整版在 `design.md` 第 4 节。

### 6.3 Critical Rules（铁律表）

| 规则 | 说明 |
|------|------|
| **技术准确性第一** | 不编造；不确定就明确标注 `⚠️待核实`，宁可留空也不写错 |
| 笔记必须遵循统一格式 | 见 `@.claude/rules/note-format.md` |
| 讲解中文、面试部分中英对照 | 问题/核心答案/口述版做中英对照；讲解用中文 |
| 英文用词简单 + 保留术语 | 短句常用词，只有专业术语用英文标准写法 |
| 文件名数字前缀、不加日期 | `02-attention.md` |
| 改完内容必须更新看板 | 同步 `syllabus.md` |
| status 按生命周期流转 | `planned → drafted → polished` |

### 6.4 准确性协议（见第 7 节，CLAUDE.md 放精简版 + 链接）

### 6.5 完成前 Verification Checklist（见第 8 节）

### 6.6 导航表

| 需要 | 看 |
|------|-----|
| 笔记格式规范 | `@.claude/rules/note-format.md` |
| 大纲 / 进度 | `@syllabus.md` |
| 设计说明 | `@design.md` |
| 起草新主题 | skill `add-topic` |
| 模拟面试 / 复习 | skill `interview` |

---

## 7. 准确性协议（核心补充）

代码项目靠"跑测试"保证质量；本知识库的内容由 **Claude 起草**，最大风险是**幻觉 / 讲错** —— 而这是面试备考，讲错会误导用户。因此起草任何笔记时遵循：

1. **分层标注可信度**
   - 稳定的核心知识（如 self-attention 的定义、QKV 机制）→ 正常陈述。
   - 与**版本 / 具体数字 / 最新进展**相关的内容（如某模型上下文窗口大小、某库最新 API、SOTA 排名）→ 标注 `⚠️待核实` 或注明"截至 XX 时间"。
2. **不确定就留空或标注**，绝不为了"看起来完整"而编造细节。
3. **必要时查证再写**：对版本相关 / 最新进展 / 关键数字的内容，可用 `context7`（库文档）或 web 搜索核实后再落笔。
4. **追问要诚实**：模拟面试中遇到笔记没覆盖、自己也不确定的点，明确说明而不是硬编。
5. **润色环节是第二道关**：用户润色时人工校验技术点，确认后才把 status 改为 `polished`。

---

## 8. 完成前 Verification Checklist

把一篇笔记标成 `polished`（或宣布某主题完成）前，逐项确认：

- [ ] frontmatter 字段完整（topic / domain / difficulty / status / tags）
- [ ] 有"一句话概览" + "概念讲解" + "问答卡" + "口述版"
- [ ] 每张问答卡含 Answer(EN) + 核心答案(中) + 追问/深入 + 常见误区
- [ ] 问题 / 核心答案 / 口述版已做中英对照；英文用词简单、只术语保留英文
- [ ] 版本/数字/最新进展类内容已核对或已标 `⚠️待核实`
- [ ] 文件名符合数字前缀规范
- [ ] `syllabus.md` 看板已同步更新

---

## 9. Skills

项目级 skill，放在 `.claude/skills/`。

### 9.1 `add-topic` — 起草一篇新主题笔记
**触发**：用户给出主题名（或从 syllabus 选 `planned` 的主题）。
**流程**：
1. 读 `note-format.md` 规范与 `syllabus.md`。
2. 按标准格式起草整篇：一句话概览 → 概念讲解（中文、由浅入深）→ 问答卡（基础到进阶，每卡含 Answer(EN) + 核心答案(中) + 追问 + 误区 四段，问题中英对照）→ 口述版（英文短稿 + 中文对照）→ 延伸阅读。
3. 遵守准确性协议（标注待核实项）；英文一律用词简单 + 保留专业术语。
4. 写入 `topics/<domain>/NN-xxx.md`，置 `status: drafted`。
5. 更新 `syllabus.md` 看板。
6. 提示用户润色。

### 9.2 `interview` — 模拟面试 / 快速复习
两种模式：

**模拟面试模式**（英文进行 + 中文讲评）
1. 选范围（domain / 主题 / 难度）。
2. **一次问一题**，**用英文提问**，从相关问答卡抽题，可即兴生成英文追问。
3. 用户**用英文作答**（卡壳可用中文兜底）→ 对照卡片"核心答案"评估 → **用中文讲评**（答得好的点 / 漏掉的点 / 误区）+ **教更简单的英文说法**（给出可直接背的简单英文示范）。
4. 一场结束后把记录写入 `interviews/YYYY-MM-DD-<主题>.md`（题目、用户作答要点、评分、薄弱点、待改进的英文表达）。
5. 更新 `syllabus.md` 看板的"掌握度 / 薄弱点 / 上次复习"。

**快速复习模式**
- 按"上次复习时间 + 掌握度"挑卡（类间隔重复），快问快答刷一遍，更新掌握度。比完整模拟面试轻量。

---

## 10. syllabus.md 看板格式

单张表，既是大纲也是进度追踪：

```markdown
# 大纲 & 进度看板

## LLM / GenAI
| # | 主题 | 文件 | 难度 | 内容状态 | 掌握度 | 薄弱点 | 上次复习 |
|---|------|------|------|----------|--------|--------|----------|
| 1 | Transformer 架构 | 01-transformer.md | 基础 | planned | - | - | - |
| 2 | Attention | 02-attention.md | 基础 | drafted | 🟡 | KV cache | 2026-06-14 |

## AI 系统工程
| # | 主题 | ... |
```

- 内容状态：`planned / drafted / polished`
- 掌握度：🔴 弱 / 🟡 中 / 🟢 好（由模拟面试 / 复习更新）

---

## 11. 初始大纲（可增删）

**LLM / GenAI**
1. Transformer 架构总览
2. Attention（self-attention / multi-head / 起头 KV cache）
3. Tokenization & Embeddings
4. 预训练与训练目标（next-token prediction 等）
5. 解码与采样策略（temperature / top-k / top-p / beam）
6. Prompting & In-context Learning
7. RAG 基础（检索 + 生成 / chunking / 向量检索）
8. RAG 进阶（reranking / hybrid search / 评估）
9. Fine-tuning（full / LoRA-PEFT / instruction tuning / RLHF / DPO 概念）
10. Agents（tool use / ReAct / planning / memory）
11. Evals（离线/在线评估 / LLM-as-judge）
12. 幻觉与对齐（hallucination / safety / guardrails）
13. 多模态（基础概念）

**AI 系统工程**
1. 推理服务与部署（serving / batching / KV cache / quantization）
2. 延迟与吞吐优化（latency vs throughput / streaming / speculative decoding）
3. 向量数据库（HNSW / IVF / 相似度 / 选型）
4. LLM 应用架构（API 编排 / caching / fallback / rate limiting）
5. 成本优化（token 成本 / 模型选型 / caching / 蒸馏）
6. 监控与可观测性（tracing / logging / drift / 线上评估）
7. MLOps / LLMOps（CI-CD / versioning / 部署模式）
8. 数据与隐私（PII / data pipeline / security）

---

## 12. 工作流

**内容生命周期**
```
planned ──add-topic──▶ drafted ──用户润色+核验──▶ polished
```

**典型学习流**
1. 从 syllabus 选一个 `planned` 主题 → 跑 `add-topic` 起草。
2. 阅读"概念讲解"学习 → 润色补充自己的理解 → 标 `polished`。
3. 用 `interview` 快速复习模式刷问答卡。

**典型备考流**
1. 攒够若干 `polished` 主题后，跑 `interview` 模拟面试模式。
2. 看 `interviews/` 记录与看板薄弱点，回头补强对应主题。

---

## 12.5 抽认卡视图（cards.html，Anki 风格）

为了比 raw markdown 更直观地刷题，提供一个**生成式的 HTML 抽认卡视图**。**markdown 仍是唯一数据源**，HTML 只是视图。

- **生成**：`python3 tools/build_cards.py` 读 `topics/**/*.md`，解析问答卡，输出自包含的 `cards.html`（零依赖，双击用浏览器打开）。改完笔记重跑即可。
- **解析**：按 note-format 提取 frontmatter（topic/domain/difficulty）+ 每张卡的 `问题(中英) / Answer(EN) / 核心答案(中) / 追问 / 误区`。
- **学习模式（Anki 风格）**：一次一张卡 → 显示答案（空格）→ 按 **重来 / 难 / 良 / 简单**（键 1–4）评分；用简化 SM-2 间隔重复(SRS)调度，进度存浏览器 `localStorage`（不写回仓库）。
- **浏览模式**：网格列出全部卡，可展开看答案。
- **筛选**：按 领域 / 主题 / 难度；语言 中英 / EN / 中 切换。
- **边界**：`cards.html` 是生成产物、**不要手改**；SRS 进度只在浏览器本地，跨设备不同步（够用；要跨端再考虑 Phase 2 的 Anki 导出）。

## 13. Phase 2 展望（可选，暂不实现）

内容够丰富后，可把笔记升级为真正的检索问答系统：用 frontmatter + 问答卡切块做 embedding，建向量索引，做语义检索（这本身就是 RAG 练手项目）；并可增量支持导出 Anki。当前格式已为此预留。

---

## 14. 落地实施顺序

1. 写骨架文件：`CLAUDE.md`、`README.md`、`syllabus.md`（初始大纲，全部 `planned`）。
2. 写 `.claude/rules/note-format.md`（详细格式规范）。
3. 写两个 skill：`.claude/skills/add-topic/SKILL.md`、`.claude/skills/interview/SKILL.md`。
4. 用 `add-topic` 起草 1 个样板主题（建议 `02-attention.md`），验证整套格式 + 准确性协议跑通。
5. 用户润色样板 → 标 `polished` → 用 `interview` 跑一次小测验证陪练流程。
```
