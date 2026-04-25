export async function completeJson() {
  return null;
}

export async function generateTravelPlan(kind, input = {}) {
  return builtInPlan(kind, input);
}

const destinationAliases = {
  東京: ['東京', 'tokyo', '成田', '羽田'],
  大阪: ['大阪', 'osaka', '關西', '京都', '神戶'],
  首爾: ['首爾', '서울', 'seoul', '仁川', '金浦'],
  曼谷: ['曼谷', 'bangkok', 'bkk'],
  香港: ['香港', 'hong kong', 'hkg'],
  新加坡: ['新加坡', 'singapore', 'sin'],
  福岡: ['福岡', 'fukuoka', '博多'],
  沖繩: ['沖繩', 'okinawa', '那霸'],
  吉隆坡: ['吉隆坡', 'kuala lumpur', 'kul'],
  胡志明市: ['胡志明', '胡志明市', 'ho chi minh', '西貢', 'sgn'],
  馬尼拉: ['馬尼拉', 'manila', 'mnl'],
  峇里島: ['峇里', '峇里島', 'bali', 'dps'],
  河內: ['河內', 'hanoi', 'han'],
  峴港: ['峴港', 'danang', 'da nang', 'dad'],
  澳門: ['澳門', 'macau', 'macao', 'mfm']
};

