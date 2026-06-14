---
topic: 多模态
domain: llm
difficulty: 进阶
status: drafted
prerequisites: [tokenization-embeddings]
tags: [multimodal, vision-language, CLIP, VLM, image-encoder]
---

# 多模态

## 一句话概览
> 多模态模型能同时处理多种输入（文本 + 图像 / 音频等），核心做法是把图像这类非文本输入也变成"token / embedding"，对齐到语言模型的表示空间，从而像理解文字一样理解图片。

## 概念讲解

**1. 什么是多模态（multimodal）**
"模态"就是信息的形式：文字是一种模态，图像、音频、视频是另一些模态。**单模态**模型只吃一种输入（如纯文本 LLM）；**多模态**模型能同时吃多种，最常见的是**文本 + 图像**。典型场景：给模型一张图再用文字提问，它用文字回答。

**2. 图像怎么进入模型：vision encoder + patch**
LLM 只会处理 token 序列，而图像是像素网格，得先"翻译"成模型能用的东西。常见流程：
- **切 patch**：把图像切成一个个小方块（patch），例如 16×16 像素一块。
- **vision encoder（如 ViT）**：每个 patch 展平后做线性投影，加上位置信息，送进 Transformer。ViT（Vision Transformer）就是"把图像当成一串 patch token 来跑 Transformer"。
- 输出是一组 patch 的向量表示——可以理解为"图像版的 token embedding"。

类比：文本被切成 token，图像被切成 patch；两者都变成一串向量，再交给 Transformer 处理。

**3. 对齐到语言模型空间：projector**
vision encoder 产出的图像向量，**维度和语义空间**通常和 LLM 的 token embedding 对不上。所以中间加一个**projector（投影模块，也叫 adapter / connector）**，把图像向量映射到 LLM 能直接当输入吃的空间。projector 可以简单到一个线性层 / MLP，也可以更复杂（如 Q-Former 之类的查询模块）。映射后，这些"图像 token"就和文本 token 拼在一起，送进 LLM。

**4. CLIP：图文对比学习**
CLIP（Contrastive Language–Image Pre-training）解决的是另一件事：**让图像和文本落在同一个向量空间**，相关的图文挨得近，不相关的离得远。
- 有两个编码器：一个 image encoder、一个 text encoder。
- 训练用海量"图片 + 配文"对。一个 batch 里，正确配对的图文要相似度高，错误配对要相似度低（这就是 contrastive learning / 对比学习）。
- 训练完后，图像和文本可以直接比相似度 → 支持**图文检索**、**zero-shot 分类**（给一张图和几个文字标签，看哪个标签向量最接近）。

注意：CLIP 本身**不生成文字**，它只做"图文映射 / 比相似度"。很多 VLM 会拿 CLIP 训好的 image encoder 当视觉骨干。

**5. VLM 的大致架构（image encoder + projector + LLM）**
VLM（vision-language model）把"看图"和"说话"接起来，常见三段式：
1. **image encoder**：把图像变成视觉向量（常用 CLIP 系或 ViT 系）。
2. **projector**：把视觉向量对齐到 LLM 的输入空间。
3. **LLM**：把"图像 token + 文本 token"一起当输入，生成文字回答。

训练上常见做法是**冻结**已经训好的 image encoder 和 LLM，**主要训中间的 projector**（再视情况微调 LLM），这样成本低、复用已有能力。⚠️待核实（具体哪些组件冻结 / 解冻、训练阶段划分因模型而异，截至 2026-06 没有统一标准）。

**6. 典型能力与应用**
- **图像问答（VQA, visual question answering）**：看图回答问题。
- **OCR / 看图读字**：识别图里的文字、读图表和文档。
- **图文检索（image-text retrieval）**：用文字搜图、用图搜文（CLIP 类擅长）。
- **图像描述（captioning）**、看图写代码 / 看 UI 截图等。

