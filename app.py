import streamlit as st
import requests
import numpy as np

# --- 1. 配置与数据库 ---
st.set_page_config(page_title="量化重炮 V14.0", layout="wide")

# 核心战力值库 (Win Shares / Impact)
PLAYER_DB = {
    "Luka Doncic": 19.5, "Nikola Jokic": 19.8, "Shai Gilgeous-Alexander": 16.5,
    "Giannis Antetokounmpo": 15.8, "Anthony Davis": 14.5, "Jayson Tatum": 14.0,
    "Stephen Curry": 13.5, "Kevin Durant": 13.2, "LeBron James": 12.5,
    "Trae Young": 12.0, "Jimmy Butler": 11.8, "Kyrie Irving": 12.2,
    "Joel Embiid": 17.5, "Victor Wembanyama": 15.0, "Anthony Edwards": 14.8,
    "Jalen Brunson": 14.2, "Damian Lillard": 12.5, "James Harden": 11.0,
    "Kawhi Leonard": 13.5, "Ja Morant": 13.0, "Devin Booker": 13.0
}

# --- 2. Polymarket API 精准对齐引擎 ---
def get_polymarket_by_search(query):
    try:
        # 使用过滤参数搜索特定的比赛
        url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=10&search={query}"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        
        results = []
        for m in data:
            if 'outcomePrices' in m and m['outcomePrices']:
                price = float(m['outcomePrices'][0])
                odds = round(1 / price, 2) if 0 < price < 1 else 2.0
                results.append({"label": f"{m.get('question')} (实时赔率: {odds})", "odds": odds, "title": m.get('question')})
        return results
    except:
        return []

# --- 3. 界面布局 ---
st.title("🛡️ 量化重炮 V14.0 - 球员级精准博弈终端")

# 步骤一：API 赔率对齐
st.subheader("第一步：精准对齐 Polymarket 赔率")
search_query = st.text_input("输入球队名搜索实时盘口 (例如: Lakers 或 Mavericks)", "Lakers")
api_results = get_polymarket_by_search(search_query)

if api_results:
    selected_match = st.selectbox("发现以下实时盘口，请选择：", api_results, format_func=lambda x: x['label'])
    target_odds = selected_match['odds']
    st.success(f"✅ 已成功连接 API，锁定赔率: {target_odds}")
else:
    target_odds = st.number_input("未找到盘口？请手动输入 Polymarket 实时赔率", value=1.95)
    st.warning("目前使用手动赔率模式")

st.divider()

# 步骤二：球员对冲模拟
st.subheader("第二步：点名式球员缺阵修正 (双阵营)")
col_l, col_r = st.columns(2)

with col_l:
    st.markdown("#### 🏠 主队损失")
    home_missing = st.multiselect("搜索主队缺阵球员:", options=list(PLAYER_DB.keys()), key="h_m")
    home_penalty = sum([PLAYER_DB.get(p, 5.0) for p in home_missing])

with col_r:
    st.markdown("#### 🚩 客队损失")
    away_missing = st.multiselect("搜索客队缺阵球员:", options=list(PLAYER_DB.keys()), key="a_m")
    away_penalty = sum([PLAYER_DB.get(p, 5.0) for p in away_missing])

# 步骤三：量化决策
st.divider()
bankroll = st.sidebar.number_input("💰 你的总本金 ($)", value=2000)
base_p = st.sidebar.slider("初始基础胜率基准 (%)", 10, 90, 50)

if st.button("🔥 执行 30,000 次精准对冲模拟", use_container_width=True):
    # 核心公式
    final_p = (base_p - home_penalty + away_penalty) / 100
    final_p = max(0.01, min(0.99, final_p))
    
    # 蒙特卡罗模拟
    sims = np.random.choice([1, 0], size=30000, p=[final_p, 1-final_p])
    win_rate = np.mean(sims)
    
    # 期望值与风控
    ev = (win_rate * target_odds) - 1
    b = target_odds - 1
    kelly = (b * win_rate - (1 - win_rate)) / b if b > 0 else 0
    safe_bet = min(max(0, kelly * 0.5), 0.12) # 半凯利，12%封顶

    # 结果展示
    r1, r2, r3 = st.columns(3)
    with r1:
        st.metric("对冲后真实胜率", f"{win_rate:.2%}", delta=f"{away_penalty - home_penalty:.1f}%")
    with r2:
        st.metric("期望值 (EV)", f"{ev:.2%}")
    with r3:
        st.metric("建议下单金额", f"${bankroll * safe_bet:.2f}")

    if ev > 0.05:
        st.success(f"✅ 发现价值！赔率 {target_odds} 尚未反应球员变动，建议介入。")
    else:
        st.error("❌ 赔率已封死或风险过大，无交易价值。")