const destinationProfiles = {
  東京: profile({
    intro: '先把新宿/澀谷/銀座等核心商圈、經典景點與採買點排好，交通以 JR/地鐵為主。',
    hotel: 3800,
    food: 1900,
    transport: 700,
    activity: 2200,
    shopping: 6000,
    days: [
      ['成田或羽田進市區，先到新宿放行李、買 Suica/PASMO', '明治神宮、原宿竹下通、表參道散步', '澀谷 Scramble Square、澀谷 Sky 或 Hachiko 周邊晚餐'],
      ['淺草寺、雷門、仲見世通買人形燒與雷門煎餅', '晴空塔 Solamachi、東京香蕉/Press Butter Sand 採買', '上野阿美橫町吃海鮮丼、逛藥妝'],
      ['築地場外市場吃玉子燒與海鮮早餐', '銀座 Loft、Itoya、UNIQLO Ginza、東京車站一番街', '丸之內夜景、KITTE 屋上庭園'],
      ['TeamLab Borderless 麻布台之丘或豐洲市場', '台場 DiverCity、Aqua City、富士電視台周邊', '豐洲千客萬來或台場海濱公園看夜景'],
      ['吉祥寺井之頭公園、Satou 牛肉丸', '中野 Broadway 或下北澤古著店', '新宿思出橫丁、歌舞伎町 Tower'],
      ['自由之丘甜點、Luz 自由之丘雜貨', '代官山 T-Site、蔦屋書店、惠比壽 Garden Place', '目黑川或惠比壽居酒屋'],
      ['東京車站 Character Street 最後採買', '機場免稅店買 Royce、白色戀人、Tokyo Milk Cheese Factory', '返程']
    ],
    souvenirs: ['東京香蕉', 'Press Butter Sand', 'Tokyo Milk Cheese Factory', '藥妝', 'Loft 文具']
  }),
  大阪: profile({
    intro: '以難波/梅田為基地，排進道頓堀、USJ、京都或奈良一日與伴手禮採買。',
    hotel: 3300,
    food: 1700,
    transport: 650,
    activity: 2600,
    shopping: 5500,
    days: [
      ['關西機場進難波，南海電鐵到飯店放行李', '道頓堀、心齋橋、固力果跑跑人拍照', '一蘭或金龍拉麵、唐吉訶德道頓堀店採買'],
      ['大阪城天守閣與西之丸庭園', '梅田藍天大廈、Grand Front Osaka、阪急百貨', 'HEP FIVE 摩天輪、梅田地下街晚餐'],
      ['USJ 環球影城整日，先排 Nintendo World 或哈利波特區', 'CityWalk 買 Minion 餅乾與限定周邊', '難波宵夜或便利商店補給'],
      ['京都清水寺、二年坂三年坂', '祇園花見小路、錦市場買京漬物與抹茶點心', '河原町晚餐後回大阪'],
      ['黑門市場吃章魚燒、海鮮、草莓大福', '新世界通天閣、阿倍野 Harukas', '551 蓬萊、Pablo 起司塔、Calbee+ 最後採買'],
      ['奈良公園、東大寺、春日大社', '近鐵奈良商店街買柿葉壽司與大佛布丁', '難波或梅田按摩、居酒屋'],
      ['臨空城 Outlet 或關西機場免稅店', '機場買 Royce、白色戀人、KitKat 限定口味', '返程']
    ],
    souvenirs: ['551 蓬萊', 'Pablo 起司塔', '大阪香蕉戀人', 'Calbee+', 'KitKat 限定口味']
  }),
  首爾: profile({
    intro: '以弘大/明洞/聖水/江南核心區為主，先排交通、住宿區域、每日採買與美食重點。',
    hotel: 3000,
    food: 1500,
    transport: 450,
    activity: 1500,
    shopping: 5500,
    days: [
      ['仁川或金浦進市區，搭 AREX/機場巴士到弘大或明洞', '弘大商圈、Olive Young、Kakao Friends、AK Plaza', '明洞烤肉、明洞夜市、換錢與藥妝補貨'],
      ['景福宮、北村韓屋村、三清洞咖啡', '安國 Onion、Tamburins、Gentle Monster', '益善洞韓屋街、鍾路三街烤肉'],
      ['聖水 Dior Seongsu、Amore 聖水、Ader Error', 'Common Ground、建大商圈、首爾林', '漢江盤浦大橋或汝矣島便利商店泡麵'],
      ['COEX Mall、星空圖書館、奉恩寺', '狎鷗亭 Rodeo、Cafe Knotted、Tamburins', '江南站地下街或新沙洞林蔭道'],
      ['南山塔或梨泰院慢散步', '東大門 DDP、現代 City Outlet', '廣藏市場吃綠豆煎餅、麻藥飯捲'],
      ['樂天世界塔 Seoul Sky、蠶室樂天 Mall', '蠶室石村湖、樂天超市採買海苔/泡麵/零食', '弘大或延南洞咖啡廳'],
      ['明洞或弘大最後採買：Olive Young、海苔、蜂蜜奶油杏仁', '搭 AREX/機場巴士到機場', '返程']
    ],
    souvenirs: ['Olive Young 保養品', '海苔', '蜂蜜奶油杏仁', '泡麵', 'Tamburins 香氛']
  }),
  曼谷: profile({
    intro: '以 Siam/Asok/Silom 作為移動核心，安排百貨、夜市、按摩與寺廟水上市場。',
    hotel: 2400,
    food: 1300,
    transport: 550,
    activity: 1700,
    shopping: 4500,
    days: [
      ['素萬那普或廊曼進市區，BTS/MRT 交通卡與換匯', 'Siam Paragon、CentralWorld、Big C 採買零食', 'After You、Nara Thai 或 Somboon 建興酒家'],
      ['大皇宮、臥佛寺、鄭王廟', 'Tha Maharaj 河岸咖啡、ICONSIAM', '昭披耶河遊船或 ICONSIAM 水舞'],
      ['恰圖恰週末市集或 Or Tor Kor 市場', 'Ari 咖啡街、La Villa Ari', 'Health Land 或 Let’s Relax 按摩'],
      ['丹嫩莎朵水上市場或美功鐵道市場半日', 'Terminal 21、EmQuartier', 'Jodd Fairs 夜市吃火山排骨與泰奶'],
      ['Erawan 四面佛、Platinum Fashion Mall', 'Central Embassy、Boots/Watsons 採買', 'Rooftop Bar 或 Asiatique 河濱夜市'],
      ['洽圖洽 JJ Mall、Union Mall', 'Big C 買 Pocky、Mama 麵、小老闆海苔、Mistine', '回飯店整理行李與按摩'],
      ['機場快線或 Grab 到機場', '機場 King Power 買芒果乾、泰奶茶包', '返程']
    ],
    souvenirs: ['小老闆海苔', 'Mama 麵', '泰奶茶包', 'Mistine 彩妝', '芒果乾']
  }),
  香港: profile({
    intro: '用港鐵串起中環、尖沙咀、旺角與迪士尼/太平山，吃買點都先排進去。',
    hotel: 3600,
    food: 1800,
    transport: 550,
    activity: 2300,
    shopping: 5200,
    days: [
      ['機場快線到香港站或九龍站，買八達通', '中環半山手扶梯、PMQ、蘭芳園', '太平山夜景、鏞記或九記牛腩'],
      ['尖沙咀星光大道、K11 Musea', '海港城、Bakehouse 蛋撻、Jenny Bakery', '維港幻彩詠香江、廟街夜市'],
      ['迪士尼樂園整日', '迪士尼限定周邊與曲奇', '回市區吃翠華或一樂燒鵝'],
      ['旺角女人街、波鞋街、朗豪坊', '深水埗鴨寮街、合益泰腸粉', '油麻地廟街煲仔飯'],
      ['赤柱市集或南區海濱', '銅鑼灣 Times Square、SOGO、希慎廣場', '甘牌燒鵝或橋底辣蟹'],
      ['上環買奇華餅家、檸檬王、樓上燕窩莊', '機場快線回機場', '返程']
    ],
    souvenirs: ['Jenny Bakery', '奇華餅家', '檸檬王', '曲奇四重奏', '港式奶茶茶包']
  }),
  新加坡: profile({
    intro: '以 MRT 串連濱海灣、烏節、牛車水、小印度與聖淘沙，吃飯與採買點都排入動線。',
    hotel: 4200,
    food: 1900,
    transport: 500,
    activity: 2600,
    shopping: 5000,
    days: [
      ['樟宜機場入境，Jewel 瀑布與 Shake Shack/松發肉骨茶', '濱海灣金沙、魚尾獅公園、Helix Bridge', 'Gardens by the Bay 燈光秀'],
      ['牛車水佛牙寺、Chinatown Complex', 'Maxwell Food Centre 天天海南雞飯、林志源肉乾', '克拉碼頭或 Boat Quay 河岸晚餐'],
      ['聖淘沙 Universal Studios Singapore 或 S.E.A. Aquarium', 'VivoCity、Candylicious 採買', 'Wings of Time 或海邊酒吧'],
      ['小印度 Sri Veeramakaliamman Temple、Mustafa Centre', '阿拉伯街 Haji Lane、蘇丹回教堂', 'Bugis Junction、白蘭閣街美食'],
      ['烏節路 ION、Takashimaya、Design Orchard', 'Bacha Coffee、TWG Tea、松發肉骨茶包採買', 'Newton Food Centre 吃辣椒螃蟹或沙嗲'],
      ['Tiong Bahru Bakery、BooksActually 周邊', '樟宜 Jewel 最後採買：斑斕蛋糕、咖椰醬、肉乾', '返程']
    ],
    souvenirs: ['Bacha Coffee', 'TWG Tea', '林志源肉乾', '咖椰醬', '斑斕蛋糕']
  }),
  福岡: profile({
    intro: '以博多/天神為住宿核心，排太宰府、運河城、屋台與九州伴手禮。',
    hotel: 3000,
    food: 1600,
    transport: 600,
    activity: 1500,
    shopping: 4800,
    days: [
      ['福岡機場搭地鐵到博多，飯店放行李', '博多車站 AMU Plaza、阪急百貨', '中洲屋台吃拉麵、明太子玉子燒'],
      ['太宰府天滿宮、表參道梅枝餅', '九州國立博物館或竈門神社', '天神地下街、Parco、Solaria Plaza'],
      ['櫛田神社、博多町家故鄉館', '運河城 Canal City、拉麵競技場', '一蘭本社總本店或博多華味鳥水炊鍋'],
      ['糸島半日：夫婦岩、Beach Cafe SUNSET', '回天神買明太子、通堂拉麵包、茅乃舍高湯包', '大名咖啡廳、屋台二訪'],
      ['博多車站最後採買：博多通りもん、明月堂、Calbee+', '福岡機場免稅店', '返程']
    ],
    souvenirs: ['博多通りもん', '明太子', '茅乃舍高湯包', '梅枝餅', '一蘭拉麵包']
  }),
  沖繩: profile({
    intro: '以那霸/國際通和海景路線為主，搭配美麗海水族館、古宇利島與沖繩限定採買。',
    hotel: 3300,
    food: 1600,
    transport: 900,
    activity: 2100,
    shopping: 4500,
    days: [
      ['那霸機場到國際通，買 Yui Rail 一日券或取車', '國際通、牧志公設市場、Calbee+ 沖繩限定', '屋台村吃沖繩麵、阿古豬料理'],
      ['波上宮、瀨長島 Umikaji Terrace', 'Ashibinaa Outlet、iias 沖繩豐崎', '國際通 Don Quijote 採買雪鹽、黑糖、泡盛'],
      ['美麗海水族館、海洋博公園', '古宇利島大橋、蝦蝦飯 Kouri Shrimp', '名護或恩納村海景晚餐'],
      ['萬座毛、青之洞窟浮潛或玻璃船', '美國村 American Village、Depot Island', '北谷看夕陽、Blue Seal 冰淇淋'],
      ['首里城公園、金城町石疊道', '壺屋通買陶器、咖啡廳', '國際通最後採買：紅芋塔、雪鹽餅乾、海葡萄'],
      ['那霸機場商店街買御菓子御殿紅芋塔', '還車或搭 Yui Rail 到機場', '返程']
    ],
    souvenirs: ['紅芋塔', '雪鹽餅乾', '黑糖', '泡盛', '海葡萄']
  }),
  吉隆坡: profile({
    intro: '以 Bukit Bintang/KLCC 為核心，排雙子星、茨廠街、黑風洞與 Pavilion 採買。',
    hotel: 2500,
    food: 1300,
    transport: 600,
    activity: 1500,
    shopping: 4200,
    days: [
      ['KLIA Ekspres 或 Grab 到市區，入住 Bukit Bintang/KLCC', 'Pavilion KL、Lot 10、Jalan Alor 熟食街', 'KLCC 雙子星夜景與 Suria KLCC'],
      ['黑風洞 Batu Caves', 'Royal Selangor Visitor Centre 或 The Row 咖啡', 'Jalan Alor 吃黃亞華小食店烤雞翅'],
      ['獨立廣場、蘇丹阿都沙末大樓、城市藝廊', '茨廠街、鬼仔巷、中央藝術坊買蠟染與白咖啡', 'Heli Lounge Bar 或 TRX Exchange'],
      ['Thean Hou Temple 天后宮', 'Mid Valley Megamall、The Gardens Mall', 'Village Park Nasi Lemak 或 Madam Kwan’s'],
      ['Putrajaya 粉紅清真寺半日', 'Pavilion/Don Don Donki 最後採買：Beryl’s 巧克力、舊街場白咖啡', '按摩或回飯店整理行李'],
      ['KLIA2 Mitsui Outlet 或機場免稅店', '買榴槤餅、白咖啡、Beryl’s 巧克力', '返程']
    ],
    souvenirs: ['舊街場白咖啡', 'Beryl’s 巧克力', '榴槤餅', '蠟染小物', 'BOH 茶']
  }),
  胡志明市: profile({
    intro: '以第一郡為基地，排咖啡、公寓咖啡、濱城市場、歷史景點與越南伴手禮。',
    hotel: 2200,
    food: 1200,
    transport: 450,
    activity: 1500,
    shopping: 3800,
    days: [
      ['新山一機場 Grab 到第一郡，換匯與 SIM 卡', '聖母聖殿主教座堂、中央郵局、書街', '阮惠步行街、公寓咖啡 42 Nguyen Hue'],
      ['統一宮、戰爭遺跡博物館', '濱城市場買腰果、咖啡、G7、椰子糖', 'Pizza 4P’s 或 Secret Garden 晚餐'],
      ['粉紅教堂 Tan Dinh Church', 'Tan Dinh Market、Maison Marou 巧克力咖啡', 'Bui Vien 或 Saigon Saigon Rooftop Bar'],
      ['古芝地道半日或湄公河一日遊', '回第一郡按摩 Miu Miu Spa 或 Temple Leaf Spa', 'Bep Me In 吃越南菜'],
      ['Saigon Centre、Takashimaya、L’Usine 咖啡', 'An Dong Market 或 Saigon Square 採買', '最後吃 Pho Hoa Pasteur 或 Banh Mi Huynh Hoa'],
      ['機場前補買 Trung Nguyen 咖啡、腰果、越南泡麵', 'Grab 到新山一機場', '返程']
    ],
    souvenirs: ['G7 咖啡', 'Trung Nguyen 咖啡', '腰果', '椰子糖', 'Maison Marou 巧克力']
  }),
  馬尼拉: profile({
    intro: '以 Makati/BGC/馬尼拉灣為主，先把 Intramuros、商場、咖啡甜點與伴手禮安排好。',
    hotel: 2800,
    food: 1200,
    transport: 500,
    activity: 1500,
    shopping: 5000,
    days: [
      ['NAIA 機場到 Makati 或 BGC，先買 SIM/Grab 設定', 'Greenbelt、Glorietta、SM Makati 熟悉周邊', 'Manam 或 Mesa 吃菲式料理'],
      ['Intramuros、Fort Santiago、San Agustin Church', 'Rizal Park、National Museum of Fine Arts', 'Binondo 中國城吃 Eng Bee Tin、Sincerity Fried Chicken'],
      ['Salcedo Saturday Market 或 Legazpi Sunday Market', 'BGC High Street、Mind Museum、Fully Booked', 'Venice Grand Canal Mall 拍照與晚餐'],
      ['Mall of Asia、馬尼拉灣海濱', 'Kultura Filipino 買芒果乾、珍珠飾品、Barong 小物', 'Conrad/S Maison 或 MOA Seaside 餐廳'],
      ['Ayala Museum、Ayala Triangle Gardens', 'Power Plant Mall、Rockwell 咖啡甜點', 'Poblacion 酒吧街或 The Alley by Vikings'],
      ['最後採買：Kultura、SM Supermarket、Jollibee 甜派', 'NAIA 機場買 7D 芒果乾、Polvoron、Ube Jam、Barako Coffee', '返程']
    ],
    souvenirs: ['7D 芒果乾', 'Goldilocks Polvoron', 'Ube Jam', 'Barako Coffee', 'Eng Bee Tin Hopia']
  }),
  峇里島: profile({
    intro: '把烏布、海神廟、Seminyak/Canggu 與海灘咖啡排成低壓但明確的動線。',
    hotel: 3200,
    food: 1400,
    transport: 900,
    activity: 2200,
    shopping: 4200,
    days: [
      ['DPS 機場到 Seminyak 或 Canggu，安排包車/Grab', 'Seminyak Village、Sisterfields、Petitenget Beach', 'La Plancha 或 Potato Head 看夕陽'],
      ['烏布皇宮、烏布市場', 'Tegalalang Rice Terrace、Tirta Empul 聖泉寺', '烏布晚餐 Bebek Bengil 或 Locavore To Go'],
      ['海神廟 Tanah Lot', 'Canggu 咖啡：Crate Cafe、The Lawn', 'Canggu 海灘酒吧或按摩'],
      ['Uluwatu Temple、Padang Padang Beach', 'GWK 文化公園', 'Jimbaran 海鮮晚餐'],
      ['Krisna Oleh-Oleh 採買伴手禮', 'Beachwalk Shopping Center、Kuta Beach', '最後按摩與整理行李'],
      ['機場前買 Bali Banana、Kopi Luwak、精油、香氛皂', 'DPS 機場報到', '返程']
    ],
    souvenirs: ['Kopi Luwak', 'Bali Banana', '精油', '香氛皂', '木雕/藤編小物']
  }),
  峴港: profile({
    intro: '以美溪沙灘、韓市場、會安古鎮、巴拿山與海鮮按摩排成可直接執行的路線。',
    hotel: 2600,
    food: 1200,
    transport: 650,
    activity: 2200,
    shopping: 3500,
    days: [
      ['抵達 DAD 後叫 Grab 到美溪沙灘飯店，先買 SIM/eSIM 與換匯', '美溪沙灘散步、A La Carte 或 HAIAN 周邊咖啡', 'Bé Mặn 或 Hải Sản Năm Đảnh 海鮮晚餐'],
      ['粉紅教堂、龍橋、韓江橋拍照', '韓市場買腰果、咖啡、椰子餅、草編包', 'Helio Night Market 或 Sơn Trà 夜市'],
      ['巴拿山 Sun World 整日，黃金佛手橋、法國村、纜車', '園區午餐與拍照，下午下山回市區', 'Con Market 宵夜或飯店附近按摩'],
      ['會安古鎮半日：日本橋、福建會館、燈籠街', 'Faifo Coffee、Reaching Out Tea House、會安市場採買', 'Thu Bồn River 放水燈，晚餐吃 Morning Glory'],
      ['山茶半島靈應寺、Lady Buddha', '峴港大教堂附近咖啡、Vincom Plaza 或 Lotte Mart 採買', '龍橋噴火日可看表演，不然安排海邊酒吧'],
      ['飯店早餐後整理行李', 'Lotte Mart 補買 G7、Trung Nguyen、腰果、椰子餅', '前往 DAD 機場返程']
    ],
    souvenirs: ['G7 咖啡', 'Trung Nguyen 咖啡', '腰果', '椰子餅', '韓市場草編包']
  }),
  河內: profile({
    intro: '以還劍湖與老城區為核心，排咖啡、米其林小吃、下龍灣/寧平近郊與伴手禮。',
    hotel: 2500,
    food: 1200,
    transport: 550,
    activity: 1800,
    shopping: 3500,
    days: [
      ['抵達 HAN 後搭車進老城區，飯店放行李', '還劍湖、玉山祠、三十六古街散步', 'Bún Chả Hương Liên 或 Bánh Mì 25 晚餐'],
      ['河內大教堂、Train Street 咖啡', '文廟、昇龍皇城、越南婦女博物館', 'Tạ Hiện 啤酒街或水上木偶戲'],
      ['下龍灣一日遊或寧平陸龍灣一日遊', '搭船/景點行程依當天團體安排', '回老城區按摩與宵夜 Pho Thin'],
      ['Giảng Cafe 蛋咖啡、Loading T Cafe', '同春市場買咖啡、腰果、蓮花茶', '西湖 Tran Quoc Pagoda 與湖邊晚餐'],
      ['Lotte Center Hanoi 或 Vincom Center 採買', '老城區最後補貨：Marou 巧克力、越南咖啡濾杯', '整理行李與機場交通確認'],
      ['飯店早餐', '最後買伴手禮與前往 HAN 機場', '返程']
    ],
    souvenirs: ['G7 咖啡', 'Trung Nguyen 咖啡', '蓮花茶', 'Marou 巧克力', '腰果']
  }),
  澳門: profile({
    intro: '把大三巴、議事亭前地、路氹飯店娛樂、官也街與葡式伴手禮排成不浪費腳程的路線。',
    hotel: 4200,
    food: 1700,
    transport: 500,
    activity: 1600,
    shopping: 4500,
    days: [
      ['抵達 MFM 或港珠澳口岸後搭接駁到飯店', '議事亭前地、玫瑰堂、大三巴牌坊', '黃枝記、瑪嘉烈蛋撻、福隆新街晚餐'],
      ['東望洋燈塔、瘋堂斜巷、塔石廣場', '新馬路買鉅記、咀香園、杏仁餅與肉乾', '永利皇宮纜車或美高梅夜景'],
      ['路氹金光大道：威尼斯人、巴黎人、倫敦人', '官也街吃大利來記豬扒包、莫義記榴槤雪糕', '水舞間/飯店秀或綜合度假村晚餐'],
      ['媽閣廟、海事博物館、主教山小堂', '十月初五街、咖啡與葡國菜餐廳', '漁人碼頭或澳門塔夜景'],
      ['黑沙海灘或龍環葡韻', '路氹最後購物與飯店設施', '整理行李'],
      ['飯店早餐與退房', '最後補買蛋捲、杏仁餅、花生糖', '前往機場或口岸返程']
    ],
    souvenirs: ['鉅記杏仁餅', '咀香園蛋捲', '肉乾', '花生糖', '葡式罐頭']
  })
};