**7. 局限**
- **幻觉**：会"看见"图里没有的东西，或编造细节。
- **细粒度 / 计数 / 空间关系**弱：数数、精确位置、小物体常出错。
- **分辨率限制**：patch 化后细节可能丢失，密集小字 / 复杂图表容易读错。
- **对齐质量**：projector 没对齐好，视觉信息进不去 LLM，回答就和图脱节。

## 面试问答卡

### Q1. What is a multimodal model? / 什么是多模态模型？
**难度:** 基础
**Answer (EN):**
- A multimodal model can take more than one type of input, such as text plus images (or audio, video).
- The most common case is vision + language: you give an image and ask a question in text, and it answers in text.
- The key idea is to turn non-text inputs into token-like embeddings the model can process.
**核心答案 (中):**
- 多模态模型能接收不止一种输入，比如文本 + 图像（或音频、视频）。
- 最常见是"视觉 + 语言"：给一张图、用文字提问，它用文字回答。
- 核心思想：把非文本输入也变成类似 token 的 embedding，让模型能处理。
**追问 / 深入 (中):**
- 追问"和普通 LLM 差别在哪？" → 普通 LLM 只吃文本 token；多模态模型多了一条"把图像 / 音频变成 embedding"的输入通路，再和文本一起处理。
**常见误区 (中):**
- 以为多模态 = 模型自己长了眼睛；实际是靠一个 vision encoder 把图像编码成向量再喂进去。

### Q2. How does an image get into a language model? / 图像是怎么进入语言模型的？
**难度:** 基础
**Answer (EN):**
- The image is split into small patches (e.g. 16×16 pixels each).
- A vision encoder like ViT turns these patches into a sequence of vectors, like "image tokens".
- A projector maps these vectors into the LLM's input space, so they can sit next to text tokens.
**核心答案 (中):**
- 图像先被切成一个个小 patch（如 16×16 像素）。
- 用 ViT 这类 vision encoder 把 patch 变成一串向量，相当于"图像 token"。
- 再用 projector 把这些向量映射到 LLM 的输入空间，和文本 token 拼在一起。
**追问 / 深入 (中):**
- 追问"为什么要切 patch？" → Transformer 处理的是序列，patch 化把二维图像变成一串"视觉 token"，就能套用 Transformer。
- 追问"ViT 是什么？" → Vision Transformer，把图像当成 patch 序列跑 Transformer 的视觉模型。
**常见误区 (中):**
- 以为图像像素直接喂进 LLM；中间必须经过 vision encoder + projector 两步转换。

### Q3. What is CLIP and what is its core idea? / CLIP 是什么？核心思想是什么？
**难度:** 进阶
**Answer (EN):**
- CLIP maps images and text into the same vector space using contrastive learning.
- It has two encoders: one for images, one for text, trained on many image–caption pairs.
- Matching image–text pairs are pulled close; non-matching pairs are pushed apart.
- After training you can compare an image and text by similarity — good for retrieval and zero-shot classification.
**核心答案 (中):**
- CLIP 用对比学习把图像和文本映射到**同一个向量空间**。
- 有两个编码器：image encoder 和 text encoder，用海量"图 + 配文"对训练。
- 正确配对的图文拉近，错误配对推远。
- 训完后可直接比图文相似度 → 适合图文检索、zero-shot 分类。
**追问 / 深入 (中):**
- 追问"什么是 zero-shot 分类？" → 给一张图和几个文字标签，分别编码后比相似度，最近的就是预测类别，不用为新类别重新训练。
- 追问"CLIP 能直接生成回答吗？" → 不能，CLIP 只做映射 / 比相似度；要生成文字得接 LLM（VLM 常拿 CLIP 当视觉骨干）。
**常见误区 (中):**
- 以为 CLIP 是个聊天 / 生成模型；它是个"图文对齐 + 检索"模型，不生成文本。
- 把对比学习理解成分类训练；它学的是"配对相不相似"，不是固定类别。

