# AIE — AI Engineer 面试知识库

一个本地的、问答式的 AI Engineer 面试备考知识库。聚焦 **LLM/GenAI** 与 **AI 系统工程**，面向**英文面试**。

## 这是什么

- 内容是结构化 markdown 问答笔记，每个主题一个文件：**概念讲解（中文）** + **面试问答卡（中英对照）** + **口述版（英文短稿 + 中文对照）**。
- 两种用法：**自己刷问答复习**；**让 Claude Code 拿笔记给你做英文模拟面试 + 中文讲评**。
- 内容由 **Claude 起草、你润色**。

## 怎么用

| 我想… | 怎么做 |
|-------|--------|
| 新增一个主题笔记 | 跑 skill `add-topic`，给主题名（或从 `syllabus.md` 选 `planned` 的）|
| 润色草稿 | 读 `topics/` 下的草稿，改完把 frontmatter `status` 改为 `polished` |
| 模拟面试 | 跑 skill `interview` → 选**模拟面试**模式（英文问答 + 中文讲评）|
| 快速复习 | 跑 skill `interview` → 选**快速复习**模式（按掌握度刷卡）|
| 看进度 / 薄弱点 | 看 `syllabus.md` 看板 |

## 目录

- `topics/llm/`、`topics/systems/` — 主题笔记
- `syllabus.md` — 大纲 + 进度看板
- `interviews/` — 模拟面试记录
- `design.md` — 完整设计说明
- `CLAUDE.md` — Claude 工作规范
- `.claude/rules/note-format.md` — 笔记格式规范

## 学习流程

```
planned ──add-topic 起草──▶ drafted ──你润色 + 核验──▶ polished ──interview 复习/模拟面试
```
