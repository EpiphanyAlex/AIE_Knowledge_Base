# PRD — cards.html 重构（Apple 风格 · Token Design System）

状态：已实现 ✅ · 2026-06-14 · 由 `ui-ux-pro-max` 设计系统驱动 · 实现见 `tools/build_cards.py`

## 1. 背景与目标
现有 `cards.html` 是 Anki 风格抽认卡（学习/浏览双模式 + SRS），功能已验证，但视觉偏重、风格普通。本次**只重构外观与交互质感，不改功能与数据流**。

**目标**：以 **Apple.com 的克制美学**重做界面——大量留白、精致排版、近白背景、极淡阴影、柔和圆角——并落地为一套 **design token 体系**，尽量简洁。

**约束（不变）**
- 单文件、自包含 HTML+CSS+JS，零依赖；由 `tools/build_cards.py` 生成。
- markdown 仍是唯一数据源；SRS / 模式 / 筛选 / 键盘逻辑保持不变。
- 字体用 **Apple 系统字体栈**（SF Pro / 系统），不引外部字体，保持零依赖。

## 2. 设计方向（Apple Web 原则）
1. **留白优先**：宽松间距、单列聚焦，一次只突出一张卡。
2. **近白而非纯白**：页面 `#F5F5F7`，卡片纯白 `#FFFFFF`，发丝级分隔线。
3. **排版即设计**：大号标题、负字距、清晰层级；正文 17px。
4. **克制的色彩**：中性灰阶 + 单一蓝色强调；评分用 iOS 系统色但以「浅底深字」的淡色按钮呈现，克制不刺眼。
5. **微动效**：仅 1–2 处关键过渡（翻面、hover），150–250ms ease-out；尊重 `prefers-reduced-motion`。

## 3. Design Tokens（token design system）
全部以 CSS 自定义属性落在 `:root`，组件只引用 token，不写死值。深色模式通过 `prefers-color-scheme` 覆盖同名 token。

### 3.1 颜色（Light，默认）
| Token | 值 | 用途 |
|------|-----|------|
| `--bg` | `#f5f5f7` | 页面背景 |
| `--surface` | `#ffffff` | 卡片/弹层 |
| `--surface-2` | `#f5f5f7` | 次级填充（segmented 轨道）|
| `--text` | `#1d1d1f` | 主文字 |
| `--text-secondary` | `#6e6e73` | 次文字/中文副标 |
| `--separator` | `#d2d2d7` | 发丝分隔线/边框 |
| `--accent` | `#0071e3` | 强调/主按钮 |
| `--accent-hover` | `#0077ed` | 主按钮 hover |
| `--again` / `--hard` / `--good` / `--easy` | `#d70015` / `#9a5b00` / `#1d7a33` / `#0058b0` | 评分按钮文字色（深，过对比度）|
| `--again-bg`…`--easy-bg` | 对应色 12–14% alpha | 评分按钮浅底 |

### 3.2 颜色（Dark，`prefers-color-scheme: dark` 覆盖）
`--bg:#000` · `--surface:#1c1c1e` · `--surface-2:#2c2c2e` · `--text:#f5f5f7` · `--text-secondary:#98989d` · `--separator:#38383a` · `--accent:#2997ff`。评分色用更亮变体。

### 3.3 字体
- `--font`: `-apple-system, "SF Pro Text", "SF Pro Display", "Helvetica Neue", "PingFang SC", "Microsoft YaHei", sans-serif`
- 字号：`--fs-xs 12 · --fs-sm 14 · --fs-base 17 · --fs-lg 21 · --fs-xl 28`
- 字重：`--fw-regular 400 · --fw-medium 500 · --fw-semibold 600`
- 标题负字距：`--tracking-tight -0.02em`

### 3.4 间距（8pt 网格）
`--space-1 4 · --space-2 8 · --space-3 12 · --space-4 16 · --space-5 24 · --space-6 32 · --space-8 48 · --space-10 64`

### 3.5 圆角 / 阴影 / 动效
- 圆角：`--radius-sm 8 · --radius-md 12 · --radius-lg 18 · --radius-xl 24 · --radius-pill 980px`
- 阴影：`--shadow-sm 0 1px 3px rgba(0,0,0,.06)` · `--shadow-md 0 4px 20px rgba(0,0,0,.08)`
- 动效：`--ease cubic-bezier(.4,0,.2,1)` · `--dur-fast 150ms · --dur 250ms`

## 4. 布局与组件
- **顶栏**：贴顶、半透明毛玻璃（`backdrop-filter`）、底部发丝线。含：标题 · 模式 segmented（学习/浏览）· 三个筛选下拉 · 语言 segmented（中英/EN/中）· 右侧统计 · 重置。
- **Segmented control**（Apple/iOS 风）：`--surface-2` 轨道，选中段为白底 + `--shadow-sm`，圆角 pill。
- **学习卡**：居中、最大宽 `~600px`、白底、圆角 `--radius-xl`、内边距 `--space-8`、`--shadow-md`。
  - 徽章（领域/主题/难度）：浅灰 pill，次文字色。
  - 问题：`--fs-xl`、`--fw-semibold`、负字距；中文副标 `--fs-lg`、次文字色。
  - 分隔：发丝虚线。答案分区标签：`--fs-sm`、次文字色、`--fw-semibold`。
  - **显示答案**：Apple pill CTA（`--accent` 底、白字、`--radius-pill`）。
  - **评分条**：4 个等宽淡色按钮（重来/难/良/简单 + 间隔），浅底深字，hover 加深。
- **浏览网格**：`auto-fill minmax(300px,1fr)` 等宽白卡，`--radius-lg`、`--shadow-sm`、发丝边；`<details>` 展开答案。
- **完成态**：居中，**SVG 对勾**（不用 emoji）+ 简短文案 + 再来一遍按钮。

## 5. 交互与状态
- 功能不变：显示答案（空格）→ 重来/难/良/简单（键 1–4，SRS）；模式/筛选/语言切换；进度存 `localStorage`。
- hover：仅颜色/底色过渡，**不做位移缩放**导致的跳动（cards 用 `--shadow` 微变）。
- 触控目标 ≥ 44px。

## 6. 可访问性（来自 ui-ux-pro-max，CRITICAL/HIGH）
- 文字对比 ≥ 4.5:1（评分按钮用深字浅底已满足）。
- `:focus-visible` 可见焦点环（`--accent`，offset 2px）；不移除 outline 无替代。
- `prefers-reduced-motion: reduce` → 关闭过渡/动画。
- 图标用 SVG，不用 emoji。
- `<select>` 有可达标签（`aria-label`）。

## 7. 非目标
- 不改 SRS 算法、解析逻辑、markdown 格式。
- 不引入框架/外部字体/图标库（保持单文件零依赖）。
- 不做花哨 bento 异形网格（保持简洁）。

## 8. 验收标准
- [ ] 视觉为 Apple 风：近白背景、白卡、发丝线、柔和圆角与极淡阴影、系统字体。
- [ ] 全部颜色/间距/圆角/字体走 token；改 token 即换肤。
- [ ] 学习/浏览/筛选/语言/SRS/键盘 全部照常工作。
- [ ] 浅色 + 深色（系统）两套均可读、对比达标。
- [ ] focus 环可见、reduced-motion 生效、无 emoji 图标。
- [ ] 仍是 `python3 tools/build_cards.py` 生成的单文件。
