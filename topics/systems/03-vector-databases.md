---
topic: 向量数据库
domain: systems
difficulty: 基础
status: drafted
prerequisites: [tokenization-embeddings]
tags: [vector-database, ANN, HNSW, embeddings, similarity-search]
---

# 向量数据库

## 一句话概览
> 向量数据库专门存 embedding 向量并做"按相似度找最近的几个"的检索，是 RAG 等应用里"根据语义找相关内容"的底层引擎。

## 概念讲解

**1. 为什么需要它**
文本、图片这些内容先被模型转成 embedding——一个高维向量（比如 768 维、1536 维），语义相近的内容向量也相近。要做"语义检索"（找意思最像的内容），就得在海量向量里快速找到离查询向量最近的几个。普通数据库擅长精确匹配（等于、范围），但不擅长"高维空间里找最近邻"。向量数据库就是为这件事造的：**存 embedding + 高效相似度检索**。RAG 的"检索"那一步，基本就是它在干活。

**2. 相似度怎么衡量**
"近"要有个度量。常见三种：
- **cosine similarity（余弦相似度）**：看两个向量的**夹角**，只关心方向不关心长度，文本 embedding 最常用。
- **dot product（点积）**：方向和长度都算进去。如果向量已经归一化（长度为 1），点积和 cosine 等价。
- **L2 / Euclidean distance（欧氏距离）**：两点之间的直线距离，越小越近。

选哪个通常要和当初训练 embedding 模型时用的度量一致。

**3. 为什么用 ANN 而不是精确最近邻**
精确最近邻（exact nearest neighbor）要把查询向量和库里**每一个**向量都比一遍，复杂度 O(N)。库里有上千万、上亿向量时，每次查询都全量扫一遍太慢、太贵。

所以实际用 **ANN（approximate nearest neighbor，近似最近邻）**：**牺牲一点准确率，换大幅提速**。它不保证一定找到最近的那几个，但绝大多数时候找到的结果足够好，而速度可能快几个数量级。准确率用 **recall** 衡量（找回的结果里有多少是真正的 top-k）。

**4. 索引算法的直觉**
ANN 靠"索引"提前组织好向量，查询时只看一小部分候选。三类主流思路：

- **HNSW（图索引）**：把向量连成一张"小世界"图，相近的向量互为邻居，还分多层（上层稀疏、下层密集）。查询时从上层入口出发，**像导航一样一步步跳到离查询更近的节点**，很快收敛到目标附近。查询快、recall 高，但**内存占用大**（要存图结构）。
- **IVF（倒排 + 聚类）**：先把所有向量**聚成很多簇**（类似先分区）。查询时只在离查询最近的几个簇里找，跳过其余的。靠参数控制看几个簇（看得多→准但慢，看得少→快但可能漏）。
- **PQ（Product Quantization，乘积量化）**：一种**压缩**手段。把高维向量切成几段，每段用一个"码本"里的近似值代替，于是一个向量能用很少的字节表示。**省内存、加速距离计算**，代价是精度有损。常和 IVF 组合（如 IVF-PQ）。

记忆：**HNSW 用图、IVF 用聚类、PQ 是压缩**，后两者常组合。

**5. 三个权衡（accuracy / speed / memory）**
ANN 索引本质是在三者间取舍：
- **recall（准确率）↑** 一般要么更慢、要么更费内存。
- **speed（速度）↑** 常以 recall 或内存为代价。
- **memory（内存）↓**（如用 PQ 压缩）通常牺牲一点 recall。

调参（如 HNSW 的 `ef_search`、IVF 看几个簇 `nprobe`）就是在这个三角里找平衡点。

**6. metadata filtering（元数据过滤）**
真实场景里光"语义最像"不够，常要叠加结构化条件，比如"只在**用户 A**、**2024 年之后**、**category=docs** 的文档里做相似度检索"。这就是 metadata filtering：每条向量带上标签/字段，检索时既按向量相似度排序，又按 metadata 过滤。怎么把过滤和 ANN 高效结合（先过滤还是先检索）是各产品的工程难点之一。

**7. 常见产品定位**
> 以下为各产品**大致定位**；具体功能/性能/限制随版本变化快，未逐条核实，使用前请查官方文档。⚠️待核实（截至 2026-06）

