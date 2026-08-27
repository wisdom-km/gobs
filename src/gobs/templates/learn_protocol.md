<!-- gobs:learn-protocol -->
## 学习模式（推荐：会话内 /learn）

主入口仍是普通 `gobs`。想上课时在已经打开的会话里输入 `/learn` 或 `/learn Transformer`。
与 `/save-to-vault` 一样是 skill，不需要退出去跑 `gobs learn start`。

也可以说「进入学习模式」、「开始学 Transformer」。只有这时才当教练。
平时仍是书记官。讲解要准、要好懂（细则见 `/learn` skill）：先人话和完整小例子，再点名术语。

### 保存（学习模式 = 两步并成一句）

说 **保存**、**写进库**、**记下来**：一次完成

1. 原文进 `99_Archive/transcripts/`
2. 刚完成的一块写进 `15_Learn/` 领域卡

调用 `gobs learn save`。不要拆成「先写卡」和「再归档」。卡片里不贴聊天原文。

### CLI（可选，不是主路径）

- `gobs learn start NAME`：终端一键建卡 + 启动/续 session
- `gobs learn start NAME --no-launch`：只建卡（`/learn` skill 内部会调）
- `gobs learn save --note 15_Learn/NAME.md --body-file CARD.md --chat-file CHAT.md`
- `gobs learn status`：看档位与 session_id

### 档位

L0→L1：定界 → 建图 → 跟样 → 回教 → 补洞。一次一扇门。
升档须用户说「确认升到 L1」。
<!-- /gobs:learn-protocol -->
