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

3. 模型在当前会话切成教练，并 `gobs learn start <名> --no-launch` 确保 `15_Learn/` 有卡。
4. 讲解要准、要好懂：先人话和一个完整小例子，再点名术语；需要公式就给，先讲它在算什么。
5. 你说 **保存**（或 写进库 / 记下来）：一次完成
   - 原文进 `99_Archive/transcripts/`，写成一篇可读讲解（像默认 gobs 的「Attention Is All You Need 讲解」），不是 `/learn` 对话 log
   - 刚完成的一块写进 `15_Learn/` 领域卡

   内部调用 `gobs learn save`。不要拆成两步。

`/learn` 与 `/save-to-vault` 同级：都是 vault 里的 Grok skill。

## CLI（可选）

仅当你想从 shell 一键建卡+启动时：

```bash
gobs learn start Transformer
gobs learn start Transformer --resume SESSION_ID
gobs learn start Transformer --new
gobs learn save --note 15_Learn/Transformer.md --body-file CARD.md --chat-file CHAT.md
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
