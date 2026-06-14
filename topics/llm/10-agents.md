---
topic: Agents
domain: llm
difficulty: 进阶
status: drafted
prerequisites: [prompting-icl]
tags: [agents, ReAct, tool-use, function-calling, planning, memory]
---

# Agents

## 一句话概览
> LLM agent 是把 LLM 当成"决策大脑"，让它在一个循环里**自己思考 → 调用工具 → 看结果 → 再决定下一步**，直到完成任务——而不是一次问答就结束。

## 概念讲解

**1. 直觉：从"问答"到"会做事"**
普通用法是：你问一句，LLM 答一句，结束。
agent 不一样：给它一个目标（比如"帮我查今天北京天气并决定要不要带伞"），它会**自己拆步骤、调工具（查天气 API）、读返回结果、再判断**，循环往复直到目标达成。核心区别是有了一个 **loop（循环）** 和**外部行动能力**。

**2. agent 的循环长什么样**
最经典的循环可以概括成几步，不断重复：
1. **观察 / Observe**：看当前状态和已有信息。
2. **思考 / Reason**：LLM 想"现在该干什么"。
3. **行动 / Act**：调用一个工具（搜索、计算、查数据库、写文件……）。
4. **得到结果 / Observation**：把工具返回塞回上下文。
5. 回到第 1 步，直到 LLM 认为任务完成、输出最终答案。

**3. 三大核心组件**

- **Planning（规划 / 任务分解）**
  把一个大目标拆成可执行的小步骤。可以是一次性先列计划（plan-then-execute），也可以是边走边想下一步（如 ReAct）。复杂任务还会有"反思 / reflection"：做完一步回头检查对不对，错了就改。

- **Tool use / Function calling（工具调用）**
  LLM 本身只会生成文字，**做不了实际动作**（查实时信息、算数、改数据）。工具调用让它能"伸手"去用外部能力：搜索引擎、计算器、代码执行、数据库、各种 API。
  现在主流做法是 **function calling**：你预先告诉模型有哪些函数、每个函数的参数 schema；模型在需要时输出一个**结构化的调用请求（函数名 + 参数 JSON）**，由你的程序去真正执行，再把结果喂回去。

- **Memory（记忆）**
  - **短期记忆 / short-term**：就是当前对话的 **context window**（上下文窗口）。本轮看到的工具结果、中间推理都在里面，但**窗口有限、对话一结束就没了**。
  - **长期记忆 / long-term**：把信息存到外部（常用向量数据库），需要时再检索回来（本质就是 RAG 思路）。让 agent 跨会话记住事实、用户偏好、过去经验。

**4. ReAct 模式（Reason + Act 交替）**
ReAct 是最常被问的 agent 模式。它让模型**交替产出"思考"和"行动"**：

```
Thought: 我需要先查一下北京今天天气
Action: search("北京 今天 天气")
Observation: 北京今天小雨，最高 18 度
Thought: 有雨，应该建议带伞
Answer: 建议带伞，今天北京有小雨。
```

好处：把"推理过程"显式写出来，让调工具更有依据、也更可解释、更好调试。

**5. 单 agent vs multi-agent**
- **单 agent**：一个 LLM 循环，配一组工具，自己干完整个任务。简单、好控制、好调试。
- **multi-agent（多智能体）**：多个各有分工的 agent 协作，比如一个"规划者"、几个"执行者"、一个"审查者"，互相传消息。
  - 好处：分工清晰、可并行、每个 agent 提示更聚焦。
  - 代价：更复杂、协调/通信开销大、更贵、更难调试，错误也可能在 agent 之间传播放大。
  - 经验法则：**能用单 agent 解决就别上 multi-agent**，复杂度要为收益买单。

**6. 典型应用与局限**

- **典型应用**：编程助手（读代码、跑测试、改 bug 的循环）、深度研究（多轮搜索+综述）、网页/电脑操作自动化、客服与工作流自动化。
- **核心局限**（面试高频）：
  - **错误累积 / error accumulation**：一步错，后面基于错误结果继续，越走越偏。
  - **死循环 / loops**：反复调同一个工具、来回打转不收敛。
  - **成本与延迟**：一个任务可能调用 LLM 几十次，token 和时间都贵。
  - **可靠性**：输出不稳定、function call 参数有时出错、对真实世界副作用（删文件、发邮件）需要兜底。
  - 常见缓解：步数上限、超时、人类确认（human-in-the-loop）关键动作、自检/反思、限制工具权限。

## 面试问答卡

