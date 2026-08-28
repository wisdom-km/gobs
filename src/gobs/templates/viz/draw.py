#!/usr/bin/env python3
"""Adult schematic figures for /learn. matplotlib only — not image-gen."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle

SENTENCE = "The animal didn't cross the street because it was too tired"
TOKENS = SENTENCE.split()
ANIMAL_I = TOKENS.index("animal")
STREET_I = TOKENS.index("street")
IT_I = TOKENS.index("it")
TIRED_I = TOKENS.index("tired")

# Schematic weights, not a trained model. High on animal, low on street, modest on tired.
COREF_W = np.array(
    [0.03, 0.52, 0.04, 0.03, 0.02, 0.05, 0.06, 0.04, 0.03, 0.03, 0.15], dtype=float
)
ATTN_W = np.array(
    [0.04, 0.42, 0.06, 0.05, 0.03, 0.05, 0.08, 0.04, 0.05, 0.04, 0.14], dtype=float
)

INK = "#2c3338"
MUTED = "#6b7280"
BOX = "#eef1f4"
BOX_EDGE = "#8b949e"
QUERY_FILL = "#d9e3ee"
QUERY_EDGE = "#3d5a73"
HIGH = "#b4533a"
LOW = "#9aa3ad"
MID = "#6d7f4f"
SEQ = "#6b7280"
CLEAR = "#3d5a73"
HUSH = "#d4d8dc"
BG = "#fafbfc"


def _font_name() -> str | None:
    wanted = (
        "Noto Sans CJK SC",
        "Noto Sans CJK",
        "Noto Sans CJK JP",
        "WenQuanYi Zen Hei",
        "WenQuanYi Micro Hei",
    )
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in wanted:
        if name in available:
            return name
    for path in (
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ):
        p = Path(path)
        if not p.is_file():
            continue
        try:
            font_manager.fontManager.addfont(str(p))
            return font_manager.FontProperties(fname=str(p)).get_name()
        except (OSError, ValueError, RuntimeError):
            continue
    return None


def _has_cjk(name: str | None) -> bool:
    if not name:
        return False
    low = name.lower()
    return "cjk" in low or "wenquan" in low or "wqy" in low


def setup_style() -> bool:
    plt.rcParams["axes.unicode_minus"] = False
    name = _font_name()
    if name:
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
    else:
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["font.size"] = 10
    plt.rcParams["axes.titlesize"] = 12
    plt.rcParams["figure.facecolor"] = "white"
    plt.rcParams["axes.facecolor"] = "white"
    plt.rcParams["savefig.facecolor"] = "white"
    plt.rcParams["savefig.dpi"] = 160
    return _has_cjk(name)


def lab(zh: str, en: str, cjk: bool) -> str:
    return f"{zh} / {en}" if cjk else en


def _mix(a: str, b: str, t: float) -> str:
    def rgb(h: str) -> np.ndarray:
        h = h.lstrip("#")
        return np.array([int(h[i : i + 2], 16) for i in (0, 2, 4)], dtype=float)

    v = (1 - t) * rgb(a) + t * rgb(b)
    return "#{:02x}{:02x}{:02x}".format(*(int(round(c)) for c in v))


def _token_boxes(ax, xs, y, tokens, *, query_i: int | None, cjk: bool) -> None:
    w, h = 0.82, 0.34
    for i, (x, tok) in enumerate(zip(xs, tokens)):
        is_q = i == query_i
        box = FancyBboxPatch(
            (x - w / 2, y - h / 2),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.04",
            facecolor=QUERY_FILL if is_q else BOX,
            edgecolor=QUERY_EDGE if is_q else BOX_EDGE,
            linewidth=1.8 if is_q else 1.0,
            zorder=3,
        )
        ax.add_patch(box)
        weight = "bold" if is_q or tok in {"animal", "street", "tired"} else "regular"
        color = HIGH if tok == "animal" else (LOW if tok == "street" else INK)
        if tok == "tired":
            color = MID
        if is_q:
            color = QUERY_EDGE
        ax.text(
            x,
            y,
            tok,
            ha="center",
            va="center",
            fontsize=8.2,
            color=color,
            fontweight=weight,
            zorder=4,
        )
        if is_q:
            tag = lab("问", "query", cjk)
            ax.text(x, y + 0.28, tag, ha="center", va="bottom", fontsize=7.5, color=QUERY_EDGE)


def _panel_frame(ax) -> None:
    ax.set_xlim(-0.7, len(TOKENS) - 0.3)
    ax.set_ylim(-0.15, 1.55)
    ax.axis("off")
    ax.set_facecolor(BG)


def draw_seq_vs_attn(out: Path, cjk: bool) -> None:
    n = len(TOKENS)
    xs = np.arange(n, dtype=float)
    fig, axes = plt.subplots(1, 2, figsize=(14.2, 5.6), constrained_layout=True)
    fig.patch.set_facecolor("white")

    ax = axes[0]
    _panel_frame(ax)
    y_tok = 1.05
    _token_boxes(ax, xs, y_tok, TOKENS, query_i=None, cjk=cjk)
    for i in range(n - 1):
        ax.annotate(
            "",
            xy=(xs[i + 1] - 0.42, y_tok),
            xytext=(xs[i] + 0.42, y_tok),
            arrowprops=dict(arrowstyle="-|>", color=SEQ, lw=1.15, mutation_scale=9),
            zorder=2,
        )
    ax.set_title(
        lab("排队传话（每步只看见上一步）", "Sequential / RNN — each step sees only the previous", cjk),
        loc="left",
        color=INK,
        pad=8,
        fontsize=11,
    )
    ax.text(
        xs[0],
        1.42,
        lab("信息只能一个传一个", "information is handed one step at a time", cjk),
        ha="left",
        va="center",
        fontsize=8,
        color=MUTED,
    )

    clarity = np.exp(-0.55 * np.maximum(xs - ANIMAL_I, 0))
    clarity[:ANIMAL_I] = 0.15
    bar_y, bar_h = 0.42, 0.22
    for i, x in enumerate(xs):
        t = float(clarity[i])
        face = _mix(CLEAR, HUSH, 1 - t)
        rect = Rectangle(
            (x - 0.38, bar_y),
            0.76,
            bar_h,
            facecolor=face,
            edgecolor="#c5cad0",
            linewidth=0.6,
            zorder=2,
        )
        ax.add_patch(rect)
        if i == ANIMAL_I:
            ax.text(
                x,
                bar_y + bar_h / 2,
                "animal",
                ha="center",
                va="center",
                fontsize=7,
                color="white",
                fontweight="bold",
            )
        elif i == IT_I:
            ax.text(
                x,
                bar_y + bar_h / 2,
                lab("糊", "blur", cjk),
                ha="center",
                va="center",
                fontsize=7.5,
                color=INK,
            )
        elif i == n - 1:
            ax.text(x, bar_y + bar_h / 2, "…", ha="center", va="center", fontsize=8, color=MUTED)

    ax.text(
        -0.55,
        bar_y + bar_h / 2,
        lab("印象包\n里的 animal", "packet:\nclarity of\nanimal", cjk),
        ha="right",
        va="center",
        fontsize=7.4,
        color=MUTED,
    )
    ax.annotate(
        lab("到 it 时，animal 已被挤糊", "by it, animal is squeezed / blur", cjk),
        xy=(xs[IT_I], bar_y),
        xytext=(xs[IT_I] - 1.6, 0.12),
        fontsize=8,
        color=INK,
        arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.9),
    )
    ax.text(
        xs.mean(),
        -0.05,
        lab(
            "不是人排队。方块是 token，箭头是隐状态只传给下一步。",
            "Boxes are tokens; arrows are the hidden state passed only forward.",
            cjk,
        ),
        ha="center",
        va="top",
        fontsize=7.6,
        color=MUTED,
    )

    ax = axes[1]
    _panel_frame(ax)
    y_tok = 0.55
    _token_boxes(ax, xs, y_tok, TOKENS, query_i=IT_I, cjk=cjk)
    ax.set_title(
        lab("Attention：问词 it 一次看全句", "Attention — query it sees the whole sentence at once", cjk),
        loc="left",
        color=INK,
        pad=8,
        fontsize=11,
    )
    q = xs[IT_I]
    y_src = y_tok + 0.22
    for i, w in enumerate(ATTN_W):
        if i == IT_I:
            continue
        rad = 0.18 + 0.055 * abs(i - IT_I)
        if i > IT_I:
            rad = -rad
        color = HIGH if i == ANIMAL_I else (LOW if i == STREET_I else MUTED)
        lw = 0.5 + 10.5 * w
        alpha = 0.35 + 0.65 * (w / ATTN_W.max())
        ax.annotate(
            "",
            xy=(xs[i], y_tok + 0.20),
            xytext=(q, y_src),
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                lw=lw,
                mutation_scale=8,
                connectionstyle=f"arc3,rad={rad:.3f}",
                alpha=min(alpha, 0.95),
            ),
            zorder=1,
        )
    ax.text(
        xs[ANIMAL_I],
        1.38,
        lab("权重大", "high weight", cjk),
        ha="center",
        fontsize=8,
        color=HIGH,
        fontweight="bold",
    )
    ax.text(
        xs[STREET_I],
        1.38,
        lab("权重小", "low weight", cjk),
        ha="center",
        fontsize=8,
        color=LOW,
    )
    ax.text(
        xs.mean(),
        -0.05,
        lab(
            "粗线 → animal，细线 → street。示意，不是训练好的模型。",
            "Thick → animal, thin → street. Schematic, not a trained model.",
            cjk,
        ),
        ha="center",
        va="top",
        fontsize=7.6,
        color=MUTED,
    )

    fig.suptitle(
        lab("有它 vs 没有它：同一张图上的左右对照", "With vs without attention — same figure, left / right", cjk),
        fontsize=13,
        color=INK,
        fontweight="normal",
        y=1.03,
    )
    fig.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def draw_coref(out: Path, cjk: bool) -> None:
    n = len(TOKENS)
    xs = np.arange(n, dtype=float)
    fig, ax = plt.subplots(figsize=(13.2, 4.4), constrained_layout=True)
    fig.patch.set_facecolor("white")
    ax.set_xlim(-0.7, n - 0.3)
    ax.set_ylim(-0.28, 1.88)
    ax.axis("off")
    ax.set_facecolor(BG)

    ax.set_title(
        lab("「它」在看谁", "who does it attend to", cjk),
        loc="left",
        fontsize=13,
        color=INK,
        pad=6,
    )
    ax.text(
        0.99,
        1.0,
        lab("示意 / schematic — 不是训练好的模型", "schematic — not a trained model", cjk),
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        color=MUTED,
        style="italic",
    )

    y_tok = 0.38
    _token_boxes(ax, xs, y_tok, TOKENS, query_i=IT_I, cjk=cjk)

    ymax = float(COREF_W.max())
    for i, (x, w) in enumerate(zip(xs, COREF_W)):
        h = 0.14 + 0.62 * (w / ymax)
        if i == ANIMAL_I:
            face, edge = HIGH, "#8c3d2c"
        elif i == STREET_I:
            face, edge = "#c5cad0", LOW
        elif i == TIRED_I:
            face, edge = "#8fa06c", MID
        elif i == IT_I:
            face, edge = "#b7c6d4", QUERY_EDGE
        else:
            face, edge = "#d7dbe0", BOX_EDGE
        bar = Rectangle(
            (x - 0.32, 0.72), 0.64, h, facecolor=face, edgecolor=edge, linewidth=0.7, zorder=2
        )
        ax.add_patch(bar)
        if i in {ANIMAL_I, STREET_I, TIRED_I}:
            ax.text(x, 0.72 + h + 0.03, f"{w:.2f}", ha="center", va="bottom", fontsize=8, color=INK)

    ax.text(xs[ANIMAL_I], 1.72, lab("高", "high", cjk), ha="center", fontsize=8, color=HIGH, fontweight="bold")
    ax.text(xs[STREET_I], 1.72, lab("低", "low", cjk), ha="center", fontsize=8, color=LOW)
    ax.text(xs[TIRED_I], 1.72, lab("中", "modest", cjk), ha="center", fontsize=8, color=MID)

    ax.text(
        xs.mean(),
        -0.12,
        lab(
            "query = it。animal 高、street 低、tired 中。示意权重，不是论文里的真实矩阵。",
            "query = it. High on animal, low on street, modest on tired. Schematic weights, not a trained matrix.",
            cjk,
        ),
        ha="center",
        va="top",
        fontsize=8,
        color=MUTED,
    )
    fig.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _have_pillow() -> bool:
    try:
        import PIL  # noqa: F401
    except ImportError:
        return False
    return True


def draw_process(out: Path, cjk: bool) -> None:
    """Looping GIF: sequential playhead, then attention weights grow in."""
    from matplotlib.animation import FuncAnimation, PillowWriter

    n = len(TOKENS)
    xs = np.arange(n, dtype=float)
    seq_n = n
    hold_a = 3
    attn_n = 8
    hold_b = 4
    frames = seq_n + hold_a + attn_n + hold_b
    fig, ax = plt.subplots(figsize=(12.4, 4.5))
    fig.patch.set_facecolor("white")

    def _frame_ax() -> None:
        ax.set_xlim(-0.7, n - 0.3)
        ax.set_ylim(-0.22, 1.68)
        ax.axis("off")
        ax.set_facecolor(BG)
        ax.text(
            0.995,
            0.98,
            lab("示意", "schematic", cjk),
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=7.5,
            color=MUTED,
            style="italic",
        )

    def _seq_scene(play: int) -> None:
        y_tok = 1.02
        _token_boxes(ax, xs, y_tok, TOKENS, query_i=None, cjk=cjk)
        # playhead underline
        ax.plot(
            [xs[play] - 0.36, xs[play] + 0.36],
            [y_tok - 0.24, y_tok - 0.24],
            color=SEQ,
            lw=2.0,
            solid_capstyle="round",
            zorder=5,
        )
        if play > 0:
            ax.annotate(
                "",
                xy=(xs[play] - 0.42, y_tok),
                xytext=(xs[play - 1] + 0.42, y_tok),
                arrowprops=dict(arrowstyle="-|>", color=SEQ, lw=1.6, mutation_scale=11),
                zorder=2,
            )
        # hidden-state marker at current token
        ax.scatter(
            [xs[play]],
            [y_tok + 0.30],
            s=36,
            c=SEQ,
            zorder=5,
            marker="s",
            edgecolors=INK,
            linewidths=0.4,
        )
        h_ha = "right" if play >= n - 2 else "center"
        h_x = xs[play] - 0.12 if play >= n - 2 else xs[play]
        ax.text(
            h_x,
            y_tok + 0.46,
            lab("隐状态", "h", cjk),
            ha=h_ha,
            va="bottom",
            fontsize=7,
            color=MUTED,
        )
        clarity = np.exp(-0.55 * np.maximum(xs - ANIMAL_I, 0))
        clarity[:ANIMAL_I] = 0.15
        bar_y, bar_h = 0.36, 0.22
        for i in range(play + 1):
            x = xs[i]
            t = float(clarity[i])
            face = _mix(CLEAR, HUSH, 1 - t)
            ax.add_patch(
                Rectangle(
                    (x - 0.38, bar_y),
                    0.76,
                    bar_h,
                    facecolor=face,
                    edgecolor="#c5cad0",
                    linewidth=0.6,
                    zorder=2,
                )
            )
            if i == ANIMAL_I:
                ax.text(
                    x,
                    bar_y + bar_h / 2,
                    "animal",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white",
                    fontweight="bold",
                )
            elif i == IT_I:
                ax.text(
                    x,
                    bar_y + bar_h / 2,
                    lab("糊", "blur", cjk),
                    ha="center",
                    va="center",
                    fontsize=7.5,
                    color=INK,
                )
        ax.text(
            -0.55,
            bar_y + bar_h / 2,
            lab("印象包\n里的 animal", "packet:\nclarity of\nanimal", cjk),
            ha="right",
            va="center",
            fontsize=7.2,
            color=MUTED,
        )
        ax.set_title(
            lab("排队传话，每步只看见上一步", "Sequential: each step sees only the previous", cjk),
            loc="left",
            color=INK,
            pad=6,
            fontsize=12,
        )
        ax.text(
            xs.mean(),
            -0.08,
            lab(
                "方块是 token，箭头是隐状态只传给下一步。示意。",
                "Boxes are tokens; the arrow is the hidden state passed only forward.",
                cjk,
            ),
            ha="center",
            va="top",
            fontsize=7.5,
            color=MUTED,
        )

    def _attn_scene(grow: float) -> None:
        y_tok = 0.52
        _token_boxes(ax, xs, y_tok, TOKENS, query_i=IT_I, cjk=cjk)
        q = xs[IT_I]
        y_src = y_tok + 0.22
        g = max(0.0, min(1.0, grow))
        for i, w in enumerate(ATTN_W):
            if i == IT_I:
                continue
            rad = 0.18 + 0.055 * abs(i - IT_I)
            if i > IT_I:
                rad = -rad
            color = HIGH if i == ANIMAL_I else (LOW if i == STREET_I else MUTED)
            lw = (0.5 + 10.5 * w) * g
            alpha = (0.35 + 0.65 * (w / ATTN_W.max())) * g
            if lw < 0.08 or alpha < 0.04:
                continue
            ax.annotate(
                "",
                xy=(xs[i], y_tok + 0.20),
                xytext=(q, y_src),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=color,
                    lw=lw,
                    mutation_scale=8,
                    connectionstyle=f"arc3,rad={rad:.3f}",
                    alpha=min(alpha, 0.95),
                ),
                zorder=1,
            )
        if g > 0.25:
            fade = min(1.0, (g - 0.25) / 0.75)
            ax.text(
                xs[ANIMAL_I],
                1.42,
                lab("权重大", "high weight", cjk),
                ha="center",
                fontsize=8,
                color=HIGH,
                fontweight="bold",
                alpha=fade,
            )
            ax.text(
                xs[STREET_I],
                1.42,
                lab("权重小", "low weight", cjk),
                ha="center",
                fontsize=8,
                color=LOW,
                alpha=fade,
            )
        ax.set_title(
            lab("attention，it 一次看全句", "attention: it sees the whole sentence at once", cjk),
            loc="left",
            color=INK,
            pad=6,
            fontsize=12,
        )
        ax.text(
            xs.mean(),
            -0.08,
            lab(
                "粗线 → animal，细线 → street。示意，不是训练好的模型。",
                "Thick → animal, thin → street. Schematic, not a trained model.",
                cjk,
            ),
            ha="center",
            va="top",
            fontsize=7.5,
            color=MUTED,
        )

    def update(frame: int):
        ax.clear()
        _frame_ax()
        if frame < seq_n:
            _seq_scene(frame)
        elif frame < seq_n + hold_a:
            _seq_scene(seq_n - 1)
        else:
            k = frame - (seq_n + hold_a)
            if k >= attn_n:
                grow = 1.0
            else:
                grow = (k + 1) / attn_n
            _attn_scene(grow)
        return []

    frame_ids = list(range(frames))
    anim = FuncAnimation(
        fig,
        update,
        frames=frame_ids,
        interval=200,
        blit=False,
        cache_frame_data=False,
        repeat=True,
    )
    writer = PillowWriter(fps=5)
    anim.save(str(out), writer=writer, dpi=105)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Library diagrams for /learn (adult, schematic).")
    p.add_argument("figure", choices=("seq-vs-attn", "coref", "process"))
    p.add_argument("--out", required=True, help="Output PNG or GIF path")
    p.add_argument(
        "--anim",
        action="store_true",
        help="Write a looping GIF (seq-vs-attn --anim is the same as process)",
    )
    args = p.parse_args(argv)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    want_gif = args.figure == "process" or (args.figure == "seq-vs-attn" and args.anim)
    if want_gif and not _have_pillow():
        print("GIF export needs pillow. Install with: pip install pillow", file=sys.stderr)
        return 1
    cjk = setup_style()
    if want_gif:
        draw_process(out, cjk)
    elif args.figure == "seq-vs-attn":
        draw_seq_vs_attn(out, cjk)
    else:
        draw_coref(out, cjk)
    print(out.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
