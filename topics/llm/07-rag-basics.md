---
topic: RAG 基础
domain: llm
difficulty: 基础
status: drafted
prerequisites: [tokenization-embeddings]
tags: [RAG, retrieval, embeddings, vector-search, chunking]
---

# RAG 基础

## 一句话概览
> RAG（Retrieval-Augmented Generation）让模型在回答前**先去外部知识库检索相关内容**，再把检索到的内容拼进 prompt 一起生成——这样模型能用到训练时没见过的、私有的或最新的知识，并且答案可溯源。

## 概念讲解

**1. 直觉**
LLM 的知识"冻"在训练数据里：训练截止之后的事、公司内部文档、你昨天写的笔记，它都不知道。直接问，它要么答不出，要么**编一个看起来很像的答案（hallucination）**。
RAG 的思路像"开卷考试"：答题前先去资料库里**翻出相关的几页**，把这几页放在面前，再照着它回答。模型不用把所有知识背进参数里，而是**临时查、临时用**。

**2. 为什么需要 RAG**
- **知识 cutoff**：模型训练有截止时间，之后的新知识它没有；RAG 可以接最新数据。
- **私有 / 领域数据**：公司文档、产品手册、个人笔记不在训练集里，RAG 让模型能用上。
- **减少 hallucination**：给模型真实出处当依据，比让它"凭记忆瞎编"更可靠。
- **可溯源（attribution）**：答案能附上来自哪篇文档、哪一段，方便核对和建立信任。
- **更新便宜**：知识更新只要改知识库 / 重新索引，不用重新训练模型。

**3. 基本流程：retrieve → augment → generate**
1. **retrieve（检索）**：根据用户问题，从知识库里找出最相关的若干段内容。
2. **augment（增强）**：把这些内容拼进 prompt，作为"上下文 / context"喂给模型。
3. **generate（生成）**：模型基于"问题 + 检索到的内容"生成答案。

**4. 离线 indexing（建索引，提前做一次）**
这一步把你的文档变成"可检索"的形式，通常离线批量跑：
- **chunking（切块）**：把长文档切成小段（chunk），因为整篇太长、检索粒度也太粗。
- **embedding（向量化）**：用 embedding 模型把每个 chunk 变成一个向量（一串数字），向量表示这段文字的"语义"。
- **存向量库（vector store / vector DB）**：把"chunk 文本 + 它的向量"存进向量数据库，建好索引方便快速查相似向量。

**5. 在线 query（用户提问时实时做）**
- **query embedding**：用**同一个** embedding 模型把用户问题也变成向量。
- **相似度检索 top-k**：在向量库里找和问题向量最相似的 k 个 chunk（常用 cosine similarity 等度量）。
- **拼进 prompt**：把这 top-k 个 chunk 和问题一起组织成 prompt。
- **生成**：模型读着这些 context 回答。

**6. chunking 的直觉与影响**
切块大小是个权衡：
- **块太大**：一个 chunk 塞进太多内容，向量"语义被稀释"，检索不准；还占 context 长度。
- **块太小**：单块信息不完整，可能把一句话/一个概念切断，检索到也讲不清楚。
- 常见做法是**按语义边界切（段落、标题）**并让相邻块**有重叠（overlap）**，避免边界处的信息被切散。具体多大合适要看文档和场景，需要实验调。

**7. RAG vs fine-tuning：什么时候用哪个**
- **RAG**：擅长"**注入知识 / 事实**"，尤其是**经常变、量大、要溯源**的知识（文档问答、知识库、最新资料）。改知识只改库，不动模型。
- **fine-tuning**：擅长"**改风格 / 格式 / 行为**"，或让模型稳定掌握某种任务套路、固定输出格式、特定语气。
- 经验法则：缺**知识**先上 RAG；要改**行为/风格**才考虑 fine-tuning；两者也可以结合。

## 面试问答卡

