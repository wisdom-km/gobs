<!-- gobs:learn-protocol -->
## 学习模式（推荐：会话内 /learn）

主入口仍是普通 `gobs`。想上课时在已经打开的会话里输入 `/learn` 或 `/learn Transformer`。
与 `/save-to-vault` 一样是 skill，不需要退出去跑 `gobs learn start`。

也可以说「进入学习模式」、「开始学 Transformer」。只有这时才当教练。
平时仍是书记官。L0 对零基础讲故事和例子，像默认 gobs 讲解，不像考卷（细则见 `/learn` skill）。术语课后贴。

### 保存（学习模式 = 两步并成一句）

说 **保存**、**写进库**、**记下来**：一次完成

1. 原文写成一篇可读讲解（像默认 gobs 讲解），不是聊天 log
2. 刚完成的一块写进**该主题文件夹里的领域卡**（没有主题夹才用 `22_study/00_learn/`）

调用 `gobs learn save --note` 用 `gobs learn start` 打印的卡片路径。不要拆成两步。卡片和原文里都不要贴 `/learn` 对话 log。

### CLI（可选，不是主路径）

- `gobs learn start NAME`：终端一键建卡 + 启动/续 session
- `gobs learn start NAME --no-launch`：只建卡（`/learn` skill 内部会调）
- `gobs learn save --note 卡片路径.md --body-file CARD.md --chat-file LECTURE.md`
- `gobs learn status`：看档位与 session_id

### 档位

L0：能复述这一课的画面和「只要记住」的几句。
L1：能不看笔记把例子走完，并说出没有它会怎样。
升档须用户说「确认升到 L1」。术语和公式是升档后的贴纸，不是第一课的开场。
<!-- /gobs:learn-protocol -->
