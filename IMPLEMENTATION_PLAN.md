# AI 讲师 v1 实施计划

设计共识见 `GLOSSARY.md` 和 `docs/adr/0001-offline-lecture-scripts.md`。代码放在 `lessons/lecturer/`。v1 只做 SA02。

## Stage 1: 讲稿格式与校验
**Goal**: 定义讲稿 JSON 格式，写好加载与校验模块，并完成 `AUTHORING.md`。
**Success Criteria**: 合法的讲稿能加载成功；不合法的讲稿报错，错误信息指明是哪一步、哪个字段。
**Tests**: 合法讲稿可以加载；缺字段报错；未知步骤类型报错；`--from` 能定位到小节的第一步。
**Status**: Complete

## Stage 2: 语音合成与缓存
**Goal**: 实现 `tts.py`。用 edge-tts 合成，用 macOS `say` 兜底，按"声音 + 文本"的哈希缓存。提供 `just lecture-audio SA02` 预合成整课音频。
**Success Criteria**: 一课的讲师音频能全部合成好；第二次运行全部命中缓存；edge-tts 失败时自动切到 `say`。
**Tests**: 缓存文件名稳定；分句器能正确切分中文句子；文本清洗能去掉 Markdown 符号。
**Status**: Complete

## Stage 3: 播放器（讲、演示、自测）
**Goal**: 用 Playwright 打开有界面的 Chrome，注入控制条和高亮样式，按讲稿执行 say、demo、quiz 三类步骤。支持空格、←/→、Esc 快捷键，以及 `--from`。
**Success Criteria**: SA02 能从头讲到尾。暂停和继续都能立刻生效，上一步/下一步正常。焦点在输入框时快捷键不生效。
**Tests**: 控制状态机的单元测试（暂停、继续、跳步）；用一份冒烟讲稿做端到端测试。
**Status**: Complete

## Stage 4: 代问与换个讲法
**Goal**: proxy 步骤在右栏公开提问，助教回答时按句流式朗读，用助教的声音。按 `R` 时用 Kimi 改写当前这一步并朗读；没有 Kimi key 时改用 DeepSeek。缺 DeepSeek key 时启动报错。
**Success Criteria**: 代问的问答能在页面上看到，也能听到朗读；换个讲法能在 15 秒内开始说话。
**Tests**: 选模型的逻辑（Kimi 优先、DeepSeek 兜底）；增量分句（流式文本只吐出新完整的句子）。
**Status**: In Progress

## Stage 5: SA02 讲稿与端到端验收
**Goal**: 按 `AUTHORING.md` 写好 `scripts/SA02.json`，预合成音频，完整跑一遍。
**Success Criteria**: 一课完整讲完：2–4 个重点话题、1–2 次代问、两个演示都有操作、4 道自测题。
**Tests**: 讲稿通过校验；端到端跑通。
**Status**: Not Started
