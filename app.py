import streamlit as st
import requests
import numpy as np

# --- 1. 初始化 ---
st.set_page_config(page_title="量化重炮 V18.0 - NBA 英文实战版", layout="wide")

# --- 2. 2026 全联盟球星权重库 (基于最新交易) ---
NBA_DB = {
    "Lakers (LAL)": {"Luka Doncic": 19.5, "Austin Reaves": 7.2, "Rui Hachimura": 5.5},
    "Wizards (WAS)": {"Anthony Davis": 14.8, "Jordan Poole": 6.5},
    "Warriors (GSW)": {"Stephen Curry": 13.8, "Jimmy Butler": 12.2, "Draymond Green": 7.5},
    "Spurs (SAS)": {"Victor Wembanyama": 16.5, "Trae Young": 13.5, "Devin Vassell": 7.0},
    "Nuggets (DEN)": {"Nikola Jokic": 19.8, "Jamal Murray": 11.5, "Aaron Gordon": 8.0},
    "Thunder (OKC)": {"Shai Gilgeous-Alexander": 16.8, "Chet Holmgren": 12.0},
    "Celtics (BOS)": {"Jayson Tatum": 14.5, "Jaylen Brown": 12.5, "Kristaps Porzingis": 10.0},
    "Mavericks (DAL)": {"Kyrie Irving": 12.8, "Klay Thompson": 8.5},
    "Suns (PHX)": {"Kevin Durant": 13.5, "Devin Booker": 13.2},
    "Timberwolves (MIN)": {"Anthony Edwards": 15.5, "Rudy Gobert": 11.0},
    "Knicks (NYK)": {"Jalen Brunson": 14.5, "OG Anunoby": 9.0},
    "76ers (PHI)": {"Joel Embiid": 17.5, "Tyrese Maxey": 13.0, "Paul George": 11.5},
    "Bucks (MIL)": {"Giannis Antetokounmpo": 16.2, "Damian Lillard": 12.5},
    "Rockets (HOU)": {"Alperen Sengun": 11.0, "Jalen Green": 10.0},
    "Grizzlies (MEM)": {"Ja Morant": 13.5, "Jaren Jackson Jr.": 11.0},
    "Pacers (IND)": {"Tyrese Haliburton": 14.0, "Pascal Siakam": 11.5},
    "Kings (SAC)": {"Domantas Sabonis": 12.8, "De'Aaron Fox": 12.2}
}

# --- 3. 英文 API 抓取函数 ---
def get_poly_live(keyword):
    try:
        # 强制搜索活跃的 NBA 相关盘口
        url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&search={keyword}&limit=15"
        resp = requests.get(url, timeout=5).json()
        matches = []
        for m in resp:
            if 'outcomePrices' in m and m['outcomePrices']:
                # 取得 Yes 的价格
                price = float(m['outcomePrices'][0])
                if 0.01 < price < 0.99:
                    odds = round(1 / price, 2)
                    matches.append({"label": f"{m.get('question')} (Odds: {odds})", "odds": odds})
        return matches
    except: return []

# --- 4. 界面渲染 ---
st.title("🏹 量化重炮 V18.0 - 英文 API 实战终端")

# 步骤一：API 对接 (只支持英文搜索)
with st.container(border=True):
    st.subheader("1️⃣ 实时对齐 Polymarket (Search in English)")
    search_en = st.text_input("Enter Team Name (e.g. Lakers, Warriors, Celtics):", "Lakers")
    api_res = get_poly_live(search_en)
    
    if api_res:
        selected = st.selectbox("Select Market:", api_res, format_func=lambda x: x['label'])
        live_odds = selected['odds']
        st.success(f"✅ Connected! Live Odds: {live_odds}")
    else:
        st.warning("No active markets found. Check spelling or enter odds manually.")
        live_odds = st.number_input("Manual Odds:", value=1.95)

# 步骤二：阵容对冲
st.divider()
st.subheader("2️⃣ Precise Player Impact (2026 Rosters)")
c1, c2 = st.columns(2)

with c1:
    h_team = st.selectbox("🏠 Home Team", list(NBA_DB.keys()), key="h_t")
    h_m = st.multiselect(f"{h_team} INJURY/OUT:", options=list(NBA_DB[h_team].keys()), key="h_m")
    h_loss = sum([NBA_DB[h_team][p] for p in h_m])

with c2:
    a_team = st.selectbox("🚩 Away Team", list(NBA_DB.keys()), index=1, key="a_t")
    a_m = st.multiselect(f"{a_team} INJURY/OUT:", options=list(NBA_DB[a_team].keys()), key="a_m")
    a_loss = sum([NBA_DB[a_team][p] for p in a_m])

# 步骤三：深度推演
st.divider()
bankroll = st.sidebar.number_input("💰 Bankroll ($)", value=2000)
base_p = st.sidebar.slider("Base Win Probability (%)", 10, 95, 50)

if st.button("🚀 RUN 30,000 MONTE CARLO SIMULATIONS", use_container_width=True):
    # 对冲算法
    final_p = (base_p - h_loss + a_loss) / 100
    final_p = max(0.01, min(0.99, final_p))
    
    # 模拟
    sims = np.random.choice([1, 0], size=30000, p=[final_p, 1-final_p])
    win_rate = np.mean(sims)
    
    # 结果
    ev = (win_rate * live_odds) - 1
    b = live_odds - 1
    kelly = (b * win_rate - (1 - win_rate)) / b if b > 0 else 0
    bet_amt = min(max(0, kelly * 0.5), 0.12) * bankroll

    r1, r2, r3 = st.columns(3)
    with r1: st.metric("Adjusted Win Rate", f"{win_rate:.2%}", delta=f"{a_loss - h_loss:.1f}%")
    with r2: st.metric("Expected Value (EV)", f"{ev:.2%}")
    with r3: st.metric("Suggested Bet", f"${bet_amt:.2f}")

    if ev > 0.05:
        st.success("🎯 SIGNAL: ALPHA DETECTED. HIGH CONVICTION.")
    else:
        st.error("❌ SIGNAL: NO VALUE / HIGH RISK.")