const fallbackProfile = profile({
  intro: '先排城市核心地標、主要商圈、在地市場與交通方便的住宿區；若你指定景點，我會把它排進最順路的一天。',
  hotel: 3000,
  food: 1500,
  transport: 600,
  activity: 1800,
  shopping: 4000,
  days: [
    ['抵達後先進市中心交通樞紐，買交通卡與 SIM 卡', '市中心主要廣場、官方旅遊中心確認路線', '飯店附近代表性餐廳與超市補給'],
    ['城市最知名歷史景點或博物館', '主要商圈與百貨、當地設計選物店', '夜市或河岸夜景'],
    ['在地市場早餐與咖啡店', '文化街區、寺廟/教堂/老街', '伴手禮採買與按摩'],
    ['近郊半日遊或海邊/山景景點', '回市區自由購物', '最後晚餐與整理行李'],
    ['飯店附近早餐', '最後採買與機場交通', '返程']
  ],
  souvenirs: ['在地咖啡/茶', '零食', '特色調味料', '設計小物']
});

export function builtInPlan(kind, input) {
  const destination = normalizeDestination(input.destination ?? destinationFromRegion(input.region) ?? '首爾');
  const days = clampDays(input.days ?? travelDays(input.startDate, input.endDate), kind === 'quick' ? 3 : 5);
  const lodging = input.lodgingPreference ?? '交通優先';

  if (kind === 'local_transport') return transportGuide(destination);
  if (kind === 'star_trip') return starTripPlan(destination, input, days);

  const title = kind === 'quick' ? '說走就走行程' : '自由行行程';
  const daysPlan = buildDailyPlan(destination, days, input.mustVisit);
  const profileData = getProfile(destination);

  return {
    title: `${destination} ${days}天${title}`,
    destination,
    summary: [
      `${destination} ${days}天以 ${lodging}、住宿區域、每日景點與採買重點先排好。${profileData.intro}`,
      hasSpecialNeed(input.mustVisit) ? `已把特殊需求納入：${input.mustVisit}。` : ''
    ].filter(Boolean).join(' '),
    budget: estimateBudget({ destination, days, flightPicks: input.flightPicks, travelerCount: input.travelerCount }),
    days: daysPlan,
    reminders: [
      `伴手禮先鎖定：${profileData.souvenirs.join('、')}。`,
      '機票與住宿價格會浮動，出發前仍要以訂購頁最終金額為準。',
      '說走就走版本先抓好大方向與可直接執行的店家/景點，細節可再依班機時間微調。'
    ]
  };
}

