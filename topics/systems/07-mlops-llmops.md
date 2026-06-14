---
topic: MLOps / LLMOps
domain: systems
difficulty: 进阶
status: drafted
prerequisites: [monitoring-observability]
tags: [MLOps, LLMOps, CI-CD, versioning, experiment-tracking, deployment]
---

# MLOps / LLMOps

## 一句话概览
> MLOps 是把 ML 模型从开发、上线到迭代的整套工程实践——让数据 / 训练 / 部署 / 监控自动化、可重复、可回溯；LLMOps 是这套实践在大模型时代的变体，重点从"从头训练"挪到了 prompt / RAG / 评测 / 成本 / 护栏。

## 概念讲解

**1. 直觉：ML 系统的难点不在模型，在"运维"**
一个 demo 跑通模型只是开始。要真正上线，你得反复问：这个结果是哪份数据、哪份代码、哪组超参跑出来的？换一版数据后效果是涨是跌？线上模型悄悄变差了怎么第一时间发现？这些"工程化"问题就是 MLOps 要解决的，本质是把 **DevOps 的可重复、自动化、可回溯**思想搬到 ML。

**2. ML 生命周期（lifecycle）**
ML 不是"训完就结束"，而是一个**循环**：
- **数据**：采集、清洗、标注、做特征。
- **训练 / 实验**：调模型、调超参，跑很多次实验做对比。
- **评估**：在留出集 / 测试集上验证，决定哪版能上。
- **部署**：把选中的模型发布到线上服务。
- **监控**：盯线上效果、延迟、数据分布。
- **迭代**：监控发现问题（如 data drift）→ 回到数据 / 训练重来。
MLOps 就是给这个循环装上"自动化 + 版本化 + 监控"的轨道。

**3. Versioning：四样东西都要版本化**
ML 的可重复性比普通软件难，因为结果由多个东西共同决定。要能复现一次实验，得同时锁定：
- **代码 version**：训练 / 预处理脚本（用 git）。
- **数据 version**：哪份数据集、哪个快照（数据变了结果就变）。
- **模型 version**：训出来的权重 + 它对应的代码和数据。
- **配置 / 超参 version**：learning rate、epoch 等。
> 口诀：**代码 + 数据 + 模型 + 配置**，缺一样就无法复现。

**4. Experiment tracking（实验追踪）**
调模型要跑几十上百次实验。experiment tracking 工具自动记录每次跑的**超参、指标、产物（artifact）、对应的代码 / 数据版本**，让你能横向对比"哪组配置最好"，而不是靠记在脑子里或 Excel。常见工具如 MLflow、Weights & Biases 等（⚠️待核实：具体功能 / 版本以官方文档为准）。

**5. CI/CD for models**
传统软件 CI/CD：代码提交 → 自动测试 → 自动部署。ML 多了两层：
- **CI（持续集成）**：除了测代码，还要测数据（schema、分布是否异常）、测模型（指标是否达标）。
- **CD（持续交付 / 部署）**：自动把通过门槛的模型打包、发布。
- 业界常额外提 **CT（continuous training，持续训练）**：数据 / 效果触发条件满足时自动重训。
关键是设**质量门槛（gate）**：指标不达标就不让上线。

**6. 部署策略（deployment strategies）**
新模型不要"一把全量切换"，要控制风险，常见三种：
- **shadow（影子部署）**：新模型和老模型同时收同样的线上流量，但**新模型的结果不返回给用户**，只用来对比 / 记录。零用户风险，用来验证。
- **canary（金丝雀）**：先把**一小部分流量**（如 5%）切到新模型，观察指标没问题再逐步放量。
- **A/B test**：把流量分成两组分别走新 / 老模型，**用业务指标统计对比**哪个更好（侧重决策，不只是技术验证）。

