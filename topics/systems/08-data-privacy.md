---
topic: 数据与隐私
domain: systems
difficulty: 基础
status: drafted
prerequisites: []
tags: [privacy, PII, data-governance, compliance, security]
---

# 数据与隐私

## 一句话概览
> LLM 应用会大量接触用户数据，"数据与隐私"就是确保这些数据——尤其是 PII（个人可识别信息）——在收集、传输、存储、训练全过程里被合法、安全、最小化地处理，避免泄露和违规。

## 概念讲解

**1. 什么是 PII**
PII（Personally Identifiable Information，个人可识别信息）是能定位到某个具体人的信息。分两类：
- **直接标识符**：姓名、身份证号、手机号、邮箱、银行卡号、人脸等——单独就能认出一个人。
- **间接（准）标识符**：出生日期、邮编、性别等——单独不够，但**组合起来**就能锁定某人。
还有更敏感的一档，常叫 **sensitive data / special category**：健康、种族、宗教、性取向、生物特征等，监管要求更严。

**2. 把数据发给第三方 API 的风险**
很多 LLM 应用直接调云端 API（如各家大模型）。把用户数据塞进 prompt 发出去，要问三件事：
- **是否被用于训练**：供应商会不会拿你的数据再训练模型？（很多企业版/API 默认**不**用于训练，但这是合同/政策问题，**⚠️待核实** 具体供应商当下条款。）
- **是否留存、留多久**：服务端会不会存请求日志，存多久。
- **数据流向哪里**：经过哪些地区/子处理方，是否跨境。
核心结论：**数据一旦离开你的边界，控制权就交给了对方**，所以要看合同（DPA、数据处理协议）和配置（如关闭训练、关闭日志留存）。

**3. PII 检测与脱敏（redaction）**
在数据进入模型前先"洗一遍"：
- **检测（detection）**：用规则（正则匹配邮箱/卡号格式）+ 模型（NER 命名实体识别）找出 PII。
- **脱敏（redaction / masking）**：把找到的 PII 替换掉。常见做法：
  - **删除/打码**：`张三` → `[NAME]`、`138****1234`。
  - **占位符替换 + 还原映射**：替成 `[PERSON_1]`，并在内存里存一张映射表，等模型回答后再换回真实值（这样模型既不接触真名，用户又能看到正常结果）。
  - **假名化（pseudonymization）**：换成假但可逆的代号；**匿名化（anonymization）**：彻底不可逆地去标识。监管上两者待遇不同。

**4. 数据最小化与数据保留（minimization & retention）**
- **最小化（data minimization）**：只收集/只发送**完成任务所必需**的数据，别图省事把整条用户记录都塞进 prompt。
- **保留（retention）**：定义数据存多久、到期自动删；不该留的别留（如 prompt 日志里别长期存原始 PII）。"少存、短存"既降风险也利合规。

**5. 合规（GDPR 等）**
- **GDPR**（欧盟通用数据保护条例）是最常被提到的框架，核心理念：合法依据、最小化、用户对自己数据的权利（如访问、删除/"被遗忘权"）。**⚠️待核实** 具体条款、罚则金额、适用范围请以官方文本/法务为准，面试别背具体数字。
- 其他常见的还有美国加州 **CCPA/CPRA**、医疗领域 **HIPAA** 等；不同地区不同行业要求不一样。**⚠️待核实** 具体适用细节。
- 面试要点不是背法条，而是**展示意识**：知道有合规约束、知道要做最小化/可删除/可审计，遇到细节诚实说"具体条款要查/问法务"。

**6. Prompt 里泄露敏感数据的风险**
- 用户或开发者可能**无意把敏感数据写进 prompt**（如把整份合同、客户名单、密钥粘进去）。
- 风险点：这些内容可能被供应商日志记录、被缓存、甚至（在共享环境下）出现在别人的上下文里。
- 还要小心**system prompt / 上下文里放了密钥或内部数据**，被 prompt injection 诱导吐出来（这块和 security 交界）。

