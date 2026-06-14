---
name: add-topic
description: Use when adding or drafting a new topic note for the AIE interview knowledge base. Drafts a full bilingual (中英对照) note following note-format.md, sets status to drafted, and updates the syllabus board. Claude drafts, user polishes.
---

# add-topic — 起草一篇新主题笔记

给 AIE 知识库起草一篇新主题笔记。**Claude 起草草稿，用户随后润色。**

## 何时用
- 用户给出一个主题名要起草。
- 或从 `syllabus.md` 选一个 `status: planned` 的主题。

## 流程

1. **读规范**：读 `.claude/rules/note-format.md`（格式权威）和 `syllabus.md`（确认编号、domain、难度、是否已存在）。
2. **确认范围**：和用户确认主题名、domain（`llm`/`systems`）、难度、文件编号。若主题已在 syllabus，沿用其编号 / 文件名。
3. **起草**，严格按 note-format 的六区块顺序：
   - 一句话概览（中文）
   - 概念讲解（中文，由浅入深，初学者能懂）
   - 面试问答卡：**3–6 张**，由易到难；每张含 **Answer(EN) + 核心答案(中) + 追问/深入(中) + 常见误区(中)**；问题写成 `English question? / 中文问题？`
   - 速记 / 口述版（英文短稿 + 每句中文对照）
   - 延伸阅读
4. **语言**：讲解中文；问题 / 核心答案 / 口述版中英对照；英文一律**用词简单 + 保留专业术语**。
5. **准确性协议**（见 CLAUDE.md / design.md 第 7 节）：版本 / 数字 / 最新进展类内容标 `⚠️待核实` 或注明时间；不确定不编造；必要时用 `context7`（库文档）或 web 查证后再写。
6. **写文件**：`topics/<domain>/NN-slug.md`，frontmatter `status: drafted`。
7. **更新看板**：把 `syllabus.md` 对应行的"内容状态"改为 `drafted`。
8. **重新生成抽认卡**：跑 `python3 tools/build_cards.py`，让新卡进入 `cards.html`。
9. **过完成清单**（见 CLAUDE.md），然后提示用户润色；润色完由用户把 status 改 `polished`。

## 注意
- **不要直接标 `polished`** —— 那是人工润色 + 核验后的状态。
- 一次只起草一个主题，保持质量。
- 起草后简要告诉用户：写了几张卡、哪些点标了 `⚠️待核实` 需要重点核对。
