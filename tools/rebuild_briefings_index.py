#!/usr/bin/env python3
"""Maintain briefing metadata and render the public briefings archive."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
MANIFEST_PATH = CONTENT_DIR / "briefings.json"
PUBLIC_MANIFEST_PATH = ROOT / "briefings.json"
BRIEFINGS_HTML = ROOT / "briefings.html"


class BriefingCardParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cards: list[dict[str, str]] = []
        self._card: dict[str, str] | None = None
        self._field: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        classes = set((attr.get("class") or "").split())
        if tag == "div" and "briefing-card" in classes:
            self._card = {"lang": attr.get("data-lang") or "en"}
            return
        if self._card is None:
            return
        if tag == "a" and attr.get("href"):
            self._card["url"] = normalize_url(attr["href"] or "")
        elif tag == "div" and "briefing-title" in classes:
            self._field = "title"
        elif tag == "div" and "briefing-meta" in classes:
            self._field = "meta"

    def handle_data(self, data: str) -> None:
        if self._card is not None and self._field:
            current = self._card.get(self._field, "")
            self._card[self._field] = (current + data).strip()

    def handle_endtag(self, tag: str) -> None:
        if self._field and tag == "div":
            self._field = None
        elif self._card is not None and tag == "div" and self._card.get("title"):
            self.cards.append(self._card)
            self._card = None


def cst_now() -> datetime:
    return datetime.now(timezone(timedelta(hours=8)))


def normalize_url(url: str) -> str:
    url = url.strip()
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return url if url.startswith("/") else "/" + url


def date_from_meta(meta: str) -> str:
    text = (meta or "").split("·", 1)[0].strip()
    for pattern in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            pass
    match = re.search(r"(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})", meta or "")
    if match:
        year, month, day = match.groups()
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    return ""


def display_date(date_str: str, lang: str = "en") -> str:
    if not date_str:
        return "Undated"
    date = datetime.strptime(date_str, "%Y-%m-%d")
    if lang == "zh":
        return f"{date.year}年{date.month}月{date.day}日"
    return date.strftime("%b %d, %Y")


def load_manifest() -> dict[str, object]:
    if not MANIFEST_PATH.exists():
        return {"briefings": []}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def save_manifest(manifest: dict[str, object]) -> None:
    CONTENT_DIR.mkdir(exist_ok=True)
    manifest["updated_at"] = cst_now().isoformat(timespec="seconds")
    briefings = sorted(
        manifest.get("briefings", []),
        key=lambda item: (item.get("date", ""), item.get("published_at", ""), item.get("url", "")),
        reverse=True,
    )
    manifest["briefings"] = briefings
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    MANIFEST_PATH.write_text(text, encoding="utf-8")
    PUBLIC_MANIFEST_PATH.write_text(text, encoding="utf-8")


def bootstrap_from_html() -> dict[str, object]:
    parser = BriefingCardParser()
    parser.feed(BRIEFINGS_HTML.read_text(encoding="utf-8"))
    items: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for card in parser.cards:
        url = normalize_url(card.get("url", ""))
        lang = card.get("lang") or "en"
        key = (url, lang)
        if not url or key in seen:
            continue
        seen.add(key)
        meta = card.get("meta", "")
        date = date_from_meta(meta)
        section = "daily" if "/briefings/daily/" in url else "research"
        items.append({
            "date": date,
            "lang": lang,
            "title": card.get("title", "").strip(),
            "url": url,
            "section": section,
            "source": "legacy-briefings-html",
            "published_at": f"{date}T00:00:00+08:00" if date else "",
            "meta": meta,
        })
    return {
        "version": 1,
        "updated_at": cst_now().isoformat(timespec="seconds"),
        "briefings": items,
    }


def upsert_briefing(manifest: dict[str, object], entry: dict[str, str]) -> None:
    briefings = list(manifest.get("briefings", []))
    entry["url"] = normalize_url(entry["url"])
    entry.setdefault("section", "daily")
    entry.setdefault("published_at", f"{entry.get('date', '')}T00:00:00+08:00")
    entry.setdefault("source", "manual")
    replaced = False
    for index, existing in enumerate(briefings):
        if existing.get("url") == entry["url"] and existing.get("lang") == entry.get("lang", "en"):
            briefings[index] = {**existing, **entry}
            replaced = True
            break
    if not replaced:
        briefings.append(entry)
    manifest["briefings"] = briefings


def render_card(item: dict[str, str]) -> str:
    lang = item.get("lang", "en")
    label = "每日简报" if lang == "zh" else "Daily Briefing"
    date_label = display_date(item.get("date", ""), lang)
    title = html.escape(item.get("title", "Untitled briefing"))
    url = html.escape(item.get("url", "#"))
    meta = f"{date_label} · {label}"
    return f"""          <article class="briefing-card" data-lang="{html.escape(lang)}">
            <a href="{url}">
              <div>
                <div class="briefing-title">{title}</div>
                <div class="briefing-meta">{html.escape(meta)}</div>
              </div>
              <div class="arrow">→</div>
            </a>
          </article>"""


def render_empty(lang: str) -> str:
    text = "No Chinese briefings have been published yet." if lang == "zh" else "No English briefings have been published yet."
    return f"""          <div class="empty-state">{html.escape(text)}</div>"""


def render_index(manifest: dict[str, object]) -> None:
    items = list(manifest.get("briefings", []))
    en_items = [item for item in items if item.get("lang") == "en"]
    zh_items = [item for item in items if item.get("lang") == "zh"]
    updated = manifest.get("updated_at") or cst_now().isoformat(timespec="seconds")
    en_cards = "\n".join(render_card(item) for item in en_items) or render_empty("en")
    zh_cards = "\n".join(render_card(item) for item in zh_items) or render_empty("zh")
    html_text = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Daily Briefings — ChinaVol</title>
  <meta name="description" content="ChinaVol daily briefings archive in English and Chinese.">
  <meta property="og:title" content="Daily Briefings — ChinaVol">
  <meta property="og:description" content="ChinaVol daily briefings archive in English and Chinese.">
  <meta property="og:url" content="https://chinavol.com/briefings.html">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@chinavol1">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #08090a;
      --panel: #101214;
      --surface: rgba(255,255,255,0.045);
      --border: rgba(255,255,255,0.1);
      --text: #f7f8f8;
      --muted: #8d939d;
      --gold: #f59e0b;
      --cyan: #38bdf8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        linear-gradient(rgba(255,255,255,0.024) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.024) 1px, transparent 1px),
        var(--bg);
      background-size: 44px 44px;
      color: var(--text);
    }}
    a {{ color: inherit; text-decoration: none; }}
    .shell {{ width: min(1080px, calc(100vw - 40px)); margin: 0 auto; }}
    header {{
      min-height: 74px;
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 18px;
      align-items: center;
      border-bottom: 1px solid var(--border);
    }}
    .brand {{ display: inline-flex; align-items: center; gap: 11px; font-weight: 900; }}
    .brand img {{ width: 34px; height: 34px; border-radius: 8px; border: 1px solid rgba(245,158,11,0.45); object-fit: cover; }}
    nav {{
      justify-self: center;
      display: flex;
      align-items: center;
      gap: 6px;
      max-width: 100%;
      overflow-x: auto;
      padding: 4px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: rgba(255,255,255,0.035);
      scrollbar-width: none;
    }}
    nav::-webkit-scrollbar {{ display: none; }}
    nav a {{
      min-height: 34px;
      display: inline-flex;
      align-items: center;
      border-radius: 6px;
      padding: 0 12px;
      color: #b9c0ca;
      font-size: 0.88rem;
      font-weight: 750;
      white-space: nowrap;
    }}
    nav a.active {{ background: #f6f7f9; color: #08090a; }}
    .stamp, .label {{
      font: 700 0.72rem "JetBrains Mono", ui-monospace, monospace;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
    }}
    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 24px;
      align-items: end;
      padding: 58px 0 28px;
      border-bottom: 1px solid var(--border);
    }}
    h1 {{
      margin: 0;
      font-size: clamp(3rem, 7vw, 6.4rem);
      line-height: 0.9;
      letter-spacing: 0;
    }}
    .subtitle {{
      max-width: 660px;
      color: #bec5d0;
      line-height: 1.6;
      font-size: 1.08rem;
      margin: 22px 0 0;
    }}
    .tabs {{
      display: inline-flex;
      gap: 6px;
      padding: 4px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: rgba(255,255,255,0.035);
    }}
    .tab {{
      min-height: 38px;
      border: 0;
      border-radius: 6px;
      background: transparent;
      color: #b9c0ca;
      padding: 0 14px;
      font: 800 0.9rem Inter, system-ui, sans-serif;
      cursor: pointer;
    }}
    .tab.active {{ background: #f6f7f9; color: #08090a; }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin: 20px 0 18px;
    }}
    .metric {{
      border: 1px solid var(--border);
      border-radius: 8px;
      background: rgba(255,255,255,0.035);
      padding: 16px;
    }}
    .metric strong {{ display: block; margin-top: 8px; font-size: 1.65rem; }}
    .briefing-list {{ display: none; flex-direction: column; gap: 12px; padding: 18px 0 56px; }}
    .briefing-list.active {{ display: flex; }}
    .briefing-card {{
      border: 1px solid var(--border);
      border-radius: 8px;
      background: rgba(255,255,255,0.035);
      transition: border-color 0.15s, transform 0.15s, background 0.15s;
    }}
    .briefing-card:hover {{ border-color: rgba(245,158,11,0.55); transform: translateY(-1px); background: rgba(255,255,255,0.055); }}
    .briefing-card a {{ display: flex; justify-content: space-between; gap: 18px; padding: 18px; }}
    .briefing-title {{ color: #f8fafc; font-weight: 800; line-height: 1.35; font-size: 1.05rem; }}
    .briefing-meta {{ color: var(--muted); margin-top: 7px; font: 700 0.76rem "JetBrains Mono", ui-monospace, monospace; text-transform: uppercase; letter-spacing: 0.04em; }}
    .arrow {{ color: var(--gold); font-size: 1.4rem; line-height: 1; }}
    .empty-state {{ border: 1px solid var(--border); border-radius: 8px; background: rgba(255,255,255,0.035); padding: 22px; color: #bec5d0; }}
    footer {{ border-top: 1px solid var(--border); color: var(--muted); padding: 20px 0 34px; font-size: 0.85rem; }}
    @media (max-width: 780px) {{
      .shell {{ width: min(100% - 24px, 1080px); }}
      header, .hero, .summary {{ grid-template-columns: 1fr; }}
      nav {{ justify-self: stretch; }}
      .tabs {{ width: 100%; }}
      .tab {{ flex: 1; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <a class="brand" href="/"><img src="/assets/logo_icon_raw.png" alt="">ChinaVol</a>
      <nav aria-label="Primary">
        <a href="/">Today</a>
        <a href="/newsroom.html">Newsroom</a>
        <a href="/volatility.html">Volatility</a>
        <a class="active" href="/briefings.html">Briefings</a>
        <a href="/subscribe.html">Subscribe</a>
      </nav>
      <div class="stamp">Generated {html.escape(str(updated))}</div>
    </header>
    <main>
      <section class="hero">
        <div>
          <div class="label">Archive / Daily briefing</div>
          <h1>Daily Briefings</h1>
          <p class="subtitle">Daily China market briefings in English and Chinese, ordered latest first.</p>
        </div>
        <div class="tabs" role="tablist" aria-label="Briefing language">
          <button class="tab active" data-tab="en" type="button">English</button>
          <button class="tab" data-tab="zh" type="button">中文</button>
        </div>
      </section>
      <section class="summary" aria-label="Archive summary">
        <div class="metric"><div class="label">English</div><strong>{len(en_items)}</strong></div>
        <div class="metric"><div class="label">中文</div><strong>{len(zh_items)}</strong></div>
        <div class="metric"><div class="label">Total</div><strong>{len(items)}</strong></div>
      </section>
      <section class="briefing-list active" data-lang-section="en">
{en_cards}
      </section>
      <section class="briefing-list" data-lang-section="zh">
{zh_cards}
      </section>
    </main>
    <footer>© 2026 ChinaVol.</footer>
  </div>
  <script>
    const tabs = document.querySelectorAll("[data-tab]");
    const sections = document.querySelectorAll("[data-lang-section]");
    function switchLang(lang) {{
      tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === lang));
      sections.forEach((section) => section.classList.toggle("active", section.dataset.langSection === lang));
      try {{ localStorage.setItem("cv_lang", lang); }} catch (error) {{}}
    }}
    tabs.forEach((tab) => tab.addEventListener("click", () => switchLang(tab.dataset.tab)));
    try {{
      const saved = localStorage.getItem("cv_lang");
      if (saved === "en" || saved === "zh") switchLang(saved);
    }} catch (error) {{}}
  </script>
</body>
</html>
"""
    BRIEFINGS_HTML.write_text(html_text, encoding="utf-8")


