import streamlit as st
import requests
import numpy as np
import json
import re

# --- 1. 2026 全联盟 30 队核心战力库 (含 KD 火箭/Luka 湖人) ---
NBA_MASTER_DB = {
    "Rockets (火箭)": {"Kevin Durant": 28.5, "Alperen Sengun": 22.5, "Jalen Green": 19.5, "Fred VanVleet": 18.8, "Amen Thompson": 16.8},
    "Lakers (湖人)": {"Luka Doncic": 31.5, "Anthony Davis": 28.5, "Austin Reaves": 18.2, "Rui Hachimura": 15.5},
    "76ers (76人)": {"Joel Embiid": 32.0, "Tyrese Maxey": 24.5, "Paul George": 21.0, "Kelly Oubre Jr.": 15.5},
    "Celtics (凯尔特人)": {"Jayson Tatum": 26.5, "Jaylen Brown": 23.5, "Kristaps Porzingis": 21.0, "Derrick White": 18.5},
    "Spurs (马刺)": {"Victor Wembanyama": 30.2, "Trae Young": 25.5, "Devin Vassell": 19.0, "Jeremy Sochan": 15.2},
    "Warriors (勇士)": {"Stephen Curry": 26.8, "Jimmy Butler": 24.2, "Draymond Green": 14.5, "Andrew Wiggins": 15.8},
    "Suns (太阳)": {"Devin Booker": 24.8, "Bradley Beal": 18.5, "Tyus Jones": 16.2},
    "Mavericks (独行侠)": {"Kyrie Irving": 23.5, "Klay Thompson": 16.5, "Dereck Lively II": 17.0},
    "Nuggets (掘金)": {"Nikola Jokic": 33.2, "Jamal Murray": 21.0, "Aaron Gordon": 17.5},
    "Thunder (雷霆)": {"Shai Gilgeous-Alexander": 30.5, "Chet Holmgren": 22.0, "Jalen Williams": 19.8},
    "Bucks (雄鹿)": {"Giannis Antetokounmpo": 29.8, "Damian Lillard": 23.2},
    "Knicks (尼克斯)": {"Jalen Brunson": 25.8, "Karl-Anthony Towns": 22.5},
    "Heat (热火)": {"Bam Adebayo": 21.5, "Tyler Herro": 19.0},
    "Hawks (老鹰)": {"Jalen Johnson": 19.5, "Bogdan Bogdanovic": 17.2},
}

st.set_page_config(page_title="量化重炮 V37.0", layout="wide")

# --- 2. 增强型 API 解析引擎 ---
def fetch_now():
    try:
        url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&tag_id=10051"
        data = requests.get(url, timeout=5).json()
        res = {}
        for m in data:
            q = m.get('question', '')
            p_raw = json.loads(m['outcomePrices']) if isinstance(m['outcomePrices'], str) else m.get('outcomePrices')
            if p_raw:
                odd = round(1 / float(p_raw[0]), 2) if float(p_raw[0]) > 0 else 1.95
                sp = re.search(r'([+-]\d+\.?\d*)', q)
                res[q] = {"odds": odd, "spread": float(sp.group(1)) if sp else 0.0}
        return res
    except: return {}

# --- 3. 核心持久化逻辑 ---
if "db" not in st.session_state: st.session_state.db = {}
if "target_odds" not in st.session_state: st.session_state.target_odds = 1.95
if "target_spread" not in st.session_state: st.session_state.target_spread = 0.0

st.title("🏹 量化重炮 V37.0 - 钢铁逻辑版")

# 第一步：同步
with st.expander("📡 第一步：同步 API 数据", expanded=True):
    if st.button("🔄 立即执行全量同步", use_container_width=True):
        st.session_state.db = fetch_now()
        st.toast("API 同步尝试完成")

    if st.session_state.db:
        game_sel = st.selectbox("选择比赛：", list(st.session_state.db.keys()))
        st.session_state.target_odds = st.session_state.db[game_sel]['odds']
        st.session_state.target_spread = st.session_state.db[game_sel]['spread']
        st.success(f"已锁定：赔率 {st.session_state.target_odds} | 让分 {st.session_state.target_spread}")
    else:
        st.warning("未检测到 API 数据，将使用下方手动值进行模拟。")
        c1, c2 = st.columns(2)
        with c1: st.session_state.target_odds = st.number_input("手动校对赔率", value=1.95)
        with c2: st.session_state.target_spread = st.number_input("手动校对让分", value=0.0)

# 第二步：对冲名单
st.divider()
st.subheader("👥 第二步：配置球员缺阵")
col_h, col_a = st.columns(2)
with col_h:
    h_team = st.selectbox("🏠 主队", list(NBA_MASTER_DB.keys()), key="h_key")
    h_miss = st.multiselect(f"{h_team} 缺阵球员:", options=list(NBA_MASTER_DB[h_team].keys()), key="hm_key")
    h_loss = sum([NBA_MASTER_DB[h_team][p] for p in h_miss])
with col_a:
    a_team = st.selectbox("🚩 客队", list(NBA_MASTER_DB.keys()), index=1, key="a_key")
    a_miss = st.multiselect(f"{a_team} 缺阵球员:", options=list(NBA_MASTER_DB[a_team].keys()), key="am_key")
    a_loss = sum([NBA_MASTER_DB[a_team][p] for p in a_miss])

# 第三步：推演结果
st.divider()
bankroll = st.sidebar.number_input("本金 ($)", value=2000)
if st.button("🚀 第三步：启动 50,000 次深度模拟", use_container_width=True):
    # 强制读取当前锁定的值
    current_o = st.session_state.target_odds
    current_s = st.session_state.target_spread
    
    # 算法逻辑
    base_p = 1 / (10**(-current_s / 13.5) + 1)
    final_p = max(0.01, min(0.99, base_p + (a_loss - h_loss) * 0.0055))
    
    # 模拟运行
    sims = np.random.choice([1, 0], size=50000, p=[final_p, 1-final_p])
    win_rate = np.mean(sims)
    ev = (win_rate * current_o) - 1
    
    # 显示结果
    res1, res2, res3 = st.columns(3)
    with res1: st.metric("预测真实胜率", f"{win_rate:.2%}")
    with res2: st.metric("期望回报 (EV)", f"{ev:.2%}")
    with res3:
        kelly = ((current_o - 1) * win_rate - (1 - win_rate)) / (current_o - 1) if current_o > 1 else 0
        st.metric("建议下单量", f"${min(max(0, kelly * 0.5), 0.15) * bankroll:.2f}")

    if ev > 0.05: st.success("💰 存在显著博弈价值")
    else: st.error("📉 风险过高，无价值")
