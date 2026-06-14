---
topic: 预训练与训练目标
domain: llm
difficulty: 基础
status: drafted
prerequisites: [tokenization-embeddings]
tags: [pretraining, next-token-prediction, causal-lm, masked-lm, self-supervised]
---

# 预训练与训练目标

## 一句话概览
> 预训练（pretraining）是让模型在海量未标注文本上做"自我监督"任务——主要是预测下一个 token——从而学到语言、知识和推理的通用能力；之后再用少量数据微调（fine-tuning）让它擅长具体任务。

## 概念讲解

**1. 预训练 vs 微调：两阶段的分工**
现代 LLM 一般分两步：
- **预训练（pretraining）**：在超大规模、**没有人工标注**的文本上训练，目标是学"通用能力"——语法、常识、世界知识、基本推理。这一步最贵（算力、数据、时间）。
- **微调（fine-tuning）**：在预训练好的模型上，用**少量、更有针对性**的数据继续训练，让它适配某个任务或风格（如对话、写代码、遵循指令）。
直觉类比：预训练像"读完整个图书馆打基础"，微调像"针对某场考试再做专项练习"。

**2. 自监督学习（self-supervised learning）：为什么不需要人工标注**
传统监督学习需要人工标注（给每张图标"猫/狗"），又慢又贵。
**self-supervised** 的巧妙之处：**标签直接来自数据本身**。
- 拿一句话 "我今天去了___"，把后面的词盖住，让模型来预测——**正确答案就是原文里那个词**，不需要人工标。
- 所以可以用互联网上几乎无限的纯文本来训练，规模能拉得极大。
这就是 LLM 能"读"海量数据的根本原因：监督信号是自动生成的。

**3. Next-token prediction（causal / autoregressive LM，GPT 类）**
这是 GPT 类模型的训练目标，也叫 **causal LM** 或 **autoregressive LM**：
- 给定前面所有 token，预测**下一个** token。
- "causal（因果）"指**只能看左边**（已经出现的 token），看不到右边（未来），这样训练时的预测目标才不会"作弊"看到答案。
- 训练时一句话可以**并行**算出每个位置的预测（用 causal mask 挡住未来），但生成时是**一个一个**往外吐 token（autoregressive，自回归）。

**4. Masked language modeling（BERT 类）对比**
BERT 类用的是 **masked language modeling (MLM)**：
- 随机**盖住（mask）句子里一部分 token**，让模型根据**左右两边的上下文**把它们填回来。
- 因为能同时看左右，BERT 学到的是**双向（bidirectional）**表示，特别适合**理解类**任务（分类、检索、抽取）。
- 但它不擅长**逐词生成**文本——它不是为"接着往下写"设计的。

简单对比：

| | next-token prediction (GPT 类) | masked LM (BERT 类) |
|---|---|---|
| 看上下文 | 只看左边（单向） | 看左右（双向） |
| 训练目标 | 预测下一个 token | 还原被盖住的 token |
| 强项 | 生成 / 续写 | 理解 / 编码 |

**5. 为什么 next-token prediction 能学到"通用能力"**
直觉：**"预测下一个词"这个任务本身极难，逼着模型理解一切**。
- 要准确预测下一个 token，模型必须隐式掌握语法、事实、逻辑、上下文，甚至简单推理。
- 例："2 + 3 = ___" 要答对就得会算；"法国的首都是___" 要答对就得记住事实。
- 所以一个看似简单的目标，在海量数据 + 大模型下，会"涌现"出广泛的能力。这就是为什么单一目标能撑起通用模型。

**6. Loss 用 cross-entropy 的直觉**
模型每步输出的是下一个 token 在整个词表上的**概率分布**。怎么衡量预测好不好？用 **cross-entropy loss**：
- 它衡量"模型给**正确那个 token** 的概率有多高"。
- 模型给正确 token 的概率越高，loss 越低；给得越低，惩罚越大（loss 越高）。
- 训练就是不断调权重，让正确 token 的预测概率变高 → cross-entropy 下降。
（cross-entropy 和语言模型常说的 perplexity 直接相关：perplexity ≈ exp(cross-entropy)，越小越好。）

**7. 预训练数据规模与 scaling 直觉**
经验规律（scaling laws）：**模型变大 + 数据变多 + 算力变多，loss 会以可预测的方式持续下降**，能力随之提升。
- 直觉：更多数据 → 见过更多模式；更大模型 → 能记/能学更多。
- ⚠️待核实：具体的"最优模型大小 vs 数据量"配比（如 Chinchilla 提出的 token 数与参数量大致成比例的结论）属于会随研究更新的数字结论，引用前需核对原始论文。
- ⚠️待核实：各家前沿模型的**具体参数量、训练 token 数、数据集大小**多未完全公开或随版本变化，截至 2026-06 不要凭记忆给出确切数字。

