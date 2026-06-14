---
topic: 推理服务与部署
domain: systems
difficulty: 进阶
status: drafted
prerequisites: [attention]
tags: [serving, inference, vLLM, batching, KV-cache, deployment]
---

# 推理服务与部署

## 一句话概览
> 把训练好的 LLM 变成一个能被反复调用、又快又省钱的在线服务，核心是理解推理的两阶段（prefill / decode）特性，再用 KV cache、continuous batching、合适的并行和硬件去压成本、提吞吐。

## 概念讲解

**1. 什么是推理服务（serving / inference）**
训练只做一次，推理（inference）是模型上线后**每来一个请求就跑一次**的过程。serving 就是把模型包成一个常驻服务（通常是 HTTP / gRPC API），接收 prompt、返回生成结果。和训练不同，推理的目标是：
- **低延迟（latency）**：用户等得越短越好，尤其首字延迟。
- **高吞吐（throughput）**：单位时间、单张卡能服务越多 token / 越多请求越好（直接决定成本）。
- 这两者常常互相拉扯，serving 的工程就是在它们之间找平衡。

**2. 推理两阶段：prefill vs decode**
自回归 LLM 生成时分两个阶段，计算特性**完全不同**：

- **Prefill（预填充）**：把整段 prompt 一次性喂进去，**并行**算出所有输入 token 的表示，并填好它们的 KV cache。
  - 一次处理很多 token → 计算密集（compute-bound），能把 GPU 算力吃满。
- **Decode（解码 / 逐字生成）**：之后**一次只生成一个** token，每生成一个就把它喂回去再生成下一个。
  - 每步只处理 1 个新 token，但要读取前面所有 token 的 KV cache → **访存密集（memory-bandwidth-bound）**，算力反而吃不满。

一个直觉对比：prefill 像"一口气读完整道题"，decode 像"一个字一个字往外蹦"。decode 阶段卡在显存带宽上，所以很多优化（batching、KV cache 管理）都是为了让 decode 更高效。

**3. KV cache 在推理里的作用**
self-attention 里每个 token 都要用前面所有 token 的 Key 和 Value。如果不缓存，每生成一个新 token 就要把前面所有 token 的 K、V **重算一遍**，复杂度爆炸。
- **KV cache** 就是把已经算过的每个 token 的 K、V 存下来，生成新 token 时直接复用，只算新 token 自己的 Q、K、V。
- 代价：KV cache **占显存**，且**随序列长度、batch 大小线性增长**。长上下文 + 大 batch 时，KV cache 往往比模型权重还吃显存，是 serving 的主要显存瓶颈。

**4. Batching：static / dynamic / continuous**
GPU 擅长并行，把多个请求**合并成一个 batch** 一起算，能大幅提吞吐。三种做法：

- **Static batching（静态批）**：凑够固定数量的请求才一起跑，整批一起开始、一起结束。
  - 问题：每个请求生成长度不同，**短的要等长的**，先算完的位置空转，GPU 利用率低、尾延迟高。
- **Dynamic batching（动态批）**：在很短的时间窗口里把陆续到达的请求凑成一批再跑（常见于传统模型 serving）。
  - 缓解了"等够请求"的问题，但**一旦开跑，整批还是要一起结束**，仍有短等长的浪费。
- **Continuous batching（连续批 / in-flight batching）**：**以"步"为粒度调度**——每生成一步后，已经生成完（出 EOS）的请求立刻离开 batch，新到的请求随时插进来填空位。
  - 直觉：GPU 的每一步都尽量塞满活跃请求，不让任何完成的请求拖住整批 → 吞吐显著提升，是现代 LLM 推理引擎的关键技术。

**5. 推理引擎（inference engine）**
不用自己从零造轮子，业界有专门的推理引擎，封装了上面这些优化。常见角色：
- **vLLM**：开源推理引擎，以 **PagedAttention**（像操作系统分页一样管理 KV cache 显存，减少碎片）和 continuous batching 著称，主打高吞吐。⚠️待核实（具体版本号与最新特性请以官方为准，截至 2026-06）。
- **TGI（Text Generation Inference）**：Hugging Face 出的推理服务框架，方便部署 HF 模型，支持 continuous batching 等。⚠️待核实（版本/特性，截至 2026-06）。
- **TensorRT-LLM**：NVIDIA 的推理优化库，把模型编译成高度优化的 GPU kernel，在 NVIDIA 硬件上追求极致延迟/吞吐。⚠️待核实（版本/特性，截至 2026-06）。