function buildDailyPlan(destination, days, mustVisit) {
  const profileData = getProfile(destination);
  const result = Array.from({ length: days }, (_, index) => {
    const [morning, afternoon, evening] = profileData.days[index % profileData.days.length];
    return { day: index + 1, morning, afternoon, evening };
  });

  if (hasSpecialNeed(mustVisit)) {
    result[0] = {
      ...result[0],
      afternoon: `${mustVisit}；再接 ${result[0].afternoon}`
    };
  }

  return result;
}

function hasSpecialNeed(value) {
  const text = String(value ?? '').trim();
  return Boolean(text && text !== '無');
}

function estimateBudget({ destination, days, flightPicks, travelerCount = 1 }) {
  const profileData = getProfile(destination);
  const people = Math.max(1, Number(travelerCount) || 1);
  const flight = parsePrice(flightPicks?.cheapest?.priceText) ?? defaultFlightBudget(destination);
  const nights = Math.max(1, days - 1);
  const perPerson = flight
    + profileData.hotel * nights
    + (profileData.food + profileData.transport) * days
    + profileData.activity
    + profileData.shopping;
  const total = perPerson * people;

  return {
    title: people > 1 ? `${people}人預算` : '一人預算',
    totalText: `約 TWD ${roundHundred(total).toLocaleString()}`,
    lines: [
      `機票：${people}人 x 約 TWD ${roundHundred(flight).toLocaleString()}`,
      `住宿：${people}人 ${nights}晚，共約 TWD ${roundHundred(profileData.hotel * nights * people).toLocaleString()}`,
      `餐飲交通：共約 TWD ${roundHundred((profileData.food + profileData.transport) * days * people).toLocaleString()}`,
      `門票/採買預留：共約 TWD ${roundHundred((profileData.activity + profileData.shopping) * people).toLocaleString()}`
    ],
    note: '不含精品、大量購物和旺季漲價。'
  };
}

