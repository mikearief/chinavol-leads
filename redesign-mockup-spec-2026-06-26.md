# ChinaVol Jobs + Automation Inventory and Landing Page Mockup Spec

**Created:** 2026-06-26 07:47 CST / 2026-06-25 23:47 UTC  
**Purpose:** Give Codex enough context to generate mockup designs for a better-organized `chinavol.com` landing page and content architecture.

---

## 1. Current State Summary

### What I verified

- `chinavol.com` is live and serving the static site from the ChinaVol vault tree.
- The current homepage is clean but too static: hero + CTA + live bar + three stale briefing cards.
- There are **no charts, sparklines, extreme-move widgets, current-date market panels, or data proofs above the fold**.
- There is an active automation ecosystem with 19 Hermes cron jobs, including several ChinaVol-specific pipelines.
- The daily briefing content **is being generated and published as article HTML**, but the index/listing is malformed:
  - Live `/briefings.html` English tab shows only old May 28 cards.
  - June English daily briefing cards are inserted inside the Chinese section.
  - Chinese briefing cron outputs exist, but the Chinese publisher does not appear to be creating fresh native ZH cards for June 25.
- Latest verified published daily briefing article: `https://chinavol.com/briefings/daily/fed-hawkish-pivot-oil-crash-and-trumps-new-tariff-wall-compr.html` for June 25, 2026.
- Latest verified news archive page: `https://chinavol.com/news/2026-06-25.html` exists, but it says “No major headlines for this period.”

### Visual assessment of current landing page

Current page has a dark fintech/newsletter feel, but it does not prove the product promise of “real-time data” or “volatility intelligence.” It reads more like a premium newsletter landing page than a live market-intelligence command center.

Key gaps:

1. No quantitative proof above the fold.
2. No current-date/timestamp freshness marker.
3. No volatility/risk-regime hero metric despite the name ChinaVol.
4. The “latest” homepage cards are stale placeholders from May 13/14.
5. No chart/sparkline widgets showing an extreme today move.
6. The main nav includes `𝕏`, which is visually ambiguous.
7. Landing page does not surface the strongest automations: signal detection, option anomalies, Polymarket spikes, RSSHub China news, daily briefing, or news curator.

---

## 2. Live Cron / Automation Inventory

Hermes currently reports **19 cron jobs**.

