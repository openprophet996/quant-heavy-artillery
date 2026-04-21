import streamlit as st
import requests
import numpy as np

# --- 1. 初始化配置 ---
st.set_page_config(page_title="量化重炮 V17.2 - 终极版", layout="wide")

# --- 2. 2026 全联盟核心球员数据库 (覆盖最新交易) ---
NBA_DB = {
    "湖人 (Lakers)": {"Luka Doncic": 19.5, "Austin Reaves": 7.2, "Rui Hachimura": 5.5, "Jarred Vanderbilt": 4.5},
    "奇才 (Wizards)": {"Anthony Davis": 14.8, "Jordan Poole": 6.0, "Kyle Kuzma": 8.5},
    "勇士 (Warriors)": {"Stephen Curry": 13.8, "Jimmy Butler": 12.2, "Draymond Green": 7.5, "Brandin Podziemski": 6.5},
    "马刺 (Spurs)": {"Victor Wembanyama": 16.5, "Trae Young": 13.5, "Devin Vassell": 7.0},
    "掘金 (Nuggets)": {"Nikola Jokic": 19.8, "Jamal Murray": 11.5, "Aaron Gordon": 8.0},
    "雷霆 (Thunder)": {"Shai Gilgeous-Alexander": 16.8, "Chet Holmgren": 12.0, "Jalen Williams": 9.5},
    "凯尔特人 (Celtics)": {"Jayson Tatum": 14.5, "Jaylen Brown": 12.5, "Kristaps Porzingis": 10.0},
    "独行侠 (Mavericks)": {"Kyrie Irving": 12.8, "Klay Thompson": 8.5, "Dereck Lively II": 7.5},
    "太阳 (Suns)": {"Kevin Durant": 13.5, "Devin Booker": 13.2, "Bradley Beal": 9.0},
    "森林狼 (Timberwolves)": {"Anthony Edwards": 15.5, "Rudy Gobert": 11.0, "Karl-Anthony Towns": 11.5},
    "尼克斯 (Knicks)": {"Jalen Brunson": 14.5, "OG Anunoby": 9.0, "Josh Hart": 6.5},
    "76人 (76ers)": {"Joel Embiid": 17.5, "Tyrese Maxey": 13.0, "Paul George": 11.5},
    "雄鹿 (Bucks)": {"Giannis Antetokounmpo": 16.2, "Damian Lillard": 12.5, "Brook Lopez": 7.0},
    "快船 (Clippers)": {"James Harden": 11.5, "Kawhi Leonard": 13.5, "Norman Powell": 8.0},
    "火箭 (Rockets)": {"Alperen Sengun": 11.0, "Jalen Green": 10.0, "Fred VanVleet": 9.5}
}

# --- 3. 增强型 API 对齐引擎 ---
def get_poly_live_final(query):
    try:
        # 使用更广泛的 API 搜索参数
        url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&search={query}&limit=20"
        response = requests.get(url, timeout=8)
        data = response.json()
        
        matches = []
        for m in data:
            # 过滤包含 outcomePrices 的盘口
            if 'outcomePrices' in m and m['outcomePrices']:
                p_yes = float(m['outcomePrices'][0])
                if 0.05 < p_yes < 0.95:  # 过滤掉已经没悬念的比赛
                    odds = round(1 / p_yes, 2)
                    matches.append({
                        "display": f"{m.get('question')} | 实时赔率: {odds}",
                        "val": odds
                    })
        return matches
    except Exception:
        return []

# --- 4. 界面布局 ---
st.title("🏹 量化重炮 V17.2 - 2026 全联盟实战终端")
st.markdown("---")

# 第一部分：API 实时抓取
with st.container(border=True):
    st.subheader("1️⃣ 对接 Polymarket 实时水位")
    search_input = st.text_input("输入球队关键词 (如 Lakers, Nuggets, Spurs):", value="Lakers")
    
    found_matches = get_poly_live_final(search_input)
    
    if found_matches:
        selected_match = st.selectbox("发现以下实时盘口，请选择：", 
                                    options=found_matches, 
                                    format_func=lambda x: x['display'],
                                    key="match_selector")
        current_odds = selected_match['val']
        st.success(f"✅ API 连接成功！已锁定赔率: **{current_odds}**")
    else:
        st.warning(f"⚠️ API 暂未在 Polymarket 搜到 '{search_input}' 相关盘口，请尝试英文缩写或手动填入。")
        current_odds = st.number_input("手动指定实时赔率:", value=1.95, step=0.01)

# 第二部分：双向球员对冲
st.divider()
st.subheader("2️⃣ 全联盟阵容精准对冲")
c1, c2 = st.columns(2)

with c1:
    h_team = st.selectbox("🏠 选择主队", list(NBA_DB.keys()), key="h_t")
    h_m = st.multiselect(f"{h_team} 缺阵球星:", options=list(NBA_DB[h_team].keys()), key="h_m_key")
    h_loss = sum([NBA_DB[h_team][p] for p in h_m])
    if h_m: st.error(f"主队战力流失: -{h_loss}%")

with c2:
    a_team = st.selectbox("🚩 选择客队", list(NBA_DB.keys()), index=1, key="a_t")
    a_m = st.multiselect(f"{a_team} 缺阵球星:", options=list(NBA_DB[a_team].keys()), key="a_m_key")
    a_loss = sum([NBA_DB[a_team][p] for p in a_m])
    if a_m: st.success(f"客队战力流失: +{a_loss}%")

# 第三部分：蒙特卡洛深度模拟
st.divider()
bankroll = st.sidebar.number_input("💰 账户总本金 ($)", value=2000)
base_win = st.sidebar.slider("初始基础胜率基准 (%)", 10, 95, 50)

if st.button("🔥 执行 30,000 次精准对冲推演", use_container_width=True):
    # 概率修正核心算法
    final_p = (base_win - h_loss + a_loss) / 100
    final_p = max(0.01, min(0.99, final_p))
    
    # 模拟运算
    sims = np.random.choice([1, 0], size=30000, p=[final_p, 1-final_p])
    real_wr = np.mean(sims)
    
    # 财务决策
    ev = (real_wr * current_odds) - 1
    b = current_odds - 1
    kelly = (b * real_wr - (1 - real_wr)) / b if b > 0 else 0
    safe_bet = min(max(0, kelly * 0.5), 0.12) * bankroll

    res_c1, res_c2, res_c3 = st.columns(3)
    with res_c1:
        st.metric("修正后真实胜率", f"{real_wr:.2%}", delta=f"{a_loss - h_loss:.1f}%")
    with res_c2:
        st.metric("期望值 (EV)", f"{ev:.2%}", delta="价值洼地" if ev > 0.05 else "风险/无利")
    with res_c3:
        st.metric("建议下单金额", f"${safe_bet:.2f}")

    if ev > 0.05:
        st.success(f"⚖️ 结论：发现显著信息差！建议以 ${safe_bet:.2f} 介入。")
    else:
        st.error("❌ 结论：赔率已吃满，不建议参与博弈。")

st.caption("数据源: Polymarket Gamma API (2026) | 战力模型: 量化重炮 V17.2")
