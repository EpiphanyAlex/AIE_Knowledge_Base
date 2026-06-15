---
topic: RAG 进阶
domain: llm
difficulty: 进阶
status: drafted
prerequisites: [rag-basics]
tags: [RAG, hybrid-search, reranking, query-rewriting, chunking-strategy, evaluation, RRF, ColPali, vision-rag, late-interaction]
---

# RAG 进阶

## 一句话概览
> 朴素 RAG（embedding 检索 top-k → 塞进 prompt）效果常常不够；进阶 RAG 通过更好的检索（hybrid search + reranking）、更好的 query（rewriting / HyDE）、更好的切块（语义 / 父子块）和系统化评估，把"检索质量"和"生成 faithfulness"显著提上去。

## 概念讲解

朴素 RAG 的常见痛点：单一向量检索召回不全、top-k 里混进无关块、query 和文档用词不匹配、切块切坏了上下文。进阶 RAG 就是围绕这几个环节做优化。可以把整条链路拆成四段来理解：**怎么切（chunking）→ 怎么查（query）→ 怎么找（retrieval）→ 怎么验（evaluation）**。

**1. Hybrid search（混合检索）：dense + sparse 一起用**

- **dense（稠密）检索**：用 embedding 把 query 和文档都变向量，按语义相似度（如 cosine）找。优点是抓"意思相近"，缺点是对**精确关键词 / 专有名词 / 罕见词 / 代码符号**不敏感。
- **sparse（稀疏）检索**：以 **BM25** 为代表的关键词检索（基于词频 TF-IDF 思路）。优点是精确命中关键词，缺点是不懂同义改写。
- **hybrid** = 两路都查，再把分数融合。常见融合法是 **RRF（Reciprocal Rank Fusion，倒数排名融合）**：只看每路给出的**排名**，按 `1/(k+rank)` 求和（k 是平滑常数，工程上常取 **60**），不依赖两套分数量纲是否可比，简单稳健。
- 直觉：dense 管"语义近"，sparse 管"词对上"，互补能同时覆盖两类 query。

**2. Reranking（重排）：先粗召回，再精排 top-k**

- 第一阶段检索（bi-encoder / BM25）为了快，query 和文档**分开编码**，只能做粗略相似度，召回的 top-k 里常有噪声。
- **reranker** 通常是 **cross-encoder**：把 `[query, 文档块]` **拼在一起**喂进模型，直接打一个相关性分数。它能看 query 和块的逐词交互，判别更准，但慢——所以不能对全库跑，只对第一阶段召回的 top-k（如 50~100 条）重排，取重排后的前几条进 prompt。
- 这是典型的 **retrieve-then-rerank** 两阶段：召回求"全"（高 recall），重排求"准"（高 precision）。

**3. Query 侧优化：让查询更好查**

- **query rewriting（查询改写）**：把用户口语化 / 含上下文指代的 query 改写成更适合检索的形式。多轮对话里尤其重要——把"它多少钱？"补全成"iPhone 15 多少钱？"。
- **query expansion（查询扩展）**：生成多个改写 / 同义版本分别检索，再合并结果，提升召回。
- **HyDE（Hypothetical Document Embeddings，假设性文档嵌入）**：先让 LLM 针对 query **编一段"假想答案"**，再用这段假想答案的 embedding 去检索。直觉是：答案和真正的文档块，在 embedding 空间里往往比"问题"更接近文档。代价是多一次 LLM 调用、且假想答案可能跑偏。

**4. Chunking 策略：切得好，检索才好**

- **固定窗口（fixed-size）**：按固定 token 数切，可设 overlap（重叠）防止把句子切断。简单，但可能切碎语义。
- **语义切分（semantic chunking）**：按句子/段落语义边界切（如相邻句 embedding 相似度突降处断开），块内更聚焦。
- **父子块 / 上下文扩展（parent-child / small-to-big）**：用**小块**做检索（精准命中），命中后把它所在的**大块（父块）或邻近上下文**取出来喂给 LLM。这样"检索粒度小、给模型的上下文大"，兼顾命中率和上下文完整。
- 没有万能块大小；要按文档类型和 query 类型调，并配合评估来选。

**5. Metadata filtering（元数据过滤）**

