# learn-deepseek-super-agent

**Super-agent 设计课**：一套中文互动自学课程，精读 DeepSeek Harness 团队的文章
[《Super-agent 设计探索：迈向更自主的 Agent 系统》](https://mp.weixin.qq.com/s/zoS7GlReWPhfCjENGxXCdg)（2026-10-31）。

- **左栏**：学习路线（4 步 9 课）和本课小节，记录已学进度。
- **中间**：图文课程。嵌入原文配图，每课 2–3 个可操作的模拟演示，课末有自测题和速记表。
- **右栏**：AI 助教。它读过原文全文和本课全部内容。你可以选中一段话问它，也可以点图片或演示右上角的“问 AI”，让它看着图讲解。

> 本课程是个人学习项目，与 DeepSeek 无隶属关系。原文和原图的版权归 DeepSeek，本仓库不附带，需要你在本地下载（见第 2 步）。

## 课程目录

| 步骤 | 课程 | 原文 |
|---|---|---|
| 1 问题与全景 | SA01 为什么需要 Super-agent | §1 |
| 2 核心架构 | SA02 双层架构：Router 与 Worker | §2 |
| | SA03 事件驱动（上）：过滤与路由 | §3.1–3.2 |
| | SA04 事件驱动（下）：上下文组织与提前行动 | §3.3–3.4 |
| 3 交互与运行 | SA05 面向人的交互：全双工与多信道 | §4 |
| | SA06 存算分离与 Watchdog | §5–6 |
| 4 验证与落地 | SA07 读懂实验：消融与批处理 | §7 |
| | SA08 开源原型 dsh-superagent 拆解 | [GitHub 原型](https://github.com/deepseek-ai/dsh-superagent-prototype) |
| | SA09 开放问题与全课总结 | §8–9 |

## 快速开始

### 0. 准备

- [uv](https://docs.astral.sh/uv/)（运行 Python 脚本）
- 现代浏览器（Chrome / Edge / Safari / Firefox）
- 一个 DeepSeek API key（只有 AI 助教需要）

### 1. 克隆仓库

```bash
git clone https://github.com/aicoder2048/learn-deepseek-super-agent.git
cd learn-deepseek-super-agent
```

### 2. 下载原文和配图（第一次使用时做一次）

```bash
uv run --no-project --with beautifulsoup4 --with markdownify python lessons/tools/fetch_article.py
```

脚本从微信公众号取回原文，生成：

- `docs/articles/super-agent-design-exploration.md`：原文 Markdown，AI 助教用它做上下文。
- `docs/articles/img/` 和 `lessons/img/`：14 张原文配图。

这些文件已加入 `.gitignore`，不会被提交。如果脚本提示没拿到正文，先用浏览器打开原文链接，确认文章还在，稍后再试。

### 3. 配置你自己的 DeepSeek API key

```bash
cp lessons/.env.sample lessons/.env
```

打开 `lessons/.env`，把 `DEEPSEEK_API_KEY=sk-your-key-here` 换成**你自己的 key**。在 [DeepSeek 开放平台](https://platform.deepseek.com/api_keys) 申请。

- **费用**：DeepSeek 官方 API 按量计费，需要先充值。每次提问都会消耗你账户里的额度。每次请求都带上原文和本课全文作上下文（约 1–2 万 token），重复提问时多数能命中 DeepSeek 的前缀缓存。
- **安全**：`.env` 已在 `.gitignore` 里，不会被提交。key 只在本机的 `tools/serve.py` 里使用，不会发到浏览器页面。服务只监听 `127.0.0.1`，并拒绝访问任何点文件。
- 可选设置：`DEEPSEEK_MODEL`（默认 `deepseek-flash`）、`DEEPSEEK_EFFORT`（`low` / `high` / `max`，默认 `low`）。

### 4. 启动课程

```bash
cd lessons
uv run --no-project python tools/serve.py
```

浏览器打开 **http://127.0.0.1:8766/lessons/** 。换端口：`--port 9000`。按 `Ctrl+C` 停止。

> 不想用 AI 助教？直接双击 `lessons/index.html` 也能学，只是右栏助教不可用。

## 怎样学

1. 按 1 → 4 步的顺序学。每课先读“学完本课，你能够”。
2. 对照原文图。点图片可以放大。
3. 动手玩演示：调参数、换场景，看设计在什么条件下有效、代价在哪里。演示是简化模型，页面上标明了它的假设。
4. 做课末自测题。答错会显示解释。
5. 遇到不懂的词，把鼠标移到带虚线的词上看定义，或打开顶栏的“术语表”（70 条）。
6. 问 AI 助教。
   - 选中正文里的一段话，点浮出的“问 AI”。
   - 点图片或演示右上角的“问 AI”，助教会带着截图、当前参数和读数回答。
   - 快捷按钮：“用更简单的话讲讲”“考考我”“这个设计的代价和局限”。
7. 顶栏可切换浅色 / 深色 / 水墨三种主题。进度和对话记录只存在你本机的浏览器里。

## 目录结构

```
docs/articles/
  prototype-docs/           dsh-superagent-prototype 的设计文档存档（MIT，含 LICENSE）
  (下载后) super-agent-design-exploration.md / .original.html / img/
lessons/
  index.html  glossary.html  SA01–SA09 *.html
  assets/                   公用样式、脚本、AI 助教、术语表
  tools/serve.py            本地服务 + DeepSeek 转发
  tools/fetch_article.py    下载原文和配图
  tools/check_page.py       用真 Chrome 检查页面（开发用）
  tools/finalize.mjs        合并术语表、生成反向链接（开发用）
  AUTHORING.md              课程编写规范
  .env.sample               API key 模板
```

## 常见问题

- **助教显示“未连接”**：页面是直接双击打开的（`file://`）。按第 4 步启动本地服务，再从 http 地址打开。
- **助教报“没有 DEEPSEEK_API_KEY”**：检查 `lessons/.env` 是否存在、key 是否填对，然后重启服务。
- **助教报“还没下载原文” / 配图缺失**：运行第 2 步的下载脚本。
- **DeepSeek 返回 401 / 402**：key 无效或余额不足，去 DeepSeek 开放平台检查。

## 开发者：检查页面

```bash
cd lessons
uv run --no-project --with playwright python tools/check_page.py index.html glossary.html SA0*.html --theme dark
```

需要本机装有 Chrome。

## 致谢与版权

- 原文：DeepSeek Harness 团队《Super-agent 设计探索：迈向更自主的 Agent 系统》，2026-10-31 首发于微信公众号。版权归原作者，本仓库不分发原文和原图。
- 开源原型：[deepseek-ai/dsh-superagent-prototype](https://github.com/deepseek-ai/dsh-superagent-prototype)（MIT），设计文档存档于 `docs/articles/prototype-docs/`，许可证见同目录 `LICENSE`。
- 课程中标为“补充”的内容和所有模拟演示，是课程作者的解释，不是原文观点。
- 名字相近但无关的项目：`superagentxai/superagentx` 是第三方多 Agent 框架，与本文和 DeepSeek 的原型无关。

## 许可证

本仓库的课程页面、脚本和文档采用 [MIT 许可证](LICENSE)。许可证不覆盖原文和原图（版权归 DeepSeek，不在本仓库中），也不覆盖 `docs/articles/prototype-docs/`（沿用原型自己的 MIT 许可证）。
