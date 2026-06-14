---
topic: Transformer 架构总览
domain: llm
difficulty: 基础
status: drafted
prerequisites: []
tags: [transformer, architecture, encoder, decoder, positional-encoding, FFN, residual]
---

# Transformer 架构总览

## 一句话概览
> Transformer 是当今几乎所有大语言模型的底层架构：它用 attention 取代了 RNN 的顺序处理，让模型能并行训练、并能直接建立任意两个 token 之间的关系。

## 概念讲解

**1. 它解决了什么问题**
在 Transformer 之前，处理序列主要用 RNN / LSTM：token 一个接一个地处理，信息要一步步往后传。这有两个毛病：① 不能并行，训练慢；② 距离远的 token 之间信息容易丢。Transformer（2017，*Attention Is All You Need*）用 **attention** 让任意两个 token 直接相连，并且**一次看整个序列**，既能并行又能抓长距离关系。

**2. 整体数据流**
一句话从输入到输出大致是：

```
tokens → token embedding + positional encoding → N 个相同的层(Layer) → 输出表示 → (预测下一个 token)
```

**3. 一个 Transformer 层(block)里有什么**
每一层主要由两个子层(sub-layer)组成，按顺序：
- **多头自注意力 multi-head self-attention**：让每个 token 关注序列里其他 token（细节见 `02-attention`）。
- **前馈网络 feed-forward network (FFN)**：对每个 token 各自做一次小型 MLP 变换，增加非线性表达能力。

这两个子层外面都包了：
- **残差连接 residual connection**：把子层的输入直接加到输出上（`x + Sublayer(x)`），帮助梯度流动、训练更深的网络。
- **层归一化 layer normalization**：稳定每层的数值分布，让训练更稳。

把这样的层**堆叠 N 次**（如 12、24、96 层），就得到完整模型。

**4. 为什么需要 positional encoding（位置编码）**
attention 本身**不区分顺序**——打乱 token 顺序，算出来一样。但语言里顺序很重要（"猫追狗" ≠ "狗追猫"）。所以要给每个 token 的 embedding **加上位置信息**，模型才知道谁先谁后。早期用固定的正弦位置编码，现代模型常用可学习的或旋转位置编码（如 RoPE）。

**5. 三种架构变体**
- **Encoder-only（编码器）**：双向看整句，擅长**理解类**任务（分类、检索）。代表：BERT。
- **Decoder-only（解码器）**：从左到右、只看前文，擅长**生成**。代表：GPT 系列——**现在大多数 LLM 都是 decoder-only**。
- **Encoder-Decoder（编码器-解码器）**：一边读输入、一边生成输出，擅长翻译、摘要这类"输入→输出"任务。代表：T5、原始 Transformer。

## 面试问答卡

### Q1. What is a Transformer and why did it replace RNNs? / 什么是 Transformer？它为什么取代了 RNN？
**难度:** 基础
**Answer (EN):**
- A Transformer is a neural network architecture built around attention instead of recurrence.
- It looks at the whole sequence at once, so it trains in parallel and is much faster than RNNs.
- It also connects any two tokens directly, so it handles long-range relations better.
**核心答案 (中):**
- Transformer 是一种以 **attention** 为核心、不用循环(recurrence)的网络架构。
- 它**一次看整个序列**，可以并行训练，比 RNN 快很多。
- 任意两个 token 直接相连，长距离关系处理得更好。
**追问 / 深入 (中):**
- 追问"那 Transformer 有什么代价？" → 计算量随序列长度是 O(n²)，长上下文很贵（见 `02-attention` Q5）。
**常见误区 (中):**
- 以为 Transformer 是某个具体模型；它是一类**架构**，GPT、BERT 都基于它。

### Q2. What are the main parts of a Transformer block? / 一个 Transformer 层里主要有哪些部分？
**难度:** 基础
**Answer (EN):**
- Two main sub-layers: multi-head self-attention, then a feed-forward network (FFN).
- Each sub-layer is wrapped with a residual connection and layer normalization.
- We stack many of these identical blocks to build the full model.
**核心答案 (中):**
- 两个主要子层：多头自注意力，然后是前馈网络(FFN)。
- 每个子层外面都有**残差连接**和**层归一化**。
- 把许多个这样相同的层**堆叠**起来，构成完整模型。
**追问 / 深入 (中):**
- 追问"FFN 是干嘛的？" → 对每个 token 各自做一次小 MLP，加入非线性、扩大表达能力；attention 负责"token 之间交换信息"，FFN 负责"每个 token 自己加工信息"。
**常见误区 (中):**
- 以为一层里只有 attention；FFN 同样关键，参数量往往比 attention 还大。