**7. 训练/微调数据的隐私**
模型会"记住"训练数据，带来三类风险：
- **memorization（记忆）**：模型逐字记住了训练集里的稀有片段（如某人的邮箱、一段私密文本），生成时可能原样吐出来。
- **data leakage / extraction（数据提取攻击）**：攻击者通过精心构造的 prompt，把训练数据里的隐私内容"套"出来。
- **membership inference（成员推断攻击）**：攻击者判断"某条具体数据是否在训练集里"。在医疗等场景，"你在这个数据集里"本身就泄露隐私。
缓解方向：训练前清洗去重 PII、限制重复样本、加 differential privacy（差分隐私，**⚠️待核实** 具体参数与效果取决于实现）、对输出做过滤。

**8. on-prem / 自托管 vs API 的隐私权衡**
- **API（云端）**：上手快、省运维，但数据要出门，依赖供应商合同与配置。
- **on-prem / 自托管开源模型**：数据**不出自己的边界**，隐私可控性最高；代价是要自己搞 GPU、运维、模型可能偏弱。
- 折中：有些供应商提供 **VPC 部署 / 私有部署 / 不留存模式**。选型本质是 **隐私可控性 ↔ 成本与能力** 的权衡，按数据敏感度来定。

**9. 访问控制与审计（access control & audit）**
- **访问控制**：谁能看哪些数据，遵循**最小权限（least privilege）**；多租户系统要严格做**租户隔离**，别让 A 用户检索到 B 用户的数据（RAG 系统尤其要注意按权限过滤检索结果）。
- **审计（audit log）**：记录"谁在何时访问/导出了什么数据"，出事能追溯，也是合规要求。

**10. 与 security 的边界（一笔带过）**
隐私（privacy）关注的是"数据该不该被这样用、会不会泄露给不该看的人"；安全（security）关注"系统会不会被攻破"。两者交叉，比如 **prompt injection** 既是安全问题，也可能导致隐私泄露（诱导模型吐出上下文里的敏感数据）。本篇聚焦隐私，攻击面细节见 security 主题。

## 面试问答卡

### Q1. What is PII and why does it matter in LLM apps? / 什么是 PII？在 LLM 应用里为什么重要？
**难度:** 基础
**Answer (EN):**
- PII means Personally Identifiable Information — data that can identify a person, like name, email, phone, ID number.
- Some fields alone identify someone; some (like birth date plus zip code) identify when combined.
- It matters because LLM apps send user data to models and store logs, so PII can leak or be misused, which causes privacy harm and legal risk.
**核心答案 (中):**
- PII 是个人可识别信息：能定位到具体个人的数据，如姓名、邮箱、手机号、身份证号。
- 有的字段单独就能认人；有的（如出生日期 + 邮编）组合起来才能认人。
- 重要是因为 LLM 应用会把用户数据发给模型、还会存日志，PII 可能泄露或被滥用，带来隐私伤害和法律风险。
**追问 / 深入 (中):**
- 追问"哪些算更敏感？" → 健康、种族、宗教、生物特征等属 sensitive / special category，监管要求更严，处理要更谨慎。
**常见误区 (中):**
- 以为只有姓名身份证才是 PII；间接标识符组合起来也能认人，同样要保护。

### Q2. What are the risks of sending user data to a third-party LLM API? / 把用户数据发给第三方 LLM API 有什么风险？
**难度:** 基础
**Answer (EN):**
- Once data leaves your boundary, the provider controls it, not you.
- Three key questions: is my data used for training? is it stored, and for how long? where does it flow (which region, which sub-processors)?
- This is a contract and config issue — check the data processing agreement and turn off training / log retention if possible.
**核心答案 (中):**
- 数据一旦离开你的边界，控制权就归供应商，不归你。
- 三个关键问题：会不会被用于训练？会不会留存、留多久？数据流向哪里（哪个地区、哪些子处理方）？
- 这是合同 + 配置问题——看数据处理协议（DPA），能关训练、关日志留存就关。
**追问 / 深入 (中):**
- 追问"企业版 API 默认会拿数据训练吗？" → 很多企业/API 方案**默认不**用于训练，但这是政策/合同问题，**⚠️待核实** 具体供应商当下条款，别一口咬定。
**常见误区 (中):**
- 以为"调 API 数据就一定安全/一定不被训练"；要看具体合同和配置，不能默认。

