/* 课程配置：按课程修改。这是课程自己的文件，sync_course.py 不会动它。
 * 框架文件（course-lib.js、course-tutor.js、course.css）各门课相同，用 sync_course.py 升级。
 * 页面里它要排在 course-lib.js 之前（见 AUTHORING.md 第 2 节）。
 */
window.CL = window.CL || {};

CL.CONFIG = {
  prefix: "sa",          // localStorage 键前缀，每门课唯一（file:// 下所有课程共用一个源）
  title: "Super-agent 设计课",
  seal: "智",              // 顶栏图章，一个字
  sourceLink: "../docs/articles/super-agent-design-exploration.md", // 顶栏“原文”链接，相对课程目录
  port: 8766,                // tools/serve.py 的端口，和 tools/sources.json 的 course.port 一致
  lessonsDir: "lessons", // 课程目录名，离线提示里的命令和地址用它
};

// 学习路线：3–5 步。课程顺序 = 推荐学习顺序（翻页也按这个顺序）
CL.STEPS = [
  { n: 1, name: "问题与全景", desc: "为什么要有 Super-agent：瓶颈从模型转向人的注意力。四个特征、五个模块。" },
  { n: 2, name: "核心架构", desc: "双层架构、事件过滤与路由、上下文组织与投机执行。系统怎样“想”和“分工”。" },
  { n: 3, name: "交互与运行", desc: "全双工、多信道、存算分离、Watchdog。系统怎样“说话”和“活下去”。" },
  { n: 4, name: "验证与落地", desc: "实验数据、开源原型、开放问题。设计是否有效，代码里做到了哪一步。" },
];
// file 必须和课程文件名一致；src = 对应原文章节
CL.LESSONS = [
  { step: 1, file: "SA01-why-super-agent.html", id: "SA01", title: "为什么需要 Super-agent", src: "§1" },
  { step: 2, file: "SA02-two-layer.html", id: "SA02", title: "双层架构：Router 与 Worker", src: "§2" },
  { step: 2, file: "SA03-event-filter-route.html", id: "SA03", title: "事件驱动（上）：过滤与路由", src: "§3.1–3.2" },
  { step: 2, file: "SA04-context-speculation.html", id: "SA04", title: "事件驱动（下）：上下文组织与提前行动", src: "§3.3–3.4" },
  { step: 3, file: "SA05-human-interaction.html", id: "SA05", title: "面向人的交互：全双工与多信道", src: "§4" },
  { step: 3, file: "SA06-separation-watchdog.html", id: "SA06", title: "存算分离与 Watchdog", src: "§5–6" },
  { step: 4, file: "SA07-experiments.html", id: "SA07", title: "读懂实验：消融与批处理", src: "§7" },
  { step: 4, file: "SA08-prototype.html", id: "SA08", title: "开源原型 dsh-superagent 拆解", src: "GitHub 原型" },
  { step: 4, file: "SA09-open-problems.html", id: "SA09", title: "开放问题与全课总结", src: "§8–9" },
];

// 可选：AI 助教的快捷问题（第二项 = 是否附截图）。
// TUTOR_QUICK 追加在通用问题之后；TUTOR_QUICK_BASE 整组替换通用问题（通用问题偏技术文章，面向小学生等读者时替换）。
// CL.TUTOR_QUICK = [["这一节对应源码的哪个函数？", false]];
// CL.TUTOR_QUICK_BASE = [["用更简单的话讲讲这一节", false], ["这张图怎么看？", true], ["考考我：就这一节出一道题", false]];
// 可选：图片 / 演示右上角“问 AI”的预填问题
// CL.TUTOR_ASK_FIG = "这张图该怎么看？它说明了本课的哪个设计点？";
// CL.TUTOR_ASK_DEMO = "这个演示该怎么看？现在的结果说明了什么？";

// 多课共用的课程自己的函数也写在这里，挂到 CL 上（course-lib.js 会保留它们）。
// 改动会改变演示读数：写进正文和讲稿的数字要重核。
