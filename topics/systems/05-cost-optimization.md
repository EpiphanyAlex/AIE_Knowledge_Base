---
topic: 成本优化
domain: systems
difficulty: 基础
status: drafted
prerequisites: []
tags: [cost, token-cost, model-routing, caching, prompt-compression]
---

# 成本优化

## 一句话概览
> LLM 应用按 token 计费，成本 = 调用量 × 每次的 token 数 × 单价；成本优化就是在保证质量的前提下，用更便宜的模型、更短的 prompt、缓存与批处理把这三项压下去。

## 概念讲解

**1. 成本从哪来**
大多数 LLM API 按 **token** 收费，而且 **input token 和 output token 分开计价**（通常 output 更贵）。一次调用的成本大致是：

```
单次成本 ≈ input_tokens × 单价_in + output_tokens × 单价_out
总成本   ≈ 单次成本 × 调用量(QPS / 日请求数)
```

影响成本的几个旋钮：
- **模型大小 / 档位**：越大越强的模型单价越高（大模型 vs 小模型可以差一个数量级）。
- **input token**：prompt 本身长度，包括 system prompt、few-shot 例子、检索回来的 context（RAG 里 context 往往是大头）。
- **output token**：生成多长，直接影响费用，而且生成是逐 token 的，也最影响延迟。
- **调用量**：有多少请求、是否重复、有没有失败重试放大。

> ⚠️待核实：各家具体单价、大小模型差几倍、input/output 价差倍数，随厂商和时间变化很快，请以官方定价页为准（截至 2026-06 不写死具体数字）。

**2. 优化手段总览（从最划算到更重的工程）**

**(a) 模型选择 + model routing（性价比最高）**
不是所有请求都需要最强模型。做个"路由器"：
- 简单任务（分类、抽取、格式化、闲聊）→ 用小 / 便宜模型。
- 难任务（复杂推理、长文综合、代码）→ 才上大模型。
- 路由可以靠规则（按任务类型 / 输入长度）或一个轻量分类器来判断难度。
直觉类比：不是每封邮件都要请律师，简单的自己回就行。

**(b) caching（缓存，复用结果）**
- **精确缓存**：同样的请求直接返回上次结果（key = prompt 的 hash）。
- **语义缓存 / semantic cache**：把请求做 embedding，新请求和历史请求**语义相似**就复用答案（如 "法国首都是？" 和 "法国的首都叫什么？"）。
- **prompt caching（厂商提供）**：缓存 prompt 里固定不变的前缀（如长 system prompt、固定的 few-shot），命中时这部分 input token 更便宜。⚠️待核实：是否支持、折扣多少各家不同。

**(c) batching（批处理）**
把多个请求合并成一批发出去。很多厂商提供异步 **batch API**，对不要求实时的任务（离线打标、批量摘要）给折扣；自己 self-host 时，批处理还能提高 GPU 利用率、摊薄成本。代价是延迟变高，适合离线场景。

**(d) 缩短 prompt / prompt compression**
- 去掉啰嗦的指令、重复的例子、用不到的 context。
- few-shot 例子能少则少（够用就行，甚至 zero-shot）。
- RAG 里只放最相关的 chunk，别把检索结果一股脑全塞进去。
- 必要时用 prompt 压缩技术（如重写 / 蒸馏成更短的提示）。

**(e) 控制 output 长度**
- 设 `max_tokens` 上限，要求模型简短回答（"answer in one sentence"）。
- 让输出结构化（JSON / 固定字段），避免模型写一大段废话。
- output 既贵又慢，是很容易忽视的省钱点。

**(f) 用小模型 fine-tune 替代大模型 prompt**
如果某个任务量很大、模式固定，可以用大模型的输出造数据，去 **fine-tune 一个小模型**：之后用小模型就能达到接近的效果，但单价低很多、prompt 也更短（不用塞一堆例子）。前提是任务稳定、量足够大，能摊平 fine-tune 的一次性成本。

**(g) self-host vs API 的成本权衡**
- **API**：按用量付费，零运维，量小或波动大时更划算；省心。
- **self-host（自己部署开源模型）**：要买 / 租 GPU、自己做运维和扩缩容，是**固定成本**；只有在量足够大、利用率够高时，平摊下来才比 API 便宜。
- 经验法则：先用 API 验证产品，等用量大且稳定、或有数据隐私 / 定制需求时，再评估 self-host。

**(h) 监控 token 用量（前提中的前提）**
- 没有度量就没法优化：记录每个请求 / 每个功能 / 每个用户的 input/output token 和花费。
- 设预算告警、找出"成本大户"（哪个 endpoint、哪个 prompt 最烧钱）。
- 上线任何优化后，对比前后成本看是否真省了。

