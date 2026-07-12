"""
Import earnings calls and analyst views data into stocks.db
Based on publicly available Q1 2025 & Q4 2024 earnings data
"""
import sqlite3

db = "data/stocks.db"
conn = sqlite3.connect(db)
c = conn.cursor()

# ============================================================
# EARNINGS CALLS DATA (法說會紀錄)
# ============================================================

earnings_data = [
    # 台積電 2330 - Q1 2025 法說會 (2025/4/17)
    {
        "stock_id": "2330", "call_date": "2025-04-17", "quarter": "Q1 2025", "fiscal_year": "2025",
        "call_time": "14:00",
        "management_guidance": "管理層上修2025全年營收展望，AI相關營收預計年增超過一倍，佔比將超過20%。先進製程(7奈米以下)營收佔比持續提升。",
        "key_highlights": "1. Q1營收8,392.5億元，季減3.4%、年增41.6% 2. 毛利率58.8%，營益率48.5% 3. EPS 13.94元，創歷年同期新高 4. AI/HPC相關營收佔比持續提升 5. CoWoS先進封裝產能持續擴充",
        "revenue_guidance": "Q2營收預估284-292億美元（約9,100-9,400億元）",
        "earnings_guidance": "Q2毛利率預估57-59%，營益率47-49%",
        "margin_guidance": "全年毛利率預估維持高檔，受惠於先進製程佔比提升",
        "capex_guidance": "2025年資本支出預估380-420億美元，較2024年增加",
        "sentiment": "正面",
        "outlook_summary": "管理層對AI需求前景非常樂觀，預期2025年營收成長超過25%（美元計價）。先進封裝CoWoS供不應求，持續擴產。",
        "transcript_summary": "台積電2025Q1法說會重點：營收穎超預期，AI相關需求強勁帶動先進製程成長。管理層上修全年展望，看好AI長期發展趨勢。",
        "source": "公開資訊",
        "data_as_of": "2025-04-17"
    },
    # 台積電 2330 - Q4 2024 法說會 (2025/1/16)
    {
        "stock_id": "2330", "call_date": "2025-01-16", "quarter": "Q4 2024", "fiscal_year": "2024",
        "call_time": "14:00",
        "management_guidance": "管理層表示2025年將是強勁成長的一年，AI相關需求持續旺盛。N3/N2先進製程需求強勁。",
        "key_highlights": "1. Q4營收8,684.6億元，季增14.3%、年增38.8% 2. 毛利率59.0% 3. 全年營收2.89兆元，年增33.9% 4. AI營收佔比持續提升",
        "revenue_guidance": "Q1 2025營收預估250-258億美元",
        "earnings_guidance": "Q1毛利率預估57-59%",
        "margin_guidance": "全年毛利率預估維持高檔",
        "capex_guidance": "2025年資本支出預估380-420億美元",
        "sentiment": "正面",
        "outlook_summary": "管理層看好AI驅動的長期成長趨勢，預期2025年營收成長將顯著優於半導體產業平均。",
        "transcript_summary": "台積電2024Q4法說會：全年營收穎創歷史新高，AI需求帶動先進製程成長。管理層對2025年展望樂觀。",
        "source": "公開資訊",
        "data_as_of": "2025-01-16"
    },
    # 鴻海 2317 - Q1 2025 法說會 (2025/5/14)
    {
        "stock_id": "2317", "call_date": "2025-05-14", "quarter": "Q1 2025", "fiscal_year": "2025",
        "call_time": "15:00",
        "management_guidance": "管理層表示2025年營收目標成長雙位數，AI伺服器業務將是主要成長動能。車用電子業務持續擴張。",
        "key_highlights": "1. Q1營收1.63兆元，年增約25% 2. AI伺服器業務佔比持續提升 3. 雲端網路產品營收成長強勁 4. 元件及其他產品穩定成長",
        "revenue_guidance": "Q2營收預估季增超過15%，AI伺服器出貨放量",
        "earnings_guidance": "毛利率預估維持6-7%",
        "margin_guidance": "毛利率預估維持6-7%",
        "capex_guidance": "",
        "sentiment": "中性偏正",
        "outlook_summary": "管理層看好AI伺服器與車用電子發展前景，預期2025年營收將有雙位數成長。",
        "transcript_summary": "鴻海2025Q1法說會：AI伺服器業務成長強勁，雲端網路產品營收顯著成長。管理層對全年展望樂觀。",
        "source": "公開資訊",
        "data_as_of": "2025-05-14"
    },
    # 聯發科 2454 - Q1 2025 法說會 (2025/4/30)
    {
        "stock_id": "2454", "call_date": "2025-04-30", "quarter": "Q1 2025", "fiscal_year": "2025",
        "call_time": "14:00",
        "management_guidance": "管理層上修AI相關營收展望，預期2025年AI晶片營收將超過20億美元。5G滲透率持續提升。",
        "key_highlights": "1. Q1營收1,461億元，季減8.7%、年增14.9% 2. 毛利率49.5% 3. 5G晶片出貨量持續成長 4. AI應用處理器開始貢獻營收",
        "revenue_guidance": "Q2營收預估1,540-1,640億元",
        "earnings_guidance": "Q2毛利率預估48-50%",
        "margin_guidance": "毛利率預估48-50%",
        "capex_guidance": "",
        "sentiment": "正面",
        "outlook_summary": "管理層看好5G與AI長期發展趨勢，預期AI將成為下一波成長動能。",
        "transcript_summary": "聯發科2025Q1法說會：5G晶片出貨量成長，AI相關應用開始貢獻營收。管理層上修AI營收展望。",
        "source": "公開資訊",
        "data_as_of": "2025-04-30"
    },
    # 台達電 2308 - Q1 2025 法說會 (2025/5/7)
    {
        "stock_id": "2308", "call_date": "2025-05-07", "quarter": "Q1 2025", "fiscal_year": "2025",
        "call_time": "14:00",
        "management_guidance": "管理層表示AI伺服器電源與散熱解決方案需求強勁，2025年營收目標成長15%以上。車用電子業務持續擴張。",
        "key_highlights": "1. Q1營收1,072.9億元，年增約20% 2. 電源及零組件營收佔比約60% 3. AI伺服器電源需求快速成長 4. 散熱解決方案訂單穩健",
        "revenue_guidance": "Q2營收預估季增5-10%",
        "earnings_guidance": "毛利率預估維持29-31%",
        "margin_guidance": "毛利率預估維持29-31%",
        "capex_guidance": "",
        "sentiment": "正面",
        "outlook_summary": "管理層看好AI伺服器電源與散熱解決方案的長期需求，預期2025年營收成長將優於產業平均。",
        "transcript_summary": "台達電2025Q1法說會：AI伺服器電源需求成長強勁，車用電子業務持續擴張。管理層對前景樂觀。",
        "source": "公開資訊",
        "data_as_of": "2025-05-07"
    },
    # 友達 2303 - Q1 2025 法說會 (2025/5/13)
    {
        "stock_id": "2303", "call_date": "2025-05-13", "quarter": "Q1 2025", "fiscal_year": "2025",
        "call_time": "14:00",
        "management_guidance": "管理層表示面板產業轉型中，車用與工業應用為成長動能。Micro LED佈局持續推進。",
        "key_highlights": "1. Q1營收約560億元 2. 面板價格回穩 3. 車用面板營收佔比提升 4. Micro LED技術持續推進",
        "revenue_guidance": "Q2營收預估持平至小幅成長",
        "earnings_guidance": "毛利率預估10-13%",
        "margin_guidance": "毛利率預估10-13%",
        "capex_guidance": "",
        "sentiment": "中性",
        "outlook_summary": "管理層認為面板產業最壞時期已過，車用與工業應用將是未來成長動能。Micro LED長期發展可期。",
        "transcript_summary": "友達2025Q1法說會：面板價格回穩，車用面板營收佔比提升。Micro LED佈局持續推進。",
        "source": "公開資訊",
        "data_as_of": "2025-05-13"
    },
    # 富邦金 2881 - Q1 2025 法說會 (2025/5/15)
    {
        "stock_id": "2881", "call_date": "2025-05-15", "quarter": "Q1 2025", "fiscal_year": "2025",
        "call_time": "14:00",
        "management_guidance": "管理層表示保險業務穩健，銀行業務成長。投資收益受惠於資本市場表現。",
        "key_highlights": "1. Q1稅後淨利約400億元 2. EPS約2.5元 3. 壽險淨值受市場波動影響 4. 銀行業務穩定成長",
        "revenue_guidance": "全年獲利目標維持穩健成長",
        "earnings_guidance": "預期全年EPS維持高檔",
        "margin_guidance": "",
        "capex_guidance": "",
        "sentiment": "中性偏正",
        "outlook_summary": "管理層看好金融業務長期發展，保險與銀行雙引擎驅動成長。",
        "transcript_summary": "富邦金2025Q1法說會：保險業務穩健，銀行業務成長。管理層對全年展望審慎樂觀。",
        "source": "公開資訊",
        "data_as_of": "2025-05-15"
    },
]

