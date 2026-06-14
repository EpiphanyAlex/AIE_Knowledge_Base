---
topic: Tokenization & Embeddings
domain: llm
difficulty: 基础
status: drafted
prerequisites: []
tags: [tokenization, embeddings, BPE, subword, vocabulary]
---

# Tokenization & Embeddings

## 一句话概览
> Tokenization 把文本切成模型能处理的小单元（token），embedding 再把每个离散 token 映射成连续向量——这是任何文本进入 LLM 之前的两步"翻译"，直接影响成本、上下文长度和语义理解。

## 概念讲解

**1. 直觉：模型不直接读文字**
模型只会算数字，不会直接读 "hello"。所以送进模型前要做两件事：
1. **Tokenization（分词）**：把文本切成一段段小单元，每个单元在词表里有一个整数 ID。
2. **Embedding（嵌入）**：把这些整数 ID 换成一串浮点数向量，模型真正计算的是这些向量。

可以理解成：tokenization 把句子切成"零件"并编号，embedding 给每个零件配一张"含义名片"。

**2. token vs word vs character**
切文本有三种粒度：
- **character（字符）**：词表很小，但序列很长，一个含义被打散，模型难学。
- **word（整词）**：序列短、语义完整，但词表会爆炸（英语词形变化、各种语言），还会遇到没见过的词（OOV，out-of-vocabulary）。
- **token（子词 / subword）**：现代 LLM 的主流折中。常见词当一个 token，生僻词拆成几个有意义的片段。
  - 经验上英文里 **1 个 token ≈ 0.75 个单词 / 约 4 个字符**（粗略经验值，随 tokenizer 和语言变化，⚠️待核实具体比例）。

**3. 为什么用 subword：解决 OOV + 控制词表**
整词分词的死穴是 **OOV**：训练时没见过的词（新词、拼写、专有名词）无法表示。subword 的思路是：
- 把词表固定成一批"高频片段"。
- 任何词都能用这些片段拼出来——常见词一个 token 搞定，没见过的词拆成已知子词（比如 `tokenization` → `token` + `ization`）。
- 这样**几乎不会真正 OOV**，同时词表大小可控（通常几万级别）。

**4. 三种主流 subword 算法（了解差异即可）**
- **BPE（Byte-Pair Encoding）**：从字符开始，反复把"出现最频繁的相邻对"合并成新 token，直到词表达到目标大小。GPT 系列用的就是 BPE 的变体（byte-level BPE）。
- **WordPiece**：思路类似 BPE，但合并时不是按频率，而是按"哪种合并最能提升语言模型似然"来选。BERT 用的是 WordPiece。
- **SentencePiece**：是一个**工具/框架**，直接在原始文本上训练（把空格也当普通字符），不依赖预先按空格分词，对中文、日文等没有空格的语言更友好。它内部可以用 BPE 或 unigram 算法。

**5. vocabulary（词表）**
词表就是"所有 token → 整数 ID"的固定映射表，模型训练前就定好、之后不变。
- 词表大：单条文本 token 数更少（更省），但 embedding 表更大、输出 softmax 更慢。
- 词表小：embedding 表小，但同样文本要更多 token。
- 这是一个工程权衡，常见规模在几万 token。

**6. token 数 ↔ 成本 / 上下文窗口**
LLM 的计费和长度限制都按 **token 数**算，不是按字数：
- **成本**：API 通常按 input tokens + output tokens 收费，token 越多越贵。
- **上下文窗口（context window）**：模型一次最多能处理的 token 总数（prompt + 生成）。超了就放不下，要截断或压缩。
- 含义：同样一段话，不同语言 / 不同 tokenizer 切出的 token 数差别很大（中文、代码、罕见词往往更"费 token"）。

**7. 什么是 embedding**
embedding 是把**离散符号映射到连续向量空间**的一层。模型里有一张 **embedding 矩阵**：词表里每个 token ID 对应一行向量（比如 768 维）。查表（lookup）就能把 token ID 变成向量。
- 这些向量是**训练学出来的**，不是手工设的。
- 训练让**含义相近的 token 在向量空间里靠得近**（距离/夹角小），含义不同的离得远。所以 embedding 携带了"语义"。

**8. token embedding ≠ 句向量 / 文本 embedding**
两个常被混淆的"embedding"，用途不同：
- **token embedding**：LLM **内部**的查表层，针对**单个 token**，是模型前向计算的第一步。
- **句向量 / 文本 embedding（text / sentence embedding）**：把**一整段文本**压成**一个**向量，用于**检索 / 相似度 / 聚类**（如 RAG、语义搜索）。通常由专门的 embedding 模型产出，常做归一化后用 cosine similarity 比较。
- 一句话区分：token embedding 是"模型内部理解每个词"，文本 embedding 是"对外表示整段话用来比对"。

