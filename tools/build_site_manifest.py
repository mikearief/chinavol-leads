#!/usr/bin/env python3
"""Build the lightweight JSON manifest consumed by redesign.html."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BriefingsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cards: list[dict[str, str]] = []
        self._card: dict[str, str] | None = None
        self._field: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        classes = set((attr.get("class") or "").split())
        if tag == "div" and "briefing-card" in classes:
            self._card = {"lang": attr.get("data-lang") or ""}
            return
        if self._card is None:
            return
        if tag == "a" and "href" in attr:
            href = attr["href"] or ""
            self._card["url"] = href if href.startswith("/") else "/" + href
        elif tag == "div" and "briefing-title" in classes:
            self._field = "title"
        elif tag == "div" and "briefing-meta" in classes:
            self._field = "meta"

    def handle_data(self, data: str) -> None:
        if self._card is not None and self._field:
            self._card[self._field] = (self._card.get(self._field, "") + data).strip()

    def handle_endtag(self, tag: str) -> None:
        if self._field and tag == "div":
            self._field = None
        elif self._card is not None and tag == "div" and self._card.get("title"):
            self.cards.append(self._card)
            self._card = None
            self._field = None


class NewsArchiveParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href") or ""
        if re.fullmatch(r"/news/\d{4}-\d{2}-\d{2}\.html", href):
            self.links.append(href)


class NewsPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.headlines: list[dict[str, str]] = []
        self.no_data = False
        self._in_card = False
        self._card: dict[str, str] = {}
        self._field: str | None = None
        self._link_pending = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        classes = set((attr.get("class") or "").split())
        if tag == "article" and "headline-card" in classes:
            self._in_card = True
            self._card = {}
        elif self._in_card and tag == "span" and "source-tag" in classes:
            self._field = "source"
        elif self._in_card and tag == "h2":
            self._field = "title"
        elif self._in_card and tag == "p" and "summary" in classes:
            self._field = "summary"
        elif self._in_card and tag == "a" and "source-link" in classes:
            self._card["url"] = attr.get("href") or ""
            self._link_pending = True
        elif tag == "p" and "no-data" in classes:
            self.no_data = True

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if self._in_card and self._field:
            self._card[self._field] = (self._card.get(self._field, "") + " " + text).strip()

    def handle_endtag(self, tag: str) -> None:
        if self._field and tag in {"span", "h2", "p"}:
            self._field = None
        if self._in_card and tag == "article":
            if self._card.get("title"):
                self.headlines.append(self._card)
            self._in_card = False
            self._card = {}
            self._field = None
            self._link_pending = False


def parse_date(text: str) -> str:
    patterns = ["%b %d, %Y", "%B %d, %Y"]
    date_text = text.split("·", 1)[0].strip()
    for pattern in patterns:
        try:
            return datetime.strptime(date_text, pattern).date().isoformat()
        except ValueError:
            continue
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if match:
        return match.group(0)
    return ""


def read_html(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def latest_briefing_from_content() -> dict[str, str] | None:
    manifest_path = ROOT / "content" / "briefings.json"
    if not manifest_path.exists():
        return None

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None

    cards = []
    for item in manifest.get("briefings", []):
        if not isinstance(item, dict) or item.get("lang") != "en":
            continue
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        date = str(item.get("date") or "").strip()
        if not title or not url or not date:
            continue
        cards.append({
            "date": date,
            "title": title,
            "url": url if url.startswith("/") else "/" + url,
            "meta": str(item.get("meta") or "Daily Briefing").strip(),
            "published_at": str(item.get("published_at") or ""),
            "source": str(item.get("source") or "content/briefings.json"),
        })

    cards.sort(key=lambda item: (item["date"], item["published_at"], item["url"]), reverse=True)
    if not cards:
        return None

    latest = cards[0].copy()
    latest.pop("published_at", None)
    return latest


def latest_briefing() -> dict[str, str]:
    briefing = latest_briefing_from_content()
    if briefing:
        return briefing

    parser = BriefingsParser()
    parser.feed(read_html(ROOT / "briefings.html"))
    cards = []
    for card in parser.cards:
        if card.get("lang") != "en":
            continue
        date = parse_date(card.get("meta", ""))
        if not date:
            continue
        cards.append({**card, "date": date})
    cards.sort(key=lambda item: item["date"], reverse=True)
    if not cards:
        return {
            "date": "",
            "title": "ChinaVol Daily Briefing",
            "url": "/briefings.html",
            "meta": "Daily Briefing"
        }
    return cards[0]


def latest_news() -> dict[str, object]:
    archive = NewsArchiveParser()
    archive.feed(read_html(ROOT / "news" / "index.html"))
    links = sorted(set(archive.links), reverse=True)
    latest_link = links[0] if links else "/news/"
    page_path = ROOT / latest_link.lstrip("/")
    parser = NewsPageParser()
    if page_path.exists():
        parser.feed(read_html(page_path))
    date_match = re.search(r"\d{4}-\d{2}-\d{2}", latest_link)
    return {
        "date": date_match.group(0) if date_match else "",
        "url": latest_link,
        "headline_count": len(parser.headlines),
        "headlines": parser.headlines[:3],
        "status": "active" if parser.headlines else "quiet",
        "message": "No major headlines for this period." if parser.no_data and not parser.headlines else ""
    }


def build_manifest() -> dict[str, object]:
    try:
        cst = timezone(timedelta(hours=8))
        now = datetime.now(cst)
    except Exception:
        now = datetime.now(timezone.utc)
    briefing = latest_briefing()
    news = latest_news()
    news_headline = "China news wire is quiet"
    news_url = news["url"]
    if news["headlines"]:
        news_headline = str(news["headlines"][0].get("title", news_headline))
        news_url = str(news["headlines"][0].get("url") or news_url)

    return {
        "updated_at": now.isoformat(timespec="seconds"),
        "display_updated": now.strftime("Updated %b %d, %Y %H:%M CST"),
        "data_quality": "mixed",
        "data_note": "Briefing archive is generated from content/briefings.json. News archive is generated from local HTML. Signal and volatility widgets are design placeholders until exporters are wired.",
        "hero": {
            "headline": "China risk is quiet. The tape is not.",
            "dek": "Daily China market intelligence from live signals, options skew, prediction markets, and Chinese financial news.",
            "primary_cta": "Read today's briefing",
            "primary_url": briefing.get("url", "/briefings.html"),
            "secondary_cta": "Open volatility lab",
            "secondary_url": "/volatility.html"
        },
        "briefing": briefing,
        "news": news,
        "regime": {
            "label": "Watch",
            "score": 62,
            "trend": "+8 pts",
            "source": "design-placeholder",
            "explanation": "Volatility is subdued, but catalysts are clustered around Fed policy, oil, tariffs, and China ADR breadth."
        },
        "options": {
            "title": "Option skew spike",
            "label": "Jun 26 +3.1 sigma",
            "z_score": 3.1,
            "source": "design-placeholder",
            "series": [0.4, 0.6, 0.2, 0.9, 1.1, 0.8, 1.4, 1.0, 1.7, 1.2, 2.0, 3.1]
        },
        "signals": {
            "fired_now": 0,
            "watches_online": 35,
            "last_fired": "2h 15m ago",
            "source": "design-placeholder"
        },
        "sections": {
            "today": {
                "title": "Command Center",
                "text": "Risk regime, fired signals, skew spike, news count."
            },
            "newsroom": {
                "title": "Market Narrative",
                "headline": news_headline,
                "url": news_url
            },
            "volatility": {
                "title": "Chart Lab",
                "text": "Options z-score, prediction shifts, signal heatmap."
            }
        }
    }


def main() -> None:
    manifest = build_manifest()
    (ROOT / "site-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()