| Job ID | Name | Schedule | Status | Site Relevance | Recommendation |
|---|---|---:|---|---|---|
| `906d125c8356` | ChinaVol Alerts | `0 0,9,13 * * *` | OK | High | Feed homepage “Pre-market Alerts” card + `/alerts.html`; generate headline teaser + tickers. |
| `677285db5f52` | ChinaVol Daily Briefing (EN) | `0 8 * * 1-5` | OK | High | Primary homepage hero source and “Daily Briefing” top story. Fix index insertion. |
| `816b1470fe73` | ChinaVol Daily Briefing | `20 8 * * 1-5` | OK | High | Chinese version; currently generated but apparently not reliably published/indexed. Fix publisher. |
| `009869c3d0ee` | ChinaVol Daily News Curator | `55 23,8,12 * * *` | OK, occasional 120s timeout | High | Surface as `/news/` and “China News” module. Needs timeout mitigation if translations run. |
| `46935b906e0b` | RSSHub China News Monitor | `55 23,8,12 * * *` | OK | High | Feed “China News Wire” / top headline count. Producer for news curator. |
| `8061c84c2900` | ChinaVol Tweet Reviewer & Publisher | every 5 min | OK / often silent | Medium | Not site content directly, but can expose a “Latest X post” widget if desired. |
| `09e27278e53d` | ChinaVol Reply Scout and Drafter | daily 08:00 | ERROR | Medium | Social engagement backend; not site-facing until fixed. Recent error was `KeyError: 'url'`, though local script now contains fallback code. Verify next run. |
| `d0ee8ef5430e` | ChinaVol Reply Publisher | every 5 min | OK / no approved replies | Low-Medium | Social publishing only; do not clutter homepage. |
| `b7edaba90ecd` | Signal Detection + Alert Check | every 15 min | OK / silent | High | Strong homepage material: “Market Signal Radar” with fired/no-fired status, asset, trigger, severity. |
| `c68adb3d061a` | Option Anomaly Alerts (Discord) | every 5 min | OK / silent | High | Strong chart module: option IV/skew/gamma anomaly dashboard with extreme spikes. |
| `8f857a5e1ba2` | Polymarket 15-min Spike Watcher | every 15 min | OK / silent | High | “Prediction Market Shock Tape”; great clickbait if phrased carefully. |
| `a0acb7ac1848` | Weekly Market Discovery | weekly Sun 04:00 | OK | Medium | Use for a weekly “Market map” or “New watches” page. |
| `e197953f99f3` | Pre-China Open Correlation Check | weekdays 23:00 | OK | High | Useful for “lead/lag radar” / predictive-leads section. |
| `f6f5144703b1` | Weekly Option Alert Calibration | weekly Sun | ERROR timeout | Medium | Do not surface until fixed; useful back-office calibration. |
| `d235c497a943` | Consumables Dashboard Check | daily 09:00 | OK | Internal only | Do not put on ChinaVol; operational cost monitoring. |
| `b840662758de` | Weekly Digest | weekly Sun | OK | Internal/possible archive | Could become internal digest or member-only archive, not homepage. |
| `a0ac...` etc. | Trading-journal jobs | varies | OK | Medium | Data source for signals; not direct content unless distilled. |
| `fe9356f2f6dc` | QMD Re-embed | every 6h | OK | Internal only | Do not put on site. |
| `eeca8444764e` | Daily Hermes Backup | daily 00:00 | OK | Internal only | Do not put on site. |
| `456c86cee303` | Weekly Memory Synthesis | paused | Internal only | Do not put on site. |

---

## 3. What Should Go Onto ChinaVol.com

### High-priority public modules

1. **Daily Briefing / Hero Story**
   - Source: `677285db5f52` EN daily briefing article, plus `816b1470fe73` ZH article.
   - Use: homepage hero headline, “Read today’s briefing” CTA, latest briefing card.
   - Fix first: `/briefings.html` language sections are malformed.

2. **China News Wire**
   - Source: RSSHub monitor (`46935b906e0b`) + curator (`009869c3d0ee`).
   - Use: top 3 China market headlines, with source labels and “last updated” timestamp.
   - If no headlines, do not show “No major headlines” above the fold; use a neutral small status badge.

3. **Market Signal Radar**
   - Source: `signal_detection_alert.sh` / trading-journal DB tables: `signals`, `signal_watches`, `market_metrics`.
   - Use: live status strip: “0 fired now / last fired X ago / 35 watches online.”
   - When a signal fires, it becomes homepage hero-worthy.

4. **Options / Volatility Anomaly Board**
   - Source: `option_chain_snapshots`, `option_skew`, option alert job.
   - Use: charts showing today/current date and extreme z-score spikes.
   - Best visual fit for the ChinaVol brand.

5. **Prediction Market Shock Tape**
   - Source: `polymarket_15min_watcher.py`, DB tables `polymarket_snapshots_v2`, `market_probabilities`, `pm_alert_dedup`.
   - Use: “Markets repriced X pp in 15 min” cards.
   - Keep it clicky but defensible: show probability move, timestamp, and source.

6. **Pre-China Open Correlation / Lead-Lag**
   - Source: `e197953f99f3`, leads app, trading journal DB.
   - Use: dashboard/paid feature teaser: “What moved before China opens?”

### Medium-priority modules

- Latest X post from `@chinavol1` if available through xurl/GetXAPI.
- Weekly market discovery as a weekend “Watchlist” page.
- Deep Dives index as evergreen research, not hero unless no fresh daily content.

### Do NOT put on public site

