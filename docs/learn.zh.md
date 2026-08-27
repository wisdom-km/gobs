# gobs learn：L0 → L1

## 推荐用法（先普通 gobs，再切 /learn）

1. 照常 `gobs` 进任意会话（新的或续旧的都行）。这是主入口。
2. 想上课时在对话里输入：

```text
/learn
/learn Transformer
/learn 英语
```

或说「进入学习模式」。**不用**退出去执行 `gobs learn start …`。

3. 模型在当前会话切成教练，并 `gobs learn start <名> --no-launch` 确保有领域卡（已有主题夹则用夹里的卡）。
4. L0 对零基础讲：麻烦 → 例子 → 没有它会怎样 → 「只要记住」→ **先问哪步不懂并补上** → 再课间确认。论文第一课只吃摘要+引言。排队的「没有它」图要画出印象包被挤。有论文用原文词+语境人话。L1 只在旧图上贴名字。
5. 你说 **保存**（或 写进库 / 记下来）：一次完成
   - 原文进 `90_archive/transcripts/`，写成一篇可读讲解（像默认 gobs 的「Attention Is All You Need 讲解」），不是 `/learn` 对话 log
   - 刚完成的一块写进该主题的领域卡

   内部调用 `gobs learn save`。不要拆成两步。

`/learn` 与 `/save-to-vault` 同级：都是 vault 里的 Grok skill。

## CLI（可选）

仅当你想从 shell 一键建卡+启动时：

```bash
gobs learn start Transformer
gobs learn start Transformer --resume SESSION_ID
gobs learn start Transformer --new
gobs learn save --note 22_study/00_learn/Transformer.md --body-file CARD.md --chat-file CHAT.md
gobs learn status
```

## 三条桥（与旧 gobs）

1. 续学 / session 列表（CLI 路径）
2. 领域卡 `session_id`
3. 保存 = 原文归档 + 写卡（一句）

## 初始化

```bash
gobs init "/path/to/vault"
```

会安装 `.grok/skills/learn` 与 `learn-domain`，并插入学习协议。
