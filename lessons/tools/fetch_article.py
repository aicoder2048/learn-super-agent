"""从微信公众号下载原文《Super-agent 设计探索：迈向更自主的 Agent 系统》到本地。

原文和原图的版权归 DeepSeek，本仓库不附带它们。运行一次这个脚本，在你自己的机器上取回：
  - docs/articles/super-agent-design-exploration.md          原文 Markdown（AI 助教的上下文）
  - docs/articles/super-agent-design-exploration.original.html  网页快照
  - docs/articles/img/fig01–fig14.*                          原文配图
  - lessons/img/fig01–fig14.*                                课程页嵌入的同一批配图

用法（在项目根目录或 lessons/ 下都行）:
    uv run --no-project --with beautifulsoup4 --with markdownify python lessons/tools/fetch_article.py
"""

import datetime
import re
import shutil
import sys
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup
from markdownify import markdownify as md

URL = "https://mp.weixin.qq.com/s/zoS7GlReWPhfCjENGxXCdg"
SLUG = "super-agent-design-exploration"
N_FIGS = 14          # 正文配图数；文末还有一张招聘海报，不要
ROOT = Path(__file__).resolve().parent.parent.parent
ART = ROOT / "docs" / "articles"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def get(url: str, referer: str = "") -> bytes:
    headers = {"User-Agent": UA}
    if referer:
        headers["Referer"] = referer
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return r.read()


def main():
    print(f"下载 {URL}")
    raw = get(URL).decode("utf-8", "replace")
    soup = BeautifulSoup(raw, "html.parser")
    title_el, body = soup.select_one("#activity-name"), soup.select_one("#js_content")
    if not title_el or not body:
        sys.exit("没有拿到正文。可能被微信要求验证：用浏览器打开上面的链接确认文章还在，稍后再试。")
    title = title_el.get_text(strip=True)
    author = soup.select_one("#js_name")
    author = author.get_text(strip=True) if author else "DeepSeek Harness 团队"
    ct = re.search(r'var ct = "(\d+)"', raw)
    tz = datetime.timezone(datetime.timedelta(hours=8))
    date = datetime.datetime.fromtimestamp(int(ct.group(1)), tz).strftime("%Y-%m-%d %H:%M") if ct else ""

    (ART / "img").mkdir(parents=True, exist_ok=True)
    (ART / f"{SLUG}.original.html").write_text(raw, encoding="utf-8")

    n = 0
    for img in body.find_all("img"):
        u = img.get("data-src") or img.get("src")
        if not u or u.startswith("data:"):
            img.decompose()
            continue
        n += 1
        if n > N_FIGS:                      # 文末招聘海报
            img.decompose()
            continue
        fmt = re.search(r"wx_fmt=(\w+)", u)
        name = f"fig{n:02d}.{(fmt.group(1) if fmt else 'png').replace('jpeg', 'jpg')}"
        (ART / "img" / name).write_bytes(get(u, "https://mp.weixin.qq.com/"))
        img.attrs = {"src": f"img/{name}", "alt": f"图{n}"}
    if n < N_FIGS:
        print(f"警告：只找到 {n} 张图，预期 {N_FIGS} 张。文章可能被修改过，课程里的部分配图会缺失。")

    lines = []
    for line in md(str(body), heading_style="ATX", bullets="-").split("\n"):
        m = re.match(r"^(#{1,3}) (.*)$", line)
        if m and len(m.group(2)) > 40:                       # 段落被误包进标题
            line = m.group(2)
        elif re.match(r"^\d+\.\d+ \S.{0,30}$", line):         # 丢了标记的二级标题
            line = "## " + line
        elif re.match(r"^\d+\. [^\s*].{0,20}$", line) and not line.endswith(("。", "；", "：")):
            line = "# " + line                                # 丢了标记的一级标题（本文只有“5. …”）
        lines.append(line)
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    head = (f"# {title}\n\n> 作者/公众号：{author}  \n> 发布时间：{date}（北京时间）  \n> 原文链接：{URL}  \n"
            "> 开源原型：https://github.com/deepseek-ai/dsh-superagent-prototype  \n"
            f"> 本地存档日期：{datetime.date.today().isoformat()}（仅供个人学习，版权归原作者）\n\n---\n\n")
    (ART / f"{SLUG}.md").write_text(head + text + "\n", encoding="utf-8")

    dst = ROOT / "lessons" / "img"
    dst.mkdir(exist_ok=True)
    for f in sorted((ART / "img").glob("fig*")):
        shutil.copy(f, dst / f.name)
    heads = sum(1 for l in text.split("\n") if l.startswith("#"))
    print(f"完成：《{title}》，{min(n, N_FIGS)} 张图，{heads} 个标题 → {ART.relative_to(ROOT)}/ 和 lessons/img/")


if __name__ == "__main__":
    main()