### Q1. What is RAG and why do we use it? / 什么是 RAG？为什么要用它？
**难度:** 基础
**Answer (EN):**
- RAG means Retrieval-Augmented Generation.
- Before answering, the model first retrieves relevant text from an external knowledge base, then puts it into the prompt and generates the answer.
- We use it to give the model new, private, or up-to-date knowledge, to reduce hallucination, and to make answers traceable to a source.
**核心答案 (中):**
- RAG = Retrieval-Augmented Generation（检索增强生成）。
- 回答前先从外部知识库检索相关内容，拼进 prompt 再生成。
- 用它来补充模型没有的新知识 / 私有知识，减少 hallucination，并让答案可溯源。
**追问 / 深入 (中):**
- 追问"为什么不直接把知识塞进训练？" → 知识常变、量大，重训昂贵；RAG 只改知识库就能更新，还能给出处。
- 可一句英文示范："With RAG we just update the knowledge base, no retraining."
**常见误区 (中):**
- 以为 RAG 会"修改模型权重"；它不动模型，只是在 prompt 里临时加内容。
- 以为 RAG 能完全消除 hallucination；它只是**降低**，检索错了或上下文不全照样会编。

### Q2. What are the three steps of RAG? / RAG 的三个基本步骤是什么？
**难度:** 基础
**Answer (EN):**
- Retrieve: find the most relevant chunks from the knowledge base for the user's question.
- Augment: put those chunks into the prompt as context.
- Generate: let the model answer using the question plus the retrieved context.
**核心答案 (中):**
- retrieve：根据问题，从知识库找出最相关的若干 chunk。
- augment：把这些 chunk 作为 context 拼进 prompt。
- generate：模型基于"问题 + 检索内容"生成答案。
**追问 / 深入 (中):**
- 追问"检索是怎么做的？" → 把问题也转成向量，在向量库里找最相似的 top-k chunk（语义检索）。
**常见误区 (中):**
- 把"检索"理解成关键词全文搜索；现代 RAG 多用 embedding 做**语义相似度**检索（也可和关键词混合）。

### Q3. What happens offline when building the index vs. online at query time? / 离线建索引和在线查询时分别发生了什么？
**难度:** 基础
**Answer (EN):**
- Offline (indexing, done once): split documents into chunks, turn each chunk into an embedding, and store them in a vector store.
- Online (query time): embed the user's question with the same model, search for the top-k most similar chunks, put them into the prompt, and generate.
- The key point: documents and the query must use the same embedding model so the vectors live in the same space.
**核心答案 (中):**
- 离线（indexing，做一次）：文档切块 → 每块做 embedding → 存进向量库。
- 在线（query 时）：用**同一个** embedding 模型把问题向量化 → 检索 top-k 相似 chunk → 拼进 prompt → 生成。
- 关键：文档和问题要用**同一个 embedding 模型**，向量才在同一个空间里可比。
**追问 / 深入 (中):**
- 追问"为什么 indexing 放离线？" → 切块和 embedding 算一次就能反复用，放离线省在线延迟；只有问题向量化和检索是实时的。
**常见误区 (中):**
- 文档用一个 embedding 模型、问题用另一个 → 向量不在同一空间，检索基本失效。

### Q4. Why do we chunk documents, and how does chunk size affect retrieval? / 为什么要对文档做 chunking？chunk 大小怎么影响检索？
**难度:** 进阶
**Answer (EN):**
- We chunk because whole documents are too long for the prompt and too coarse to retrieve precisely.
- Chunks that are too large dilute the meaning of the embedding and waste context length.
- Chunks that are too small may cut an idea in half, so a single chunk is not self-contained.
- A common practice is to split on semantic boundaries (paragraphs, headings) with some overlap between chunks.
**核心答案 (中):**
- 切块因为整篇文档太长（放不进 prompt）、粒度也太粗（检索不准）。
- 块太大：embedding 语义被稀释，还浪费 context。
- 块太小：一个想法被切断，单块不自包含。
- 常见做法：按语义边界（段落 / 标题）切，并让相邻块有 overlap。
**追问 / 深入 (中):**
- 追问"overlap 有什么用？" → 防止关键信息正好落在两块交界被切散，重叠能让边界信息在某块里完整出现。
- 追问"块多大合适？" → 没有万能值，取决于文档和场景，要实验调 ⚠️待核实（具体 token 数视 embedding 模型和数据而定）。
**常见误区 (中):**
- 以为块越小检索越准；太小会丢上下文，反而答不全，是个权衡。