## 面试问答卡

### Q1. What drives the cost of an LLM application? / LLM 应用的成本主要由什么决定？
**难度:** 基础
**Answer (EN):**
- Most APIs charge per token, and input tokens and output tokens are priced separately (output is usually more expensive).
- Single-call cost ≈ input_tokens × input_price + output_tokens × output_price.
- Total cost ≈ single-call cost × number of calls.
- Bigger / stronger models cost more per token.
**核心答案 (中):**
- 大多数 API 按 token 计费，input 和 output **分开计价**（output 通常更贵）。
- 单次成本 ≈ input token × 单价 + output token × 单价。
- 总成本 ≈ 单次成本 × 调用量。
- 模型越大越强，单价越高。
**追问 / 深入 (中):**
- 追问"RAG 应用成本大头通常在哪？" → 往往在 input：检索回来的 context 会让 prompt 很长，token 数飙升。
**常见误区 (中):**
- 以为只按调用次数收费；其实主要看 token 数，长 prompt / 长输出比次数更影响账单。
- 忘了 output 通常比 input 单价更贵。

### Q2. How would you cut LLM cost without hurting quality much? / 怎么在不太影响质量的前提下降低 LLM 成本？
**难度:** 基础
**Answer (EN):**
- Use model routing: small / cheap model for easy tasks, big model only for hard ones.
- Shorten the prompt: drop useless context and extra few-shot examples.
- Limit output length with max_tokens and ask for short answers.
- Cache results so repeated or similar requests don't hit the model again.
**核心答案 (中):**
- model routing：简单任务用小 / 便宜模型，难任务才上大模型。
- 缩短 prompt：去掉没用的 context 和多余的 few-shot 例子。
- 用 max_tokens 限制输出、要求简短回答。
- 加 caching：重复或相似的请求别再调模型。
**追问 / 深入 (中):**
- 追问"先做哪个？" → 一般先 model routing 和 caching，性价比最高、改动小；prompt 瘦身和 fine-tune 是后续。
**常见误区 (中):**
- 一上来就想 self-host 省钱；量不够大时反而更贵，应先用便宜的优化。
- 只盯着省钱忽略质量；要用评测对比优化前后的效果。

### Q3. What is model routing and when do you use it? / 什么是 model routing？什么时候用？
**难度:** 进阶
**Answer (EN):**
- Model routing means picking which model handles a request based on how hard it is.
- Easy tasks (classification, extraction, simple chat) go to a small / cheap model; hard tasks (complex reasoning, code, long synthesis) go to a big model.
- You can route by simple rules (task type, input length) or by a light classifier that scores difficulty.
- It saves money because most traffic is easy and doesn't need the strongest model.
**核心答案 (中):**
- model routing 就是按请求难度选用哪个模型。
- 简单任务（分类、抽取、简单对话）走小 / 便宜模型；难任务（复杂推理、代码、长文综合）走大模型。
- 路由可以用规则（任务类型、输入长度）或一个轻量分类器打难度分。
- 省钱是因为大部分流量都是简单的，不需要最强模型。
**追问 / 深入 (中):**
- 追问"路由判断错了怎么办？" → 可设兜底：小模型不确定（如置信度低 / 自评不会）就升级到大模型，叫 cascade / fallback。
**常见误区 (中):**
- 以为路由器本身很贵；它通常是规则或很小的模型，开销远小于省下的钱。
- 把 routing 和 multi-agent 混淆；routing 是"选一个模型"，不是让多个模型协作。

### Q4. What is semantic caching and how is it different from exact caching? / 什么是语义缓存？和精确缓存有什么不同？
**难度:** 进阶
**Answer (EN):**
- Exact cache reuses the answer only when the new request is byte-for-byte the same (key = hash of the prompt).
- Semantic cache embeds the request and reuses a past answer when a new one is semantically similar, even if the wording differs.
- Example: "capital of France?" and "what's France's capital?" can share one cached answer.
- It raises hit rate and saves more calls, but you must set a similarity threshold to avoid wrong reuse.
**核心答案 (中):**
- 精确缓存只有当新请求**完全一样**时才复用（key = prompt 的 hash）。
- 语义缓存把请求做 embedding，**语义相似**就复用，即使措辞不同。
- 例子："法国首都是？" 和 "法国的首都叫什么？" 可以共用一个缓存答案。
- 命中率更高、省更多调用，但要设相似度阈值，避免复用错答案。
**追问 / 深入 (中):**
- 追问"语义缓存有什么风险？" → 阈值太松会把不该复用的也复用了（答非所问）；对时效性强、个性化的请求要慎用甚至关掉缓存。
**常见误区 (中):**
- 以为缓存对所有场景都安全；带用户个人信息、强时效或随机性要求高的请求不适合缓存。