## 面试问答卡

### Q1. What is tokenization and why do LLMs need it? / 什么是 tokenization？为什么 LLM 需要它？
**难度:** 基础
**Answer (EN):**
- Tokenization splits raw text into small units called tokens, each mapped to an integer ID.
- LLMs only work with numbers, so text must be turned into token IDs first.
- These IDs are later turned into vectors (embeddings) that the model actually computes on.
**核心答案 (中):**
- tokenization 把原始文本切成小单元（token），每个 token 在词表里有一个整数 ID。
- LLM 只会算数字，文本必须先变成 token ID。
- 这些 ID 之后再变成向量（embedding），模型真正算的是向量。
**追问 / 深入 (中):**
- 追问"切成什么粒度？" → 现代 LLM 用 subword：常见词一个 token，生僻词拆成片段，平衡词表大小和序列长度。
**常见误区 (中):**
- 以为 1 个 token = 1 个单词；实际一个词可能是多个 token，标点、空格也可能单独算 token。

### Q2. Token vs word vs character — what are the trade-offs? / token、word、character 三种粒度各有什么权衡？
**难度:** 基础
**Answer (EN):**
- Character level: tiny vocabulary, but sequences get very long and meaning is spread out.
- Word level: short sequences and full meaning, but a huge vocabulary and many out-of-vocabulary (OOV) words.
- Subword token level: a middle ground — common words stay whole, rare words split into known pieces.
**核心答案 (中):**
- 字符级：词表很小，但序列很长，含义被打散。
- 整词级：序列短、语义完整，但词表巨大且常遇到 OOV。
- 子词 token 级：折中——常见词整体保留，生僻词拆成已知片段。
**追问 / 深入 (中):**
- 追问"为什么主流选 subword？" → 它同时控制了词表大小、序列长度，并几乎消除 OOV，是工程上的最佳折中。
**常见误区 (中):**
- 以为整词分词最自然最好；它的致命问题是词表爆炸和 OOV。

### Q3. What is the OOV problem and how does subword tokenization solve it? / 什么是 OOV 问题？subword 分词怎么解决它？
**难度:** 基础
**Answer (EN):**
- OOV (out-of-vocabulary) means a word never seen in training, so a word-level model can't represent it.
- Subword tokenization keeps a fixed set of frequent pieces, and any word can be built from those pieces.
- So a new or rare word is split into known subwords instead of being unknown — OOV almost disappears.
**核心答案 (中):**
- OOV（词表外）指训练时没见过的词，整词模型无法表示它。
- subword 把词表固定成一批高频片段，任何词都能用这些片段拼出来。
- 新词 / 生僻词被拆成已知子词，而不是变成"未知"，OOV 几乎消失。
**追问 / 深入 (中):**
- 追问"举个例子？" → 比如 `tokenization` 可拆成 `token` + `ization`；模型没见过整词，但见过这些片段。
**常见误区 (中):**
- 以为 subword 能把任意输入变得有意义；它只是保证"可表示"，拆出的片段不一定语义干净。

### Q4. Compare BPE, WordPiece, and SentencePiece. / 对比一下 BPE、WordPiece、SentencePiece。
**难度:** 进阶
**Answer (EN):**
- BPE starts from characters and repeatedly merges the most frequent adjacent pair until the vocabulary is full. GPT-style models use a byte-level BPE.
- WordPiece is similar, but it merges the pair that most improves the language model likelihood, not just raw frequency. BERT uses WordPiece.
- SentencePiece is a tool that trains directly on raw text (treating spaces as normal characters), so it works well for languages without spaces like Chinese. It can use BPE or unigram inside.
**核心答案 (中):**
- BPE：从字符开始，反复合并"最高频的相邻对"直到词表填满；GPT 系列用 byte-level BPE。
- WordPiece：类似 BPE，但按"哪种合并最能提升语言模型似然"来选，而非纯频率；BERT 用 WordPiece。
- SentencePiece：一个直接在原始文本上训练的工具（把空格也当普通字符），对中文这类没空格的语言友好；内部可用 BPE 或 unigram。
**追问 / 深入 (中):**
- 追问"byte-level 是什么意思？" → 在字节（byte）而非字符上做 BPE，任何 Unicode 字符都能被表示，彻底避免未知字符。
**常见误区 (中):**
- 以为 SentencePiece 是一种算法；它是个框架/工具，里面可以装 BPE 或 unigram 这些算法。
- 把三者当成完全不同的思路；BPE 和 WordPiece 都是"自底向上合并"，差别主要在合并的选择标准。

