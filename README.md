# YouTube Weekly Digest

每週六 12:00 自動抓取追蹤頻道最新影片 + 主題熱門 → 產生靜態網頁 → 貼給 Gemini 做摘要

---

## 使用方式

1. 開啟 GitHub Pages 網址
2. 全選（Ctrl+A）→ 複製
3. 貼給 Gemini：「請整理成繁體中文重點摘要」

---

## 追蹤頻道

| 分類 | 頻道 |
|---|---|
| 🤖 科技 AI 或機器人 | Two Minute Papers, Lex Fridman |
| 💰 投資 | Andrei Jikh, Minority Mindset |
| 📊 行銷與管理 | HubSpot Marketing, Dan Martell |
| 🛠 AI 應用與工具 | Silicon Valley Girl, The AI Advantage |
| 🌐 國際貿易與經濟 | Wendover Productions, Economics Explained, CaspianReport |

---

## 初始設定（只做一次）

### 1. 申請 YouTube Data API Key
1. 前往 https://console.cloud.google.com
2. 建立專案 `youtube-digest`
3. APIs & Services → Library → 啟用 `YouTube Data API v3`
4. Credentials → Create Credentials → API Key
5. API 限制：只選 `YouTube Data API v3`
6. 複製 Key（格式：`AIzaSy...`）

### 2. 存入 GitHub Secrets
GitHub repo → Settings → Secrets and variables → Actions → New repository secret
- Name: `YOUTUBE_API_KEY`
- Value: 貼上你的 Key

### 3. 開啟 GitHub Pages
Settings → Pages → Deploy from branch → main / (root)

### 4. 手動測試第一次
Actions → YouTube Weekly Digest → Run workflow → Run workflow

---

## 更新頻道清單

編輯 `fetch_youtube.py` 裡的 `CHANNELS` 字典即可。

---

## 配額說明

YouTube Data API v3 免費每日 10,000 單位
每次執行約用 2,200 單位（11 頻道 × 2 次查詢 + 5 主題搜尋）
每週只跑一次，完全不會超過。
