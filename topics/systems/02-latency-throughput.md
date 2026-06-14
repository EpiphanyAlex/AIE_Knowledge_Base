---
topic: 延迟与吞吐优化
domain: systems
difficulty: 进阶
status: drafted
prerequisites: [serving-inference]
tags: [latency, throughput, TTFT, quantization, speculative-decoding, KV-cache]
---

# 延迟与吞吐优化

## 一句话概览
> LLM 上线后两个核心目标常常冲突：单个请求要**快**（latency 低）和整体要能**扛量**（throughput 高）。这篇聚焦怎么用指标衡量它们，以及 batching、quantization、speculative decoding、KV cache / prefix caching、PagedAttention 这几类手段怎么按 SLA 取舍。

## 概念讲解

**1. latency vs throughput：先分清两件事**
- **latency（延迟）**：一个请求从发出到拿到（部分）结果有多快，关心的是**单个用户的体验**。
- **throughput（吞吐）**：单位时间系统能处理多少（请求 / token），关心的是**整体处理能力和成本**。
- 它们常常对立：把很多请求攒成一个大 batch 一起算，GPU 利用率高、throughput 涨，但每个请求要等"凑批"，单个 latency 反而变长。优化的本质就是在这两者之间按业务需求找平衡。

**2. LLM 推理分两个阶段，延迟来源不同**
LLM 生成是自回归的（一个一个 token 往外蹦），整个过程分两段：
- **prefill（预填充）**：把用户输入的 prompt 一次性喂进去，算出所有输入 token 的 K、V 并产出第一个输出 token。这一步是**计算密集**（compute-bound），决定了第一个字多久出来。
- **decode（解码）**：之后每一步只算一个新 token，要反复读取已缓存的 K、V，是**显存带宽密集**（memory-bound）。这一步决定了后续每个字之间的间隔。

理解这个分段是理解所有延迟指标和优化手段的基础。

**3. 关键指标**
- **TTFT（Time To First Token，首 token 延迟）**：从请求到吐出第一个 token 的时间，主要由 prefill 决定，也包含排队 / 凑批等待。对话、流式输出场景，TTFT 直接决定"感觉快不快"。
- **TPOT（Time Per Output Token，每 token 延迟）/ inter-token latency（token 间延迟，ITL）**：生成阶段相邻两个 token 之间的平均间隔，由 decode 阶段决定。它决定了文字"流出来"的速度。
- **总延迟（end-to-end latency）**：粗略地 ≈ `TTFT + TPOT × 输出 token 数`。所以输出越长，TPOT 的影响越大。
- 上线时通常还看**尾延迟**（p95 / p99），平均值好看不代表用户都满意。

**4. 提升手段（按作用对象分类）**

*偏 throughput：*
- **batching（批处理）**：把多个请求合在一起送进 GPU，一次算多条，显著提高 GPU 利用率和 throughput。代价是单请求要等凑批。现代推理引擎多用 **continuous batching（连续批处理 / in-flight batching）**：不必等整批都生成完，谁结束就把谁换出、新请求随时插进来，比静态批更省资源。

*偏 latency + 省显存：*
- **quantization（量化）**：把权重 /（有时）激活从 FP16 降到 int8 甚至 int4，**显存占用更小、显存带宽压力更低**，decode 这种 memory-bound 阶段往往因此变快，也能在同样的卡上放下更大模型或更大 batch。代价是**精度损失**，量化越激进（int4 < int8）风险越大，需要评测确认质量没掉太多。
- **speculative decoding（投机 / 推测解码）**：用一个**小而快的草稿模型（draft model）**先一口气猜出若干个 token，再让**大模型一次性并行校验**：猜对的直接采纳，猜错的从分歧点重来。因为大模型一次能验证多个 token，平均每个 token 的开销下降，**降低 TPOT**，且**不改变最终输出分布**（数学上等价于大模型自己解码）。收益取决于草稿模型的"命中率"。

