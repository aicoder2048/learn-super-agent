# 运行 `just` 查看全部命令。需要 just >= 1.54（[continue] 让 Ctrl+C 干净退出）。

default:
    @just --list

# 启动课程（含 AI 助教）；加 --lecture [SA02] 同时让 AI 讲师开讲（不写课号从第一课开始）。如：just course --lecture --port 9000
[continue]
course *args:
    cd lessons && uv run --no-project python tools/course.py {{args}}

# AI 讲师开讲（课程服务已在另一个终端运行时用），如：just lecture SA02 --from s3
[continue]
lecture lesson *args:
    cd lessons/lecturer && uv run lecturer.py run {{lesson}} {{args}}

# 预合成 AI 讲师音频；不写课号 = 全部。如：just lecture-audio SA02
lecture-audio *lessons:
    cd lessons/lecturer && uv run lecturer.py audio {{lessons}}

# 讲稿自检（不用启动服务，不调用模型）；不写课号 = 全部。如：just lecture-check SA02 --readouts
lecture-check *args:
    cd lessons/lecturer && uv run lecturer.py check {{args}}
