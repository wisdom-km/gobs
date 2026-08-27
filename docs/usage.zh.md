# gobs 怎么用

gobs 是**启动器**，不是聊天软件。终端里敲 `gobs`：打开你的 Obsidian 库、等 MCP，再启动 **Grok**（或其它 CLI），工作目录就是这个库。你和 Grok 对话；Grok 读库、写库。**只有你明确说保存，才会把判断落成笔记。**

人**看**。模型**写和归档**。

保存协议细节见 [saving.md](saving.md)。其它 CLI：[other-clis.md](other-clis.md)。

---

## 1. 只做一次的准备

需要：Python 3.10+、桌面版 Obsidian、社区插件 Local REST API（MCP 默认 `http://127.0.0.1:27123/mcp/`）、PATH 上的 `grok`。

安装：

```powershell
irm https://raw.githubusercontent.com/wisdom-km/gobs/main/install.ps1 | iex
```

```bash
pip install git+https://github.com/wisdom-km/gobs.git
# 或
curl -fsSL https://raw.githubusercontent.com/wisdom-km/gobs/main/install.sh | bash
```

装完**新开一个终端**，好让 `PATH` 生效。

已有库（不改你的文件夹，不整份覆盖 `AGENTS.md`）：

```bash
gobs init "/path/to/your/vault"
gobs doctor
```

空目录、可选骨架（`00_inbox`、`10_projects` …）：

```bash
gobs init ~/Notes/Vault --skeleton
```

`gobs init` 会：

- 在 `AGENTS.md` 里插入（或更新）`<!-- gobs:save-protocol -->` 这一块；只有 `--force-agents` 才整份覆盖
- 安装 `.grok/skills/save-to-vault/SKILL.md` → 斜杠命令 `/save-to-vault`
- 没有的话创建 `90_archive/transcripts/`
- 把库路径记进 `~/.gobs/config.toml`

语言、日历、「这个目录不要动」写在**你自己的** `AGENTS.md` 里。gobs 不把私人规则推进 Git。

Grok 的 MCP 地址自己配在 `~/.grok/config.toml`。gobs 不复制密钥。`gobs doctor` 只说有没有配、有没有 auth，不打印 token。

---

## 2. 每天：打开就是对话

```bash
gobs
```

流程：

1. 后台打开这个库的 Obsidian（不占用这个终端）。
2. 等到 MCP 端口有响应。
3. **还没有** gobs 会话 → 立刻启动 Grok（打开就是对话）。
4. **已有** → 短菜单：`n` 新建，数字继续，`q` 退出。

```text
gobs --new           # 总是新开会话
gobs --resume <id>   # 续上某个已标记会话
gobs sessions        # 列出 gobs 会话
gobs --no-open       # 不自动开 Obsidian
```

在 gobs 会话里顺手改几行代码，也还算 gobs 会话。

一起读一篇讲解、当场改那一页，属于「写现行页」，**不是**下面的保存/归档。保存是另一次、你亲口说的动作。

---

## 3. 保存（精华 / 现行页）

三天后还想找得到的那句话，在 **Grok 对话里说**，一般不用自己跑 CLI：

| 你说 | 效果 |
| --- | --- |
| 写进库 / 记下来 / save to vault | 只写精华现行页 |
| `/save-to-vault` | 同上 |

模型应：先搜旧页能改就改；按你库里的分类放（有骨架才用 00/10/20 口诀）；用 `gobs save` 写短页；**不要**把聊天贴进 README、日记或 Lessons。

然后你到 Obsidian 里打开它报的那条路径。

可选骨架（仅 `--skeleton` 时）：

| 情况 | 目录 |
| --- | --- |
| 说不清 | `00_inbox/` |
| 会结束 | `10_projects/` |
| 创作 | `20_creation/` |
| 命理 | `21_metaphysics/` |
| 学习 | `22_study/` |
| 学习卡兜底 | `22_study/00_learn/` |
| 洞察 | `23_insights/` |
| 自我 | `24_self/` |
| 换项目还成立 | `30_lessons/` |
| 能再贴的提示词 | `40_prompts/` |
| PDF / 原件 | `50_resources/` |
| 库本身的说明 | `80_meta/` |
| 转录 / 冷页 | `90_archive/` |

库里已有自己的分类，就跟你的走。

---

## 4. 归档（可选全文）

要以后点回原话时，同一句里加上：

| 你说 | 效果 |
| --- | --- |
| 写进库，连同原文 | 精华 **加上** 归档转录 |
| `/save-to-vault including transcript` | 同上 |

两份文件：

| 文件 | 位置 | 用途 |
| --- | --- | --- |
| 精华 | 主题目录里的现行页 | 给你读 |
| 原文 | `90_archive/transcripts/日期-标题.md` | 备查，不当「今天看这篇」 |

精华里的关键句链到转录**对应那一段**（`[p2]` → 块链接）。在 Obsidian 里点链接就跳到原话。

归档不是日历，也不会自动改首页。日历、首页仍按你库自己的规则（例如你说「写进日历」才动）。

---

## 5. 自己跑 CLI（调试用）

`--note` 必须是库内相对路径，不能包含 `..`。

```bash
gobs save --note 30_lessons/idea.md --body-file distilled.md
gobs save --note 30_lessons/idea.md --body-file distilled.md --chat-file chat.md --title idea
```

`chat.md` 里段落用空行分开。精华里的 `[p2]` 会变成指向第 2 段的 wikilink。没有 `[pN]` 时，会在文末加一条指向第 1 段的 Source。

---

## 6. 命令一览

```text
gobs
gobs --new
gobs --resume ID
gobs init [vault] [--skeleton] [--force-agents]
gobs save --note REL.md --body-file FILE [--chat-file FILE] [--title NAME]
gobs sessions
gobs doctor
gobs config
gobs config vault PATH
```

---

## 7. 不对时

| 现象 | 试 |
| --- | --- |
| 找不到 `gobs` | 新开终端；或 `python -m gobs -V` |
| 只开了 Obsidian、没有 Grok | 更新 gobs。第一次应打印 `gobs: new session — starting grok` |
| 终端里刷 Obsidian 安装器日志 | 旧版会把 Obsidian 绑在这个控制台；当前版本已脱离 |
| 模型把整段聊天贴进笔记 | 提醒：写进库必须走 `/save-to-vault` / `gobs save` |
| doctor 报 MCP | 打开这个库、启用 Local REST API，在 Grok 里自己配 MCP 和 token |
| 库路径不对 | `gobs config vault /path/to/vault` |
