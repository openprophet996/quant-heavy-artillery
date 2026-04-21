import streamlit as st
import requests
import numpy as np
import json

# --- 1. 配置与全联盟 30 队数据库 (2026 赛季最新 PER 估值) ---
st.set_page_config(page_title="量化重炮 V22.0 - 全联盟版", layout="wide")

NBA_PER_DB = {
    # --- 西部 ---
    "Lakers (湖人)": {"Luka Doncic": 31.5, "Austin Reaves": 18.2, "Rui Hachimura": 15.5},
    "Warriors (勇士)": {"Stephen Curry": 26.8, "Jimmy Butler": 24.2, "Draymond Green": 14.5},
    "Wizards (奇才)": {"Anthony Davis": 28.5, "Jordan Poole": 17.0, "Kyle Kuzma": 18.5},
    "Spurs (马刺)": {"Victor Wembanyama": 30.2, "Trae Young": 25.5, "Devin Vassell": 19.0},
    "Nuggets (掘金)": {"Nikola Jokic": 33.2, "Jamal Murray": 21.0, "Aaron Gordon": 17.5},
    "Thunder (雷霆)": {"Shai Gilgeous-Alexander": 30.5, "Chet Holmgren": 22.0, "Jalen Williams": 19.8},
    "Suns (太阳)": {"Kevin Durant": 25.5, "Devin Booker": 24.8, "Bradley Beal": 18.5},
    "Mavericks (独行侠)": {"Kyrie Irving": 23.5, "Klay Thompson": 16.5, "Dereck Lively II": 17.0},
    "Timberwolves (森林狼)": {"Anthony Edwards": 26.2, "Rudy Gobert": 18.5, "Naz Reid": 17.2},
    "Rockets (火箭)": {"Alperen Sengun": 22.5, "Jalen Green": 19.5, "Amen Thompson": 16.8},
    "Grizzlies (灰熊)": {"Ja Morant": 24.8, "Jaren Jackson Jr.": 21.2, "Desmond Bane": 19.5},
    "Kings (国王)": {"De'Aaron Fox": 22.2, "Domantas Sabonis": 23.8, "Keegan Murray": 17.5},
    "Clippers (快船)": {"James Harden": 21.5, "Kawhi Leonard": 24.5, "Norman Powell": 18.0},
    "Pelicans (鹈鹕)": {"Zion Williamson": 25.5, "Brandon Ingram": 21.0, "CJ McCollum": 18.5},
    "Jazz (爵士)": {"Lauri Markkanen": 22.0, "Keyonte George": 16.5, "Walker Kessler": 15.8},
    "Blazers (开拓者)": {"Anfernee Simons": 19.2, "Scoot Henderson": 15.5, "Shaedon Sharpe": 16.0},

    # --- 东部 ---
    "Celtics (凯尔特人)": {"Jayson Tatum": 26.5, "Jaylen Brown": 23.5, "Kristaps Porzingis": 21.0},
    "76ers (76人)": {"Joel Embiid": 32.0, "Tyrese Maxey": 24.5, "Paul George": 21.0},
    "Bucks (雄鹿)": {"Giannis Antetokounmpo": 29.8, "Damian Lillard": 23.2, "Brook Lopez": 16.5},
    "Knicks (尼克斯)": {"Jalen Brunson": 25.8, "OG Anunoby": 18.2, "Karl-Anthony Towns": 22.5},
    "Cavaliers (骑士)": {"Donovan Mitchell": 25.2, "Evan Mobley": 19.5, "Jarrett Allen": 19.0},
    "Pacers (步行者)": {"Tyrese Haliburton": 23.5, "Pascal Siakam": 21.8, "Myles Turner": 18.5},
    "Magic (魔术)": {"Paolo Banchero": 22.0, "Franz Wagner": 19.5, "Jalen Suggs": 16.2},
    "Heat (热火)": {"Bam Adebayo": 21.5, "Tyler Herro": 19.0, "Terry Rozier": 17.5},
    "Hawks (老鹰)": {"Jalen Johnson": 19.5, "Bogdan Bogdanovic": 17.2, "Zaccharie Risacher": 15.0},
    "Bulls (公牛)": {"Coby White": 18.5, "Josh Giddey": 16.8, "Matas Buzelis": 14.5},
    "Raptors (猛龙)": {"Scottie Barnes": 21.2, "RJ Barrett": 18.5, "Immanuel Quickley": 17.8},
    "Nets (网队)": {"Cam Thomas": 19.5, "Nic Claxton": 17.2, "Cameron Johnson": 16.0},
    "Hornets (黄蜂)": {"LaMelo Ball": 22.5, "Brandon Miller": 19.0, "Miles Bridges": 17.5},
    "Pistons (活塞)": {"Cade Cunningham": 21.5, "Jaden Ivey": 17.2, "Jalen Duren": 18.0}
}

