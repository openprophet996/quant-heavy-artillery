import streamlit as st
import requests
import numpy as np

# --- 1. 初始化 ---
st.set_page_config(page_title="量化重炮 V17.1 - 修复版", layout="wide")

# --- 2. 2026 全联盟核心球员数据库 ---
NBA_DB = {
    "湖人 (Lakers)": {"Luka Doncic": 19.5, "Austin Reaves": 7.2, "Rui Hachimura": 5.5},
    "奇才 (Wizards)": {"Anthony Davis": 14.8, "Jordan Poole": 6.0},
    "勇士 (Warriors)": {"Stephen Curry": 13.8, "Jimmy Butler": 12.2, "Draymond Green": 7.5},
    "马刺 (Spurs)": {"Victor Wembanyama": 16.5, "Trae Young": 13.5, "Devin Vassell": 7.0},
    "掘金 (Nuggets)": {"Nikola Jokic": 19.8, "Jamal Murray": 11.5, "Aaron Gordon": 8.0},
    "雷霆 (Thunder)": {"Shai Gilgeous-Alexander": 16.8, "Chet Holmgren": 12.0, "Jalen Williams": 9.5},
    "凯尔特人 (Celtics)": {"Jayson Tatum": 14.5, "Jaylen Brown": 12.5, "Kristaps Porzingis": 10.0},
    "独行侠 (Mavericks)": {"Kyrie Irving": 12.8, "Klay Thompson": 8.5, "Dereck Lively II": 7.5},
    "太阳 (Suns)": {"Kevin Durant": 13.5, "Devin Booker": 13.2, "Bradley Beal": 9.0},
    "森林狼 (Timberwolves)": {"Anthony Edwards": 15.5, "Rudy Gobert": 11.0, "Karl-Anthony Towns": 11.5},
    "尼克斯 (Knicks)": {"Jalen Brunson": 14.5, "OG Anunoby": 9.0, "Julius Randle": 10.5},
    "76人 (76ers)": {"Joel Embiid": 17.5, "Tyrese Maxey": 13.0, "Paul George": 11.5},
    "雄鹿 (Bucks)": {"Giannis Antetokounmpo": 16.2, "Damian Lillard": 12.5, "Khris Middleton": 8.5},
    "热火 (Heat)": {"Bam Adebayo": 11.5, "Tyler Herro": 9.0},
    "快船 (Clippers)": {"James Harden": 11.5, "Kawhi Leonard": 13.5},
    "国王 (Kings)": {"Domantas Sabonis": 12.8, "De'Aaron Fox": 12.2},
    "火箭 (Rockets)": {"Alperen Sengun": 11.0, "Jalen Green": 9.5},
    "灰熊 (Grizzlies)": {"Ja Morant": 13.5, "Jaren Jackson Jr.": 11.0},
    "步行者 (Pacers)": {"Tyrese Haliburton": 14.0, "Pascal Siakam": 11.5}
}

# --- 3. API 自动取价引擎 ---
def get_poly_live(search_keyword):
    try:
        url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&search={search_keyword}&limit=10"
        response = requests.get(url, timeout=5)
        data = response.json()
        results = []
        for market in data:
            if 'outcomePrices' in market:
                price = float(market['outcomePrices'][0])
                odds = round(1 / price, 2) if price > 0 else 2.0
                results.append({"name": market.get('question'), "odds": odds})
        return results
    except: return []

# --- 4. 界面渲染 ---
st.title("🏹 量化重炮 V17.1 - 修复稳定版")

# 步骤一：API 对接
with st.container(border=True):
    st.subheader("1️⃣ 自动同步 Polymarket 赔率")
    query = st.text_input("搜索球队名 (Lakers, Warriors...):", "Lakers")
    live_data = get_poly_live(query)
    if live_data:
        choice = st.selectbox("选择比赛：", live_data, format_func=lambda x: x['name'])
        final_odds = choice['odds']
        st.success(f"✅ 抓取成功！实时赔率：{final_odds}")
    else:
        final_odds = st.number_input("手动输入赔率:", value=1.95)

# 步骤二：全联盟对冲 (修复了 Duplicate ID 报错)
st.divider()
st.subheader("2️⃣ 阵容精准对冲")
col_l, col_r = st.columns(2)

with col_l:
    home_name = st.selectbox("🏠 选择主队", list(NBA_DB.keys()), key="home_select")
    # 增加唯一 key="home_m"
    h_m = st.multiselect(f"勾选 {home_name} 缺阵球员:", options=list(NBA_DB[home_name].keys()), key="home_m")
    h_loss = sum([NBA_DB[home_name][p] for p in h_m])

with col_r:
    # 增加唯一 key="away_select"
    away_name = st.selectbox("🚩 选择客队", list(NBA_DB.keys()), index=1, key="away_select")
    # 增加唯一 key="away_m"
    a_m = st.multiselect(f"勾选 {away_name} 缺阵球员:", options=list(NBA_DB[away_name].keys()), key="away_m")
    a_loss = sum([NBA_DB[away_name][p] for p in a_m])

# 步骤三：运算
st.divider()
bankroll = st.sidebar.number_input("💰 账户本金 ($)", value=2000)
base_p = st.sidebar.slider("初始基准胜率 (%)", 10, 95, 55)

if st.button("🚀 执行 30,000 次精准模拟"):
    calc_p = (base_p - h_loss + a_loss) / 100
    calc_p = max(0.01, min(0.99, calc_p))
    sims = np.random.choice([1, 0], size=30000, p=[calc_p, 1-calc_p])
    win_rate = np.mean(sims)
    
    ev = (win_rate * final_odds) - 1
    b = final_odds - 1
    kelly = (b * win_rate - (1 - win_rate)) / b if b > 0 else 0
    safe_amt = min(max(0, kelly * 0.5), 0.12) * bankroll

    r1, r2, r3 = st.columns(3)
    with r1: st.metric("修正后真实胜率", f"{win_rate:.2%}", delta=f"{a_loss - h_loss:.1f}%")
    with r2: st.metric("期望值 (EV)", f"{ev:.2%}")
    with r3: st.metric("建议下单金额", f"${safe_amt:.2f}")

    if ev > 0.05:
        st.success("🎯 发现价值，建议接入。")
    else:
        st.warning("❌ 无交易价值。")
