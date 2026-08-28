---
gobs_type: domain
title: "{{title}}"
level: L0
status: active
enough: ""
enough_who: ""
enough_scene: ""
stop: ""
phase: enough
bloom: understand
map_ready: false
principles_n: 0
last_review: ""
next_review: ""
interval_days: 0
artifact: ""
known: ""
unknown: ""
next_move: ""
open_door: "first"
session_id: ""
doors:
  - id: first
    title: 第一扇门（命名前用这个）
    state: open
updated:
---

# {{title}}

本课指令：一课一个 phase。只打开当前 phase 那一节，不念整张卡。先提取再讲。对零基础讲。有论文用原文词+语境人话。保存 = 可读讲解 + 章节补丁（未点名的章节原样保留）。脏讲义（用户：/助手：/孔明：/ /learn）拒绝。

## 定界

- 够用（整门课结束时能做什么）：
- 谁够用（enough_who）：
- 场景（enough_scene，整门课）：
- 停线（明确不学）：

## 领域地图

门 = 地图节点。最多 5 个。`open_door` 指向当前节点。拆和留是同一节点的左右对照，不要拆开再把右边推走。

- first：

## 第一性原理

`principles_n` = 卡上已有条数，目标总额 3–7。**这一课最多新上 4 条。** 不够 3 就下次 principles 课再补。每条的人话+图+类比+反例是该条的四路编码，算 1 个组块。

1.

## 当前组块

最多 4 个（工作记忆上限）。**encode 课只服务标为 current 的那 1 个。** 人话 + 图 + 类比 + 反例 = 这 1 个组块的四路编码，禁止再带另外 3 个组块上课。

- [current]
- [ ]
- [ ]
- [ ]

## 提取队列

题干 + due。不写答案。提取答案只进归档，不进卡。

- （题干） due:

## 费曼

对打写在 feynman 课。不写标准答案进卡。

## 最小产物

artifact 那个 phase 的一份东西，不是四件套打包。出现库内路径才写 `artifact`。

## 已知 / 未知 / 下一步

- known:
- unknown:
- next_move:

## L1 履历

四件套只算履历，不写进任一 phase 的作业。L0：对着地图能讲已有原理；提取失败过至少一次。L1：履历四件套齐；用户说「确认升到 L1」且 `artifact` 非空。

- [ ] 能重建地图
- [ ] 能讲 3–7 条原理
- [ ] 问好问题
- [ ] 最小产物（artifact 非空）
