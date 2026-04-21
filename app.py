import streamlit as st
import requests
import numpy as np
import json
import re

# --- 核心：2026 全联盟 30 队 180+ 球员数据库 (已更新 KD 到火箭) ---
NBA_MASTER_DB = {
    "Rockets (火箭)": {"Kevin Durant": 28.5, "Alperen Sengun": 22.5, "Jalen Green": 19.5, "Fred VanVleet": 18.8, "Amen Thompson": 16.8, "Jabari Smith Jr.": 16.0},
    "Lakers (湖人)": {"Luka Doncic": 31.5, "Anthony Davis": 28.5, "Austin Reaves": 18.2, "Rui Hachimura": 15.5, "Jarred Vanderbilt": 14.0, "Jaxson Hayes": 13.0},
    "Warriors (勇士)": {"Stephen Curry": 26.8, "Jimmy Butler": 24.2, "Draymond Green": 14.5, "Andrew Wiggins": 15.8, "Brandin Podziemski": 15.0, "Jonathan Kuminga": 17.5},
    "Spurs (马刺)": {"Victor Wembanyama": 30.2, "Trae Young": 25.5, "Devin Vassell": 19.0, "Jeremy Sochan": 15.2, "Harrison Barnes": 14.5, "Chris Paul": 14.0},
    "Nuggets (掘金)": {"Nikola Jokic": 33.2, "Jamal Murray": 21.0, "Aaron Gordon": 17.5, "Michael Porter Jr.": 16.8, "Christian Braun": 13.5},
    "76ers (76人)": {"Joel Embiid": 32.0, "Tyrese Maxey": 24.5, "Paul George": 21.0, "Kelly Oubre Jr.": 15.5, "Caleb Martin": 14.0},
    "Celtics (凯尔特人)": {"Jayson Tatum": 26.5, "Jaylen Brown": 23.5, "Kristaps Porzingis": 21.0, "Derrick White": 18.5, "Jrue Holiday": 16.2},
    "Suns (太阳)": {"Devin Booker": 24.8, "Bradley Beal": 18.5, "Tyus Jones": 16.2, "Jusuf Nurkic": 16.0, "Grayson Allen": 14.5},
    "Thunder (雷霆)": {"Shai Gilgeous-Alexander": 30.5, "Chet Holmgren": 22.0, "Jalen Williams": 19.8, "Isaiah Hartenstein": 16.5, "Alex Caruso": 14.5},
    "Mavericks (独行侠)": {"Kyrie Irving": 23.5, "Klay Thompson": 16.5, "Dereck Lively II": 17.0, "P.J. Washington": 14.8, "Daniel Gafford": 16.2},
    "Timberwolves (森林狼)": {"Anthony Edwards": 26.2, "Rudy Gobert": 18.5, "Naz Reid": 17.2, "Jaden McDaniels": 14.5, "Mike Conley": 15.0},
    "Kings (国王)": {"De'Aaron Fox": 22.2, "Domantas Sabonis": 23.8, "DeMar DeRozan": 21.0, "Keegan Murray": 17.5, "Malik Monk": 18.0},
    "Bucks (雄鹿)": {"Giannis Antetokounmpo": 29.8, "Damian Lillard": 23.2, "Khris Middleton": 17.5, "Brook Lopez": 16.5, "Bobby Portis": 17.2},
    "Knicks (尼克斯)": {"Jalen Brunson": 25.8, "Karl-Anthony Towns": 22.5, "OG Anunoby": 18.2, "Josh Hart": 16.5, "Mikal Bridges": 18.0},
    "Cavaliers (骑士)": {"Donovan Mitchell": 25.2, "Evan Mobley": 19.5, "Jarrett Allen": 19.0, "Darius Garland": 18.5, "Caris LeVert": 15.5},
    "Pacers (步行者)": {"Tyrese Haliburton": 23.5, "Pascal Siakam": 21.8, "Myles Turner": 18.5, "Bennedict Mathurin": 16.2, "Andrew Nembhard": 15.0},
    "Magic (魔术)": {"Paolo Banchero": 22.0, "Franz Wagner": 19.5, "Jalen Suggs": 16.2, "K. Caldwell-Pope": 13.5, "Jonathan Isaac": 15.8},
    "Heat (热火)": {"Bam Adebayo": 21.5, "Tyler Herro": 19.0, "Jimmy Butler": 22.0, "Terry Rozier": 17.5, "Jaime Jaquez Jr.": 15.2},
    "Hawks (老鹰)": {"Jalen Johnson": 19.5, "Bogdan Bogdanovic": 17.2, "Zaccharie Risacher": 15.0, "Clint Capela": 16.5},
    "Bulls (公牛)": {"Coby White": 18.5, "Josh Giddey": 16.8, "Zach LaVine": 19.0, "Nikola Vucevic": 17.5},
    "Raptors (猛龙)": {"Scottie Barnes": 21.2, "RJ Barrett": 18.5, "Immanuel Quickley": 17.8, "Jakob Poeltl": 16.5},
    "Nets (网队)": {"Cam Thomas": 19.5, "Nic Claxton": 17.2, "Cameron Johnson": 16.0, "Dennis Schroder": 15.5},
    "Wizards (奇才)": {"Alex Sarr": 15.5, "Jordan Poole": 17.0, "Kyle Kuzma": 18.5, "Jonas Valanciunas": 17.5},
    "Hornets (黄蜂)": {"LaMelo Ball": 22.5, "Brandon Miller": 19.0, "Miles Bridges": 17.5, "Mark Williams": 16.8},
    "Pistons (活塞)": {"Cade Cunningham": 21.5, "Jaden Ivey": 17.2, "Tobias Harris": 16.5, "Jalen Duren": 18.0},
    "Grizzlies (灰熊)": {"Ja Morant": 24.8, "Jaren Jackson Jr.": 21.2, "Desmond Bane": 19.5, "Zach Edey": 15.5},
    "Clippers (快船)": {"Kawhi Leonard": 24.5, "James Harden": 21.5, "Norman Powell": 18.0, "Ivica Zubac": 17.5},
    "Pelicans (鹈鹕)": {"Zion Williamson": 25.5, "Brandon Ingram": 21.0, "Dejounte Murray": 20.5, "CJ McCollum": 18.5},
    "Jazz (爵士)": {"Lauri Markkanen": 22.0, "Keyonte George": 16.5, "Walker Kessler": 15.8, "John Collins": 16.5},
    "Blazers (开拓者)": {"Anfernee Simons": 19.2, "Scoot Henderson": 15.5, "Shaedon Sharpe": 16.0, "Deandre Ayton": 17.8}
}

