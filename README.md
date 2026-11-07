# learn-super-agent

**Super-agent 设计课**：一套中文互动自学课程，精读 DeepSeek Harness 团队的文章
[《Super-agent 设计探索：迈向更自主的 Agent 系统》](https://mp.weixin.qq.com/s/zoS7GlReWPhfCjENGxXCdg)（2026-10-31）。

页面分三栏：左栏是学习路线（4 步 9 课）和进度，中间是图文课程（原文插图、可操作的模拟演示、课末自测），右栏是 AI 助教。

课程有两种 AI 功能，按需开启：

| | AI 助教 | AI 讲师（语音讲课） |
|---|---|---|
| 是什么 | 右栏的答疑助手，读过原文和本课全文（讲原型的课还附原型设计文档）；能画流程图、把对话整理成笔记 | 打开 Chrome 带你走读课程：滚动高亮、亲手操作演示、语音讲解，讲完自动进入下一课 |
| 怎么用 | 你自己读课，随时选中段落或点图片/演示上的“问 AI” | 坐着听；随时可暂停、跳步、插话问助教 |
| 能否单独用 | **可以**，只开课程就有，不需要讲师 | 依赖 AI 助教（讲师会公开向助教提问） |
| 需要 | `DEEPSEEK_API_KEY` | `DEEPSEEK_API_KEY` + Chrome；建议先预合成音频 |
| 启动 | `just super-agent-course` | `just super-agent-course --lecture` |

两者都不要也行：直接双击 `lessons/index.html` 就能当静态课程读。

> 个人学习项目，与 DeepSeek 无隶属关系。原文和原图版权归 DeepSeek，本仓库不附带，需在本地下载（见第 2 步）。

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

- [uv](https://docs.astral.sh/uv/)：运行 Python 脚本（必需）。
- [just](https://just.systems) ≥ 1.54：**推荐**，所有命令一行搞定。`brew install just`（已装旧版用 `brew upgrade just`）。不装也行，下面每步都给了 uv 写法。
- Chrome：AI 讲师需要；只看课程用任意现代浏览器即可。
- DeepSeek API key：AI 助教和 AI 讲师需要。

### 1. 克隆仓库

```bash
git clone https://github.com/aicoder2048/learn-super-agent.git
cd learn-super-agent
```

### 2. 下载原文和配图（只需一次）

```bash
uv run --no-project --with beautifulsoup4 --with markdownify python lessons/tools/fetch_article.py
```

生成 `docs/articles/super-agent-design-exploration.md`（助教的上下文）和 14 张配图（`docs/articles/img/`、`lessons/img/`），均已在 `.gitignore` 里。没拿到正文时，先确认原文链接还能打开，稍后再试。

### 3. 配置 API key

```bash
cp lessons/.env.sample lessons/.env
```

编辑 `lessons/.env`：

| 变量 | 是否必需 | 作用 |
|---|---|---|
| `DEEPSEEK_API_KEY` | 必需（用 AI 功能时） | AI 助教答疑；AI 讲师的助教问答；“换个讲法”的兜底模型。[在此申请](https://platform.deepseek.com/api_keys)，按量计费需先充值。 |
| `MOONSHOT_API_KEY` | 可选 | Kimi Code key，只用于 AI 讲师的 **“换个讲法”**（`R` 键，让讲师换一种说法重讲当前这段）。**没配就由 `DEEPSEEK_API_KEY` 兜底**；配了但 Kimi 调用出错，也会自动退回 DeepSeek。 |
| `DEEPSEEK_MODEL` / `DEEPSEEK_EFFORT` | 可选 | 默认 `deepseek-flash` / `low`（可选 `low` / `high` / `max`）。 |
| `KIMI_MODEL` | 可选 | 默认 `k3.1-pro`。 |

`.env` 不会被提交；key 只在本机服务里使用，不会发到浏览器。服务只监听 `127.0.0.1`。

### 4. 预合成讲师音频（可选，用 AI 讲师前建议做）

AI 讲师用 edge-tts 合成语音（需联网；失败时退回 macOS `say`）。不预合成也能讲，只是每课开头几步会边合成边讲、稍慢。

```bash
just lecture-audio            # 全部 9 课；或 just lecture-audio SA02 只合成一课（约 1 分钟）
# 不用 just：
cd lessons/lecturer && uv run lecturer.py audio [SA02]
```

音频缓存在 `lessons/lecturer/audio/`，改了讲稿只会补合成变化的句子。

### 5. 启动

```bash
just super-agent-course                     # 只开课程（含 AI 助教）
just super-agent-course --lecture           # 同时让 AI 讲师从 SA01 开讲
just super-agent-course --lecture SA02 --from s4 --port 9000   # 指定课、小节、端口
```

不用 just（在项目根目录）：

```bash
cd lessons && uv run --no-project python tools/course.py [--lecture SA02] [--port 9000]
```

浏览器打开 **http://127.0.0.1:8766/lessons/**（默认端口 8766）。`Ctrl+C` 停止；带讲师时关掉讲课窗口，服务也会一起停。

## AI 讲师操作

- 左下角控制条；**空格** 暂停/继续，**← / →** 上一步/下一步，**R** 换个讲法，**Esc** 离开输入框（之后快捷键才生效）。
- 随时在右栏问助教，讲师会自动暂停并用助教的声音读出回答。
- 讲完一课倒数 5 秒进入下一课，倒数时按空格可留在本课。

## 怎样学

1. 按 1 → 4 步顺序学，每课先看“学完本课，你能够”。
2. 对照原文图（点击放大），动手玩演示，留意页面标明的简化假设。
3. 做课末自测；不懂的词悬停虚线看定义，或打开顶栏“术语表”。
4. 问 AI 助教：选中段落点“问 AI”，或点图片/演示右上角的“问 AI”（会带上截图和当前参数）。拖动助教栏左边缘可调宽度（双击恢复）。
5. 记笔记：助教栏点“记笔记”，勾选几段对话，点“整理为笔记”（约半分钟，也按量计费）。笔记是 Markdown，存在 `lessons/study-notes/`（不进 git），可直接放进 Obsidian；顶栏“学习笔记”页可浏览、复制、下载或打印。
6. 顶栏可切换浅色 / 深色 / 水墨主题。进度和对话只存在本机浏览器。

## 常见问题

- **助教显示“未连接”**：页面是双击打开的（`file://`），请按第 5 步启动服务后从 http 地址打开。
- **提示没有 `DEEPSEEK_API_KEY`**：检查 `lessons/.env` 是否存在、key 是否正确，然后重启。
- **“还没下载原文” / 配图缺失**：运行第 2 步。
- **DeepSeek 返回 401 / 402**：key 无效或余额不足。
- **`just` 报读不了 justfile**：版本太旧，`brew upgrade just`。

## 开发者

```bash
just lecture-check            # 讲稿自检：对照真实页面检查元素、演示和自测题，不启动服务、不调模型
just lecture SA02 --port 9000 # 单独启动讲师（课程服务需先在另一终端运行）
cd lessons && uv run --no-project --with playwright python tools/check_page.py index.html glossary.html notes.html SA0*.html --theme dark
cd lessons && uv run --no-project python tools/serve.py --check   # 每课附带的资料、未登记的引用、来源漂移
```

课程编写规范见 `lessons/AUTHORING.md`（含来源快照、勘误和框架升级），讲稿写法见 `lessons/lecturer/AUTHORING.md`。课程框架来自 interactive-courseware 模板，升级用它的 `sync_course.py`。

```
lessons/
  index.html  glossary.html  notes.html  SA01–SA09 *.html
  assets/            course-config.js（课程配置）、course-lib.js / course-tutor.js / course.css（框架）、术语表
  tools/             serve.py（本地服务 + DeepSeek 转发）、sources.json（助教资料清单）、course.py（启动入口）、fetch_article.py 等
  lecturer/          AI 讲师：讲稿 scripts/、语音 tts.py、音频缓存 audio/
  .env.sample        API key 模板
docs/articles/prototype-docs/   dsh-superagent-prototype 设计文档存档（MIT）
```

## 致谢与版权

- 原文：DeepSeek Harness 团队《Super-agent 设计探索：迈向更自主的 Agent 系统》，2026-10-31 首发于微信公众号。版权归原作者，本仓库不分发原文和原图。
- 开源原型：[deepseek-ai/dsh-superagent-prototype](https://github.com/deepseek-ai/dsh-superagent-prototype)（MIT），设计文档存档于 `docs/articles/prototype-docs/`。
- 课程中标为“补充”的内容和所有模拟演示，是课程作者的解释，不是原文观点。
- `superagentxai/superagentx` 是名字相近但无关的第三方项目。

## 许可证

课程页面、脚本和文档采用 [MIT 许可证](LICENSE)，不覆盖原文和原图，也不覆盖 `docs/articles/prototype-docs/`（沿用原型自己的 MIT 许可证）。详见 [NOTICE](NOTICE)。