- 给每个块附带结构化元数据（如 `source`、`date`、`author`、`doc_type`、权限标签），检索时先按元数据**硬过滤**，再做向量 / 关键词检索。
- 好处：缩小搜索范围、保证时效（只查最近文档）、做权限隔离（只查用户有权看的）。这是把"语义检索"和"结构化条件"结合的关键工程手段。

**6. 视觉原生 RAG：ColPali（处理图表 / 扫描 PDF）**

- 传统 RAG 先把 PDF 做 **OCR → 抽文本 → 切块 → embedding**，但 OCR 会丢图表数据、切块会切断表格行、文本 embedding 看不懂图——**视觉信息全丢了**。
- **ColPali** 换思路：**直接把每一页当图片**编码（用视觉语言模型如 PaliGemma），每页得到一组 patch 向量；query 也编成若干 token 向量；用 **late interaction（MaxSim）** 打分（沿用 ColBERT 思路）。**完全跳过 OCR**，保留版式、图表、字体、排版。
- 适合**视觉密集**的文档（财报、论文、带图表的 PDF）。代价：每页存多个向量，**存储显著变大**（可用乘积量化 PQ 压缩）。
- （多模态本身见 `13-multimodal`；这里聚焦"用视觉做检索"。）

**7. 多跳 / multi-hop 检索与 agentic RAG（简述）**

- 有些问题一次检索答不了，需要**多跳**：先查到中间事实，再用它去查下一步（如"X 公司 CEO 的母校在哪个城市"——先查 CEO，再查母校，再查城市）。
- **agentic RAG**：把检索当成 LLM 能反复调用的**工具**。模型自己决定是否检索、检索什么、要不要再查一轮、何时停止，可拆解子问题、跨多个数据源。比固定流水线灵活，但更慢、更难控、更贵。

**8. RAG 评估：检索 + 生成两层都要测**

- **检索质量**：看找回来的块对不对。
  - **recall**（召回率）：该被找到的相关块，有多少被找回来了。
  - **precision**（精确率）：找回来的块里，有多少是真相关的。
  - 也常用考虑排名的指标（如 MRR、nDCG，看相关块排得够不够靠前）。
- **生成质量**：看答案本身。
  - **faithfulness / groundedness（忠实度 / 有据性）**：答案是不是**只**基于检索到的内容，有没有"无中生有"地编（hallucination）。
  - **answer relevance（答案相关性）**：答案有没有真正回答用户的问题。
- 工程上常用 RAG 评估框架（如 RAGAS、TruLens 等）来半自动跑这些指标，许多实现用 **LLM-as-a-judge** 来打 faithfulness 这类难以规则化的分。⚠️待核实：具体框架的指标定义、默认实现和默认评判模型随版本变化，集成前请查最新文档。

## 面试问答卡

### Q1. What is hybrid search in RAG and why use it? / RAG 里的 hybrid search 是什么？为什么要用？
**难度:** 基础
**Answer (EN):**
- Hybrid search combines dense (embedding) retrieval with sparse keyword retrieval like BM25.
- Dense search finds text with similar meaning; sparse search nails exact keywords, names, and rare terms.
- They are complementary, so combining them gives better recall than either alone.
- Scores are usually merged, often with Reciprocal Rank Fusion (RRF), which fuses by rank, not raw score.
**核心答案 (中):**
- hybrid search = dense（embedding 语义）检索 + sparse（如 BM25 关键词）检索一起用。
- dense 抓"意思相近"，sparse 抓"精确关键词、专有名词、罕见词"。
- 两者互补，合起来比单用任一个召回更全。
- 分数通常融合，常用 RRF：只按**排名**融合，不依赖两套分数量纲是否可比。
**追问 / 深入 (中):**
- 追问"dense 已经懂语义了，为什么还要 BM25？" → embedding 对精确符号 / 罕见专有名词 / 代码常常不敏感，BM25 能精确命中关键词，补 dense 的短板。
- 追问"两路分数怎么合？" → 最稳的是 RRF（按 `1/(k+rank)` 求和）；也可以加权融合，但要先归一化分数。
**常见误区 (中):**
- 以为"有了 embedding 就不需要关键词检索了"；很多场景 BM25 仍很强，尤其是关键词精确匹配的查询。

