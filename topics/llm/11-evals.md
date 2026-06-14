---
topic: Evals
domain: llm
difficulty: 进阶
status: drafted
prerequisites: []
tags: [evaluation, llm-as-judge, benchmarks, metrics, offline-online]
---

# Evals

## 一句话概览
> Eval（评估）是衡量 LLM 系统好不好的办法。LLM 输出是开放式的、常常没有唯一正确答案，所以评估很难——做对 eval 是把"感觉还行"变成"能拿数字说话"的关键。

## 概念讲解

**1. 为什么评估 LLM 很难**
传统 ML 分类任务有明确标签，算个 accuracy 就完了。但 LLM 经常做**开放式生成**（写邮件、总结、答问），同一个问题可以有很多合理答案，措辞还各不相同：
- **没有唯一正确答案**：一个总结可以有十种好写法，逐字对比会判错。
- **答案是文本**：好坏要看语义、事实对不对、有没有跑题，不是简单匹配。
- **要评的维度多**：正确性、相关性、风格、是否安全、是否啰嗦……不止一个指标。

**2. 评估的几种类型**

**(a) 基于参考的指标（reference-based）**
有一个"标准答案"（reference），把模型输出和它比对：
- **BLEU**：原本给机器翻译用，看输出和参考的 **n-gram 重叠**（连续若干词的重合度），偏 precision。
- **ROUGE**：原本给摘要用，也是看 n-gram 重叠，偏 recall（参考里的词有没有被覆盖）。
- **局限**：它们只看**字面重叠**，不懂语义。换个说法、用同义词，分数就掉，但答案其实一样好。所以这类指标对开放式生成越来越不够用。

**(b) 任务指标（task metrics）**
当任务能转成有标准答案的形式时，用经典指标：
- **accuracy**：选择题、分类题，对就是对。
- **F1 / precision / recall**：抽取类任务（如从文本里抽实体）常用。
- 好处是客观、可复现；前提是任务本身有明确答案。

**(c) 人评（human evaluation）**
让人来打分或两两对比（A 好还是 B 好）：
- **优点**：最贴近真实质量，能评细微的语义、风格、有用程度。
- **缺点**：慢、贵、难规模化；不同标注员标准不一（要算一致性、写评分规范 rubric）。

**(d) LLM-as-judge（用模型当裁判）**
用一个强模型去给另一个模型的输出打分或做对比：
- **怎么做**：给裁判模型一个清晰的评分标准（rubric），让它输出分数或选出更好的一个。常见有两种：**打分式**（给 1–5 分）和**对比式 / pairwise**（A vs B 选一个）。
- **优点**：比人评快很多、便宜、可规模化，比 BLEU/ROUGE 更懂语义。
- **缺点 / 偏差**：
  - **position bias（位置偏差）**：对比时倾向选排在前面（或后面）的那个。
  - **verbosity bias（啰嗦偏差）**：倾向选更长的答案。
  - **self-preference（自我偏好）**：倾向给和自己风格像的、或自己家模型的输出更高分。
  - 缓解办法：交换 A/B 顺序再评一次、给清晰 rubric、用更强的裁判、关键场景配合人评抽查。

**3. Benchmark（基准测试）**
社区共享的标准题库，用来横向比较不同模型，例如 **MMLU**（多学科知识选择题）等。⚠️待核实：具体的 benchmark 列表、各模型在上面的分数、当前 SOTA，都随版本快速变化，引用前务必核对来源与时间。
- benchmark 的价值：统一、可比、好沟通。
- benchmark 的坑：
  - **数据污染（contamination）**：测试题可能已混进训练数据，分数虚高。
  - **过拟合榜单**：刷分不等于真实有用。
  - **和你的任务不匹配**：榜单高分≠在你具体场景好用。所以**自建 eval** 往往更重要。

**4. Offline eval vs Online eval**
- **Offline eval（线下）**：上线前，用固定的测试集离线跑，看指标。快、可复现、好做回归对比（改了 prompt 有没有变差）。
- **Online eval（线上）**：上线后，用真实流量看真实效果。
  - **A/B test**：把流量分两组，比较新旧版本的线上指标（点击、留存、任务完成率、用户点赞点踩）。
  - **线上反馈信号**：用户的赞/踩、是否重试、是否人工接管等。
  - offline 看"理论上好不好"，online 看"真用户用着好不好"，两者互补：先 offline 把关，再 online 验证。

**5. 怎么评 RAG 和 agent**
- **RAG**：拆成两段评。
  - **检索（retrieval）**：召回的文档对不对、全不全（用 recall、precision、或排序指标）。
  - **生成（generation）**：答案有没有忠实于检索到的内容（**faithfulness / 不能编**）、有没有真正回答问题（**answer relevance**）、检索内容相不相关（**context relevance**）。⚠️待核实：RAGAS 等具体工具的指标定义与实现细节请核对官方文档。
- **Agent**：通常是多步、调工具，评估更看**端到端**和**过程**。
  - **task success rate**：最终任务有没有完成（端到端，最重要）。
  - **过程指标**：步数、是否选对工具、有没有死循环、成本/延迟。
  - 评 agent 一般要搭一套可复现的任务环境，比单轮问答难得多。

