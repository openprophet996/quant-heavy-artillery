import streamlit as st
import numpy as np
import pandas as pd

# --- 页面配置 ---
st.set_page_config(page_title="量化重炮 V12.0 - 精准球员版", layout="wide")

# --- 1. 核心球员战力数据库 (2026 最新修正) ---
# 这里解决了你提到的球员交易问题，手动维护最新核心权重
PLAYER_IMPACT = {
    "Luka Doncic": 18.5,    # 超巨级影响 (点名 Luka)
    "Anthony Davis": 14.2,  # 核心防守+进攻
    "Trae Young": 12.8,     # 进攻引擎
    "Jimmy Butler": 11.5,   # 季后赛硬解
    "Nikola Jokic": 19.0,
    "Shai Gilgeous-Alexander": 15.5
}

# 球队与球员的动态关联 (示例，你可以随时修改)
TEAM_ROSTERS = {
    "湖人 (Lakers)": ["Anthony Davis", "Luka Doncic", "Austin Reaves"],
    "小牛 (Mavericks)": ["Kyrie Irving", "Klay Thompson"],
    "热火 (Heat)": ["Bam Adebayo"],
    "太阳 (Suns)": ["Kevin Durant", "Devin Booker"]
}

st.title("🛡️ 量化重炮 V12.0 - 精准球员模拟器")
st.markdown("---")

# --- 2. 核心设置区 ---
with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        target_team = st.selectbox("🎯 目标球队", list(TEAM_ROSTERS.keys()))
    with col2:
        market_odds = st.number_input("💰 Polymarket 实时赔率", value=1.95)
    with col3:
        bankroll = st.number_input("💵 你的本金 ($)", value=2000)

# --- 3. 球员精准减法逻辑 ---
st.subheader("🧬 球员缺阵实时修正")
st.write(f"当前 **{target_team}** 的核心名单已载入。请选择今日缺阵的球员：")

# 获取当前球队的球员列表
current_roster = TEAM_ROSTERS.get(target_team, [])
missing_players = st.multiselect("点击选择缺阵球员 (可多选)", current_roster)

# 计算总减分
total_penalty = 0
for player in missing_players:
    impact = PLAYER_IMPACT.get(player, 5.0) # 如果没在库里，默认扣 5%
    total_penalty += impact
    st.warning(f"⚠️ 检测到 {player} 缺阵：模型胜率精准扣除 {impact}%")

# --- 4. 蒙特卡罗 30,000 次推演 ---
st.divider()
base_p = st.slider("初始基础胜率 (模型基准 %)", 10, 95, 50)

if st.button(f"🔥 执行 {target_team} 深度量化模拟"):
    final_p = (base_p - total_penalty) / 100
    final_p = max(0.01, min(0.99, final_p))
    
    # 模拟
    sims = np.random.choice([1, 0], size=30000, p=[final_p, 1-final_p])
    win_rate = np.mean(sims)
    
    # 计算价值
    b = market_odds - 1
    ev = (win_rate * market_odds) - 1
    kelly_f = (b * win_rate - (1 - win_rate)) / b if b > 0 else 0
    safe_bet = min(max(0, kelly_f * 0.5), 0.10) # 封顶 10%

    res1, res2, res3 = st.columns(3)
    with res1:
        st.metric("精准修正后胜 rate", f"{win_rate:.2%}", delta=f"-{total_penalty}%")
    with res2:
        st.metric("期望值 (EV)", f"{ev:.2%}")
    with res3:
        st.metric("建议下注金额", f"${bankroll * safe_bet:.2f}")

    if ev > 0.05:
        st.success(f"✅ 发现洼地！建议投入 ${bankroll * safe_bet:.2f}")
    else:
        st.error("❌ 胜率不足以对冲风险。")