**7. LLMOps：和传统 MLOps 有什么不同**
LLM 时代很多团队**不再从头训练模型**，而是直接用现成基座模型（base / foundation model）+ API。于是工程重心变了：
- **重点不在训练，在 prompt / RAG / eval / 成本 / 护栏（guardrails）**。
- **Prompt 要当代码管**：prompt 也要版本化、纳入流水线、可回滚——改一句 prompt 可能让效果剧变。
- **Eval 更难也更关键**：输出是开放文本，没有简单的"准确率"，常用 LLM-as-judge、人工评测、离线评测集，eval 集本身也要版本化。
- **成本 / 延迟是一等公民**：按 token 计费，prompt 长度、调用次数、缓存策略直接影响账单。
- **护栏 / 安全**：要防 prompt injection、防有害输出、做内容过滤。
- 微调（fine-tuning）仍存在，但常是 LoRA 等轻量方式，且往往排在 prompt / RAG 之后再考虑。
> 一句话：MLOps 管"模型从无到有再运维"，LLMOps 在**基座现成**的前提下，把 **prompt 和 eval 也纳入版本与流水线**，并把成本 / 护栏顶到前台。

## 面试问答卡

### Q1. What is MLOps? / 什么是 MLOps？
**难度:** 基础
**Answer (EN):**
- MLOps applies DevOps ideas to the whole ML lifecycle: data, training, deployment, and monitoring.
- The goal is to make ML systems automated, repeatable, and traceable, not just a one-off demo.
- It covers things like versioning, experiment tracking, CI/CD, and production monitoring.
**核心答案 (中):**
- MLOps 把 DevOps 思想用到整个 ML 生命周期：数据、训练、部署、监控。
- 目标是让 ML 系统**自动化、可重复、可回溯**，而不是一次性的 demo。
- 涵盖 versioning、experiment tracking、CI/CD、线上监控等。
**追问 / 深入 (中):**
- 追问"和普通 DevOps 比多了什么？" → ML 的输出还依赖**数据和模型**，所以除了代码，还要版本化数据 / 模型，CI 要测数据和指标，监控要盯 data drift。
**常见误区 (中):**
- 以为 MLOps 就是"部署模型"；部署只是其中一环，它是覆盖整个生命周期的工程实践。

### Q2. Why must you version data and models, not just code? / 为什么不只版本化代码，还要版本化数据和模型？
**难度:** 基础
**Answer (EN):**
- In ML, the result depends on code, data, config, and the trained model together.
- If you only version code, you still cannot reproduce a past result when the data changed.
- So to reproduce an experiment you need to lock all four: code, data, model, and config.
**核心答案 (中):**
- ML 的结果由**代码 + 数据 + 配置 + 训出的模型**共同决定。
- 只版本化代码不够：数据一变，结果就变，还是复现不出来。
- 要复现一次实验，必须同时锁定这四样。
**追问 / 深入 (中):**
- 追问"数据那么大怎么版本化？" → 一般不复制整份数据，而是记录数据的**快照 / 引用 / 哈希**（如数据版本工具或对象存储里的版本号），代码里只存指针。
**常见误区 (中):**
- 以为 git 提交代码就能复现实验；数据和模型权重通常不进 git，得用专门的版本化手段。

### Q3. What is experiment tracking and why does it matter? / 什么是 experiment tracking？为什么重要？
**难度:** 进阶
**Answer (EN):**
- Experiment tracking records each run's hyperparameters, metrics, artifacts, and the code/data version it used.
- It lets you compare many runs and pick the best one, instead of trusting memory or a spreadsheet.
- It also makes a good run reproducible, because everything that produced it is logged.
**核心答案 (中):**
- experiment tracking 记录每次实验的**超参、指标、产物（artifact）、对应代码 / 数据版本**。
- 让你能横向对比几十次实验、挑出最好的，而不是靠脑子或 Excel。
- 也让好的实验**可复现**，因为产生它的所有信息都被记下来了。
**追问 / 深入 (中):**
- 追问"和 versioning 什么关系？" → tracking 是"记录每次跑了什么、结果如何"；versioning 是"锁定代码 / 数据 / 模型的具体版本"。tracking 往往**引用** version，二者配合才能真正复现。
**常见误区 (中):**
- 把 tracking 当成只是存指标；它还要把指标和**具体的代码 / 数据 / 配置版本**绑起来才有意义。

