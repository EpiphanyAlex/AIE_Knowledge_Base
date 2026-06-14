---
topic: 监控与可观测性
domain: systems
difficulty: 进阶
status: drafted
prerequisites: [llm-app-architecture]
tags: [monitoring, observability, tracing, drift, online-eval]
---

# 监控与可观测性

## 一句话概览
> 监控（monitoring）回答"系统现在健不健康"（latency、错误率、成本），可观测性（observability）回答"为什么出问题"——把一次请求经过的整条链路（检索、工具、各 LLM 调用）追踪出来。LLM 应用还要额外盯**输出质量**，因为它可能"跑得很顺但答得很烂"。

## 概念讲解

**1. 为什么 LLM 应用的监控不一样**
传统服务挂了就是报错、超时、500，比较好抓。LLM 应用的麻烦是：请求**全部成功（HTTP 200），输出却是错的**——胡编（hallucination）、答非所问、忽然拒答。所以除了系统指标，还得专门监控**质量**。

**2. 系统指标（system metrics）——"跑得快不快、贵不贵"**
- **latency 延迟**：一次请求多久返回。LLM 里要特别看 **TTFT（Time To First Token，首 token 时间）**——用户看到第一个字的等待，对流式（streaming）体验最关键；以及**总生成时间 / 每 token 时间**。
- **throughput 吞吐**：单位时间能处理多少请求 / 多少 token（如 tokens/s、QPS）。
- **error rate 错误率**：超时、限流（rate limit）、API 报错、上游模型 5xx 的比例。
- **成本 / token 用量（cost / token usage）**：input/output token 数、每次调用花多少钱。LLM 应用成本基本和 token 成正比，是最容易失控的一项，必须按用户 / 功能 / 模型维度拆开看。

**3. 质量指标（quality metrics）——"答得好不好"**
- **输出质量**：答案对不对、有没有用、格式合不合规。
- **faithfulness 忠实度**：RAG 场景里，答案是否**忠于检索到的内容**、有没有瞎编（与上下文无关或矛盾就是幻觉）。
- **用户反馈（user feedback）**：点赞 / 点踩（thumbs up/down）、重新生成次数、复制率、是否追问。
- **拒答率（refusal rate）**：模型说"我无法回答"的比例。太高说明 prompt 太保守或检索没命中，伤体验。

**4. tracing（链路追踪）——可观测性的核心**
一次 LLM 应用请求往往不是一次模型调用，而是一条链路：
```
用户输入 → 改写 query → 检索（retrieval）→ 调工具（tool call）→ 拼 prompt → LLM 调用 → 可能再来一轮 → 最终输出
```
**trace** 把这整条链路记录成一棵带时间的树，每个环节是一个 **span**（带耗时、输入、输出、token 数）。出问题时能精确定位是**哪一步**慢了 / 错了——是检索没召回，还是 prompt 太长，还是某次 LLM 调用跑偏。这是和传统"只看一个聚合数字"最大的不同。LangSmith、Langfuse、Arize Phoenix 等工具就是干这个的（⚠️待核实：各工具的具体功能边界 / 定价随版本变化，截至 2026-06 仅作角色说明）。

**5. logging（日志）——记 prompt 和 output，但小心隐私**
把每次的 prompt、检索内容、模型输出、参数都记下来，方便复盘和回放（replay）。但 prompt / output 里常含**用户隐私（PII）**——姓名、邮箱、聊天内容。所以要：脱敏（redaction / masking）、按需采样而非全量、设访问权限和保留期限（retention）、遵守合规（如 GDPR）。

**6. drift（漂移）——"世界变了，模型没变"**
- **输入分布漂移（input drift）**：用户问的问题类型、语言、长度随时间变化（如忽然一堆新话题），模型没见过就答不好。
- **质量漂移（quality drift）**：输出质量随时间下滑。可能因为上游模型被供应商悄悄更新、检索库过期、用户群变化。
- 监控做法：跟踪输入特征分布、关键质量指标的时间趋势，异常就告警。

**7. 在线评估与反馈回路（online eval & feedback loop）**
线下（offline）评估是上线前用固定测试集打分；**在线（online）评估**是对**真实流量**持续评。常见两条路：
- **用户反馈信号**：点赞点踩、重生成、停留——便宜但稀疏、有偏。
- **LLM-as-judge 抽样打分**：用另一个 LLM 当裁判，对**抽样**的线上请求按 faithfulness / 有用性等维度打分。能规模化，但裁判本身会错、会有偏好（⚠️待核实：判官可靠性依模型 / prompt 而定，需人工抽检校准）。
这些信号回流，用来发现退化、挑数据做后续优化——形成 feedback loop。

**8. 告警（alerting）**
对关键指标设阈值（如 p95 latency 超标、error rate 飙升、成本突增、拒答率异常、质量分掉到某线以下），触发就通知（PagerDuty / Slack 等）。要点：盯**用户能感知**的指标，控制噪音，避免告警疲劳（alert fatigue）。