## 面试问答卡

### Q1. What is the difference between pretraining and fine-tuning? / 预训练和微调有什么区别？
**难度:** 基础
**Answer (EN):**
- Pretraining trains the model on huge unlabeled text to learn general skills like grammar, facts, and basic reasoning.
- Fine-tuning takes that pretrained model and trains it more on a small, focused dataset for a specific task or style.
- Pretraining is expensive and done once; fine-tuning is cheaper and done many times for different needs.
**核心答案 (中):**
- 预训练在海量**无标注**文本上学通用能力（语法、知识、基本推理）。
- 微调在预训练模型上，用**少量针对性**数据继续训练，适配具体任务或风格。
- 预训练贵、一般只做一次；微调便宜，可针对不同需求做很多次。
**追问 / 深入 (中):**
- 追问"为什么不直接为每个任务从头训练？" → 从头训太贵，且单任务数据太少学不到通用能力；预训练一次、到处微调，复用了通用基础，成本和效果都更好。
**常见误区 (中):**
- 以为微调会"重新学语言"；其实它只在已有通用能力上做小幅适配。
- 把 fine-tuning 和 prompt/in-context learning 混为一谈：微调改权重，prompt 不改权重。

### Q2. What is self-supervised learning and why does it not need human labels? / 什么是自监督学习？为什么它不需要人工标注？
**难度:** 基础
**Answer (EN):**
- In self-supervised learning, the label comes from the data itself, not from a human.
- For text, we hide part of a sentence and ask the model to predict it; the original word is the correct answer.
- This means we can train on almost unlimited raw text from the internet, with no manual labeling.
**核心答案 (中):**
- self-supervised 里，**标签来自数据本身**，不是人工标的。
- 对文本：盖住句子的一部分让模型预测，**原文里的词就是正确答案**。
- 所以能用互联网上近乎无限的纯文本训练，无需人工标注，规模可以拉很大。
**追问 / 深入 (中):**
- 追问"那和无监督学习是一回事吗？" → 通常把它看成无监督的一种，但它**有明确的预测目标和监督信号**（自动生成的标签），所以更精确的叫法是 self-supervised。
**常见误区 (中):**
- 以为自监督"没有标签所以没有学习目标"；其实有明确目标，只是标签是自动构造的。

### Q3. What is next-token prediction (causal / autoregressive LM)? / 什么是 next-token prediction（causal / autoregressive LM）？
**难度:** 基础
**Answer (EN):**
- The model is given all previous tokens and must predict the next token.
- "Causal" means it can only look left (past tokens), not right (future), so it cannot cheat by seeing the answer.
- This is the training objective for GPT-style models; at generation time it produces tokens one at a time (autoregressive).
**核心答案 (中):**
- 给定前面所有 token，预测**下一个** token。
- "causal" 指只能看左边（过去），看不到右边（未来），训练时不会偷看答案。
- 这是 GPT 类模型的训练目标；生成时一个一个往外吐 token（autoregressive）。
**追问 / 深入 (中):**
- 追问"训练时也是一个一个预测吗？" → 不是。训练时用 causal mask 挡住未来，可以**并行**算出一句话里每个位置的预测；只有生成时才是逐 token 的自回归。
**常见误区 (中):**
- 把"训练并行"和"生成逐 token"搞混；两者都对，但是不同阶段。

### Q4. How does masked language modeling (BERT) differ from next-token prediction (GPT)? / masked language modeling（BERT）和 next-token prediction（GPT）有什么区别？
**难度:** 进阶
**Answer (EN):**
- Masked LM hides some tokens in a sentence and predicts them using both left and right context (bidirectional).
- Next-token prediction only looks left and predicts the next token (unidirectional).
- BERT-style models are great for understanding tasks (classification, retrieval); GPT-style models are great for generation.
**核心答案 (中):**
- masked LM 盖住句子里部分 token，用**左右两边**上下文预测它们（双向）。
- next-token prediction 只看左边，预测下一个 token（单向）。
- BERT 类擅长**理解**类任务（分类、检索）；GPT 类擅长**生成**。
**追问 / 深入 (中):**
- 追问"为什么生成式大模型大多用 next-token 而不是 MLM？" → next-token 天然就是"接着往下写"，和生成任务完全对齐；MLM 是填空，不直接对应逐词生成，做长文本生成不自然。
**常见误区 (中):**
- 以为 BERT 也能像 GPT 那样自由续写长文本；MLM 的目标不是逐词生成，不适合这个用法。
- 以为"双向一定更强"；双向利于理解，但和自回归生成目标不匹配。

