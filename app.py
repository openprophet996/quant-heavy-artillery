import streamlit as st
import requests
import numpy as np
import json

# --- 1. 配置与【全量级】30 队核心球员数据库 ---
st.set_page_config(page_title="量化重炮 V24.0 - 全量实战版", layout="wide")

# 数据库包含 30 支球队及其 2026 赛季最新核心 PER 估值
NBA_FULL_DB = {
    # 西部 - 太平洋赛区
    "Lakers (湖人)": {"Luka Doncic": 31.5, "Austin Reaves": 18.2, "Rui Hachimura": 15.5, "Jarred Vanderbilt": 14.0},
    "Warriors (勇士)": {"Stephen Curry": 26.8, "Jimmy Butler": 24.2, "Draymond Green": 14.5, "Andrew Wiggins": 15.8},
    "Suns (太阳)": {"Kevin Durant": 25.5, "Devin Booker": 24.8, "Bradley Beal": 18.5, "Jusuf Nurkic": 16.2},
    "Kings (国王)": {"De'Aaron Fox": 22.2, "Domantas Sabonis": 23.8, "Keegan Murray": 17.5, "Malik Monk": 18.0},
    "Clippers (快船)": {"Kawhi Leonard": 24.5, "James Harden": 21.5, "Norman Powell": 18.0, "Ivica Zubac": 17.5},
    
    # 西部 - 西北赛区
    "Nuggets (掘金)": {"Nikola Jokic": 33.2, "Jamal Murray": 21.0, "Aaron Gordon": 17.5, "Michael Porter Jr.": 16.8},
    "Thunder (雷霆)": {"Shai Gilgeous-Alexander": 30.5, "Chet Holmgren": 22.0, "Jalen Williams": 19.8, "Isaiah Hartenstein": 16.5},
    "Timberwolves (森林狼)": {"Anthony Edwards": 26.2, "Rudy Gobert": 18.5, "Naz Reid": 17.2, "Jaden McDaniels": 14.5},
    "Jazz (爵士)": {"Lauri Markkanen": 22.0, "Keyonte George": 16.5, "Walker Kessler": 15.8, "John Collins": 16.5},
    "Blazers (开拓者)": {"Anfernee Simons": 19.2, "Scoot Henderson": 15.5, "Shaedon Sharpe": 16.0, "Deandre Ayton": 17.8},
    
    # 西部 - 西南赛区
    "Mavericks (独行侠)": {"Kyrie Irving": 23.5, "Klay Thompson": 16.5, "Dereck Lively II": 17.0, "P.J. Washington": 14.8},
    "Spurs (马刺)": {"Victor Wembanyama": 30.2, "Trae Young": 25.5, "Devin Vassell": 19.0, "Jeremy Sochan": 15.2},
    "Rockets (火箭)": {"Alperen Sengun": 22.5, "Jalen Green": 19.5, "Fred VanVleet": 18.8, "Amen Thompson": 16.8},
    "Grizzlies (灰熊)": {"Ja Morant": 24.8, "Jaren Jackson Jr.": 21.2, "Desmond Bane": 19.5, "Zach Edey": 15.5},
    "Pelicans (鹈鹕)": {"Zion Williamson": 25.5, "Brandon Ingram": 21.0, "Dejounte Murray": 20.5, "Herb Jones": 15.0},

    # 东部 - 大西洋赛区
    "Celtics (凯尔特人)": {"Jayson Tatum": 26.5, "Jaylen Brown": 23.5, "Kristaps Porzingis": 21.0, "Derrick White": 18.5},
    "76ers (76人)": {"Joel Embiid": 32.0, "Tyrese Maxey": 24.5, "Paul George": 21.0, "Kelly Oubre Jr.": 15.5},
    "Knicks (尼克斯)": {"Jalen Brunson": 25.8, "Karl-Anthony Towns": 22.5, "OG Anunoby": 18.2, "Josh Hart": 16.5},
    "Raptors (猛龙)": {"Scottie Barnes": 21.2, "RJ Barrett": 18.5, "Immanuel Quickley": 17.8, "Jakob Poeltl": 16.5},
    "Nets (网队)": {"Cam Thomas": 19.5, "Nic Claxton": 17.2, "Cameron Johnson": 16.0, "Dennis Schroder": 15.5},

    # 东部 - 中部赛区
    "Bucks (雄鹿)": {"Giannis Antetokounmpo": 29.8, "Damian Lillard": 23.2, "Khris Middleton": 17.5, "Brook Lopez": 16.5},
    "Cavaliers (骑士)": {"Donovan Mitchell": 25.2, "Evan Mobley": 19.5, "Jarrett Allen": 19.0, "Darius Garland": 18.5},
    "Pacers (步行者)": {"Tyrese Haliburton": 23.5, "Pascal Siakam": 21.8, "Myles Turner": 18.5, "Bennedict Mathurin": 16.2},
    "Bulls (公牛)": {"Coby White": 18.5, "Josh Giddey": 16.8, "Zach LaVine": 19.0, "Nikola Vucevic": 17.5},
    "Pistons (活塞)": {"Cade Cunningham": 21.5, "Jaden Ivey": 17.2, "Tobias Harris": 16.5, "Jalen Duren": 18.0},

    # 东部 - 东南赛区
    "Magic (魔术)": {"Paolo Banchero": 22.0, "Franz Wagner": 19.5, "Jalen Suggs": 16.2, "Kentavious Caldwell-Pope": 13.5},
    "Heat (热火)": {"Bam Adebayo": 21.5, "Tyler Herro": 19.0, "Jimmy Butler": 22.0, "Terry Rozier": 17.5},
    "Hawks (老鹰)": {"Jalen Johnson": 19.5, "Bogdan Bogdanovic": 17.2, "Zaccharie Risacher": 15.0, "Clint Capela": 16.5},
    "Wizards (奇才)": {"Alex Sarr": 15.5, "Jordan Poole": 17.0, "Kyle Kuzma": 18.5, "Bub Carrington": 14.2},
    "Hornets (黄蜂)": {"LaMelo Ball": 22.5, "Brandon Miller": 19.0, "Miles Bridges": 17.5, "Mark Williams": 16.8}
}

