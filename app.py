import streamlit as st
import numpy as np

# --- 页面设置 ---
st.set_page_config(page_title="Polymarket 实战终端", layout="wide")

st.title("🛡️ 球员情报量化终端")
st.markdown("---")

# --- 第一部分：实战对阵录入 ---
col_setup1, col_setup2, col_setup3 = st.columns([2, 1, 1])

with col_setup1:
    match_title = st.text_input("1. 输入当前对阵 (例如: 湖人 vs 掘金)", value="湖人 vs 掘金")
with col_setup2:
    live_odds = st.number_input("2. Polymarket 当前赔率", value=1.95, step=0.01)
with col_setup3:
    bankroll = st.number_input("3. 你的总本金 ($)", value=2000, step=100)

st.markdown("---")

# --- 第二部分：核心情报变量 (针对 AD、Trae Young 等) ---
st.subheader("💡 核心球员与环境变量修正")
st.write("根据最新的球员交易、伤病、缺阵信息进行勾选：")

col_info1, col_info2 = st.columns(2)

with col_info1:
    with st.container(border=True):
        st.write("🔴 **负面因素 (降低胜率)**")
        # 具体的球员逻辑
        inj_1 = st.checkbox("核心球星确认缺阵 (如 AD/Trae Young 不打) -15%")
        inj_2 = st.checkbox("二号得分手/主控伤停 -7%")
        travel = st.checkbox("背靠背作战/高原客场体能受限 -5%")

with col_info2:
    with st.container(border=True):
        st.write("🟢 **正面因素 (提高胜率)**")
        buff_1 = st.checkbox("对手核心确认缺阵 +12%")
        buff_2 = st.checkbox("主力伤愈复出/交易新援首秀 +5%")
        home_adv = st.checkbox("主场优势/哨息利好 +3%")

st.markdown("---")

# --- 第三部分：深度模拟运算 ---
st.subheader("🔥 30,000 次蒙特卡罗模拟推演")

# 你的预估
user_base_p = st.slider("你对该盘口的原始信心度 (基础胜率 %)", 10, 90, 55)

# 贝叶斯修正计算
penalty = (15 if inj_1 else 0) + (7 if inj_2 else 0) + (5 if travel else 0)
bonus = (12 if buff_1 else 0) + (5 if buff_2 else 0) + (3 if home_adv else 0)
final_p = (user_base_p - penalty + bonus) / 100
final_p = max(0.01, min(0.99, final_p))

if st.button("开始执行深度量化运算", use_container_width=True):
    # 执行 30k 模拟
    sims = np.random.choice([1, 0], size=30000, p=[final_p, 1-final_p])
    calc_win_rate = np.mean(sims)
    
    # 结果展示
    res_1, res_2, res_3 = st.columns(3)
    
    with res_1:
        st.metric("修正后真实胜率", f"{calc_win_rate:.2%}", delta=f"{bonus-penalty}%")
    
    # 凯利公式计算 (b * p - q) / b
    b = live_odds - 1
    p = calc_win_rate
    q = 1 - p
    kelly_f = (b * p - q) / b if b > 0 else 0
    
    # 使用稳健的 0.5 凯利策略
    suggested_bet = max(0, bankroll * kelly_f * 0.5)
    
    with res_2:
        st.metric("建议投入比例 (半凯利)", f"{kelly_f*0.5:.2%}")
    
    with res_3:
        st.metric("最终建议下注金额", f"${suggested_bet:.2f}")

    if suggested_bet > 0:
        st.success(f"✅ 结论：当前赔率 ({live_odds}) 具备正期望值。建议对【{match_title}】下单 ${suggested_bet:.2f}")
    else:
        st.error(f"❌ 结论：风险修正后胜率不足，当前赔率下无交易价值。")
