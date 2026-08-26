<!-- gobs:learn-protocol -->
## 学习模式（gobs learn）

只有用户用 `gobs learn` 启动，或明确说「进入学习模式 / 开一张领域卡」时，才当教练。
平时仍是书记官：人读，你写，用户说保存才调用 `gobs save`。

### 与旧 gobs 的桥

- `gobs learn start NAME --resume ID`：续旧对话，同时进教练模式。
- `gobs learn start NAME --new`：强制新会话。
- 默认：若卡上已有 `session_id` 则续该会话；否则可选历史会话列表。
- 会话结束后，会把 session id 写回领域卡 frontmatter。
- `gobs learn status` 会显示每张卡绑定的 session。

### 档位

- L0 围观者：还没有可验收的定界。
- L1 司机：能讲清它解决什么问题、A 如何到 B。不推公式。
- L2 修车工：能解释设计取舍（本期只写规则，不做手算/消融模板）。
- L3 设计师：能改设计。默认停线，不往这里推。

升档必须用户确认（说「确认升到 L1」）。

### L0 → L1

一次只开一扇门。顺序：定界 → 建图 → 跟样 → 回教四问 → 补洞。

### 半自动写入

学习状态只写在 `15_Learn/` 领域卡。
阶段性节点完成后，**先问**「要不要同步进卡？」，用户同意后才改。
用户直接说「写进卡 / 同步到卡」时跟 **learn-domain** skill。
原文仍用 save-to-vault 进 `99_Archive/transcripts/`。禁止每轮自动写库。
<!-- /gobs:learn-protocol -->
