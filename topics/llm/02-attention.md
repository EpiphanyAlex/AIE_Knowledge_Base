---
topic: Attention 机制
domain: llm
difficulty: 基础
status: drafted
prerequisites: []
tags: [transformer, attention, self-attention, multi-head, QKV]
---

# Attention 机制

## 一句话概览
> Attention 让模型在处理每个 token 时，按"相关性"加权地去看序列里其他所有 token——这是 Transformer 能理解上下文的核心机制。

## 概念讲解

**1. 直觉**
读 "The animal didn't cross the street because **it** was too tired" 这句话时，要理解 "it" 指什么，你得回头看 "animal"。Attention 做的就是这件事：处理某个 token 时，让它**按相关程度去关注其他 token**，相关的多看一点，无关的少看一点。

**2. 原理：Query / Key / Value（Q、K、V）**
每个 token 先变成三个向量：
- **Query（查询）**：我想找什么。
- **Key（键）**：我能被什么样的查询匹配到。
- **Value（值）**：如果我被选中，我贡献什么信息。

计算分三步：
1. 用当前 token 的 Q 和所有 token 的 K 做点积 → 得到"相关性分数"。
2. 分数过 softmax → 变成一组加起来为 1 的**权重**。
3. 用这组权重对所有 token 的 V 加权求和 → 得到该 token 的新表示。

**3. 公式**

```
Attention(Q, K, V) = softmax( Q·Kᵀ / √d_k ) · V
```

除以 `√d_k`（d_k 是 key 向量维度）是为了**缩放**：维度大时点积会很大，softmax 会变得极端、梯度很小，缩放能让训练更稳。

**4. self-attention vs cross-attention**
- **self-attention**：Q、K、V 都来自**同一个序列**（句子自己看自己）。
- **cross-attention**：Q 来自一个序列，K、V 来自**另一个**序列（如翻译里 decoder 看 encoder 的输出）。

**5. multi-head（多头）**
不只算一组 Q/K/V，而是**并行算多组**（多个 head），每个 head 关注不同的关系（有的看语法、有的看指代），最后把各 head 的结果拼接再投影。好处是同时从多个角度看序列。

**6. 复杂度**
self-attention 要让每个 token 看其他所有 token，计算量是 **O(n²)**（n = 序列长度）。这是**长上下文的主要瓶颈**，也是很多优化（如 KV cache、FlashAttention、稀疏 attention）要解决的问题。

## 面试问答卡

### Q1. What is self-attention and why does a Transformer need it? / 什么是 self-attention？为什么 Transformer 需要它？
**难度:** 基础
**Answer (EN):**
- Self-attention lets each token look at all other tokens in the same sequence and decide which ones matter.
- A Transformer needs it to understand context — for example, what a word like "it" refers to.
- Unlike RNNs, it looks at all tokens at once, so it captures long-range relations and runs in parallel.
**核心答案 (中):**
- self-attention 让每个 token 看同一序列里其他所有 token，并决定哪些重要。
- Transformer 靠它理解上下文（比如 "it" 指代谁）。
- 和 RNN 不同，它**一次看全部 token**，能抓长距离关系，且可并行。
**追问 / 深入 (中):**
- 追问"和 RNN 比好在哪？" → RNN 顺序处理、信息要一步步传，远距离容易丢；self-attention 任意两个 token 直接相连，且并行计算更快。
**常见误区 (中):**
- 以为 attention 是一个独立模型；它只是 Transformer 里的一层运算。
- 把 self-attention 和 multi-head 混为一谈：multi-head 是"并行做多组 self-attention"。

### Q2. How does attention work? Explain Q, K, V. / attention 怎么算的？解释 Q、K、V。
**难度:** 基础
**Answer (EN):**
- Each token is turned into three vectors: Query, Key, Value.
- We do a dot product between one token's Query and every token's Key to get scores.
- We pass the scores through softmax to get weights, then take a weighted sum of the Values.
**核心答案 (中):**
- 每个 token 变成三个向量：Query、Key、Value。
- 用一个 token 的 Query 和所有 token 的 Key 点积，得到分数。
- 分数过 softmax 变权重，再对所有 Value 加权求和。
**追问 / 深入 (中):**
- 追问"Q、K、V 哪来的？" → 由输入向量分别乘三个可学习的权重矩阵 W_Q、W_K、W_V 得到。
**常见误区 (中):**
- 以为 Q、K、V 是固定的；它们是学出来的线性变换结果。