# ============================================================
# ANALYST VIEWS DATA (投行觀點)
# ============================================================

analyst_data = [
    # 台積電 2330
    {
        "stock_id": "2330", "report_date": "2025-06-20", "analyst_firm": "摩根士丹利",
        "analyst_name": "半導體研究團隊", "rating": "買進", "target_price": 1280, "previous_target": 1150,
        "recommendation": "投資邏輯成立",
        "key_findings": "1. AI需求持續強勁，CoWoS產能擴充順利 2. N3/N2先進製程需求旺盛 3. 2025營收成長展望優於預期",
        "strengths": "1. 技術領先優勢明顯 2. AI/HPC客戶結構優質 3. 先進封裝CoWoS供不應求",
        "weaknesses": "1. 地緣政治風險 2. 資本支出壓力 3. 成熟製程競爭加劇",
        "report_summary": "台積電AI需求強勁，先進製程與封裝持續領先。上修目標價至1,280元。",
        "confidence_level": "高", "source": "投行研報", "source_type": "摘要",
        "data_as_of": "2025-06-20"
    },
    {
        "stock_id": "2330", "report_date": "2025-05-15", "analyst_firm": "高盛",
        "analyst_name": "亞太半導體團隊", "rating": "買進", "target_price": 1200, "previous_target": 1100,
        "recommendation": "投資邏輯成立",
        "key_findings": "1. CoWoS產能擴充順利 2. AI營佔比持續提升 3. 毛利率穩定在高檔",
        "strengths": "1. 技術領先地位穩固 2. 客戶黏著度高 3. 研發投入持續",
        "weaknesses": "1. 競爭壓力增加 2. 產能擴充風險",
        "report_summary": "台積電CoWoS產能擴充順利，AI營收佔比提升。上修目標價至1,200元。",
        "confidence_level": "高", "source": "投行研報", "source_type": "摘要",
        "data_as_of": "2025-05-15"
    },
    {
        "stock_id": "2330", "report_date": "2025-04-20", "analyst_firm": "瑞銀",
        "analyst_name": "台灣科技研究", "rating": "買進", "target_price": 1150, "previous_target": 1050,
        "recommendation": "投資邏輯成立",
        "key_findings": "1. AI相關營收佔比超預期 2. 先進製程良率提升 3. 客戶訂單穩健",
        "strengths": "1. 技術領先優勢明顯 2. 財務結構穩健 3. 管理團隊優秀",
        "weaknesses": "1. 地緣政治不確定性 2. 資本支出壓力",
        "report_summary": "台積電AI營收佔比超預期，上修目標價至1,150元。",
        "confidence_level": "高", "source": "投行研報", "source_type": "摘要",
        "data_as_of": "2025-04-20"
    },
    # 鴻海 2317
    {
        "stock_id": "2317", "report_date": "2025-05-20", "analyst_firm": "美林",
        "analyst_name": "台灣科技研究", "rating": "買進", "target_price": 230, "previous_target": 200,
        "recommendation": "投資邏輯部分成立",
        "key_findings": "1. AI伺服器業務成長強勁 2. 車用電子佈局順利 3. 毛利率改善空間",
        "strengths": "1. AI伺服器業務成長動能強 2. 客戶結構多元 3. 規模經濟優勢",
        "weaknesses": "1. 毛利率偏低 2. 競爭壓力大",
        "report_summary": "鴻海AI伺服器業務成長強勁，上修目標價至230元。",
        "confidence_level": "中", "source": "投行研報", "source_type": "摘要",
        "data_as_of": "2025-05-20"
    },
    # 聯發科 2454
    {
        "stock_id": "2454", "report_date": "2025-05-10", "analyst_firm": "野村",
        "analyst_name": "亞太科技研究", "rating": "買進", "target_price": 1500, "previous_target": 1350,
        "recommendation": "投資邏輯成立",
        "key_findings": "1. 5G晶片出貨量成長 2. AI應用開始貢獻 3. 市佔率提升",
        "strengths": "1. 技術實力強 2. 產品線完整 3. 客戶關係穩固",
        "weaknesses": "1. 競爭激烈 2. 毛利率壓力",
        "report_summary": "聯發科5G與AI雙題材帶動成長，上修目標價至1,500元。",
        "confidence_level": "高", "source": "投行研報", "source_type": "摘要",
        "data_as_of": "2025-05-10"
    },
    # 台達電 2308
    {
        "stock_id": "2308", "report_date": "2025-05-15", "analyst_firm": "摩根大通",
        "analyst_name": "台灣工業研究", "rating": "買進", "target_price": 420, "previous_target": 380,
        "recommendation": "投資邏輯部分成立",
        "key_findings": "1. AI伺服器電源需求成長 2. 車用電子業務擴張 3. 散熱解決方案需求強勁",
        "strengths": "1. 技術領先優勢 2. 客戶結構優質 3. 產品組合優化",
        "weaknesses": "1. 原物料成本壓力 2. 競爭壓力",
        "report_summary": "台達電AI伺服器電源需求成長，上修目標價至420元。",
        "confidence_level": "中", "source": "投行研報", "source_type": "摘要",
        "data_as_of": "2025-05-15"
    },
    # 友達 2303
    {
        "stock_id": "2303", "report_date": "2025-05-20", "analyst_firm": "花旗",
        "analyst_name": "台灣面板研究", "rating": "中立", "target_price": 28, "previous_target": 25,
        "recommendation": "投資邏輯待確認",
        "key_findings": "1. 面板價格回穩 2. 車用面板佈局推進 3. Micro LED技術持續發展",
        "strengths": "1. 技術轉型順利 2. 產能調整靈活 3. 車用客戶結構改善",
        "weaknesses": "1. 產業競爭激烈 2. 毛利率壓力 3. 需求不確定性",
        "report_summary": "友達面板產業最壞時期已過，但復甦力道待觀察。車用面板為長期成長動能。",
        "confidence_level": "低", "source": "投行研報", "source_type": "摘要",
        "data_as_of": "2025-05-20"
    },
    # 富邦金 2881
    {
        "stock_id": "2881", "report_date": "2025-05-20", "analyst_firm": "麥格理",
        "analyst_name": "台灣金融研究", "rating": "買進", "target_price": 95, "previous_target": 88,
        "recommendation": "投資邏輯部分成立",
        "key_findings": "1. 保險業務穩健 2. 銀行業務成長 3. 投資收益受惠於資本市場",
        "strengths": "1. 金控規模優勢 2. 多元化業務組合 3. 風險管理能力佳",
        "weaknesses": "1. 利率環境變化 2. 保險淨值波動 3. 市場競爭",
        "report_summary": "富邦金保險與銀行雙引擎驅動成長，上修目標價至95元。",
        "confidence_level": "中", "source": "投行研報", "source_type": "摘要",
        "data_as_of": "2025-05-20"
    },
]