*偏复用 / 省重复计算：*
- **KV cache**：生成时把已经算过的每个 token 的 K、V 缓存下来，新 token 只需算自己的那一份，避免每步重算整个前缀。这是自回归生成几乎必备的优化，代价是 KV cache 会**占大量显存**，且随上下文长度和并发数线性增长。
- **prefix caching（前缀缓存）**：如果多个请求共享相同前缀（比如同一段长 system prompt、同一篇被反复提问的文档），把这段前缀的 KV 算一次并**跨请求复用**，省掉重复的 prefill，**显著降低 TTFT**。
- **PagedAttention**：把 KV cache 像操作系统管理内存那样**分页（page）管理**，按需分配小块而非给每个请求预留一整段连续显存。这样能**几乎消除显存碎片**、把显存用满，从而支持更大的 batch / 更高并发；它也是高效共享前缀 KV 的底层机制。⚠️待核实（出自 vLLM 的 PagedAttention 论文，具体性能数字以原文为准）。

**5. 怎么按 SLA 取舍**
没有"最优配置"，只有"匹配业务的配置"：
- **交互 / 对话类**（看重体感）：优先压低 **TTFT 和 TPOT** → 小 batch 或激进的 continuous batching、prefix caching、必要时量化；流式输出让首 token 尽快出来。
- **离线 / 批处理类**（看重成本和总量）：优先拉高 **throughput** → 大 batch、量化以塞更多请求，可以容忍较高的单请求 latency。
- 通用做法：先定 SLA（如 "p95 TTFT < 500ms"），再在满足约束的前提下尽量提 throughput / 降成本，并持续盯 p95 / p99 尾延迟。

> 与"推理服务（serving-inference）"主题的区别：那篇讲**怎么把模型部署成服务**（架构、引擎、扩缩容等）；本篇聚焦**衡量延迟/吞吐的指标和具体优化技术**。

## 面试问答卡

### Q1. What is the difference between latency and throughput in LLM serving? / LLM 服务里 latency 和 throughput 有什么区别？
**难度:** 基础
**Answer (EN):**
- Latency is how fast one request gets its result. It is about a single user's experience.
- Throughput is how many requests or tokens the system handles per unit time. It is about total capacity and cost.
- They often trade off: bigger batches raise throughput but make each request wait longer, so latency goes up.
**核心答案 (中):**
- latency 是单个请求多快拿到结果，关心**单个用户体验**。
- throughput 是单位时间能处理多少请求 / token，关心**整体能力和成本**。
- 二者常对立：batch 越大 throughput 越高，但单请求要等凑批，latency 变长。
**追问 / 深入 (中):**
- 追问"那到底优化哪个？" → 看 SLA：交互类压 latency，离线批处理类拉 throughput；通常是"先满足 latency 约束，再在约束内尽量提 throughput"。
**常见误区 (中):**
- 以为两者能同时无脑拉满；它们多数时候是权衡关系。
- 把高 throughput 当成低 latency 的同义词，其实可能正相反。

### Q2. What is TTFT and TPOT? How do they relate to total latency? / 什么是 TTFT 和 TPOT？它们和总延迟什么关系？
**难度:** 基础
**Answer (EN):**
- TTFT (Time To First Token) is the time until the first token comes out. It is driven by the prefill step plus any queue / batching wait.
- TPOT (Time Per Output Token), also called inter-token latency, is the average gap between later tokens, driven by the decode step.
- Total latency is roughly TTFT + TPOT × number of output tokens.
**核心答案 (中):**
- **TTFT** = 第一个 token 出来的时间，主要由 prefill 决定，还含排队 / 凑批等待。
- **TPOT**（即 inter-token latency）= 后续相邻 token 之间的平均间隔，由 decode 决定。
- 总延迟 ≈ **TTFT + TPOT × 输出 token 数**。
**追问 / 深入 (中):**
- 追问"流式输出为什么要看 TTFT？" → 流式下用户看到第一个字就觉得"开始响应了"，TTFT 直接决定体感快慢，哪怕总时长一样。
- 追问"为什么 prefill 和 decode 瓶颈不同？" → prefill 一次算整个 prompt，是 compute-bound；decode 每步只算一个 token 但反复读 KV，是 memory-bound。
**常见误区 (中):**
- 只盯平均延迟，忽略 p95 / p99 尾延迟。
- 以为输出越长 TTFT 越大；TTFT 基本只跟输入长度 + 等待有关，输出长度影响的是总延迟里的 TPOT 部分。

