import warnings
import requests
from bs4 import BeautifulSoup
import streamlit as st
import streamlit.components.v1 as components

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
    """只從主內容區塊 #cMainBlk 擷取各 h3 段落的重點資訊"""
    soup = fetch_page(MAIN_URL)
    main = soup.find(id="cMainBlk") or soup.body
    sections = {}
    for h3 in main.find_all("h3"):
        title = h3.get_text(strip=True)
        if not title:
            continue
        paragraphs = []
        for sib in h3.find_next_siblings():
            if sib.name == "h3":
                break
            text = sib.get_text(" ", strip=True)
            if text and len(text) > 5:
                paragraphs.append(text)
        if paragraphs:
            sections[title] = paragraphs
    return sections


def get_latest_news():
    """解析台糖活動快遞，擷取每筆新聞的標題、日期、連結"""
    soup = fetch_page(NEWS_URL)
    news_items = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if "News_detail" not in href:
            continue
        h3 = a_tag.find("h3")
        p = a_tag.find("p")
        title = h3.get_text(strip=True) if h3 else a_tag.get_text(strip=True)
        date_summary = p.get_text(strip=True) if p else ""
        if not title:
            continue
        full_url = (
            "https://www.taisugar.com.tw/chinese/" + href.lstrip("./")
            if not href.startswith("http")
            else href
        )
        news_items.append({"標題": title, "摘要": date_summary, "連結": full_url})
    return news_items


# ── Streamlit UI ──────────────────────────────────────────
st.set_page_config(page_title="月眉觀光糖廠旅遊資訊", page_icon="🏭", layout="wide")

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

# 兩欄：左為即時公告，右為社群貼文
left_col, right_col = st.columns([1, 1], gap="large")

# ── 左欄：即時公告 ──────────────────────────────────────
with left_col:
    st.subheader("📢 即時公告與注意事項")
    if st.button("🔄 抓取最新公告"):
        with st.spinner("爬取中，請稍候..."):
            try:
                info = get_basic_info()
                news = get_latest_news()

                if info:
                    for section, paragraphs in info.items():
                        with st.expander(f"📌 {section}"):
                            for p in paragraphs:
                                st.write(p)
                else:
                    st.info("目前官網無特別公告。")

                st.markdown("---")
                st.markdown("**📰 台糖最新消息**")
                if news:
                    for n in news:
                        st.markdown(f"**[{n['標題']}]({n['連結']})**")
                        if n["摘要"]:
                            st.caption(n["摘要"])
                else:
                    st.info("目前無最新消息。")

            except Exception as e:
                st.error(f"爬取失敗：{e}")

# ── 右欄：Facebook 社群貼文 ──────────────────────────────
with right_col:
    st.subheader("📘 Facebook 最新貼文")
    st.caption("台糖月眉觀光糖廠官方粉絲頁")
    components.html(
        """
        <div id="fb-root"></div>
        <script async defer crossorigin="anonymous"
            src="https://connect.facebook.net/zh_TW/sdk.js#xfbml=1&version=v19.0">
        </script>
        <div class="fb-page"
            data-href="https://www.facebook.com/TSCYUEMEI/"
            data-tabs="timeline"
            data-width="500"
            data-height="700"
            data-small-header="true"
            data-adapt-container-width="true"
            data-hide-cover="false"
            data-show-facepile="false">
        </div>
        """,
        height=720,
    )
