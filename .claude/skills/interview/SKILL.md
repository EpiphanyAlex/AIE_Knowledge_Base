---
name: interview
description: Use when the user wants to practice for AI Engineer interviews. Runs a mock interview (English questions + Chinese feedback) or a quick spaced-review session using the AIE knowledge base notes, then logs results and updates the syllabus board.
---

# interview — 模拟面试 / 快速复习

拿 AIE 知识库的笔记给用户陪练。两种模式，**开场先问用户选哪种**。

## 通用准备
- 读 `syllabus.md`：看哪些主题 `polished`（优先）/ `drafted`，以及掌握度与薄弱点。
- 只从已写出的笔记（`topics/`）的问答卡抽题；笔记没覆盖的点若要问，遵守准确性协议、诚实说明不确定。

## 模式一：模拟面试（英文进行 + 中文讲评）

1. **选范围**：问用户练哪个 domain / 主题 / 难度，几道题。
2. **一次问一题，用英文提问**（从相关问答卡抽题，可即兴生成英文追问）。问完**停下等用户作答，不要自问自答**。
3. 用户**用英文作答**（卡壳允许中文兜底）。
4. **讲评（中文）**：对照卡片"核心答案"评估 →
   - 答得好的点 / 漏掉的点 / 误区；
   - **教更简单的英文说法**：给一句可直接背的简单英文示范；
   - 给这题打分（1–5）。
5. 全部问完后**写记录**：`interviews/YYYY-MM-DD-<主题>.md`（用今天的日期），含题目、用户作答要点、每题评分、薄弱点、**待改进的英文表达**。
6. **更新看板**：`syllabus.md` 对应主题的 掌握度（🔴/🟡/🟢）/ 薄弱点 / 上次复习。

## 模式二：快速复习（刷卡）

1. 按"上次复习时间 + 掌握度"挑卡（掌握度低 / 久未复习优先，类间隔重复）。
2. 快问快答：问一题 → 用户答 → 给核心答案对照 → 用户自评会 / 不会。
3. 更新看板掌握度与上次复习时间。比模拟面试轻量，不必写完整记录。

## 注意
- 模拟面试默认**英文提问**；讲评和纠正用**中文**，方便理解。
- 鼓励用户开口说英文；纠正时给**最简单、可直接背**的英文版本。
- 评分和薄弱点要具体，便于回头补强对应主题。
