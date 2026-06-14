---
topic: 幻觉与对齐
domain: llm
difficulty: 进阶
status: drafted
prerequisites: []
tags: [hallucination, alignment, RLHF, grounding, safety]
---

# 幻觉与对齐

## 一句话概览
> Hallucination 指模型很自信地编出不真实的内容；alignment 指让模型的行为符合人类的意图和价值——两者是 LLM 能否被放心用在真实场景里的核心问题。

## 概念讲解

**1. 什么是 hallucination（幻觉）**
模型输出看起来通顺、语气很自信，但内容是**错的或编造的**：编造不存在的论文、假的 API、错误的日期、虚构的人物引用。关键不是"答错"，而是它**毫不犹豫地把假的当真的说出来**，普通用户很难一眼看穿。

**2. 为什么会发生**
- **训练目标是"预测下一个 token"，不是"说真话"**：模型学的是"什么样的句子更像训练数据里出现过的"，流畅 ≠ 正确。一个语法完美、风格地道的假答案，在它眼里是高概率的。
- **知识有边界**：训练数据里没有、或太稀少的事实，它没真正"记住"，被问到时就会**用相似模式去补全**——补出来的往往是合理但虚假的内容。
- **过度泛化 / 模式套用**：它见过"某某大学的某某教授发表了某论文"这种句式，于是套用这个模式，填进一个**听起来对、实际不存在**的名字和标题。
- **没有内建的"我不知道"机制**：默认它总会给一个答案，而不是承认信息不足。

**3. 怎么缓解 hallucination**
没有银弹，常见组合拳：
- **RAG / grounding（给上下文）**：先检索真实资料，把资料塞进 prompt，让模型**基于给定材料**回答，而不是凭记忆瞎编。这是工程上最主流的手段。
- **引用来源（citation）**：要求模型答案附出处，方便人工核对，也逼它"有据可依"。
- **教会模型说"不知道"**：通过 prompt 或训练，让模型在证据不足时**承认不确定**，而不是硬答。
- **解码 / 温度（decoding / temperature）**：降低 temperature 让输出更保守，减少天马行空（但不能根治）。
- **评测（eval）**：用专门的事实性 benchmark / 人工核查去**度量**幻觉率，才能持续改进。

**4. 什么是 alignment（对齐）**
让模型的行为**符合人类的意图与价值观**：你想要的它去做，不该做的它别做。一个"能力很强但没对齐"的模型可能很会写代码，却也乐于帮人造谣、写恶意软件、或者答非所问。Alignment 关心的不是"会不会"，而是"该不该、按不按你的意思来"。

**5. alignment 的常见方法**
- **RLHF（Reinforcement Learning from Human Feedback，从人类反馈中强化学习）**：典型三步——
  1. 先用人工示范数据做**监督微调（SFT）**，让模型学会按指令回答；
  2. 让人对模型的多个回答**排序**，训练一个**奖励模型（reward model）**来打分；
  3. 用强化学习（如 PPO）优化模型，让它**生成奖励模型打分更高的回答**。
- **Constitutional AI（宪法式 AI）思路** ⚠️待核实（Anthropic 提出）：用一套写明的**原则（"宪法"）**让模型**自己批评并修改**自己的回答，从而**减少对人工标注有害样本的依赖**，用 AI 反馈部分替代人类反馈。

**6. HHH 框架：Helpful / Harmless / Honest**
一个常被引用的对齐目标三件套：
- **Helpful（有用）**：真的帮上忙、答到点子上。
- **Harmless（无害）**：不输出有害、危险、歧视性的内容。
- **Honest（诚实）**：说真话、不编造，不确定就说不确定。
三者会**互相冲突**：有时"最有用"的答案可能不安全，"最安全"的做法是拒绝回答但就没那么有用——对齐很大一部分是在这几者之间做权衡。

**7. alignment 与 hallucination 的关系**
- Hallucination 可以看成是 **Honest 这一维没做好**：模型编内容，就是不诚实。
- 所以"减少幻觉"在很大程度上属于 alignment 的目标之一——通过 RLHF 等手段，可以**奖励"承认不知道"、惩罚"自信地编造"**，让模型更诚实。
- 但两者**不完全等价**：alignment 还覆盖无害、遵从意图等更广的范围；而幻觉也有纯能力/知识层面的成因（知识缺失），不是光靠对齐就能根治，往往要配合 RAG 等工程手段。

## 面试问答卡