### Q5. When should you fine-tune a small model instead of prompting a big one? / 什么时候该 fine-tune 小模型，而不是给大模型写 prompt？
**难度:** 进阶
**Answer (EN):**
- When one task has high volume and a stable, repeated pattern.
- Fine-tune a small model on examples (often generated by a big model), then serve the small model.
- It lowers per-call price and shortens prompts (no need to stuff many few-shot examples).
- It pays off only if volume is large enough to cover the one-time fine-tuning cost.
**核心答案 (中):**
- 当某个任务**量大且模式固定、重复**时。
- 用例子（常由大模型生成）fine-tune 一个小模型，之后用小模型来服务。
- 单价更低、prompt 更短（不用塞一堆 few-shot 例子）。
- 只有量足够大、能摊平 fine-tune 的一次性成本时才划算。
**追问 / 深入 (中):**
- 追问"任务还会变怎么办？" → 任务定义不稳定时别急着 fine-tune，改一次就要重训；先用 prompt + routing 更灵活。
**常见误区 (中):**
- 以为 fine-tune 一定更省；前期数据 + 训练 + 维护是成本，量小时不如直接调 API。
- 把 fine-tune 当成提升知识的手段；它更适合固定格式 / 风格 / 任务，不是往模型里灌新事实。

### Q6. API vs self-hosting: how do you decide on cost? / 用 API 还是自己部署（self-host）？成本上怎么权衡？
**难度:** 高阶
**Answer (EN):**
- API is pay-per-use with zero ops; cheaper when volume is small or spiky, and fastest to start.
- Self-hosting an open model is a fixed cost (GPU + ops + scaling); cheaper only at large, steady volume with high utilization.
- Rule of thumb: start with API to validate the product, move to self-host when volume is large and stable, or when you need data privacy / customization.
- Always measure real token usage first, then compare total cost of both options.
**核心答案 (中):**
- API 按用量付费、零运维；量小或波动大时更便宜，启动也最快。
- self-host 开源模型是**固定成本**（GPU + 运维 + 扩缩容）；只有量大、稳定、利用率高时才更便宜。
- 经验法则：先用 API 验证产品，等量大且稳定、或有数据隐私 / 定制需求时再转 self-host。
- 先量出真实 token 用量，再算两种方案的总成本对比。
**追问 / 深入 (中):**
- 追问"self-host 容易被忽略的成本？" → GPU 闲置（利用率低）、运维 / 扩缩容人力、模型升级维护，这些都摊进总成本。
**常见误区 (中):**
- 只比"每 token 单价"就下结论；要算上固定成本和利用率，低利用率的自建往往比 API 还贵。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "LLM cost is roughly calls times tokens times price, and input and output tokens are priced separately."
  (中) LLM 成本大致是 调用量 × token 数 × 单价，而且 input 和 output 分开计价。
- (EN) "The biggest win is usually model routing: small cheap model for easy tasks, big model only for hard ones."
  (中) 最划算的通常是 model routing：简单任务用小而便宜的模型，难任务才上大模型。
- (EN) "Caching helps a lot — exact cache for identical requests, semantic cache for similar ones."
  (中) 缓存很有用——精确缓存处理完全相同的请求，语义缓存处理相似的请求。
- (EN) "Shorten the prompt and cap the output length, since both input and output tokens cost money."
  (中) 缩短 prompt、限制输出长度，因为 input 和 output token 都要花钱。
- (EN) "For high-volume stable tasks, fine-tuning a small model can beat prompting a big one."
  (中) 对量大又稳定的任务，fine-tune 一个小模型可能比给大模型写 prompt 更省。
- (EN) "Start with an API; only self-host when volume is large and steady. And always monitor token usage first."
  (中) 先用 API；只有量大又稳定时才自建。而且一定要先监控 token 用量。

## 延伸阅读
- 各厂商官方定价页（OpenAI / Anthropic / Google 等）—— 具体单价、batch / prompt caching 折扣，以官方为准（⚠️待核实，价格随时间变化）。
- *GPTCache*（开源语义缓存库）—— semantic cache 的常见实现参考。
- 各厂商 "prompt caching" / "batch API" 官方文档 —— input 缓存折扣与异步批处理用法（⚠️待核实，支持情况各家不同）。
