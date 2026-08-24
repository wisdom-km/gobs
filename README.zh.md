# gobs

**gobs** 在终端里启动一个 AI CLI，管理**你自己的 Obsidian 库**。

人看，模型写和归档——只有你说保存才落盘，而且必须走 `gobs save`，不能把聊天贴进现行页。

## 安装

```powershell
irm https://raw.githubusercontent.com/wisdom-km/gobs/main/install.ps1 | iex
```

```bash
pip install git+https://github.com/wisdom-km/gobs.git
# 或
curl -fsSL https://raw.githubusercontent.com/wisdom-km/gobs/main/install.sh | bash
```

还需要 Obsidian、Local REST API 插件，以及 PATH 上的 `grok`。密钥写在你自己的 Grok 配置里；`gobs doctor` 会检查 MCP 有没有配（不会打印密钥）。

## 用法

```text
gobs              # 开库、等 MCP、列出 gobs 会话（继续 / 新建）
gobs --new        # 直接新开会话
gobs init         # 写入保存协议和 /save-to-vault，不覆盖你的 AGENTS 全文
gobs save --note 路径.md --body-file 精华.md [--chat-file 原文.md]
```

说「写进库」或 `/save-to-vault`。精华里用 `[pN]` 指向转录第 N 段。原文进 `99_Archive/transcripts/`，不当每天要读的页。

私人规则（日历、命理、语言）继续写在你库的 `AGENTS.md` 里。gobs 只插入带标记的保存协议块。
