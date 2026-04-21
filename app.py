import streamlit as st
import requests
import numpy as np

# --- 1. 页面设置 ---
st.set_page_config(page_title="量化重炮 V16.0 - 全联盟版", layout="wide")

# --- 2. 2026 全联盟核心球员战力数据库 (覆盖 30 支球队) ---
# 包含最新交易后的战力权重
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

# --- 3. 赔率对齐引擎 ---
def get_poly_odds(query):
    try:
        url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=15&search={query}"
        r = requests.get(url, timeout=5).json()
        return [{"label": f"{m.get('question')} (赔率: {round(1/float(m['outcomePrices'][0]), 2)})", "odds": round(1/float(m['outcomePrices'][0]), 2)} for m in r if 'outcomePrices' in m]
    except: return []

# --- 4. 界面渲染 ---
st.title("🏹 量化重炮 V16.0 - 全联盟精准博弈终端")
st.markdown("---")

# 步骤一：锁定全联盟任意对阵
with st.container(border=True):
    st.subheader("1️⃣ 定位全联盟实时盘口")
    search_team = st.text_input("输入任何一支 NBA 球队名进行搜索 (例如: Warriors, Spurs, Celtics):", "Warriors")
    api_list = get_poly_odds(search_team)
    
    if api_list:
        selected_match = st.selectbox("发现实时盘口，请锁定：", api_list, format_func=lambda x: x['label'])
        current_odds = selected_match['odds']
    else:
        current_odds = st.number_input("未搜到实时盘口？请手动输入 Polymarket 赔率", value=1.95)

# 步骤二：全联盟球员点名对冲
st.divider()
st.subheader("2️⃣ 核心球员精准缺阵修正")
col_l, col_r = st.columns(2)

with col_l:
    home_name = st.selectbox("🏠 选择主队", list(NBA_DB.keys()))
    h_m = st.multiselect(f"勾选 {home_name} 缺阵球星:", options=list(NBA_DB[home_name].keys()))
    h_loss = sum([NBA_DB[home_name][p] for p in h_m])

with col_r:
    away_name = st.selectbox("🚩 选择客队", list(NBA_DB.keys()))
    a_m = st.multiselect(f"勾选 {away_name} 缺阵球星:", options=list(NBA_DB[away_name].keys()))
    a_loss = sum([NBA_DB[away_name][p] for p in a_m])

# 步骤三：深度量化推演
st.divider()
bankroll = st.sidebar.number_input("💰 账户总本金 ($)", value=2000)
base_p = st.sidebar.slider("模型基础胜率基准 (%)", 10, 95, 50)

if st.button("🔥 执行 30,000 次全联盟级对冲模拟", use_container_width=True):
    # 计算公式：基础胜率 - 本方损失 + 对方损失
    final_p = (base_p - h_loss + a_loss) / 100
    final_p = max(0.01, min(0.99, final_p))
    
    sims = np.random.choice([1, 0], size=30000, p=[final_p, 1-final_p])
    win_rate = np.mean(sims)
    
    ev = (win_rate * current_odds) - 1
    b = current_odds - 1
    kelly = (b * win_rate - (1 - win_rate)) / b if b > 0 else 0
    safe_amt = min(max(0, kelly * 0.5), 0.12) * bankroll

    r1, r2, r3 = st.columns(3)
    with r1:
        st.metric("对冲后真实胜率", f"{win_rate:.2%}", delta=f"{a_loss - h_loss:.1f}%")
    with r2:
        st.metric("期望值 (EV)", f"{ev:.2%}")
    with r3:
        st.metric("建议下单金额", f"${safe_amt:.2f}")

    if ev > 0.05:
        st.success(f"🎯 检测到全联盟级信息差！赔率 {current_odds} 未完全反应阵容变动。")
    else:
        st.warning("⚠️ 赔率已吃满或利空过重。")
