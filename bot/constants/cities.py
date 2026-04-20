"""城市 IATA 代碼、名稱對照、國旗 emoji、台灣機場"""

# 城市 IATA 代碼對照表
CITY_CODES = {
    # 日本
    "東京": "TYO", "tokyo": "TYO",
    "大阪": "OSA", "osaka": "OSA", "關西": "KIX",
    "名古屋": "NGO", "愛知": "NGO",
    "福岡": "FUK", "九州": "FUK",
    "札幌": "CTS", "北海道": "CTS", "hokkaido": "CTS",
    "沖繩": "OKA", "那霸": "OKA", "okinawa": "OKA",
    "京都": "KIX",
    "仙台": "SDJ", "東北": "SDJ",
    "廣島": "HIJ",
    "高松": "TAK", "四國": "TAK",
    "長崎": "NGS", "鹿兒島": "KOJ",
    "金澤": "KMQ", "北陸": "KMQ",
    # 韓國
    "首爾": "SEL", "seoul": "SEL", "韓國": "SEL",
    "釜山": "PUS",
    "濟州": "CJU", "濟州島": "CJU",
    "大邱": "TAE", "光州": "KWJ", "大田": "CJJ",
    # 東南亞
    "曼谷": "BKK", "bangkok": "BKK", "泰國": "BKK",
    "清邁": "CNX", "清萊": "CEI",
    "普吉": "HKT", "普吉島": "HKT", "布吉": "HKT",
    "蘇梅島": "USM", "蘇美島": "USM",
    "新加坡": "SIN", "singapore": "SIN",
    "吉隆坡": "KUL", "馬來西亞": "KUL",
    "胡志明": "SGN", "胡志明市": "SGN", "越南": "SGN",
    "河內": "HAN",
    "岘港": "DAD", "峴港": "DAD",
    "峇里島": "DPS", "巴里島": "DPS", "峇里": "DPS", "bali": "DPS", "印尼": "DPS",
    "馬尼拉": "MNL", "菲律賓": "MNL",
    "宿霧": "CEB",
    "雅加達": "JKT",
    "科隆": "USU", "巴拉望": "USU",
    "緬甸": "RGN",
    # 港澳中
    "香港": "HKG", "hong kong": "HKG",
    "澳門": "MFM",
    "上海": "SHA",
    "北京": "BJS",
    "廣州": "CAN",
    "深圳": "SZX",
    "成都": "CTU",
    "昆明": "KMG",
    "西安": "XIY",
    "三亞": "SYX",
    # 歐洲
    "倫敦": "LON", "london": "LON", "英國": "LON",
    "巴黎": "PAR", "paris": "PAR", "法國": "PAR",
    "羅馬": "ROM", "義大利": "ROM",
    "米蘭": "MIL",
    "佛羅倫斯": "FLR", "威尼斯": "VCE",
    "巴塞隆納": "BCN", "西班牙": "MAD", "馬德里": "MAD",
    "阿姆斯特丹": "AMS", "荷蘭": "AMS",
    "法蘭克福": "FRA", "德國": "FRA", "慕尼黑": "MUC",
    "維也納": "VIE", "奧地利": "VIE",
    "布拉格": "PRG", "捷克": "PRG",
    "蘇黎世": "ZRH", "瑞士": "ZRH", "日內瓦": "GVA",
    "伊斯坦堡": "IST", "土耳其": "IST",
    "雅典": "ATH", "希臘": "ATH",
    "赫爾辛基": "HEL", "芬蘭": "HEL",
    "哥本哈根": "CPH", "丹麥": "CPH",
    "斯德哥爾摩": "STO", "瑞典": "STO",
    "奧斯陸": "OSL", "挪威": "OSL",
    "雷克雅維克": "REK", "冰島": "REK", "極光": "REK",
    "里斯本": "LIS", "葡萄牙": "LIS",
    "布達佩斯": "BUD", "匈牙利": "BUD",
    "華沙": "WAW", "波蘭": "WAW",
    "克羅埃西亞": "ZAG", "杜布羅夫尼克": "DBV",
    # 美洲
    "紐約": "NYC", "new york": "NYC", "美國": "LAX",
    "洛杉磯": "LAX", "la": "LAX",
    "舊金山": "SFO",
    "西雅圖": "SEA",
    "拉斯維加斯": "LAS", "賭城": "LAS",
    "夏威夷": "HNL", "檀香山": "HNL",
    "溫哥華": "YVR", "加拿大": "YVR",
    "多倫多": "YTO",
    "墨西哥城": "MEX", "墨西哥": "MEX",
    "坎昆": "CUN",
    # 大洋洲
    "雪梨": "SYD", "sydney": "SYD", "澳洲": "SYD",
    "墨爾本": "MEL",
    "布里斯本": "BNE",
    "奧克蘭": "AKL", "紐西蘭": "AKL",
    "黃金海岸": "OOL",
    # 中東
    "杜拜": "DXB", "阿聯酋": "DXB",
    "阿布達比": "AUH",
    "多哈": "DOH", "卡達": "DOH",
    # 南亞
    "新德里": "DEL", "印度": "DEL",
    "孟買": "BOM",
    "清奈": "MAA",
    "斯里蘭卡": "CMB", "可倫坡": "CMB",
    "加德滿都": "KTM", "尼泊爾": "KTM",
    # 其他
    "帛琉": "ROR",
    "關島": "GUM",
    "亞庇": "BKI",
    "蘭卡威": "LGK",
    "檳城": "PEN",
    "金邊": "PNH", "柬埔寨": "PNH",
    "暹粒": "REP", "吳哥窟": "REP",
    "仰光": "RGN", "緬甸": "RGN",
}

