import streamlit as st
import requests
import numpy as np
import json
import re
import pandas as pd

# --- 配置与核心数据库 ---
st.set_page_config(page_title="量化重炮 V43.0 PRO", layout="wide")

# 球员价值库 (基于 PER, Win Shares 及市场赔率波动加权)
NBA_DB = {
    "Rockets (火箭)": {"Kevin Durant": 9.2, "Alperen Sengun": 6.8, "Jalen Green": 5.2, "Fred VanVleet": 5.0},
    "Lakers (湖人)": {"Luka Doncic": 10.5, "Anthony Davis": 8.8, "Austin Reaves": 4.5, "Rui Hachimura": 3.8},
    "76ers (76人)": {"Joel Embiid": 9.8, "Tyrese Maxey": 6.5, "Paul George": 6.0, "Kelly Oubre Jr.": 3.5},
    "Celtics (凯尔特人)": {"Jayson Tatum": 8.5, "Jaylen Brown": 7.8, "Kristaps Porzingis": 6.2},
    "Spurs (马刺)": {"Victor Wembanyama": 9.5, "Trae Young": 7.2, "Devin Vassell": 5.0},
    "Warriors (勇士)": {"Stephen Curry": 8.8, "Jimmy Butler": 7.5, "Draymond Green": 4.2},
    "Suns (太阳)": {"Devin Booker": 7.8, "Bradley Beal": 5.5, "Tyus Jones": 4.2},
    "Knicks (尼克斯)": {"Jalen Brunson": 8.2, "Karl-Anthony Towns": 7.5, "OG Anunoby": 5.5},
    "Hawks (老鹰)": {"Jalen Johnson": 5.8, "Bogdan Bogdanovic": 4.5, "Clint Capela": 4.2},
}

# --- 初始化 ---
if "api_cache" not in st.session_state: st.session_state.api_cache = []

# --- 辅助函数 ---
def calculate_prob(base_val, h_imp, a_imp, category):
    """基于 Logistic 函数的胜率推算"""
    diff = a_imp - h_imp
    if category == "Spread":
        # 基础概率由让分盘转换，diff 对让分进行偏移
        p_base = 1 / (1 + 10**(-base_val / 13.5))
        return p_base + (diff * 0.015) 
    elif category == "Moneyline":
        # 默认 50/50 基础上叠加伤病影响
        return 0.5 + (diff * 0.02)
    else: # Total
        return 0.5 + (h_imp + a_imp) * 0.01

# --- UI 侧边栏：风险管理 ---
st.sidebar.header("🛡️ 风险控制中心")
bankroll = st.sidebar.number_input("当前账户总额 ($)", value=2000, step=100)
kelly_fraction = st.sidebar.slider("凯利系数 (1.0=全凯利, 0.5=半凯利)", 0.1, 1.0, 0.5)
min_ev = st.sidebar.slider("最低介入 EV (%)", 0.0, 10.0, 3.0) / 100

# --- 主页面 ---
st.title("🏹 量化重炮 V43.0 - 系统博弈专家")

# 第一阶段：盘口同步
with st.expander("第一阶段：确立博弈盘口", expanded=True):
    col_a, col_b = st.columns([1, 2])
    with col_a:
        source = st.radio("数据源", ["API 自动同步", "手动录入"], horizontal=True)
    
    with col_b:
        if source == "API 自动同步":
            if st.button("🔄 同步最新 Polymarket 数据"):
                try:
                    url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=50&tag_id=10051"
                    resp = requests.get(url, timeout=5).json()
                    st.session_state.api_cache = []
                    for m in resp:
                        prices = json.loads(m['outcomePrices']) if isinstance(m['outcomePrices'], str) else m.get('outcomePrices')
                        if prices:
                            st.session_state.api_cache.append({
                                "q": m.get('question', 'Unknown'),
                                "odd": round(1/float(prices[0]), 2),
                                "cat": "Spread" if "Spread" in m['question'] else "Moneyline"
                            })
                    st.success("同步成功！")
                except: st.error("网络连接超时")
            
            if st.session_state.api_cache:
                selected = st.selectbox("选择市场题目", st.session_state.api_cache, format_func=lambda x: x['q'])
                target_odd = selected['odd']
                target_cat = selected['cat']
                # 提取数字
                nums = re.findall(r'[+-]?\d+\.?\d*', selected['q'])
                target_val = float(nums[-1]) if nums else 0.0
            else:
                st.info("请先点击同步按钮")
                target_odd, target_cat, target_val = 1.95, "Moneyline", 0.0
        else:
            c1, c2, c3 = st.columns(3)
            target_cat = c1.selectbox("类型", ["Moneyline", "Spread", "Total"])
            target_odd = c2.number_input("实时赔率", value=1.95)
            target_val = c3.number_input("盘口参数", value=0.0)

# 第二阶段：伤病对冲
st.subheader("第二阶段：球员伤病量化对冲")
with st.container(border=True):
    h_col, a_col = st.columns(2)
    with h_col:
        ht = st.selectbox("🏠 主队 (Home)", list(NBA_DB.keys()))
        hm = st.multiselect("缺阵名单:", NBA_DB[ht].keys())
        h_total_impact = sum(NBA_DB[ht][p] for p in hm)
        st.caption(f"主队实力受损指数: {h_total_impact:.1f}")
    with a_col:
        at = st.selectbox("🚩 客队 (Away)", list(NBA_DB.keys()), index=1)
        am = st.multiselect("缺阵名单 :", NBA_DB[at].keys())
        a_total_impact = sum(NBA_DB[at][p] for p in am)
        st.caption(f"客队实力受损指数: {a_total_impact:.1f}")

# 第三阶段：模型模拟
if st.button("🚀 启动量化推演", use_container_width=True):
    # 模拟计算
    win_prob = calculate_prob(target_val, h_total_impact, a_total_impact, target_cat)
    win_prob = max(0.01, min(0.99, win_prob))
    
    # 50000 次模拟
    sim_results = np.random.choice([1, 0], size=50000, p=[win_prob, 1-win_prob])
    real_win_rate = np.mean(sim_results)
    ev = (real_win_rate * target_odd) - 1
    
    # 凯利公式计算: f = (bp - q) / b
    b = target_odd - 1
    kelly_f = (b * real_win_rate - (1 - real_win_rate)) / b if b > 0 else 0
    suggested_bet = max(0, kelly_f * kelly_fraction) * bankroll

    # 结果展示
    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric("模型预测胜率", f"{real_win_rate:.2%}")
    res2.metric("期望回报 (EV)", f"{ev:.2%}", delta=f"{(ev-min_ev):.1%} vs 阈值")
    res3.metric("建议投注金额", f"${suggested_bet:.2f}")

    if ev > min_ev:
        st.balloons()
        st.success(f"🔥 **高价值发现！** 建议在 {target_odd} 赔率下介入。")
    else:
        st.warning("⚠️ **博弈价值不足**：当前胜率无法覆盖赔率抽水，建议放弃。")
    
    # 图表展示
    st.subheader("📊 模拟分布")
    chart_data = pd.DataFrame({"Outcome": ["Win", "Loss"], "Probability": [real_win_rate, 1-real_win_rate]})
    st.bar_chart(chart_data.set_index("Outcome"))