- **FAISS**：Meta 开源的相似度检索**库**（不是完整数据库），算法丰富、性能强，常被别的系统当底层引擎。要自己管持久化、服务化。
- **pgvector**：给 PostgreSQL 加向量类型和索引的**扩展**。最大优点是**和已有 Postgres 数据/事务/SQL 一起用**，适合不想单独运维一套向量系统的团队。
- **Pinecone**：托管（managed）向量数据库服务，主打开箱即用、不用自己运维。
- **Weaviate**：开源向量数据库，强调内置向量化、混合检索等特性。
- **Milvus**：开源、面向大规模的向量数据库，强调可扩展性。

> 选型直觉：已有 Postgres、规模不大 → pgvector；想要自己控算法/嵌进自己系统 → FAISS；不想运维、要托管 → Pinecone；要开源 + 较大规模/功能 → Weaviate / Milvus。

## 面试问答卡

### Q1. What is a vector database and why do we need one? / 什么是向量数据库？为什么需要它？
**难度:** 基础
**Answer (EN):**
- A vector database stores embeddings (high-dimensional vectors) and finds the most similar ones to a query vector.
- We need it for semantic search: finding content by meaning, not exact keywords.
- It is the engine behind the "retrieval" step in RAG.
**核心答案 (中):**
- 向量数据库存 embedding（高维向量），并能找出和查询向量最相似的几个。
- 它支撑语义检索：按"意思"找内容，而不是精确关键词。
- 它是 RAG 里"检索"那一步的底层引擎。
**追问 / 深入 (中):**
- 追问"普通数据库不行吗？" → 普通数据库擅长精确匹配和范围查询，不擅长"高维空间里找最近邻"；向量数据库专门为相似度检索优化。
**常见误区 (中):**
- 以为向量数据库自己会算 embedding；多数情况下 embedding 由外部模型算好再存进去（部分产品可内置向量化，属可选功能）。

### Q2. What similarity metrics are used, and how do you choose? / 相似度怎么衡量？怎么选度量？
**难度:** 基础
**Answer (EN):**
- Common metrics: cosine similarity, dot product, and L2 (Euclidean) distance.
- Cosine looks at the angle (direction only); L2 looks at straight-line distance.
- If vectors are normalized, dot product and cosine give the same ranking.
- Pick the metric that matches how the embedding model was trained.
**核心答案 (中):**
- 常见三种：cosine similarity、dot product、L2（欧氏距离）。
- cosine 看夹角（只看方向）；L2 看直线距离。
- 向量归一化后，dot product 和 cosine 的排序结果一致。
- 选哪个要和 embedding 模型训练时用的度量保持一致。
**追问 / 深入 (中):**
- 追问"文本检索一般用哪个？" → 文本 embedding 多用 cosine，因为更关心语义方向、不关心向量长度。
**常见误区 (中):**
- 以为度量随便选都行；和训练时不一致会让"相近"的判断失真，检索质量下降。

### Q3. Why use approximate nearest neighbor (ANN) instead of exact search? / 为什么用 ANN（近似最近邻）而不是精确最近邻？
**难度:** 基础
**Answer (EN):**
- Exact search compares the query to every vector — O(N) — which is too slow at large scale.
- ANN trades a little accuracy for a big speedup, often orders of magnitude faster.
- We measure how good it is with recall: how many of the true top-k it finds.
**核心答案 (中):**
- 精确检索要和库里每个向量都比，O(N)，规模大时太慢。
- ANN 牺牲一点准确率换大幅提速，常快几个数量级。
- 好坏用 recall 衡量：找回的结果里有多少是真正的 top-k。
**追问 / 深入 (中):**
- 追问"那 ANN 会漏掉真正最近的吗？" → 会，它不保证；但绝大多数场景下结果够用，且可调参数提高 recall（代价是变慢或更费内存）。
**常见误区 (中):**
- 把"近似"理解成"质量差"；其实在合理调参下 recall 可以很高，近似只是不做 100% 保证。

