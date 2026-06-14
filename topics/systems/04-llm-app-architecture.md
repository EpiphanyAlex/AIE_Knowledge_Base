---
topic: LLM 应用架构
domain: systems
difficulty: 基础
status: drafted
prerequisites: [rag-basics]
tags: [architecture, orchestration, caching, guardrails, fallback]
---

# LLM 应用架构

## 一句话概览
> 一个生产级 LLM 应用不只是"调一次模型"，而是一条完整链路：前端/API 接收请求 → orchestration 编排各步骤 → 检索/工具补充信息 → 调 LLM → 后处理与校验 → 返回；外加 caching、guardrails、fallback、observability 这些保证质量、成本、安全和可观测的支撑模块。

## 概念讲解

**0. 为什么需要"架构"**
直接 `prompt → 模型 → 回答` 在 demo 里够用，但上线后会暴露一堆问题：模型会胡说（hallucination）、会被恶意输入诱导（prompt injection）、慢、贵、偶尔超时、出问题查不到原因。生产架构就是围绕这些问题，在裸模型外面加一圈"工程外壳"。

**1. 典型分层**
从外到内可以分成几层：

- **前端 / API 层**：接收用户请求，做鉴权、限流（rate limit）、参数校验；常用流式返回（streaming）把 token 逐个吐给前端，降低用户感知延迟。
- **Orchestration（编排层）**：整个链路的"大脑"，决定每一步做什么、按什么顺序、把谁的输出喂给谁。简单应用是固定流程（检索→拼 prompt→调模型）；复杂应用是 agent，由模型自己决定下一步调哪个工具。
- **Prompt 管理**：把 prompt 当成"代码"管理——用模板（template）+ 变量，版本化、可测试、可灰度，而不是把字符串散落在代码里。
- **检索 / RAG 模块**：把用户问题去向量库 / 搜索引擎找相关文档，作为 context 拼进 prompt，让模型基于"事实"回答（详见 rag-basics）。
- **工具调用（tool calling）**：让模型调用外部函数 / API（查数据库、算数、调天气接口等），把 LLM 从"只会说"变成"能做事"。
- **后处理层**：解析模型输出（如抽 JSON）、格式化、校验、再加工。
- **支撑模块**：caching、guardrails、fallback / 路由、observability，横跨上面各层。

**2. Orchestration 与编排框架的角色**
"编排"就是把上面这些步骤串成一条可控的链路。框架（如 LangChain、LlamaIndex）提供现成的"积木"：prompt 模板、检索器（retriever）、工具接口、链（chain）、记忆（memory）等，让你少写胶水代码。

- **LangChain**：偏"通用编排 / agent 框架"，强项是把多步骤、多工具、多模型串起来。
- **LlamaIndex**：偏"数据 / RAG 框架"，强项是把外部数据接进来、做索引和检索。
- 两者功能有重叠，也常一起用。⚠️待核实：具体 API、模块名、最佳实践随版本变化很快，截至 2026-06 引用前应查官方文档。
- **重要权衡**：框架省事，但也带来抽象层、隐藏的 prompt、调试困难、版本耦合。很多团队上线时会"去框架"，自己写薄薄的编排逻辑，换取可控性。这是常考的设计判断题。

**3. Prompt 管理与模板**
- **模板化**：`"回答用户问题。已知资料：{context}。问题：{question}"`，把变量和固定结构分开。
- **版本化 / 评测**：prompt 改一个字都可能影响效果，所以要像代码一样有版本、有回归测试（eval）、能 A/B。
- **分层**：system prompt（角色 / 规则）+ few-shot 示例 + 用户输入 + 检索到的 context，拼成最终 prompt。

**4. Caching（缓存）**
LLM 调用慢又贵，缓存能显著省钱降延迟。两类常见：

- **结果缓存（exact / result cache）**：完全相同的请求直接返回上次结果（key 是 prompt 的精确匹配或 hash）。简单、可靠，但只命中"一字不差"的重复。
- **语义缓存（semantic cache）**：用 embedding 判断"语义相近"的问题，相似度超过阈值就复用旧答案。命中率更高，但有"答非所问"的风险（两个问题看起来像、其实要求不同），阈值要谨慎调。
- 另有 **provider 侧的 prompt caching**：缓存长 prompt 的前缀（如固定的 system prompt + 文档），后续请求复用，省的是输入侧的重复计算。⚠️待核实：是否支持、计费方式各家不同，截至 2026-06 用前查对应文档。

