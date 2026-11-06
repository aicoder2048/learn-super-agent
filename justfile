# Run `just` to list recipes. Needs just >= 1.54 (Ctrl+C exits cleanly via [continue]).

default:
    @just --list

# Start the Super-agent course with its AI tutor: http://127.0.0.1:<port>/lessons/
[continue]
super-agent-course port="8766":
    cd lessons && uv run --no-project python tools/serve.py --port {{port}}

# 预合成一课的 AI 讲师音频，如：just lecture-audio SA02
lecture-audio lesson:
    cd lessons/lecturer && uv run lecturer.py audio {{lesson}}

# AI 讲师开讲（先在另一个终端运行 just super-agent-course），如：just lecture SA02 --from s3 --port 9000
[continue]
lecture lesson *args:
    cd lessons/lecturer && uv run lecturer.py run {{lesson}} {{args}}
