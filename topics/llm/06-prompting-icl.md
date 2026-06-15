---
topic: Prompting & In-context Learning
domain: llm
difficulty: 基础
status: drafted
prerequisites: []
tags: [prompting, in-context-learning, few-shot, chain-of-thought, prompt-engineering, self-consistency, tree-of-thought, ReAct, context-engineering, lost-in-the-middle]
---

# Prompting & In-context Learning

## 一句话概览
> Prompting 就是用一段文本把任务讲清楚给模型；in-context learning 是大模型的一种能力——光靠 prompt 里给的几个示例就能"临时学会"任务，**完全不更新权重**。

## 概念讲解

**1. 什么是 prompting**
Prompt 就是你喂给模型的那段输入文本。LLM 本质是"接着往下写"的模型，所以你怎么写 prompt，直接决定它怎么续。Prompting 就是**通过设计输入文本来引导模型完成任务**，不改模型本身。

**2. zero-shot vs few-shot**
- **zero-shot（零样本）**：prompt 里**不给任何示例**，只给指令。比如直接说 "Classify this review as positive or negative: ..."。
- **few-shot（少样本）**：prompt 里**给几个做好的例子**，再让模型照着做。给 1 个叫 one-shot，给几个叫 few-shot。

```
（few-shot 示意）
Review: "Loved it!"      → Positive
Review: "Total waste."   → Negative
Review: "Best purchase." → ?
```

模型看了前两个"输入→输出"的例子，就能照着格式判断第三个。

**3. 什么是 in-context learning（ICL）**
这是大模型一个很关键的特性：**仅凭 prompt 里给的示例，就能在当前这次对话里"学会"任务**，而**不更新任何权重**。
- 类比：不是"上学训练"（fine-tuning 那种改权重的真正学习），而是"考试时看一眼参考例题，照着做这一题"。
- 学到的东西**不持久**：这次对话结束、示例不在 prompt 里了，模型就不"记得"了。
- 它发生在**推理（inference）阶段**，靠的是 attention 在上下文里找规律，不是梯度更新。

**4. chain-of-thought（CoT，思维链）**
让模型在给最终答案前，**先一步步写出推理过程**。
- 最简单的触发方式之一：在 prompt 里加一句 "Let's think step by step."（zero-shot CoT，来自 Kojima et al. 2022；**出处已对照 repo 核对**，但具体提升幅度随模型 / 任务而变）。
- 直觉：把一道难题拆成小步，模型每一步只做一点点，错误更少；尤其对**数学、逻辑、多步推理**类任务帮助明显。
- 代价：输出更长、更慢、token 更多。

**5. system / user 角色**
现在的 chat 模型把 prompt 分成不同角色（role）：
- **system prompt（系统提示）**：设定模型的**身份、风格、总体规则**，相当于"出场前的导演说明"。比如 "You are a helpful coding assistant. Always answer in English."
- **user prompt（用户提示）**：用户**本轮具体的问题/请求**。
- （还有 **assistant** 角色，是模型自己历史回复。）
- system 通常**优先级更高、更稳定**，适合放贯穿全程的约束。

**6. prompt engineering 实用技巧**
写好 prompt 的几条常见经验：
- **清晰指令**：直接说要做什么，别绕。明确动词（总结 / 分类 / 翻译 / 提取）。
- **给示例（few-shot）**：示范"输入长这样、输出长这样"，比纯描述更有效。
- **指定输出格式**：要 JSON 就说 "Return JSON with keys x, y"，要列表就说清楚，减少自由发挥。
- **分步 / 拆任务**：复杂任务拆成几步，或让模型先想再答（CoT）。
- **给上下文/约束**：补背景、设边界（"只用给定材料回答"），减少跑题和编造。

**7. prompting vs fine-tuning 的取舍**
两条改变模型行为的路：
- **prompting**：不动权重，快、便宜、好试错；但能力受限于模型已有知识，长 prompt 占 context、每次调用都要带着示例。
- **fine-tuning**：用数据再训练、**改权重**；能更深地定制风格/任务、省掉每次的长示例；但要数据、算力、时间，且改完不易回退。
- 经验法则：**先用 prompting（含 few-shot）试**，能解决就别 fine-tune；只有当任务量大、要稳定特定行为、prompt 怎么调都不够时，再考虑 fine-tuning。

