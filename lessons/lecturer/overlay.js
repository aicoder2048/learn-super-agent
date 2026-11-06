/* AI 讲师注入到课程页的部分：控制条、快捷键、段落高亮、音频播放。
 * 由 stage.py 通过 add_init_script 注入；按键通过 window.__lecturerCmd 回传给 Python。
 */
(function () {
  "use strict";
  if (window.__lecturer) return;

  const css = `
  /* 只画外框，不动元素自己的背景和圆角：深色底的 hero 等元素换了背景，浅色文字就看不见了 */
  .lecturer-focus { outline: 3px solid #e8a33d; outline-offset: 6px; transition: outline-color .3s; }
  .lecturer-bar { position: fixed; left: 20px; bottom: 20px; z-index: 9999; display: flex; gap: 6px; align-items: center;
    padding: 8px 10px; border-radius: 12px; background: rgba(28,32,40,.92); color: #fff;
    font: 13px/1.4 -apple-system, "PingFang SC", sans-serif; box-shadow: 0 6px 24px rgba(0,0,0,.25); }
  .lecturer-bar button { all: unset; cursor: pointer; padding: 5px 9px; border-radius: 8px; background: rgba(255,255,255,.1); }
  .lecturer-bar button:hover { background: rgba(255,255,255,.22); }
  .lecturer-bar button[disabled] { opacity: .35; cursor: default; }
  .lecturer-bar .who { min-width: 13em; max-width: 22em; padding: 0 6px; opacity: .9; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .lecturer-bar .who b { color: #f5c26b; font-weight: 600; }
  .lecturer-bar kbd { font: 11px ui-monospace, monospace; opacity: .6; margin-left: 3px; }`;

  const audio = new Audio();
  let ended = null; // 当前这段音频播完时调用

  function finish() { const f = ended; ended = null; if (f) f(); }
  audio.addEventListener("ended", finish);
  audio.addEventListener("error", finish);

  // 第二路音频：朗读学生自己提问的助教回答，不打扰暂停中的讲师音频
  const aside = new Audio();
  let asideEnded = null;
  function finishAside() { const f = asideEnded; asideEnded = null; if (f) f(); }
  aside.addEventListener("ended", finishAside);
  aside.addEventListener("error", finishAside);

  function send(cmd) { if (window.__lecturerCmd) window.__lecturerCmd(cmd); }

  function mount() {
    if (document.querySelector(".lecturer-bar")) return;
    const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
    const bar = document.createElement("div");
    bar.className = "lecturer-bar";
    bar.innerHTML =
      '<button data-cmd="prev" title="上一步（←）">⏮</button>' +
      '<button data-cmd="toggle" class="tog" title="暂停/继续（空格）">⏸</button>' +
      '<button data-cmd="next" title="下一步（→）">⏭</button>' +
      '<button data-cmd="reexplain" class="rex" title="没听懂，换个讲法（R）">换个讲法<kbd>R</kbd></button>' +
      '<span class="who">讲师准备中…</span>';
    bar.addEventListener("click", (e) => { const b = e.target.closest("button[data-cmd]"); if (b && !b.disabled) send(b.dataset.cmd); });
    document.body.appendChild(bar);
  }

  function typing(t) {
    return t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName));
  }
  document.addEventListener("keydown", (e) => {
    if (e.isComposing || e.metaKey || e.ctrlKey || e.altKey) return;
    if (typing(e.target)) {
      if (e.key === "Escape") { e.target.blur(); e.preventDefault(); }
      return; // 输入框里打字时快捷键不生效
    }
    const cmd = { " ": "toggle", ArrowRight: "next", ArrowLeft: "prev", r: "reexplain", R: "reexplain" }[e.key];
    if (!cmd) return;
    e.preventDefault(); e.stopPropagation();
    const b = document.querySelector('.lecturer-bar button[data-cmd="' + cmd + '"]');
    if (!b || !b.disabled) send(cmd);
  }, true);

  window.__lecturer = {
    /* 播放一段音频，播完（或被 stop）时 Promise 才返回 */
    play(url) {
      finish();
      return new Promise((resolve) => {
        ended = resolve;
        audio.src = url;
        audio.play().catch(() => finish());
      });
    },
    pause() { audio.pause(); },
    resume() { if (ended) audio.play().catch(() => finish()); },
    stop() { audio.pause(); finish(); },
    playAside(url) {
      finishAside();
      return new Promise((resolve) => {
        asideEnded = resolve;
        aside.src = url;
        aside.play().catch(() => finishAside());
      });
    },
    stopAside() { aside.pause(); finishAside(); },
    highlight(sel, nth) {
      document.querySelectorAll(".lecturer-focus").forEach((x) => x.classList.remove("lecturer-focus"));
      const el = document.querySelectorAll(sel)[nth || 0];
      if (!el) return false;
      el.classList.add("lecturer-focus");
      el.scrollIntoView({ behavior: "smooth", block: el.offsetHeight > innerHeight * 0.8 ? "start" : "center" });
      return true;
    },
    status(html, paused, canReexplain) {
      mount();
      const bar = document.querySelector(".lecturer-bar");
      bar.querySelector(".who").innerHTML = html;
      bar.querySelector(".tog").textContent = paused ? "▶" : "⏸";
      bar.querySelector(".rex").disabled = !canReexplain;
    },
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount); else mount();
})();