### Q5. How does similarity search find the right chunks? / 相似度检索是怎么找到相关 chunk 的？
**难度:** 进阶
**Answer (EN):**
- Each chunk is stored as an embedding vector that captures its meaning.
- The query is turned into a vector with the same model.
- We compute similarity (often cosine similarity) between the query vector and chunk vectors, and return the top-k closest ones.
- "Similar" here means close in meaning, not just matching words.
**核心答案 (中):**
- 每个 chunk 存成一个表示语义的 embedding 向量。
- 问题用同一个模型转成向量。
- 计算问题向量和各 chunk 向量的相似度（常用 cosine similarity），取最近的 top-k。
- 这里的"相似"是**语义相近**，不只是字面匹配。
**追问 / 深入 (中):**
- 追问"k 怎么选？" → k 太小可能漏关键内容，k 太大塞太多噪音还占 context，需要权衡和实验。
- 追问"向量库怎么做到快？" → 用 ANN（approximate nearest neighbor）索引近似检索，不必和每个向量精确比对。
**常见误区 (中):**
- 以为语义检索一定优于关键词；遇到精确名词 / 代号时关键词反而更准，实务常用 hybrid（语义 + 关键词）。

### Q6. When should you use RAG vs. fine-tuning? / 什么时候用 RAG，什么时候用 fine-tuning？
**难度:** 高阶
**Answer (EN):**
- Use RAG to add knowledge or facts, especially when the knowledge changes often, is large, or needs a source.
- Use fine-tuning to change style, format, or behavior — to make the model follow a fixed pattern or tone.
- Rule of thumb: if the model lacks knowledge, try RAG first; if you need to change behavior, consider fine-tuning. They can also be combined.
**核心答案 (中):**
- RAG：注入**知识 / 事实**，尤其是**常变、量大、要溯源**的知识。
- fine-tuning：改**风格 / 格式 / 行为**，让模型稳定遵循某种套路或语气。
- 经验法则：缺**知识**先上 RAG；要改**行为**才考虑 fine-tuning；二者可结合。
**追问 / 深入 (中):**
- 追问"知识更新频繁选哪个？" → 选 RAG，改库即可；fine-tuning 每次更新都要重新训练，成本高。
- 追问"能不能都用？" → 可以：fine-tuning 定行为/格式，RAG 供实时知识，常见组合。
**常见误区 (中):**
- 以为 fine-tuning 能"教会模型新事实"且可靠记住；它更擅长改行为，灌入大量事实易遗忘且更新麻烦。
- 把两者当二选一；很多生产系统是两者结合。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "RAG means the model retrieves relevant text first, then generates the answer using it — like an open-book exam."
  (中) RAG 就是模型先检索相关内容，再据此生成答案——像开卷考试。
- (EN) "We use it for new, private, or changing knowledge, to reduce hallucination, and to make answers traceable."
  (中) 用它来接新知识 / 私有 / 常变的知识，减少 hallucination，并让答案可溯源。
- (EN) "The flow is retrieve, augment, generate. Offline we chunk, embed, and store; online we embed the query and search top-k."
  (中) 流程是 retrieve、augment、generate。离线切块、embedding、入库；在线把问题向量化并检索 top-k。
- (EN) "Chunk size is a trade-off: too big dilutes meaning, too small loses context, so we split on semantic boundaries with overlap."
  (中) chunk 大小是权衡：太大稀释语义，太小丢上下文，所以按语义边界切并加 overlap。
- (EN) "Use RAG to add knowledge; use fine-tuning to change behavior or style. They can be combined."
  (中) 注入知识用 RAG，改行为 / 风格用 fine-tuning，两者可结合。

## 延伸阅读
- *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*（Lewis et al., 2020）—— RAG 原始论文，提出 retrieve + generate 框架。
- *Dense Passage Retrieval for Open-Domain Question Answering*（Karpukhin et al., 2020）—— 用 dense embedding 做语义检索（DPR）。
- 各向量数据库 / RAG 框架官方文档（如 FAISS、LangChain、LlamaIndex）—— 工程实现与 chunking / 检索参数实践 ⚠️待核实（API 与默认参数随版本变化，使用时查最新文档）。