> 它们的共同角色：在一张/多张 GPU 上，用 batching + KV cache 管理 + 优化 kernel，把模型跑得又快又省。选型时按"是否要极致性能 / 是否绑定 NVIDIA / 易用性 / 生态"权衡。

**6. Model parallelism：tensor vs pipeline**
当模型**大到一张 GPU 放不下**（权重 + KV cache 超出单卡显存），就要把模型拆到多张卡上：
- **Tensor parallelism（张量并行）**：把**单层内部**的大矩阵按维度切开，分到多张卡，每张卡算一部分再合并。
  - 通信频繁、对带宽要求高，通常用在**同一台机器内**用高速互联（如 NVLink）连接的多卡。
- **Pipeline parallelism（流水线并行）**：把模型**按层切段**，不同卡负责不同层，数据像流水线一样依次流过。
  - 通信少，可**跨机器**，但有"流水线气泡"（开头结尾阶段有卡空闲）。

什么时候需要：**模型单卡放不下**时才需要并行；放得下就别拆（拆了有通信开销）。常见做法是先用 tensor parallelism 占满单机多卡，不够再叠 pipeline parallelism 跨机。

**7. 部署形态与硬件直觉**
- **托管 API vs 自托管（self-hosting）**：
  - **API**（调用别人的服务）：上手快、不用管 GPU、按量付费；但有数据出域、定制受限、长期高用量可能更贵的顾虑。
  - **自托管**：数据可控、可深度定制、规模大时单位成本可能更低；但要自己搞 GPU、运维、扩缩容。
- **GPU 选型直觉**：
  - **显存够装下"模型权重 + KV cache"是硬门槛**，先看显存够不够，再看算力。
  - 高吞吐离线批处理更看算力和显存带宽；低延迟在线服务还要看单请求响应。
  - 具体型号、显存大小、价格变化快 → ⚠️待核实（按当前可用硬件和官方规格核对，截至 2026-06）。

## 面试问答卡

### Q1. What does it mean to "serve" an LLM, and how is inference different from training? / 什么叫"serve"一个 LLM？推理和训练有什么不同？
**难度:** 基础
**Answer (EN):**
- Serving means wrapping a trained model as a live service (usually an API) that handles many requests.
- Training runs once; inference runs every time a user sends a prompt.
- For serving we care about two things: low latency (fast response) and high throughput (more tokens per GPU, which drives cost).
**核心答案 (中):**
- serving 就是把训练好的模型包成一个常驻服务（通常是 API），处理大量请求。
- 训练只做一次；inference 是每来一个请求就跑一次。
- serving 关心两件事：低 latency（响应快）和高 throughput（每张卡出更多 token，决定成本）。
**追问 / 深入 (中):**
- 追问"latency 和 throughput 为什么会冲突？" → 加大 batch 能提吞吐，但请求要凑批、排队，单个请求的延迟可能变高；serving 就是在二者间权衡。
**常见误区 (中):**
- 把 serving 当成"再训练一遍"；serving 不更新权重，只做前向推理。

### Q2. What are the prefill and decode phases in LLM inference, and why do they behave differently? / LLM 推理里的 prefill 和 decode 是什么？为什么计算特性不同？
**难度:** 进阶
**Answer (EN):**
- Prefill: the whole prompt is processed in parallel in one pass; it is compute-bound and uses the GPU well.
- Decode: tokens are generated one at a time, each step reads all past KV cache; it is memory-bandwidth-bound.
- So prefill is heavy on compute, while decode is limited by memory bandwidth, not raw compute.
**核心答案 (中):**
- prefill：整段 prompt 一次并行处理；计算密集（compute-bound），能吃满 GPU 算力。
- decode：一次生成一个 token，每步都要读全部历史 KV cache；访存密集（memory-bandwidth-bound）。
- 所以 prefill 吃算力，decode 卡在显存带宽上，而不是算力。
**追问 / 深入 (中):**
- 追问"为什么 decode 算力吃不满？" → 每步只算 1 个新 token 的运算量很小，但要搬运大量 KV cache，瓶颈在带宽不在算力。
- 追问"这对优化有什么启示？" → decode 是逐字生成的主战场，所以 batching、KV cache 管理主要在优化 decode。
**常见误区 (中):**
- 以为 prefill 和 decode 用的是不同模型；是同一个模型的两个阶段。
- 以为生成慢是因为算力不够；decode 慢主要是访存瓶颈。

