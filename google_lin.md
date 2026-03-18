# Google 搜尋結果爬蟲程式

## 目標
使用 Python 爬取 Google 搜尋結果，抓取搜尋標題、連結與摘要。

---

## 注意事項
- Google 的服務條款禁止自動化抓取，頻繁請求可能導致 IP 被封鎖或出現 CAPTCHA。
- 建議使用 `User-Agent` 偽裝瀏覽器、加入延遲，避免觸發反爬蟲機制。
- 若需穩定使用，建議改用 [Google Custom Search API](https://developers.google.com/custom-search/v1/overview)。

---

## 環境需求

- Python 3.8+
- 套件：`requests`、`beautifulsoup4`、`lxml`

---

## 步驟一：安裝套件

```bash
pip install requests beautifulsoup4 lxml
```

---

## 步驟二：了解 Google 搜尋網址格式

Google 搜尋的基本 URL：

```
https://www.google.com/search?q=關鍵字&num=10&hl=zh-TW
```

| 參數  | 說明                         |
|-------|------------------------------|
| `q`   | 搜尋關鍵字                   |
| `num` | 每頁顯示筆數（最多 100）     |
| `hl`  | 介面語言（`zh-TW` = 繁體中文）|
| `start` | 起始索引（用於翻頁，0、10、20…）|

---

## 步驟三：設定請求標頭 (Headers)

Google 會檢查請求來源，需要偽裝成瀏覽器：

```python
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}
```

---

## 步驟四：解析 HTML 結構

Google 搜尋結果的 HTML 結構（以 BeautifulSoup 選取）：

| 元素     | CSS 選擇器 / 說明                              |
|----------|------------------------------------------------|
| 每筆結果 | `div.g`                                        |
| 標題     | `h3`                                           |
| 連結     | `a[href]`（取 `href` 屬性）                    |
| 摘要     | `div[data-sncf]` 或 `div.VwiC3b`              |

> **注意**：Google 的 HTML 結構常更新，若解析失敗請檢查最新 class 名稱。

---

## 步驟五：完整程式碼

建立檔案 `google_scraper.py`：

```python
import requests
from bs4 import BeautifulSoup
import time
import random


def google_search(query: str, num_results: int = 10, lang: str = "zh-TW") -> list[dict]:
    """
    爬取 Google 搜尋結果

    Args:
        query:       搜尋關鍵字
        num_results: 要取得的結果筆數
        lang:        搜尋語言

    Returns:
        包含 title, link, snippet 的字典清單
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": f"{lang},zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    results = []
    start = 0

    while len(results) < num_results:
        # 每次最多取 10 筆
        fetch_num = min(10, num_results - len(results))
        url = (
            f"https://www.google.com/search"
            f"?q={requests.utils.quote(query)}"
            f"&num={fetch_num}"
            f"&hl={lang}"
            f"&start={start}"
        )

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # 解析每筆搜尋結果
        items = soup.select("div.g")
        if not items:
            print("未找到結果，Google 可能已更新 HTML 結構或觸發反爬蟲。")
            break

        for item in items:
            title_tag = item.select_one("h3")
            link_tag = item.select_one("a[href]")
            snippet_tag = item.select_one("div.VwiC3b") or item.select_one("[data-sncf]")

            title = title_tag.get_text(strip=True) if title_tag else ""
            link = link_tag["href"] if link_tag else ""
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

            # 過濾非正常連結
            if link.startswith("http") and title:
                results.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet,
                })

            if len(results) >= num_results:
                break

        start += 10

        # 加入隨機延遲，避免被封鎖（1~3 秒）
        time.sleep(random.uniform(1, 3))

    return results


def main():
    keyword = input("請輸入搜尋關鍵字：").strip()
    count = int(input("要取得幾筆結果（建議 10~20）：").strip())

    print(f"\n正在搜尋：{keyword}...\n")
    results = google_search(keyword, num_results=count)

    for i, r in enumerate(results, start=1):
        print(f"[{i}] {r['title']}")
        print(f"    URL     : {r['link']}")
        print(f"    摘要    : {r['snippet'][:100]}...")
        print()

    # 儲存為 CSV
    import csv
    filename = f"results_{keyword[:20].replace(' ', '_')}.csv"
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "link", "snippet"])
        writer.writeheader()
        writer.writerows(results)
    print(f"結果已儲存至 {filename}")


if __name__ == "__main__":
    main()
```

---

## 步驟六：執行程式

```bash
python google_scraper.py
```

執行後會：
1. 提示輸入搜尋關鍵字
2. 提示輸入要取得的筆數
3. 印出每筆結果的標題、連結、摘要
4. 自動儲存為 CSV 檔案

---

## 步驟七：輸出範例

```
請輸入搜尋關鍵字：Python 爬蟲教學
要取得幾筆結果（建議 10~20）：5

正在搜尋：Python 爬蟲教學...

[1] Python 爬蟲入門教學 - 使用 requests + BeautifulSoup
    URL     : https://example.com/python-scraping
    摘要    : 本教學介紹如何使用 Python 的 requests 與 BeautifulSoup 套件...

[2] ...

結果已儲存至 results_Python_爬蟲教學.csv
```

---

## 常見問題排解

| 問題 | 原因 | 解法 |
|------|------|------|
| 回傳 429 / 503 | 請求過於頻繁 | 增加 `time.sleep` 延遲 |
| 出現 CAPTCHA 頁面 | Google 偵測到爬蟲 | 更換 IP 或使用代理 |
| 找不到 `div.g` | Google 更新 HTML | 用 DevTools 重新確認 class |
| 編碼亂碼 | CSV 編碼問題 | 已使用 `utf-8-sig` 相容 Excel |

---

## 進階建議

- **使用 Google Custom Search API**：官方合法方式，每天免費 100 次查詢。
- **使用代理 IP（Proxy）**：避免單一 IP 被封鎖。
- **使用 Selenium**：若 Google 回傳 JavaScript 渲染頁面時使用。

---

*文件建立日期：2026-03-18*

---

# 月眉觀光糖廠旅遊注意事項爬蟲

## 目標網站

- 台糖官網月眉糖廠頁面：https://www.taisugar.com.tw/chinese/Attractions_detail.aspx?n=10048&s=191&p=0
- 台糖最新消息頁面：https://www.taisugar.com.tw/chinese/News_Index.aspx?p=71&n=10052

---

## 安裝套件

```bash
pip install requests beautifulsoup4
```

---

## 程式碼：`yuemei_scraper.py`

```python
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

MAIN_URL = "https://www.taisugar.com.tw/chinese/Attractions_detail.aspx?n=10048&s=191&p=0"
NEWS_URL = "https://www.taisugar.com.tw/chinese/News_Index.aspx?p=71&n=10052"


def fetch_page(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = "utf-8"
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def get_basic_info():
    """擷取月眉糖廠基本資訊與注意事項"""
    soup = fetch_page(MAIN_URL)
    results = {}

    time_keywords = ["營業時間", "開放時間", "休館", "暫停", "公休"]
    for tag in soup.find_all(["p", "li", "td", "div", "span"]):
        text = tag.get_text(strip=True)
        if any(kw in text for kw in time_keywords) and len(text) < 200:
            results.setdefault("營業時間與注意事項", []).append(text)

    notice_keywords = ["注意", "公告", "提醒", "禁止", "暫停", "關閉", "停止", "停辦"]
    for tag in soup.find_all(["p", "li", "td", "div"]):
        text = tag.get_text(strip=True)
        if any(kw in text for kw in notice_keywords) and 10 < len(text) < 300:
            results.setdefault("公告與注意事項", []).append(text)

    return results


def get_latest_news():
    """擷取台糖最新消息中與月眉相關的公告"""
    soup = fetch_page(NEWS_URL)
    news_items = []

    for a_tag in soup.find_all("a", href=True):
        title = a_tag.get_text(strip=True)
        href = a_tag["href"]
        if "月眉" in title or "yuemei" in href.lower():
            full_url = (
                "https://www.taisugar.com.tw" + href
                if href.startswith("/")
                else href
            )
            news_items.append({"標題": title, "連結": full_url})

    return news_items


def main():
    print("=" * 50)
    print("月眉觀光糖廠 旅遊注意事項爬蟲")
    print("=" * 50)

    print("\n【基本資訊與注意事項】")
    info = get_basic_info()
    if info:
        for section, items in info.items():
            print(f"\n▶ {section}")
            seen = set()
            for item in items:
                if item not in seen:
                    print(f"  · {item}")
                    seen.add(item)
    else:
        print("  目前官網無特別公告，請直接致電確認：04-2555-1100")

    print("\n【最新相關公告】")
    news = get_latest_news()
    if news:
        for n in news:
            print(f"  · {n['標題']}")
            print(f"    {n['連結']}")
    else:
        print("  目前無月眉糖廠專屬最新公告")

    print("\n【固定旅遊資訊】")
    print("  地址  ：臺中市后里區甲后路二段350號")
    print("  電話  ：04-2555-1100")
    print("  園區  ：08:30 – 17:00（平日及假日）")
    print("  冰店  ：09:00 – 17:00（每日）")
    print("  入園費：免費")
    print("  公車  ：92、155、212、213、215、813、888路")
    print("          → 月眉糖廠站下車")


if __name__ == "__main__":
    main()
```

---

## 執行方式

```bash
python yuemei_scraper.py
```

---

## 目前已知旅遊資訊（2026-03-18 擷取）

| 項目 | 說明 |
|------|------|
| 地址 | 臺中市后里區甲后路二段350號 |
| 電話 | 04-2555-1100 |
| 園區開放時間 | 08:30 – 17:00（平日及假日） |
| 冰店營業時間 | 09:00 – 17:00（每日） |
| 入園費 | 免費 |
| 大眾運輸 | 公車 92、155、212、213、215、813、813副、813繞、888 路，月眉糖廠站下車 |
| 自行開車（北） | 國道一號 160km 交流道出口，循甲后路前往 |
| 自行開車（西） | 國道三號大甲交流道，往東約 5 分鐘 |
| 台糖官網 | https://www.taisugar.com.tw/chinese/Attractions_detail.aspx?n=10048&s=191&p=0 |
| 台糖 Facebook | https://www.facebook.com/taiwanTSC/ |

> **備註**：截至 2026-03-18，官網無特別停業或緊急公告。出發前建議致電 **04-2555-1100** 再次確認。

---

*月眉糖廠爬蟲章節建立日期：2026-03-18*

---

## 月眉觀光糖廠園區景點總覽

### 工業歷史景點

| 景點 | 說明 |
|------|------|
| **製糖工場** | 保留龐大機組設備，展示製糖歷史流程 |
| **煙囪及囪底隧道** | 全國少見的囪底隧道，工業遺產特色景點 |
| **日立 #808 內燃機車頭** | 懷舊糖廠小火車頭展示 |
| **石轆** | 早期壓榨甘蔗的古董設備 |
| **台糖第一磅** | 歷史文物展示 |

### 休閒體驗

| 景點 | 說明 |
|------|------|
| **錦鯉魚池** | 觀賞錦鯉，適合悠閒散步 |
| **循環共享廣場** | 新設休閒廣場 |
| **循環共創小站** | 互動體驗空間 |

### 購物 & 飲食

| 設施 | 說明 |
|------|------|
| **展售賣場** | 販售台糖伴手禮、相關商品 |
| **冰店** | 招牌台糖冰品，09:00–17:00 |
| **團客餐廳** | 提供餐飲（團客為主） |

> 整體以工業歷史文化為主軸，免費入園，適合輕鬆半日遊。最推薦參觀**囪底隧道**，為全台少見特色景點。
