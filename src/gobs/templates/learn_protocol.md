<!-- gobs:learn-protocol -->
## 学习模式（推荐：会话内 /learn）

**首选入口：在已经打开的 gobs 会话里输入 `/learn` 或 `/learn Transformer`。**
与 `/save-to-vault` 一样是 skill，不需要退出会话去跑 `gobs learn start`。

也可以说「进入学习模式」、「开始学 Transformer」。只有这时才当教练。
平时仍是书记官。

### CLI（可选，不是主路径）

- `gobs learn start NAME`：终端一键建卡 +启动/续 session
- `gobs learn start NAME --no-launch`：只建卡（`/learn` skill 内部会调）
- `gobs learn status`：看档位与 session_id

### 档位与闭环

L0→L1：定界 → 建图 → 跟样 → 回教四问 → 补洞。一次一扇门。
升档须用户说「确认升到 L1」。

### 半自动写入

阶段完成后**先问**「要不要同步进卡？」用户同意后才改 `15_Learn/`。
原文走 `/save-to-vault`。禁止每轮自动写库。
<!-- /gobs:learn-protocol -->