### Q4. What is the difference between shadow, canary, and A/B deployment? / shadow、canary、A/B 部署有什么区别？
**难度:** 进阶
**Answer (EN):**
- Shadow: the new model gets the same live traffic as the old one, but its output is **not** returned to users — it is only logged and compared. Zero user risk.
- Canary: route a **small share** of real traffic (e.g. 5%) to the new model, watch the metrics, then ramp up slowly.
- A/B test: split traffic into two groups, one per model, and compare **business metrics** to decide which is better.
**核心答案 (中):**
- **shadow（影子）**：新模型和老模型收同样的线上流量，但结果**不返回给用户**，只记录 / 对比。对用户零风险，用来验证。
- **canary（金丝雀）**：先把**一小部分**真实流量（如 5%）切给新模型，盯指标没问题再逐步放量。
- **A/B test**：流量分两组分别走新 / 老模型，用**业务指标统计对比**谁更好。
**追问 / 深入 (中):**
- 追问"什么时候用哪个？" → 想零风险纯验证用 shadow；想小步上线、随时回滚用 canary；想科学判定"哪个对业务更好"用 A/B（要够样本量和统计显著）。
**常见误区 (中):**
- 把 shadow 和 canary 搞反：shadow 的结果**不给用户**，canary 是**真给一小部分用户**。
- 以为 A/B 只是"切流量"；它核心是**统计对比业务指标**做决策，不只是技术验证。

### Q5. How does LLMOps differ from traditional MLOps? / LLMOps 和传统 MLOps 有什么不同？
**难度:** 高阶
**Answer (EN):**
- Many teams no longer train from scratch; they use a ready-made base model plus an API.
- So the focus shifts from training to prompt, RAG, eval, cost, and guardrails.
- Prompts must be treated like code: versioned, put in the pipeline, and rollback-able.
- Eval is harder because output is open text — teams use LLM-as-judge, human review, and versioned eval sets.
- Cost and latency become first-class, since you pay per token.
**核心答案 (中):**
- 很多团队**不再从头训练**，而是用现成基座模型 + API。
- 工程重心从训练挪到 **prompt / RAG / eval / 成本 / 护栏（guardrails）**。
- **prompt 要当代码管**：版本化、进流水线、可回滚（改一句话效果就可能剧变）。
- **eval 更难**：输出是开放文本，没有简单准确率，常用 LLM-as-judge、人工评测、版本化的 eval 集。
- **成本 / 延迟变成一等公民**，因为按 token 计费。
**追问 / 深入 (中):**
- 追问"那 LLMOps 还需要 versioning 吗？" → 需要，而且范围更广：除了代码 / 数据 / 模型，还要把 **prompt 和 eval 集**也版本化，才能在换模型或改 prompt 后做可靠对比。
- 追问"为什么 prompt 也要进 CI/CD？" → prompt 改动像代码改动一样能直接改变线上行为，要有评测门槛和回滚，否则上线即翻车。
**常见误区 (中):**
- 以为用了大模型就不用 MLOps 了；其实监控、版本化、CI/CD 仍在，只是对象变成了 prompt / RAG / eval。
- 把 LLMOps 等同于"调 prompt"；它是一整套运维实践，prompt 只是其中一块。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "MLOps brings DevOps to the whole ML lifecycle, so the system is automated, repeatable, and traceable."
  (中) MLOps 把 DevOps 用到整个 ML 生命周期，让系统自动化、可重复、可回溯。
- (EN) "To reproduce a result you must version four things: code, data, model, and config."
  (中) 要复现结果，得版本化四样：代码、数据、模型、配置。
- (EN) "Experiment tracking logs every run's hyperparameters and metrics, tied to the exact code and data version."
  (中) experiment tracking 记录每次跑的超参和指标，并绑定具体的代码 / 数据版本。
- (EN) "For deployment: shadow validates with no user risk, canary sends a small slice of real traffic, A/B compares business metrics."
  (中) 部署上：shadow 零风险验证，canary 切一小股真实流量，A/B 比业务指标。
- (EN) "LLMOps uses ready-made base models, so the focus moves to prompt, RAG, eval, cost, and guardrails — and prompts are versioned like code."
  (中) LLMOps 用现成基座模型，重心移到 prompt、RAG、eval、成本、护栏——prompt 像代码一样版本化。

## 延伸阅读
- *Hidden Technical Debt in Machine Learning Systems*（Sculley et al., 2015）—— 经典论文，讲 ML 系统里"模型只是一小块"的工程债务。
- *Machine Learning Operations (MLOps): Overview, Definition, and Architecture*（Kreuzberger et al.）—— MLOps 概念 / 原则综述（⚠️待核实：作者 / 年份以原文为准）。
- 各 MLOps / LLMOps 平台官方文档（如 MLflow、Weights & Biases、LangSmith 等）—— 具体功能 / 接口以官方文档为准（⚠️待核实）。