### Q1. What is hallucination in LLMs? / 什么是 LLM 的 hallucination（幻觉）？
**难度:** 基础
**Answer (EN):**
- Hallucination is when the model confidently makes up content that is not true.
- The output sounds fluent and sure, but the facts are wrong or invented (fake papers, fake APIs, wrong dates).
- The danger is that it looks correct, so users may not notice.
**核心答案 (中):**
- hallucination 就是模型**很自信地编造不真实的内容**。
- 输出很流畅、语气笃定，但事实是错的或虚构的（假论文、假 API、错日期）。
- 危险在于它**看起来像对的**，用户不容易察觉。
**追问 / 深入 (中):**
- 追问"答错和幻觉有区别吗？" → 有：幻觉强调"**自信地编造、看起来可信**"；不是简单的算错或笔误。
**常见误区 (中):**
- 以为幻觉只在小模型里出现；其实再强的大模型也会幻觉，只是频率不同。
- 以为输出流畅就代表正确；流畅和真实是两回事。

### Q2. Why do LLMs hallucinate? / LLM 为什么会产生幻觉？
**难度:** 进阶
**Answer (EN):**
- The training goal is to predict the next token, not to tell the truth. Fluent text can still be false.
- The model has limited knowledge; for facts it never really learned, it fills the gap with a plausible-looking guess.
- It over-generalizes patterns, so it produces something that fits the style but does not exist.
- By default it has no built-in way to say "I don't know."
**核心答案 (中):**
- 训练目标是**预测下一个 token，不是求真**，流畅的句子也可能是假的。
- 知识有边界：没真正学过的事实，它会**用看似合理的猜测去补全**。
- 它会**过度泛化模式**，造出符合风格但不存在的内容。
- 默认没有"我不知道"的机制，倾向于总给个答案。
**追问 / 深入 (中):**
- 追问"那加大模型能解决吗？" → 能降低，但不能根治；知识缺失和"预测 token"的本质还在，工程上常配 RAG。
**常见误区 (中):**
- 以为幻觉是 bug、能靠改代码修掉；它更像是当前训练范式的**固有副作用**。

### Q3. How do you reduce hallucination in a real system? / 在真实系统里怎么减少幻觉？
**难度:** 进阶
**Answer (EN):**
- Use RAG / grounding: retrieve real documents and let the model answer based on them, not from memory.
- Ask the model to cite sources, so answers can be checked.
- Train or prompt the model to say "I don't know" when evidence is weak.
- Lower temperature for more conservative output, and use eval to measure the hallucination rate.
**核心答案 (中):**
- 用 **RAG / grounding**：检索真实材料，让模型**基于给定材料**回答，而不是凭记忆。
- 让模型**引用来源**，方便核对。
- 训练或用 prompt 让模型在证据不足时**说"不知道"**。
- 降低 temperature 让输出更保守；用 **eval** 度量幻觉率以持续改进。
**追问 / 深入 (中):**
- 追问"RAG 能彻底消除幻觉吗？" → 不能：检索到错的/无关的材料，或模型不遵守材料，照样会幻觉；RAG 是大幅缓解，不是消除。
**常见误区 (中):**
- 以为接了 RAG 就万事大吉；检索质量差、模型不"听话"时仍会编。

### Q4. What is alignment, and why does it matter? / 什么是 alignment（对齐）？为什么重要？
**难度:** 进阶
**Answer (EN):**
- Alignment means making the model's behavior match human intent and values.
- A strong but unaligned model could be very capable yet also do harmful things or ignore what you asked.
- It matters because raw capability is not enough — we need the model to do what we want and avoid what we don't.
**核心答案 (中):**
- alignment 就是让模型行为**符合人类的意图和价值观**。
- 一个**强但没对齐**的模型可能很能干，却也会做有害的事、或答非所问。
- 重要性在于：光有能力不够，还要模型**按你的意思来、并避开不该做的**。
**追问 / 深入 (中):**
- 追问"对齐和能力是一回事吗？" → 不是：能力是"会不会"，对齐是"该不该、按不按你意思来"，两者可以分开。
**常见误区 (中):**
- 把对齐窄化成"不说脏话/不输出有害内容"；它也包括遵从意图、诚实等更广的目标。

