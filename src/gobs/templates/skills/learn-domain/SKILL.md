---
name: learn-domain
description: >-
  更新领域卡（主题文件夹里，或 22_study/00_learn/）。学习模式下用户说「保存」「写进库」「记下来」时：
  原文进归档并且按 ## 做章节补丁，一次 `gobs learn save`。
  「写进卡」「同步到卡」只改点名的章节。「确认升到 L1」才升档。
  开启学习请用 /learn。
user-invocable: true
argument-hint: "[保存|写进卡|确认升到 L1]"
---

# learn-domain — 改卡（保存时连同原文）

开启教练、讲解方式见 `/learn`。本 skill 只负责落盘。

## 保存（学习模式）

用户说 **保存**、**写进库**、**记下来**：按 `/learn` 的保存步骤。
`--chat-file` 必须是一篇可读讲解（`##` 标题 + 正文），不是聊天 log。
`--body-file` 是章节补丁，不是整卡重写：只写当前 phase 改过的 frontmatter 和点名的 `##`。
脏讲义（`用户：` / `助手：` / `孔明：` / `/learn`）会被拒绝。
调用 `gobs learn save --note <卡片真实路径> --body-file CARD.md --chat-file LECTURE.md --title "领域名"`。
不要另写 Lessons 页，不要再问「要不要同步」。

## 只改卡

用户只说「写进卡」「同步到卡」：编辑已有领域卡，只改刚完成的那一个 phase。
新卡没有四列表、没有回教。提取走 ## 提取队列（题干+due）；费曼对打在 feynman 课。
保持 frontmatter 唯一套：`gobs_type` `title` `level` `status` `enough` `enough_who` `enough_scene` `stop` `phase` `bloom` `map_ready` `principles_n` `last_review` `next_review` `interval_days` `artifact` `known` `unknown` `next_move` `open_door` `session_id` `doors` `updated`。一次只一课 / 一个 phase open。

## 升档

L0：对着地图能讲已有原理；提取失败过至少一次。
L1：履历四件套齐；只有用户说「确认升到 L1」且 `artifact` 非空才改 `level`。

## 禁止

- 把聊天原文写进领域卡
- 整卡覆盖未点名的章节
- 未确认或无 artifact 就升档
- 学习模式下把「保存」做成只写卡、不归档原文
- 把原文写成 `/learn` / `用户：` / `助手：` / `孔明：` 对话 log