### Q3. What is the KV cache and why is it important for inference? / 什么是 KV cache？为什么它对推理很重要？
**难度:** 进阶
**Answer (EN):**
- In attention, each new token needs the Key and Value of all earlier tokens.
- KV cache stores those Keys and Values so we don't recompute them every step.
- It makes decode much faster, but it takes GPU memory that grows with sequence length and batch size.
**核心答案 (中):**
- attention 里每个新 token 都要用到前面所有 token 的 Key 和 Value。
- KV cache 把这些 K、V 存下来，避免每一步重算。
- 它让 decode 快很多，但占显存，且随序列长度和 batch 大小增长。
**追问 / 深入 (中):**
- 追问"KV cache 大到什么程度？" → 长上下文 + 大 batch 时它常常比模型权重还吃显存，是 serving 的主要显存瓶颈。
- 追问"怎么省 KV cache 显存？" → 例如分页管理（PagedAttention）减少碎片、量化 KV、共享 KV（如 GQA/MQA）等思路。
**常见误区 (中):**
- 以为 KV cache 缓存的是输出文本；它缓存的是每个 token 的 Key / Value 向量。
- 以为它是训练时的优化；它主要省的是**推理**时的重复计算。

### Q4. Compare static, dynamic, and continuous batching. Why does continuous batching boost throughput? / 对比 static、dynamic、continuous batching；为什么 continuous batching 能提吞吐？
**难度:** 进阶
**Answer (EN):**
- Static batching waits for a fixed batch, then runs it all together — short requests must wait for long ones.
- Dynamic batching groups requests in a short time window, but once started the batch still finishes together.
- Continuous batching schedules per step: finished requests leave immediately and new ones join, so the GPU stays full each step — that is why throughput goes up.
**核心答案 (中):**
- static batching：凑满固定批再一起跑，短请求要等长请求，GPU 空转。
- dynamic batching：短时间窗口内凑批，但开跑后整批还是一起结束，仍有浪费。
- continuous batching：以"步"为粒度调度，生成完的请求立刻走、新请求随时插进来，每步都尽量塞满 GPU → 所以吞吐显著提升。
**追问 / 深入 (中):**
- 追问"continuous batching 还有别的好名字吗？" → 也叫 in-flight batching，强调请求在飞行中被动态加入/移出 batch。
- 追问"它会牺牲什么？" → 调度更复杂，且需要灵活的 KV cache 显存管理来支持请求随时进出。
**常见误区 (中):**
- 把 continuous batching 当成"batch 更大"；关键不是更大，而是**调度粒度更细**、不让完成的请求拖住整批。

### Q5. What roles do vLLM, TGI, and TensorRT-LLM play in serving? / vLLM、TGI、TensorRT-LLM 在推理服务里各扮演什么角色？
**难度:** 进阶
**Answer (EN):**
- They are inference engines that handle batching, KV cache management, and optimized GPU kernels for you.
- vLLM: open-source, known for PagedAttention and continuous batching, focused on high throughput.
- TGI: Hugging Face's serving framework, easy to deploy HF models. TensorRT-LLM: NVIDIA's library that compiles models into highly optimized GPU kernels.
- (Exact versions and newest features should be checked against official docs.)
**核心答案 (中):**
- 它们都是推理引擎，替你封装 batching、KV cache 管理、优化 GPU kernel。
- vLLM：开源，以 PagedAttention（分页管理 KV cache 显存）和 continuous batching 著称，主打高吞吐。
- TGI：Hugging Face 的 serving 框架，方便部署 HF 模型；TensorRT-LLM：NVIDIA 的库，把模型编译成高度优化的 GPU kernel。
- （⚠️待核实：具体版本号与最新特性以官方为准，截至 2026-06。）
**追问 / 深入 (中):**
- 追问"怎么选？" → 要极致性能且在 NVIDIA 卡上偏向 TensorRT-LLM；要开源、高吞吐、社区活跃偏向 vLLM；要快速部署 HF 模型可看 TGI。按性能 / 硬件绑定 / 易用性 / 生态权衡。
**常见误区 (中):**
- 把推理引擎当成模型本身；它们是"跑模型的运行时"，模型权重还是另外加载的。
- 背诵具体版本号或性能数字 → 这些变化快，面试宁可说"按官方最新为准"也别编（⚠️待核实）。

