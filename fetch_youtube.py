#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_youtube.py
— 抓頻道最新影片 + 主題熱門影片 → 產生 index.html

資安審查：
  ✅ 只連 YouTube Data API v3（官方）
  ✅ API Key 從環境變數讀取，不寫進程式碼
  ✅ 只寫入本機 index.html
  ✅ 無刪除、無後門、無其他上傳
"""

import os, json, sys, html
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError

# ── API Key（從環境變數讀取）─────────────────────────────
API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
if not API_KEY:
    print("❌ 找不到 YOUTUBE_API_KEY 環境變數")
    sys.exit(1)

BASE = "https://www.googleapis.com/youtube/v3"

# ── 頻道設定 ─────────────────────────────────────────────
CHANNELS = {
    "🤖 科技 AI 或機器人": [
        "@TwoMinutePapers",
        "@lexfridman",
    ],
    "💰 投資": [
        "@AndreiJikh",
        "@MinorityMindset",
    ],
    "📊 行銷與管理": [
        "@HubSpotMarketing",
        "@danmartell",
    ],
    "🛠 AI 應用與工具": [
        "@SiliconValleyGirl",
        "@aiadvantage",
    ],
    "🌐 國際貿易與經濟": [
        "@Wendoverproductions",
        "@EconomicsExplained",
        "@CaspianReport",
    ],
}

# ── 主題熱門搜尋關鍵字 ───────────────────────────────────
TOPICS = [
    ("🤖 Tech AI & Robotics",        "Tech AI Robotics 2025"),
    ("💰 Investment & Finance",       "Investment Finance 2025"),
    ("📊 Marketing & Business",       "Marketing Business Strategy 2025"),
    ("🛠 AI Tools & Productivity",    "AI Tools Productivity 2025"),
    ("🌐 Global Economy & Trade",     "Global Economy Trade 2025"),
]

VIDEOS_PER_CHANNEL = 2
VIDEOS_PER_TOPIC   = 3


# ── HTTP 工具 ─────────────────────────────────────────────
def api_get(endpoint, params):
    params["key"] = API_KEY
    url = f"{BASE}/{endpoint}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=15) as r:
            return json.loads(r.read().decode())
    except HTTPError as e:
        body = e.read().decode()
        print(f"  HTTP {e.code} on {endpoint}: {body[:200]}")
        return {}
    except Exception as e:
        print(f"  Error on {endpoint}: {e}")
        return {}


# ── 把 @handle 轉成 channel_id ───────────────────────────
def handle_to_channel_id(handle):
    """用 search API 查頻道 ID"""
    handle_clean = handle.lstrip("@")
    data = api_get("search", {
        "part": "snippet",
        "q": handle_clean,
        "type": "channel",
        "maxResults": 1,
    })
    items = data.get("items", [])
    if not items:
        return None, handle_clean
    ch = items[0]
    cid = ch["snippet"].get("channelId") or ch["id"].get("channelId")
    title = ch["snippet"].get("title", handle_clean)
    return cid, title


# ── 取頻道最新影片 ────────────────────────────────────────
def get_channel_videos(channel_id, channel_title, n=2):
    data = api_get("search", {
        "part": "snippet",
        "channelId": channel_id,
        "order": "date",
        "type": "video",
        "maxResults": n,
    })
    results = []
    for item in data.get("items", []):
        vid = item["id"].get("videoId")
        if not vid:
            continue
        snip = item["snippet"]
        results.append({
            "title":   snip.get("title", ""),
            "url":     f"https://youtu.be/{vid}",
            "channel": channel_title,
            "date":    snip.get("publishedAt", "")[:10],
            "thumb":   snip.get("thumbnails", {}).get("medium", {}).get("url", ""),
        })
    return results


# ── 取主題熱門影片（本週內）──────────────────────────────
def get_topic_videos(query, n=3):
    # 一週前的 ISO 時間
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = api_get("search", {
        "part": "snippet",
        "q": query,
        "type": "video",
        "order": "viewCount",
        "publishedAfter": since,
        "maxResults": n,
        "regionCode": "US",
        "relevanceLanguage": "en",
    })
    results = []
    for item in data.get("items", []):
        vid = item["id"].get("videoId")
        if not vid:
            continue
        snip = item["snippet"]
        results.append({
            "title":   snip.get("title", ""),
            "url":     f"https://youtu.be/{vid}",
            "channel": snip.get("channelTitle", ""),
            "date":    snip.get("publishedAt", "")[:10],
            "thumb":   snip.get("thumbnails", {}).get("medium", {}).get("url", ""),
        })
    return results


# ── 產生 HTML ─────────────────────────────────────────────
def make_html(channel_data, topic_data, generated_at):
    date_str = generated_at.strftime("%Y-%m-%d")
    week_str = generated_at.strftime("第 %W 週")

    def card(v):
        t  = html.escape(v["title"])
        ch = html.escape(v["channel"])
        d  = html.escape(v["date"])
        u  = html.escape(v["url"])
        return f"""
        <a class="card" href="{u}" target="_blank" rel="noopener">
          <div class="card-body">
            <div class="card-title">{t}</div>
            <div class="card-meta">{ch} · {d}</div>
          </div>
          <div class="card-arrow">↗</div>
        </a>"""

    sections_html = ""

    # 頻道區塊
    sections_html += '<div class="section-header">📺 追蹤頻道最新影片</div>'
    for cat, videos in channel_data.items():
        cat_e = html.escape(cat)
        cards = "".join(card(v) for v in videos) if videos else '<div class="empty">本週無新影片</div>'
        sections_html += f'<div class="category"><div class="category-title">{cat_e}</div><div class="cards">{cards}</div></div>'

    # 主題熱門區塊
    sections_html += '<div class="section-header" style="margin-top:32px">🔥 本週主題熱門</div>'
    for topic_name, videos in topic_data:
        tn_e = html.escape(topic_name)
        cards = "".join(card(v) for v in videos) if videos else '<div class="empty">無結果</div>'
        sections_html += f'<div class="category"><div class="category-title">{tn_e}</div><div class="cards">{cards}</div></div>'

    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>YouTube Weekly Digest · {date_str}</title>
<style>
  :root{{--bg:#0a0e1a;--card:#111827;--border:rgba(255,255,255,.07);--text:#e2e8f0;--muted:#64748b;--accent:#ef4444;--accent2:#f97316}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,"Noto Sans TC",sans-serif;min-height:100vh}}
  .hero{{background:linear-gradient(135deg,#0f172a,#1e1040);padding:32px 20px 28px;border-bottom:1px solid var(--border)}}
  .hero-inner{{max-width:860px;margin:0 auto}}
  .hero-badge{{display:inline-block;background:var(--accent);color:#fff;font-size:11px;font-weight:700;padding:3px 10px;border-radius:999px;letter-spacing:.06em;margin-bottom:12px}}
  .hero-title{{font-size:clamp(22px,5vw,32px);font-weight:800;line-height:1.2}}
  .hero-sub{{color:var(--muted);font-size:13px;margin-top:6px}}
  .wrap{{max-width:860px;margin:0 auto;padding:24px 16px 48px}}
  .section-header{{font-size:13px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:0 0 16px;padding-bottom:8px;border-bottom:1px solid var(--border)}}
  .category{{margin-bottom:28px}}
  .category-title{{font-size:15px;font-weight:700;margin-bottom:10px;color:var(--text)}}
  .cards{{display:grid;gap:8px}}
  .card{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 14px;background:var(--card);border:1px solid var(--border);border-radius:10px;text-decoration:none;color:var(--text);transition:border-color .15s,background .15s}}
  .card:hover{{border-color:rgba(255,255,255,.18);background:#1a2235}}
  .card-body{{flex:1;min-width:0}}
  .card-title{{font-size:14px;font-weight:600;line-height:1.4;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
  .card-meta{{font-size:12px;color:var(--muted);margin-top:3px}}
  .card-arrow{{color:var(--muted);font-size:16px;flex-shrink:0}}
  .empty{{font-size:13px;color:var(--muted);padding:10px 0}}
  .footer{{text-align:center;color:var(--muted);font-size:12px;padding:24px 0;border-top:1px solid var(--border)}}
  .gemini-hint{{background:#111827;border:1px solid var(--border);border-radius:12px;padding:16px;margin:24px 0;font-size:13px;color:var(--muted);line-height:1.7}}
  .gemini-hint b{{color:var(--text)}}
</style>
</head>
<body>
<div class="hero">
  <div class="hero-inner">
    <div class="hero-badge">WEEKLY DIGEST</div>
    <div class="hero-title">📺 YouTube Weekly</div>
    <div class="hero-sub">{date_str} · {week_str} · 自動產生</div>
  </div>
</div>
<div class="wrap">
  <div class="gemini-hint">
    💡 <b>用法：</b>選取全頁文字（Ctrl+A）→ 複製 → 貼給 Gemini，說「請整理成繁體中文重點摘要」
  </div>
  {sections_html}
  <div class="footer">資料來源：YouTube Data API v3 · 每週六 12:00 自動更新 · {date_str}</div>
</div>
</body>
</html>"""