function getProfile(destination) {
  return destinationProfiles[normalizeDestination(destination)] ?? fallbackProfile;
}

function profile(data) {
  return data;
}

function normalizeDestination(value = '') {
  const text = String(value).trim();
  const lower = text.toLowerCase();
  for (const [canonical, aliases] of Object.entries(destinationAliases)) {
    if (aliases.some((alias) => lower.includes(alias.toLowerCase()))) return canonical;
  }
  return text || '首爾';
}

function parsePrice(text = '') {
  const matched = String(text).replaceAll(',', '').match(/TWD\s*(\d+)/i);
  return matched ? Number(matched[1]) : null;
}

function defaultFlightBudget(destination) {
  const normalized = normalizeDestination(destination);
  if (['東京', '大阪', '首爾', '福岡', '沖繩'].includes(normalized)) return 9000;
  if (['曼谷', '新加坡', '吉隆坡', '峇里島'].includes(normalized)) return 11000;
  if (['香港', '胡志明市', '馬尼拉'].includes(normalized)) return 8000;
  return 10000;
}

function roundHundred(value) {
  return Math.ceil(value / 100) * 100;
}

function transportGuide(destination) {
  const normalized = normalizeDestination(destination);
  return {
    title: `${normalized} 交通快速指南`,
    destination: normalized,
    summary: `${normalized} 建議先確認機場到市區的最快路線，再用地鐵/捷運/Grab/計程車串每日景點。`,
    reminders: [
      '抵達後先處理交通卡、SIM/eSIM 與機場到住宿的路線。',
      '行李多或深夜抵達時，優先選直達巴士、機場快線或叫車。',
      '每日景點安排以同區域串接，避免說走就走卻把時間浪費在轉車。'
    ],
    days: []
  };
}