**8. 比 CoT 更进阶的推理 prompting（了解即可）**
CoT 之上还有几种"靠 prompt 提升推理"的常见套路（面试能点到为止）：
- **self-consistency（自一致）**：对同一题用带随机性的采样跑**多条**推理链，再对最终答案**投票**取多数。比单条 CoT 更稳，代价是多花算力。
- **tree-of-thought（ToT，思维树）**：把推理展开成**树**——生成多个中间想法、评估、剪枝、再往下探，适合需要搜索 / 回溯的难题。
- **ReAct（reason + act）**：让模型在"思考 → 调用工具 / 查资料（act）→ 看结果（observe）"之间循环，把推理和**外部工具**结合。这也是 agent 的基础套路（详见 `10-agents`）。
> 这些都不改权重，仍属 prompting；区别在于"组织推理的结构"。

**9. context engineering（上下文工程）：比 prompt 更大的范畴**
- **定义**：prompt engineering 只是其中一小块。**context（上下文）= 进到模型窗口里的一切**：system 指令、检索来的文档、工具定义、对话历史、few-shot 示例，以及当前 prompt。怎么**取舍 / 安排**这些，就是 context engineering。
- **窗口是稀缺资源**：context window 像 RAM——又快又有限。**精挑的 1 万 token 常比硬塞的 10 万 token 更好**；attention 是 O(n²)，塞太多既贵又稀释重点。
- **lost-in-the-middle（中间被忽略）**：模型对放在**开头和结尾**的信息利用得最好，**放在中间**的容易被忽略（Liu et al. 2023）。实践：最关键的信息放最前 / 最后，query 和最相关内容靠近末尾，别把要点埋在中段。
- **常见手段**：相关性过滤、动态只挂需要的工具、历史压缩（把旧轮总结掉）、用 2–3 个强 few-shot 例子而不是堆一大段指令。

## 面试问答卡

### Q1. What is the difference between zero-shot and few-shot prompting? / zero-shot 和 few-shot prompting 有什么区别？
**难度:** 基础
**Answer (EN):**
- Zero-shot means you give only an instruction, with no examples.
- Few-shot means you put a few worked examples in the prompt, then ask the model to follow them.
- Few-shot usually helps the model match the format and the task better.
**核心答案 (中):**
- zero-shot：prompt 里**只给指令、不给示例**。
- few-shot：prompt 里**给几个做好的例子**，让模型照着做。
- few-shot 通常能让模型更好地对齐**格式和任务**。
**追问 / 深入 (中):**
- 追问"few-shot 给几个例子合适？" → 没有定数，经验上 **3–5 个**常够用，再多往往收益递减、还占 context、变慢；选**和当前问题相似**的例子通常比随机选更好。
- 追问"例子顺序重要吗？" → 重要，示例的顺序和选取会影响结果（order/selection sensitivity），是 few-shot 的已知不稳定点。
**常见误区 (中):**
- 以为 few-shot 里的"shot"是训练步数；这里 shot 指**prompt 里的示例个数**，不涉及任何训练。

### Q2. What is in-context learning? / 什么是 in-context learning？
**难度:** 基础
**Answer (EN):**
- In-context learning means the model learns a task just from examples in the prompt, at inference time.
- It does NOT update any weights. Nothing is saved after the conversation.
- It works because the model uses attention to find the pattern in the context.
**核心答案 (中):**
- in-context learning 指模型**仅凭 prompt 里的示例**，在**推理时**就学会任务。
- **不更新任何权重**，对话结束就不"记得"了。
- 靠的是 attention 在上下文里找规律，不是梯度更新。
**追问 / 深入 (中):**
- 追问"那它和 fine-tuning 本质区别？" → fine-tuning **改权重、能持久**；ICL **不改权重、只在当前 context 里临时生效**。
- 追问"为什么大模型才有这能力？" → 这是规模变大后涌现（emergent）出来的能力，小模型通常不明显（⚠️待核实：具体在哪个规模阈值出现，随模型族不同，无统一定论）。
**常见误区 (中):**
- 以为 ICL 会"记住"用户教的东西；它不持久，下次新对话又是白纸。
- 把 ICL 当成训练；它发生在 inference，不产生权重更新。

### Q3. What is chain-of-thought prompting and when does it help? / 什么是 chain-of-thought？什么时候有用？
**难度:** 进阶
**Answer (EN):**
- Chain-of-thought (CoT) asks the model to write its reasoning step by step before the final answer.
- It helps most on multi-step tasks like math, logic, and reasoning.
- The cost is longer, slower output and more tokens.
**核心答案 (中):**
- chain-of-thought（CoT）让模型在给答案前**一步步写出推理过程**。
- 对**数学、逻辑、多步推理**类任务帮助最大。
- 代价是输出更长、更慢、更费 token。
**追问 / 深入 (中):**
- 追问"怎么触发 CoT？" → 可以给带推理过程的 few-shot 例子，或直接加一句类似 "Let's think step by step." 的提示词。
- 追问"CoT 一定让答案更对吗？" → 不一定；它能减少多步任务的错误，但推理过程本身也可能写错（看起来有理却结论错），不能盲信。
**常见误区 (中):**
- 以为 CoT 改变了模型的"思考方式"；它只是引导模型把中间步骤**显式写出来**，本质还是续写。
- 对简单任务也强加 CoT，徒增延迟和成本。

