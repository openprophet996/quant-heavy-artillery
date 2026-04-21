import streamlit as st
import requests
import numpy as np
import json
import re

# --- 1. 全联盟核心战力库 (保持更新) ---
NBA_MASTER_DB = {
    "Rockets (火箭)": {"Kevin Durant": 28.5, "Alperen Sengun": 22.5, "Jalen Green": 19.5, "Fred VanVleet": 18.8, "Amen Thompson": 16.8},
    "Lakers (湖人)": {"Luka Doncic": 31.5, "Anthony Davis": 28.5, "Austin Reaves": 18.2, "Rui Hachimura": 15.5, "Jarred Vanderbilt": 14.0},
    "76ers (76人)": {"Joel Embiid": 32.0, "Tyrese Maxey": 24.5, "Paul George": 21.0, "Kelly Oubre Jr.": 15.5, "Caleb Martin": 14.0},
    "Celtics (凯尔特人)": {"Jayson Tatum": 26.5, "Jaylen Brown": 23.5, "Kristaps Porzingis": 21.0, "Derrick White": 18.5, "Jrue Holiday": 16.2},
    "Warriors (勇士)": {"Stephen Curry": 26.8, "Jimmy Butler": 24.2, "Draymond Green": 14.5, "Andrew Wiggins": 15.8},
    "Spurs (马刺)": {"Victor Wembanyama": 30.2, "Trae Young": 25.5, "Devin Vassell": 19.0, "Jeremy Sochan": 15.2},
    "Nuggets (掘金)": {"Nikola Jokic": 33.2, "Jamal Murray": 21.0, "Aaron Gordon": 17.5, "Michael Porter Jr.": 16.8},
    "Thunder (雷霆)": {"Shai Gilgeous-Alexander": 30.5, "Chet Holmgren": 22.0, "Jalen Williams": 19.8, "Isaiah Hartenstein": 16.5},
    "Suns (太阳)": {"Devin Booker": 24.8, "Bradley Beal": 18.5, "Kevin Durant": 28.5, "Jusuf Nurkic": 16.0},
}

st.set_page_config(page_title="量化重炮 V34.0", layout="wide")

# --- 2. API 核心对齐引擎 (带异常处理) ---
def fetch_realtime_data():
    try:
        url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&tag_id=10051"
        resp = requests.get(url, timeout=10).json()
        games = {}
        for m in resp:
            q = m.get('question', '')
            prices = json.loads(m['outcomePrices']) if isinstance(m['outcomePrices'], str) else m.get('outcomePrices')
            if not prices or len(prices) < 1: continue
            
            # 赔率换算
            raw_p = float(prices[0])
            odds = round(1 / raw_p, 2) if raw_p > 0 else 1.95
            # 让分提取
            spread_match = re.search(r'([+-]\d+\.?\d*)', q)
            spread_val = float(spread_match.group(1)) if spread_match else 0.0
            
            games[q] = {"odds": odds, "spread": spread_val}
        return games
    except Exception as e:
        st.error(f"API 链接失败: {e}")
        return {}

# --- 3. 界面逻辑 (使用 Session State 锁死数据) ---
st.title("🏹 量化重炮 V34.0 - 数据锁死稳定版")

# 第一步：同步
if st.button("🔥 第一步：一键同步 API 盘口", use_container_width=True):
    st.session_state.master_dict = fetch_realtime_data()

# 检查是否有数据，如果没有，显示警告并跳过后面逻辑
if "master_dict" not in st.session_state or not st.session_state.master_dict:
    st.warning("⚠️ 赔率尚未加载。请先点击上方的红色按钮同步 API 数据。")
else:
    # 第二步：选择比赛 (数据从缓存读取，保证不会消失)
    sel_q = st.selectbox("第二步：选择比赛盘口", list(st.session_state.master_dict.keys()))
    current_game = st.session_state.master_dict[sel_q]
    
    # 核心数据显示区 - 确保你选完后一眼就能看到
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1: st.metric("📢 实时赔率 (Odds)", current_game['odds'])
        with c2: st.metric("🎯 实时让分 (Spread)", current_game['spread'])

    # 第三步：阵容配置
    st.divider()
    col_h, col_a = st.columns(2)
    with col_h:
        h_team = st.selectbox("🏠 主队", list(NBA_MASTER_DB.keys()), key="h")
        h_miss = st.multiselect(f"{h_team} 缺阵:", options=list(NBA_MASTER_DB[h_team].keys()))
        h_loss = sum([NBA_MASTER_DB[h_team][p] for p in h_miss])
    with col_a:
        a_team = st.selectbox("🚩 客队", list(NBA_MASTER_DB.keys()), index=1, key="a")
        a_miss = st.multiselect(f"{a_team} 缺阵:", options=list(NBA_MASTER_DB[a_team].keys()))
        a_loss = sum([NBA_MASTER_DB[a_team][p] for p in a_miss])

    # 第四步：执行模拟
    st.divider()
    bankroll = st.sidebar.number_input("账户本金 ($)", value=2000)
    if st.button("🚀 第四步：启动 50,000 次深度推演", use_container_width=True):
        # 使用当前锁定的赔率和让分
        o = current_game['odds']
        s = current_game['spread']
        
        base_p = 1 / (10**(-s / 13.5) + 1)
        final_p = max(0.01, min(0.99, base_p + (a_loss - h_loss) * 0.0055))
        
        sims = np.random.choice([1, 0], size=50000, p=[final_p, 1-final_p])
        win_rate = np.mean(sims)
        ev = (win_rate * o) - 1
        
        # 结果反馈
        r1, r2 = st.columns(2)
        with r1: st.metric("预测真实胜率", f"{win_rate:.2%}")
        with r2: st.metric("期望回报 (EV)", f"{ev:.2%}")
        
        if ev > 0.05:
            st.success(f"💰 发现价值！赔率 {o} 具有博弈优势。")
        else:
            st.error("📉 赔率过低或风险过大，无价值。")
