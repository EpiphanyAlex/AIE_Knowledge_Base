---
topic: 解码与采样策略
domain: llm
difficulty: 基础
status: drafted
prerequisites: []
tags: [decoding, sampling, temperature, top-p, top-k, beam-search]
---

# 解码与采样策略

## 一句话概览
> LLM 每步输出的是"下一个 token"在整个词表上的概率分布，解码（decoding）就是怎么从这个分布里挑词——挑法不同，直接决定生成内容的随机性、多样性和质量。

## 概念讲解

**1. 起点：每步是一个概率分布**
模型每生成一个 token，最后一层会先算出一组 **logits**（词表里每个 token 的原始打分），再过 **softmax** 变成一个加起来为 1 的概率分布。比如 "The cat sat on the ___"，模型可能给 "mat" 0.4、"floor" 0.2、"sofa" 0.1……解码要解决的就是：**从这个分布里选哪个 token**。选完这个 token，把它接到序列后面，再算下一步——这是一个逐步（autoregressive，自回归）的过程。

**2. greedy decoding（贪心解码）**
最简单：每步都选概率最高的那个 token。
- 优点：确定（deterministic）、快、可复现。
- 缺点：**短视**——这一步选最优，不代表整句最优；容易重复、单调。

**3. beam search（束搜索）**
不只保留一条路径，而是同时保留 **k 条**最可能的部分序列（k 叫 beam width，束宽）。每步对每条路径扩展候选，再按累积概率保留得分最高的 k 条。最后选整体概率最高的一条。
- 优点：比 greedy 更可能找到全局更优的句子，适合**有标准答案**的任务（如翻译、摘要）。
- 缺点：计算量随 k 增大；倾向生成**安全、偏短、偏通用**的句子；对开放式创意生成反而显得**乏味、重复**。

**4. temperature（温度）：缩放 logits**
在 softmax 之前，把 logits 除以一个温度 T：
```
softmax(logits / T)
```
- **T < 1**：分布更"尖"，高概率 token 更突出 → 更确定、更聚焦。
- **T = 1**：用原始分布。
- **T > 1**：分布更"平"，低概率 token 也有机会 → 更随机、更多样。
- **T → 0**：约等于 greedy（永远选最大概率那个）。

直觉：温度调的是"分布有多平/多尖"，不改模型权重，只改这一步采样。

**5. top-k 采样**
只在概率最高的 **k 个** token 里采样，其余直接丢弃（概率置 0、重新归一化）。
- k 小 → 更保守；k 大 → 更多样。
- 缺点：k 是固定数量，**不看分布形状**。有时前几个 token 就占了绝大部分概率（应该只留少数），有时概率很分散（应该多留几个），固定 k 不够灵活。

**6. top-p / nucleus sampling（核采样）**
不固定数量，而是**按累积概率**选：从高到低累加 token 概率，直到累积超过阈值 p（如 0.9），就在这批 token 里采样。
- 候选集合大小**随分布自动变化**：分布尖时候选少，分布平时候选多 → 比 top-k 更自适应。
- 这是开放式生成里很常用的默认策略。

**7. repetition / frequency penalty（重复惩罚）简述**
LLM 容易陷入重复（一直说同一句）。常见缓解：
- **repetition penalty**：对**已经出现过**的 token，降低它再次被选中的概率。
- **frequency penalty**：出现**次数越多**，惩罚越大（按频次线性叠加）。
- **presence penalty**：只要出现过就惩罚一个固定量（不看次数），鼓励引入新词。
> ⚠️待核实：上述三个 penalty 的**具体公式与取值范围**各家实现/API 不一致（如 OpenAI 的 frequency/presence penalty 取值范围、HuggingFace 的 repetition_penalty 默认与算法），用到具体平台时以其官方文档为准。

**8. 怎么选：确定性任务 vs 创意任务**
- **确定性 / 有标准答案**（翻译、代码、抽取、分类、数学）：要稳、要可复现 → 倾向 greedy 或低 temperature（甚至 T=0）、小 top-p。
- **开放式 / 创意**（写故事、头脑风暴、对话）：要多样、不单调 → 适度 temperature（如 0.7~1.0）+ top-p（如 0.9）。
> ⚠️待核实：上面括号里的**具体数值**是常见经验区间，不是硬性标准；不同模型/任务最优值不同，需自己调。

## 面试问答卡

