# 课程编写规范（给写课程的人和 AI 看）

本课程精读 DeepSeek Harness 团队的文章《Super-agent 设计探索：迈向更自主的 Agent 系统》（2026-10-31）。
框架移植自 `~/Python/Playground/TechnicalAnalysis/docs/ta-knowhow/LESSONS`（左 = 学习路线与本课小节，中 = 图文课程，右 = AI 助教）。

每篇课程 = 一个独立的 HTML 文件，放在 `lessons/` 根目录。双击就能打开（`file://`）；AI 助教需要本地服务。

**参考样板：`SA01-why-super-agent.html`。** 写新课之前先完整读一遍它，照它的结构、组件和语气写。

## 1. 文件与目录

| 路径 | 用途 |
|---|---|
| `SAxx-*.html` | 课程页。文件名必须和 `assets/course-config.js` 里 `CL.LESSONS` 的 `file` 一致 |
| `assets/course-config.js` | **课程配置**：`CL.CONFIG`（前缀 `sa`、标题、端口）、`CL.STEPS`、`CL.LESSONS`、可选的 `CL.TUTOR_*` 快捷问题。课程自己的公用函数也挂在这里 |
| `assets/course-theme.css` | 课程自己的公用样式（目前为空）。只用 CSS 变量，不写死颜色；单课样式写在那一课的 `<style>` 里 |
| `assets/course-lib.js` / `course-tutor.js` / `course.css` | **框架文件，不要改**：顶栏、左栏、翻页、测验、术语提示、原图放大、`CL.lanes`、AI 助教（可拖宽、记笔记）。从 interactive-courseware 模板同步（见第 9 节） |
| `assets/glossary-data.js` | 共用术语表 |
| `assets/glossary-add-<课号>.js` | 写课时新增术语的临时文件（见第 5 节），最后由总编合并 |
| `img/figNN.*` | 原文配图（图 1–14，编号与原文顺序一致） |
| `tools/serve.py` | 本地服务 + DeepSeek 转发（AI 助教、记笔记）、来源漂移检查。框架文件 |
| `tools/sources.json` | 来源清单：助教人设与规则、每课附带哪些资料（原文全课都带；原型文档按课挑选）、来源快照 |
| `notes.html` | 学习笔记页：列出助教整理出的笔记（存在 `study-notes/`，不进 git） |
| `tools/check_page.py` | 用真 Chrome 打开页面，报 JS 错误、坏链接、缺术语、横向滚动 |
| `../docs/articles/super-agent-design-exploration.md` | **原文**（唯一事实来源） |
| `../docs/articles/prototype-docs/` | 开源原型的设计文档（README、000–008） |

### 原文配图对照

| 文件 | 原文位置 | 内容 |
|---|---|---|
| fig01 | §1 | 同一任务在 IM 群聊与 GitHub PR 评审之间连续推进 |
| fig02 | §1 | 持续关注公共群聊，无人 @ 时主动识别缺陷并提交修复 PR |
| fig03 | §1 | 整体系统架构（标号 [2]–[6] 对应第 2–6 节） |
| fig04 | §2 | 双层架构：Router 层 + 多个隔离的 Worker Session |
| fig05 | §3.1 | 两级过滤：程序层策略 → 语义层策略 |
| fig06 | §3.2 | Thread 示例 |
| fig07 | §3.2 | 订阅与直通 |
| fig08 | §3.3 | 链式召回 |
| fig09 | §3.4 | 投机执行示例：群里还在讨论，后台已提交修复 PR |
| fig10 | §4.1 | 经典 ReAct Loop 与异步 ReAct Loop 对比 |
| fig11 | §5.2 | 存算分离与执行环境解耦 |
| fig12 | §7.1 | 工作请求累计到达曲线与四种方案的累计完成曲线 |
| fig13 | §7.1 | 四种方案的 p50/p95 与读缓存 token 表 |
| fig14 | §7.2 | Router batch 大小、单次请求耗时、每个决定的分摊推理时间 |

