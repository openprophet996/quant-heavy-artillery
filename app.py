import streamlit as st
import numpy as np

# --- 页面配置 ---
st.set_page_config(page_title="量化重炮 V11.0", layout="wide")

st.title("🛡️ 量化重炮 V11.0 - 实时情报对冲终端")
st.caption("不再使用预设名单，完全基于你掌握的最新交易与伤病数据进行即时建模。")

# --- 第一部分：赛事与赔率 (Polymarket 同步) ---
with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        team_target = st.text_input("🎯 目标球队 (你准备下注的一方)", "例如：太阳")
    with col2:
        market_odds = st.number_input("💰 实时赔率 (Polymarket)", value=1.95, step=0.01)
    with col3:
        bankroll = st.number_input("💵 你的总本金 ($)", value=2000)

st.markdown("---")

# --- 第二部分：自定义球员影响 (这里解决交易与伤病的新数据问题) ---
st.subheader("🧬 实时情报修正 (基于最新新闻)")
st.write("根据你看到的最新球员变动（如 Trae Young 交易、AD 伤停等），手动调整影响权重：")

col_info1, col_info2 = st.columns(2)

with col_info1:
    st.markdown("#### 🔴 负面冲击 (针对目标球队)")
    # 这里让你根据最新数据自己勾选，不设死名字
    neg_1 = st.checkbox("核心球星确阵/刚被交易走 (S级战力流失) -15%")
    neg_2 = st.checkbox("主要轮换受伤/防守体系崩塌 -7%")
    neg_custom = st.slider("自定义额外负面影响 (%)", 0, 30, 0)

with col_info2:
    st.markdown("#### 🟢 正面补偿 (针对目标球队)")
    pos_1 = st.checkbox("对手核心确认缺阵 (对方战力真空) +12%")
    pos_2 = st.checkbox("新援首秀/主力伤愈复出 (如新交易球员上场) +6%")
    pos_custom = st.slider("自定义额外正面补偿 (%)", 0, 30, 0)

# --- 第三部分：深度运算与博弈决策 ---
st.divider()
st.subheader("🔥 30,000 次蒙特卡洛深度模拟")

# 你的初始直觉/模型基础
base_p = st.slider("基础信心胜率 (基于历史战绩判断 %)", 10, 90, 50)

if st.button(f"🚀 开始对 【{team_target}】 进行量化推演", use_container_width=True):
    # 动态概率计算逻辑
    penalty = (15 if neg_1 else 0) + (7 if neg_2 else 0) + neg_custom
    bonus = (12 if pos_1 else 0) + (6 if pos_2 else 0) + pos_custom
    
    # 贝叶斯修正：最终概率
    final_p = (base_p - penalty + bonus) / 100
    final_p = max(0.01, min(0.99, final_p))
    
    # 30,000 次模拟
    sims = np.random.choice([1, 0], size=30000, p=[final_p, 1-final_p])
    win_rate = np.mean(sims)
    
    # 期望值与凯利公式
    ev = (win_rate * market_odds) - 1
    b = market_odds - 1
    kelly_f = (b * win_rate - (1 - win_rate)) / b if b > 0 else 0
    # 稳健策略：半凯利且不超 10% 仓位
    safe_bet = min(max(0, kelly_f * 0.5), 0.10)

    # 结果看板
    res1, res2, res3 = st.columns(3)
    with res1:
        st.metric("修正后真实胜率", f"{win_rate:.2%}", delta=f"{bonus-penalty}%")
    with res2:
        st.metric("期望值 (EV)", f"{ev:.2%}", delta="洼地机会" if ev > 0.05 else "风险偏高")
    with res3:
        st.metric("建议下单金额", f"${bankroll * safe_bet:.2f}")

    if ev > 0.05:
        st.success(f"⚖️ 结论：检测到信息差。建议在 Polymarket 以 {market_odds} 赔率买入 ${bankroll * safe_bet:.2f}")
    else:
        st.error("❌ 结论：利空过载或赔率太低，无博弈价值。")

st.info("💡 实战技巧：当你看到 Twitter 突发球员交易时，立即在左侧输入球队名，勾选'核心缺阵'并运行模拟，抢在 Polymarket 赔率变动前下单。")