### Q2. What is reranking and where does a cross-encoder fit in? / reranking 是什么？cross-encoder 用在哪一步？
**难度:** 进阶
**Answer (EN):**
- Reranking is a second stage: first retrieve many candidates fast, then re-score the top-k more accurately.
- The reranker is usually a cross-encoder: it feeds the query and a document together into one model and outputs a relevance score.
- It is more accurate than bi-encoder retrieval because it sees query-document interaction, but it is slower.
- So we only rerank the top-k (e.g. 50-100) from stage one, then keep the best few for the prompt.
**核心答案 (中):**
- reranking 是第二阶段：先快速召回一批候选，再对 top-k 做更准的重新打分。
- reranker 通常是 cross-encoder：把 query 和文档**拼在一起**送进一个模型，直接输出相关性分数。
- 它能看 query 和文档的逐词交互，比 bi-encoder 召回更准，但慢。
- 所以只对第一阶段的 top-k（如 50~100 条）重排，再取最好的几条进 prompt。
**追问 / 深入 (中):**
- 追问"为什么第一阶段不直接用 cross-encoder？" → cross-encoder 要对每个 (query, 文档) 对都跑一次模型，全库跑太慢；bi-encoder 可以离线把文档编好向量、查询时只比相似度，所以快。
- 追问"retrieve-then-rerank 各自的目标？" → 召回阶段求 recall（别漏），重排阶段求 precision（排得准）。
**常见误区 (中):**
- 把 reranker 和第一阶段的 embedding 模型混为一谈：embedding（bi-encoder）分开编码、求快；reranker（cross-encoder）合并编码、求准。
- 以为 rerank 能"召回"新内容；它只能在第一阶段召回的候选里重排，第一阶段漏了它救不回来。

### Q3. What is HyDE, and how does it differ from plain query rewriting? / HyDE 是什么？和普通的 query rewriting 有什么区别？
**难度:** 进阶
**Answer (EN):**
- Query rewriting reshapes the user's query into a cleaner search query (e.g. resolving "it" in a chat).
- HyDE (Hypothetical Document Embeddings) instead asks an LLM to write a fake answer to the query, then embeds that fake answer and uses it to retrieve.
- The idea: a hypothetical answer sits closer in embedding space to real document chunks than the question does.
- Cost: an extra LLM call, and the fake answer can be wrong and pull retrieval off-topic.
**核心答案 (中):**
- query rewriting：把用户 query 改写成更适合检索的形式（如多轮里把"它"补全成具体对象）。
- HyDE：让 LLM 先**编一段假想答案**，再用这段假想答案的 embedding 去检索。
- 直觉：假想答案在 embedding 空间里通常比"问题"更接近真正的文档块。
- 代价：多一次 LLM 调用；假想答案可能编错，把检索带偏。
**追问 / 深入 (中):**
- 追问"query expansion 又是什么？" → 生成多个改写/同义版本分别检索再合并，目的是提召回；HyDE 可以看成 expansion 的一种特殊形式（用"假答案"扩展）。
- 追问"HyDE 什么时候不适合？" → 模型对该领域不熟、容易胡编时，假想答案会把检索带偏，反而更差。
**常见误区 (中):**
- 以为 HyDE 把假想答案直接当最终回答返回；它只用假想答案去**检索**，最终答案仍要基于检索回来的真实文档生成。

### Q4. How do chunking strategies affect RAG, and what is parent-child chunking? / chunking 策略怎么影响 RAG？什么是父子块？
**难度:** 进阶
**Answer (EN):**
- Chunking decides what unit gets embedded and retrieved, so it strongly affects retrieval quality.
- Fixed-size chunking is simple but can cut sentences or topics in half; overlap helps a bit.
- Semantic chunking splits at meaning boundaries, so each chunk is more focused.
- Parent-child (small-to-big): retrieve with small chunks for precision, then feed the larger parent chunk (or surrounding context) to the LLM for completeness.
**核心答案 (中):**
- chunking 决定"被 embedding 和检索的单位"，直接影响检索质量。
- 固定窗口简单，但可能把句子/话题切断；加 overlap 能缓解。
- 语义切分按意义边界切，块内更聚焦。
- 父子块（small-to-big）：用**小块**检索求精准命中，命中后把**大的父块**（或邻近上下文）喂给 LLM，保证上下文完整。
**追问 / 深入 (中):**
- 追问"块太大或太小各有什么问题？" → 太大：一块里混多个话题，检索不精、还浪费 context；太小：命中精准但上下文不全，模型缺背景。父子块就是为兼顾两者。
- 追问"怎么定块大小？" → 没有万能值，按文档类型和 query 类型试，并用评估指标（如检索 recall）来选。
**常见误区 (中):**
- 以为存在一个"最佳块大小"通用值；它是要随数据和场景调的超参数。

