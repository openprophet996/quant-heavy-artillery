if source == "API 自动同步":
    if st.button("🔄 强制穿透同步 (Gamma + Data)", use_container_width=True):
        try:
            # 1. 尝试多个 NBA 相关的 Tag 和搜索词，确保不落空
            # Tag 10051 是 NBA，同时也通过 query 搜索防止 Tag 失效
            url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=50&query=NBA"
            resp = requests.get(url, timeout=8).json()
            
            if not resp:
                st.warning("API 返回空列表，当前可能没有正在进行的 NBA 盘口。")
            
            st.session_state.api_cache = []
            
            for m in resp:
                q = m.get('question', '')
                
                # --- 核心修复：多级价格解析 ---
                raw_prices = m.get('outcomePrices')
                prices = []
                
                try:
                    if isinstance(raw_prices, str):
                        prices = json.loads(raw_prices)
                    elif isinstance(raw_prices, list):
                        prices = raw_prices
                    
                    # 如果上述解析失败，尝试从 clobTokenIds 侧面验证（进阶逻辑）
                    if not prices or float(prices[0]) == 0:
                        continue 
                        
                    p_val = float(prices[0])
                    # 赔率计算：1 / 价格
                    # 限制最小价格避免除零错误
                    odd = round(1 / max(p_val, 0.01), 2)
                    
                except (json.JSONDecodeError, ValueError, IndexError):
                    continue # 跳过无法解析价格的盘口

                # --- 智能分类逻辑 ---
                cat = "Moneyline"
                if any(word in q for word in ["Spread", "Point", "+", "-"]): 
                    cat = "Spread"
                elif any(word in q for word in ["Total", "Over", "Under"]): 
                    cat = "Total"
                
                # 存入缓存
                st.session_state.api_cache.append({
                    "q": q, 
                    "odd": odd, 
                    "cat": cat,
                    "prob": p_val
                })
            
            if st.session_state.api_cache:
                st.success(f"成功捕获 {len(st.session_state.api_cache)} 个实时盘口！")
            else:
                st.info("解析完成，但未发现符合条件的 NBA 盘口。")
                
        except Exception as e:
            st.error(f"同步失败，错误代码: {str(e)}")