### Q5. Why can such a simple objective (predict the next token) lead to general abilities? / 为什么"预测下一个 token"这么简单的目标能学出通用能力？
**难度:** 进阶
**Answer (EN):**
- To predict the next token well, the model must implicitly learn grammar, facts, logic, and even simple reasoning.
- Example: to finish "2 + 3 =" it must do math; to finish "The capital of France is" it must know facts.
- With huge data and a large model, broad abilities emerge from this single hard objective.
**核心答案 (中):**
- 要把下一个 token 预测准，模型必须隐式学会语法、事实、逻辑、甚至简单推理。
- 例："2 + 3 =" 要接对得会算；"法国的首都是" 要接对得记住事实。
- 在海量数据 + 大模型下，单一困难目标会"涌现"出广泛能力。
**追问 / 深入 (中):**
- 追问"那为什么 loss 用 cross-entropy？" → cross-entropy 衡量模型给**正确 token** 的概率有多高，概率越高 loss 越低；训练就是让正确 token 的预测概率变高，和"预测准下一个词"完全一致。
**常见误区 (中):**
- 以为模型是"背"下来的；它学的是可泛化的模式与规律，所以能处理没见过的句子（虽然也会有记忆成分）。

### Q6. What do scaling laws say about pretraining data and model size? / scaling laws 对预训练数据和模型大小说了什么？
**难度:** 进阶
**Answer (EN):**
- Scaling laws say that as model size, data, and compute grow, the loss goes down in a predictable way.
- More data means more patterns seen; a bigger model can learn and store more.
- The exact "best size vs. data" ratio and the exact numbers for frontier models change over time, so quote them carefully. (⚠️to verify)
**核心答案 (中):**
- scaling laws：模型、数据、算力一起变大，loss 会**可预测地**下降，能力随之提升。
- 更多数据 → 见过更多模式；更大模型 → 能学/能记更多。
- "最优大小 vs 数据量"的具体配比、前沿模型的确切数字会随研究/版本变化，引用要谨慎（⚠️待核实）。
**追问 / 深入 (中):**
- 追问"是不是模型越大越好？" → 不一定。给定算力预算，盲目堆大而数据不够，效果不如把参数量和数据量**配比**调好（Chinchilla 类结论，⚠️待核实具体配比）。
**常见误区 (中):**
- 以为只要参数量大就一定强；数据量和数据质量同样关键，且要和模型大小匹配。
- 凭记忆报某模型的确切参数量 / 训练 token 数；这些数字多未公开或随版本变化（⚠️待核实）。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "Pretraining learns general skills from huge unlabeled text; fine-tuning adapts that model to a specific task with a small dataset."
  (中) 预训练在海量无标注文本上学通用能力；微调用小数据让模型适配具体任务。
- (EN) "It's self-supervised: the label comes from the data itself, so we don't need humans to label anything."
  (中) 这是自监督：标签来自数据本身，所以不需要人工标注。
- (EN) "GPT-style models use next-token prediction — given past tokens, predict the next one, looking only left."
  (中) GPT 类用 next-token prediction：给定前面的 token，只看左边，预测下一个。
- (EN) "BERT-style models use masked language modeling — they fill in hidden tokens using both sides, which is great for understanding."
  (中) BERT 类用 masked language modeling：用左右上下文填空，擅长理解类任务。
- (EN) "Predicting the next token sounds simple, but doing it well forces the model to learn grammar, facts, and reasoning."
  (中) 预测下一个词听起来简单，但要做好就逼着模型学会语法、事实和推理。
- (EN) "We train it with cross-entropy loss, which pushes the probability of the correct next token higher."
  (中) 用 cross-entropy loss 训练，让正确下一个 token 的概率变高。

## 延伸阅读
- *Improving Language Understanding by Generative Pre-Training*（GPT-1，Radford et al., 2018）—— 生成式预训练 + next-token prediction 的代表。
- *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding*（Devlin et al., 2018）—— masked language modeling 原论文。
- *Scaling Laws for Neural Language Models*（Kaplan et al., 2020）—— scaling 直觉的来源（具体数字 ⚠️待核实）。
- *Training Compute-Optimal Large Language Models*（Chinchilla，Hoffmann et al., 2022）—— 参数量与数据量配比（具体结论 ⚠️待核实）。