# --- 2. API 对接逻辑 ---
def fetch_poly_live(query):
    try:
        url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&search={query}&limit=10"
        resp = requests.get(url, timeout=5).json()
        results = []
        for m in resp:
            if 'outcomePrices' in m:
                # 处理某些 API 返回字符串或列表的兼容性
                prices = m['outcomePrices']
                if isinstance(prices, str): prices = json.loads(prices)
                if len(prices) >= 1:
                    y_p = float(prices[0])
                    odds = round(1 / y_p, 2) if y_p > 0 else 0
                    results.append({"title": m.get("question"), "odds": odds})
        return results
    except: return []

# --- 3. 界面逻辑 ---
st.title("🏹 量化重炮 V22.0 - NBA 全联盟实战终端")
st.markdown("---")

# 步骤一：API 输入
with st.container(border=True):
    st.subheader("1️⃣ 市场实时水位 (API 搜索)")
    search_q = st.text_input("输入球队英文词 (Lakers, Celtics, Nuggets...):", value="Lakers")
    live_res = fetch_poly_live(search_q)
    
    if live_res:
        choice = st.selectbox("对接实时盘口:", options=live_res, format_func=lambda x: f"{x['title']} (Odds: {x['odds']})")
        poly_odds = choice['odds']
        st.success(f"✅ API 成功！实时赔率锁定: {poly_odds}")
    else:
        st.warning("⚠️ API 未找到盘口，请手动填入赔率。")
        poly_odds = st.number_input("手动指定赔率:", value=1.95)

# 步骤二：全维度输入
st.divider()
st.subheader("2️⃣ 比赛核心维度输入")
sc1, sc2, sc3, sc4 = st.columns(4)
with sc1: spread = st.number_input("主队让分 (Spread):", value=-5.5)
with sc2: total_p = st.number_input("大小球 (Total Points):", value=225.5)
with sc3: bankroll = st.number_input("账户本金 ($):", value=2000)
with sc4: confidence = st.slider("信心修正 (0.5-1.0):", 0.5, 1.0, 0.5)

# 步骤三：双向球员状态修正
st.divider()
st.subheader("3️⃣ 阵容深度对冲")
col_h, col_a = st.columns(2)
status_map = {"Out (100%)": 1.0, "GTD (50%)": 0.5, "Probable (25%)": 0.25}

with col_h:
    h_team = st.selectbox("🏠 选择主队", list(NBA_PER_DB.keys()), key="h_t")
    h_m = st.multiselect(f"{h_team} 球员名单:", options=list(NBA_PER_DB[h_team].keys()), key="h_m")
    h_s = st.radio(f"{h_team} 状态等级:", list(status_map.keys()), key="h_s", horizontal=True)
    h_loss = sum([NBA_PER_DB[h_team][p] for p in h_m]) * status_map[h_s]

with col_a:
    a_team = st.selectbox("🚩 选择客队", list(NBA_PER_DB.keys()), index=1, key="a_t")
    a_m = st.multiselect(f"{a_team} 球员名单:", options=list(NBA_PER_DB[a_team].keys()), key="a_m")
    a_s = st.radio(f"{a_team} 状态等级:", list(status_map.keys()), key="a_s", horizontal=True)
    a_loss = sum([NBA_PER_DB[a_team][p] for p in a_m]) * status_map[a_s]

# 步骤四：蒙特卡洛量化推演
st.divider()
if st.button("🚀 开始执行 50,000 次深度量化模拟", use_container_width=True):
    # 核心算法
    base_prob = 1 / (10**(-spread / 13.5) + 1)
    pace_factor = 1.15 if total_p > 230 else (0.85 if total_p < 215 else 1.0)
    
    # PER 影响力换算 (每 10 点 PER 差异影响约 5% 胜率)
    impact = (a_loss - h_loss) * 0.005 * pace_factor
    final_win_p = base_prob + impact
    final_win_p = max(0.01, min(0.99, final_win_p))
    
    # 模拟运行
    sim_runs = np.random.choice([1, 0], size=50000, p=[final_win_p, 1-final_win_p])
    calc_win_rate = np.mean(sim_runs)
    
    # 财务决策
    ev = (calc_win_rate * poly_odds) - 1
    b = poly_odds - 1
    kelly = (b * calc_win_rate - (1 - calc_win_rate)) / b if b > 0 else 0
    safe_bet = min(max(0, kelly * confidence), 0.15) * bankroll

    # 输出
    res_c1, res_c2, res_c3 = st.columns(3)
    with res_c1: st.metric("修正后真实胜率", f"{calc_win_rate:.2%}", delta=f"{(calc_win_rate-base_prob):.1%}")
    with res_c2: st.metric("期望收益 (EV)", f"{ev:.2%}", delta="价值洼地" if ev > 0.08 else None)
    with res_c3: st.metric("建议下单量", f"${safe_bet:.2f}")

    if ev > 0.08:
        st.success("🎯 深度扫描结论：赔率存在巨大偏差，建议立刻介入。")
    elif ev > 0:
        st.info("⚖️ 结论：优势微弱，建议轻仓博弈。")
    else:
        st.error("❌ 结论：此盘口无利可图。")
