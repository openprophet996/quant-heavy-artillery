import streamlit as st
import numpy as np
import pandas as pd

# --- 页面 UI 增强 ---
st.set_page_config(page_title="量化重炮终端 V8.0", layout="wide")
st.title("🛡️ 量化重炮 - 小玩家博弈武器")
st.subheader("集成：球员情报修正 + 3万次模拟 + 凯利风控")

# --- 模块 1：数据采集 (Manual Bridge) ---
with st.expander("📡 第一步：录入 Polymarket 实时水位", expanded=True):
    col_a, col_b = st.columns(2)
    with col_a:
        match_name = st.text_input("赛事名称", "NBA: 湖人 vs 掘金")
        market_price = st.number_input("Polymarket 当前买入价格 (0.01 - 0.99)", value=0.48, step=0.01)
    with col_b:
        # 自动换算成赔率
        odds = round(1 / market_price, 2) if market_price > 0 else 2.0
        st.metric("实时换算赔率", f"{odds}")
        bankroll = st.number_input("你的当前本金 ($)", value=1000)

# --- 模块 2：情报引擎 (Intelligence Core) ---
st.divider()
st.subheader("🧬 第二步：球员情报与贝叶斯修正")
col1, col2 = st.columns(2)

with col1:
    st.write("🔴 **利空情报 (降低胜率)**")
    inj_star = st.checkbox("核心超级球星缺阵 (如 AD / Trae Young) -15%")
    inj_role = st.checkbox("重要主力/防守闸门缺阵 -7%")
    schedule_hit = st.checkbox("赛程劣势 (背靠背 / 高原客场) -4%")

with col2:
    st.write("🟢 **利好情报 (提升胜率)**")
    opp_star_out = st.checkbox("对手核心球星缺阵 +12%")
    new_signing = st.checkbox("交易补强新援首秀 / 主力复出 +5%")
    home_boost = st.checkbox("主场哨利好 / 关键对位优势 +3%")

# --- 模块 3：混合模拟引擎 ---
st.divider()
if st.button("🚀 执行 30,000 次蒙特卡洛深度推演", use_container_width=True):
    # 基础概率推算 (此处可接入更复杂的历史数据)
    base_p = 0.50 # 默认 50/50 均衡开局
    
    # 贝叶斯变量叠加
    adjustment = (12 if opp_star_out else 0) + (5 if new_signing else 0) + (3 if home_boost else 0) \
                 - (15 if inj_star else 0) - (7 if inj_role else 0) - (4 if schedule_hit else 0)
    
    final_p = (base_p * 100 + adjustment) / 100
    final_p = max(0.01, min(0.99, final_p))
    
    # 运行 30,000 次模拟
    sims = np.random.choice([1, 0], size=30000, p=[final_p, 1-final_p])
    calc_wr = np.mean(sims)
    
    # --- 模块 4：价值挖掘与下注建议 ---
    st.subheader("🎯 模拟结果与策略输出")
    res_col1, res_col2, res_col3 = st.columns(3)
    
    # 计算 EV
    ev = (calc_wr * odds) - 1
    
    # 计算凯利公式 (b*p-q)/b
    b = odds - 1
    p = calc_wr
    q = 1 - p
    kelly_f = (b * p - q) / b if b > 0 else 0
    
    # 安全阀门：最高只允许投入 10%
    safe_kelly = min(kelly_f * 0.5, 0.10) if kelly_f > 0 else 0

    with res_col1:
        st.metric("模型预测真实胜率", f"{calc_wr:.2%}", delta=f"{adjustment}%")
    with res_col2:
        st.metric("期望值 (EV)", f"{ev:.2%}", delta="洼地" if ev > 0.05 else "无利")
    with res_col3:
        st.metric("建议下注额", f"${bankroll * safe_kelly:.2f}")

    st.divider()
    if ev > 0.05:
        st.success(f"⚖️ **量化结论**：发现显著价值。建议以本金的 {safe_kelly:.1%} (${bankroll * safe_kelly:.2f}) 介入。")
    else:
        st.warning("⚠️ **量化结论**：当前赔率已被吃满，或利空太重，不具备博弈价值，建议观望。")

st.caption("提示：此工具旨在消除信息差，请严格遵守凯利仓位，切勿梭哈。")
