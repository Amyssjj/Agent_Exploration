#!/usr/bin/env python3
"""Prepare WeRead notebooks as Notion page payloads.

Fetches the signed-in user's notebooks, highlights (划线), and their own
reviews (想法 / 书评) from the WeRead Agent Gateway. Writes
prepared/<bookId>.json for Notion MCP (notion-create-pages).

Does not call Notion. Does not read secret files.

Env:
  WEREAD_API_KEY                 required to call WeRead
  NOTION_PARENT_DATA_SOURCE_ID   overrides config.json

Setup:
  cp config.example.json config.json
  # set NOTION_PARENT_DATA_SOURCE_ID and property names

Usage:
  python3 prepare.py --limit 5
  python3 prepare.py --book-id BOOK_ID
  python3 prepare.py --self-check
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GATEWAY = "https://i.weread.qq.com/api/agent/gateway"
PARENT_PLACEHOLDER = "YOUR_PARENT_DATA_SOURCE_ID"
DEFAULT_SKILL_VERSION = "1.0.4"
DEFAULT_MAX_BODY_CHARS = 100_000

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
STATE_PATH = ROOT / "state.json"
PREPARED_DIR = ROOT / "prepared"
REPORT_PATH = ROOT / "last_report.json"

_SECRET_RE = re.compile(
    r"(Bearer\s+)\S+|wrk-[A-Za-z0-9_\-]+",
    re.IGNORECASE,
)


class WeReadUpgradeRequired(RuntimeError):
    """Gateway returned upgrade_info. Callers must stop the whole run."""


def redact(text: str, limit: int = 500) -> str:
    cleaned = _SECRET_RE.sub(
        lambda m: "Bearer [redacted]" if m.group(0).lower().startswith("bearer") else "[redacted]",
        text or "",
    )
    return cleaned[:limit]


def load_config() -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "NOTION_PARENT_DATA_SOURCE_ID": "",
        "title_property": "Title",
        "author_property": "Author",
        "category_property": "Category",
        "category_value": "Reading",
        "skill_version": DEFAULT_SKILL_VERSION,
        "max_body_chars": DEFAULT_MAX_BODY_CHARS,
    }
    if CONFIG_PATH.is_file():
        file_cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if not isinstance(file_cfg, dict):
            raise SystemExit("config.json must be a JSON object")
        cfg.update({k: v for k, v in file_cfg.items() if v is not None})
    env_parent = os.environ.get("NOTION_PARENT_DATA_SOURCE_ID", "").strip()
    if env_parent:
        cfg["NOTION_PARENT_DATA_SOURCE_ID"] = env_parent
    parent = str(cfg.get("NOTION_PARENT_DATA_SOURCE_ID") or "").strip()
    cfg["NOTION_PARENT_DATA_SOURCE_ID"] = parent
    cfg["parent_configured"] = bool(parent) and parent != PARENT_PLACEHOLDER
    return cfg


def load_api_key() -> str:
    key = os.environ.get("WEREAD_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "WEREAD_API_KEY is unset. Export it in your shell. Do not commit it."
        )
    return key


def gateway_payload(api_name: str, data: Any) -> dict:
    """Validate a decoded gateway body. HTTP 200 can still be a business error."""
    if not isinstance(data, dict):
        raise RuntimeError(f"WeRead {api_name}: response was not a JSON object")
    upgrade = data.get("upgrade_info")
    if "upgrade_info" in data and upgrade not in (None, False, "", 0):
        message = ""
        if isinstance(upgrade, dict):
            message = str(upgrade.get("message") or "")
        else:
            message = str(upgrade)
        detail = redact(message)
        extra = f" {detail}" if detail else ""
        raise WeReadUpgradeRequired(
            f"WeRead {api_name} requires an upgrade before continuing.{extra}"
        )
    errcode = data.get("errcode", 0)
    try:
        code = int(errcode) if errcode not in (None, "") else 0
    except (TypeError, ValueError):
        code = -1
    if code != 0:
        summary = {
            "errcode": code,
            "errmsg": data.get("errmsg") or data.get("message") or data.get("errMsg") or "",
        }
        detail = redact(json.dumps(summary, ensure_ascii=False))
        raise RuntimeError(f"WeRead {api_name} errcode {code}: {detail}")
    return data


def weread_call(api_key: str, skill_version: str, api_name: str, **params: Any) -> dict:
    body = {"api_name": api_name, "skill_version": skill_version, **params}
    req = urllib.request.Request(
        GATEWAY,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        err_body = redact(e.read().decode("utf-8", errors="replace"))
        raise RuntimeError(f"WeRead {api_name} HTTP {e.code}: {err_body}") from e
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"WeRead {api_name}: response was not JSON") from e
    return gateway_payload(api_name, decoded)


def fetch_all_notebooks(api_key: str, skill_version: str) -> list[dict]:
    books: list[dict] = []
    last_sort = None
    for _ in range(50):
        params: dict[str, Any] = {"count": 20}
        if last_sort is not None:
            params["lastSort"] = last_sort
        data = weread_call(api_key, skill_version, "/user/notebooks", **params)
        page = data.get("books") or []
        books.extend(page)
        if not page or not data.get("hasMore"):
            break
        last_sort = page[-1].get("sort")
        if last_sort is None:
            break
    return books


def book_meta(nb: dict) -> dict:
    book = nb.get("book") if isinstance(nb.get("book"), dict) else {}
    return {
        "bookId": str(book.get("bookId") or nb.get("bookId") or ""),
        "title": (book.get("title") or nb.get("title") or "").strip(),
        "author": (book.get("author") or "").strip(),
        "cover": (book.get("cover") or "").strip(),
        "noteCount": int(nb.get("noteCount") or 0),
        "reviewCount": int(nb.get("reviewCount") or 0),
        "bookmarkCount": int(nb.get("bookmarkCount") or 0),
    }


def fetch_bookmarks(
    api_key: str, skill_version: str, book_id: str
) -> tuple[list[dict], dict[int, str]]:
    data = weread_call(api_key, skill_version, "/book/bookmarklist", bookId=book_id)
    marks = data.get("updated") or []
    chapter_map: dict[int, str] = {}
    for ch in data.get("chapters") or []:
        uid = ch.get("chapterUid")
        title = (ch.get("title") or "").strip()
        if uid is not None and title:
            chapter_map[int(uid)] = title
    return marks, chapter_map


def fetch_reviews(api_key: str, skill_version: str, book_id: str) -> list[dict]:
    out: list[dict] = []
    synckey = 0
    for _ in range(50):
        data = weread_call(
            api_key,
            skill_version,
            "/review/list/mine",
            bookid=book_id,
            synckey=synckey,
            count=50,
        )
        batch = data.get("reviews") or []
        for item in batch:
            review = item.get("review") if isinstance(item.get("review"), dict) else item
            if isinstance(review, dict):
                out.append(review)
        synckey = data.get("synckey") or synckey
        if not data.get("hasMore") or not batch:
            break
    return out


def escape_md(text: str) -> str:
    """Escape Notion-flavored markdown specials outside code blocks."""
    if not text:
        return ""
    for ch in ("\\", "*", "~", "`", "$", "[", "]", "<", ">", "{", "}", "|", "^"):
        text = text.replace(ch, "\\" + ch)
    return text


def quote_block(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    escaped = escape_md(text).replace("\n", "<br>")
    return f"> {escaped}"


def build_body(
    marks: list[dict],
    chapter_map: dict[int, str],
    reviews: list[dict],
    max_body_chars: int,
) -> tuple[str, dict]:
    """Build Notion markdown. Prefer newer items if over the size cap."""
    marks_sorted = sorted(marks, key=lambda m: int(m.get("createTime") or 0), reverse=True)
    reviews_sorted = sorted(reviews, key=lambda r: int(r.get("createTime") or 0), reverse=True)

    usable_reviews: list[dict] = []
    for r in reviews_sorted:
        content = (r.get("content") or "").strip()
        abstract = (r.get("abstract") or "").strip()
        if content or abstract:
            usable_reviews.append(r)

    def chapter_title(review: dict) -> str:
        title = (review.get("chapterTitle") or review.get("chapterName") or "").strip()
        uid = review.get("chapterUid")
        if not title and uid is not None:
            title = chapter_map.get(int(uid), "")
        return title

    def render(selected_marks: list[dict], selected_reviews: list[dict], truncated: bool) -> str:
        parts: list[str] = ["## 划线"]
        if not selected_marks:
            parts.append("_（暂无划线）_")
        else:
            by_ch: dict[Any, list[dict]] = defaultdict(list)
            for m in selected_marks:
                by_ch[m.get("chapterUid")].append(m)

            def ch_sort_key(uid: Any) -> tuple:
                title = chapter_map.get(int(uid), "") if uid is not None else ""
                return (0 if title else 1, str(title), str(uid))

            for uid in sorted(by_ch.keys(), key=ch_sort_key):
                title = chapter_map.get(int(uid), "") if uid is not None else ""
                parts.append(f"### {escape_md(title)}" if title else "### （未命名章节）")
                chapter_marks = sorted(by_ch[uid], key=lambda m: int(m.get("createTime") or 0))
                for m in chapter_marks:
                    qt = quote_block(m.get("markText") or "")
                    if qt:
                        parts.append(qt)
                        parts.append("<empty-block/>")

        parts.append("## 想法 / 书评")
        if not selected_reviews:
            parts.append("_（暂无想法或书评）_")
        else:
            for r in selected_reviews:
                ch_title = chapter_title(r)
                if ch_title:
                    parts.append(f"### {escape_md(ch_title)}")
                abstract = (r.get("abstract") or "").strip()
                content = (r.get("content") or "").strip()
                if abstract:
                    parts.append(quote_block(abstract))
                if content:
                    parts.append(escape_md(content).replace("\n", "<br>"))
                parts.append("<empty-block/>")

        if truncated:
            parts.append("---")
            parts.append("_正文过长，已优先保留较新的划线与想法；完整笔记可在微信读书中查看。_")
        return "\n".join(parts)

    selected_m = list(marks_sorted)
    selected_r = list(usable_reviews)
    truncated = False
    body = render(selected_m, selected_r, False)
    while len(body) > max_body_chars and (selected_m or selected_r):
        truncated = True
        if len(selected_m) >= len(selected_r) and selected_m:
            selected_m.pop()
        elif selected_r:
            selected_r.pop()
        elif selected_m:
            selected_m.pop()
        body = render(selected_m, selected_r, True)

    stats = {
        "marks_total": len(marks),
        "marks_included": len(selected_m),
        "reviews_total": len(reviews),
        "reviews_usable": len(usable_reviews),
        "reviews_included": len(selected_r),
        "body_chars": len(body),
        "truncated": truncated,
    }
    return body, stats


def parent_block(cfg: dict[str, Any]) -> dict[str, Any]:
    if not cfg["parent_configured"]:
        return {
            "type": "data_source_id",
            "data_source_id": None,
            "configured": False,
            "hint": "Set NOTION_PARENT_DATA_SOURCE_ID in the environment or config.json",
        }
    return {
        "type": "data_source_id",
        "data_source_id": cfg["NOTION_PARENT_DATA_SOURCE_ID"],
        "configured": True,
    }


def load_state() -> dict:
    if STATE_PATH.is_file():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"synced": {}, "updated_at": None}


def save_state(state: dict) -> None:
    state["updated_at"] = datetime.now(timezone.utc).astimezone().isoformat()
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def choose_books(
    metas: list[dict],
    *,
    limit: int,
    book_ids: list[str] | None,
    synced: dict,
    skip_titles: set[str],
    skip_synced: bool,
) -> tuple[list[dict], list[dict]]:
    """Choose notebooks to prepare.

    Already-synced titles and skipped titles are removed before --limit is
    applied, so a full page of synced top-ranked books does not hide the next
    unsynced notebook.
    """

    def score(meta: dict) -> int:
        return int(meta.get("noteCount") or 0) + int(meta.get("reviewCount") or 0)

    def ineligible(meta: dict) -> str | None:
        if skip_synced and meta["bookId"] in synced:
            return "already_in_manifest"
        if meta["title"] in skip_titles:
            return "title_exists_in_notion"
        return None

    def skip_entry(meta: dict, reason: str) -> dict:
        entry = {
            "bookId": meta["bookId"],
            "title": meta["title"],
            "author": meta.get("author") or "",
            "score": score(meta),
            "reason": reason,
        }
        if reason == "already_in_manifest":
            entry["notion_url"] = (synced.get(meta["bookId"]) or {}).get("notion_url")
        return entry

    skipped: list[dict] = []
    if book_ids:
        want = set(book_ids)
        pool = [m for m in metas if m["bookId"] in want]
    else:
        pool = sorted(metas, key=lambda m: -score(m))

    chosen: list[dict] = []
    for meta in pool:
        if book_ids is None and len(chosen) >= limit:
            break
        reason = ineligible(meta)
        if reason:
            skipped.append(skip_entry(meta, reason))
            continue
        chosen.append(meta)
    return chosen, skipped


def prepare_pages(
    api_key: str,
    cfg: dict[str, Any],
    limit: int,
    book_ids: list[str] | None,
    skip_titles: set[str],
    skip_synced: bool,
) -> dict:
    state = load_state()
    synced = state.get("synced") or {}
    skill_version = str(cfg.get("skill_version") or DEFAULT_SKILL_VERSION)
    max_body = int(cfg.get("max_body_chars") or DEFAULT_MAX_BODY_CHARS)

    notebooks = fetch_all_notebooks(api_key, skill_version)
    metas = [book_meta(nb) for nb in notebooks]
    metas = [m for m in metas if m["bookId"] and m["title"]]

    selected, skipped = choose_books(
        metas,
        limit=limit,
        book_ids=book_ids,
        synced=synced,
        skip_titles=skip_titles,
        skip_synced=skip_synced,
    )

    PREPARED_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "started_at": datetime.now().astimezone().isoformat(),
        "notebooks_total": len(metas),
        "parent_configured": cfg["parent_configured"],
        "selected": [],
        "prepared": [],
        "skipped": skipped,
        "errors": [],
    }

    for meta in selected:
        entry = {
            "bookId": meta["bookId"],
            "title": meta["title"],
            "author": meta["author"],
            "score": meta["noteCount"] + meta["reviewCount"],
        }
        report["selected"].append(entry)

        try:
            marks, chapter_map = fetch_bookmarks(api_key, skill_version, meta["bookId"])
            reviews = fetch_reviews(api_key, skill_version, meta["bookId"])
            body, stats = build_body(marks, chapter_map, reviews, max_body)
            properties: dict[str, str] = {
                str(cfg["title_property"]): meta["title"],
            }
            if cfg.get("author_property"):
                properties[str(cfg["author_property"])] = meta["author"]
            if cfg.get("category_property") and cfg.get("category_value"):
                properties[str(cfg["category_property"])] = str(cfg["category_value"])
            payload = {
                "bookId": meta["bookId"],
                "cover": meta["cover"],
                "cover_is_signed_hint": _looks_signed(meta["cover"]),
                "properties": properties,
                "content": body,
                "stats": stats,
                "parent": parent_block(cfg),
            }
            out_path = PREPARED_DIR / f"{meta['bookId']}.json"
            out_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report["prepared"].append({**entry, "path": str(out_path.name), "stats": stats})
            time.sleep(0.3)
        except WeReadUpgradeRequired:
            raise
        except Exception as e:  # noqa: BLE001
            report["errors"].append({**entry, "error": redact(str(e))})

    report["finished_at"] = datetime.now().astimezone().isoformat()
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def _looks_signed(url: str) -> bool:
    if not url:
        return False
    lowered = url.lower()
    return any(token in lowered for token in ("signature=", "expires=", "x-oss-", "token="))


def mark_synced(book_id: str, title: str, notion_url: str) -> None:
    state = load_state()
    state.setdefault("synced", {})[book_id] = {
        "title": title,
        "notion_url": notion_url,
        "synced_at": datetime.now().astimezone().isoformat(),
    }
    save_state(state)


def _fake_http_200(payload: dict) -> Any:
    class _Resp:
        def read(self) -> bytes:
            return json.dumps(payload).encode("utf-8")

        def __enter__(self) -> "_Resp":
            return self

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
            return False

    return _Resp()


def _example_notebook(book_id: str, title: str, notes: int) -> dict:
    return {
        "bookId": book_id,
        "noteCount": notes,
        "reviewCount": 0,
        "bookmarkCount": 0,
        "book": {"bookId": book_id, "title": title, "author": "Example", "cover": ""},
    }


def _check_gateway_http() -> None:
    """HTTP 200 with errcode or upgrade_info must not look like an empty success."""
    import unittest.mock as mock

    secret_body = {
        "errcode": -2012,
        "errmsg": "bad Bearer wrk-supersecretvalue",
        "books": [],
    }
    for api_name in ("/user/notebooks", "/book/bookmarklist", "/review/list/mine"):
        with mock.patch(
            "urllib.request.urlopen",
            return_value=_fake_http_200(secret_body),
        ):
            try:
                weread_call("example-key", "1.0.4", api_name)
            except WeReadUpgradeRequired as e:
                raise SystemExit(f"self-check failed: errcode raised upgrade ({e})") from e
            except RuntimeError as e:
                message = str(e)
            else:
                raise SystemExit(f"self-check failed: {api_name} errcode treated as success")
        if "wrk-" in message or "supersecret" in message:
            raise SystemExit("self-check failed: secret leaked from errcode body")
        if "errcode -2012" not in message:
            raise SystemExit(f"self-check failed: errcode missing from {message}")

    upgrade_body = {
        "errcode": 12,
        "upgrade_info": {"message": "Upgrade before continuing. Bearer wrk-supersecretvalue"},
    }
    with mock.patch("urllib.request.urlopen", return_value=_fake_http_200(upgrade_body)):
        try:
            weread_call("example-key", "1.0.4", "/book/bookmarklist", bookId="example-book")
        except WeReadUpgradeRequired as e:
            upgrade_message = str(e)
        else:
            raise SystemExit("self-check failed: upgrade_info was ignored")
    if "wrk-" in upgrade_message or "supersecret" in upgrade_message:
        raise SystemExit("self-check failed: secret leaked from upgrade_info")
    if "upgrade" not in upgrade_message.lower():
        raise SystemExit("self-check failed: upgrade error did not name the stop")


def _check_upgrade_stops_run() -> None:
    """upgrade_info from a per-book call must leave prepare_pages, not the error list."""
    import tempfile
    import unittest.mock as mock

    notebooks = [_example_notebook("example-a", "Example A", 3), _example_notebook("example-b", "Example B", 1)]
    calls: list[str] = []

    def fake_call(api_key: str, skill_version: str, api_name: str, **params: Any) -> dict:
        calls.append(api_name + ":" + str(params.get("bookId") or params.get("bookid") or ""))
        if api_name == "/user/notebooks":
            return {"books": notebooks, "hasMore": 0}
        if api_name == "/book/bookmarklist" and params.get("bookId") == "example-a":
            raise WeReadUpgradeRequired("WeRead /book/bookmarklist requires an upgrade before continuing.")
        raise AssertionError(f"unexpected call after upgrade: {api_name} {params}")

    cfg = load_config()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        old = (STATE_PATH, PREPARED_DIR, REPORT_PATH)
        try:
            globals()["STATE_PATH"] = root / "state.json"
            globals()["PREPARED_DIR"] = root / "prepared"
            globals()["REPORT_PATH"] = root / "last_report.json"
            with mock.patch(f"{__name__}.weread_call", side_effect=fake_call):
                try:
                    prepare_pages("example-key", cfg, limit=5, book_ids=None, skip_titles=set(), skip_synced=True)
                except WeReadUpgradeRequired:
                    pass
                else:
                    raise SystemExit("self-check failed: upgrade_info was swallowed")
        finally:
            globals()["STATE_PATH"], globals()["PREPARED_DIR"], globals()["REPORT_PATH"] = old
    if any(item.endswith("example-b") for item in calls):
        raise SystemExit("self-check failed: run continued after upgrade_info")


def _check_errcode_stays_on_that_book() -> None:
    """A non-zero errcode fails that book and the run continues."""
    import tempfile
    import unittest.mock as mock

    notebooks = [
        _example_notebook("example-a", "Example A", 4),
        _example_notebook("example-b", "Example B", 2),
    ]

    def fake_call(api_key: str, skill_version: str, api_name: str, **params: Any) -> dict:
        if api_name == "/user/notebooks":
            return {"books": notebooks, "hasMore": 0}
        if api_name == "/book/bookmarklist" and params.get("bookId") == "example-a":
            raise RuntimeError('WeRead /book/bookmarklist errcode -2012: {"errmsg": "[redacted]"}')
        if api_name == "/book/bookmarklist":
            return {"updated": [], "chapters": []}
        if api_name == "/review/list/mine":
            return {"reviews": [], "hasMore": 0}
        raise AssertionError(api_name)

    cfg = load_config()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        old = (STATE_PATH, PREPARED_DIR, REPORT_PATH)
        try:
            globals()["STATE_PATH"] = root / "state.json"
            globals()["PREPARED_DIR"] = root / "prepared"
            globals()["REPORT_PATH"] = root / "last_report.json"
            with mock.patch(f"{__name__}.weread_call", side_effect=fake_call):
                report = prepare_pages(
                    "example-key",
                    cfg,
                    limit=5,
                    book_ids=None,
                    skip_titles=set(),
                    skip_synced=True,
                )
        finally:
            globals()["STATE_PATH"], globals()["PREPARED_DIR"], globals()["REPORT_PATH"] = old
    if [e["bookId"] for e in report["errors"]] != ["example-a"]:
        raise SystemExit(f"self-check failed: errcode did not stay on one book ({report['errors']})")
    if [p["bookId"] for p in report["prepared"]] != ["example-b"]:
        raise SystemExit("self-check failed: later book was not prepared after errcode")


def _check_limit_skips_synced_first() -> None:
    """Top-ranked synced books must not consume --limit."""
    metas = [
        book_meta(_example_notebook(f"example-{i}", f"Example {i}", 50 - i))
        for i in range(6)
    ]
    synced = {f"example-{i}": {"notion_url": "https://www.notion.so/example"} for i in range(5)}
    chosen, skipped = choose_books(
        metas,
        limit=5,
        book_ids=None,
        synced=synced,
        skip_titles=set(),
        skip_synced=True,
    )
    chosen_ids = [m["bookId"] for m in chosen]
    if chosen_ids != ["example-5"]:
        raise SystemExit(f"self-check failed: limit ate synced books, chose {chosen_ids}")
    if {s["bookId"] for s in skipped} != {f"example-{i}" for i in range(5)}:
        raise SystemExit("self-check failed: synced books were not recorded as skipped")

    import tempfile
    import unittest.mock as mock

    fetched: list[str] = []

    def fake_call(api_key: str, skill_version: str, api_name: str, **params: Any) -> dict:
        if api_name == "/user/notebooks":
            return {"books": [_example_notebook(m["bookId"], m["title"], m["noteCount"]) for m in metas], "hasMore": 0}
        if api_name == "/book/bookmarklist":
            fetched.append(str(params.get("bookId")))
            return {
                "updated": [
                    {
                        "markText": "Example highlight sentence.",
                        "chapterUid": 1,
                        "createTime": 1,
                    }
                ],
                "chapters": [{"chapterUid": 1, "title": "Example chapter"}],
            }
        if api_name == "/review/list/mine":
            return {"reviews": [], "hasMore": 0}
        raise AssertionError(api_name)

    cfg = load_config()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        old = (STATE_PATH, PREPARED_DIR, REPORT_PATH)
        try:
            globals()["STATE_PATH"] = root / "state.json"
            globals()["PREPARED_DIR"] = root / "prepared"
            globals()["REPORT_PATH"] = root / "last_report.json"
            save_state({"synced": synced, "updated_at": None})
            with mock.patch(f"{__name__}.weread_call", side_effect=fake_call):
                report = prepare_pages(
                    "example-key",
                    cfg,
                    limit=5,
                    book_ids=None,
                    skip_titles=set(),
                    skip_synced=True,
                )
        finally:
            globals()["STATE_PATH"], globals()["PREPARED_DIR"], globals()["REPORT_PATH"] = old
    prepared_ids = [p["bookId"] for p in report["prepared"]]
    if prepared_ids != ["example-5"]:
        raise SystemExit(f"self-check failed: did not prepare the next unsynced book ({prepared_ids})")
    if fetched != ["example-5"]:
        raise SystemExit(f"self-check failed: fetched synced books {fetched}")


def self_check(cfg: dict[str, Any]) -> None:
    """Synthetic checks. No network."""
    marks = [
        {
            "bookmarkId": "example-mark",
            "bookId": "example-book",
            "chapterUid": 1,
            "markText": "Example highlight sentence.",
            "createTime": 1700000000,
        }
    ]
    reviews = [
        {
            "reviewId": "example-review",
            "content": "Example idea about the highlight.",
            "abstract": "Example highlight sentence.",
            "chapterUid": 1,
            "chapterName": "Example chapter",
            "createTime": 1700000100,
        }
    ]
    body, stats = build_body(marks, {1: "Example chapter"}, reviews, int(cfg["max_body_chars"]))
    if "Example highlight sentence." not in body:
        raise SystemExit("self-check failed: highlight missing from markdown")
    if "## 划线" not in body or "## 想法 / 书评" not in body:
        raise SystemExit("self-check failed: section headings missing")
    print("self-check ok")
    print(
        f"marks={stats['marks_included']}/{stats['marks_total']} "
        f"reviews={stats['reviews_included']}/{stats['reviews_usable']} "
        f"chars={stats['body_chars']}"
    )
    if cfg["parent_configured"]:
        print("parent: configured")
    else:
        print("parent: unset (set NOTION_PARENT_DATA_SOURCE_ID before creating pages)")
    _check_gateway_http()
    _check_upgrade_stops_run()
    _check_errcode_stays_on_that_book()
    _check_limit_skips_synced_first()
    print("gateway and limit checks ok")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare WeRead notebooks for Notion MCP")
    parser.add_argument("--limit", type=int, default=5, help="Top N books by highlight+review count")
    parser.add_argument("--book-id", action="append", dest="book_ids", help="Specific book id")
    parser.add_argument("--dry-run", action="store_true", help="Alias: prepare only (Notion is never called)")
    parser.add_argument("--skip-synced", action="store_true", default=True)
    parser.add_argument("--no-skip-synced", action="store_false", dest="skip_synced")
    parser.add_argument("--skip-title", action="append", default=[], help="Title already in Notion")
    parser.add_argument(
        "--mark-synced",
        nargs=3,
        metavar=("BOOK_ID", "TITLE", "NOTION_URL"),
        help="Record a Notion page URL in local state.json",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Build synthetic markdown and exit (no WeRead, no Notion)",
    )
    args = parser.parse_args()
    cfg = load_config()

    if args.self_check:
        self_check(cfg)
        return

    if args.mark_synced:
        book_id, title, notion_url = args.mark_synced
        mark_synced(book_id, title, notion_url)
        print(f"Recorded sync for book {book_id}")
        return

    api_key = load_api_key()
    try:
        report = prepare_pages(
            api_key,
            cfg,
            limit=args.limit,
            book_ids=args.book_ids,
            skip_titles=set(args.skip_title or []),
            skip_synced=args.skip_synced,
        )
    except WeReadUpgradeRequired as e:
        raise SystemExit(str(e)) from e

    print(f"Notebooks: {report['notebooks_total']}")
    print(f"Selected: {len(report['selected'])}")
    print(f"Prepared: {len(report['prepared'])}")
    print(f"Skipped: {len(report['skipped'])}")
    print(f"Errors: {len(report['errors'])}")
    print(f"Parent configured: {report['parent_configured']}")
    for p in report["prepared"]:
        st = p.get("stats") or {}
        print(
            f"  prepared {p['title']} "
            f"marks={st.get('marks_included')}/{st.get('marks_total')} "
            f"reviews={st.get('reviews_included')}/{st.get('reviews_usable')} "
            f"chars={st.get('body_chars')}"
        )
    for s in report["skipped"]:
        print(f"  skip {s['title']}: {s.get('reason')}")
    for e in report["errors"]:
        print(f"  error {e['title']}: {e.get('error')}")
    print(f"Report: {REPORT_PATH.name}")
    print(f"Prepared dir: {PREPARED_DIR.name}/")
    if args.dry_run or not cfg["parent_configured"]:
        print("Notion create is a separate MCP step. Use prepared JSON with notion-create-pages.")


if __name__ == "__main__":
    main()