### Q3. How do batching and KV cache improve serving, and what do they cost? / batching 和 KV cache 怎么提升服务？代价是什么？
**难度:** 进阶
**Answer (EN):**
- Batching runs many requests together on the GPU, raising utilization and throughput. The cost is each request may wait to be batched, so latency can rise.
- Continuous batching swaps finished requests out and new ones in on the fly, instead of waiting for a whole batch, so it wastes less.
- KV cache stores the K and V of past tokens so each new token is not recomputed from scratch. The cost is large GPU memory that grows with context length and concurrency.
**核心答案 (中):**
- **batching**：多个请求一起算，提升 GPU 利用率和 throughput；代价是单请求要等凑批，latency 可能上升。
- **continuous batching**：谁算完就换出、新请求随时插入，不必等整批，更省资源。
- **KV cache**：缓存历史 token 的 K、V，新 token 不必重算整个前缀；代价是**占大量显存**，随上下文长度和并发线性增长。
**追问 / 深入 (中):**
- 追问"KV cache 省的是哪部分计算？" → 省的是 decode 阶段对前缀 K、V 的重复计算，是推理时优化，不改训练。
- 追问"显存不够放 KV 怎么办？" → 量化 KV、PagedAttention 减碎片、或限制最大上下文 / 并发。
**常见误区 (中):**
- 以为 batch 越大永远越好；batch 太大会拉高单请求 latency，也可能爆显存。
- 把 KV cache 当成省显存的手段；它是省**计算**的，反而**额外吃显存**。

### Q4. What is speculative decoding and why does it help? / 什么是 speculative decoding？为什么有用？
**难度:** 进阶
**Answer (EN):**
- A small, fast draft model first guesses several tokens ahead.
- The big model then verifies all of them in one parallel pass: accepted guesses are kept, the first wrong one is corrected and generation continues from there.
- Because the big model checks many tokens at once, the average cost per token drops, so TPOT goes down — and the final output distribution is unchanged.
**核心答案 (中):**
- 小而快的**草稿模型**先一次猜出若干 token。
- 大模型**一次并行校验**这些 token：猜对的采纳，从第一个猜错处纠正并继续。
- 大模型一次能验证多个 token，平均每 token 开销下降，**降低 TPOT**；且**不改变最终输出分布**。
**追问 / 深入 (中):**
- 追问"收益靠什么？" → 靠草稿模型的命中率：草稿越接近大模型、猜得越准，被采纳的 token 越多，加速越明显；猜得差则收益有限甚至倒亏。
- 追问"会不会改变结果质量？" → 校验机制保证等价于大模型自己解码（采纳/拒绝规则做了概率上的修正），所以**质量不变**，省的是时间。
**常见误区 (中):**
- 以为是"用小模型替大模型回答"，质量会降；其实大模型仍负责最终校验，质量不变。
- 以为一定提速；命中率低时几乎没收益。

### Q5. How does quantization help latency and memory, and what is the trade-off? / quantization 怎么帮到延迟和显存？有什么权衡？
**难度:** 进阶
**Answer (EN):**
- Quantization stores weights (and sometimes activations) in lower precision, like int8 or int4, instead of FP16.
- This uses less GPU memory and lowers memory bandwidth pressure, so the memory-bound decode step often gets faster, and you can fit a bigger model or a bigger batch on the same GPU.
- The trade-off is accuracy loss: more aggressive quantization (int4 vs int8) carries more risk, so you must evaluate quality.
**核心答案 (中):**
- quantization 把权重（有时含激活）从 FP16 降到 int8 / int4。
- 显存更省、显存带宽压力更低，memory-bound 的 decode 常因此变快，同卡能放更大模型或更大 batch。
- 权衡是**精度损失**：量化越激进（int4 比 int8）风险越大，必须评测确认质量。
**追问 / 深入 (中):**
- 追问"为什么省显存还能变快？" → decode 阶段瓶颈是从显存搬权重 / KV，数据更小搬得更快；不是因为算得少。
- 追问"怎么尽量少掉精度？" → 用更成熟的量化方案、对敏感层保留高精度、量化后跑评测对比；具体方案 ⚠️待核实（随工具版本演进）。
**常见误区 (中):**
- 以为量化一定明显提速；在 compute-bound 的 prefill 上提速可能不明显，主要利好 memory-bound 阶段。
- 以为精度无损；总有损失，关键是能不能控制在可接受范围。

