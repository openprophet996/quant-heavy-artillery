import streamlit as st
import requests
import numpy as np
import json
import re

# --- 全联盟战力库 ---
NBA_DB = {
    "Rockets (火箭)": {"Kevin Durant": 28.5, "Alperen Sengun": 22.5, "Jalen Green": 19.5, "Fred VanVleet": 18.8},
    "Lakers (湖人)": {"Luka Doncic": 31.5, "Anthony Davis": 28.5, "Austin Reaves": 18.2, "Rui Hachimura": 15.5},
    "76ers (76人)": {"Joel Embiid": 32.0, "Tyrese Maxey": 24.5, "Paul George": 21.0},
    "Spurs (马刺)": {"Victor Wembanyama": 30.2, "Trae Young": 25.5, "Devin Vassell": 19.0},
    "Warriors (勇士)": {"Stephen Curry": 26.8, "Jimmy Butler": 24.2, "Draymond Green": 14.5}
}

st.set_page_config(page_title="NBA 多玩法量化终端 V38.0", layout="wide")

# --- API 识别引擎 ---
def get_poly_markets():
    try:
        url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&tag_id=10051"
        data = requests.get(url, timeout=5).json()
        games = []
        for m in data:
            q = m.get('question', '')
            p = json.loads(m['outcomePrices'])[0] if m.get('outcomePrices') else 0.5
            # 识别玩法
            m_type = "Moneyline"
            if "Spread" in q or re.search(r'[+-]\d+\.', q): m_type = "Spread"
            if "Total" in q or "Over" in q: m_type = "Over/Under"
            
            games.append({"title": q, "price": float(p), "type": m_type})
        return games
    except: return []

# --- 界面 ---
st.title("🏹 NBA 多玩法量化终端 V38.0")

if st.button("🔄 同步所有玩法 (Moneyline/Spread/OU)", use_container_width=True):
    st.session_state.all_games = get_poly_markets()

if "all_games" in st.session_state and st.session_state.all_games:
    # 玩法过滤器
    choice = st.selectbox("选择具体盘口", st.session_state.all_games, format_func=lambda x: f"[{x['type']}] {x['title']}")
    
    # 自动解析数据
    current_odds = round(1 / choice['price'], 2)
    sp_match = re.search(r'([+-]\d+\.?\d*)', choice['title'])
    current_spread = float(sp_match.group(1)) if sp_match else 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("当前玩法", choice['type'])
    c2.metric("当前赔率", current_odds)
    c3.metric("解析让分", current_spread if choice['type'] == "Spread" else "N/A")

    # 阵容对冲
    st.divider()
    col_h, col_a = st.columns(2)
    with col_h:
        h_t = st.selectbox("🏠 主队", list(NBA_DB.keys()), key="h")
        h_m = st.multiselect("缺阵:", options=list(NBA_DB[h_t].keys()))
        h_l = sum([NBA_DB[h_t][p] for p in h_m])
    with col_a:
        a_t = st.selectbox("🚩 客队", list(NBA_DB.keys()), index=1, key="a")
        a_m = st.multiselect("缺阵:", options=list(NBA_DB[a_t].keys()))
        a_l = sum([NBA_DB[a_t][p] for p in a_m])

    # 模拟
    if st.button("🚀 启动 50,000 次玩法针对性模拟", use_container_width=True):
        # 基础概率逻辑
        if choice['type'] == "Spread":
            base_p = 1 / (10**(-current_spread / 13.5) + 1)
        else: # Moneyline 或 Over/Under 暂时使用价格作为基准概率
            base_p = choice['price']
            
        final_p = max(0.01, min(0.99, base_p + (a_l - h_l) * 0.0055))
        sims = np.random.choice([1, 0], size=50000, p=[final_p, 1-final_p])
        win_rate = np.mean(sims)
        ev = (win_rate * current_odds) - 1
        
        st.metric("预测真实胜率/命中率", f"{win_rate:.2%}")
        st.metric("期望回报 (EV)", f"{ev:.2%}")
        if ev > 0.05: st.success("💰 该玩法具备下单价值")
else:
    st.info("请先点击上方按钮同步。")
