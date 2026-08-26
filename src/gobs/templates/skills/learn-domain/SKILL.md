---
name: learn-domain
description: >-
  更新 15_Learn/ 领域卡（定界、四列表、样例、回教、过关）。
  用户说「写进卡」「同步到卡」「确认升到 L1」时使用。
  若要**开启**学习模式，请用 /learn（不是本 skill）。
user-invocable: true
argument-hint: "[写进卡|确认升到 L1]"
---

# learn-domain — 只负责改卡

**开启教练模式请用 `/learn`。** 本 skill 只在用户要改领域卡或升档时用。

## 更新卡片

1. 编辑 `15_Learn/` 已有卡，不另开同主题新卡。
2. 只改刚完成的那一块。
3. 保持 frontmatter：`gobs_type`、`level`、`open_door`、`status`、`session_id`。
4. 一次只一扇门 open。

## 升档

对照 L1 六条。只有用户说「确认升到 L1」才改 `level`。

## 禁止

- 把聊天原文写进领域卡
- 未确认就升档或每轮自动写库