# ── 主程式 ────────────────────────────────────────────────
def main():
    now = datetime.now(timezone(timedelta(hours=8)))  # 台灣時間
    print(f"開始抓取 {now.strftime('%Y-%m-%d %H:%M')} CST")

    # 頻道影片
    channel_data = {}
    for cat, handles in CHANNELS.items():
        print(f"\n── {cat} ──")
        videos = []
        for handle in handles:
            print(f"  查頻道：{handle}")
            cid, title = handle_to_channel_id(handle)
            if not cid:
                print(f"  ⚠️  找不到 {handle}，略過")
                continue
            vids = get_channel_videos(cid, title, VIDEOS_PER_CHANNEL)
            print(f"  ✔ {title}：{len(vids)} 部")
            videos.extend(vids)
        channel_data[cat] = videos

    # 主題熱門
    topic_data = []
    print(f"\n── 主題熱門 ──")
    for label, query in TOPICS:
        print(f"  搜尋：{query}")
        vids = get_topic_videos(query, VIDEOS_PER_TOPIC)
        print(f"  ✔ {label}：{len(vids)} 部")
        topic_data.append((label, vids))

    # 產生 HTML
    output = make_html(channel_data, topic_data, now)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\n✅ index.html 產生完成")


if __name__ == "__main__":
    main()