# 城市中文名對照（IATA → 顯示名稱）
IATA_TO_NAME = {
    "TYO": "東京", "OSA": "大阪", "NGO": "名古屋", "FUK": "福岡",
    "CTS": "札幌", "OKA": "沖繩", "KIX": "京都/關西",
    "SEL": "首爾", "PUS": "釜山", "CJU": "濟州",
    "BKK": "曼谷", "CNX": "清邁", "HKT": "普吉島", "SIN": "新加坡",
    "KUL": "吉隆坡", "SGN": "胡志明市", "HAN": "河內",
    "DPS": "峇里島", "MNL": "馬尼拉", "CEB": "宿霧", "JKT": "雅加達",
    "HKG": "香港", "MFM": "澳門", "SHA": "上海", "BJS": "北京",
    "CAN": "廣州", "SZX": "深圳",
    "LON": "倫敦", "PAR": "巴黎", "ROM": "羅馬", "MIL": "米蘭",
    "BCN": "巴塞隆納", "AMS": "阿姆斯特丹", "FRA": "法蘭克福",
    "VIE": "維也納", "PRG": "布拉格", "ZRH": "蘇黎世", "IST": "伊斯坦堡",
    "NYC": "紐約", "LAX": "洛杉磯", "SFO": "舊金山", "SEA": "西雅圖",
    "YVR": "溫哥華", "YTO": "多倫多",
    "SYD": "雪梨", "MEL": "墨爾本", "AKL": "奧克蘭",
    "DXB": "杜拜", "ROR": "帛琉", "GUM": "關島",
    "NRT": "東京成田", "HND": "東京羽田", "ICN": "首爾仁川",
    "BKI": "亞庇", "LGK": "蘭卡威", "PEN": "檳城",
    "PNH": "金邊", "REP": "暹粒", "RGN": "仰光",
    # 台灣國內線
    "TPE": "台北桃園", "TSA": "台北松山",
    "KHH": "高雄", "RMQ": "台中", "TNN": "台南",
    "HUN": "花蓮", "TTT": "台東",
    "MZG": "澎湖馬公", "CMJ": "澎湖七美", "WOT": "澎湖望安",
    "KNH": "金門", "MFK": "馬祖北竿", "LZN": "馬祖南竿",
    "GNI": "綠島", "KYD": "蘭嶼",
    "CYI": "嘉義", "TXG": "豐原",
}