### Q1. What is an LLM agent, and how is it different from a normal chatbot? / 什么是 LLM agent？它和普通聊天机器人有什么不同？
**难度:** 基础
**Answer (EN):**
- An LLM agent uses an LLM as a decision maker that runs in a loop: it reasons, calls tools, reads the result, and decides the next step until the task is done.
- A normal chatbot just answers in one turn; an agent can take actions in the outside world (search, run code, call APIs) and keep going on its own.
- Key parts of an agent are planning, tool use, and memory.
**核心答案 (中):**
- agent 把 LLM 当决策者，放在一个循环里：思考 → 调工具 → 看结果 → 决定下一步，直到任务完成。
- 普通 chatbot 一问一答就结束；agent 能在外部世界**采取行动**（搜索、跑代码、调 API），还能自己持续推进。
- agent 的核心组件：planning、tool use、memory。
**追问 / 深入 (中):**
- 追问"为什么需要循环？" → 因为很多任务一步做不完，要根据上一步的真实结果（工具返回）再决定下一步，循环才能动态适应。
**常见误区 (中):**
- 以为接了几个工具就叫 agent；关键在于**模型自己在循环里做决策**，而不是被写死的流程一步步驱动。

### Q2. What are the core components of an agent? / agent 的核心组件有哪些？
**难度:** 基础
**Answer (EN):**
- Planning: break the goal into steps, and sometimes reflect to fix mistakes.
- Tool use (function calling): let the LLM call outside tools like search, calculator, code, or APIs.
- Memory: short-term is the context window; long-term stores info outside (often a vector database) and retrieves it later.
**核心答案 (中):**
- Planning：把目标拆成步骤，必要时反思纠错。
- Tool use / function calling：让 LLM 调用外部工具，如搜索、计算器、代码、API。
- Memory：短期是 context window；长期把信息存到外部（常用向量库），用时再检索。
**追问 / 深入 (中):**
- 追问"短期和长期记忆区别？" → 短期就是当前上下文窗口，容量有限、会话结束就没；长期是外部存储 + 检索（RAG 思路），能跨会话、跨任务记住东西。
**常见误区 (中):**
- 把"记忆"等同于"更大的 context window"；长期记忆是**外部存储 + 检索**，不是单纯把窗口撑大。

### Q3. What is function calling, and how does it let an LLM use tools? / 什么是 function calling？它如何让 LLM 使用工具？
**难度:** 进阶
**Answer (EN):**
- You give the model a list of functions, each with a name and a parameter schema.
- When the model wants a tool, it outputs a structured call: the function name plus arguments as JSON.
- Your program runs the real function, then feeds the result back into the context so the model can continue.
- The LLM never runs the tool itself; it only decides which tool to call and with what arguments.
**核心答案 (中):**
- 你先告诉模型有哪些函数，每个函数的名字和参数 schema。
- 模型需要工具时，输出一个**结构化调用**：函数名 + 参数（JSON）。
- 你的程序真正执行函数，把结果喂回上下文，模型再继续。
- LLM 自己不执行工具，它只决定**调哪个、传什么参数**。
**追问 / 深入 (中):**
- 追问"function calling 和 ReAct 什么关系？" → ReAct 是一种"思考+行动交替"的提示/推理模式；function calling 是把"行动"做成结构化 JSON 调用的工程实现，两者常配合使用。
- 追问"参数出错怎么办？" → 校验返回的 JSON（schema validation），出错可让模型重试或返回错误信息让它纠正。
**常见误区 (中):**
- 以为模型亲自执行了函数；模型只产生**调用意图**，执行在你的代码侧。

### Q4. Explain the ReAct pattern. / 解释一下 ReAct 模式。
**难度:** 进阶
**Answer (EN):**
- ReAct means the model alternates between Reasoning and Acting.
- It writes a Thought (its reasoning), then an Action (a tool call), then reads the Observation (the tool result), and repeats.
- Making the reasoning explicit helps the model choose better actions, and makes the agent easier to debug and explain.
**核心答案 (中):**
- ReAct = Reason（推理）和 Act（行动）**交替进行**。
- 模型先写 Thought（推理），再写 Action（调工具），然后读 Observation（工具结果），如此循环。
- 把推理显式写出来，能让选的行动更靠谱，也更好调试、更可解释。
**追问 / 深入 (中):**
- 追问"ReAct 和 Chain-of-Thought 区别？" → CoT 只在脑子里推理、不调工具；ReAct 在推理的同时**真去调外部工具拿真实信息**，能纠正纯推理的幻觉。
**常见误区 (中):**
- 以为 ReAct 是某个模型或框架；它是一种**推理+行动交替的模式/范式**，可以用不同模型和工具实现。