### Q1. What does an LLM output at each step, and what is decoding? / LLM 每一步输出什么？什么是解码？
**难度:** 基础
**Answer (EN):**
- At each step the model outputs logits over the whole vocabulary, then softmax turns them into a probability distribution for the next token.
- Decoding is the rule for picking the next token from that distribution.
- The chosen token is appended, and the model runs again — this is autoregressive generation.
**核心答案 (中):**
- 每一步模型先输出整个词表的 logits，softmax 把它变成"下一个 token"的概率分布。
- decoding（解码）就是**从这个分布里挑 token 的规则**。
- 挑出的 token 接到序列后面再算下一步，这是自回归（autoregressive）生成。
**追问 / 深入 (中):**
- 追问"logits 和概率啥区别？" → logits 是 softmax 之前的原始打分，可正可负、不归一；过 softmax 后才是加起来为 1 的概率。
**常见误区 (中):**
- 以为模型"直接吐出一个词"；其实它给的是**整个词表的分布**，挑哪个由解码策略决定。

### Q2. What is greedy decoding? What are its pros and cons? / 什么是 greedy decoding？优缺点是什么？
**难度:** 基础
**Answer (EN):**
- Greedy decoding picks the highest-probability token at every step.
- Pros: deterministic, fast, and easy to reproduce.
- Cons: it is short-sighted — picking the best token now may not give the best full sentence; output can be repetitive and dull.
**核心答案 (中):**
- greedy 每一步都选概率最高的 token。
- 优点：确定、快、可复现。
- 缺点：**短视**——单步最优不等于整句最优；容易重复、单调。
**追问 / 深入 (中):**
- 追问"什么时候用 greedy？" → 需要稳定、可复现的确定性任务（如代码、抽取），或要 debug 时；不适合要多样性的创意生成。
**常见误区 (中):**
- 以为 greedy 一定给"最好的句子"；它只保证每一步局部最优，整句未必最优。

### Q3. What is temperature and how does it change the output? / 什么是 temperature？它怎么影响输出？
**难度:** 基础
**Answer (EN):**
- Temperature scales the logits before softmax: softmax(logits / T).
- Low temperature (T < 1) makes the distribution sharper — more focused and deterministic.
- High temperature (T > 1) makes it flatter — more random and diverse.
- T near 0 behaves like greedy decoding.
**核心答案 (中):**
- temperature 在 softmax 之前缩放 logits：softmax(logits / T)。
- 低温（T < 1）让分布更尖 → 更聚焦、更确定。
- 高温（T > 1）让分布更平 → 更随机、更多样。
- T 接近 0 时约等于 greedy decoding。
**追问 / 深入 (中):**
- 追问"temperature=0 严格等于 greedy 吗？" → 概念上等价（永远选最大概率 token）；实现上 T=0 会让公式除零，所以代码里通常**特判**成 greedy 而不是真的代入 0。
**常见误区 (中):**
- 以为 temperature 改的是模型权重；它只改采样这一步，不动任何参数。
- 以为 temperature 越高一定越好；太高会胡言乱语，是质量与多样性的权衡。

### Q4. Compare top-k and top-p (nucleus) sampling. / 比较 top-k 和 top-p（nucleus）采样。
**难度:** 进阶
**Answer (EN):**
- top-k keeps the k most likely tokens and samples among them; k is a fixed count.
- top-p (nucleus) keeps the smallest set of tokens whose cumulative probability reaches p, then samples among them.
- top-p adapts to the distribution: a sharp distribution gives few candidates, a flat one gives more.
- top-k ignores the distribution shape, so the same k can be too tight or too loose depending on the step.
**核心答案 (中):**
- top-k 保留概率最高的 **k 个** token 再采样，k 是固定数量。
- top-p（nucleus）按**累积概率**保留：从高到低加到超过 p 为止，再在这批里采样。
- top-p 会**自适应分布**：分布尖时候选少，分布平时候选多。
- top-k 不看分布形状，固定 k 在不同步可能太紧或太松。
**追问 / 深入 (中):**
- 追问"top-k、top-p 能和 temperature 一起用吗？" → 能，常组合：temperature 先调分布"平/尖"，再用 top-k/top-p 截断候选集，最后采样。
**常见误区 (中):**
- 把 top-p 的 p 当成"保留 p 个 token"；p 是**累积概率阈值**（如 0.9），不是数量。
- 以为 top-k / top-p 让输出确定；它们只是**缩小候选集**，最终仍是随机采样。

