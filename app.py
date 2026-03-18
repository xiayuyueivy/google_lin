import warnings
import requests
from bs4 import BeautifulSoup
import streamlit as st

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

MAIN_URL = "https://www.taisugar.com.tw/chinese/Attractions_detail.aspx?n=10048&s=191&p=0"
NEWS_URL = "https://www.taisugar.com.tw/chinese/News_Index.aspx?p=71&n=10052"


def fetch_page(url):
    resp = requests.get(url, headers=HEADERS, timeout=30, verify=False)
    resp.raise_for_status()
    # 自動偵測編碼，優先使用 apparent_encoding
    encoding = resp.apparent_encoding or "utf-8"
    resp.encoding = encoding
    return BeautifulSoup(resp.text, "html.parser")


def get_basic_info():
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


# ── Streamlit UI ──────────────────────────────────────────
st.set_page_config(page_title="月眉觀光糖廠旅遊資訊", page_icon="🏭", layout="centered")

st.title("🏭 月眉觀光糖廠旅遊資訊")
st.caption("資料來源：台灣糖業公司官網")

# 固定資訊
st.subheader("📍 基本資訊")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**地址**：臺中市后里區甲后路二段350號")
    st.markdown("**電話**：04-2555-1100")
    st.markdown("**入園費**：免費")
with col2:
    st.markdown("**園區時間**：08:30 – 17:00")
    st.markdown("**冰店時間**：09:00 – 17:00")
    st.markdown("**公車**：92、155、212、213、215、813、888路")

st.divider()

# 園區景點
st.subheader("🗺️ 園區景點")

tab1, tab2, tab3 = st.tabs(["工業歷史", "休閒體驗", "購物飲食"])
with tab1:
    st.markdown("""
- 🏗️ **製糖工場** — 保留龐大機組設備，展示製糖歷史流程
- 🕳️ **煙囪及囪底隧道** — 全國少見的囪底隧道，工業遺產特色景點
- 🚂 **日立 #808 內燃機車頭** — 懷舊糖廠小火車頭展示
- ⚙️ **石轆** — 早期壓榨甘蔗的古董設備
- ⚖️ **台糖第一磅** — 歷史文物展示
""")
with tab2:
    st.markdown("""
- 🐟 **錦鯉魚池** — 觀賞錦鯉，適合悠閒散步
- 🌳 **循環共享廣場** — 新設休閒廣場
- 🎨 **循環共創小站** — 互動體驗空間
""")
with tab3:
    st.markdown("""
- 🛍️ **展售賣場** — 販售台糖伴手禮、相關商品
- 🍦 **冰店** — 招牌台糖冰品（09:00–17:00）
- 🍽️ **團客餐廳** — 提供餐飲（團客為主）
""")

st.divider()

# 即時爬蟲
st.subheader("📢 即時公告與注意事項")
if st.button("🔄 抓取最新公告"):
    with st.spinner("爬取中，請稍候..."):
        try:
            info = get_basic_info()
            news = get_latest_news()

            if info:
                for section, items in info.items():
                    st.markdown(f"**{section}**")
                    seen = set()
                    for item in items:
                        if item not in seen:
                            st.write(f"· {item}")
                            seen.add(item)
            else:
                st.info("目前官網無特別公告。")

            if news:
                st.markdown("**最新消息**")
                for n in news:
                    st.markdown(f"· [{n['標題']}]({n['連結']})")
            else:
                st.info("目前無月眉糖廠專屬最新公告。")

        except Exception as e:
            st.error(f"爬取失敗：{e}")
