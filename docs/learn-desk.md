# gobs learn desk

课桌是 `/learn` 的课堂主界面：一个本地网页，三栏。不启动、不依赖 Obsidian。库只是一叠 markdown 文件夹。

```
+------------------+------------------+
| 对话（像终端）      | 图（process 渲染） |
+------------------+------------------+
| 笔记（当前 phase + 最近讲解）。可复制 markdown。 |
+-------------------------------------+
```

```bash
gobs learn desk --vault /path/to/vault
gobs learn desk --vault /path/to/vault --note 22_study/00_learn/Attention-Is-All-You-Need.md --port 8765
```

浏览器打开 `http://127.0.0.1:8765/`。本机没有 grok 也能看图和笔记；对话会记下「CLI 不在」，页面不崩。

## 图：通用协议，不是写死的小猫句

教练按**这篇**论文的例子写 `80_meta/gobs-viz/figure.json`。教课（enough / map / principles / encode）锁论文标，学生只点揭开。测验课（retrieve / feynman）学生自己标，再交卷。

```bash
gobs learn judge --note 22_study/00_learn/NAME.md --attempt attempt.json
```

判断对照 `paper` 的 hi / mid / lo。命名词必须对上；学生多标了「高」而论文没有或标「低」，未过。每个词都高但论文不是这样，也不算过。

## API

| 路径 | 作用 |
| --- | --- |
| `GET /` | 课桌 |
| `GET /figure` | 当前 figure.json（mode 跟卡上 phase） |
| `PUT /figure` | 写入新 spec（先校验） |
| `POST /judge` | 学生交卷 |
| `GET /notes` | 当前章节 + 最近讲解 |
| `POST /chat` | `{text}` → 跑库里配置的 CLI |
| `GET /status` | title / phase / level / mode |

课桌对话落在 `90_archive/transcripts/desk-SESSION.md`。这是日志，不是讲解，不要喂给 `gobs learn save`。