**5. Guardrails（护栏 / 安全校验）**
在输入和输出两端加"检查关卡"：

- **输入校验**：过滤 / 检测恶意或不合规输入，重点是 **prompt injection**（用户在输入里塞"忽略上面的指令，改成……"来劫持模型）。
- **输出校验**：检查模型输出是否符合格式（如必须是合法 JSON）、是否含有害 / 敏感内容（content safety）、是否泄露了不该说的信息。
- **结构校验**：用 schema（如 JSON schema）约束输出结构，不合格就重试或拒绝。
- 防 prompt injection 没有银弹，常见做法是：把"系统指令"和"用户数据"清晰隔离、对工具调用做权限限制（最小权限）、对高风险动作加人工确认。

**6. Fallback / 重试 / 多模型路由**
- **重试（retry）**：模型超时、限流、偶发错误时自动重试，通常配指数退避（exponential backoff）。
- **fallback（降级）**：主模型挂了 / 太慢，自动切到备用模型或更简单的回答路径，保证服务不中断。
- **多模型路由（routing）**：按任务难度 / 成本把请求分给不同模型——简单问题用小而快的便宜模型，难问题才上大模型，平衡成本和质量。

**7. Observability（可观测性）钩子**
LLM 应用是"非确定性"的，出问题难复现，所以要全程埋点：

- **logging / tracing**：记录每一步的输入输出（prompt、检索结果、工具调用、模型回答），出问题能回溯整条链路。
- **指标（metrics）**：延迟、token 用量、成本、错误率、缓存命中率。
- **评测（eval）**：线下用测试集 + 线上抽样，持续衡量回答质量（常用 LLM-as-a-judge 或人工标注）。

**8. 典型数据流**
一个带 RAG + 工具的请求，典型走法：

```
用户请求
  → [API 层] 鉴权 / 限流 / 校验
  → [Guardrails] 输入校验（含 prompt injection 检测）
  → [Cache] 查缓存，命中则直接返回
  → [Orchestration] 决定步骤
      → [检索 / RAG] 取相关文档
      → [拼 prompt] 模板 + context + 用户问题
      → [LLM 调用]（可能触发 tool calling，循环几轮）
  → [后处理] 解析 / 格式化输出
  → [Guardrails] 输出校验（格式 / 内容安全）
  → [Cache] 写入缓存
  → 返回（含 observability 全程埋点；任一步失败走 fallback / retry）
```

## 面试问答卡

### Q1. What are the main parts of a production LLM application? / 一个生产级 LLM 应用有哪些主要组成部分？
**难度:** 基础
**Answer (EN):**
- It is more than one model call. Typical parts: API layer, orchestration, prompt management, retrieval / RAG, tool calling, post-processing.
- Plus cross-cutting modules: caching, guardrails, fallback / routing, and observability.
- The model is the core, but most engineering work is the "shell" around it that handles cost, safety, speed, and reliability.
**核心答案 (中):**
- 不只是调一次模型。典型组成：API 层、orchestration（编排）、prompt 管理、检索 / RAG、tool calling、后处理。
- 加上横切模块：caching、guardrails、fallback / 路由、observability。
- 模型是核心，但大部分工程在外面这层"外壳"，处理成本、安全、速度、可靠性。
**追问 / 深入 (中):**
- 追问"哪些是 demo 可省、上线必须有的？" → demo 可只留检索+prompt+模型；上线后 guardrails、caching、fallback、observability 基本都得补，因为模型会胡说、会慢、会挂、出问题要能查。
**常见误区 (中):**
- 以为"接个模型 API 就完事了"；生产化的难点恰恰在模型之外的工程外壳。