### Q6. You are given an SLA. How do you tune the system for latency vs throughput? / 给定一个 SLA，你怎么在 latency 和 throughput 之间调？
**难度:** 高阶
**Answer (EN):**
- First nail down the SLA, e.g. "p95 TTFT under 500 ms". Tail latency (p95 / p99) matters more than the average.
- For interactive / chat: push TTFT and TPOT down — smaller or continuous batching, prefix caching for shared prompts, maybe quantization; stream the output.
- For offline / batch: push throughput up — large batches and quantization to pack more requests, accepting higher per-request latency.
- General rule: meet the latency constraint first, then maximize throughput / cut cost within that constraint, and keep watching p95 / p99.
**核心答案 (中):**
- 先定 SLA（如 "p95 TTFT < 500ms"），盯**尾延迟 p95 / p99**，别只看平均。
- **交互 / 对话类**：压 TTFT、TPOT → 小 batch 或 continuous batching、prefix caching 复用共享前缀、必要时量化；流式输出。
- **离线 / 批处理类**：拉 throughput → 大 batch + 量化塞更多请求，容忍较高单请求 latency。
- 通则：先满足 latency 约束，再在约束内尽量提 throughput / 降成本，持续监控尾延迟。
**追问 / 深入 (中):**
- 追问"长 system prompt 被反复用，怎么优化？" → 上 prefix caching，把这段前缀 KV 算一次跨请求复用，直接砍 TTFT。
- 追问"并发上来显存不够？" → PagedAttention 减碎片把显存用满、量化 KV、限制最大上下文 / 并发，或加卡。
**常见误区 (中):**
- 上来就追求"最优配置"；其实只有匹配业务 SLA 的配置，没有放之四海皆准的最优。
- 只优化平均延迟，忽略尾延迟导致部分用户体验很差。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "Latency is how fast one request is; throughput is how many requests the system handles. They often trade off."
  (中) latency 是单请求多快，throughput 是系统能处理多少，二者常常权衡。
- (EN) "TTFT is time to first token, set by prefill and queueing. TPOT is the gap between later tokens, set by decode. Total latency is roughly TTFT plus TPOT times output length."
  (中) TTFT 是首 token 时间，由 prefill 和排队决定；TPOT 是后续 token 间隔，由 decode 决定；总延迟约等于 TTFT 加上 TPOT 乘输出长度。
- (EN) "Batching raises throughput but adds wait. KV cache avoids recomputing past tokens but eats memory."
  (中) batching 提吞吐但增加等待；KV cache 省重复计算但吃显存。
- (EN) "Speculative decoding uses a small draft model to guess tokens and the big model to verify them in parallel, lowering TPOT without changing the output."
  (中) speculative decoding 用小草稿模型猜 token、大模型并行校验，降低 TPOT 又不改输出。
- (EN) "Quantization uses int8 or int4 to save memory and speed up the memory-bound decode step, at the cost of some accuracy."
  (中) quantization 用 int8 / int4 省显存、加速 memory-bound 的 decode，代价是一点精度。
- (EN) "Prefix caching reuses the KV of a shared prompt across requests to cut TTFT; PagedAttention pages the KV cache to kill memory fragmentation and allow bigger batches."
  (中) prefix caching 跨请求复用共享前缀的 KV，砍 TTFT；PagedAttention 把 KV 分页管理，消除显存碎片、支持更大 batch。
- (EN) "There is no best config — pick the one that meets your SLA: latency first for chat, throughput first for batch jobs."
  (中) 没有最优配置，只有满足 SLA 的配置：对话优先 latency，批处理优先 throughput。

## 延伸阅读
- *Efficient Memory Management for Large Language Model Serving with PagedAttention*（Kwon et al., 2023，vLLM 论文）—— PagedAttention 与 KV 分页管理。⚠️待核实（具体数字以原文为准）
- *Fast Inference from Transformers via Speculative Decoding*（Leviathan et al., 2023）—— speculative decoding 原理与等价性证明。⚠️待核实
- vLLM / TensorRT-LLM 官方文档 —— continuous batching、prefix caching、量化等工程实现（随版本更新，⚠️待核实具体配置与数字）。