### Q4. What is the difference between a system prompt and a user prompt? / system prompt 和 user prompt 有什么区别？
**难度:** 基础
**Answer (EN):**
- The system prompt sets the model's role, style, and overall rules for the whole chat.
- The user prompt is the user's specific request for this turn.
- The system prompt usually has higher priority and stays stable across turns.
**核心答案 (中):**
- system prompt 设定模型的**身份、风格、整体规则**，贯穿整个对话。
- user prompt 是用户**本轮具体的请求**。
- system 通常**优先级更高、更稳定**，适合放全程约束。
**追问 / 深入 (中):**
- 追问"还有别的角色吗？" → 还有 assistant 角色，是模型自己的历史回复；多轮对话就是 system + 交替的 user/assistant。
- 追问"system prompt 是不是绝对优先？" → 不是绝对铁律；它优先级高，但仍可能被精心构造的输入绕过（prompt injection 风险）。
**常见误区 (中):**
- 把所有约束都堆在 user prompt 里；贯穿全程的规则放 system 更稳。

### Q5. When would you choose prompting over fine-tuning? / 什么时候选 prompting 而不是 fine-tuning？
**难度:** 进阶
**Answer (EN):**
- Prompting does not change weights: it is fast, cheap, and easy to try and change.
- Fine-tuning trains on data and changes weights: better for deep, stable customization, but needs data, compute, and time.
- Rule of thumb: try prompting (and few-shot) first; fine-tune only when prompting is not enough or you need a stable behavior at scale.
**核心答案 (中):**
- prompting **不改权重**：快、便宜、好试错、好改。
- fine-tuning **用数据训练、改权重**：能更深更稳地定制，但要数据、算力、时间。
- 经验法则：**先试 prompting（含 few-shot）**，不够再考虑 fine-tuning（任务量大、要稳定特定行为时）。
**追问 / 深入 (中):**
- 追问"prompting 有什么缺点？" → 长 prompt / 示例每次调用都要带着，**占 context、增加延迟和成本**，且能力受限于模型已有知识。
- 追问"除了这两条还有别的路吗？" → 还有 RAG（把外部知识检索进 prompt）等；常见做法是 prompting + RAG 先行，fine-tune 作为最后手段。
**常见误区 (中):**
- 一上来就 fine-tune；很多需求其实好的 prompt + few-shot 就够了，fine-tune 成本和维护负担更大。
- 以为 fine-tune 能"教给模型新事实"且总比 prompting 准；它更擅长定制**风格/格式/任务行为**，灌注大量新知识不一定可靠，常不如 RAG。

### Q6. Beyond chain-of-thought: what are self-consistency, tree-of-thought, and ReAct? / CoT 之外：self-consistency、tree-of-thought、ReAct 是什么？
**难度:** 高阶
**Answer (EN):**
- Self-consistency samples several reasoning chains for the same question and takes a majority vote on the final answer — more reliable than a single chain, at extra cost.
- Tree-of-thought expands reasoning into a tree: generate several intermediate thoughts, evaluate, prune, and search — good for problems that need backtracking.
- ReAct interleaves reasoning with actions: think → call a tool / look something up → observe → repeat. It connects reasoning to external tools and is the basis of agents.
- All three are prompting (no weight update); they differ in how they structure the reasoning.
**核心答案 (中):**
- self-consistency：对同一题采样**多条**推理链，对最终答案**投票**取多数，比单条更稳，代价是多花算力。
- tree-of-thought：把推理展开成**树**——生成多个想法、评估、剪枝、搜索，适合要回溯的难题。
- ReAct：在"思考 → 调用工具 / 查资料 → 看结果"之间循环，把推理和**外部工具**结合，是 agent 的基础。
- 三者都不改权重，仍是 prompting；区别在"组织推理的结构"。
**追问 / 深入 (中):**
- 追问"这些是不是都更准但更贵？" → 基本是。self-consistency 和 ToT 用更多算力换稳健 / 搜索能力；简单任务不值得，难推理 / 要回溯时才用。
**常见误区 (中):**
- 以为它们改了模型；都只是 prompt 层面"怎么组织推理"，不动权重。
- 把 ReAct 当成纯推理技巧；它的关键是**接外部工具**（搜索、计算器、API），属于 agent 范畴。