- Hermes backups, QMD re-embedding, memory synthesis, consumables dashboard.
- Raw cron logs.
- Internal publisher/reviewer operational status, except in an admin-only dashboard.

---

## 4. Current Broken / Messy Areas to Fix Before or During Redesign

### A. Briefings index organization bug

Current `/briefings.html` structure:

- English section contains only two old May 28 cards.
- Chinese section contains a mix of native Chinese card(s) and many English June cards.
- Latest EN article exists, but the default English tab does not show it.

Likely fix direction:

- Replace regex insertion into HTML with a deterministic index rebuild script.
- Store briefing metadata in a JSON manifest, then render `briefings.html` from the manifest.
- Never mutate nested HTML with regex. This is why language sections drift.

Suggested manifest:

```json
{
  "briefings": [
    {
      "date": "2026-06-25",
      "lang": "en",
      "title": "China Market Pre-Open Briefing — June 25, 2026",
      "headline": "Fed hawkish pivot, oil crash, and Trump's new tariff wall...",
      "url": "/briefings/daily/fed-hawkish-pivot-oil-crash-and-trumps-new-tariff-wall-compr.html",
      "section": "daily",
      "source_job": "677285db5f52",
      "published_at": "2026-06-25T08:06:22+08:00"
    }
  ]
}
```

### B. News curator timeout

`009869c3d0ee` often succeeds, but recent midday runs timed out after 120s. It is a `no_agent` script, so it hits the hard cron script timeout. If translations or LLM calls exceed 120s, use a nohup/background pattern or reduce work per tick.

### C. Reply scout/drafter error

Recent output shows `KeyError: 'url'` in `chinavol_reply_drafter.py`. The local script now has fallback logic using `post.get("url") or post.get("post_url")`; verify the next run before considering fixed.

### D. Homepage stale content

Homepage cards are hardcoded to May 13/14 and some links are `#`. Replace with generated data from latest manifest.

---

## 5. Proposed Site Information Architecture

### Top navigation

Recommended:

```text
Home | Today | Signals | News | Briefings | Deep Dives | Methodology | Subscribe
```

Move X/Twitter into footer or label it `Follow @chinavol1`, not bare `𝕏` in the primary nav.

### Pages

| Page | Purpose | Data source |
|---|---|---|
| `/` | Live landing / command center | Aggregated JSON manifest + latest briefings + signals |
| `/today.html` | Today’s market command page | Daily briefing + all today signals/charts |
| `/signals.html` | Market Signal Radar | trading journal DB export |
| `/volatility.html` | Options / vol anomaly board | option_chain_snapshots, option_skew |
| `/prediction-markets.html` | Polymarket shock tape | polymarket snapshots |
| `/news/` | China news archive | news curator |
| `/briefings.html` | Daily briefing archive with EN/ZH tabs | briefing manifest |
| `/deep-dives.html` | Evergreen analysis | static archive |
| `/methodology.html` | Trust / process | static |
| `/subscribe.html` | Email capture | existing page |

---

## 6. Landing Page Mockup Requirements

Codex should generate **static mockups only** first. Do not wire real deployment or cron edits yet.

### Output target

Create:

```text
/home/mikea/.hermes/vault/Projects/chinavol/mockups/
  landing-v1-command-center.html
  landing-v2-newsroom.html
  landing-v3-volatility-lab.html
  mock-data.json
  README.md
```

### Common constraints

- Do not modify the live root `index.html` during mockup generation.
- Use static JSON fixtures and clearly mark data as mock/sample unless read from existing local HTML/JSON.
- Dark, premium market-intelligence aesthetic.
- Mobile responsive.
- No build step required unless Codex chooses to also create a tiny Vite/Next sandbox; plain HTML/CSS/JS is acceptable and preferred for first mockups.
- Include a visible `Updated Jun 26, 2026 HH:MM CST` freshness stamp.
- Include at least one chart-like visualization in the first viewport.
- Include current-date labels on charts, e.g. `Jun 26` marker at far right.
- Show “extreme spike” affordances: red/orange vertical spike, z-score badge, probability move badge, or volatility regime banner.
- Avoid fabricating real prices in production copy. Mock values must be labeled `Sample data` in the mockup footer or README.