### Q3. Why do we divide by √d_k in attention? / attention 里为什么要除以 √d_k？
**难度:** 进阶
**Answer (EN):**
- When d_k is large, the dot products get large too.
- Large values make softmax very sharp, so gradients become very small and training gets unstable.
- Dividing by √d_k keeps the scores in a good range. This is called scaled dot-product attention.
**核心答案 (中):**
- d_k 大时，点积结果也会变大。
- 数值太大会让 softmax 过于尖锐，梯度极小、训练不稳。
- 除以 √d_k 把分数拉回合适范围，这就叫 scaled dot-product attention。
**追问 / 深入 (中):**
- 追问"为什么偏偏是 √d_k？" → 若 Q、K 各维独立、方差为 1，点积方差约为 d_k，除以 √d_k 把方差拉回约 1。
**常见误区 (中):**
- 以为这个缩放是为了归一化概率；归一化是 softmax 干的，缩放是为了数值/梯度稳定。

### Q4. What is multi-head attention and why use multiple heads? / 什么是 multi-head attention？为什么用多个头？
**难度:** 进阶
**Answer (EN):**
- Multi-head attention runs several attention operations in parallel, each with its own Q, K, V.
- Each head can focus on a different kind of relation (e.g. syntax vs. reference).
- We concatenate the heads and project them back, so the model sees the sequence from many angles at once.
**核心答案 (中):**
- multi-head 并行跑多组 attention，每组有自己的 Q、K、V。
- 每个 head 可以关注不同的关系（如语法 / 指代）。
- 把各 head 拼接再投影，让模型同时从多个角度看序列。
**追问 / 深入 (中):**
- 追问"head 多了维度不会爆吗？" → 通常把总维度切分给各 head（如 512 维分 8 头、每头 64 维），总计算量基本不变。
**常见误区 (中):**
- 以为头越多一定越好；头太多每头维度太小，反而学不到东西，是个权衡。

### Q5. What is the computational cost of self-attention, and why does it matter for long context? / self-attention 的计算复杂度是多少？为什么对长上下文是个问题？
**难度:** 进阶
**Answer (EN):**
- Self-attention is O(n²) in sequence length, because every token attends to every other token.
- For long inputs, both compute and memory grow fast, which makes long context expensive.
- This is why techniques like KV cache, FlashAttention, and sparse attention exist.
**核心答案 (中):**
- self-attention 对序列长度是 **O(n²)**，因为每个 token 都要看其他所有 token。
- 输入越长，计算和显存涨得越快，所以长上下文很贵。
- 这正是 KV cache、FlashAttention、稀疏 attention 等技术存在的原因。
**追问 / 深入 (中):**
- 追问"KV cache 解决的是哪部分？" → 生成时缓存已算过的 K、V，避免每生成一个新 token 都重算前面所有 token，省的是**推理**时的重复计算。
**常见误区 (中):**
- 把 O(n²) 说成是参数量；它说的是**计算/显存随序列长度**的增长，不是模型大小。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "Self-attention lets every token look at every other token and decide which ones matter."
  (中) self-attention 让每个 token 看其他所有 token，并决定哪些重要。
- (EN) "Each token becomes a Query, a Key, and a Value. We match Queries against Keys to get weights, then take a weighted sum of the Values."
  (中) 每个 token 变成 Query、Key、Value。用 Query 匹配 Key 得到权重，再对 Value 加权求和。
- (EN) "Multi-head means we do this several times in parallel, so the model sees the sentence from different angles."
  (中) multi-head 就是并行做好几次，让模型从不同角度看句子。
- (EN) "The cost is quadratic in length, so long context is expensive — that's why we use tricks like KV cache."
  (中) 计算量随长度平方增长，所以长上下文很贵——这就是要用 KV cache 这类技巧的原因。

## 延伸阅读
- *Attention Is All You Need*（Vaswani et al., 2017）—— Transformer 与 scaled dot-product attention 原论文。
- *The Illustrated Transformer*（Jay Alammar 博客）—— 图解 Q/K/V 与 multi-head，适合初学。
