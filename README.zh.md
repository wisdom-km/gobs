# gobs

**gobs** 在终端里启动一个 AI CLI，用来管**你自己的 [Obsidian](https://obsidian.md) 库**。

人看。模型写和归档——**只有你说保存**才落盘，而且必须走 `gobs save`，不能把聊天贴进现行页。

gobs 是启动器，聊天窗仍是 Grok。

**完整用法：** [docs/usage.zh.md](docs/usage.zh.md) · [English](docs/usage.md)

---

## 安装

需要 Python 3.10+、桌面版 Obsidian、[Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api)（MCP `http://127.0.0.1:27123/mcp/`）、PATH 上的 `grok`。

```powershell
irm https://raw.githubusercontent.com/wisdom-km/gobs/main/install.ps1 | iex
```

```bash
pip install git+https://github.com/wisdom-km/gobs.git
curl -fsSL https://raw.githubusercontent.com/wisdom-km/gobs/main/install.sh | bash
```

装完请**新开终端**。

```bash
gobs init "/path/to/your/vault"    # 不改你的文件夹，不整份覆盖 AGENTS.md
gobs doctor
gobs                               # 开库，进 Grok
```

空库可选骨架：`gobs init ~/Notes/Vault --skeleton`。

`gobs init` 会在 `AGENTS.md` 里插入保存协议块、装上 `/save-to-vault`、必要时创建 `90_archive/transcripts/`。只有 `--force-agents` 才覆盖整份 `AGENTS.md`。

日历、语言、「这个目录不要动」写在**你的** `AGENTS.md`。gobs 不复制 API 密钥；`gobs doctor` 检查 MCP 时不打印 token。

---

## 每天怎么用

```text
gobs                 # 第一次：直接进 Grok。之后：n 新建 / 数字继续 / q 退出
gobs --new
gobs --resume ID
gobs sessions
```

在 Grok 里对着库聊、一起读讲解、改现行页，都是普通对话。**保存是另说一句。**
想上课时优先 `gobs learn desk`（对话+图+笔记，不靠 Obsidian），或在同一会话里输入 `/learn`。学习模式下说 **保存**：原文进归档，同时写进该主题的领域卡。细则：[docs/learn-desk.md](docs/learn-desk.md)。

### 保存（精华）

在对话里说 **写进库**、**记下来**、**save to vault**，或 **`/save-to-vault`**。

得到一页短的现行笔记（结论、决策、待办）。模型先搜旧页，按你的分类归档，必须调用 `gobs save`，不能把聊天贴进去。

### 归档（可选原文）

说 **写进库，连同原文** 或 **`/save-to-vault including transcript`**。

| 文件 | 位置 | 用途 |
| --- | --- | --- |
| 精华 | 主题目录里的现行页 | 给你读 |
| 原文 | `90_archive/transcripts/日期-标题.md` | 备查，不当「今天看这篇」 |

精华里 `[pN]` 会链到转录**第 N 段**。在 Obsidian 里点链接跳回原话。

归档不是日历，也不会自动改首页。

CLI 和块链接细节：[docs/saving.md](docs/saving.md)。完整逐步说明：[docs/usage.zh.md](docs/usage.zh.md)。

---

## 命令

```text
gobs
gobs --new
gobs --resume ID
gobs init [vault] [--skeleton] [--force-agents]
gobs save --note 相对路径.md --body-file FILE [--chat-file FILE] [--title NAME]
gobs learn desk [--vault PATH]
gobs learn save --note 22_study/00_learn/NAME.md --body-file CARD.md --chat-file LECTURE.md
gobs learn judge --attempt ATTEMPT.json
gobs sessions
gobs doctor
gobs config vault PATH
```

`--note` 必须是库内相对路径，不能包含 `..`。

## 许可证

MIT
