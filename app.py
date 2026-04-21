import streamlit as st
import numpy as np

# --- 1. 配置与全联盟 PER 核心库 (基于 2026 实时表现) ---
st.set_page_config(page_title="量化重炮 V20.0 - 全维度版", layout="wide")

# 权重逻辑：PER值越高，缺阵对胜率的负面影响越指数级增加
NBA_PER_DB = {
    "Lakers (LAL)": {"Luka Doncic": 31.5, "Austin Reaves": 18.2, "Rui Hachimura": 15.5},
    "Warriors (GSW)": {"Stephen Curry": 26.8, "Jimmy Butler": 24.2, "Draymond Green": 14.5},
    "Wizards (WAS)": {"Anthony Davis": 28.5, "Jordan Poole": 17.0, "Kyle Kuzma": 18.5},
    "Spurs (SAS)": {"Victor Wembanyama": 30.2, "Trae Young": 25.5, "Devin Vassell": 19.0},
    "Nuggets (DEN)": {"Nikola Jokic": 33.2, "Jamal Murray": 21.0, "Aaron Gordon": 17.5},
    "Celtics (BOS)": {"Jayson Tatum": 26.5, "Jaylen Brown": 23.5, "Kristaps Porzingis": 21.0},
    "Thunder (OKC)": {"Shai Gilgeous-Alexander": 30.5, "Chet Holmgren": 22.0},
    "Suns (PHX)": {"Kevin Durant": 25.5, "Devin Booker": 24.8, "Bradley Beal": 18.5},
    "Mavericks (DAL)": {"Kyrie Irving": 23.5, "Klay Thompson": 16.5, "Dereck Lively II": 17.0},
    "76ers (PHI)": {"Joel Embiid": 32.0, "Tyrese Maxey": 24.5, "Paul George": 21.0}
}

# --- 2. 核心数学函数 ---
def spread_to_win_prob(spread):
    """将让分盘转换为原始胜率: Win% = 1 / (10^(-spread/13.5) + 1)"""
    return 1 / (10**(-spread / 13.5) + 1)

# --- 3. 界面渲染 ---
st.title("🏹 量化重炮 V20.0 - 全维度精准模拟器")
st.info("模式：让分转换 + 大小球节奏修正 + 球员 PER 深度模拟")

# 第一部分：市场盘口维度
with st.container(border=True):
    st.subheader("1️⃣ 盘口多维输入 (Market Inputs)")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        spread = st.number_input("主队让分 (Spread):", value=-5.5, help="负数代表主队让分，正数代表受让")
    with c2:
        total_points = st.number_input("大小球预设 (Total):", value=225.5)
    with c3:
        poly_odds = st.number_input("Polymarket 实时赔率:", value=1.95)
    with c4:
        bankroll = st.number_input("账户本金 ($):", value=2000)

# 第二部分：球员状态维度
st.divider()
st.subheader("2️⃣ 球员出席状态 (Status Check)")
col_h, col_a = st.columns(2)

status_map = {"确定缺阵 (Out)": 1.0, "出战成疑 (GTD 50%)": 0.5, "大概率出战 (Probable 25%)": 0.25}

with col_h:
    h_team = st.selectbox("🏠 主队", list(NBA_PER_DB.keys()), key="h_t")
    h_m = st.multiselect(f"{h_team} 关键球员变动:", options=list(NBA_PER_DB[h_team].keys()), key="h_m")
    h_status = st.radio("主队球员状态等级:", list(status_map.keys()), key="h_s", horizontal=True)
    h_loss = sum([NBA_PER_DB[h_team][p] for p in h_m]) * status_map[h_status]

with col_a:
    a_team = st.selectbox("🚩 客队", list(NBA_PER_DB.keys()), index=1, key="a_t")
    a_m = st.multiselect(f"{a_team} 关键球员变动:", options=list(NBA_PER_DB[a_team].keys()), key="a_m")
    a_status = st.radio("客队球员状态等级:", list(status_map.keys()), key="a_s", horizontal=True)
    a_loss = sum([NBA_PER_DB[a_team][p] for p in a_m]) * status_map[a_status]

# 第三部分：蒙特卡洛深度模拟
st.divider()
if st.button("🔥 执行 50,000 次多维度全量模拟", use_container_width=True):
    # A. 计算初始胜率
    base_win_prob = spread_to_win_prob(spread)
    
    # B. 节奏修正 (Pace Adjustment)
    # 如果总分高于 230，球员缺阵的影响增加 15%；低于 215，影响减少 15%
    pace_factor = 1.0
    if total_points > 230: pace_factor = 1.15
    elif total_points < 215: pace_factor = 0.85
    
    # C. 战力价值转换 (将 PER 损失转化为胜率波动)
    # 逻辑：每 10 点 PER 影响约 4%-6% 的胜率波动
    net_per_impact = (a_loss - h_loss) * 0.005 * pace_factor
    final_p = base_win_prob + net_per_impact
    final_p = max(0.01, min(0.99, final_p))
    
    # D. 模拟
    sims = np.random.choice([1, 0], size=50000, p=[final_p, 1-final_p])
    real_wr = np.mean(sims)
    
    # E. 结果分析
    ev = (real_wr * poly_odds) - 1
    b = poly_odds - 1
    kelly = (b * real_wr - (1 - real_wr)) / b if b > 0 else 0
    safe_amt = min(max(0, kelly * 0.5), 0.15) * bankroll # 15% 仓位封顶

    res1, res2, res3 = st.columns(3)
    with res1:
        st.metric("模型预估胜率", f"{real_wr:.2%}", delta=f"{(real_wr - base_win_prob):.1%}")
    with res2:
        st.metric("期望值 (EV)", f"{ev:.2%}", delta="🔥 强力建议" if ev > 0.08 else None)
    with res3:
        st.metric("建议下单", f"${safe_amt:.2f}")

    if ev > 0.08:
        st.success(f"⚖️ 精准对齐结论：盘口高度低估了球员缺阵影响，建议介入。")
    elif ev > 0:
        st.info("⚖️ 结论：微弱优势，请谨慎操作。")
    else:
        st.error("❌ 结论：市场赔率已完全覆盖变动，无利可图。")