### Q3. Why does a Transformer need positional encoding? / 为什么 Transformer 需要位置编码？
**难度:** 基础
**Answer (EN):**
- Attention does not care about order — if you shuffle the tokens, the result is the same.
- But word order carries meaning, so we add position information to each token embedding.
- This lets the model know which token comes first and which comes later.
**核心答案 (中):**
- attention **不在意顺序**——打乱 token，结果一样。
- 但词序有意义，所以要给每个 token 的 embedding **加上位置信息**。
- 这样模型才知道 token 的先后。
**追问 / 深入 (中):**
- 追问"有哪些位置编码方式？" → 固定的正弦编码、可学习的位置 embedding，以及现代常用的旋转位置编码 RoPE（对长度外推更友好）。
**常见误区 (中):**
- 以为位置编码是单独一层；它通常是**加到** token embedding 上的一组向量，不是独立网络。

### Q4. What's the difference between encoder-only, decoder-only, and encoder-decoder Transformers? / encoder-only、decoder-only、encoder-decoder 有什么区别？
**难度:** 进阶
**Answer (EN):**
- Encoder-only reads the whole input both ways; good for understanding tasks. Example: BERT.
- Decoder-only reads left to right and only sees past tokens; good for generation. Example: GPT — most LLMs today are decoder-only.
- Encoder-decoder reads an input and then generates an output; good for translation or summarization. Example: T5.
**核心答案 (中):**
- **Encoder-only**：双向读整段输入，擅长理解类任务。代表 BERT。
- **Decoder-only**：从左到右、只看前文，擅长生成。代表 GPT——**现在大多数 LLM 都是这种**。
- **Encoder-decoder**：先读输入再生成输出，擅长翻译、摘要。代表 T5。
**追问 / 深入 (中):**
- 追问"为什么生成模型用 decoder-only？" → 它用因果掩码(causal mask)保证每个 token 只能看前面的，天然适合"预测下一个 token"的自回归生成。
**常见误区 (中):**
- 以为 GPT 里有 encoder；GPT 是纯 decoder-only。

### Q5. What do residual connections and layer normalization do? / 残差连接和层归一化有什么作用？
**难度:** 进阶
**Answer (EN):**
- A residual connection adds the input of a sub-layer back to its output, so gradients flow well and we can train very deep networks.
- Layer normalization keeps the values in each layer in a stable range, which makes training smoother and faster.
**核心答案 (中):**
- **残差连接**把子层的输入加回到输出上，让梯度顺畅流动，从而能训练很深的网络。
- **层归一化**把每层的数值保持在稳定范围，让训练更平滑、更快。
**追问 / 深入 (中):**
- 追问"LayerNorm 放前面还是后面？" → 有 post-norm（原版，放子层后）和 pre-norm（放子层前）两种；现代大模型多用 **pre-norm**，训练更稳定。
**常见误区 (中):**
- 把 layer normalization 和 batch normalization 搞混；LayerNorm 对**单个样本的特征维**归一化，不依赖 batch 大小，更适合变长序列。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "A Transformer is built on attention instead of recurrence, so it reads the whole sequence at once and trains in parallel."
  (中) Transformer 以 attention 为核心、不用循环，所以能一次读整个序列、并行训练。
- (EN) "Each block has two parts: multi-head self-attention and a feed-forward network, both wrapped with residual connections and layer norm. We stack many blocks."
  (中) 每个 block 有两部分：多头自注意力和前馈网络，外面都包着残差连接和层归一化。我们堆很多层。
- (EN) "Because attention ignores order, we add positional encoding so the model knows the token order."
  (中) 因为 attention 不管顺序，我们加位置编码，让模型知道 token 的先后。
- (EN) "There are three types: encoder-only like BERT, decoder-only like GPT, and encoder-decoder like T5. Most LLMs today are decoder-only."
  (中) 有三种：BERT 那样的 encoder-only、GPT 那样的 decoder-only、T5 那样的 encoder-decoder。现在多数 LLM 是 decoder-only。

## 延伸阅读
- *Attention Is All You Need*（Vaswani et al., 2017）—— Transformer 原论文。
- *The Illustrated Transformer*（Jay Alammar 博客）—— 图解整体架构，适合初学。
- 进阶：pre-norm vs post-norm、RoPE 位置编码（可在掌握基础后再深入）。
