---
name: learn-domain
description: >-
  更新领域卡（主题文件夹里，或 22_study/00_learn/）。学习模式下用户说「保存」「写进库」「记下来」时：
  原文进归档并且写进领域卡，一次 `gobs learn save`。
  「写进卡」「同步到卡」只改卡。「确认升到 L1」才升档。
  开启学习请用 /learn。
user-invocable: true
argument-hint: "[保存|写进卡|确认升到 L1]"
---

# learn-domain — 改卡（保存时连同原文）

开启教练、讲解方式见 `/learn`。本 skill 只负责落盘。

## 保存（学习模式）

用户说 **保存**、**写进库**、**记下来**：按 `/learn` 的保存步骤。
`--chat-file` 必须是一篇可读讲解（`##` 标题 + 正文），不是聊天 log。
调用 `gobs learn save --note <卡片路径> --body-file CARD.md --chat-file LECTURE.md --title "领域名"`。
不要另写 Lessons 页，不要再问「要不要同步」。

## 只改卡

用户只说「写进卡」「同步到卡」：编辑已有领域卡，只改刚完成的那一块。
四列表和回教是课后档案，按课堂上已经讲过的例子填，不要把讲稿改成提纲。
他卡住的那一步写入「洞」，不要贴问答 log。
保持 frontmatter：`gobs_type`、`level`、`open_door`、`status`、`session_id`。一次只一课 open。

## 升档

对照 L1 六条。只有用户说「确认升到 L1」才改 `level`。

## 禁止

- 把聊天原文写进领域卡
- 未确认就升档
- 学习模式下把「保存」做成只写卡、不归档原文
- 把原文写成 `/learn` / `用户：` / `助手：` 对话 log
