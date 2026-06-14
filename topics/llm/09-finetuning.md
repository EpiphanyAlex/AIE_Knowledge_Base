---
topic: Fine-tuning（LoRA / RLHF / DPO）
domain: llm
difficulty: 进阶
status: drafted
prerequisites: [pretraining-objectives]
tags: [fine-tuning, LoRA, QLoRA, RLHF, DPO, PEFT, instruction-tuning]
---

# Fine-tuning（LoRA / RLHF / DPO）

## 一句话概览
> Fine-tuning 是在一个已经预训练好的模型上**继续训练**，让它适配你的任务、风格或偏好；现在主流不是改全部参数，而是用 LoRA 这类 PEFT 方法只训练一小块增量，再配合 SFT、RLHF/DPO 等阶段做"对齐"。

## 概念讲解

**1. 什么是 fine-tuning（直觉）**
预训练（pretraining）让模型在海量文本上学会通用的语言能力，但它不一定知道**你想要的格式、语气或专业知识**。fine-tuning 就是拿这个"通才"模型，用一批更小、更有针对性的数据继续训练，把它调成"专才"。类比：预训练 = 上完大学的通识教育，fine-tuning = 入职后的岗位培训。

**2. Full fine-tuning vs PEFT（为什么不直接改全部参数）**
- **Full fine-tuning（全量微调）**：更新模型**所有**参数。效果好，但很贵——要存一整份新权重（几十亿参数），显存和存储都吃不消；每个任务都存一份完整模型也不现实。
- **PEFT（Parameter-Efficient Fine-Tuning，参数高效微调）**：**冻结**原模型的绝大部分参数，只训练**很小一部分**新增参数。省显存、省存储，一个底座模型可以挂多个小"插件"切换任务。LoRA 是目前最常用的 PEFT 方法。

**3. LoRA 的核心思想（冻结原权重，训练低秩增量）**
LoRA（Low-Rank Adaptation）的关键假设：微调时权重的**变化量 ΔW 是"低秩"的**——也就是这个变化没那么复杂，可以用两个小矩阵的乘积来近似。

- 原权重矩阵 `W`（很大，比如 d×d）**冻结不动**。
- 把变化量拆成两个瘦长矩阵：`ΔW ≈ B · A`，其中 `A` 是 r×d、`B` 是 d×r，**r 很小**（比如 8、16）。
- 前向计算变成：`h = Wx + BAx`（原输出 + 低秩增量）。
- 训练时**只更新 A、B**，参数量从 d×d 降到 2×r×d，通常只占原模型的零点几个百分点。

直觉：与其重写整本书（改 W），不如贴一叠小便签（A、B）。推理时还可以把 `BA` **合并回 W**，这样不增加推理延迟。

**4. QLoRA（在 LoRA 基础上再省显存）**
QLoRA = **量化（quantization）+ LoRA**。把冻结的底座模型用低精度（如 4-bit）存储，大幅降低显存占用，同时仍用全精度训练那两个小 LoRA 矩阵。好处是**单张消费级 GPU 就能微调很大的模型**。它的代表性技术包括 4-bit NormalFloat（NF4）量化等。

**5. Instruction tuning / SFT（让模型"会听话"）**
预训练后的模型是个"续写机器"，给它一句话它就接着写，不一定按指令做事。
- **Instruction tuning（指令微调）**：用大量"指令 → 期望回答"的样本训练，让模型学会**遵循指令**。
- **SFT（Supervised Fine-Tuning，监督微调）**：就是用人工写好的高质量"问题-答案"对做监督训练。指令微调通常就是通过 SFT 实现的。
- SFT 是对齐流程的**第一步**：先让模型学会"该长什么样"。

**6. 对齐阶段之 RLHF（用人类偏好进一步对齐）**
SFT 之后，模型会回答了，但还不一定**符合人类偏好**（有用、无害、诚实）。RLHF（Reinforcement Learning from Human Feedback）三步：
1. **SFT**：先做监督微调，得到一个初始能听话的模型。
2. **训练 reward model（奖励模型）**：让人对同一问题的多个回答**排序**（A 比 B 好），用这些偏好数据训练一个模型，它能给任意回答打一个"好坏分数"。
3. **用 RL 优化（PPO）**：把语言模型当作"策略"，让它生成回答、用 reward model 打分，用强化学习算法 **PPO（Proximal Policy Optimization）** 朝高分方向更新；同时加一个 **KL 惩罚**，约束新模型别偏离 SFT 模型太远（防止它为了刷分输出乱七八糟的东西）。

直觉：reward model 是个"自动评委"，PPO 让模型学会去讨好这个评委，但 KL 惩罚拉着它别走火入魔。