### Q5. What is beam search? When is it good, and when does it hurt? / 什么是 beam search？什么时候好用，什么时候反而不好？
**难度:** 进阶
**Answer (EN):**
- Beam search keeps the k best partial sequences (beam width) at each step, instead of just one.
- It is more likely to find a high-probability full sentence, so it helps tasks with a clear target like translation or summarization.
- Downsides: more compute as k grows; it favors safe, short, generic sentences, which makes open-ended creative text dull and repetitive.
**核心答案 (中):**
- beam search 每步保留 **k 条**最优部分序列（k 是 beam width），而不是只留一条。
- 它更可能找到整体高概率的句子，所以适合**有明确目标**的任务，如翻译、摘要。
- 缺点：k 越大算得越多；倾向**安全、偏短、通用**的句子，用在开放式创意生成会显得乏味、重复。
**追问 / 深入 (中):**
- 追问"为什么开放式生成不爱用 beam search？" → 高概率 ≠ 有趣，beam 会偏向"最稳"的说法，缺乏多样性；创意场景更常用 temperature + top-p 采样。
**常见误区 (中):**
- 以为 beam search 一定给"最优句子"；它只在保留的 k 条里找近似最优，且高概率不等于高质量。
- 把 beam width 和 batch size 混了：beam width 是**搜索保留的候选条数**，不是并行样本数。

### Q6. What are repetition / frequency / presence penalties? / repetition / frequency / presence penalty 是什么？
**难度:** 进阶
**Answer (EN):**
- These penalties reduce repetitive output by lowering the score of tokens the model already used.
- repetition penalty: down-weight any token that already appeared.
- frequency penalty: the more times a token appeared, the larger the penalty.
- presence penalty: a fixed penalty once a token has appeared at all, to push for new words.
**核心答案 (中):**
- 这几类 penalty 都用来减少重复：对**已经出现过**的 token 降低其打分。
- repetition penalty：只要出现过就压低它再次被选的概率。
- frequency penalty：出现**次数越多**，惩罚越大（按频次叠加）。
- presence penalty：出现过就扣一个固定量（不看次数），鼓励引入新词。
**追问 / 深入 (中):**
- 追问"penalty 太大有什么副作用？" → 过强会逼模型为了不重复而硬换词，导致跑题、用词奇怪、甚至语义不连贯，是个权衡。
- ⚠️待核实：具体公式、取值范围、默认值各平台不一致（如 OpenAI API 与 HuggingFace 的实现），落到具体平台以官方文档为准。
**常见误区 (中):**
- 把 frequency penalty 和 presence penalty 当成一回事；前者按**出现次数**叠加惩罚，后者只看**是否出现过**。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "At each step the model gives a probability distribution over the whole vocabulary. Decoding is how we pick the next token from it."
  (中) 每一步模型给出整个词表上的概率分布，解码就是怎么从里面挑下一个 token。
- (EN) "Greedy always picks the top token — deterministic but often dull. Beam search keeps several paths and is good for tasks with a clear answer like translation."
  (中) greedy 永远选最高的那个——确定但常单调。beam search 保留多条路径，适合翻译这种有标准答案的任务。
- (EN) "Temperature scales the logits: low temperature is focused, high temperature is diverse. It only changes sampling, not the weights."
  (中) temperature 缩放 logits：低温聚焦，高温多样。它只改采样，不动权重。
- (EN) "top-k keeps a fixed number of candidates; top-p keeps the smallest set whose cumulative probability hits p, so it adapts to the distribution."
  (中) top-k 留固定数量的候选；top-p 按累积概率到 p 为止，会自适应分布。
- (EN) "For deterministic tasks like code or extraction, use greedy or low temperature. For creative tasks, use moderate temperature with top-p."
  (中) 代码、抽取这类确定性任务用 greedy 或低温；创意任务用适度 temperature 加 top-p。

## 延伸阅读
- *The Curious Case of Neural Text Degeneration*（Holtzman et al., 2019）—— top-p / nucleus sampling 原论文，解释 beam search 为何在开放式生成里退化。
- *Hugging Face — How to generate text*（generation 策略博客/文档）—— greedy、beam、top-k、top-p 的图解与代码，⚠️待核实具体 API 参数以最新官方文档为准。