### Q3. How do you detect and redact PII before it reaches the model? / 怎么在数据进入模型前检测并脱敏 PII？
**难度:** 进阶
**Answer (EN):**
- Detection: use rules (regex for emails, card numbers) plus a model (NER) to find PII.
- Redaction: replace PII with placeholders like `[NAME]`, or mask it.
- A common pattern: replace with `[PERSON_1]`, keep a mapping in memory, then map back after the model answers — so the model never sees the real value but the user still gets a normal result.
**核心答案 (中):**
- 检测：用规则（正则匹配邮箱、卡号）+ 模型（NER 命名实体识别）找出 PII。
- 脱敏：把 PII 换成 `[NAME]` 这样的占位符，或打码。
- 常见做法：替成 `[PERSON_1]`，内存里存一张映射表，模型答完再换回真实值——模型不接触真名，用户仍得到正常结果。
**追问 / 深入 (中):**
- 追问"假名化和匿名化有啥区别？" → pseudonymization（假名化）可逆、还能还原；anonymization（匿名化）不可逆、彻底去标识，监管上待遇不同（匿名化后常被视为不再是个人数据）。
**常见误区 (中):**
- 以为正则就够了；正则会漏（如不规范写法的姓名），通常要正则 + NER 模型互补，且没有 100% 准确，要有兜底。

### Q4. What is data minimization and retention, and why do they reduce risk? / 什么是数据最小化和数据保留？为什么能降低风险？
**难度:** 进阶
**Answer (EN):**
- Data minimization: only collect and send the data the task really needs; don't dump a full user record into the prompt.
- Retention: define how long data is kept and delete it when it expires; don't keep raw PII in logs forever.
- Less data and shorter storage means a smaller attack surface and easier compliance — you can't leak what you don't hold.
**核心答案 (中):**
- 数据最小化：只收集、只发送任务真正需要的数据，别把整条用户记录塞进 prompt。
- 数据保留：定义数据存多久、到期就删；别在日志里长期存原始 PII。
- 数据少、存得短 = 攻击面小、合规更容易——你没存的东西就泄不出去。
**追问 / 深入 (中):**
- 追问"日志一定要存怎么办？" → 存之前先脱敏/打码、设保留期限到期自动删、加访问控制，别存明文 PII。
**常见误区 (中):**
- 以为"多存点数据以后可能有用"是好事；从隐私/合规看，不必要的留存是负债，不是资产。

### Q5. What privacy risks come from training or fine-tuning on data? / 用数据训练 / 微调会带来哪些隐私风险？
**难度:** 高阶
**Answer (EN):**
- Memorization: the model can memorize rare snippets from training data and output them verbatim later.
- Data extraction: an attacker uses crafted prompts to pull private training data back out.
- Membership inference: an attacker figures out whether a specific record was in the training set — which itself can be sensitive (e.g. medical).
- Mitigations: clean and dedup PII before training, limit repeated samples, consider differential privacy, and filter outputs.
**核心答案 (中):**
- memorization（记忆）：模型记住训练集里的稀有片段，之后可能原样吐出来。
- 数据提取（extraction）：攻击者用精心构造的 prompt 把训练数据里的隐私套出来。
- 成员推断（membership inference）：攻击者判断"某条具体数据是否在训练集里"，这本身就可能泄露隐私（如医疗场景）。
- 缓解：训练前清洗去重 PII、限制重复样本、考虑 differential privacy、对输出做过滤。
**追问 / 深入 (中):**
- 追问"为什么重复样本更危险？" → 同一条数据出现越多次，模型越容易记住它、越容易被原样吐出，所以去重很关键。
- 追问"differential privacy 能彻底解决吗？" → 它用加噪等手段降低单条数据的影响，但有隐私 ↔ 效果的权衡，**⚠️待核实** 具体参数与效果取决于实现，不是银弹。
**常见误区 (中):**
- 以为"模型只学规律不记原文"；实际会 memorize 稀有片段，尤其重复出现的，所以训练数据隐私不能忽视。