### Q6. When do you need tensor or pipeline parallelism, and how do they differ? / 什么时候需要 tensor / pipeline parallelism？两者有什么区别？
**难度:** 高阶
**Answer (EN):**
- You need model parallelism when the model (weights plus KV cache) does not fit on a single GPU.
- Tensor parallelism splits the big matrices inside a layer across GPUs; it talks a lot, so it is usually within one machine with fast links (e.g. NVLink).
- Pipeline parallelism splits the model by layers across GPUs; it talks less and can span machines, but has pipeline bubbles (some GPUs idle at the start and end).
**核心答案 (中):**
- 当模型（权重 + KV cache）单卡放不下时，才需要 model parallelism。
- tensor parallelism：把单层内部的大矩阵切到多卡；通信频繁，通常用在单机内用高速互联（NVLink）的多卡。
- pipeline parallelism：把模型按层切段分到多卡；通信少、可跨机，但有流水线气泡（首尾阶段部分卡空闲）。
**追问 / 深入 (中):**
- 追问"两者能一起用吗？" → 能。常见先用 tensor parallelism 占满单机多卡，不够再叠 pipeline parallelism 跨机。
- 追问"放得下还要拆吗？" → 不要。并行有通信开销，单卡能装就别拆。
**常见误区 (中):**
- 把 model parallelism 和 data parallelism 混了：data parallelism 是每张卡放完整模型、分摊不同数据（训练常用）；model parallelism 是把一个模型拆到多卡（单卡装不下时用）。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "Serving means running the model as a live API. We balance two goals: low latency and high throughput, and throughput drives cost."
  (中) serving 就是把模型跑成在线 API。我们平衡两个目标：低 latency 和高 throughput，吞吐决定成本。
- (EN) "Inference has two phases. Prefill processes the whole prompt in parallel and is compute-bound. Decode generates one token at a time and is memory-bandwidth-bound."
  (中) 推理分两阶段。prefill 并行处理整段 prompt，是 compute-bound；decode 一次生成一个 token，是访存带宽 bound。
- (EN) "KV cache stores the Keys and Values of past tokens so we don't recompute them. It is fast but eats GPU memory that grows with length and batch size."
  (中) KV cache 存下历史 token 的 Key 和 Value，避免重算。它快，但占显存，且随长度和 batch 增长。
- (EN) "Continuous batching schedules per step: finished requests leave and new ones join, so the GPU stays full. That is the big throughput win."
  (中) continuous batching 以"步"为粒度调度：完成的请求离开、新的加入，让 GPU 一直满载，这就是吞吐提升的关键。
- (EN) "Engines like vLLM, TGI, and TensorRT-LLM package these tricks for us. I'd check official docs for exact versions and features."
  (中) vLLM、TGI、TensorRT-LLM 这类引擎替我们封装了这些技巧。具体版本和特性我会查官方文档。
- (EN) "We use model parallelism only when the model doesn't fit on one GPU. Tensor parallelism splits inside a layer within a machine; pipeline parallelism splits by layers across machines."
  (中) 只有单卡放不下时才用 model parallelism。tensor parallelism 在机器内切单层；pipeline parallelism 按层跨机切。

## 延伸阅读
- vLLM 官方文档 / PagedAttention 论文（*Efficient Memory Management for LLM Serving with PagedAttention*）—— continuous batching 与分页 KV cache（⚠️版本/特性以官方为准）。
- Hugging Face Text Generation Inference（TGI）官方文档 —— HF 模型部署与 serving（⚠️待核实版本）。
- NVIDIA TensorRT-LLM 官方文档 —— kernel 级推理优化与 in-flight batching（⚠️待核实版本）。
- Megatron-LM 论文 —— tensor / pipeline parallelism 的经典工程实现。
