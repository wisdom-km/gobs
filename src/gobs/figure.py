"""Generic paper-figure spec (figure.json) and teach/test judge."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Any

from gobs.constants import VIZ_DIR

KINDS = ("attention", "seq")
MODES = ("teach", "test")
WEIGHTS = ("hi", "mid", "lo")
TEST_PHASES = ("retrieve", "feynman")
WEIGHT_ALIASES = {
    "hi": "hi",
    "high": "hi",
    "高": "hi",
    "mid": "mid",
    "middle": "mid",
    "med": "mid",
    "中": "mid",
    "lo": "lo",
    "low": "lo",
    "低": "lo",
}

_PUNCT = re.compile(r"[.,!?;:\"'()\[\]{}]")


class FigureError(ValueError):
    pass


def mode_from_phase(phase: str | None) -> str:
    p = (phase or "").strip().lower()
    return "test" if p in TEST_PHASES else "teach"


def bare(token: str) -> str:
    return _PUNCT.sub("", str(token or "")).strip().lower()


def normalize_weight(value: Any) -> str | None:
    if value is None:
        return None
    key = str(value).strip().lower()
    return WEIGHT_ALIASES.get(key) or WEIGHT_ALIASES.get(str(value).strip())


def split_sentence(sentence: str) -> list[str]:
    return [w for w in str(sentence or "").strip().split() if w]


def default_figure() -> dict[str, Any]:
    """Attention Is All You Need coreference example (offline fallback)."""
    sentence = "The animal didn't cross the street because it was too tired"
    tokens = split_sentence(sentence)
    return {
        "kind": "attention",
        "mode": "teach",
        "phase": "encode",
        "source": (
            "Attention Is All You Need — coreference example "
            "(The animal didn't cross the street because it was too tired)"
        ),
        "sentence": sentence,
        "tokens": tokens,
        "query": "it",
        "paper": {"animal": "hi", "street": "lo", "tired": "mid"},
        "reveal": [
            {"token": "animal", "weight": "hi", "why": "没过马路的是动物。它 = animal。"},
            {"token": "street", "weight": "lo", "why": "马路不会累。street 低。"},
            {"token": "tired", "weight": "mid", "why": "累是原因，不是「它」指的东西。"},
        ],
        "caption": "「它」在看谁",
    }


def _template_figure_bytes() -> bytes:
    try:
        return files("gobs.templates").joinpath("viz", "figure.json").read_bytes()
    except (FileNotFoundError, ModuleNotFoundError, TypeError, AttributeError):
        root = Path(__file__).resolve().parent / "templates" / "viz" / "figure.json"
        return root.read_bytes()


def packaged_figure() -> dict[str, Any]:
    raw = json.loads(_template_figure_bytes().decode("utf-8"))
    return validate_figure(raw)


def figure_path(vault: Path) -> Path:
    return vault / VIZ_DIR / "figure.json"


def _as_dict(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise FigureError("figure spec must be a JSON object")
    return data


def _tokens_of(data: dict[str, Any]) -> list[str]:
    raw = data.get("tokens")
    if isinstance(raw, list) and raw:
        out = [str(t) for t in raw if str(t).strip()]
        if out:
            return out
    return split_sentence(str(data.get("sentence") or ""))


def validate_figure(data: Any) -> dict[str, Any]:
    """Return a normalized spec. Keep the schema small."""
    spec = dict(_as_dict(data))
    kind = str(spec.get("kind") or "attention").strip().lower()
    if kind not in KINDS:
        raise FigureError(f"unknown figure kind {kind!r} (want attention|seq)")
    mode = str(spec.get("mode") or "teach").strip().lower()
    if mode not in MODES:
        raise FigureError(f"unknown figure mode {mode!r} (want teach|test)")
    tokens = _tokens_of(spec)
    if not tokens:
        raise FigureError("figure needs sentence or tokens")
    sentence = str(spec.get("sentence") or "").strip() or " ".join(tokens)
    query = str(spec.get("query") or "").strip()
    if not query:
        for tok in tokens:
            if bare(tok) in {"it", "它"}:
                query = tok
                break
        if not query:
            query = tokens[-1]
    paper_in = spec.get("paper") or {}
    if not isinstance(paper_in, dict):
        raise FigureError("paper must be an object of token → hi|mid|lo")
    paper: dict[str, str] = {}
    for key, val in paper_in.items():
        w = normalize_weight(val)
        if w is None:
            raise FigureError(f"paper weight for {key!r} must be hi|mid|lo")
        paper[str(key)] = w
    reveal_in = spec.get("reveal") or []
    if not isinstance(reveal_in, list):
        raise FigureError("reveal must be a list")
    reveal: list[dict[str, str]] = []
    for item in reveal_in:
        if not isinstance(item, dict):
            raise FigureError("reveal item must be an object")
        token = str(item.get("token") or "").strip()
        if not token:
            raise FigureError("reveal item needs token")
        w = normalize_weight(item.get("weight"))
        if w is None:
            raise FigureError(f"reveal weight for {token!r} must be hi|mid|lo")
        reveal.append(
            {
                "token": token,
                "weight": w,
                "why": str(item.get("why") or "").strip(),
            }
        )
        paper.setdefault(token, w)
    out = {
        "kind": kind,
        "mode": mode,
        "phase": str(spec.get("phase") or "").strip(),
        "source": str(spec.get("source") or "").strip(),
        "sentence": sentence,
        "tokens": tokens,
        "query": query,
        "paper": paper,
        "reveal": reveal,
        "caption": str(spec.get("caption") or "").strip(),
    }
    extra = spec.get("weights") or spec.get("attempt")
    if isinstance(extra, dict):
        out["weights"] = extract_weights(extra, tokens)
    return out


def load_figure(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        return packaged_figure()
    p = Path(path)
    if not p.is_file():
        raise FigureError(f"figure.json missing: {p}")
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FigureError(f"figure.json is not valid JSON: {exc}") from exc
    return validate_figure(raw)


def load_figure_for_vault(vault: Path, *, phase: str | None = None) -> dict[str, Any]:
    path = figure_path(vault)
    spec = load_figure(path) if path.is_file() else default_figure()
    if phase is not None:
        spec["phase"] = phase
        spec["mode"] = mode_from_phase(phase)
    return spec


def extract_weights(data: Any, tokens: list[str] | None = None) -> dict[str, str]:
    """Accept {weights:{…}}, a flat token→weight map, or index→weight."""
    if not isinstance(data, dict):
        raise FigureError("attempt must be a JSON object")
    raw = data.get("weights") if isinstance(data.get("weights"), dict) else data
    if not isinstance(raw, dict):
        raise FigureError("attempt weights must be an object")
    skip = {
        "kind",
        "mode",
        "phase",
        "source",
        "sentence",
        "tokens",
        "query",
        "paper",
        "reveal",
        "caption",
        "attempt",
        "weights",
    }
    out: dict[str, str] = {}
    token_list = tokens or []
    for key, val in raw.items():
        if key in skip:
            continue
        w = normalize_weight(val)
        if w is None:
            continue
        name = str(key)
        if token_list and name.isdigit():
            i = int(name)
            if 0 <= i < len(token_list):
                name = token_list[i]
        out[name] = w
    return out


def _why_for(reveal: list[dict[str, str]], token: str) -> str:
    want = bare(token)
    for item in reveal:
        if bare(item.get("token", "")) == want:
            return item.get("why") or ""
    return ""



@dataclass
class JudgeResult:
    ok: bool
    wrong: list[tuple[str, str, str]] = field(default_factory=list)
    extras_hi: list[str] = field(default_factory=list)
    verdict: str = ""

    @property
    def code(self) -> int:
        return 0 if self.ok else 1


def judge(
    paper: dict[str, str] | dict[str, Any],
    attempt: dict[str, Any] | None = None,
    *,
    reveal: list[dict[str, str]] | None = None,
    tokens: list[str] | None = None,
) -> JudgeResult:
    """Compare student weights to paper.

    Named paper tokens must match hi/mid/lo. A student mark of hi on a token
    the paper omits or marks lo fails. All-high fails unless the paper says so.
    """
    paper_map: dict[str, Any]
    if isinstance(paper, dict) and (
        "kind" in paper or "reveal" in paper or isinstance(paper.get("paper"), dict)
    ):
        paper_map = paper.get("paper") or {}
        if reveal is None:
            reveal = list(paper.get("reveal") or [])
        if tokens is None:
            tokens = list(paper.get("tokens") or [])
        if attempt is None:
            attempt = paper
    else:
        paper_map = paper or {}

    weights = extract_weights(attempt or {}, tokens)
    paper_norm: dict[str, str] = {}
    for key, val in (paper_map or {}).items():
        w = normalize_weight(val)
        if w:
            paper_norm[bare(str(key))] = w
    reveal = list(reveal or [])

    student_idx: dict[str, str] = {}
    student_label: dict[str, str] = {}
    for key, val in weights.items():
        student_idx[bare(key)] = val
        student_label[bare(key)] = str(key)

    wrong: list[tuple[str, str, str]] = []
    for key, expect in paper_norm.items():
        got = student_idx.get(key)
        if got != expect:
            label = student_label.get(key) or key
            wrong.append((label, got or "无", expect))

    extras_hi: list[str] = []
    for key, got in student_idx.items():
        if got != "hi":
            continue
        expect = paper_norm.get(key)
        if expect is None or expect == "lo":
            extras_hi.append(student_label.get(key) or key)

    check_tokens = [bare(t) for t in (tokens or list(weights))]
    check_tokens = [t for t in check_tokens if t]
    all_high = False
    if check_tokens and all(student_idx.get(t) == "hi" for t in check_tokens):
        covers = bool(paper_norm) and all(paper_norm.get(t) == "hi" for t in check_tokens)
        paper_all_hi = bool(paper_norm) and all(v == "hi" for v in paper_norm.values())
        if not (paper_all_hi and covers):
            all_high = True

    ok = not wrong and not extras_hi and not all_high
    result = JudgeResult(ok=ok, wrong=wrong, extras_hi=extras_hi)
    result.verdict = format_verdict(result, reveal=reveal, all_high=all_high)
    return result


def format_verdict(
    result: JudgeResult,
    *,
    reveal: list[dict[str, str]] | None = None,
    all_high: bool = False,
) -> str:
    reveal = reveal or []
    cn = {"hi": "高", "mid": "中", "lo": "低", "无": "无"}
    if result.ok:
        return "通过。标的高低和论文一致。"
    bits: list[str] = ["未过。"]
    if all_high:
        bits.append("不能把每个词都标成高（除非论文就是这样）。")
    for token, got, expect in result.wrong:
        why = _why_for(reveal, token)
        got_cn = cn.get(got, got)
        expect_cn = cn.get(expect, expect)
        line = f"{token} 你标了{got_cn}，论文是{expect_cn}"
        if why:
            line += f"（{why}）"
        bits.append(line + "。")
    extra = [t for t in result.extras_hi if bare(t) not in {bare(w[0]) for w in result.wrong}]
    if extra:
        bits.append("这些词你标了高，论文没有或标的是低：" + "、".join(extra) + "。")
    return "".join(bits)


def judge_files(
    *,
    figure: Path | dict[str, Any],
    attempt: Path | dict[str, Any] | None = None,
) -> JudgeResult:
    spec = figure if isinstance(figure, dict) else load_figure(figure)
    payload: dict[str, Any] | None
    if attempt is None:
        payload = spec
    elif isinstance(attempt, dict):
        payload = attempt
    else:
        p = Path(attempt)
        if not p.is_file():
            raise FigureError(f"attempt missing: {p}")
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise FigureError(f"attempt is not valid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise FigureError("attempt must be a JSON object")
    return judge(spec, payload, reveal=spec.get("reveal"), tokens=spec.get("tokens"))
