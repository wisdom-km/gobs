# gobs

**gobs** 在终端里启动一个 AI CLI，用来管理**你自己的 [Obsidian](https://obsidian.md) 库**。

人看，模型写和归档——而且只有你说「写进库」才落盘。

第一版是**启动器**，不是新的聊天界面。默认 CLI 是 [Grok](https://github.com/xai-org/grok)。其它 CLI 可以共用同一套库内文件，见 [docs/other-clis.md](docs/other-clis.md)。

## 命令

```text
gobs                 # 打开库、等 MCP、启动 grok
gobs init            # 给已有库加上约定（不改你的文件夹骨架）
gobs init --skeleton # 空库可选创建 00_Inbox / 10_Projects / …
gobs doctor          # 检查库、grok、Obsidian
```

从 `gobs` 开出的会话以该库为工作目录，CLI 的欢迎页 / `/resume` 列出的就是这个库的对话。会话里顺手改几行代码，也仍然算 gobs 会话。

## 安装

Python 3.10+：

```bash
pip install git+https://github.com/wisdom-km/gobs.git
```

还需要 Obsidian、[Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) 插件，以及 PATH 上的 `grok`。MCP 密钥写在你自己的 `~/.grok/config.toml`，gobs 不会去复制密钥。

## 保存

你明确说保存之后：

- **现行页**：精华（结论、决策、待办）
- **原文（可选）**：`99_Archive/transcripts/`，不当每天要读的页
- 精华里的关键句链到转录里**对应的那一段**（块链接 `#^block-id`）

有骨架就按 `AGENTS.md` 里的口诀归档；已有自己的分类就跟你的走。拿得准就自动放，拿不准才问，并且只给一两个具体路径。

私人规则（日历、语言、哪些目录不能动）写在**你库里的** `AGENTS.md`，不要写进 gobs 源码。

## 许可证

MIT
