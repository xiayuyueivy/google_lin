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