def refresh_site_manifest() -> None:
    script = ROOT / "tools" / "build_site_manifest.py"
    if script.exists():
        subprocess.run([sys.executable, str(script)], cwd=str(ROOT), check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", action="store_true", help="Parse current briefings.html into content/briefings.json before rendering.")
    parser.add_argument("--add", action="store_true", help="Add or update one briefing before rendering.")
    parser.add_argument("--date", help="Briefing date, YYYY-MM-DD.")
    parser.add_argument("--lang", choices=["en", "zh"], default="en")
    parser.add_argument("--title", help="Briefing title.")
    parser.add_argument("--url", help="Briefing URL, such as /briefings/daily/example.html.")
    parser.add_argument("--section", default="daily")
    parser.add_argument("--source", default="manual")
    parser.add_argument("--published-at", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.bootstrap or not MANIFEST_PATH.exists():
        manifest = bootstrap_from_html()
    else:
        manifest = load_manifest()
    manifest.setdefault("version", 1)
    if args.add:
        missing = [name for name in ("date", "title", "url") if not getattr(args, name.replace("-", "_"), None)]
        if missing:
            raise SystemExit(f"--add requires: {', '.join(missing)}")
        upsert_briefing(manifest, {
            "date": args.date,
            "lang": args.lang,
            "title": args.title,
            "url": args.url,
            "section": args.section,
            "source": args.source,
            "published_at": args.published_at or f"{args.date}T00:00:00+08:00",
        })
    save_manifest(manifest)
    render_index(manifest)
    refresh_site_manifest()
    print(f"Rendered {BRIEFINGS_HTML.relative_to(ROOT)} from {MANIFEST_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