### Q4. Give the intuition behind HNSW, IVF, and PQ. / 直觉上讲讲 HNSW、IVF、PQ。
**难度:** 进阶
**Answer (EN):**
- HNSW: a multi-layer graph where similar vectors are neighbors; search "navigates" the graph toward the query. Fast and high recall, but uses a lot of memory.
- IVF: cluster all vectors first, then only search the few clusters nearest the query. Skips most of the data.
- PQ (product quantization): a compression trick — split a vector into parts and store cheap approximations, saving memory and speeding up distance math, at some accuracy cost.
- IVF and PQ are often combined (IVF-PQ).
**核心答案 (中):**
- HNSW：多层图，相近向量互为邻居，查询时"沿图导航"向查询靠近。快、recall 高，但很费内存。
- IVF：先把向量聚成簇，查询只看离查询最近的几个簇，跳过其余。
- PQ（乘积量化）：压缩手段——把向量切段、用近似值代替，省内存、加速距离计算，代价是精度有损。
- IVF 和 PQ 常组合使用（IVF-PQ）。
**追问 / 深入 (中):**
- 追问"HNSW 为什么 recall 高还流行？" → 图导航能很快收敛到查询附近，查询快且 recall 高；主要代价是内存大、构建索引慢。
**常见误区 (中):**
- 把三者当成同一层的并列选项；其实 HNSW/IVF 是"怎么找候选"，PQ 是"怎么压缩存储"，可以叠加。

### Q5. Explain the accuracy / speed / memory tradeoff, and what metadata filtering is. / 讲讲精度 / 速度 / 内存的权衡，以及什么是 metadata filtering。
**难度:** 进阶
**Answer (EN):**
- ANN indexes trade off three things: recall (accuracy), query speed, and memory.
- Higher recall usually means slower queries or more memory; compression (like PQ) saves memory but lowers recall.
- Tuning knobs (e.g. HNSW ef_search, IVF nprobe) move you around this triangle.
- Metadata filtering: each vector carries fields (user, date, category), so you can do similarity search only within rows that match the filter.
**核心答案 (中):**
- ANN 索引在三者间权衡：recall（精度）、查询速度、内存。
- recall 高通常更慢或更费内存；用 PQ 压缩省内存但 recall 会降。
- 调参（如 HNSW 的 ef_search、IVF 的 nprobe）就是在这个三角里挪位置。
- metadata filtering：每条向量带字段（用户、时间、类别），检索时只在满足过滤条件的范围内做相似度搜索。
**追问 / 深入 (中):**
- 追问"过滤和 ANN 怎么结合？" → 难点在"先过滤还是先检索"：先过滤可能破坏索引结构，先检索再过滤可能候选不够；不同产品的工程做法不同，是个常见难点。
**常见误区 (中):**
- 以为加了 metadata 过滤就一定更快；过滤和 ANN 索引结合不好时反而可能变慢或漏召回。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "A vector database stores embeddings and finds the most similar ones to a query — it powers the retrieval step in RAG."
  (中) 向量数据库存 embedding，找出和查询最像的几个——它支撑 RAG 的检索那一步。
- (EN) "Common similarity metrics are cosine, dot product, and L2. Pick the one the embedding model was trained with."
  (中) 常用度量是 cosine、dot product、L2；选 embedding 模型训练时用的那个。
- (EN) "Exact search is O(N), too slow at scale, so we use ANN: trade a little accuracy for a big speedup, measured by recall."
  (中) 精确检索是 O(N)，规模大太慢，所以用 ANN：牺牲一点精度换大提速，用 recall 衡量。
- (EN) "HNSW is a graph, IVF clusters the vectors, and PQ compresses them — IVF and PQ are often combined."
  (中) HNSW 是图、IVF 做聚类、PQ 做压缩——IVF 和 PQ 常组合。
- (EN) "It is always a tradeoff between accuracy, speed, and memory; tuning knobs move you around that triangle."
  (中) 永远是在精度、速度、内存之间权衡；调参就是在这个三角里挪位置。
- (EN) "Metadata filtering lets you do similarity search only within rows that match fields like user or date."
  (中) metadata filtering 让你只在满足字段（如用户、时间）的数据里做相似度检索。

## 延伸阅读
- *Efficient and robust approximate nearest neighbor search using HNSW graphs*（Malkov & Yashunin）—— HNSW 原论文。
- *Product Quantization for Nearest Neighbor Search*（Jégou et al.）—— PQ 原论文。
- FAISS 官方文档/wiki —— 各索引（IVF、PQ、HNSW）的工程实现与参数（⚠️待核实，使用前查最新版）。
- pgvector / Pinecone / Weaviate / Milvus 官方文档 —— 各产品功能与限制（⚠️待核实，随版本变化）。