### Q5. How do you evaluate a RAG system? / 怎么评估一个 RAG 系统？
**难度:** 进阶
**Answer (EN):**
- Evaluate two layers separately: retrieval and generation.
- Retrieval: recall (did we find the relevant chunks?) and precision (are the retrieved chunks actually relevant?); ranking metrics like MRR / nDCG also help.
- Generation: faithfulness / groundedness (is the answer supported only by the retrieved context, no made-up facts?) and answer relevance (does it actually answer the question?).
- In practice, frameworks like RAGAS often use an LLM-as-a-judge to score things like faithfulness.
**核心答案 (中):**
- 分两层评：检索层 + 生成层。
- 检索层：recall（相关块找回来了吗）+ precision（找回来的块真相关吗）；也用 MRR / nDCG 这类看排名的指标。
- 生成层：faithfulness / groundedness（答案是否**只**基于检索内容、没编造）+ answer relevance（是否真回答了问题）。
- 工程上常用 RAGAS 等框架，且常用 LLM-as-a-judge 来打 faithfulness 这类难规则化的分。
**追问 / 深入 (中):**
- 追问"答案错了，怎么判断是检索的锅还是生成的锅？" → 分层定位：先看检索层指标——相关块根本没召回，是检索问题；相关块召回了但答案还错/编造，是生成（faithfulness）问题。
- 追问"为什么 faithfulness 单独很重要？" → 它直接对应 hallucination：答案"听起来对"但没有检索依据，正是 RAG 要压制的风险。
**常见误区 (中):**
- 只看最终答案对不对，不分检索/生成两层，导致定位不到问题出在哪。
- 把 answer relevance 和 faithfulness 混淆：相关性看"答没答到点上"，忠实度看"有没有依据、有没有编"。

### Q6. What is agentic / multi-hop RAG, and when do you need it? / 什么是 agentic / multi-hop RAG？什么时候才需要？
**难度:** 高阶
**Answer (EN):**
- Multi-hop means a question needs several retrieval steps: find an intermediate fact, then use it to retrieve the next.
- Agentic RAG treats retrieval as a tool the LLM can call repeatedly: it decides whether to search, what to search, whether to search again, and when to stop.
- Use it for complex, multi-step, or multi-source questions that one-shot retrieval cannot answer.
- Trade-off: more flexible, but slower, harder to control, and more expensive (more LLM calls).
**核心答案 (中):**
- multi-hop：一个问题需要多步检索——先查到中间事实，再用它去查下一步。
- agentic RAG：把检索当成 LLM 能反复调用的**工具**，由模型自己决定是否检索、检索什么、要不要再查、何时停。
- 适用场景：一次检索答不了的复杂、多步、跨数据源问题。
- 权衡：更灵活，但更慢、更难控、更贵（LLM 调用变多）。
**追问 / 深入 (中):**
- 追问"什么时候**不**该上 agentic？" → 简单单跳问答用固定流水线（retrieve → rerank → generate）就够，且更快更稳；agentic 的灵活性是用延迟、成本和不确定性换来的。
- 追问"multi-hop 的主要风险？" → 误差累积：前一跳查错，后面全跑偏；所以每跳的检索质量更关键。
**常见误区 (中):**
- 以为 agentic RAG 总比朴素 RAG 好；它只在问题确实需要多步/多源时才划算，简单场景反而是过度工程。

