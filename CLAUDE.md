# CLAUDE.md

本文件指导 Claude Code 在 AIE 知识库中工作。权威/完整设计见 `@design.md`。

## 项目目的

AI Engineer 面试备考知识库，聚焦 **LLM/GenAI** + **AI 系统工程**。内容是结构化 markdown 问答笔记，用于：自己刷问答复习 + 让 Claude 拿笔记做模拟面试。使用者为**初学/系统入门**，**面试为英文**。

## 语言约定

- **概念讲解用中文**（便于理解）。
- **面试要开口的部分——问题 / 核心答案 / 口述版——做中英对照**。
- 英文一律**用词简单 + 保留专业术语**：短句、常用词；只有术语（如 self-attention、KV cache、quantization）用英文标准写法，不硬译。
- **模拟面试英文进行 + 中文讲评**。

## 仓库结构

```
AIE/
├── CLAUDE.md          # 本文件：操作仪表盘
├── README.md          # 怎么用
├── design.md          # 完整设计说明（权威）
├── syllabus.md        # 大纲 + 进度看板
├── cards.html         # 生成的 Anki 风格抽认卡查看器（视图，勿手改）
├── tools/build_cards.py  # 从 topics/ 生成 cards.html 的脚本
├── topics/
│   ├── llm/           # LLM/GenAI 主题笔记
│   └── systems/       # AI 系统工程主题笔记
├── interviews/        # 模拟面试记录 + 评分
└── .claude/
    ├── rules/note-format.md      # 详细笔记格式规范
    └── skills/{add-topic,interview}/
```

> **markdown 是唯一数据源**；`cards.html` 是从 `topics/` 生成的视图，**不要手改**。改完任何笔记后重新生成：`python3 tools/build_cards.py`。

## Critical Rules（铁律，勿违反）

| 规则 | 说明 |
|------|------|
| **技术准确性第一** | 不编造；不确定就标 `⚠️待核实`，宁可留空也不写错 |
| 笔记遵循统一格式 | 见 `@.claude/rules/note-format.md` |
| 讲解中文、面试部分中英对照 | 问题 / 核心答案 / 口述版中英对照；讲解用中文 |
| 英文用词简单 + 保留术语 | 短句常用词，只有专业术语用英文标准写法 |
| 文件名数字前缀、不加日期 | `02-attention.md`（不要 `2026-06-14-attention.md`）|
| 改完内容必须更新看板 | 同步 `syllabus.md` |
| 改完笔记重新生成卡片 | `python3 tools/build_cards.py`（`cards.html` 是视图，勿手改）|
| status 按生命周期流转 | `planned → drafted → polished` |

## 准确性协议（精简版）

内容由 Claude 起草，最大风险是**幻觉 / 讲错**（这是面试备考，讲错会误导用户）。起草任何笔记时：

1. 稳定核心知识正常陈述；与**版本 / 具体数字 / 最新进展**相关的内容标 `⚠️待核实` 或注明"截至 XX 时间"。
2. 不确定就留空或标注，**绝不**为"看起来完整"而编造细节。
3. 必要时用 `context7`（库文档）或 web 搜索查证后再写。
4. 模拟面试遇到笔记没覆盖 / 自己不确定的点，**诚实说明**，不硬编。

完整版见 `@design.md` 第 7 节。

## 完成前检查（标 polished 或宣布完成前逐项确认）

- [ ] frontmatter 完整（topic / domain / difficulty / status / tags）
- [ ] 有 一句话概览 + 概念讲解 + 问答卡 + 口述版
- [ ] 每张问答卡含 Answer(EN) + 核心答案(中) + 追问/深入 + 常见误区
- [ ] 问题 / 核心答案 / 口述版已中英对照；英文用词简单、只术语保留英文
- [ ] 版本 / 数字 / 最新进展类已核对或已标 `⚠️待核实`
- [ ] 文件名合规；`syllabus.md` 看板已同步更新

## 导航

| 需要 | 看 |
|------|-----|
| 笔记格式规范 | `@.claude/rules/note-format.md` |
| 大纲 / 进度 | `@syllabus.md` |
| 完整设计 | `@design.md` |
| 起草新主题 | skill `add-topic` |
| 模拟面试 / 复习 | skill `interview` |
| 抽认卡复习（浏览器）| 跑 `python3 tools/build_cards.py` 后打开 `cards.html` |