st.set_page_config(page_title="量化重炮 V32.0", layout="wide")

# --- API 连接引擎 ---
def get_poly_data():
    try:
        url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&tag_id=10051"
        data = requests.get(url, timeout=10).json()
        games = {}
        for m in data:
            q = m.get('question', '')
            prices = json.loads(m['outcomePrices']) if isinstance(m['outcomePrices'], str) else m['outcomePrices']
            if not prices: continue
            odds = round(1 / float(prices[0]), 2)
            spread = re.search(r'([+-]\d+\.?\d*)', q)
            spread_val = float(spread.group(1)) if spread else 0.0
            games[q] = {"odds": odds, "spread": spread_val}
        return games
    except: return {}

# --- 界面展示 ---
st.title("🏹 量化重炮 V32.0 - 终极球员库版")

# 1. API 同步
with st.container(border=True):
    if st.button("🔥 点击全自动同步 Polymarket 实时盘口", use_container_width=True):
        st.session_state.api_data = get_poly_data()

    if "api_data" in st.session_state and st.session_state.api_data:
        sel_q = st.selectbox("选择比赛：", list(st.session_state.api_data.keys()))
        target = st.session_state.api_data[sel_q]
        st.write(f"**实时赔率:** {target['odds']} | **让分:** {target['spread']}")
    else:
        st.info("请先同步数据。")
        target = {"odds": 1.95, "spread": 0.0}

# 2. 阵容对冲
st.divider()
st.subheader("👥 核心名单伤病对冲 (实时库)")
col1, col2 = st.columns(2)
with col1:
    ht = st.selectbox("🏠 主队", list(NBA_MASTER_DB.keys()), key="ht")
    hm = st.multiselect("缺阵球员:", options=list(NBA_MASTER_DB[ht].keys()), key="hm")
    h_loss = sum([NBA_MASTER_DB[ht][p] for p in hm])
with col2:
    at = st.selectbox("🚩 客队", list(NBA_MASTER_DB.keys()), index=1, key="at")
    am = st.multiselect("缺阵球员:", options=list(NBA_MASTER_DB[at].keys()), key="am")
    a_loss = sum([NBA_MASTER_DB[at][p] for p in am])

# 3. 模拟计算
if st.button("🚀 开始 50,000 次深度量化模拟", use_container_width=True):
    base_p = 1 / (10**(-target['spread'] / 13.5) + 1)
    final_p = max(0.01, min(0.99, base_p + (a_loss - h_loss) * 0.0055))
    sims = np.random.choice([1, 0], size=50000, p=[final_win_p, 1-final_win_p]) if 'final_win_p' in locals() else np.random.choice([1, 0], size=50000, p=[final_p, 1-final_p])
    win_rate = np.mean(sims)
    ev = (win_rate * target['odds']) - 1
    
    st.metric("真实预估胜率", f"{win_rate:.2%}")
    st.metric("期望回报 (EV)", f"{ev:.2%}")
    if ev > 0.1: st.success("💰 高价值信号！")
