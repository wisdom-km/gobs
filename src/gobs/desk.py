"""Local three-pane learn desk: chat + figure + notes. stdlib only."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import traceback
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from importlib.resources import files
from pathlib import Path
from typing import Any, Callable
from wsgiref.simple_server import WSGIServer, make_server
from socketserver import ThreadingMixIn

from gobs.config import load_user_config, load_vault_config
from gobs.constants import DEFAULT_TRANSCRIPTS, VIZ_DIR
from gobs.figure import (
    FigureError,
    default_figure,
    figure_path,
    judge,
    load_figure_for_vault,
    mode_from_phase,
    validate_figure,
)
from gobs.learn import (
    PHASE_SECTION,
    DomainCard,
    find_domain,
    list_domains,
    parse_card,
    split_front,
    split_sections,
)

_HTML_ESC = (
    ("&", "&amp;"),
    ("<", "&lt;"),
    (">", "&gt;"),
    ('"', "&quot;"),
)


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


def _pkg_text(*parts: str) -> str:
    try:
        return files("gobs.templates").joinpath(*parts).read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, TypeError, AttributeError):
        root = Path(__file__).resolve().parent / "templates"
        return root.joinpath(*parts).read_text(encoding="utf-8")


def escape_html(text: str) -> str:
    out = str(text or "")
    for a, b in _HTML_ESC:
        out = out.replace(a, b)
    return out


def md_to_html(text: str) -> str:
    """Tiny markdown subset: headings, fences, lists, inline code, paragraphs."""
    src = text or ""
    lines = src.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    in_ul = False
    in_ol = False

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def inline(s: str) -> str:
        s = escape_html(s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        return s

    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            close_lists()
            buf: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            out.append("<pre><code>" + escape_html("\n".join(buf)) + "</code></pre>")
            continue
        m = re.match(r"^(#{1,3})\s+(.+)$", line)
        if m:
            close_lists()
            n = len(m.group(1))
            out.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
            i += 1
            continue
        if re.match(r"^\s*[-*]\s+", line):
            if not in_ul:
                close_lists()
                out.append("<ul>")
                in_ul = True
            out.append("<li>" + inline(re.sub(r"^\s*[-*]\s+", "", line)) + "</li>")
            i += 1
            continue
        if re.match(r"^\s*\d+\.\s+", line):
            if not in_ol:
                close_lists()
                out.append("<ol>")
                in_ol = True
            out.append("<li>" + inline(re.sub(r"^\s*\d+\.\s+", "", line)) + "</li>")
            i += 1
            continue
        if not line.strip():
            close_lists()
            i += 1
            continue
        close_lists()
        para = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
            r"^(#{1,3}\s+|```|\s*[-*]\s+|\s*\d+\.\s+)", lines[i]
        ):
            para.append(lines[i])
            i += 1
        out.append("<p>" + inline(" ".join(para)) + "</p>")
    close_lists()
    return "\n".join(out)


def resolve_note(vault: Path, note: str | None) -> DomainCard | None:
    if note:
        rel = note.replace("\\", "/").lstrip("/")
        dest = vault / rel
        card = parse_card(dest, vault) if dest.is_file() else None
        if card:
            return card
        found = find_domain(vault, Path(rel).stem)
        if found:
            return parse_card(found, vault)
    cards = list_domains(vault)
    return cards[0] if cards else None


def current_section(vault: Path, card: DomainCard | None) -> tuple[str, str]:
    if not card:
        return "", ""
    heading = PHASE_SECTION.get(card.phase, PHASE_SECTION["enough"])
    text = (vault / card.path).read_text(encoding="utf-8")
    _, body = split_front(text)
    _, secs = split_sections(body)
    for h, content in secs:
        if h == heading:
            return heading, content.strip()
    return heading, ""


def latest_lecture(vault: Path, card: DomainCard | None) -> tuple[str, str]:
    cfg = load_vault_config(vault, load_user_config())
    tdir = vault / (cfg.transcripts or DEFAULT_TRANSCRIPTS)
    if not tdir.is_dir():
        return "", ""
    files_md = [
        p
        for p in tdir.glob("*.md")
        if p.is_file() and not p.name.startswith("desk-")
    ]
    if card:
        slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", card.title).strip("-").lower()
        stem = card.path.stem.lower()
        preferred = [
            p
            for p in files_md
            if slug and slug.lower() in p.name.lower()
            or stem and stem.lower() in p.name.lower()
        ]
        if preferred:
            files_md = preferred
    if not files_md:
        return "", ""
    newest = max(files_md, key=lambda p: p.stat().st_mtime)
    return newest.name, newest.read_text(encoding="utf-8")


def _now_stamp() -> str:
    # UTC; caller may label. Filename uses compact UTC.
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


class DeskApp:
    """WSGI app for `gobs learn desk`."""

    def __init__(self, vault: Path, note: str | None = None) -> None:
        self.vault = vault.resolve()
        self.note_arg = note
        self.session_id = _now_stamp()
        self.transcript = (
            self.vault / DEFAULT_TRANSCRIPTS / f"desk-{self.session_id}.md"
        )
        user = load_user_config()
        self.cfg = load_vault_config(self.vault, user)
        self._boot_sent = False

    def card(self) -> DomainCard | None:
        env_note = os.environ.get("GOBS_LEARN_NOTE") or self.note_arg
        return resolve_note(self.vault, env_note)

    def status(self) -> dict[str, Any]:
        card = self.card()
        phase = card.phase if card else "enough"
        return {
            "title": card.title if card else "",
            "phase": phase,
            "level": card.level if card else "L0",
            "mode": mode_from_phase(phase),
            "note": card.rel if card else (self.note_arg or ""),
            "vault": str(self.vault),
            "session": self.session_id,
        }

    def figure_spec(self) -> dict[str, Any]:
        card = self.card()
        phase = card.phase if card else None
        try:
            return load_figure_for_vault(self.vault, phase=phase)
        except FigureError:
            spec = default_figure()
            if phase:
                spec["phase"] = phase
                spec["mode"] = mode_from_phase(phase)
            return spec

    def notes_payload(self) -> dict[str, Any]:
        card = self.card()
        heading, section = current_section(self.vault, card)
        lecture_name, lecture = latest_lecture(self.vault, card)
        title = card.title if card else "（还没有领域卡）"
        phase = card.phase if card else ""
        parts = [f"# {title}"]
        if phase:
            parts.append(f"phase：{phase}" + (f" · {heading}" if heading else ""))
        if section:
            parts.append(f"## {heading}\n\n{section}" if heading else section)
        else:
            parts.append("（这一节还是空的。）")
        if lecture:
            parts.append(f"## 最近讲解（{lecture_name}）\n\n{lecture}")
        else:
            parts.append("## 最近讲解\n\n还没有讲解归档。课桌上的对话不要直接当 `gobs learn save` 的讲义。")
        markdown = "\n\n".join(parts).strip() + "\n"
        return {
            "title": title,
            "phase": phase,
            "heading": heading,
            "lecture": lecture_name,
            "markdown": markdown,
            "html": md_to_html(markdown),
        }

    def write_figure(self, data: Any) -> dict[str, Any]:
        spec = validate_figure(data)
        dest = figure_path(self.vault)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            json.dumps(spec, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return spec

    def persist_chat(self, user_text: str, assistant: str) -> None:
        self.transcript.parent.mkdir(parents=True, exist_ok=True)
        if not self.transcript.exists():
            header = (
                f"# desk {self.session_id}\n\n"
                "课桌对话日志。说话人已标出。这不是讲解，不要喂给 `gobs learn save`。\n\n"
            )
            self.transcript.write_text(header, encoding="utf-8")
        block = f"## 学生\n\n{user_text.strip()}\n\n## 教练\n\n{assistant.strip()}\n\n"
        with self.transcript.open("a", encoding="utf-8") as fh:
            fh.write(block)

    def chat(self, text: str) -> dict[str, str]:
        text = (text or "").strip()
        if not text:
            return {"role": "assistant", "text": "先写一句再送。", "ok": False}
        card = self.card()
        note = card.rel if card else (self.note_arg or "")
        reply, source = run_cli_turn(
            self.vault,
            text,
            cli=self.cfg.cli,
            note=note,
        )
        self.persist_chat(text, reply)
        return {"role": "assistant", "text": reply, "ok": True, "source": source}

    def __call__(self, environ: dict[str, Any], start_response: Callable) -> list[bytes]:
        method = (environ.get("REQUEST_METHOD") or "GET").upper()
        path = environ.get("PATH_INFO") or "/"
        try:
            status, headers, body = self.dispatch(method, path, environ)
        except FigureError as exc:
            status, headers, body = _json_error(400, str(exc))
        except Exception as exc:  # noqa: BLE001 — desk must not crash the page
            traceback.print_exc()
            status, headers, body = _json_error(500, f"desk error: {exc}")
        start_response(status, headers)
        return [body]

    def dispatch(
        self, method: str, path: str, environ: dict[str, Any]
    ) -> tuple[str, list[tuple[str, str]], bytes]:
        if path in {"/", "/desk", "/desk.html"} and method == "GET":
            html = _pkg_text("desk.html")
            return _html(html)
        if path in {"/process", "/process.html"} and method == "GET":
            return _html(_pkg_text("viz", "process.html"))
        if path == "/figure.json" and method == "GET":
            return _json(self.figure_spec())
        if path == "/figure" and method == "GET":
            return _json(self.figure_spec())
        if path == "/figure" and method == "PUT":
            spec = self.write_figure(_read_json(environ))
            return _json(spec)
        if path == "/judge" and method == "POST":
            spec = self.figure_spec()
            attempt = _read_json(environ)
            result = judge(
                spec, attempt, reveal=spec.get("reveal"), tokens=spec.get("tokens")
            )
            return _json(
                {
                    "ok": result.ok,
                    "code": result.code,
                    "verdict": result.verdict,
                    "wrong": [
                        {"token": t, "got": g, "paper": p} for t, g, p in result.wrong
                    ],
                    "extras_hi": result.extras_hi,
                },
                status=200 if result.ok else 200,
            )
        if path == "/notes" and method == "GET":
            return _json(self.notes_payload())
        if path == "/chat" and method == "POST":
            payload = _read_json(environ)
            text = str(payload.get("text") or payload.get("message") or "")
            return _json(self.chat(text))
        if path == "/status" and method == "GET":
            return _json(self.status())
        if path.startswith("/viz/") and method == "GET":
            name = path[len("/viz/") :]
            if name and ".." not in name and "/" not in name:
                dest = self.vault / VIZ_DIR / name
                if dest.is_file():
                    return _file(dest)
        return _plain(HTTPStatus.NOT_FOUND, "not found")


def _read_json(environ: dict[str, Any]) -> dict[str, Any]:
    length = int(environ.get("CONTENT_LENGTH") or 0)
    raw = environ["wsgi.input"].read(length) if length else b"{}"
    if not raw:
        return {}
    try:
        data = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise FigureError(f"JSON 读不出来：{exc}") from exc
    if not isinstance(data, dict):
        raise FigureError("body must be a JSON object")
    return data


def _status_line(code: int, phrase: str | None = None) -> str:
    try:
        st = HTTPStatus(code)
        return f"{st.value} {st.phrase}"
    except ValueError:
        return f"{code} {phrase or 'OK'}"


def _html(text: str) -> tuple[str, list[tuple[str, str]], bytes]:
    body = text.encode("utf-8")
    return (
        _status_line(200),
        [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
        ],
        body,
    )


def _json(data: Any, status: int = 200) -> tuple[str, list[tuple[str, str]], bytes]:
    body = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return (
        _status_line(status),
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
        ],
        body,
    )


def _json_error(code: int, message: str) -> tuple[str, list[tuple[str, str]], bytes]:
    return _json({"ok": False, "error": message}, status=code)


def _plain(status: HTTPStatus, text: str) -> tuple[str, list[tuple[str, str]], bytes]:
    body = text.encode("utf-8")
    return (
        f"{status.value} {status.phrase}",
        [("Content-Type", "text/plain; charset=utf-8"), ("Content-Length", str(len(body)))],
        body,
    )


def _file(path: Path) -> tuple[str, list[tuple[str, str]], bytes]:
    data = path.read_bytes()
    ctype = "application/octet-stream"
    if path.suffix == ".html":
        ctype = "text/html; charset=utf-8"
    elif path.suffix == ".json":
        ctype = "application/json; charset=utf-8"
    elif path.suffix == ".md":
        ctype = "text/markdown; charset=utf-8"
    elif path.suffix == ".js":
        ctype = "text/javascript; charset=utf-8"
    elif path.suffix == ".css":
        ctype = "text/css; charset=utf-8"
    return (
        _status_line(200),
        [("Content-Type", ctype), ("Content-Length", str(len(data)))],
        data,
    )


def run_cli_turn(
    vault: Path,
    text: str,
    *,
    cli: str = "grok",
    note: str = "",
    timeout: int = 180,
) -> tuple[str, str]:
    """Run the vault CLI for one chat turn. Never raise into the page."""
    env = os.environ.copy()
    env["GOBS"] = "1"
    env["GOBS_VAULT"] = str(vault)
    env["GOBS_CLI"] = cli
    env["GOBS_LEARN"] = "1"
    if note:
        env["GOBS_LEARN_NOTE"] = note
    exe = shutil.which(cli)
    if not exe:
        return (
            "本机没有找到 "
            + cli
            + "。消息已记下。图和笔记还能用，装好 CLI 后再聊。",
            "local",
        )
    argv = [exe]
    if Path(exe).name.startswith("grok") or cli == "grok":
        argv.extend(["--single", text, "--cwd", str(vault), "--always-approve"])
    else:
        argv.extend(["--single", text])
    try:
        proc = subprocess.run(
            argv,
            cwd=str(vault),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ("CLI 超时。这轮没答上。图和笔记还在。", "local")
    except OSError as exc:
        return (f"没法启动 {cli}：{exc}。消息已记下。", "local")
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if out:
        return out, cli
    if err:
        return f"{cli} 没有正文，只有报错：\n{err}", "local"
    return f"{cli} 没有输出。消息已记下。", "local"


def serve_desk(
    vault: Path,
    *,
    port: int = 8765,
    note: str | None = None,
    open_browser: bool = True,
    host: str = "127.0.0.1",
) -> int:
    app = DeskApp(vault, note=note)
    httpd = make_server(host, port, app, ThreadingWSGIServer)
    url = f"http://{host}:{port}/"
    print(f"gobs learn desk: {url}")
    print(f"gobs learn desk: vault {vault}")
    if note:
        print(f"gobs learn desk: note  {note}")
    print("gobs learn desk: 不启动 Obsidian。停：Ctrl+C")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception as exc:  # noqa: BLE001
            print(f"gobs learn desk: browser: {exc}", file=sys.stderr)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\ngobs learn desk: stopped")
        return 0
    finally:
        httpd.server_close()
    return 0