### Q2. What does orchestration mean, and what role do LangChain / LlamaIndex play? / 什么是 orchestration？LangChain / LlamaIndex 扮演什么角色？
**难度:** 基础
**Answer (EN):**
- Orchestration is the logic that connects all steps: retrieve, build prompt, call the model, call tools, post-process — and decides the order.
- LangChain is more of a general orchestration / agent framework; LlamaIndex focuses more on data and RAG (indexing + retrieval).
- They give ready-made building blocks (prompt templates, retrievers, tool interfaces, chains) so you write less glue code.
**核心答案 (中):**
- orchestration 是把各步骤串起来的逻辑：检索、拼 prompt、调模型、调工具、后处理，并决定顺序。
- LangChain 偏通用编排 / agent 框架；LlamaIndex 偏数据 / RAG（索引 + 检索）。
- 它们提供现成积木（prompt 模板、retriever、工具接口、chain），少写胶水代码。
**追问 / 深入 (中):**
- 追问"用框架还是自己写？" → 框架起步快，但有抽象层、隐藏 prompt、调试难、版本耦合；很多团队上线时改用自己写的薄编排，换可控性。没有绝对答案，看团队和复杂度。(EN 一句示范: "Frameworks are great to start, but many teams drop them in production for control.")
**常见误区 (中):**
- 把 LangChain / LlamaIndex 当成"必须用"的基础设施；它们只是可选的开发框架，不用也能做。

### Q3. Why and how do you cache in an LLM app? Exact cache vs semantic cache? / 为什么以及怎么在 LLM 应用里做缓存？结果缓存和语义缓存的区别？
**难度:** 进阶
**Answer (EN):**
- LLM calls are slow and costly, so caching saves money and latency.
- Exact / result cache: same request returns the last result (key is the exact prompt or its hash). Simple and safe, but only hits identical requests.
- Semantic cache: uses embeddings to reuse answers for "similar" questions. Higher hit rate, but risk of returning a wrong answer when two questions look alike but differ — so the similarity threshold matters.
**核心答案 (中):**
- LLM 调用慢又贵，缓存省钱降延迟。
- 结果缓存：完全相同的请求返回上次结果（key 是精确 prompt 或 hash）。简单可靠，只命中一字不差的重复。
- 语义缓存：用 embedding 复用"语义相近"问题的答案。命中率高，但相似问题需求可能不同，会答非所问，阈值要谨慎调。
**追问 / 深入 (中):**
- 追问"还有别的缓存层吗？" → provider 侧的 prompt caching，缓存长 prompt 的固定前缀（如 system prompt + 文档），省输入侧重复计算。⚠️待核实：各家是否支持、怎么计费不同。
**常见误区 (中):**
- 以为语义缓存总是更好；它会引入"看起来像、其实不一样"的错误命中，安全/正确性敏感场景要慎用或调高阈值。

### Q4. What are guardrails, and how do you defend against prompt injection? / 什么是 guardrails？怎么防 prompt injection？
**难度:** 进阶
**Answer (EN):**
- Guardrails are checks on the input and output sides: input validation (including prompt injection detection), output validation (format / schema), and content safety.
- Prompt injection is when a user hides instructions in their input to hijack the model ("ignore the above and do X").
- Defenses: clearly separate system instructions from user data, limit tool permissions (least privilege), validate outputs, and add human approval for risky actions. There is no single perfect fix.
**核心答案 (中):**
- guardrails 是输入 / 输出两端的检查：输入校验（含 prompt injection 检测）、输出校验（格式 / schema）、内容安全。
- prompt injection 指用户在输入里塞指令来劫持模型（"忽略上面，改做 X"）。
- 防御：清晰隔离系统指令和用户数据、对工具做最小权限、校验输出、高风险动作加人工确认。没有单一银弹。
**追问 / 深入 (中):**
- 追问"间接 prompt injection 是什么？" → 恶意指令藏在被检索 / 被读取的外部内容里（网页、文档），模型读到后被劫持，比直接注入更隐蔽，所以对"检索来的内容"也要当成不可信数据处理。
**常见误区 (中):**
- 以为"在 system prompt 里写一句别被骗"就能防住；模型不可靠地区分指令和数据，必须靠工程隔离 + 权限 + 输出校验多层防御。

