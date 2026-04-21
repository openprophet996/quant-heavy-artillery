import streamlit as st
import requests
import numpy as np
import json
import re

# --- 1. 全联盟 30 队核心战力库 (职业校准版) ---
NBA_MASTER_DB = {
    "Rockets (火箭)": {"Kevin Durant": 28.5, "Alperen Sengun": 22.5, "Jalen Green": 19.5, "Fred VanVleet": 18.8, "Amen Thompson": 16.8},
    "Lakers (湖人)": {"Luka Doncic": 31.5, "Anthony Davis": 28.5, "Austin Reaves": 18.2, "Rui Hachimura": 15.5, "Jarred Vanderbilt": 14.0},
    "76ers (76人)": {"Joel Embiid": 32.0, "Tyrese Maxey": 24.5, "Paul George": 21.0, "Kelly Oubre Jr.": 15.5, "Caleb Martin": 14.0},
    "Celtics (凯尔特人)": {"Jayson Tatum": 26.5, "Jaylen Brown": 23.5, "Kristaps Porzingis": 21.0, "Derrick White": 18.5, "Jrue Holiday": 16.2},
    "Spurs (马刺)": {"Victor Wembanyama": 30.2, "Trae Young": 25.5, "Devin Vassell": 19.0, "Jeremy Sochan": 15.2, "Harrison Barnes": 14.5},
    "Warriors (勇士)": {"Stephen Curry": 26.8, "Jimmy Butler": 24.2, "Draymond Green": 14.5, "Andrew Wiggins": 15.8},
    "Suns (太阳)": {"Devin Booker": 24.8, "Bradley Beal": 18.5, "Tyus Jones": 16.2, "Grayson Allen": 14.5},
    "Mavericks (独行侠)": {"Kyrie Irving": 23.5, "Klay Thompson": 16.5, "Dereck Lively II": 17.0, "P.J. Washington": 14.8},
    "Nuggets (掘金)": {"Nikola Jokic": 33.2, "Jamal Murray": 21.0, "Aaron Gordon": 17.5, "Michael Porter Jr.": 16.8},
    "Thunder (雷霆)": {"Shai Gilgeous-Alexander": 30.5, "Chet Holmgren": 22.0, "Jalen Williams": 19.8, "Alex Caruso": 14.5},
    "Bucks (雄鹿)": {"Giannis Antetokounmpo": 29.8, "Damian Lillard": 23.2, "Khris Middleton": 17.5, "Brook Lopez": 16.5},
    "Knicks (尼克斯)": {"Jalen Brunson": 25.8, "Karl-Anthony Towns": 22.5, "OG Anunoby": 18.2, "Mikal Bridges": 18.0},
    "Heat (热火)": {"Bam Adebayo": 21.5, "Tyler Herro": 19.0, "Jimmy Butler": 22.0, "Terry Rozier": 17.5},
    "Hawks (老鹰)": {"Jalen Johnson": 19.5, "Bogdan Bogdanovic": 17.2, "Zaccharie Risacher": 15.0, "Clint Capela": 16.5},
    "Pacers (步行者)": {"Tyrese Haliburton": 23.5, "Pascal Siakam": 21.8, "Myles Turner": 18.5, "Bennedict Mathurin": 16.2},
}

st.set_page_config(page_title="量化重炮 V36.0", layout="wide")

# --- 2. 核心：带缓存的 API 同步逻辑 ---
def fetch_api():
    try:
        url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&tag_id=10051"
        data = requests.get(url, timeout=10).json()
        res = {}
        for m in data:
            q = m.get('question', '')
            p_raw = json.loads(m['outcomePrices']) if isinstance(m['outcomePrices'], str) else m.get('outcomePrices')
            if not p_raw: continue
            
            odds = round(1 / float(p_raw[0]), 2) if float(p_raw[0]) > 0 else 1.95
            spread = re.search(r'([+-]\d+\.?\d*)', q)
            spread_val = float(spread.group(1)) if spread else 0.0
            res[q] = {"odds": odds, "spread": spread_val}
        return res
    except: return {}

# --- 3. 界面逻辑 ---
st.title("🏹 量化重炮 V36.0 - 稳定版")

# 初始化缓存
if "game_cache" not in st.session_state:
    st.session_state.game_cache = {}

# 第一步：同步盘口
with st.container(border=True):
    if st.button("🔥 点击同步 API 盘口数据", use_container_width=True):
        st.session_state.game_cache = fetch_api()

    if st.session_state.game_cache:
        sel_q = st.selectbox("选择要分析的比赛：", list(st.session_state.game_cache.keys()))
        current = st.session_state.game_cache[sel_q]
        st.info(f"已锁定：赔率 {current['odds']} | 让分 {current['spread']}")
    else:
        st.warning("盘口数据未加载，请点击上方红色按钮同步。")
        current = {"odds": 1.95, "spread": 0.0}

# 第二步：对冲名单
st.divider()
st.subheader("👥 配置伤病/缺阵名单")
c1, c2 = st.columns(2)
with c1:
    h_t = st.selectbox("🏠 主队", list(NBA_MASTER_DB.keys()), key="h")
    h_m = st.multiselect(f"{h_t} 缺阵:", options=list(NBA_MASTER_DB[h_t].keys()), key="hm")
    h_l = sum([NBA_MASTER_DB[h_t][p] for p in h_m])
with c2:
    a_t = st.selectbox("🚩 客队", list(NBA_MASTER_DB.keys()), index=1, key="at")
    a_m = st.multiselect(f"{a_t} 缺阵:", options=list(NBA_MASTER_DB[a_t].keys()), key="am")
    a_l = sum([NBA_MASTER_DB[a_t][p] for p in a_m])

# 第三步：推演
st.divider()
bankroll = st.sidebar.number_input("本金 ($)", value=2000)
if st.button("🚀 启动 50,000 次量化推演", use_container_width=True):
    # 基准胜率 (根据让分)
    base_p = 1 / (10**(-current['spread'] / 13.5) + 1)
    # 最终胜率 (加入球员对冲)
    final_p = max(0.01, min(0.99, base_p + (a_l - h_l) * 0.0055))
    
    # 执行蒙特卡洛
    sims = np.random.choice([1, 0], size=50000, p=[final_p, 1-final_p])
    win_rate = np.mean(sims)
    ev = (win_rate * current['odds']) - 1
    
    # 结果显示
    r1, r2, r3 = st.columns(3)
    with r1: st.metric("预测真实胜率", f"{win_rate:.2%}")
    with r2: st.metric("期望回报 (EV)", f"{ev:.2%}")
    with r3: 
        kelly = ((current['odds'] - 1) * win_rate - (1 - win_rate)) / (current['odds'] - 1) if current['odds'] > 1 else 0
        st.metric("建议下单量", f"${min(max(0, kelly * 0.5), 0.15) * bankroll:.2f}")

    if ev > 0.05: st.success("✅ 发现博弈价值！")
    else: st.error("❌ 赔率无法覆盖战力损失。")