**7. 对齐阶段之 DPO（免去单独 reward model）**
RLHF 流程复杂、不稳定（要单独训 reward model + 调 PPO）。**DPO（Direct Preference Optimization，直接偏好优化）**的思路：跳过显式的 reward model 和 RL，**直接用偏好数据（好回答 vs 坏回答）做一次类似监督训练的优化**。

- 数据形式一样：每条是 `(prompt, 更优回答, 更差回答)`。
- DPO 用一个数学推导，把"最大化奖励 + KL 约束"这个 RLHF 目标，**等价改写成一个直接在偏好数据上的分类式损失**，让模型**提高对"好回答"的相对概率、降低"坏回答"的概率**。
- 好处：**不用单独训 reward model，也不用 PPO**，更简单、更稳定、更省资源；缺点是灵活性不如完整 RLHF，且仍依赖偏好数据质量。

直觉：RLHF 是"先训个评委，再让学生去讨好评委"；DPO 是"直接拿着标好的优劣样本，告诉学生哪种答法更好"。

**8. 什么时候用 fine-tuning vs RAG vs prompting（决策）**
三者解决的问题不同，常常**组合使用**，不是二选一：
- **Prompting（含 few-shot）**：不改模型，只改输入。最快最便宜，适合任务简单、需求多变、原型阶段。
- **RAG（检索增强生成）**：把外部知识检索出来塞进 prompt。适合**知识会变、要可溯源、要减少幻觉**的场景（如查公司内部文档）。改的是"模型看到什么内容"，不是模型本身。
- **Fine-tuning**：改模型本身。适合要**固定的风格 / 格式 / 语气**、要让模型掌握 prompt 难以表达的**行为模式或技能**、或要**压缩 prompt 长度 / 降低推理成本**的场景。
- 一句话经验：**知识类问题优先 RAG，行为/风格类问题优先 fine-tuning，能用 prompt 搞定就先别动模型。**

## 面试问答卡

### Q1. What is fine-tuning, and how is it different from pretraining? / 什么是 fine-tuning？它和 pretraining 有什么区别？
**难度:** 基础
**Answer (EN):**
- Pretraining trains a model from scratch on huge general text to learn language broadly.
- Fine-tuning takes that pretrained model and trains it further on a smaller, task-specific dataset.
- Pretraining gives general ability; fine-tuning adapts it to a specific task, style, or domain.
**核心答案 (中):**
- pretraining 在海量通用文本上从头训练，学到通用语言能力。
- fine-tuning 拿预训练好的模型，用更小、更有针对性的数据继续训练。
- 预训练给"通才"能力，微调把它调成适配某个任务 / 风格 / 领域的"专才"。
**追问 / 深入 (中):**
- 追问"为什么不每次都从头训？" → 预训练极贵（海量算力和数据），fine-tuning 复用已学到的能力，又快又省。
**常见误区 (中):**
- 以为 fine-tuning 会教模型全新知识；它更擅长改**行为/格式/风格**，灌大量新事实性知识不如用 RAG 高效。

### Q2. What is the difference between full fine-tuning and PEFT? / full fine-tuning 和 PEFT 有什么区别？
**难度:** 基础
**Answer (EN):**
- Full fine-tuning updates all model parameters. It works well but is expensive in memory and storage.
- PEFT (Parameter-Efficient Fine-Tuning) freezes most parameters and trains only a small set of new ones.
- PEFT saves memory and storage, and lets one base model serve many tasks via small plug-in adapters.
**核心答案 (中):**
- full fine-tuning 更新所有参数，效果好但显存和存储都很贵。
- PEFT 冻结绝大部分参数，只训练一小部分新增参数。
- PEFT 省显存省存储，一个底座模型可以挂多个小 adapter 切换任务。
**追问 / 深入 (中):**
- 追问"为什么 full fine-tuning 存储贵？" → 每个任务都要存一整份新权重（几十亿参数），多任务时存不下；PEFT 只存几 MB 的小矩阵。
**常见误区 (中):**
- 以为 PEFT 一定比 full fine-tuning 差；很多任务上 PEFT 效果接近 full，但成本低得多，是常见的默认选择。