## 2. 页面骨架（照抄 SA01）

```html
<head>  course.css → course-theme.css → glossary-data.js → [glossary-add-X.js] → course-config.js → course-lib.js
<header id="cl-topbar"></header>
<div class="layout">
  <aside class="toc"> 本课目录 <ol><li><a href="#s1">…</a></li>… </ol></aside>
  <main>
    .hero（kicker = "SAxx · 分组"，h1，一句导语，.meta）
    .objectives（学完本课，你能够：3–5 条，动词开头）
    section.lesson-sec#s1 … #sN   每节 h2 带 <span class="num">01</span>
    最后一节：自测（3–5 道 .quiz）+ 速记表 + 相关课程 .related
    <nav id="cl-pager" data-current="本文件名.html"></nav>
    <p class="disclaimer">原文出处 + “补充内容是课程作者的解释”</p>
  </main>
</div>
<script> CL.onReady(function(){ … }) </script>
```

## 3. 组件速查

- 原文配图：`<figure class="fig"><img src="img/fig04.jpg" alt="…"><figcaption><b>原文图 4</b>说明</figcaption></figure>`。AI 助教会自动给它加“问 AI”（把图片发给模型）。
- 原文金句：`blockquote.src` + `<cite>§2.1</cite>`。原样引用，少量。
- `.callout.rule` 核心规则；`.callout.note` 补充说明（**课程作者的补充一律放在这里，并在标题写“补充”**）；`.callout.tip` 实战提示；`.callout.warn` 局限/常见误解。每个 callout 第一行 `<span class="ttl">标题</span>`。
- `.grid-2 / .grid-3` 里放 `.kp` 卡片；`.vs` 方案对照卡（`.good` / `.bad`）。
- `ol.steps`；`ul.checklist`；`.tbl-wrap > table.tbl`；`.pill.fast/.slow/.hot` 小徽章；`.src-ref` 原文位置标签（如 `<span class="src-ref">§3.2</span>`）。
- 互动演示：`.chart-card` > `.chart-head`（`.chart-title` + 控件 `label.ctrl` / `.btn`）→ `.demo#id`（演示区）→ `.readout`（等宽结果）→ `.chart-foot`（一两句“看什么”）。**结论数字要写进 `.readout` 或 `.chart-foot`**，AI 助教才能读到。
- 时间线：`CL.lanes("#el", [{name, segs:[{t0,t1,cls:"c1".."c6",text}], ticks:[t]}], {t1, unit:"s"})`。
- 消息流：`ul.msgs > li.(drop|fast|slow|act)`，内含 `.src`、正文、`.verdict`。
- 内联 SVG 图示：`<div class="diagram"><svg viewBox=…>`，用类 `.box .box.hl .box.dim .edge .edge.hl .edge.dash`、`text.sm`，自动适配三种主题；下面可加 `.cap`。不要写死颜色。注意：共享样式 `:is(.diagram, .demo) svg text { fill }` 会覆盖 SVG 的 `fill="…"` 属性；确需特殊颜色时用内联 `style="fill:…"`。
- `.quiz[data-answer=正确选项下标从0起]` > `.q` + `.opts > button…` + `.explain`。
- 术语：`<a class="term" href="glossary.html#router">Router 层</a>`。ID 必须存在。
- 课程互链：`<a href="SA03-event-filter-route.html#s3">…</a>`。

## 4. course-lib.js 速查

```js
CL.$("#id")  CL.$$(".x")  CL.fmt(x, 1)  CL.esc(s)  CL.pctl(arr, 95)
const r = CL.rng(42); r()            // 可复现的随机数，演示用
CL.lanes(el, lanes, opts)            // 时间线泳道
CL.C.blue / orange / teal / purple / red / gray / gold / pink
CL.onTheme(fn)                       // 主题切换回调（JS 里用了颜色时重画）
CL.cssVar("--ink")                   // 读 CSS 变量
```