### Q4. What does a typical VLM architecture look like? / 典型的 VLM 架构长什么样？
**难度:** 进阶
**Answer (EN):**
- A typical VLM has three parts: an image encoder, a projector, and an LLM.
- The image encoder (often CLIP/ViT-based) turns the image into visual vectors.
- The projector aligns those vectors to the LLM's input space.
- The LLM takes image tokens plus text tokens together and generates the text answer.
**核心答案 (中):**
- 典型 VLM 三部分：image encoder + projector + LLM。
- image encoder（常基于 CLIP / ViT）把图像变成视觉向量。
- projector 把视觉向量对齐到 LLM 的输入空间。
- LLM 把"图像 token + 文本 token"一起当输入，生成文字回答。
**追问 / 深入 (中):**
- 追问"训练时主要训哪块？" → 常见做法是冻结已训好的 image encoder 和 LLM，主要训中间 projector，成本低、复用已有能力（具体策略因模型而异 ⚠️待核实）。
- 追问"projector 起什么作用？" → 把视觉向量的维度和语义对齐到 LLM 能直接吃的空间，否则图像信息进不去 LLM。
**常见误区 (中):**
- 以为 VLM 是从零重训一个大模型；多数是把现成的 vision encoder 和 LLM 用 projector 接起来。

### Q5. What are the main limitations of current VLMs? / 当前 VLM 的主要局限是什么？
**难度:** 高阶
**Answer (EN):**
- Hallucination: the model may describe objects or details that are not in the image.
- Fine-grained tasks are weak: counting, exact spatial relations, and small objects often fail.
- Resolution limits: after patching, fine details can be lost, so dense text or complex charts are hard.
- Alignment quality: if the projector aligns poorly, visual info does not reach the LLM well.
**核心答案 (中):**
- 幻觉：会描述图里其实没有的物体或细节。
- 细粒度任务弱：数数、精确空间关系、小物体常出错。
- 分辨率限制：patch 化后细节易丢，密集文字 / 复杂图表难读对。
- 对齐质量：projector 对齐不好，视觉信息进不去 LLM，回答和图脱节。
**追问 / 深入 (中):**
- 追问"为什么会幻觉？" → 一部分来自 LLM 本身的语言先验：它会"按常识补全"图里没明说的东西，而非严格基于像素证据。
- 追问"怎么缓解分辨率问题？" → 思路如提高输入分辨率、切多个子图 / tiles 分别编码等（具体方案因模型而异 ⚠️待核实）。
**常见误区 (中):**
- 以为 VLM 能像专用 OCR 一样精确读字；通用 VLM 的 OCR 能力有限，密集 / 小字仍易错。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "A multimodal model takes more than one input type — usually text plus images — and turns the image into token-like embeddings."
  (中) 多模态模型接收不止一种输入——通常是文本 + 图像——并把图像变成类似 token 的 embedding。
- (EN) "An image is split into patches, a vision encoder like ViT turns them into vectors, and a projector aligns them to the LLM's space."
  (中) 图像切成 patch，ViT 这类 vision encoder 把它们变成向量，projector 再把向量对齐到 LLM 的空间。
- (EN) "CLIP uses contrastive learning to put images and text in the same space, so matching pairs are close — great for retrieval and zero-shot classification."
  (中) CLIP 用对比学习把图像和文本放进同一空间，配对的挨得近——适合检索和 zero-shot 分类。
- (EN) "A typical VLM is image encoder plus projector plus LLM: the LLM reads image tokens and text tokens together and answers in text."
  (中) 典型 VLM 是 image encoder + projector + LLM：LLM 把图像 token 和文本 token 一起读，再用文字回答。
- (EN) "The main weak spots are hallucination, counting and fine details, and low resolution for dense text."
  (中) 主要弱点是幻觉、数数和细节、以及密集文字下的低分辨率问题。

## 延伸阅读
- *Learning Transferable Visual Models From Natural Language Supervision*（Radford et al., 2021）—— CLIP 原论文。
- *An Image is Worth 16x16 Words*（Dosovitskiy et al., 2020）—— ViT 原论文。
- *Visual Instruction Tuning*（LLaVA，Liu et al., 2023）—— image encoder + projector + LLM 三段式 VLM 的代表作。⚠️待核实（论文细节请以原文为准）