### Q3. How does LoRA work? / LoRA 是怎么工作的？
**难度:** 进阶
**Answer (EN):**
- LoRA assumes the weight change during fine-tuning is low-rank, so it can be approximated by two small matrices.
- It freezes the original weight W, and learns two small matrices A and B, so the update is B·A.
- The forward pass becomes h = Wx + BAx; only A and B are trained, which is a tiny fraction of all parameters.
- At inference you can merge BA back into W, so there is no extra latency.
**核心答案 (中):**
- LoRA 假设微调时的权重变化是低秩的，可以用两个小矩阵近似。
- 冻结原权重 W，只学两个小矩阵 A、B，增量是 B·A。
- 前向变成 `h = Wx + BAx`；只训练 A、B，参数量只占全部的一小部分。
- 推理时可把 BA 合并回 W，不增加延迟。
**追问 / 深入 (中):**
- 追问"r（秩）怎么选？" → r 越大表达力越强但参数越多，常用 8 / 16 / 32，是效果和成本的权衡。
- 追问"LoRA 加在哪些层？" → 常加在 attention 的 Q、K、V、O 投影矩阵上，也可扩到 MLP 层。
**常见误区 (中):**
- 以为 LoRA 改了原权重；原权重始终冻结，学的是旁路的增量。
- 把"低秩"理解成"参数少所以差"；低秩是说**变化量结构简单**，不是模型变笨。

### Q4. What is QLoRA and what problem does it solve? / 什么是 QLoRA？它解决什么问题？
**难度:** 进阶
**Answer (EN):**
- QLoRA combines quantization with LoRA.
- It stores the frozen base model in low precision (e.g. 4-bit) to cut memory use a lot.
- It still trains the small LoRA matrices in higher precision, so quality stays good.
- The main win: you can fine-tune very large models on a single consumer GPU.
**核心答案 (中):**
- QLoRA = quantization + LoRA。
- 把冻结的底座模型用低精度（如 4-bit）存储，大幅降低显存。
- 仍用较高精度训练那两个小 LoRA 矩阵，保住效果。
- 最大好处：单张消费级 GPU 就能微调很大的模型。
**追问 / 深入 (中):**
- 追问"量化会不会掉点？" → QLoRA 用 NF4 等技术尽量减少损失，论文显示在很多任务上接近全精度微调（⚠️待核实：具体差距随模型和任务变化）。
**常见误区 (中):**
- 以为 QLoRA 把整个模型都量化训练；只有**冻结的底座**被量化，可训练的 LoRA 矩阵仍是高精度。

### Q5. What is RLHF and what are its main steps? / 什么是 RLHF？它的主要步骤是什么？
**难度:** 进阶
**Answer (EN):**
- RLHF means Reinforcement Learning from Human Feedback; it aligns a model with human preferences.
- Step 1: SFT — supervised fine-tuning to get a model that follows instructions.
- Step 2: train a reward model from human rankings of different answers (which answer is better).
- Step 3: use RL (PPO) to push the model toward higher reward, with a KL penalty to stay close to the SFT model.
**核心答案 (中):**
- RLHF 即从人类反馈做强化学习，用来让模型对齐人类偏好。
- 第一步 SFT：监督微调，得到会听指令的模型。
- 第二步：用人对多个回答的排序训练 reward model（哪个回答更好）。
- 第三步：用 RL（PPO）朝高奖励方向优化，并加 KL 惩罚约束别偏离 SFT 模型太远。
**追问 / 深入 (中):**
- 追问"KL 惩罚是干嘛的？" → 防止模型为刷 reward 走极端、输出退化或重复；拉着它别离原模型太远。
- 追问"reward model 的数据怎么来？" → 人类对同一 prompt 的多个回答做两两比较 / 排序，得到偏好数据。
**常见误区 (中):**
- 以为 RLHF 直接用人给的"打分数字"训练；实际更常用的是**排序/比较**得到的偏好，再训 reward model。
- 以为 PPO 是唯一选择；它是经典做法，但不是唯一（见 DPO）。

### Q6. How does DPO differ from RLHF, and why use it? / DPO 和 RLHF 有什么不同？为什么用它？
**难度:** 高阶
**Answer (EN):**
- DPO means Direct Preference Optimization.
- RLHF needs a separate reward model plus RL (PPO), which is complex and can be unstable.
- DPO skips both: it uses the preference data (better answer vs worse answer) directly in a simple, supervised-style loss.
- It raises the probability of the preferred answer and lowers the rejected one, so it is simpler and more stable.
**核心答案 (中):**
- DPO 即直接偏好优化。
- RLHF 要单独的 reward model 加 RL（PPO），流程复杂、训练易不稳。
- DPO 跳过这两者：直接用偏好数据（好回答 vs 坏回答）做一个类似监督训练的损失。
- 它提高"好回答"的相对概率、降低"坏回答"的，所以更简单、更稳定。
**追问 / 深入 (中):**
- 追问"DPO 为什么能不要 reward model？" → 它通过数学推导，把 RLHF 的"最大奖励 + KL 约束"目标等价改写成一个直接在偏好对上的损失，奖励被隐式表达进去了。
- 追问"DPO 一定比 RLHF 好吗？" → 不一定。DPO 更简单稳定，但完整 RLHF 在某些场景下更灵活、上限可能更高，是工程权衡（⚠️待核实：两者优劣随设置和数据变化）。
**常见误区 (中):**
- 以为 DPO 不需要偏好数据；它**仍然需要**人标注的"好 vs 坏"成对数据，只是省掉了 reward model 和 RL。