**6. 建自己的 eval set（实务）**
公开 benchmark 救不了你的具体业务，自建 eval 才是工程关键：
- **从真实数据出发**：收集线上真实 query / 失败案例，比凭空编的更有代表性。
- **覆盖典型 + 边界**：常见场景要有，难例 / 易错例 / 安全红线也要有。
- **定清楚"好"的标准**：写 rubric，越具体越好（什么算对、什么算错）。
- **规模适中、可迭代**：先几十上百条能跑起来，再逐步扩充。
- **版本化、防污染**：eval set 要存好、版本化，别让它泄进 prompt 示例或训练数据。
- **混合评估法**：自动指标（含 LLM-as-judge）跑全量做回归，人评抽样校准——既快又可信。

## 面试问答卡

### Q1. Why is evaluating LLMs hard? / 为什么评估 LLM 很难？
**难度:** 基础
**Answer (EN):**
- LLM outputs are open-ended, so one question can have many good answers.
- There is often no single correct answer, and the output is free text, not a fixed label.
- Quality has many sides at once: correctness, relevance, style, safety, length.
**核心答案 (中):**
- LLM 输出是开放式的，一个问题可以有很多合理答案。
- 常常没有唯一正确答案，输出是自由文本，不是固定标签。
- 质量是多维的：正确性、相关性、风格、安全、长度都要看。
**追问 / 深入 (中):**
- 追问"那传统 ML 为什么好评？" → 分类/回归有明确标签和标准答案，直接算 accuracy 之类即可；LLM 的开放式生成没有这种唯一参考。
**常见误区 (中):**
- 以为给 LLM 算个 accuracy 就行；只有任务能转成有标准答案的形式时 accuracy 才适用。

### Q2. What are BLEU and ROUGE, and what are their limits? / BLEU 和 ROUGE 是什么？局限在哪？
**难度:** 基础
**Answer (EN):**
- Both are reference-based metrics that measure n-gram overlap between the output and a reference.
- BLEU comes from machine translation (more precision-focused); ROUGE comes from summarization (more recall-focused).
- The limit: they only look at surface word overlap, not meaning. A correct answer with different wording gets a low score.
**核心答案 (中):**
- 两者都是基于参考的指标，比较输出和参考答案的 **n-gram 重叠**。
- BLEU 出自机器翻译（偏 precision）；ROUGE 出自摘要（偏 recall）。
- 局限：只看字面词重叠，不懂语义。换个说法、用同义词，分数就掉，但答案可能一样好。
**追问 / 深入 (中):**
- 追问"那现在还用吗？" → 在有强参考、看重词面覆盖的任务（如翻译、抽取式摘要）仍有用；开放式生成更多转向 LLM-as-judge 或人评。
**常见误区 (中):**
- 以为 BLEU/ROUGE 分高就等于答案好；它们只衡量词面重叠，语义对错不管。

### Q3. What is LLM-as-judge, and what biases does it have? / 什么是 LLM-as-judge？它有哪些偏差？
**难度:** 进阶
**Answer (EN):**
- LLM-as-judge means using a strong model to score or compare another model's outputs, guided by a clear rubric.
- It is much faster and cheaper than human eval, and understands meaning better than BLEU/ROUGE.
- Common biases: position bias (favoring the first/last option), verbosity bias (favoring longer answers), and self-preference (favoring its own style or family).
- We reduce them by swapping A/B order, giving a clear rubric, using a stronger judge, and spot-checking with humans.
**核心答案 (中):**
- LLM-as-judge 就是用一个强模型，按清晰的评分标准（rubric）给另一个模型的输出打分或做对比。
- 比人评快且便宜，比 BLEU/ROUGE 更懂语义。
- 常见偏差：position bias（偏好靠前/靠后的）、verbosity bias（偏好更长的）、self-preference（偏好自己风格/自家模型）。
- 缓解：交换 A/B 顺序再评、给清晰 rubric、用更强裁判、关键场景人评抽查。
**追问 / 深入 (中):**
- 追问"打分式和对比式哪个好？" → pairwise（两两对比）通常更稳，因为"谁更好"比"打几分"更容易判一致；缺点是要两两比、成本高。
**常见误区 (中):**
- 把 LLM-as-judge 当成绝对真理；它有系统性偏差，要做缓解并配人评校准，不能完全替代人评。

### Q4. What is the difference between offline and online evaluation? / offline eval 和 online eval 有什么区别？
**难度:** 进阶
**Answer (EN):**
- Offline eval runs on a fixed test set before launch. It is fast, repeatable, and good for regression checks.
- Online eval uses real traffic after launch, e.g. A/B tests and user feedback like thumbs up/down or retries.
- Offline tells you "is it good in theory"; online tells you "is it good for real users". They are complementary.
**核心答案 (中):**
- offline eval 上线前用固定测试集离线跑，快、可复现、适合做回归对比。
- online eval 上线后用真实流量，比如 A/B test 和用户反馈（点赞点踩、重试）。
- offline 看"理论上好不好"，online 看"真用户用着好不好"，两者互补。
**追问 / 深入 (中):**
- 追问"为什么不只做 online？" → online 慢、有风险、不可复现，改坏了直接影响用户；先 offline 把关再 online 验证更稳。
**常见误区 (中):**
- 以为 offline 分高就一定线上好；offline 测试集和真实分布常有差距，必须 online 再验。