## 5. 术语表

- 先查 `assets/glossary-data.js`，有就直接用那个 ID。
- 没有、又是读者需要的概念：在你自己的 `assets/glossary-add-<课号>.js` 里新增（并在课程 `<head>` 里引入它）：
  ```js
  Object.assign(window.CL_GLOSSARY, {
    "id-kebab": { term: "中文名", en: "English", cat: "分类", short: "一句话定义", body: "<p>详细解释</p>", see: ["相关id"] },
  });
  ```
  分类只用 `glossary-data.js` 里 `CL_GLOSSARY_CATS` 列出的：基础概念 / 架构 / 事件驱动 / 上下文 / 交互 / 运行与可靠性 / 安全与边界 / 原型实现 / 系统设计经典。
- 不要修改 `glossary-data.js` 本身。

## 6. 写作规范（ASD-STE100 风格的简明中文）

1. **一句话只说一件事。** 句子尽量短（≤ 25 字为佳）。
2. **主动语态，主语明确。**
3. **先说结论，再说理由。** 每节第一段告诉读者这节讲什么。
4. **术语第一次出现就解释**，或用 `a.term` 链接到术语表。
5. **同一个东西始终用同一个词**，沿用原文用词：Router 层、Worker 层、Trigger、Thread、订阅与直通、Inline & Spill、链式召回、投机执行、异步 ReAct Loop、存算分离、Watchdog。
6. **指令用祈使句。**
7. **数字具体**，并且只用原文给出的数字。演示里的模拟数字要标明“模拟”。
8. 语气专业、平实，像一位耐心的系统架构师在讲课。不夸张，不用感叹号堆砌。
9. **忠于原文。** 原文的观点、例子、数字、限定语（“初步参考”“尚未默认开启”“研究原型”）都要讲到。补充的背景（经典系统概念的来历、与 Claude Code / Kubernetes 等的类比）放进 `.callout.note`，标题写“补充”。

## 7. 互动演示（课程的核心价值）

- 每课至少 2 个互动演示（模拟器、可切换的图示、可点的流程）。演示要**揭示原文的一个机制或权衡**，不是装饰。
- 演示是简化模型。在 `.chart-foot` 里写清楚：模型假设了什么、和原文实验的关系。不要把模拟结果说成原文结论。
- 演示的数字由页面 JS 现算，正文引用演示结果时写“在这个模拟里”。
- 用 `CL.rng(seed)` 保证每次结果一样。

## 8. 自检（交付前必须做）

```bash
cd lessons
uv run --no-project --with playwright python tools/check_page.py 你的文件.html --shots <scratchpad目录>
uv run --no-project --with playwright python tools/check_page.py 你的文件.html --theme ink --width 1500 --shots <scratchpad目录>
uv run --no-project --with playwright python tools/check_page.py 你的文件.html --theme dark --shots <scratchpad目录>
```
- 只允许出现“链接到还没写好的其他课程”这类 broken link；其他错误必须修好。
- 打开截图看一遍：演示有内容、文字没溢出、三个主题都可读。

## 9. 来源与框架升级

- **来源变了**：原文重新下载、或原型文档更新后，页面顶部会出现漂移提示。`uv run --no-project python tools/serve.py --check` 列出每课附带的资料、课文里没登记的引用和来源漂移。按变化改好课文后，`--snapshot` 记下新指纹。
- **助教发现的疑似勘误**：记在 `errata.md`（不进 git）。核实后改课文，再删掉对应条目。
- **升级框架**：`python3 ~/.claude/skills/interactive-courseware/scripts/sync_course.py lessons`（在项目根目录运行；`--check` 只报告差异）。它覆盖框架文件、服务端和讲师代码，不动 `course-config.js`、`course-theme.css`、`sources.json`、课程页、术语表和讲稿。
- 单元测试：`uv run --no-project python -m unittest discover -s tools -p "test_*.py"`。
