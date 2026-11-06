# Run `just` to list recipes.

default:
    @just --list

# Start the Super-agent course with its AI tutor: http://127.0.0.1:<port>/lessons/
super-agent-course port="8766":
    cd lessons && uv run --no-project python tools/serve.py --port {{port}}
