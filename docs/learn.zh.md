# gobs learn：L0 → L1

## 推荐用法（像 skill 一样）

1. 先照常 `gobs` 进任意会话（新的或续旧的都行）。
2. 在对话里输入：

```text
/learn
/learn Transformer
/learn 英语
```

或说「进入学习模式」。**不用**退出去执行 `gobs learn start …`。

3. 模型会在当前会话切成教练，并 `gobs learn start <名> --no-launch` 确保 `15_Learn/` 有卡。
4. 阶段完成后它会问你要不要同步进卡；你同意才写。

`/learn` 与 `/save-to-vault` 同级：都是 vault 里的 Grok skill。

## CLI（可选）

仅当你想从 shell 一键建卡+启动时：

```bash
gobs learn start Transformer
gobs learn start Transformer --resume SESSION_ID
gobs learn start Transformer --new
gobs learn status
```

## 三条桥（与旧 gobs）

1. 续学 / session 列表（CLI 路径）
2. 领域卡 `session_id`
3. 半自动写卡（先问后写）

## 初始化

```bash
gobs init "/path/to/vault"
```

会安装 `.grok/skills/learn` 与 `learn-domain`，并插入学习协议。