### Design language

Preferred blend:

- **Linear-style dark precision:** near-black canvas, subtle borders, Inter/JetBrains Mono, low-noise panels.
- **Kraken-style finance confidence:** purple/blue accent palette, clear green/red market states.
- **Cohere-style content authority:** large editorial headlines and high-quality rounded cards.

Suggested palette:

```css
--bg: #08090a;
--panel: #0f1011;
--surface: rgba(255,255,255,0.035);
--border: rgba(255,255,255,0.08);
--text: #f7f8f8;
--muted: #8a8f98;
--accent: #7170ff;
--china-gold: #f59e0b;
--danger: #ef4444;
--success: #10b981;
--cyan: #38bdf8;
```

---

## 7. Mockup Concepts

### Mockup A — “Command Center”

Goal: make ChinaVol feel live and data-backed within 3 seconds.

Above the fold:

1. Sticky nav.
2. Hero left:
   - `China risk is quiet. The tape is not.`
   - Subhead: “Daily China market intelligence from live signals, options skew, prediction markets, and Chinese financial news.”
   - CTA: `Read today’s briefing` + `View live signals`.
3. Hero right: **Risk Console** with four widgets:
   - ChinaVol Regime: `Watch / Stress / Shock` badge.
   - Option Skew Spike: mini line chart with right-edge red spike and `+3.1σ` badge.
   - Polymarket Shock: `+12pp in 15m` style badge.
   - News Wire: count of China headlines found in last window.
4. Below fold: top headlines from Briefing / News / Alerts.

### Mockup B — “Newsroom / Clickbait”

Goal: content-first, more editorial and shareable.

Above the fold:

1. Full-width editorial headline from latest daily briefing.
2. A “Why it matters” deck of 3 sharp bullets.
3. Side rail: “Moving now” cards:
   - Oil shock
   - CNH / USD pressure
   - China ADR / KWEB move
   - Polymarket repricing
4. Clickbait headline style, but defensible:
   - “The market is pricing calm. The China tape says otherwise.”
   - “Oil just flipped from inflation threat to China margin tailwind.”
   - “Volatility is not high yet. The setup is.”

### Mockup C — “Volatility Lab”

Goal: lean into ChinaVol identity and make charts the product.

Above the fold:

1. Massive “ChinaVol Dashboard” title.
2. 3-chart grid:
   - Options skew z-score line with current-date spike.
   - Prediction-market probability shift bars.
   - Signal watch heatmap by asset/theme.
3. Small editorial panel: latest briefing headline.
4. CTA: `Open today’s dashboard`.

---

## 8. Data Contract for Future Real Integration

Mockups can consume `mock-data.json` with this shape:

```json
{
  "updated_at": "2026-06-26T07:47:48+08:00",
  "regime": {
    "label": "Watch",
    "score": 62,
    "explanation": "Volatility subdued but macro catalysts are clustered."
  },
  "hero": {
    "headline": "Fed hawkish pivot, oil crash, and Trump's new tariff wall compress China ADR valuations",
    "url": "/briefings/daily/fed-hawkish-pivot-oil-crash-and-trumps-new-tariff-wall-compr.html",
    "date": "2026-06-25"
  },
  "charts": [
    {
      "id": "option-skew",
      "title": "Options skew spike",
      "unit": "z-score",
      "series": [{"date":"2026-06-20","value":0.4}, {"date":"2026-06-26","value":3.1}],
      "highlight": "Jun 26 +3.1σ"
    }
  ],
  "headlines": [
    {"section":"Daily Briefing", "title":"...", "url":"...", "tag":"Macro"},
    {"section":"China News", "title":"...", "url":"...", "tag":"Policy"},
    {"section":"Signals", "title":"No fired signals in the last window", "url":"/signals.html", "tag":"Quiet"}
  ],
  "automations": {
    "briefing_en": {"job_id":"677285db5f52", "status":"ok", "latest":"2026-06-25"},
    "briefing_zh": {"job_id":"816b1470fe73", "status":"generated_not_indexed", "latest":"2026-06-25"},
    "news": {"job_id":"009869c3d0ee", "status":"ok", "latest":"2026-06-25"},
    "signals": {"job_id":"b7edaba90ecd", "status":"silent_ok"},
    "options": {"job_id":"c68adb3d061a", "status":"silent_ok"},
    "polymarket": {"job_id":"8f857a5e1ba2", "status":"silent_ok"}
  }
}
```

