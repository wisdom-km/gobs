<!-- gobs:learn-protocol -->
## 学习模式（推荐：会话内 /learn）

主入口仍是普通 `gobs`。想上课时在已经打开的会话里输入 `/learn` 或 `/learn Transformer`。
与 `/save-to-vault` 一样是 skill，不需要退出去跑 `gobs learn start`。

也可以说「进入学习模式」、「开始学 Transformer」。只有这时才当教练。
平时仍是书记官：改讲解页，不要改进度卡。

**一课 = 一个 phase。** 8 个 phase 是一门课的阶段，不是一课里的课序。上课只打开当前 phase 对应那一节，不念整张卡。先提取再讲。

phase 顺序：enough（定界）→ map（领域地图）→ principles（第一性原理，本课最多新上 4 条，卡上总额 3–7）→ encode（当前组块里标 current 的那 1 个；人话+图+类比+反例 = 四路编码）→ retrieve（提取队列）→ feynman（费曼对打）→ artifact（最小产物）→ review（known / unknown / next_move）。

L0 对零基础讲。有论文用原文词+语境人话，不要另造正名。论文第一课只吃摘要+引言。过程课必须有能看见的图：优先库图（draw.py / Mermaid），时间过程可用库动画（gif）；库图没好再用 ASCII 兜底。排队要把「糊」画进图。禁止图像生成绘本。讲完先问哪步不懂，补上再课间确认（细则见 `/learn` skill）。L1 只在旧图上贴名字。

零基础未画先禁：配件、零件、有关。配件 vs 整台必须先画拆/留左右对照（同一张图）；拆和留是同一节点，不要把右边推到下一课。attention 说成找这个字在说谁。讲完问哪里没听懂。听懂了/可以了只收当前 phase，不要自动开下一课。禁止对学生说最空、这课行。

encode / map 课优先跑 `80_meta/gobs-viz/draw.py` 或看 `80_meta/gobs-viz/画图.md`。仍是一课一个 phase，encode = 1 个组块。

### 保存（学习模式 = 章节补丁 + 讲解，一句完成）

说 **保存**、**写进库**、**记下来**：一次完成

1. 原文写成一篇可读讲解（像默认 gobs 讲解），不是聊天 log
2. 按 `##` 做章节补丁写进**该主题文件夹里的领域卡**（没有主题夹才用 `22_study/00_learn/`）。未点名的章节原样保留。禁止整卡重写。

脏讲义（`用户：` / `助手：` / `/learn` 等说话人标签）**拒绝**，不要洗完当合格。
调用 `gobs learn save --note` 用 `gobs learn start` 打印的**真实卡片路径**（不要靠文件名 stem 回退）。不要拆成两步。卡片和原文里都不要贴 `/learn` 对话 log。提取答案只进归档，不进卡。无 artifact 不得把 `level` 写成 L1。

### CLI（可选，不是主路径）

- `gobs learn start NAME`：终端一键建卡 + 启动/续 session
- `gobs learn start NAME --no-launch`：只建卡（`/learn` skill 内部会调）
- `gobs learn save --note 卡片路径.md --body-file CARD.md --chat-file LECTURE.md`
- `gobs learn status`：看档位、phase、next_review、artifact 与 session_id

### 档位

L0：对着地图能讲已有原理；提取失败过至少一次。
L1：履历四件套齐（重建地图、讲 3–7 条原理、问好问题、最小产物）；用户说「确认升到 L1」且 `artifact` 非空。
术语和公式是升档后的贴纸，不是第一课的开场。bloom 封顶 understand | apply | analyze，写入 create 则夹成 analyze。
<!-- /gobs:learn-protocol -->