**9. 和 "MLOps / 训练监控" 的区别**
本篇聚焦**运行时可观测性**（线上请求跑得怎么样、答得怎么样），不是模型训练阶段的实验跟踪、超参、训练曲线。两者都叫"监控"，但关注的对象不同。

## 面试问答卡

### Q1. What should you monitor in an LLM application? / LLM 应用要监控什么？
**难度:** 基础
**Answer (EN):**
- Two groups. System metrics: latency (especially TTFT), throughput, error rate, and cost / token usage.
- Quality metrics: output quality, faithfulness, user feedback (thumbs up/down), and refusal rate.
- The key point: an LLM app can return HTTP 200 but still give a wrong answer, so you must watch quality, not just system health.
**核心答案 (中):**
- 分两类。系统指标：latency（尤其 TTFT）、throughput、error rate、成本 / token 用量。
- 质量指标：输出质量、faithfulness、用户反馈（点赞点踩）、拒答率。
- 关键：LLM 应用可能返回 200 但答案是错的，所以光看系统健康不够，必须盯质量。
**追问 / 深入 (中):**
- 追问"为什么单独提 TTFT 而不只看总延迟？" → 因为多数应用是流式输出，用户感受到的是"多久看到第一个字"，TTFT 直接决定体验，可附一句：(EN) "TTFT is what the user actually feels in a streaming UI."
**常见误区 (中):**
- 只搬传统服务那套（CPU、500 错误率）就以为够了；漏掉质量监控，结果系统全绿但用户在骂答案差。

### Q2. What is the difference between monitoring and observability? / monitoring 和 observability 有什么区别？
**难度:** 基础
**Answer (EN):**
- Monitoring tells you *what* is wrong: it tracks known metrics like latency, error rate, and cost, and alerts when they cross a threshold.
- Observability tells you *why*: it lets you dig into a single request to find the root cause, mainly through tracing.
- In LLM apps, observability matters a lot because one request can chain retrieval, tools, and several LLM calls.
**核心答案 (中):**
- monitoring 告诉你"哪里不对"：盯已知指标（latency、错误率、成本），超阈值就告警。
- observability 告诉你"为什么不对"：能深入到**单次请求**找根因，主要靠 tracing。
- LLM 应用里 observability 尤其重要，因为一次请求会串起检索、工具、多次 LLM 调用。
**追问 / 深入 (中):**
- 追问"只有指标不够吗？" → 聚合指标只告诉你"整体变慢了"，但说不清是哪一步慢；要定位必须能下钻到单条 trace。
**常见误区 (中):**
- 把两者当同义词。指标是"已知问题的仪表盘"，可观测性是"未知问题的探查能力"。

### Q3. What is tracing and why is it important for LLM apps? / 什么是 tracing？为什么对 LLM 应用重要？
**难度:** 进阶
**Answer (EN):**
- A trace records the full path of one request as a tree of spans; each span is a step (retrieval, a tool call, an LLM call) with its own time, input, output, and token count.
- It matters because an LLM request is usually a chain, not a single call.
- When something is slow or wrong, the trace shows *which step* — bad retrieval, a too-long prompt, or one off LLM call.
**核心答案 (中):**
- 一条 trace 把单次请求的完整路径记成一棵 span 树；每个 span 是一步（检索、工具调用、LLM 调用），带各自的耗时、输入、输出、token 数。
- 重要是因为 LLM 请求通常是**一条链**而不是单次调用。
- 出问题时，trace 能指出**是哪一步**——检索没召回、prompt 太长、还是某次 LLM 调用跑偏。
**追问 / 深入 (中):**
- 追问"有哪些工具？" → LangSmith、Langfuse、Arize Phoenix 等专门做 LLM tracing；底层概念和分布式追踪的 OpenTelemetry 一脉相承（⚠️待核实：各工具具体能力 / 定价随版本变化）。
- 追问"span 里该记什么？" → 至少：输入、输出、耗时、token 数、用了哪个模型 / 哪些检索文档。
**常见误区 (中):**
- 以为 tracing 就是打日志。日志是零散事件；trace 是**带父子关系和时序**的结构，能还原整条因果链。

### Q4. How do you evaluate quality online, and what are the trade-offs? / 怎么做在线质量评估？各有什么取舍？
**难度:** 进阶
**Answer (EN):**
- Two main signals. User feedback: thumbs up/down, regenerate, copy — cheap to collect but sparse and biased.
- LLM-as-judge: use another LLM to score a *sample* of live requests on faithfulness, helpfulness, etc. — scalable but the judge itself can be wrong or biased.
- Best practice: combine both, sample instead of scoring everything, and spot-check the judge with humans.
**核心答案 (中):**
- 两类主要信号。用户反馈：点赞点踩、重生成、复制——便宜但稀疏、有偏。
- LLM-as-judge：用另一个 LLM 对**抽样**的线上请求按 faithfulness、有用性等打分——能规模化，但裁判自己也会错、有偏好。
- 实践：两者结合，**抽样**而非全量评，再用人工抽检校准裁判。
**追问 / 深入 (中):**
- 追问"online eval 和 offline eval 区别？" → offline 是上线前用固定测试集打分；online 是对真实流量持续评，能抓到测试集覆盖不到的真实问题。
- 追问"为什么不全量用 LLM-as-judge？" → 贵且慢，对每条请求都跑等于成本翻倍，所以抽样。
**常见误区 (中):**
- 把 LLM-as-judge 的分当绝对真值；它只是个有噪声的代理指标，必须人工校准、看趋势而非单点。

