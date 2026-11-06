# Run `just` to list recipes. Needs just >= 1.54 (Ctrl+C exits cleanly via [continue]).

default:
    @just --list

# 启动课程（含 AI 助教）；加 --lecture SA02 同时让 AI 讲师开讲。如：just super-agent-course --lecture SA02 --port 9999
[continue]
super-agent-course *args:
    cd lessons && uv run --no-project python tools/course.py {{args}}

# 预合成一课的 AI 讲师音频，如：just lecture-audio SA02
lecture-audio lesson:
    cd lessons/lecturer && uv run lecturer.py audio {{lesson}}

# AI 讲师开讲（先在另一个终端运行 just super-agent-course），如：just lecture SA02 --from s3 --port 9000
[continue]
lecture lesson *args:
    cd lessons/lecturer && uv run lecturer.py run {{lesson}} {{args}}