# 國旗 emoji
CITY_FLAG = {
    "TYO": "\U0001f1ef\U0001f1f5", "OSA": "\U0001f1ef\U0001f1f5", "NGO": "\U0001f1ef\U0001f1f5",
    "FUK": "\U0001f1ef\U0001f1f5", "CTS": "\U0001f1ef\U0001f1f5", "OKA": "\U0001f1ef\U0001f1f5",
    "KIX": "\U0001f1ef\U0001f1f5", "NRT": "\U0001f1ef\U0001f1f5", "HND": "\U0001f1ef\U0001f1f5",
    "SEL": "\U0001f1f0\U0001f1f7", "PUS": "\U0001f1f0\U0001f1f7", "CJU": "\U0001f1f0\U0001f1f7",
    "ICN": "\U0001f1f0\U0001f1f7",
    "BKK": "\U0001f1f9\U0001f1ed", "CNX": "\U0001f1f9\U0001f1ed", "HKT": "\U0001f1f9\U0001f1ed",
    "SIN": "\U0001f1f8\U0001f1ec", "KUL": "\U0001f1f2\U0001f1fe",
    "SGN": "\U0001f1fb\U0001f1f3", "HAN": "\U0001f1fb\U0001f1f3",
    "DPS": "\U0001f1ee\U0001f1e9", "JKT": "\U0001f1ee\U0001f1e9",
    "MNL": "\U0001f1f5\U0001f1ed", "CEB": "\U0001f1f5\U0001f1ed",
    "HKG": "\U0001f1ed\U0001f1f0", "MFM": "\U0001f1f2\U0001f1f4",
    "SHA": "\U0001f1e8\U0001f1f3", "BJS": "\U0001f1e8\U0001f1f3",
    "CAN": "\U0001f1e8\U0001f1f3", "SZX": "\U0001f1e8\U0001f1f3",
    "LON": "\U0001f1ec\U0001f1e7", "PAR": "\U0001f1eb\U0001f1f7",
    "ROM": "\U0001f1ee\U0001f1f9", "MIL": "\U0001f1ee\U0001f1f9",
    "BCN": "\U0001f1ea\U0001f1f8", "AMS": "\U0001f1f3\U0001f1f1",
    "FRA": "\U0001f1e9\U0001f1ea", "VIE": "\U0001f1e6\U0001f1f9",
    "PRG": "\U0001f1e8\U0001f1ff", "ZRH": "\U0001f1e8\U0001f1ed",
    "IST": "\U0001f1f9\U0001f1f7",
    "NYC": "\U0001f1fa\U0001f1f8", "LAX": "\U0001f1fa\U0001f1f8",
    "SFO": "\U0001f1fa\U0001f1f8", "SEA": "\U0001f1fa\U0001f1f8",
    "YVR": "\U0001f1e8\U0001f1e6", "YTO": "\U0001f1e8\U0001f1e6",
    "SYD": "\U0001f1e6\U0001f1fa", "MEL": "\U0001f1e6\U0001f1fa",
    "AKL": "\U0001f1f3\U0001f1ff",
    "DXB": "\U0001f1e6\U0001f1ea", "ROR": "\U0001f1f5\U0001f1fc",
    "GUM": "\U0001f1ec\U0001f1fa",
    "BKI": "\U0001f1f2\U0001f1fe", "LGK": "\U0001f1f2\U0001f1fe", "PEN": "\U0001f1f2\U0001f1fe",
    "PNH": "\U0001f1f0\U0001f1ed", "REP": "\U0001f1f0\U0001f1ed", "RGN": "\U0001f1f2\U0001f1f2",
}

# 台灣機場 IATA（出發地名稱對應）
TW_AIRPORTS = {
    "台北": "TPE", "桃園": "TPE", "松山": "TSA",
    "高雄": "KHH", "小港": "KHH",
    "台中": "RMQ", "清泉崗": "RMQ",
    "台南": "TNN",
    "花蓮": "HUN",
}

# 所有台灣機場代碼（含離島）—— 用於過濾國內線
TW_ALL_AIRPORTS = {
    "TPE", "TSA",           # 台北
    "KHH",                  # 高雄
    "RMQ",                  # 台中
    "TNN",                  # 台南
    "HUN",                  # 花蓮
    "TTT",                  # 台東
    "MZG", "CMJ", "WOT",   # 澎湖
    "KNH",                  # 金門
    "MFK", "LZN",           # 馬祖
    "GNI",                  # 綠島
    "KYD",                  # 蘭嶼
    "CYI",                  # 嘉義
}