### Q7. What is vision-native RAG (e.g. ColPali), and when is it better than text RAG? / 什么是视觉原生 RAG（如 ColPali）？什么时候比文本 RAG 好？
**难度:** 高阶
**Answer (EN):**
- Normal RAG runs OCR on a PDF, extracts text, chunks it, and embeds the text — which loses charts, table layout, and figures.
- ColPali instead encodes each page as an image with a vision-language model, getting patch vectors per page; the query becomes token vectors; scoring uses late interaction (MaxSim), the ColBERT pattern.
- It skips OCR entirely and keeps layout, tables, and figures, so it wins on visually-rich documents (financial reports, papers, scanned PDFs).
- Cost: many vectors per page, so storage grows a lot (can be compressed with product quantization).
**核心答案 (中):**
- 普通 RAG 对 PDF 先 OCR、抽文本、切块、embedding，会丢图表、表格版式和插图。
- ColPali 改成**把每页当图片**用视觉语言模型编码，得到每页一组 patch 向量；query 编成 token 向量；用 **late interaction（MaxSim）** 打分（ColBERT 思路）。
- 完全跳过 OCR，保留版式 / 表格 / 图，所以在**视觉密集文档**（财报、论文、扫描件）上更好。
- 代价：每页多个向量，存储显著变大（可用 PQ 压缩）。
**追问 / 深入 (中):**
- 追问"它和普通文本 embedding 检索本质差别？" → 普通是"先把页面转成文本再 embedding 文本"，ColPali 是"直接 embedding 页面图像"，把版式和图表也纳入检索信号。
**常见误区 (中):**
- 以为所有文档都该上视觉 RAG；纯文字文档用文本 RAG 更省更快，ColPali 的价值在**图表 / 版式重要**的文档。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "Naive RAG often isn't enough. Advanced RAG improves four things: how we chunk, how we query, how we retrieve, and how we evaluate."
  (中) 朴素 RAG 常常不够。进阶 RAG 优化四件事：怎么切、怎么查、怎么找、怎么验。
- (EN) "Hybrid search mixes dense embedding search with sparse keyword search like BM25, because one finds meaning and the other finds exact words."
  (中) hybrid search 把 dense 的 embedding 检索和 BM25 这类 sparse 关键词检索混用，因为一个抓语义、一个抓精确词。
- (EN) "Then I rerank: a cross-encoder reads the query and each candidate together and scores them more accurately. It's slow, so I only run it on the top-k."
  (中) 然后我重排：cross-encoder 把 query 和每个候选一起读、打更准的分。它慢，所以只对 top-k 跑。
- (EN) "On the query side, rewriting cleans the query, and HyDE writes a fake answer first and retrieves with that, since an answer is closer to documents than a question."
  (中) query 侧：rewriting 把查询整理干净；HyDE 先编一段假答案再用它检索，因为答案比问题更接近文档。
- (EN) "For chunking, parent-child means retrieve with small chunks for precision, then feed the bigger parent chunk to the model for context."
  (中) chunking 用父子块：小块检索求精准，命中后把大父块喂给模型补上下文。
- (EN) "I evaluate two layers: retrieval with recall and precision, and generation with faithfulness — is the answer grounded in the retrieved context, with nothing made up."
  (中) 我分两层评估：检索看 recall 和 precision，生成看 faithfulness——答案是否有据于检索内容、没有编造。
- (EN) "For documents full of charts and tables, vision-native RAG like ColPali embeds the page image directly instead of OCR-ing it to text."
  (中) 对图表 / 表格多的文档，用 ColPali 这类视觉原生 RAG 直接 embedding 页面图像，而不是 OCR 成文本。

## 延伸阅读
- *Precise Zero-Shot Dense Retrieval without Relevance Labels*（HyDE 原论文，Gao et al., 2022）。
- *Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods*（Cormack et al., 2009）—— RRF 融合原论文。
- *RAGAS: Automated Evaluation of Retrieval Augmented Generation*（Es et al., EACL 2024 demo）—— reference-free 的 RAG 指标（faithfulness、answer relevancy、context precision/recall）；出处已核对，但**具体指标定义与实现随版本更新**，集成前查官方文档（⚠️待核实实现细节）。
- BM25 / Okapi BM25（经典稀疏检索打分函数，可查信息检索教材）。
- *ai-engineering-from-scratch*（rohitg00）Phase 11 `07-advanced-rag` / `10-evaluation`、Phase 12 `23-colpali-vision-native-rag` —— reranking、hybrid+RRF、HyDE、ColPali 视觉检索与 RAG 评估。本次加料与核对依据。