function starTripPlan(destination, input, days) {
  const normalized = normalizeDestination(destination);
  const artist = input.artistName ?? '藝人';
  const eventType = input.eventType ?? '活動';
  return {
    title: `${artist} ${eventType} 追星行程`,
    destination: normalized,
    summary: `以 ${eventType} 場館時間為核心，住宿選場館/交通節點附近，其他行程用同區域景點與採買補滿。`,
    budget: estimateBudget({ destination: normalized, days, flightPicks: input.flightPicks, travelerCount: input.travelerCount }),
    days: buildDailyPlan(normalized, Math.max(3, days), input.mustVisit ?? `${eventType} 場館`)
  };
}

function destinationFromRegion(region = '') {
  if (region.includes('日本')) return '東京';
  if (region.includes('韓')) return '首爾';
  if (region.includes('泰')) return '曼谷';
  return null;
}

function travelDays(startDate, endDate) {
  if (!startDate || !endDate) return null;
  const start = new Date(`${startDate}T00:00:00Z`);
  const end = new Date(`${endDate}T00:00:00Z`);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return null;
  return Math.max(1, Math.round((end - start) / 86400000) + 1);
}

function clampDays(value, fallback) {
  const match = String(value ?? '').match(/\d+/);
  const days = match ? Number(match[0]) : Number(value);
  if (!Number.isFinite(days)) return fallback;
  return Math.min(7, Math.max(1, days));
}
