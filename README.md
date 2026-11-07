# learn-super-agent · Super-agent 设计课

精读 DeepSeek Harness 团队文章[《Super-agent 设计探索：迈向更自主的 Agent 系统》](https://mp.weixin.qq.com/s/zoS7GlReWPhfCjENGxXCdg)（2026-10-31）的中文互动自学课程。

- **9 课 · 4 步**：问题与全景 → 核心架构 → 交互与运行 → 验证与落地。
- **每课**：原文插图、可操作的模拟演示、课末自测；顶栏有术语表和学习笔记。

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

默认用法：AI 讲师打开 Chrome 带你走读课程，配语音讲解，遇到疑问会向右栏的 AI 助教提问。你也可以随时自己问助教。

## 需要

- [uv](https://docs.astral.sh/uv/)
- [just](https://just.systems)，版本 ≥ 1.54
- Chrome
- 你自己的 DeepSeek API Key

## 下载原文和配图

原文和原图版权归 DeepSeek，仓库里不附带。克隆后先在本地取回一次：

```bash
uv run --no-project --with beautifulsoup4 --with markdownify python lessons/tools/fetch_article.py
```

它会生成助教用的原文 `docs/articles/super-agent-design-exploration.md` 和 14 张配图（`docs/articles/img/`、`lessons/img/`），都已被 `.gitignore` 排除。

## 配置 API Key

```bash
cp lessons/.env.sample lessons/.env
```

打开 `lessons/.env`，填入你的 key：

| 变量 | 是否必须 | 用途 |
|---|---|---|
| `DEEPSEEK_API_KEY` | 必须 | AI 助教答疑、联网查资料；AI 讲师代你向助教提问 |
| `MOONSHOT_API_KEY` | 可选 | 只用于“换个讲法”（R 键），不填就用 DeepSeek。要用 Kimi Code 会员的 key，开放平台的 key 不行 |

DeepSeek key 在 https://platform.deepseek.com/api_keys 申请，按量计费，要先充值。`.env` 已被 `.gitignore` 排除，不会提交。

## 开始上课

先合成讲师语音（edge-tts，免费，要联网，每课约 1 分钟）。语音文件不在仓库里，克隆后要在本地生成。不合成也能讲，只是每课开头会边合成边讲，稍慢：

```bash
just lecture-audio
```

然后开课：

```bash
just course --lecture
```

第一次启动时，uv 会自动安装依赖，需要几十秒。不用手动跑 `uv sync`。

上课时的按键：

| 按键 | 作用 |
|---|---|
| 空格 | 暂停 / 继续 |
| ← / → | 上一步 / 下一步 |
| R | 换个讲法 |
| Esc | 离开输入框 |

你在右栏提问时，讲课会自动暂停，看完回答按空格继续。讲完一课倒数 5 秒进入下一课，倒数时按空格可留在本课。关掉浏览器窗口或按 Ctrl+C 结束。

## 常见问题

- **提示没有 key**：检查 `lessons/.env` 是否存在，`DEEPSEEK_API_KEY=` 后面有没有填。
- **DeepSeek 返回 401 / 402**：key 填错了，或者余额不足。
- **“还没下载原文” / 配图缺失**：先跑上面“下载原文和配图”那一步。
- **助教显示“未连接”**：页面是双击打开的（`file://`），要用 `just course` 启动后从 http 地址打开。
- **找不到 Chrome**：运行 `cd lessons/lecturer && uv run playwright install chromium`。
- **端口被占用**：加 `--port 9000` 换个端口。
- **just 不认识 `[continue]`**：just 版本太老，升级到 1.54 以上。

## 目录与维护

| 路径 | 内容 |
|---|---|
| `lessons/index.html` | 课程首页；`SA01–SA09` 课程页、`glossary.html` 术语表、`notes.html` 学习笔记 |
| `lessons/assets/` | `course-config.js` 课程配置，`course-lib.js` / `course-tutor.js` / `course.css` 框架，术语表数据 |
| `lessons/lecturer/` | AI 讲师：`scripts/` 讲稿、`tts.py` 语音、`audio/` 音频缓存；讲稿写法见 `lessons/lecturer/AUTHORING.md` |
| `lessons/tools/` | `serve.py` 本地服务与助教转发，`sources.json` 助教资料清单，`course.py` 启动入口，`fetch_article.py` 取回原文，`check_page.py` 页面检查 |
| `lessons/AUTHORING.md` | 课程编写规范（含来源快照、勘误和框架升级） |
| `lessons/study-notes/` | 助教“整理为笔记”生成的 Markdown 笔记（不进 git） |
| `docs/articles/prototype-docs/` | dsh-superagent-prototype 设计文档存档（MIT） |

运行 `just` 可以看到全部命令，包括讲稿自检 `just lecture-check`。其他检查：

```bash
cd lessons && uv run --no-project python tools/serve.py --check   # 每课助教资料、未登记的引用、来源漂移
cd lessons && uv run --no-project --with playwright python tools/check_page.py index.html glossary.html notes.html SA0*.html --theme dark
```

课程框架来自 interactive-courseware 模板，升级用它的 `sync_course.py`。

## 说明

- 个人学习项目，与 DeepSeek 无隶属关系。原文版权归原作者，本仓库不分发原文和原图。
- 开源原型：[deepseek-ai/dsh-superagent-prototype](https://github.com/deepseek-ai/dsh-superagent-prototype)（MIT），设计文档存档于 `docs/articles/prototype-docs/`。
- 课程中标为“补充”的内容和所有模拟演示，是课程作者的解释，不是原文观点。
- `superagentxai/superagentx` 是名字相近但无关的第三方项目。
- 课程页面、脚本和文档采用 [MIT 许可证](LICENSE)，不覆盖原文和原图，也不覆盖 `docs/articles/prototype-docs/`。详见 [NOTICE](NOTICE)。

---

不想听语音，可以只开课程和 AI 助教：运行 `just course`，然后打开 http://127.0.0.1:8766/lessons/ 。