### Q5. How do you evaluate a RAG system? / 怎么评估一个 RAG 系统？
**难度:** 进阶
**Answer (EN):**
- Split it into two parts: retrieval and generation.
- Retrieval: are the fetched documents relevant and complete? Use recall, precision, or ranking metrics.
- Generation: is the answer faithful to the retrieved context (no made-up facts), and does it actually answer the question (answer relevance)?
- A bad answer can come from bad retrieval or bad generation, so measuring both helps you find where it breaks.
**核心答案 (中):**
- 拆成两段：检索（retrieval）和生成（generation）。
- 检索：召回的文档相不相关、全不全？用 recall、precision、或排序指标。
- 生成：答案是否忠实于检索内容（不能编 / faithfulness）、是否真正回答了问题（answer relevance）。
- 答案差可能出在检索差，也可能出在生成差，分开评才能定位问题在哪。
**追问 / 深入 (中):**
- 追问"如果检索对了但答案还是错？" → 说明问题在生成端（没用好上下文、或产生幻觉）；分段评估正是为了区分这两类故障。
**常见误区 (中):**
- 只看最终答案对不对，不拆开评；这样无法定位是检索的锅还是生成的锅。

### Q6. How would you build your own eval set for a real product? / 怎么为一个真实产品建自己的 eval set？
**难度:** 高阶
**Answer (EN):**
- Start from real data: collect real user queries and failure cases, not made-up ones.
- Cover both typical cases and edge cases (hard examples, common mistakes, safety lines).
- Write a clear rubric that defines what counts as good or bad.
- Keep it versioned and protect it from contamination — do not leak it into prompts or training data.
- Use a mix: automatic metrics (including LLM-as-judge) for full-set regression, plus human spot-checks to calibrate.
**核心答案 (中):**
- 从真实数据出发：收集真实 query 和失败案例，别凭空编。
- 同时覆盖典型场景和边界场景（难例、易错例、安全红线）。
- 写清楚 rubric，定义什么算好、什么算坏。
- eval set 要版本化、防污染——别泄进 prompt 示例或训练数据。
- 混合评估：自动指标（含 LLM-as-judge）跑全量做回归，人评抽样校准。
**追问 / 深入 (中):**
- 追问"eval set 多大合适？" → 没有绝对数；先几十到上百条能跑起来、能区分版本好坏即可，再按需扩充，关键是有代表性而非单纯堆量。
**常见误区 (中):**
- 直接拿公开 benchmark 当验收标准；榜单高分不等于你具体业务好用，自建 eval 才贴合真实场景。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "Evaluating LLMs is hard because outputs are open-ended — one question can have many good answers, and there is no single correct one."
  (中) 评估 LLM 难，因为输出是开放式的——一个问题有很多好答案，没有唯一正确答案。
- (EN) "BLEU and ROUGE only measure word overlap with a reference, so they miss meaning. A correct answer in different words scores low."
  (中) BLEU 和 ROUGE 只看和参考的词面重叠，不懂语义；换个说法的正确答案分数会很低。
- (EN) "LLM-as-judge uses a strong model to score outputs. It is fast and scalable, but has biases like position, verbosity, and self-preference."
  (中) LLM-as-judge 用强模型给输出打分，快且可规模化，但有位置、啰嗦、自我偏好等偏差。
- (EN) "Offline eval uses a fixed test set before launch; online eval uses real traffic with A/B tests and user feedback. They are complementary."
  (中) offline eval 上线前用固定测试集，online eval 上线后用真实流量做 A/B 和看用户反馈，两者互补。
- (EN) "For RAG, evaluate retrieval and generation separately — was the context relevant, and was the answer faithful and on-point?"
  (中) 评 RAG 要把检索和生成分开评——上下文相不相关、答案忠不忠实、有没有切题。
- (EN) "Public benchmarks help compare models, but your own eval set built from real cases matters more for a real product."
  (中) 公开 benchmark 便于比模型，但对真实产品来说，用真实案例自建的 eval set 更重要。

## 延伸阅读
- *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*（Zheng et al., 2023）—— LLM-as-judge 偏差与可靠性的代表性研究。⚠️待核实：具体结论与数字请核对原文。
- RAGAS 文档 —— RAG 评估指标（faithfulness、answer relevance、context relevance 等）的实现参考。⚠️待核实：指标定义与版本以官方文档为准。
- MMLU 等公开 benchmark 论文 / 排行榜 —— 用于横向比较。⚠️待核实：榜单、分数、SOTA 随时间快速变化，引用前核对来源与日期（截至 2026-06）。
