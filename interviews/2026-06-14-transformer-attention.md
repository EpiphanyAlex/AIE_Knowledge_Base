# 模拟面试记录 — Transformer & Attention

- **日期**：2026-06-14
- **模式**：模拟面试（英文进行 + 中文讲评）
- **范围**：Transformer 架构总览（01）、Attention（02）
- **题数**：3
- **整体评分**：~2.7 / 5

---

## 逐题记录

### Q1. What is a Transformer, and why did it replace RNNs?（基础）
- **作答要点**：deep learning 架构；理解上下文和词之间的关系；RNN 是逐词处理（word one by one）。
- **评分**：3 / 5
- **好**：抓住"理解关系"的直觉；用 RNN 逐词处理来对比，正确。
- **漏**：没点核心词 **attention**；漏了"并行训练更快"和"任意 token 直接相连/长距离"两个卖点。

### Q2. What is self-attention, and why does a Transformer need it?（基础）
- **作答要点**：focus on the most relevant parts；有三要素 Q、K、V。
- **评分**：3 / 5
- **好**：相关性加权的直觉对；主动报出 Q/K/V。
- **漏**：没答"为什么需要"（理解上下文/指代）；没点出 "self" = 同一序列；Q/K/V 只报名没展开。

### Q3. Explain how Q, K, V work together to compute attention.（进阶 · 追问）
- **作答要点**：Q=在看什么；K=input data；V=information。
- **评分**：2 / 5
- **好**：Q 的含义大致对，知道三者各有角色。
- **漏**：**核心计算步骤没答**（点积→softmax→加权求和 V）；K 描述模糊。

---

## 薄弱点（重点补强，按优先级）
1. **attention 的计算 4 步**：Q·K 点积 → 分数 → softmax → 对 V 加权求和。（背 02 Q2 + 口述版）
2. 答题主动点核心词：**attention / parallel / long-range**。
3. self-attention 的 "self" = 看同一序列；以及"为什么需要"（理解上下文、指代）。

## 待改进的英文表达
- "make LLM understand" → **"lets the model understand"**。
- 形容 Transformer：**"based on attention, looks at the whole sentence at once, trains in parallel, handles long-range relations"**。
- 描述计算：**"dot product Query with every Key → softmax → weighted sum of Values"**。

## 下次建议
- 先把 `02-attention` 的计算步骤练到能脱口而出，再重测 Attention；Transformer 重点练"主动点核心词"。