### Q7. What is context engineering, and what is "lost in the middle"? / 什么是 context engineering？什么是 "lost in the middle"？
**难度:** 进阶
**Answer (EN):**
- Context engineering is bigger than prompt engineering: context is everything in the model's window — system instructions, retrieved documents, tool definitions, chat history, few-shot examples, and the prompt.
- The window is a scarce resource; a curated 10K tokens often beats a dumped 100K, because attention is O(n²) and extra text dilutes the signal.
- "Lost in the middle" means models use information at the start and end of the context best, and tend to ignore what's in the middle.
- So put the most important information first or last, keep the query and most-relevant context near the end, and don't bury key points in the middle.
**核心答案 (中):**
- context engineering 比 prompt engineering 范畴更大：context = 模型窗口里的一切——system 指令、检索文档、工具定义、对话历史、few-shot、prompt。
- 窗口是稀缺资源；**精挑的 1 万 token 常比硬塞的 10 万更好**，因为 attention 是 O(n²)，多塞会稀释重点、还贵。
- "lost in the middle"：模型对放在**开头和结尾**的信息用得最好，**中间**的容易被忽略。
- 实践：最关键的信息放最前 / 最后，query 和最相关内容靠近末尾，别把要点埋中段。
**追问 / 深入 (中):**
- 追问"那是不是 context 越长越好？" → 不是。长 context 既贵又有 lost-in-the-middle 问题；关键是**放什么、放哪**，而不是一味塞满。
**常见误区 (中):**
- 以为把所有资料都塞进 context 模型就能用好；位置和相关性比总量更重要。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "Prompting means I guide the model with the input text only, without changing the model itself."
  (中) prompting 就是只用输入文本引导模型，不改模型本身。
- (EN) "Zero-shot gives just an instruction; few-shot also puts a few examples in the prompt to show the format."
  (中) zero-shot 只给指令；few-shot 还在 prompt 里放几个例子来示范格式。
- (EN) "In-context learning means the model learns from the examples in the prompt at inference time, with no weight update — nothing is saved after the chat."
  (中) in-context learning 是模型在推理时从 prompt 里的示例学习，不更新权重，对话结束就不记得了。
- (EN) "Chain-of-thought asks the model to reason step by step before answering, which helps on math and multi-step tasks."
  (中) chain-of-thought 让模型先一步步推理再回答，对数学和多步任务有帮助。
- (EN) "The system prompt sets the role and rules for the whole chat; the user prompt is the request for this turn."
  (中) system prompt 设定整段对话的身份和规则；user prompt 是本轮的具体请求。
- (EN) "I try prompting and few-shot first because it's fast and cheap, and fine-tune only when prompting is not enough."
  (中) 我先用 prompting 和 few-shot，因为快又便宜；只有它不够时才 fine-tune。
- (EN) "Beyond chain-of-thought there are self-consistency, tree-of-thought, and ReAct — different ways to structure reasoning, still all prompting."
  (中) CoT 之外还有 self-consistency、tree-of-thought、ReAct——组织推理的不同方式，本质都还是 prompting。
- (EN) "Context engineering is bigger than the prompt: it's everything in the window. Curate it, and remember models lose information in the middle."
  (中) context engineering 比 prompt 大：是窗口里的一切。要精挑，并记住模型会忽略放中间的信息。

## 延伸阅读
- *Language Models are Few-Shot Learners*（Brown et al., 2020，GPT-3 论文）—— few-shot / in-context learning 的代表性工作。
- *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*（Wei et al., 2022）—— CoT 原论文。
- *Large Language Models are Zero-Shot Reasoners*（Kojima et al., 2022）—— "Let's think step by step" 的 zero-shot CoT（出处已对照 repo 核对；具体提升幅度随模型 / 任务而变）。
- *Self-Consistency Improves Chain of Thought Reasoning*（Wang et al., 2023）/ *Tree of Thoughts*（Yao et al., 2023）/ *ReAct*（Yao et al., 2022）—— CoT 之上的进阶推理 prompting。
- *Lost in the Middle: How Language Models Use Long Contexts*（Liu et al., 2023）—— 长 context 中"中间信息被忽略"的现象。
- *ai-engineering-from-scratch*（rohitg00）Phase 11 `02-few-shot-cot` / `05-context-engineering` —— few-shot、CoT 出处、进阶推理与 context engineering。本次加料与核对依据。