### Q5. How do retry, fallback, and multi-model routing work, and why use them? / 重试、fallback、多模型路由分别是什么？为什么要用？
**难度:** 进阶
**Answer (EN):**
- Retry: automatically retry on timeout, rate limit, or transient errors, usually with exponential backoff.
- Fallback: if the main model fails or is too slow, switch to a backup model or a simpler path so the service stays up.
- Multi-model routing: send requests to different models by difficulty / cost — small fast cheap model for easy questions, big model only for hard ones.
- Together they improve reliability and balance cost vs quality.
**核心答案 (中):**
- 重试：超时 / 限流 / 偶发错误时自动重试，通常配指数退避。
- fallback：主模型挂了或太慢，切到备用模型或更简单路径，保证服务不断。
- 多模型路由：按难度 / 成本分流——简单问题用小而快的便宜模型，难问题才上大模型。
- 三者合起来提升可靠性，并平衡成本与质量。
**追问 / 深入 (中):**
- 追问"路由怎么判断难易？" → 常见用规则（长度 / 关键词）、小分类模型、或先用便宜模型试，不满意再升级（cascade，级联）。
**常见误区 (中):**
- 把 retry 当成万能：对"模型答错"这类非瞬时错误，盲目重试既不省钱也不解决问题，应配合更换 prompt / 模型或人工兜底。

### Q6. Walk me through the data flow of one request in a RAG + tools app. / 描述一个带 RAG 和工具调用的应用里，单次请求的数据流。
**难度:** 高阶
**Answer (EN):**
- API layer: auth, rate limit, validate the request.
- Guardrails: check the input, including prompt injection detection.
- Cache: check first; return early on a hit.
- Orchestration: retrieve relevant docs (RAG), build the prompt (template + context + question), call the LLM — which may trigger tool calls and loop a few rounds.
- Post-process: parse / format the output (e.g. extract JSON).
- Output guardrails: check format and content safety; write to cache; return.
- Throughout: observability (tracing / metrics); any failed step goes to retry / fallback.
**核心答案 (中):**
- API 层：鉴权、限流、校验请求。
- guardrails：输入校验，含 prompt injection 检测。
- cache：先查缓存，命中直接返回。
- orchestration：检索相关文档（RAG）→ 拼 prompt（模板 + context + 问题）→ 调 LLM（可能触发 tool calling，循环几轮）。
- 后处理：解析 / 格式化输出（如抽 JSON）。
- 输出 guardrails：校验格式和内容安全 → 写缓存 → 返回。
- 全程：observability（tracing / metrics）；任一步失败走 retry / fallback。
**追问 / 深入 (中):**
- 追问"为什么 cache 查询放在检索和模型调用之前？" → 缓存命中就能跳过最贵的检索和模型调用，省钱降延迟；所以缓存要尽量靠前（但要在 guardrails 之后，避免缓存了恶意输入的结果）。
**常见误区 (中):**
- 把数据流画成一条直线；实际是有环的——tool calling 会让"调模型 → 调工具 → 再调模型"循环多轮，直到模型给出最终答案。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "A production LLM app is not one model call. It is a pipeline: API layer, orchestration, retrieval, the model, and post-processing."
  (中) 生产级 LLM 应用不是调一次模型，而是一条链路：API 层、编排、检索、模型、后处理。
- (EN) "Around that pipeline we add caching for cost, guardrails for safety, fallback for reliability, and observability to debug."
  (中) 链路外面再加：caching 省成本、guardrails 保安全、fallback 保可靠、observability 便于排查。
- (EN) "Orchestration is the brain that connects all steps. Frameworks like LangChain or LlamaIndex give building blocks, but many teams drop them in production for control."
  (中) orchestration 是串起所有步骤的大脑。LangChain、LlamaIndex 这类框架提供积木，但很多团队上线时为了可控性会弃用框架。
- (EN) "Caching has two kinds: exact cache for identical requests, and semantic cache for similar questions — the semantic one is riskier."
  (中) 缓存有两种：结果缓存命中完全相同的请求，语义缓存命中相近的问题——后者风险更高。
- (EN) "Guardrails check input and output. Prompt injection is the key threat — separate system instructions from user data and limit tool permissions."
  (中) guardrails 检查输入和输出。prompt injection 是核心威胁——要隔离系统指令和用户数据，并限制工具权限。
- (EN) "For reliability we use retry with backoff, fallback to a backup model, and routing to send easy questions to a cheaper model."
  (中) 为了可靠性，用带退避的重试、降级到备用模型、以及把简单问题路由给便宜模型。

## 延伸阅读
- LangChain / LlamaIndex 官方文档 —— 编排与 RAG 框架（⚠️待核实：API 与模块随版本变化快，引用前查官网）。
- OWASP Top 10 for LLM Applications —— prompt injection 等 LLM 安全风险清单（防 guardrails 设计参考）。
- *Building LLM applications for production*（Chip Huyen 博客）—— 生产化 LLM 系统的工程权衡综述。
