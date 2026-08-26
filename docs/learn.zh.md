# gobs learn：L0 → L1

`gobs` 仍是通用发射器。学习是一种模式，用 `gobs learn` 进入。**不推翻旧的** `gobs` / `save` / `sessions`。

## 与旧 gobs 的三条桥

1. **续学**：`gobs learn start NAME --resume ID` 或卡上已有 `session_id` 时自动续该会话；也可在列表里选旧对话。
2. **领域卡 ↔ session**：frontmatter 的 `session_id`；`gobs learn status` 会打印。会话结束后写回卡上。
3. **半自动写卡**：定界/样例/回教完成后教练**先问**「要不要同步进卡？」，你同意才改。不每轮自动落盘。

## 手算 / 消融模板（本期不做）

L2 用的固定草稿：极小数字手算、「拿掉 X 会坏在哪」表。规则已写在协议，空白页下期加。

## 命令

```bash
gobs init "/path/to/vault"
gobs learn start Transformer
gobs learn start Transformer --new
gobs learn start Transformer --resume SESSION_ID
gobs learn status
gobs learn start 医疗 --no-launch
```

## 领域卡

`15_Learn/<名称>.md`：定界、四列表、样例、回教、洞、过关、门队列、`session_id`。

升档：你说「确认升到 L1」。

## 与「写进库」

| 你说 | 发生什么 |
| --- | --- |
| 写进卡 / 同步到卡 | 改 `15_Learn/` |
| 写进库 | `gobs save` 精炼笔记 |
| 连同原文 | transcript 归档 |