# --- 2. API 增强连接逻辑 ---
def fetch_nba_api_odds():
    try:
        url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=50&tag_id=10051"
        data = requests.get(url, timeout=10).json()
        matches = []
        for m in data:
            if 'outcomePrices' in m:
                prices = json.loads(m['outcomePrices']) if isinstance(m['outcomePrices'], str) else m['outcomePrices']
                if prices:
                    odds = round(1 / float(prices[0]), 2)
                    matches.append({"title": m['question'], "odds": odds})
        return matches
    except: return []

# --- 3. 界面逻辑 ---
st.title("🏹 量化重炮 V24.0 - 全联盟完整体")

# 步骤一：API 实时对齐
with st.container(border=True):
    st.subheader("1️⃣ 对接 Polymarket 实时盘口")
    if st.button("📡 点击同步全联盟最新赔率"):
        st.session_state.nba_list = fetch_nba_api_odds()
    
    if "nba_list" in st.session_state and st.session_state.nba_list:
        selected_match = st.selectbox("选择对阵：", st.session_state.nba_list, format_func=lambda x: f"{x['title']} | 赔率: {x['odds']}")
        current_odds = selected_match['odds']
    else:
        current_odds = st.number_input("手动填入赔率 (如 API 未连接):", value=1.95)

# 步骤二：全维度输入
st.divider()
st.subheader("2️⃣ 核心数据输入")
c1, c2, c3 = st.columns(3)
with c1: spread = st.number_input("主队让分 (Spread):", value=-4.5)
with c2: total_pts = st.number_input("大小球预设 (Total):", value=228.5)
with c3: bankroll = st.number_input("账户本金 ($):", value=2000)

# 步骤三：【全量级】球员对冲
st.subheader("3️⃣ 全联盟阵容实时对冲")
col_h, col_a = st.columns(2)
status_opts = {"Out (确定缺阵)": 1.0, "GTD (赛前决定)": 0.5, "Probable (大概率打)": 0.2}

with col_h:
    h_name = st.selectbox("🏠 选择主队", list(NBA_FULL_DB.keys()), key="h_team")
    h_inj = st.multiselect(f"{h_name} 关键球员变动:", options=list(NBA_FULL_DB[h_name].keys()), key="h_inj")
    h_s = st.radio("主队伤病严重度:", list(status_opts.keys()), key="h_s", horizontal=True)
    h_impact = sum([NBA_FULL_DB[h_name][p] for p in h_inj]) * status_opts[h_s]

with col_a:
    a_name = st.selectbox("🚩 选择客队", list(NBA_FULL_DB.keys()), index=1, key="a_team")
    a_inj = st.multiselect(f"{a_name} 关键球员变动:", options=list(NBA_FULL_DB[a_name].keys()), key="a_inj")
    a_s = st.radio("客队伤病严重度:", list(status_opts.keys()), key="a_s", horizontal=True)
    a_impact = sum([NBA_FULL_DB[a_name][p] for p in a_inj]) * status_opts[a_s]

# 步骤四：执行模拟
st.divider()
if st.button("🚀 启动 50,000 次深度蒙特卡洛计算", use_container_width=True):
    # 算法：让分基础胜率 + PER 差异影响系数 + 节奏系数
    base_prob = 1 / (10**(-spread / 13.5) + 1)
    pace_mod = 1.12 if total_pts > 232 else (0.88 if total_pts < 218 else 1.0)
    
    # 核心公式：战力差值转化为胜率修正
    final_win_p = base_prob + (a_impact - h_impact) * 0.0055 * pace_mod
    final_win_p = max(0.01, min(0.99, final_win_p))
    
    # 模拟
    results = np.random.choice([1, 0], size=50000, p=[final_win_p, 1-final_win_p])
    win_rate = np.mean(results)
    
    # 结果分析
    ev = (win_rate * current_odds) - 1
    kelly = ((current_odds - 1) * win_rate - (1 - win_rate)) / (current_odds - 1) if current_odds > 1 else 0
    bet_suggestion = min(max(0, kelly * 0.5), 0.12) * bankroll

    r1, r2, r3 = st.columns(3)
    with r1: st.metric("修正后真实胜率", f"{win_rate:.2%}", delta=f"{(win_rate-base_prob):.1%}")
    with r2: st.metric("期望值 (EV)", f"{ev:.2%}")
    with r3: st.metric("下单建议", f"${bet_suggestion:.2f}")

    if ev > 0.08: st.success("💰 发现严重价值洼地，建议按仓位介入。")
    elif ev > 0: st.info("⚖️ 优势微弱，建议谨慎博弈。")
    else: st.error("❌ 无套利空间，市场赔率已覆盖风险。")