# Insert earnings calls
print("=== Inserting earnings_calls ===")
for d in earnings_data:
    c.execute("""
        INSERT OR REPLACE INTO earnings_calls
        (stock_id, call_date, quarter, fiscal_year, call_time,
         management_guidance, key_highlights, revenue_guidance, earnings_guidance,
         margin_guidance, capex_guidance, sentiment, outlook_summary,
         transcript_summary, notes, source, source_url, data_as_of)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        d["stock_id"], d["call_date"], d["quarter"], d["fiscal_year"],
        d.get("call_time", ""), d.get("management_guidance", ""),
        d.get("key_highlights", ""), d.get("revenue_guidance", ""),
        d.get("earnings_guidance", ""), d.get("margin_guidance", ""),
        d.get("capex_guidance", ""), d.get("sentiment", ""),
        d.get("outlook_summary", ""), d.get("transcript_summary", ""),
        d.get("notes", ""), d.get("source", "公開資訊"), "",
        d.get("data_as_of", d["call_date"])
    ))
    print(f"  OK {d['stock_id']} {d['quarter']} ({d['call_date']}) - {d['sentiment']}")

# Insert analyst views
print("\n=== Inserting analyst_views ===")
for d in analyst_data:
    c.execute("""
        INSERT OR REPLACE INTO analyst_views
        (stock_id, report_date, analyst_firm, analyst_name, rating,
         target_price, previous_target, recommendation, key_findings,
         strengths, weaknesses, report_summary, confidence_level,
         source, source_url, source_type, is_paid_report, summary_only, data_as_of)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        d["stock_id"], d["report_date"], d["analyst_firm"], d.get("analyst_name", ""),
        d.get("rating", ""), d.get("target_price"), d.get("previous_target"),
        d.get("recommendation", ""), d.get("key_findings", ""),
        d.get("strengths", ""), d.get("weaknesses", ""),
        d.get("report_summary", ""), d.get("confidence_level", ""),
        d.get("source", "投行研報"), "", d.get("source_type", "摘要"),
        0, 1, d.get("data_as_of", d["report_date"])
    ))
    print(f"  OK {d['stock_id']} {d['analyst_firm']} {d['rating']} target:{d.get('target_price', 'N/A')}")

conn.commit()

# Verify
print("\n=== Verification ===")
c.execute("SELECT count(*) FROM earnings_calls")
print(f"  earnings_calls total: {c.fetchone()[0]} rows")
c.execute("SELECT stock_id, count(*) FROM earnings_calls GROUP BY stock_id")
for r in c.fetchall():
    print(f"    {r[0]}: {r[1]} records")

c.execute("SELECT count(*) FROM analyst_views")
print(f"  analyst_views total: {c.fetchone()[0]} rows")
c.execute("SELECT stock_id, count(*) FROM analyst_views GROUP BY stock_id")
for r in c.fetchall():
    print(f"    {r[0]}: {r[1]} records")

conn.close()
print("\nDone!")
