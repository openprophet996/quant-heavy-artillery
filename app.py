import streamlit as st
import requests
import json
import re
import numpy as np

# --- [1. 基础配置与数据库] ---
st.set_page_config(page_title="量化重炮 V43.0", layout="wide")

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

# --- [2. 初始化持久化状态] ---
# 解决 NameError 的关键：预先声明所有变量
if "api_cache" not in st.session_state: st.session_state.api_cache = []
if "current_odds" not in st.session_state: st.session_state.current_odds = 1.95
if "current_val" not in st.session_state: st.session_state.current_val = 0.0
if "current_cat" not in st.session_state: st.session_state.current_cat = "Moneyline"

st.title("🏹 量化重炮 V43.0 - 稳定版")

# --- [3. 第一阶段：确立博弈盘口] ---
with st.container(border=True):
    st.subheader("第一阶段：确立博弈盘口")
    
    # 修复变量定义顺序：先定义 source
    source = st.radio("数据源选择", ["API 自动同步", "手动填入"], horizontal=True)
    
    if source == "API 自动同步":
        if st.button("🔄 同步 Polymarket 最新数据", use_container_width=True):
            try:
                # 使用伪装 Headers 穿透 API 限制
                headers = {"User-Agent": "Mozilla/5.0"}
                url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=30&query=NBA"
                resp = requests.get(url, headers=headers, timeout=8).json()
                
                temp_cache = []
                for m in resp:
                    # 价格解析逻辑
                    raw_prices = m.get('outcomePrices')
                    if isinstance(raw_prices, str):
                        prices = json.loads(raw_prices)
                    else:
                        prices = raw_prices
                    
                    if prices and len(prices) > 0:
                        p_val = float(prices[0])
                        if 0.01 < p_val < 0.99:
                            odd = round(1 / p_val, 2)
                            q = m.get('question', '')
                            # 自动分类
                            cat = "Moneyline"
                            if any(x in q for x in ["Spread", "+", "-"]): cat = "Spread"
                            elif "Total" in q: cat = "Total"
                            
                            temp_cache.append({"q": q, "odd": odd, "cat": cat})
                
                st.session_state.api_cache = temp_cache
                st.success(f"同步成功，发现 {len(temp_cache)} 个有效盘口")
            except Exception as e:
                st.error(f"同步失败: {e}")

        # 下拉选择逻辑
        if st.session_state.api_cache:
            selected = st.selectbox(
                "选择具体题目", 
                st.session_state.api_cache, 
                format_func=lambda x: f"[{x['cat']}] {x['q']} (赔率:{x['odd']})"
            )
            st.session_state.current_odds = selected['odd']
            st.session_state.current_cat = selected['cat']
            # 从题目提取参数（如 +5.5）
            nums = re.findall(r'[+-]?\d+\.?\d*', selected['q'])
            st.session_state.current_val = float(nums[-1]) if nums else 0.0
            
    else:
        c1, c2, c3 = st.columns(3)
        st.session_state.current_cat = c1.selectbox("类型", ["Moneyline", "Spread", "Total"])
        st.session_state.current_odds = c2.number_input("实时赔率", value=1.95)
        st.session_state.current_val = c3.number_input("参数 (让分/总分)", value=0.0)

    st.info(f"📍 **已锁定：** {st.session_state.current_cat} | 赔率 **{st.session_state.current_odds}** | 参数 **{st.session_state.current_val}**")

# --- [4. 第二阶段：球员伤病对冲] ---
st.divider()
st.subheader("第二阶段：球员伤病量化")
ch, ca = st.columns(2)
with ch:
    h_team = st.selectbox("🏠 主队", list(NBA_DB.keys()), key="ht")
    h_miss = st.multiselect("缺阵球员:", options=list(NBA_DB[h_team].keys()), key="hm")
    h_impact = sum([NBA_DB[h_team][p] for p in h_miss])
with ca:
    a_team = st.selectbox("🚩 客队", list(NBA_DB.keys()), index=1, key="at")
    a_miss = st.multiselect("缺阵球员:", options=list(NBA_DB[a_team].keys()), key="am")
    a_impact = sum([NBA_DB[a_team][p] for p in a_miss])

# --- [5. 第三阶段：量化推演] ---
st.divider()
bankroll = st.sidebar.number_input("账户总本金 ($)", value=2000)
if st.button("🚀 启动 50,000 次蒙特卡洛模拟", use_container_width=True):
    # 胜率算法
    diff = a_impact - h_impact
    if st.session_state.current_cat == "Spread":
        # 基础胜率 + 伤病差值修正 (每个点约影响 1.5% 胜率)
        base_p = 1 / (1 + 10**(-st.session_state.current_val / 13.5))
        prob = base_p + (diff * 0.015)
    elif st.session_state.current_cat == "Moneyline":
        prob = 0.5 + (diff * 0.02)
    else: # Total
        prob = 0.5 + (h_impact + a_impact) * 0.01

    prob = max(0.01, min(0.99, prob))
    sims = np.random.choice([1, 0], size=50000, p=[prob, 1-prob])
    wr = np.mean(sims)
    
    # 凯利计算
    odd = st.session_state.current_odds
    ev = (wr * odd) - 1
    k = ((odd - 1) * wr - (1 - wr)) / (odd - 1) if odd > 1 else 0
    
    # 结果展示
    st.write(f"### 🎯 推演报告: {h_team} vs {a_team}")
    r1, r2, r3 = st.columns(3)
    r1.metric("预测胜率", f"{wr:.2%}")
    r2.metric("期望回报 (EV)", f"{ev:.2%}")
    r3.metric("建议下单 (半凯利)", f"${max(0, k * 0.5) * bankroll:.2f}")

    if ev > 0.03: st.success("💰 高价值机会，建议介入")
    else: st.error("📉 期望值为负，建议观望")