### Q5. When would you use multiple agents instead of one? / 什么时候用 multi-agent 而不是单 agent？
**难度:** 进阶
**Answer (EN):**
- Use a single agent when one LLM loop with a set of tools can finish the task — it is simpler and easier to debug.
- Use multiple agents when the task splits into clear roles (e.g. planner, workers, reviewer) or parts can run in parallel.
- Multi-agent costs more, adds coordination overhead, and is harder to debug, so only use it when the benefit is worth the complexity.
**核心答案 (中):**
- 单 agent：一个循环 + 一组工具能搞定时就用它，简单、好调试。
- multi-agent：任务能拆成清晰角色（规划者 / 执行者 / 审查者）或可并行时再用。
- multi-agent 更贵、协调开销大、更难调试，**收益要能盖过复杂度**才上。
**追问 / 深入 (中):**
- 追问"multi-agent 有什么新风险？" → 错误可能在 agent 之间传播放大；通信/协调本身要消耗大量 token；还可能出现 agent 互相等待或目标不一致。
**常见误区 (中):**
- 以为 agent 越多越强；多数任务单 agent 足够，盲目堆 agent 只会更慢更贵更乱。

### Q6. What are the main failure modes of agents, and how do you mitigate them? / agent 主要有哪些失败模式？怎么缓解？
**难度:** 高阶
**Answer (EN):**
- Error accumulation: one wrong step feeds the next, so the agent drifts further off. Mitigate with self-check / reflection and validating tool results.
- Loops: the agent repeats the same action and never finishes. Mitigate with a max step count and timeouts.
- Cost and latency: one task may call the LLM many times. Mitigate by limiting steps, using cheaper models for simple steps, and caching.
- Reliability and side effects: bad arguments or risky actions (delete, send email). Mitigate with schema validation, limited tool permissions, and human approval for risky actions.
**核心答案 (中):**
- 错误累积：一步错，后面基于错的继续，越走越偏 → 自检 / reflection、校验工具结果。
- 死循环：反复调同一工具不收敛 → 设步数上限和超时。
- 成本与延迟：一个任务调 LLM 几十次 → 限步数、简单步用便宜模型、加缓存。
- 可靠性与副作用：参数出错或危险动作（删除、发邮件）→ schema 校验、限制工具权限、关键动作加人类确认（human-in-the-loop）。
**追问 / 深入 (中):**
- 追问"怎么判断 agent 任务完成？" → 设明确的终止条件（模型显式给出最终答案、达到目标状态、或外部校验通过），并配步数/超时上限兜底，避免无限跑。
**常见误区 (中):**
- 以为加个更强的模型就能解决可靠性；工程兜底（步数上限、校验、权限、人类确认）和模型能力同样重要。

## 速记 / 口述版（EN 为主 + 中文对照）
> 面试能脱口而出的英文短稿，每句配中文
- (EN) "An LLM agent uses the model as a decision maker in a loop: it reasons, calls a tool, reads the result, and decides the next step until the task is done."
  (中) LLM agent 把模型当循环里的决策者：思考、调工具、读结果、决定下一步，直到任务完成。
- (EN) "The three core parts are planning, tool use via function calling, and memory — short-term is the context window, long-term is external storage you retrieve from."
  (中) 三大核心是 planning、靠 function calling 的 tool use、和 memory——短期是上下文窗口，长期是外部存储再检索。
- (EN) "ReAct means the model alternates Thought and Action: it reasons, calls a tool, reads the observation, and repeats."
  (中) ReAct 就是模型交替 Thought 和 Action：推理、调工具、读结果，循环往复。
- (EN) "Prefer a single agent; use multiple agents only when the task has clear roles, and the benefit beats the extra cost and complexity."
  (中) 优先用单 agent；只有任务有清晰分工、收益盖过额外成本和复杂度时才用 multi-agent。
- (EN) "The big risks are error accumulation, loops, high cost, and unreliable actions — so we add step limits, validation, and human approval for risky steps."
  (中) 主要风险是错误累积、死循环、高成本、动作不可靠——所以加步数上限、校验、关键动作人类确认。

## 延伸阅读
- *ReAct: Synergizing Reasoning and Acting in Language Models*（Yao et al., 2022）—— ReAct 模式原论文。
- *Reflexion: Language Agents with Verbal Reinforcement Learning*（Shinn et al., 2023）—— agent 自我反思 / reflection 思路。
- *LLM Powered Autonomous Agents*（Lilian Weng 博客，2023）—— planning / memory / tool use 框架综述，适合建立全局图景。
- 各家 function calling / tool use 官方文档（如 OpenAI、Anthropic）—— 具体 API 用法 ⚠️待核实（接口和参数随版本变化，使用前查最新文档）。