### Q6. On-prem / self-hosting vs API — how do you weigh the privacy trade-off? / 自托管 vs 调 API，隐私上怎么权衡？
**难度:** 高阶
**Answer (EN):**
- API (cloud): fast to use, low ops, but data leaves your boundary and you rely on the provider's contract and config.
- On-prem / self-hosted open model: data stays inside your boundary, best privacy control, but you pay in GPUs, ops, and possibly weaker models.
- Middle ground: some providers offer VPC / private deployment / no-retention modes.
- The real choice is privacy control vs cost and capability — decide by how sensitive the data is.
**核心答案 (中):**
- API（云端）：上手快、省运维，但数据要出门，依赖供应商合同与配置。
- on-prem / 自托管开源模型：数据不出自己边界，隐私可控性最高；代价是 GPU、运维成本，模型可能偏弱。
- 折中：有些供应商提供 VPC / 私有部署 / 不留存模式。
- 本质权衡是隐私可控性 ↔ 成本与能力，按数据敏感度来定。
**追问 / 深入 (中):**
- 追问"什么情况下值得自托管？" → 数据极敏感（医疗、金融、政府）、合规要求数据不能出境/出公司，或量大到自托管更省时。
**常见误区 (中):**
- 以为自托管就"绝对安全"；自托管只是把信任从供应商挪回自己，访问控制、审计、运维安全还是得自己做好。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "PII is data that can identify a person, like name, email, or ID. In LLM apps we must protect it across collection, sending, storage, and training."
  (中) PII 是能认出一个人的数据，如姓名、邮箱、身份证。LLM 应用要在收集、传输、存储、训练全程保护它。
- (EN) "When I send data to a third-party API, I ask three things: is it used for training, is it stored and for how long, and where does it flow."
  (中) 把数据发给第三方 API 时，我会问三件事：会不会用于训练、会不会留存留多久、数据流向哪里。
- (EN) "Before data hits the model, I detect PII with regex plus NER, then redact it — often replace with a placeholder and map it back after the answer."
  (中) 数据进模型前，我用正则 + NER 检测 PII，然后脱敏——常用占位符替换，模型答完再换回真实值。
- (EN) "I follow data minimization and short retention: only send what the task needs, and delete data when it expires. You can't leak what you don't hold."
  (中) 我遵循数据最小化和短保留：只发任务需要的，到期就删。你没存的东西就泄不出去。
- (EN) "Training data has privacy risks too — memorization, extraction, and membership inference. So we clean and dedup PII before training."
  (中) 训练数据也有隐私风险——memorization、数据提取、成员推断。所以训练前要清洗和去重 PII。
- (EN) "On-prem keeps data inside your boundary with the best control; API is easier but data leaves. It's a trade-off between privacy and cost."
  (中) 自托管把数据留在自己边界、可控性最好；API 更省事但数据要出门。这是隐私和成本的权衡。

## 延伸阅读
- GDPR 官方文本（欧盟）—— 合法依据、最小化、用户权利的权威来源（**⚠️待核实** 具体条款以官方文本/法务为准）。
- Microsoft Presidio —— 开源 PII 检测与脱敏（detection + redaction）工具，可作工程参考。
- *Extracting Training Data from Large Language Models*（Carlini et al., 2021）—— memorization 与训练数据提取攻击的经典论文。
- *Membership Inference Attacks Against Machine Learning Models*（Shokri et al., 2017）—— 成员推断攻击经典论文。