---

## 9. Codex Task Prompt

Use this prompt with Codex:

```text
You are working in /home/mikea/.hermes/vault/Projects/chinavol.

Goal: create static mockup designs for a redesigned ChinaVol landing page. Do NOT modify the live index.html or deploy anything. Create all output under ./mockups/.

Read ./redesign-mockup-spec-2026-06-26.md first. Then produce:

1. mockups/mock-data.json — sample fixture matching the data contract in the spec.
2. mockups/landing-v1-command-center.html — dark live command-center layout with hero + risk console + sparkline chart widgets.
3. mockups/landing-v2-newsroom.html — editorial/newsroom layout with top clicky headline and “moving now” side rail.
4. mockups/landing-v3-volatility-lab.html — chart-forward layout centered on volatility/options/prediction-market panels.
5. mockups/README.md — explain the three concepts, what data they expect, and which one you recommend.

Design constraints:
- Use plain HTML/CSS/JS, no build step.
- Use Inter from Google Fonts and JetBrains Mono for technical labels.
- Dark premium aesthetic: Linear-style precision, Kraken-style finance confidence, Cohere-style editorial hierarchy.
- Include at least one visible chart/sparkline above the fold in each mockup.
- Use current-date labels and a visible “Updated ... CST” timestamp.
- Make headlines punchier/clickier than the current site, but not dishonest.
- Mark fixture values as sample data. Do not claim fake values are live.
- Mobile responsive.

Acceptance criteria:
- Opening each HTML file locally in a browser works with no external build.
- The first viewport immediately shows: headline, CTA, current-date/timestamp, and data visualization.
- No live site files outside ./mockups/ are changed.
```

---

## 10. Follow-up Implementation Plan After Mockups

After choosing a mockup direction:

1. Fix `/briefings.html` by replacing regex mutation with manifest rebuild.
2. Add a `build_site_manifest.py` script that exports latest briefings/news/signals into JSON.
3. Replace hardcoded homepage cards with manifest-driven cards.
4. Add a static chart component reading JSON fixtures exported from trading-journal DB.
5. Deploy only after visual verification in browser.

---

## 11. Evidence / Source Paths Checked

- Live homepage: `https://chinavol.com/`
- Live briefings: `https://chinavol.com/briefings.html`
- Live alerts: `https://chinavol.com/alerts.html`
- Live deep dives: `https://chinavol.com/deep-dives.html`
- Live news: `https://chinavol.com/news/`
- Local site root: `/home/mikea/.hermes/vault/Projects/chinavol/`
- Current homepage source: `/home/mikea/.hermes/vault/Projects/chinavol/index.html`
- Briefings index source: `/home/mikea/.hermes/vault/Projects/chinavol/briefings.html`
- EN publisher: `/home/mikea/.hermes/scripts/daily_briefing_publisher_en.py`
- ZH publisher: `/home/mikea/.hermes/scripts/chinese_briefing_publisher.py`
- News curator: `/home/mikea/.hermes/scripts/chinavol_news_curator.py`
- Cron outputs: `/home/mikea/.hermes/cron/output/`
- Trading DB: `/home/mikea/.hermes/vault/data/trading_journal.db`