### Q5. What is drift in an LLM application, and how do you detect it? / LLM 应用里的 drift 是什么？怎么检测？
**难度:** 进阶
**Answer (EN):**
- Drift means the world changed but the system did not. Input drift: users start asking different kinds of questions. Quality drift: output quality slowly drops over time.
- Causes include the provider silently updating the model, a stale retrieval index, or a changing user base.
- Detect it by tracking the distribution of inputs and the time trend of key quality metrics, then alert on anomalies.
**核心答案 (中):**
- drift 指"世界变了但系统没变"。输入漂移：用户开始问不同类型的问题。质量漂移：输出质量随时间慢慢下滑。
- 成因：供应商悄悄更新了模型、检索库过期、用户群变化。
- 检测：跟踪输入特征的分布、关键质量指标的时间趋势，异常就告警。
**追问 / 深入 (中):**
- 追问"用 API 模型也会 drift 吗？" → 会，而且更隐蔽——你不控权重，供应商更新或下线某版本，你的输出可能一夜变样，所以更要持续监控。
**常见误区 (中):**
- 以为只有自训模型才会漂移；调 API 同样会，且因为不可控反而更需要盯。

### Q6. How would you log prompts and outputs without leaking user privacy? / 怎么在记录 prompt 和 output 的同时不泄露用户隐私？
**难度:** 高阶
**Answer (EN):**
- Prompts and outputs often contain PII (names, emails, chat content), so do not log everything blindly.
- Use redaction / masking on sensitive fields, sample instead of logging full traffic, set access control and a retention limit, and follow rules like GDPR.
- The goal is to keep enough to debug and replay, while limiting exposure.
**核心答案 (中):**
- prompt 和 output 常含 PII（姓名、邮箱、聊天内容），不能不假思索全量记录。
- 做法：对敏感字段脱敏 / mask、按需采样而非全量、设访问权限和保留期限、遵守 GDPR 等合规。
- 目标：留下足够复盘和回放（replay）的信息，同时把暴露面降到最低。
**追问 / 深入 (中):**
- 追问"全脱敏会不会让日志没法 debug？" → 是个权衡：可对低敏字段保留、高敏字段脱敏，或对内部受限人群短期保留原文，到期即删。
**常见误区 (中):**
- 为了"方便排查"把完整原始 prompt 长期全量存下来；这是隐私和合规的大坑。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "Monitoring tells you what is wrong; observability tells you why. For LLM apps you need both."
  (中) monitoring 告诉你哪里不对，observability 告诉你为什么；LLM 应用两者都要。
- (EN) "Watch two groups of metrics: system ones like latency, TTFT, throughput, error rate, and cost; and quality ones like faithfulness, user feedback, and refusal rate."
  (中) 盯两类指标：系统类（latency、TTFT、throughput、错误率、成本）和质量类（faithfulness、用户反馈、拒答率）。
- (EN) "The key risk is that an LLM app can return 200 but still give a wrong answer, so system health is not enough."
  (中) 关键风险是 LLM 应用可能返回 200 但答案是错的，所以只看系统健康不够。
- (EN) "Tracing records the whole request as a tree of spans, so I can see which step — retrieval, a tool, or one LLM call — went wrong."
  (中) tracing 把整次请求记成 span 树，让我看出是哪一步（检索、工具、还是某次 LLM 调用）出了问题。
- (EN) "For online eval I combine user thumbs up/down with LLM-as-judge on a sample, and I spot-check the judge with humans."
  (中) 在线评估我把用户点赞点踩和对抽样请求做 LLM-as-judge 结合，再用人工抽检校准裁判。
- (EN) "Drift means the world changed but the model did not; even API models drift when the provider updates them silently, so I track input distribution and quality trends."
  (中) drift 是世界变了模型没变；连 API 模型也会漂移（供应商悄悄更新），所以我跟踪输入分布和质量趋势。
- (EN) "When I log prompts and outputs I redact PII, sample, and set a retention limit, because those logs are a privacy risk."
  (中) 记 prompt 和 output 时我会脱敏 PII、采样、设保留期限，因为这些日志是隐私风险点。

## 延伸阅读
- LangSmith / Langfuse / Arize Phoenix 文档 —— LLM tracing 与在线评估工具的角色（⚠️待核实：功能与定价随版本变化，截至 2026-06）。
- OpenTelemetry 文档 —— 分布式 tracing 的通用标准（span / trace 概念来源）。
- *G-Eval* / "LLM-as-a-judge" 相关论文 —— 用 LLM 给输出打分的方法与已知偏差（⚠️待核实：具体方法与可靠性结论需查证最新文献）。