### Q7. When should you choose fine-tuning vs RAG vs prompting? / 什么时候该选 fine-tuning、RAG 还是 prompting？
**难度:** 高阶
**Answer (EN):**
- Prompting (incl. few-shot): change only the input, not the model. Fastest and cheapest; good for simple or changing tasks and prototypes.
- RAG: retrieve external knowledge into the prompt. Best when knowledge changes often, needs sources, or you want fewer hallucinations.
- Fine-tuning: change the model itself. Best for a fixed style/format, behaviors hard to express in a prompt, or to shorten prompts and cut cost.
- They are often combined, not either-or: knowledge problems lean RAG, behavior/style problems lean fine-tuning, and try prompting first.
**核心答案 (中):**
- prompting（含 few-shot）：只改输入不改模型，最快最便宜，适合简单/多变任务和原型。
- RAG：把外部知识检索进 prompt，适合知识常变、要溯源、要少幻觉的场景。
- fine-tuning：改模型本身，适合固定风格/格式、prompt 难表达的行为、或要压缩 prompt 降成本。
- 三者常组合：知识类偏 RAG，行为/风格类偏 fine-tuning，能 prompt 搞定就先别动模型。
**追问 / 深入 (中):**
- 追问"知识更新很快的场景为什么不 fine-tune？" → fine-tune 把知识"烤进"权重，更新就得重训；RAG 改一下知识库即可，更灵活、可溯源。
- 追问"能不能一起用？" → 可以。常见做法：用 fine-tuning 固定语气/格式，再用 RAG 提供实时、可溯源的事实。
**常见误区 (中):**
- 以为想让模型"懂更多知识"就该 fine-tune；灌事实性知识通常 RAG 更高效、更易更新，且更少幻觉。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "Fine-tuning takes a pretrained model and trains it further on smaller, task-specific data to adapt its behavior, style, or domain."
  (中) fine-tuning 拿预训练模型，用更小、更针对性的数据继续训练，调它的行为、风格或领域。
- (EN) "Instead of full fine-tuning, we usually use PEFT, which freezes most weights and trains only a small set of new parameters."
  (中) 现在通常不做全量微调，而用 PEFT：冻结大部分权重，只训练一小部分新参数。
- (EN) "LoRA assumes the weight update is low-rank, so it freezes W and learns two small matrices A and B, where the update is B times A."
  (中) LoRA 假设权重变化是低秩的，冻结 W，只学两个小矩阵 A、B，增量是 B 乘 A。
- (EN) "QLoRA adds quantization on top: it stores the frozen base in 4-bit, so you can fine-tune big models on one GPU."
  (中) QLoRA 再加量化：把冻结底座用 4-bit 存，单张 GPU 就能微调大模型。
- (EN) "For alignment, RLHF trains a reward model from human preferences and uses PPO to optimize toward it, with a KL penalty."
  (中) 对齐方面，RLHF 用人类偏好训一个 reward model，再用 PPO 朝它优化，并加 KL 惩罚。
- (EN) "DPO is simpler: it skips the reward model and RL, and learns directly from preference pairs to prefer good answers over bad ones."
  (中) DPO 更简单：跳过 reward model 和 RL，直接从偏好对学习，让模型偏好好回答、抑制坏回答。
- (EN) "Rule of thumb: prompt first, use RAG for knowledge that changes, and fine-tune for fixed style or behavior."
  (中) 经验法则：先用 prompt，知识常变用 RAG，固定风格或行为用 fine-tuning。

## 延伸阅读
- *LoRA: Low-Rank Adaptation of Large Language Models*（Hu et al., 2021）—— LoRA 原论文。
- *QLoRA: Efficient Finetuning of Quantized LLMs*（Dettmers et al., 2023）—— QLoRA 与 4-bit NF4 量化。
- *Training language models to follow instructions with human feedback*（Ouyang et al., 2022，InstructGPT）—— RLHF 三步流程的代表论文。
- *Direct Preference Optimization: Your Language Model is Secretly a Reward Model*（Rafailov et al., 2023）—— DPO 原论文。
- Hugging Face PEFT 文档 —— LoRA / QLoRA 等方法的实践入口（⚠️待核实：以官方最新文档为准）。