### Q5. Why do token counts matter for cost and context window? / 为什么 token 数对成本和上下文窗口很重要？
**难度:** 进阶
**Answer (EN):**
- LLM pricing and length limits are counted in tokens, not in words or characters.
- Cost: APIs usually charge per input token plus output token, so more tokens means higher cost.
- Context window: the max number of tokens a model can handle at once (prompt plus generation); going over means truncation.
- The same text can produce very different token counts across languages and tokenizers — Chinese, code, and rare words often cost more tokens.
**核心答案 (中):**
- LLM 的计费和长度限制都按 token 数算，不是按字数或字符数。
- 成本：API 通常按 input token + output token 收费，token 越多越贵。
- 上下文窗口：模型一次能处理的最大 token 数（prompt + 生成），超了就被截断。
- 同样文本在不同语言 / tokenizer 下 token 数差别很大——中文、代码、罕见词往往更费 token。
**追问 / 深入 (中):**
- 追问"怎么估 token 数？" → 英文经验值约 1 token ≈ 4 个字符 / 0.75 个词，但精确值要用对应模型的 tokenizer 实测（⚠️待核实具体比例，随模型而变）。
**常见误区 (中):**
- 以为字数少 token 就一定少；中文、emoji、长数字、代码可能一个字/符号就占多个 token。

### Q6. What is the difference between a token embedding and a text/sentence embedding? / token embedding 和句向量 / 文本 embedding 有什么区别？
**难度:** 进阶
**Answer (EN):**
- A token embedding is the model's internal lookup layer: each token ID maps to a learned vector. It is the first step of the forward pass, per token.
- A text (sentence) embedding compresses a whole piece of text into one vector, used for retrieval, similarity, and clustering (e.g. RAG, semantic search).
- Token embeddings live inside the LLM; text embeddings are an external representation you compare with cosine similarity.
**核心答案 (中):**
- token embedding 是模型内部的查表层：每个 token ID 映射到一个学出来的向量，是前向计算第一步，**针对单个 token**。
- 文本 / 句向量把**整段文本压成一个向量**，用于检索、相似度、聚类（如 RAG、语义搜索）。
- token embedding 在 LLM 内部；文本 embedding 是对外表示，常用 cosine similarity 比较。
**追问 / 深入 (中):**
- 追问"文本 embedding 怎么得到？" → 通常由专门的 embedding 模型产出（不是简单平均 token embedding），常做归一化后比 cosine 相似度。
**常见误区 (中):**
- 以为把 token embedding 取平均就等于句向量；专门的文本 embedding 模型效果通常好很多。
- 混淆两者用途：一个是模型"内部理解词"，一个是"对外表示整段话用来比对"。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "Tokenization splits text into tokens, and each token gets an integer ID, because the model only works with numbers."
  (中) tokenization 把文本切成 token，每个 token 给一个整数 ID，因为模型只会算数字。
- (EN) "Modern LLMs use subword tokens — common words stay whole, rare words split into pieces. This keeps the vocabulary small and almost removes the OOV problem."
  (中) 现代 LLM 用 subword token——常见词整体保留，生僻词拆片段。词表小，还几乎没有 OOV。
- (EN) "BPE, WordPiece, and SentencePiece are the common subword methods. BPE merges frequent pairs; SentencePiece works directly on raw text, good for languages without spaces."
  (中) BPE、WordPiece、SentencePiece 是常见 subword 方法。BPE 合并高频对；SentencePiece 直接在原文上做，适合没空格的语言。
- (EN) "Cost and context limits are counted in tokens, not words, so the same text can cost different tokens in different languages."
  (中) 成本和上下文限制都按 token 数算，不是按字数，所以同样文本在不同语言里 token 数不同。
- (EN) "An embedding maps a discrete token to a continuous vector, and similar meanings sit close together in that space."
  (中) embedding 把离散 token 映射到连续向量，含义相近的在空间里靠得近。
- (EN) "A token embedding is inside the model, per token. A text embedding represents a whole text as one vector for search and retrieval."
  (中) token embedding 在模型内部、针对单个 token；文本 embedding 把整段话表示成一个向量，用于搜索和检索。

## 延伸阅读
- *Neural Machine Translation of Rare Words with Subword Units*（Sennrich et al., 2016）—— 把 BPE 引入 NLP 的原论文。
- SentencePiece（Google 开源库）官方仓库与论文 *SentencePiece: A simple and language independent subword tokenizer*（Kudo & Richardson, 2018）。
- OpenAI tiktoken / Hugging Face `tokenizers` 文档 —— 实际查看不同模型如何切 token、如何估算 token 数（⚠️待核实具体经验比例，建议用对应模型 tokenizer 实测）。