### Q5. What is RLHF? Explain the steps. / 什么是 RLHF？讲讲它的步骤。
**难度:** 高阶
**Answer (EN):**
- RLHF means Reinforcement Learning from Human Feedback. It is a common way to align models.
- Step 1: supervised fine-tuning (SFT) on human demonstrations, so the model learns to follow instructions.
- Step 2: humans rank several model answers; we train a reward model to predict these preferences.
- Step 3: use reinforcement learning (e.g. PPO) to push the model toward answers the reward model scores higher.
**核心答案 (中):**
- RLHF = 从人类反馈中强化学习，是常见的对齐方法。
- 第一步：用人工示范做**监督微调（SFT）**，让模型学会按指令回答。
- 第二步：人对多个回答**排序**，训练一个**奖励模型（reward model）**预测人类偏好。
- 第三步：用强化学习（如 PPO）让模型**朝奖励模型打分更高的回答**优化。
**追问 / 深入 (中):**
- 追问"RLHF 有什么缺点？" → 依赖大量人工标注、成本高；奖励模型可能被"钻空子"（reward hacking）；人类偏好本身有噪声和偏差。
**常见误区 (中):**
- 以为 RLHF 给模型注入了新知识；它主要调的是**行为/风格/偏好**，不是教新事实。
- 把奖励模型当成最终模型；它只是个**打分器**，用来训练真正的策略模型。

### Q6. What is Constitutional AI, and what is the HHH framework? / 什么是 Constitutional AI？什么是 HHH 框架？
**难度:** 高阶
**Answer (EN):**
- Constitutional AI uses a set of written principles (a "constitution") to let the model critique and revise its own answers. ⚠️待核实
- This reduces the need for humans to label harmful examples, using AI feedback in place of some human feedback.
- HHH stands for Helpful, Harmless, Honest — a common set of alignment goals.
- These three can conflict: the most helpful answer may not be the safest, so alignment is partly about the trade-off.
**核心答案 (中):**
- Constitutional AI 用一套写明的**原则（"宪法"）**，让模型**自己批评并修改**自己的回答。⚠️待核实
- 好处是**减少对人工标注有害样本的依赖**，用 AI 反馈部分替代人类反馈。
- HHH = **Helpful（有用）/ Harmless（无害）/ Honest（诚实）**，是常被引用的一组对齐目标。
- 三者会**冲突**：最有用的答案未必最安全，所以对齐很大程度是在做权衡。
**追问 / 深入 (中):**
- 追问"hallucination 属于 HHH 哪一项？" → 主要属于 **Honest**：编内容就是不诚实，所以减少幻觉是对齐目标之一。
**常见误区 (中):**
- 以为 HHH 三者总能同时满足；实际常要在有用 vs 无害、有用 vs 诚实之间取舍。
- 把 Constitutional AI 当成"完全不用人类"；它仍需要人来写原则、并配合其他训练。⚠️待核实

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "Hallucination is when the model confidently makes up something that is not true but sounds right."
  (中) hallucination 就是模型很自信地编出听起来像真、其实是假的内容。
- (EN) "It happens because the training goal is to predict the next token, not to tell the truth — fluent is not the same as correct."
  (中) 它发生是因为训练目标是预测下一个 token，不是求真——流畅不等于正确。
- (EN) "The main fix is RAG: give the model real documents to ground its answer, ask it to cite sources, and let it say 'I don't know'."
  (中) 主要的缓解办法是 RAG：给模型真实材料来 grounding，让它引用来源，并允许它说"不知道"。
- (EN) "Alignment means making the model do what humans want and avoid harm. RLHF is the common method: SFT, then a reward model, then reinforcement learning."
  (中) alignment 就是让模型按人类意图来、避免有害。RLHF 是常见方法：先 SFT，再训奖励模型，再用强化学习优化。
- (EN) "A common goal is HHH — Helpful, Harmless, Honest. Reducing hallucination is mostly the 'Honest' part of alignment."
  (中) 常见目标是 HHH——有用、无害、诚实。减少幻觉主要对应对齐里的"诚实"那一项。

## 延伸阅读
- *Training language models to follow instructions with human feedback*（InstructGPT, Ouyang et al., 2022）—— RLHF 三步法的代表性论文。
- *Constitutional AI: Harmlessness from AI Feedback*（Bai et al., 2022, Anthropic）—— Constitutional AI 思路。⚠️待核实（标题/作者细节请核对）
- *A General Language Assistant as a Laboratory for Alignment*（Askell et al., 2021）—— HHH（Helpful/Harmless/Honest）框架来源。⚠️待核实
- *Survey of Hallucination in Natural Language Generation* —— 幻觉成因与缓解方法综述（可查最新版本）。⚠️待核实