# IATA → 國家碼（ISO 3166-1 alpha-2）
IATA_TO_COUNTRY = {
    "TYO": "JP", "OSA": "JP", "NGO": "JP", "FUK": "JP", "CTS": "JP",
    "OKA": "JP", "KIX": "JP", "NRT": "JP", "HND": "JP",
    "SEL": "KR", "PUS": "KR", "CJU": "KR", "ICN": "KR",
    "BKK": "TH", "CNX": "TH", "HKT": "TH",
    "SIN": "SG", "KUL": "MY", "BKI": "MY", "LGK": "MY", "PEN": "MY",
    "SGN": "VN", "HAN": "VN",
    "DPS": "ID", "JKT": "ID",
    "MNL": "PH", "CEB": "PH",
    "HKG": "HK", "MFM": "MO",
    "SHA": "CN", "BJS": "CN", "CAN": "CN", "SZX": "CN",
    "LON": "GB", "PAR": "FR", "ROM": "IT", "MIL": "IT",
    "BCN": "ES", "AMS": "NL", "FRA": "DE", "VIE": "AT",
    "PRG": "CZ", "ZRH": "CH", "IST": "TR",
    "NYC": "US", "LAX": "US", "SFO": "US", "SEA": "US",
    "YVR": "CA", "YTO": "CA",
    "SYD": "AU", "MEL": "AU", "AKL": "NZ",
    "DXB": "AE", "ROR": "PW", "GUM": "GU",
    "PNH": "KH", "REP": "KH", "RGN": "MM",
}

# Agoda 城市搜尋關鍵字
AGODA_CITY_KEYWORDS = {
    "NRT": "Tokyo", "TYO": "Tokyo", "HND": "Tokyo",
    "OSA": "Osaka", "KIX": "Osaka",
    "ICN": "Seoul", "GMP": "Seoul", "SEL": "Seoul",
    "BKK": "Bangkok", "DMK": "Bangkok",
    "SIN": "Singapore",
    "HKG": "Hong Kong",
    "DPS": "Bali",
    "MNL": "Manila",
    "KUL": "Kuala Lumpur",
    "CGK": "Jakarta",
    "SGN": "Ho Chi Minh City",
    "HAN": "Hanoi",
    "PUS": "Busan",
    "SHA": "Shanghai", "PVG": "Shanghai",
    "PEK": "Beijing",
    "CAN": "Guangzhou",
    "MFM": "Macau",
    "FUK": "Fukuoka",
    "CTS": "Sapporo",
    "OKA": "Okinawa",
    "NGO": "Nagoya",
}

# 城市座標（Open-Meteo 天氣 API 用）
CITY_COORDINATES = {
    "TYO": (35.6762, 139.6503), "OSA": (34.6937, 135.5023),
    "NGO": (35.1815, 136.9066), "FUK": (33.5904, 130.4017),
    "CTS": (43.0618, 141.3545), "OKA": (26.3344, 127.8056),
    "SEL": (37.5665, 126.9780), "PUS": (35.1796, 129.0756),
    "CJU": (33.4996, 126.5312),
    "BKK": (13.7563, 100.5018), "CNX": (18.7883, 98.9853),
    "HKT": (7.8804, 98.3923), "SIN": (1.3521, 103.8198),
    "KUL": (3.1390, 101.6869), "SGN": (10.8231, 106.6297),
    "HAN": (21.0278, 105.8342), "DPS": (-8.3405, 115.0920),
    "MNL": (14.5995, 120.9842), "CEB": (10.3157, 123.8854),
    "JKT": (-6.2088, 106.8456),
    "HKG": (22.3193, 114.1694), "MFM": (22.1987, 113.5439),
    "SHA": (31.2304, 121.4737), "BJS": (39.9042, 116.4074),
    "CAN": (23.1291, 113.2644), "SZX": (22.5431, 114.0579),
    "LON": (51.5074, -0.1278), "PAR": (48.8566, 2.3522),
    "ROM": (41.9028, 12.4964), "MIL": (45.4642, 9.1900),
    "BCN": (41.3874, 2.1686), "AMS": (52.3676, 4.9041),
    "FRA": (50.1109, 8.6821), "VIE": (48.2082, 16.3738),
    "PRG": (50.0755, 14.4378), "ZRH": (47.3769, 8.5417),
    "IST": (41.0082, 28.9784),
    "NYC": (40.7128, -74.0060), "LAX": (34.0522, -118.2437),
    "SFO": (37.7749, -122.4194), "SEA": (47.6062, -122.3321),
    "YVR": (49.2827, -123.1207), "YTO": (43.6532, -79.3832),
    "SYD": (-33.8688, 151.2093), "MEL": (-37.8136, 144.9631),
    "AKL": (-36.8485, 174.7633),
    "DXB": (25.2048, 55.2708), "ROR": (7.3419, 134.4793),
    "GUM": (13.4443, 144.7937),
}
