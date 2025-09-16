import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)

# 事先產生好的2025年電價資料
price_dict = {
    # 低壓電價
    ("低壓三段式電價", "not_summer"): {
        "天數": 164,
        "最高電價": 4.86,
        "最低電價": 2.12,
        "基本電費": {
            "按戶計收": 262.5,
            "經常契約": 173.2,
            "半尖峰契約": 173.2,
            "週六半尖峰契約": 34.6,
            "離峰契約": 34.6,
        },
    },
    ("低壓三段式電價", "summer"): {
        "天數": 87,
        "最高電價": 8.12,
        "最低電價": 2.23,
        "基本電費": {
            "按戶計收": 262.5,
            "經常契約": 236.2,
            "半尖峰契約": 173.2,
            "週六半尖峰契約": 47.2,
            "離峰契約": 47.2,
        },
    },
    ("低壓二段式電價", "not_summer"): {
        "天數": 164,
        "最高電價": 5.39,
        "最低電價": 2.15,
        "基本電費": {
            "裝置契約_按戶計收": 105.0,
            "裝置契約": 137.5,
            "按戶計收": 262.5,
            "經常契約": 173.2,
            "非夏月契約": 173.2,
            "週六半尖峰契約": 34.6,
            "離峰契約": 34.6,
        },
    },
    ("低壓二段式電價", "summer"): {
        "天數": 87,
        "最高電價": 5.54,
        "最低電價": 2.27,
        "基本電費": {
            "裝置契約_按戶計收": 105.0,
            "裝置契約": 137.5,
            "按戶計收": 262.5,
            "經常契約": 236.2,
            "週六半尖峰契約": 47.2,
            "離峰契約": 47.2,
        },
    },
    ("低壓電動車充換電設施電價", "not_summer"): {
        "天數": 164,
        "最高電價": 12.14,
        "最低電價": 2.9,
        "基本電費": {"按戶計收": 262.5, "經常契約": 34.6},
    },
    ("低壓電動車充換電設施電價", "summer"): {
        "天數": 87,
        "最高電價": 12.47,
        "最低電價": 3.05,
        "基本電費": {"按戶計收": 262.5, "經常契約": 47.2},
    },
    # 高壓電價
    ("高壓三段式電價", "not_summer"): {
        "天數": 144,
        "最高電價": 5.47,
        "最低電價": 2.32,
        "基本電費": {
            "經常契約": 166.9,
            "半尖峰契約": 166.9,
            "週六半尖峰契約": 33.3,
            "離峰契約": 33.3,
        },
    },
    ("高壓三段式電價", "summer"): {
        "天數": 107,
        "最高電價": 9.39,
        "最低電價": 2.53,
        "基本電費": {
            "經常契約": 223.6,
            "半尖峰契約": 166.9,
            "週六半尖峰契約": 44.7,
            "離峰契約": 44.7,
        },
    },
    ("高壓二段式電價", "not_summer"): {
        "天數": 144,
        "最高電價": 6.37,
        "最低電價": 2.46,
        "基本電費": {
            "經常契約": 166.9,
            "非夏月契約": 166.9,
            "週六半尖峰契約": 33.3,
            "離峰契約": 33.3,
        },
    },
    ("高壓二段式電價", "summer"): {
        "天數": 107,
        "最高電價": 6.75,
        "最低電價": 2.71,
        "基本電費": {"經常契約": 223.6, "週六半尖峰契約": 44.7, "離峰契約": 44.7},
    },
    ("高壓批次生產電價", "not_summer"): {
        "天數": 144,
        "最高電價": 11.79,
        "最低電價": 2.88,
        "基本電費": {
            "經常契約": 166.9,
            "非夏月契約": 166.9,
            "週六半尖峰契約": 33.3,
            "離峰契約": 33.3,
        },
    },
    ("高壓批次生產電價", "summer"): {
        "天數": 107,
        "最高電價": 12.47,
        "最低電價": 3.18,
        "基本電費": {"經常契約": 223.6, "週六半尖峰契約": 44.7, "離峰契約": 44.7},
    },
    ("高壓電動車充換電設施電價", "not_summer"): {
        "天數": 144,
        "最高電價": 11.533,
        "最低電價": 2.755,
        "基本電費": {"按戶計收": 249.375, "經常契約": 32.87},
    },
    ("高壓電動車充換電設施電價", "summer"): {
        "天數": 107,
        "最高電價": 11.8465,
        "最低電價": 2.8975,
        "基本電費": {"按戶計收": 249.375, "經常契約": 44.84},
    },
    # 特高壓電價
    ("特高壓三段式電價", "not_summer"): {
        "天數": 144,
        "最高電價": 5.03,
        "最低電價": 2.18,
        "基本電費": {
            "經常契約": 160.6,
            "半尖峰契約": 160.6,
            "週六半尖峰契約": 32.1,
            "離峰契約": 32.1,
        },
    },
    ("特高壓三段式電價", "summer"): {
        "天數": 107,
        "最高電價": 8.69,
        "最低電價": 2.4,
        "基本電費": {
            "經常契約": 217.3,
            "半尖峰契約": 160.6,
            "週六半尖峰契約": 43.4,
            "離峰契約": 43.4,
        },
    },
    ("特高壓二段式電價", "not_summer"): {
        "天數": 144,
        "最高電價": 5.79,
        "最低電價": 2.28,
        "基本電費": {
            "經常契約": 166.6,
            "非夏月契約": 166.6,
            "週六半尖峰契約": 32.1,
            "離峰契約": 32.1,
        },
    },
    ("特高壓二段式電價", "summer"): {
        "天數": 107,
        "最高電價": 6.17,
        "最低電價": 2.55,
        "基本電費": {"經常契約": 217.3, "週六半尖峰契約": 43.4, "離峰契約": 43.4},
    },
    ("特高壓批次生產電價", "not_summer"): {
        "天數": 144,
        "最高電價": 10.8,
        "最低電價": 2.67,
        "基本電費": {
            "經常契約": 160.6,
            "非夏月契約": 160.6,
            "週六半尖峰契約": 32.1,
            "離峰契約": 32.1,
        },
    },
    ("特高壓批次生產電價", "summer"): {
        "天數": 107,
        "最高電價": 11.44,
        "最低電價": 2.99,
        "基本電費": {"經常契約": 217.3, "週六半尖峰契約": 43.4, "離峰契約": 43.4},
    },
    # 表燈電價
    ("表燈標準型三段式電價", "not_summer"): {
        "天數": 164,
        "最高電價": 4.86,
        "最低電價": 2.12,
        "基本電費": {
            "按戶計收_單相": 129.1,
            "按戶計收_三相": 262.5,
            "經常契約": 173.2,
            "非夏月契約": 173.2,
            "週六半尖峰契約": 34.6,
            "離峰契約": 34.6,
        },
    },
    ("表燈標準型三段式電價", "summer"): {
        "天數": 87,
        "最高電價": 8.12,
        "最低電價": 2.23,
        "基本電費": {
            "按戶計收_單相": 129.1,
            "按戶計收_三相": 262.5,
            "經常契約": 236.2,
            "週六半尖峰契約": 47.2,
            "離峰契約": 47.2,
        },
    },
    ("表燈標準型二段式電價", "not_summer"): {
        "天數": 164,
        "最高電價": 5.39,
        "最低電價": 2.15,
        "基本電費": {
            "按戶計收_單相": 129.1,
            "按戶計收_三相": 262.5,
            "經常契約": 173.2,
            "非夏月契約": 173.2,
            "週六半尖峰契約": 34.6,
            "離峰契約": 34.6,
        },
    },
    ("表燈標準型二段式電價", "summer"): {
        "天數": 87,
        "最高電價": 5.54,
        "最低電價": 2.27,
        "基本電費": {
            "按戶計收_單相": 129.1,
            "按戶計收_三相": 262.5,
            "經常契約": 236.2,
            "週六半尖峰契約": 47.2,
            "離峰契約": 47.2,
        },
    },
    ("表燈簡易型三段式電價", "not_summer"): {
        "天數": 164,
        "最高電價": 4.33,
        "最低電價": 1.89,
        "基本電費": {"按戶計收": 75.0, "總度數額度": 2000.0, "超額費率": 1.02},
    },
    ("表燈簡易型三段式電價", "summer"): {
        "天數": 87,
        "最高電價": 6.92,
        "最低電價": 1.96,
        "基本電費": {"按戶計收": 75.0, "總度數額度": 2000.0, "超額費率": 1.02},
    },
    ("表燈簡易型二段式電價", "not_summer"): {
        "天數": 164,
        "最高電價": 4.78,
        "最低電價": 1.89,
        "基本電費": {"按戶計收": 75.0, "總度數額度": 2000.0, "超額費率": 1.02},
    },
    ("表燈簡易型二段式電價", "summer"): {
        "天數": 87,
        "最高電價": 5.01,
        "最低電價": 1.96,
        "基本電費": {"按戶計收": 75.0, "總度數額度": 2000.0, "超額費率": 1.02},
    },
}

dr_program_dict = {
    "0h": {"start_time": "15:30", "end_time": "21:30", "duration_hr": 0, "rate": 0.0},
    "2h": {
        "start_time": "18:00",
        "end_time": "20:00",
        "duration_hr": 2.0,
        "rate": 2.47,
    },
    "4h": {
        "start_time": "16:00",
        "end_time": "20:00",
        "duration_hr": 4.0,
        "rate": 1.84,
    },
    "6h": {
        "start_time": "16:00",
        "end_time": "22:00",
        "duration_hr": 6.0,
        "rate": 1.69,
    },
    "6h_batch": {
        "start_time": "15:30",
        "end_time": "21:30",
        "duration_hr": 6.0,
        "rate": 1.69,
    },
}


# TODO: 補上其他
config_desc = {
    "電價方案": {
        "契約容量": {
            "unit": "字典",
            "description": "包含old和new兩個字典，分別代表原始契約容量和調整後契約容量。每個字典包含經常契約、半尖峰契約/非夏月契約、週六半尖峰契約、離峰契約等四種容量設定",
        },
        "計費類別": {
            "unit": "字串",
            "description": "依據電價公式分類，如高壓三段式、表燈標準型二段式",
        },
        "行業別": {
            "unit": "字串",
            "description": "用電用戶所屬行業別，用於電價計算與統計",
        },
        "夏月天數": {"unit": "天", "description": "夏月期間的總天數，通常為5至10月"},
        "非夏月天數": {
            "unit": "天",
            "description": "非夏月的總天數（總日數-夏月天數）",
        },
        "夏月最高電價": {"unit": "元/kWh", "description": "夏月期間尖峰時段的最高電價"},
        "夏月最低電價": {"unit": "元/kWh", "description": "夏月期間離峰時段的最低電價"},
        "非夏月最高電價": {
            "unit": "元/kWh",
            "description": "非夏月期間尖峰時段的最高電價",
        },
        "非夏月最低電價": {
            "unit": "元/kWh",
            "description": "非夏月期間離峰時段的最低電價",
        },
        "電費調整係數": {
            "unit": "浮點數",
            "description": "針對整體基本電價做的調整倍數，用反應未來電價變動，例如：1.017表示電價上漲1.7%",
        },
        "調整後夏月最高電價": {
            "unit": "元/kWh",
            "description": "經電費調整係數調整後的夏月期間尖峰時段最高電價",
        },
        "調整後夏月最低電價": {
            "unit": "元/kWh",
            "description": "經電費調整係數調整後的夏月期間離峰時段最低電價",
        },
        "調整後非夏月最高電價": {
            "unit": "元/kWh",
            "description": "經電費調整係數調整後的非夏月期間尖峰時段最高電價",
        },
        "調整後非夏月最低電價": {
            "unit": "元/kWh",
            "description": "經電費調整係數調整後的非夏月期間離峰時段最低電價",
        },
    },
    "電價試算": {
        "原始": {
            "年用電度數": {
                "unit": "度",
                "description": "原始負載未使用儲能系統時的年度用電量",
            },
            "年基本電費": {"unit": "元", "description": "原始契約容量下的年度基本電費"},
            "年流動電費": {"unit": "元", "description": "原始負載的年度流動電費"},
            "年總電費": {
                "unit": "元",
                "description": "原始情況下的年度總電費（基本電費+流動電費）",
            },
            "年平均電費": {
                "unit": "元/度",
                "description": "原始情況下的年度平均電費單價",
            },
        },
        "應用儲能": {
            "年用電度數": {"unit": "度", "description": "應用儲能系統後的年度用電量"},
            "年基本電費": {"unit": "元", "description": "調整契約容量後的年度基本電費"},
            "年流動電費": {
                "unit": "元",
                "description": "儲能充放電調度後的年度流動電費",
            },
            "年總電費": {
                "unit": "元",
                "description": "應用儲能後的年度總電費（基本電費+流動電費）",
            },
            "年平均電費": {
                "unit": "元/度",
                "description": "應用儲能後的年度平均電費單價",
            },
        },
    },
    "降低契約容量": {
        "年節省基本電費": {
            "unit": "元",
            "description": "透過降低契約容量所節省的年度基本電費",
        },
        "每kW契約容量費用": {
            "unit": "元/kW",
            "description": "每年每 kW 契約容量需支付的容量費",
        },
        "年契約容量費用": {"unit": "元", "description": "整年度的總容量費用"},
        "降契約容量比例": {
            "unit": "%",
            "description": "預計降低契約容量的比例，與原契約容量相比",
        },
    },
    "儲能系統": {
        "單台 PCS 標稱功率": {
            "unit": "kW",
            "description": "單台一體機 PCS（雙向變流器）的額定功率",
        },
        "單台 儲能容量": {"unit": "kWh", "description": "單台一體機電池的可用儲能容量"},
        "台數": {"unit": "台", "description": "實際安裝的一體機台數"},
        "PCS 標稱功率": {"unit": "kW", "description": "串併完整體系統的 PCS 總功率"},
        "儲能容量": {"unit": "kWh", "description": "串併完整體系統的電池總容量"},
        "C-Rate": {
            "unit": "倍",
            "description": "整體儲能系統的充放電倍率（功率/容量）",
        },
        "電能損失率(Round Trip)": {
            "unit": "%",
            "description": "來回充放電過程中損失的能量百分比",
        },
        "儲能健康度年衰減率": {
            "unit": "%/年",
            "description": "儲能系統每年的容量衰退率",
        },
        "SOC上限": {
            "unit": "%",
            "description": "允許操作的最大電量（State of Charge）",
        },
        "SOC下限": {"unit": "%", "description": "允許操作的最小電量"},
        "實際建置容量": {"unit": "kWh", "description": "儲能系統實際可用的容量"},
        "每日最大循環次數": {
            "unit": "次/日",
            "description": "儲能系統每日允許最大充放電循環次數，只能設整數，目前模擬只支援2循環",
        },
    },
    "負載模擬參數": {
        "夏月每日可轉移度數": {
            "unit": "kWh/日",
            "description": "夏月期間每日尖離峰可以移轉度數",
        },
        "非夏月每日可轉移度數": {
            "unit": "kWh/日",
            "description": "非夏月期間每日尖離峰可以移轉度數",
        },
    },
    "自定義收益(年收/省)": {
        "自定義收益": {
            "unit": "元/年",
            "description": "用戶自定義的收益，不影響模型模擬結果，可能是其他市場或是其他收入來源，例如：避免超約的罰金、調降契約容量的費用",
        },
    },
    "建置成本(第0年繳)": {
        "每單位建置成本": {
            "unit": "元/kWh",
            "description": "每 kWh 儲能容量的平均建置成本",
        },
        "儲能設備": {"unit": "元", "description": "儲能設備本體成本總額"},
        "儲能設備安裝": {"unit": "元", "description": "儲能設備之安裝費用"},
        "高壓設備": {
            "unit": "元",
            "description": "包含變壓器、高壓開關等高壓電力設備成本",
        },
        "高壓設備安裝": {"unit": "元", "description": "高壓設備安裝費用"},
        "設計/監造/簽證費用": {
            "unit": "元",
            "description": "系統設計、監造與簽證的工程費用",
        },
        "EMS": {
            "unit": "元",
            "description": "能源管理系統（Energy Management System）的建置成本",
        },
        "其他": {"unit": "元", "description": "其他相關初期建置成本（調整用）"},
    },
    "維運成本(年繳)": {
        "土地年租金": {"unit": "元/年", "description": "案場土地每年的租金費用"},
        "保險費率": {"unit": "%", "description": "針對總建置成本的保險費率"},
        "案場維運成本": {
            "unit": "元/年",
            "description": "電池與設備等系統的維運與保養費用",
        },
        "EMS維運成本": {"unit": "元/年", "description": "能源管理系統的維運費用"},
        "電力交易雲端平台": {
            "unit": "元/年",
            "description": "雲端平台連接與資料上傳等服務費用",
        },
        "其他固定成本": {"unit": "元/年", "description": "其他年度固定支出（調整用）"},
    },
    "系統服務單價": {
        "EMS系統含硬體_kWh": {
            "unit": "元/kWh",
            "description": "EMS 系統（含硬體）分攤至每 kWh 的建置費用",
        },
        "EMS壓降補償功能_kWh": {
            "unit": "元/kWh",
            "description": "具壓降補償功能的 EMS 模組單價",
        },
        "EMS系統即時備轉_kWh": {
            "unit": "元/kWh",
            "description": "EMS 支援即時備轉服務功能模組單價",
        },
        "太陽能監控功能_kWh": {
            "unit": "元/kWh",
            "description": "EMS 對太陽能案場監控功能模組單價",
        },
        "電力交易雲端使用費_MW": {
            "unit": "元/MW/年",
            "description": "依參與電力市場容量計算的雲端平台年費",
        },
        "電力交易之場域通訊使用_年": {
            "unit": "元/年",
            "description": "場域通訊設備與費率之年費",
        },
        "EMS保固維運費用_年_%": {
            "unit": "%",
            "description": "EMS 系統之年保固與維運支出占初始EMS成本的比例",
        },
        "案場維運費用_年_%": {
            "unit": "%",
            "description": "案場相關維運費用年支出占初始建置成本的比例",
        },
    },
    "聚合分潤": {
        "聚合分潤比例": {
            "unit": "%",
            "description": "參與輔助服務時需分潤給聚合商的比例，如果是0則表示不分潤或是由業主自己操作",
        },
    },
    "可套利天數": {
        "可能超約天數": {"unit": "天", "description": "負載有可能超出契約容量的日數"},
        "歲修天數": {"unit": "天", "description": "設備歲修無法參與服務的日數"},
    },
    "即時備轉": {
        "投標容量": {"unit": "kW", "description": "參與即時備轉市場的最大投標容量"},
        "1級效能價格": {
            "unit": "元/kWh",
            "description": "即時備轉每 kWh 第 1 級效能服務之價格",
        },
        "容量價格": {
            "unit": "元/kWh",
            "description": "即時備轉服務每 kWh 可獲得的容量費價金，此價格是競價而來，可用月平均或年平均代表",
        },
        "得標容量比例": {
            "unit": "%",
            "description": "實際得標容量佔原投標容量的比例，此參數是供給超過需求量時，如dReg，才使用",
        },
        "折扣比例": {
            "unit": "%",
            "description": "由於負載波動少投，或是執行率不見得100%，所設計的投標量折扣率",
        },
        "每月觸發次數": {"unit": "次/月", "description": "即時備轉平均每月觸發的次數"},
        "日前電能邊際價格": {"unit": "元/MWh", "description": "日前市場的邊際電能價格"},
        "保留比例": {"unit": "%", "description": "用於應付不確定性的儲能容量保留比例"},
        "保留容量": {"unit": "kWh", "description": "保留不參與市場的儲能容量"},
    },
    "可參與輔助服務時數": {
        "不可投標天數": {"unit": "天", "description": "排除掉無法參與輔助服務的日數"},
    },
    "日選時段型": {
        "執行方案": {
            "unit": "方案名",
            "description": "所採用的日選型方案名稱，僅有四種，分別為0h、2h、4h、6h，其中0h表示不執行任何方案",
        },
        "抑低契約容量": {"unit": "kW", "description": "透過方案預計可降低的契約容量"},
        "開始時段": {
            "unit": "時間",
            "description": "每日方案開始執行的時間，例如 14:00，會依據所選執行方案自行套入",
        },
        "結束時段": {
            "unit": "時間",
            "description": "每日方案結束執行的時間，例如 17:00，會依據所選執行方案自行套入",
        },
        "執行時數": {
            "unit": "小時",
            "description": "每日執行的總時數，會依據所選執行方案自行套入",
        },
        "流動電費扣減費率": {
            "unit": "%",
            "description": "執行期間所適用的電費扣減費率，會依據所選執行方案自行套入",
        },
        "當日執行率": {
            "unit": "%",
            "description": "當日的執行率，例如：抑低100kW，執行80kW，執行率80%",
        },
        "扣減比率": {
            "unit": "%",
            "description": "當日可扣減的電費比例，依據執行率而定，最低0%，最高120%",
        },
        "5月-10月天數": {
            "unit": "天",
            "description": "方案涵蓋的夏季天數總計（5月到10月），但每年可能動態調整，所以保留調整的彈性",
        },
        "5月-10月可參與天數": {
            "unit": "天",
            "description": "在5月到10月期間可實際參與方案的天數",
        },
    },
    "再生能源義務用戶": {
        "義務裝置容量": {"unit": "kW", "description": "需設置的再生能源裝置容量"},
        "義務裝置容量比例": {
            "unit": "%",
            "description": "用戶需設置儲能容量占契約容量的比例，例如10表示需設置契約容量的10%",
        },
        "早鳥抵減比例": {
            "unit": "%",
            "description": "若在公告日起三年內設置完成可抵減20%；四年內完成則可抵減10%，超過四年則無抵減",
        },
        "既設抵減比例": {
            "unit": "%",
            "description": "若已有既設儲能設備，可依比例抵減義務容量，但不得超過義務容量的20%",
        },
    },
    "融資成本": {
        "貸款成數": {"unit": "%", "description": "建置成本可貸款的比例，通常為70%"},
        "利息費用": {"unit": "%", "description": "貸款年利率，例如2%"},
        "攤還年限": {"unit": "年", "description": "貸款的攤還年限，例如7年"},
    },
}


def load_config():
    """
    載入所有參數（使用者填入 + 計算補上），使用中文欄位名與分群。
    """
    return {
        "電價方案": {
            "契約容量": {
                "old": {
                    "經常契約": None,
                    "半尖峰契約/非夏月契約": None,
                    "週六半尖峰契約": None,
                    "離峰契約": None,
                },
                "new": {
                    "經常契約": None,
                    "半尖峰契約/非夏月契約": None,
                    "週六半尖峰契約": None,
                    "離峰契約": None,
                },
            },
            "計費類別": None,
            "行業別": None,
            # "加權平均尖峰電價": 7.14,
            # "加權平均離峰電價": 2.41,
            # "加權平均電價": 4.06,
            "夏月天數": None,
            "非夏月天數": None,
            "夏月最高電價": None,
            "夏月最低電價": None,
            "非夏月最高電價": None,
            "非夏月最低電價": None,
            "電費調整係數": None,
        },
        "電價試算": {
            "原始": {  # baseline（未用儲能）
                "年用電度數": None,
                "年基本電費": None,
                "年流動電費": None,
                "年總電費": None,
                "年平均電費": None,
            },
            "應用儲能": {  # with storage（契約調整/充放電調度後）
                "年用電度數": None,
                "年基本電費": None,
                "年流動電費": None,
                "年總電費": None,
                "年平均電費": None,
            },
        },
        "降低契約容量": {
            "年節省基本電費": None,
            "每kW契約容量費用": None,
            "年契約容量費用": None,
            "降契約容量比例": None,
        },
        "儲能系統": {
            "單台 PCS 標稱功率": 125,
            "單台 儲能容量": 261,
            "台數": None,
            "PCS 標稱功率": None,
            "儲能容量": None,
            "C-Rate": None,
            "電能損失率(Round Trip)": 10,
            "儲能健康度年衰減率": 2,
            "SOC上限": 95,
            "SOC下限": 5,
            "實際建置容量": None,
            "每日最大循環次數": 2,
        },
        "負載模擬參數": {"夏月每日可轉移度數": None, "非夏月每日可轉移度數": None},
        "自定義收益(年收/省)": {
            "自定義收益": 0,  # 這是用戶自定義的收益，可能是其他市場或是其他收入來源
        },
        "建置成本(第0年繳)": {
            "每單位建置成本": 10000,
            "儲能設備": None,
            "儲能設備安裝": 0,
            "高壓設備": 0,
            "高壓設備安裝": 0,
            "設計/監造/簽證費用": 0,
            "EMS": None,
            "其他": 0,
        },
        "維運成本(年繳)": {
            "土地年租金": 0,
            "保險費率": 1.5,
            "案場維運成本": None,
            "EMS維運成本": None,
            "電力交易雲端平台": None,
            "其他固定成本": 5000,
        },
        "系統服務單價": {
            "EMS系統含硬體_kWh": 750,
            # "EMS壓降補償功能_kWh": 0,
            # "EMS系統即時備轉_kWh": 250,
            # "太陽能監控功能_kWh": 650,
            "EMS壓降補償功能_kWh": None,
            "EMS系統即時備轉_kWh": None,
            "太陽能監控功能_kWh": None,
            "電力交易雲端使用費_MW": 50000,
            "電力交易之場域通訊使用_年": 100000,
            "EMS保固維運費用_年_%": 10,
            "案場維運費用_年_%": 1,
        },
        "聚合分潤": {"聚合分潤比例": 10},
        "可套利天數": {
            # "全年週一至週五天數": 251,
            "可能超約天數": 0,
            "歲修天數": 15,
            # "可套利天數": None,
        },
        "即時備轉": {
            "投標容量": None,
            "1級效能價格": 100,
            "容量價格": 179,
            "得標容量比例": 100,
            "折扣比例": 100,  # 這是為了負載波動所設計的參數 或是 針對成功率
            "每月觸發次數": 1,
            "日前電能邊際價格": 6000,
            "保留比例": None,  # 保留比例跟保留容量的機制跟單位要在考慮
            "保留容量": None,
        },
        "可參與輔助服務時數": {
            # "大於1000kW比例": 100.0,
            "不可投標天數": None,
            # "可參與輔助服務時數": None,
            # "可參與輔助服務天數": None,
            # "日選時段同時參與天數": None,
            # "僅參與輔助服務天數": None,
            # "聚合後收益折扣": 75.5448565022421
        },
        "日選時段型": {
            "執行方案": None,
            "抑低契約容量": None,
            "開始時段": None,
            "結束時段": None,
            "執行時數": None,
            "流動電費扣減費率": None,
            "當日執行率": 100,
            "扣減比率": 120,
            "5月-10月天數": 132,
            "5月-10月可參與天數": None,
        },
        "再生能源義務用戶": {
            "義務裝置容量": None,
            "義務裝置容量比例": 10,
            "早鳥抵減比例": 0,
            "既設抵減比例": 0,
        },
        "融資成本": {"貸款成數": 70, "利息費用": 2, "攤還年限": 7},
    }


### 更新手動曲線
def scale_15min_by_hour(df_15min: pd.DataFrame, hourly_dicts: list) -> pd.DataFrame:
    """
    依『調整後的小時平均負載』，將原始 15 分鐘資料等比例縮放，輸出調整後的 15 分鐘負載。

    Parameters
    ----------
    df_15min : pd.DataFrame
        必含欄位 ['ID','is_summer','weekday','variable','value']，
        其中 variable 為 'HH:MM'（00:00, 00:15, …）。
    hourly_dicts : list
        像 [{'hour':'00:00','summerMonday': …, 'nonSummerTuesday': …}, …] 的 list-of-dict。

    Returns
    -------
    pd.DataFrame
        在原 DataFrame 基礎上多一欄 'scaled_value'（調整後的 15 分鐘負載）。
    """

    # ---------- 1) 將 hourly_dicts 轉成長格式 ----------
    df_hour_wide = pd.DataFrame(hourly_dicts)
    df_hour_long = df_hour_wide.melt(
        id_vars="hour", var_name="season_weekday", value_name="target_avg"
    )
    # 拆 season 與 weekday
    df_hour_long["is_summer"] = (
        df_hour_long["season_weekday"].str.startswith("summer").astype(int)
    )
    df_hour_long["weekday"] = df_hour_long["season_weekday"].str.replace(
        r"^(summer|nonSummer)", "", regex=True
    )
    df_hour_long["hour"] = df_hour_long["hour"].str.slice(0, 2).astype(int)
    df_hour_target = df_hour_long[["is_summer", "weekday", "hour", "target_avg"]]

    # ---------- 2) 加入 hour 欄位到原始 15 分鐘資料 ----------
    df_15min = df_15min.copy()
    df_15min["hour"] = df_15min["variable"].str.slice(0, 2).astype(int)

    # ---------- 3) 計算原始小時平均 ----------
    orig_avg = (
        df_15min.groupby(["is_summer", "weekday", "hour"])["value"]
        .mean()
        .reset_index()
        .rename(columns={"value": "orig_avg"})
    )

    # ---------- 4) 合併目標與原始平均、算倍率 ----------
    scale_df = orig_avg.merge(
        df_hour_target, on=["is_summer", "weekday", "hour"], how="inner"
    )
    scale_df["scale_factor"] = scale_df["target_avg"] / scale_df["orig_avg"]

    # ---------- 5) 把倍率併回 15 分鐘資料並計算縮放後值 ----------
    df_scaled = df_15min.merge(
        scale_df[["is_summer", "weekday", "hour", "scale_factor"]],
        on=["is_summer", "weekday", "hour"],
        how="left",
    )
    df_scaled["scaled_value"] = df_scaled["value"] * df_scaled["scale_factor"]
    df_scaled["scaled_value"] = df_scaled["scaled_value"].round()

    # 如果有無匹配到的組別，維持原值
    df_scaled["scaled_value"].fillna(df_scaled["value"], inplace=True)
    df_scaled["value"] = df_scaled["scaled_value"]
    df_scaled.drop(columns=["hour", "scaled_value", "scale_factor"], inplace=True)

    return df_scaled


# 將 json_result 轉換成 DataFrame 格式
def ami_15min_json_to_df(json_data):
    """
    將 JSON 格式的 15分鐘資料轉換成 DataFrame 格式

    Parameters:
    -----------
    json_data : list
        由 convert_ami_to_json_15min 函數產生的 JSON 資料

    Returns:
    --------
    DataFrame : 包含 is_summer, weekday, variable, value 欄位的 DataFrame
    """

    # 定義有效的星期名稱
    valid_weekdays = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    # 收集所有資料
    data_rows = []

    for time_record in json_data:
        time_value = time_record["time"]

        # 遍歷除了 time 以外的所有欄位
        for key, value in time_record.items():
            if key != "time":
                # 解析 key，例如 'summerMonday' -> is_summer=1, weekday='Monday'
                if key.startswith("summer"):
                    is_summer = 1
                    weekday = key[6:]  # 移除 'summer' 前綴
                elif key.startswith("nonSummer"):
                    is_summer = 0
                    weekday = key[9:]  # 移除 'nonSummer' 前綴
                else:
                    continue  # 跳過無法識別的欄位

                # 確保 weekday 是有效的
                if weekday in valid_weekdays:
                    data_rows.append(
                        {
                            "is_summer": is_summer,
                            "weekday": weekday,
                            "variable": time_value,
                            "value": float(value) if value is not None else 0.0,
                        }
                    )

    # 轉換成 DataFrame
    df = pd.DataFrame(data_rows)

    return df


# 正規化AMI資料
# 鉤稽時間電價，標註最高最低價等
def norm_ami(df_ami, df_tou_2025, 計費類別):
    df_tou = df_tou_2025[df_tou_2025["type"] == 計費類別].copy()
    # df_ami = df_ami_raw[df_ami_raw["ID"] == ID].copy()
    df_ami["weekday2"] = df_ami["weekday"]
    df_ami["season"] = df_ami["is_summer"].map({1: "summer", 0: "not_summer"})
    df_ami["weekday"] = np.where(
        df_ami["weekday"].isin(["Saturday"]),
        "sat",
        np.where(df_ami["weekday"].isin(["Sunday"]), "sun", "week"),
    )

    df_tou["datetime"] = pd.to_datetime(df_tou["datetime"])
    df_tou["variable"] = df_tou["datetime"].dt.strftime("%H:%M")

    df_ami = df_ami.merge(
        df_tou[["tou", "tou_tag", "season", "weekday", "variable"]],
        how="left",
        on=["season", "weekday", "variable"],
    )
    df_ami.rename(columns={"variable": "timestamp", "value": "load_kw"}, inplace=True)

    # 找出每個 group (season + weekday2) 的 max/min
    group = df_ami.groupby(["season", "weekday2"])["tou"]
    df_ami["tou_max"] = group.transform("max")
    df_ami["tou_min"] = group.transform("min")

    # 判斷分類
    def classify_tou(row):
        if row["tou"] == row["tou_max"]:
            return "high"
        elif row["tou"] == row["tou_min"]:
            return "low"
        else:
            return "other"

    df_ami["tou_level"] = df_ami.apply(classify_tou, axis=1)

    # 移除中間欄位（如不需要）
    df_ami.drop(columns=["tou_max", "tou_min"], inplace=True)

    return df_ami.copy()


def get_contract_capacity_parameter(
    tou_program, price_dict, contract_capacities, season
):
    """
    根據電價方案和季節獲取契約容量參數
    """

    # 欄位對應表：使用者輸入名稱 → 依電價型態映射的實際欄位
    field_alias_mapping = {
        "半尖峰契約/非夏月契約": {
            "二段式": "非夏月契約",
            "批次": "非夏月契約",
            "三段式": "半尖峰契約",
        },
    }

    def resolve_contract_key(input_key, tou_program):
        if input_key not in field_alias_mapping:
            return input_key
        if "二段式" in tou_program:
            return field_alias_mapping[input_key]["二段式"]
        elif "三段式" in tou_program:
            return field_alias_mapping[input_key]["三段式"]
        elif "批次" in tou_program:
            return field_alias_mapping[input_key]["批次"]
        else:
            return input_key

    plan_info = price_dict.get((tou_program, season))
    if not plan_info:
        raise ValueError(f"找不到電價方案：{tou_program} ({season})")
    unit_prices = plan_info.get("基本電費", {})

    # 統一轉換後的契約容量字典
    contracts = {}
    for k, v in contract_capacities.items():
        resolved_key = resolve_contract_key(k, tou_program)
        contracts[resolved_key] = contracts.get(resolved_key, 0) + v

    # 主要契約容量
    ec = contracts.get("經常契約", 0)
    # 次要契約容量：二段式為非夏月契約，三段式為半尖峰契約
    sec_key = resolve_contract_key("半尖峰契約/非夏月契約", tou_program)
    sec_cap = contracts.get(sec_key, 0)
    wk_sat = contracts.get("週六半尖峰契約", 0)
    offp = contracts.get("離峰契約", 0)

    # 單價
    p_ec = unit_prices.get("經常契約", 0)
    p_sec = unit_prices.get(sec_key, 0)
    p_sat = unit_prices.get("週六半尖峰契約", 0)
    p_off = unit_prices.get("離峰契約", 0)

    if any(keyword in tou_program for keyword in ["二段式", "批次"]):
        # 非夏月尖峰，是經常性 + 非夏月契約
        if season == "summer":
            contract_data = {
                "is_summer": [1] * 4,
                "tou_tag": ["尖峰", "半尖峰", "週六半尖峰", "離峰"],
                "capacity_kw": [
                    ec,
                    ec + sec_cap,
                    ec + sec_cap + wk_sat,
                    ec + sec_cap + wk_sat + offp,
                ],
                "unit_price": [p_ec, p_sec, p_sat, p_off],
            }
        else:
            contract_data = {
                "is_summer": [0] * 4,
                "tou_tag": ["尖峰", "半尖峰", "週六半尖峰", "離峰"],
                "capacity_kw": [
                    ec + sec_cap,
                    ec + sec_cap,
                    ec + sec_cap + wk_sat,
                    ec + sec_cap + wk_sat + offp,
                ],
                "unit_price": [p_ec, p_sec, p_sat, p_off],
            }

    else:
        contract_data = {
            "is_summer": [1 if season == "summer" else 0] * 4,
            "tou_tag": ["尖峰", "半尖峰", "週六半尖峰", "離峰"],
            "capacity_kw": [
                ec,
                ec + sec_cap,
                ec + sec_cap + wk_sat,
                ec + sec_cap + wk_sat + offp,
            ],
            "unit_price": [p_ec, p_sec, p_sat, p_off],
        }

    return pd.DataFrame(contract_data)


def calculate_annual_basic_fee(
    rate_table,
    tou_program,
    contract_capacities,
    number_of_summer_months=None,
    number_of_not_summer_months=None,
):
    """
    根據電價表與契約容量，依月份計算夏月與非夏月的基本電費，並支援名稱對應與折扣邏輯。

    :param rate_table: dict，完整的電價表資料
    :param tou_program: str，電價方案名稱（如 "高壓三段式電價"）
    :param contract_capacities: dict，用戶輸入的契約容量，例如：
        {
            "經常契約": 100,
            "半尖峰契約/非夏月契約": 50,
            "週六半尖峰契約": 20,
            "離峰契約": 80
        }
    :return: dict，夏月、非夏月與年總基本電費（以整月計）
    """

    # 若為簡易型，基本電費僅按戶計收
    if "簡易" in tou_program:
        base_fee = rate_table[(tou_program, "summer")]["基本電費"]["按戶計收"] * 12
        return {"年總基本電費": round(base_fee, 2)}

    # 沒有給夏月跟非夏月個數時，用電價方案判斷夏月月數
    # 模擬負載：12月自動判斷分割
    # AMI負載：依據資料去計算
    if number_of_summer_months is None or number_of_not_summer_months is None:
        number_of_summer_months = (
            5 if "高壓" in tou_program or "特高壓" in tou_program else 4
        )
        number_of_not_summer_months = 12 - number_of_summer_months

    # 欄位對應表：使用者輸入名稱 → 依電價型態映射的實際欄位
    field_alias_mapping = {
        "半尖峰契約/非夏月契約": {
            "二段式": "非夏月契約",
            "三段式": "半尖峰契約",
            "批次": "非夏月契約",
        },
    }

    def resolve_contract_key(input_key, tou_program):
        if input_key not in field_alias_mapping:
            return input_key
        if "二段式" in tou_program:
            return field_alias_mapping[input_key]["二段式"]
        elif "三段式" in tou_program:
            return field_alias_mapping[input_key]["三段式"]
        elif "批次" in tou_program:
            return field_alias_mapping[input_key]["批次"]
        else:
            return input_key

    def _monthly_fee(season):
        plan_info = rate_table.get((tou_program, season))
        if not plan_info:
            raise ValueError(f"找不到電價方案：{tou_program} ({season})")
        unit_prices = plan_info.get("基本電費", {})

        # 統一轉換後的契約容量字典
        contracts = {}
        for k, v in contract_capacities.items():
            resolved_key = resolve_contract_key(k, tou_program)
            contracts[resolved_key] = contracts.get(resolved_key, 0) + v

        # 主要契約容量
        ec = contracts.get("經常契約", 0)
        # 次要契約容量：二段式為非夏月契約，三段式為半尖峰契約
        sec_key = resolve_contract_key("半尖峰契約/非夏月契約", tou_program)
        sec_cap = contracts.get(sec_key, 0)
        wk_sat = contracts.get("週六半尖峰契約", 0)
        offp = contracts.get("離峰契約", 0)

        # 單價
        p_ec = unit_prices.get("經常契約", 0)
        p_sec = unit_prices.get(sec_key, 0)
        p_sat = unit_prices.get("週六半尖峰契約", 0)
        p_off = unit_prices.get("離峰契約", 0)

        # 折扣公式
        # 計算折扣後的容量
        discount_base = (wk_sat + offp) - (ec + sec_cap) * 0.5
        discount_fee = max(0, discount_base) * max(p_sat, p_off)

        # 計算單月金額
        fee = ec * p_ec + sec_cap * p_sec + discount_fee
        return fee

    # 計算夏月與非夏月單月電費
    summer_monthly_fee = _monthly_fee("summer")
    not_summer_monthly_fee = _monthly_fee("not_summer")

    summer_fee = summer_monthly_fee * number_of_summer_months
    not_summer_fee = not_summer_monthly_fee * number_of_not_summer_months
    total_fee = summer_fee + not_summer_fee

    return {
        # "夏月基本電費（月計)": round(summer_fee, 2),
        # "非夏月基本電費（月計)": round(not_summer_fee, 2),
        "年總基本電費": round(total_fee, 2)
    }


def calculate_over_capacity_penalties(
    df_segment, tou_program, price_dict, contract_capacity
):
    """
    計算超約費用的整合函數

    參數:
    df_segment: DataFrame - 包含 is_summer, tou_tag, over_capacity_kw 欄位
    tou_program: str - 電價方案名稱 (如 '高壓三段式電價')
    price_dict: dict - 電價資料字典
    contract_capacity: dict - 契約容量設定

    回傳:
    dict - 包含夏月和非夏月的超約費用
    """

    # 步驟1: 按夏月/非夏月和時段分組，取各組最大超約量
    df_segment2 = (
        df_segment.groupby(["is_summer", "tou_tag"])
        .agg({"over_capacity_kw": "max"})
        .reset_index()
    )

    # 步驟2: 獲取契約容量參數並合併
    df_contract_summer = get_contract_capacity_parameter(
        tou_program, price_dict, contract_capacity, "summer"
    )
    df_contract_not_summer = get_contract_capacity_parameter(
        tou_program, price_dict, contract_capacity, "not_summer"
    )
    df_contract2 = pd.concat([df_contract_summer, df_contract_not_summer]).reset_index(
        drop=True
    )

    # 步驟3: 合併契約容量資料
    df_segment3 = df_segment2.merge(
        df_contract2, on=["is_summer", "tou_tag"], how="left"
    )

    # 步驟4: 調整超約容量 - 按優先順序分配
    df = df_segment3.copy()

    # 定義優先順序
    priority = {"尖峰": 1, "半尖峰": 2, "週六半尖峰": 3, "離峰": 4}
    df["priority"] = df["tou_tag"].map(priority)

    # 處理每個季節分開計算
    def adjust_over_capacity(group):
        used_capacity = 0
        adjusted = []

        # 按照優先順序排序
        group = group.sort_values("priority")

        for _, row in group.iterrows():
            oc = max(row["over_capacity_kw"] - used_capacity, 0)
            adjusted.append(oc)
            # 更新已佔用的超約容量
            used_capacity += oc

        group["adj_over_capacity_kw"] = adjusted
        return group

    df = (
        df.groupby(["is_summer"], group_keys=True)
        .apply(adjust_over_capacity, include_groups=False)
        .reset_index(level=["is_summer"])
    )

    # 步驟5: 計算超約費用
    over_col = "adj_over_capacity_kw"

    # 10% 門檻 (每列以該列的契約容量為準)
    threshold = 0.10 * df["capacity_kw"]

    # 分攤超約量：10% 以內與超過 10% 的兩段
    df["over_within_10pct_kw"] = np.minimum(df[over_col], threshold).clip(lower=0)
    df["over_above_10pct_kw"] = (df[over_col] - threshold).clip(lower=0)

    # 計算每列的超約費用
    # 10%以內 → 2倍單價；超過10% → 3倍單價
    df["overage_fee"] = (
        2.0 * df["unit_price"] * df["over_within_10pct_kw"]
        + 3.0 * df["unit_price"] * df["over_above_10pct_kw"]
    )

    # 步驟6: 按季節匯總超約費用
    monthly_fee = df.groupby(["is_summer"], as_index=False).agg(
        total_overage_fee=("overage_fee", "sum")
    )

    # print(monthly_fee)

    # 步驟7: 計算年度超約費用
    # 確定夏月和非夏月的月數
    number_of_summer_months = (
        5 if "高壓" in tou_program or "特高壓" in tou_program else 4
    )
    number_of_not_summer_months = 12 - number_of_summer_months

    # 轉換為字典格式回傳
    result = {}
    for _, row in monthly_fee.iterrows():
        if row["is_summer"] == 1:
            result["summer_monthly_fee"] = row["total_overage_fee"]
            result["summer_annual_capacity_penalty"] = (
                row["total_overage_fee"] * number_of_summer_months
            )
        else:
            result["not_summer_monthly_fee"] = row["total_overage_fee"]
            result["not_summer_annual_capacity_penalty"] = (
                row["total_overage_fee"] * number_of_not_summer_months
            )

    # 計算總年度費用
    # result['total_annual_fee'] = result.get('summer_annual_fee', 0) + result.get('not_summer_annual_fee', 0)

    # # 也回傳詳細的計算過程供參考
    # result['detail_df'] = df
    # result['monthly_summary'] = monthly_fee

    return result


# 計算15年的年度罰金
def calculate_annual_capacity_penalties(
    usable_kWh_list, max_summer_over, max_not_summer_over, result, rtt_loss_rate
):
    """
    計算15年的年度罰金

    參數:
    usable_kWh_list: 15年儲能可用電量列表
    max_summer_over: 夏月最大超約量
    max_not_summer_over: 非夏月最大超約量
    result: 包含罰金資訊的字典

    回傳:
    list: 15年的年度罰金列表
    """
    annual_penalties = []

    # 從result取得年度罰金
    summer_annual_penalty = result["summer_annual_capacity_penalty"]
    not_summer_annual_penalty = result["not_summer_annual_capacity_penalty"]

    for i, available_kWh in enumerate(usable_kWh_list):
        year = i + 1
        annual_penalty = 0

        available_kWh = available_kWh * np.sqrt(1 - rtt_loss_rate)
        # 判斷是否能處理夏月超約
        can_handle_summer = available_kWh >= max_summer_over
        # 判斷是否能處理非夏月超約
        can_handle_not_summer = available_kWh >= max_not_summer_over

        # 如果不能處理，就要付罰金
        if not can_handle_summer:
            annual_penalty += summer_annual_penalty
        if not can_handle_not_summer:
            annual_penalty += not_summer_annual_penalty

        annual_penalties.append(float(annual_penalty))

        # 列印詳細資訊
        status = []
        if can_handle_summer and can_handle_not_summer:
            status.append("夏月、非夏月都可處理")
        elif can_handle_summer and not can_handle_not_summer:
            status.append("只能處理夏月")
        elif not can_handle_summer and can_handle_not_summer:
            status.append("只能處理非夏月")
        else:
            status.append("夏月、非夏月都無法處理")

        # print(f"第 {year:2d} 年: 可用電量 {available_kWh:6.0f} kWh, {status[0]}, 年度罰金: {annual_penalty:,.0f} 元")

    return annual_penalties


# 計算年度電費
def calculator_annual_cost(
    df_ami,
    tou_program,
    contract_capacity_old,
    contract_capacity_new,
    tariff_adjust_factor,
):
    """計算年度電費，包含流動電費與基本電費。
    df_ami: DataFrame, 包含AMI資料，需有欄位 ['is_summer', 'weekday', 'timestamp', 'load_kw', 'tou']
    tou_program: str, 電價方案名稱，例如 '高壓三段式電價' 或 '表燈標準型二段式電價'
    contract_capacity: float, 契約容量，單位為 kW
    """

    # Step 1: 計算流動電費
    df_ami2 = (
        df_ami.groupby(["is_summer", "weekday", "timestamp"])
        .agg({"load_kw": "mean", "tou": "mean"})
        .reset_index()
    )
    df_ami2["fee"] = df_ami2["load_kw"] * df_ami2["tou"]

    df_ami3 = (
        df_ami2.groupby(["is_summer", "weekday"])
        .agg({"fee": "sum", "load_kw": "sum"})
        .reset_index()
    )
    df_ami3["fee"] = df_ami3["fee"] / 4
    df_ami3["load_kw"] = df_ami3["load_kw"] / 4

    # 代表日天數，高壓，以2025年為例
    df_representative_days_hv = pd.DataFrame(
        [
            {"is_summer": 0, "weekday": "sat", "day_count": 29.0},
            {"is_summer": 0, "weekday": "sun", "day_count": 39.0},
            {"is_summer": 0, "weekday": "week", "day_count": 144.0},
            {"is_summer": 1, "weekday": "sat", "day_count": 21.0},
            {"is_summer": 1, "weekday": "sun", "day_count": 25.0},
            {"is_summer": 1, "weekday": "week", "day_count": 107.0},
        ]
    )

    # 低壓
    df_representative_days_lv = pd.DataFrame(
        [
            {"is_summer": 0, "weekday": "sat", "day_count": 33.0},
            {"is_summer": 0, "weekday": "sun", "day_count": 46.0},
            {"is_summer": 0, "weekday": "week", "day_count": 164.0},
            {"is_summer": 1, "weekday": "sat", "day_count": 17.0},
            {"is_summer": 1, "weekday": "sun", "day_count": 18.0},
            {"is_summer": 1, "weekday": "week", "day_count": 87.0},
        ]
    )

    if "高壓" in tou_program:
        df_annual_cost = df_ami3.merge(
            df_representative_days_hv, on=["is_summer", "weekday"], how="left"
        )
    else:
        df_annual_cost = df_ami3.merge(
            df_representative_days_lv, on=["is_summer", "weekday"], how="left"
        )

    df_annual_cost["annual_fee"] = df_annual_cost["fee"] * df_annual_cost["day_count"]
    df_annual_cost["load_kw"] = df_annual_cost["load_kw"] * df_annual_cost["day_count"]

    total_annual_fee = df_annual_cost["annual_fee"].sum().round()
    total_annual_kwh = df_annual_cost["load_kw"].sum().round()

    if "簡易" in tou_program:
        if total_annual_kwh > 2000:
            total_annual_fee = total_annual_fee + (total_annual_kwh - 2000) * 1.02

    # print(f"年度用電量總計: {total_annual_kwh} kWh")
    # print(f"年度流動電費總計: {total_annual_fee} 元")
    # print(f"年度流動電費平均: {total_annual_fee / total_annual_kwh:.2f} 元/kWh")

    # Step 2: 計算基本電費
    # if '高壓' in tou_program:
    #     number_of_summer_months = 5
    # else:
    #     number_of_summer_months = 4

    # if "簡易" in tou_program:
    #     cost_Contract_Capacity =  price_dict[(tou_program, 'summer')]['基本電費']['按戶計收']*12
    # else:
    #     cost_Contract_Capacity = (price_dict[(tou_program, 'summer')]['基本電費']['經常契約']* number_of_summer_months + price_dict[(tou_program, 'not_summer')]['基本電費']['經常契約'] * (12 - number_of_summer_months)) * contract_capacity

    # cost_Contract_Capacity = round(cost_Contract_Capacity)

    result = calculate_annual_basic_fee(
        rate_table=price_dict,
        tou_program=tou_program,
        contract_capacities=contract_capacity_old,
    )

    cost_Contract_Capacity = result["年總基本電費"]

    result_new = calculate_annual_basic_fee(
        rate_table=price_dict,
        tou_program=tou_program,
        contract_capacities=contract_capacity_new,
    )

    cost_Contract_Capacity_new = result_new["年總基本電費"]

    # print(f"年度基本電費總計: {cost_Contract_Capacity} 元")
    # Step 3: 電價調整係數
    total_annual_fee = round(total_annual_fee * tariff_adjust_factor)
    cost_Contract_Capacity = round(cost_Contract_Capacity * tariff_adjust_factor)
    cost_Contract_Capacity_new = round(
        cost_Contract_Capacity_new * tariff_adjust_factor
    )

    annual_cost_summary = {
        "年用電度數(度)": total_annual_kwh,
        "年基本電費(元)": cost_Contract_Capacity,
        "年流動電費(元)": total_annual_fee,
        "年總電費(元)": total_annual_fee + cost_Contract_Capacity,
        "年平均電費(元/度)": round(
            (total_annual_fee + cost_Contract_Capacity) / total_annual_kwh, 2
        ),
        "年節省基本電費_契約調整(元)": round(
            cost_Contract_Capacity - cost_Contract_Capacity_new
        ),
    }

    return annual_cost_summary


def calculator_annual_cost_ami_365(
    tou_program,
    df_ami,
    df_tou_2025,
    price_dict,
    contract_capacity_old,
    tariff_adjust_factor,
):
    """
    計算 AMI 365 天的年費用

    Parameters:
    -----------
    tou_program : str
        電價方案名稱，用於判斷夏月期間
    df_ami : DataFrame
        AMI 資料，包含日期、時間、負載等資訊，e.g.[datetime	value, time, is_summer, weekday]
    df_tou_2025 : DataFrame
        2025 年的時間電價資料，個電價方案的六天代表日，包含季節、星期、時間等, e.g.[type,datetime,tou,tou_tag,season,weekday, date]
    price_dict : dict
        電價表，包含各電價方案的基本電費和超約費用
    contract_capacity_old : dict
        舊的契約容量設定，包含經常契約、半尖峰契ity/非夏月契約、週六半尖峰契約和離峰契約
    tariff_adjust_factor : float
        電價調整係數，用於調整最終計算結果
    Returns:
    --------
    dict : 年費用摘要，包含年用電度數、年基本電費、年流動電費、年總電費和年平均電費
    以及超約費用的詳細計算結果

    """

    # 1. 準備 AMI 資料，整合時間電價資訊
    df_ami["weekday2"] = df_ami["weekday"]
    df_ami["season"] = df_ami["is_summer"].map({1: "summer", 0: "not_summer"})
    df_ami["weekday"] = np.where(
        df_ami["weekday"].isin(["Saturday"]),
        "sat",
        np.where(df_ami["weekday"].isin(["Sunday", "Holiday"]), "sun", "week"),
    )

    df_tou = df_tou_2025[df_tou_2025["type"] == tou_program].copy()

    df_tou["datetime"] = pd.to_datetime(df_tou["datetime"])
    df_tou["time"] = df_tou["datetime"].dt.strftime("%H:%M")

    df_ami = df_ami.merge(
        df_tou[["tou", "tou_tag", "season", "weekday", "time"]],
        how="left",
        on=["season", "weekday", "time"],
    )
    df_ami.rename(columns={"time": "timestamp", "value": "load_kw"}, inplace=True)

    # 取出起始跟結束的日期 df_ami_long
    start_date = df_ami["datetime"].iloc[0].date().strftime("%Y-%m-%d")
    end_date = df_ami["datetime"].iloc[-1].date().strftime("%Y-%m-%d")
    # print(f"AMI 資料起始日期: {start_date}, 結束日期: {end_date}")

    # 計算夏月跟非夏月的月數
    # print(df_ami)
    number_of_summer_months = round(
        df_ami[df_ami["is_summer"] == 1].shape[0] / (30.4 * 96), 2
    )
    number_of_not_summer_months = round(
        df_ami[df_ami["is_summer"] == 0].shape[0] / (30.4 * 96), 2
    )
    print(
        f"[debug] 夏月月數: {number_of_summer_months}, 非夏月月數: {number_of_not_summer_months}"
    )

    # 2. 計算基本電費及超約費用
    result = calculate_annual_basic_fee(
        rate_table=price_dict,
        tou_program=tou_program,
        contract_capacities=contract_capacity_old,
        number_of_summer_months=number_of_summer_months,
        number_of_not_summer_months=number_of_not_summer_months,
    )

    print(f"[debug] 基本電費計算結果: {result}")

    # 計算流動電費
    total_annual_fee = ((df_ami["load_kw"] * df_ami["tou"]).sum() / 4).round()
    total_annual_kwh = df_ami["load_kw"].sum() / 4
    cost_Contract_Capacity = result["年總基本電費"]

    if "簡易" in tou_program:
        if total_annual_kwh > 2000:
            total_annual_fee = total_annual_fee + (total_annual_kwh - 2000) * 1.02

    # Step 3: 電價調整係數
    total_annual_fee = round(total_annual_fee * tariff_adjust_factor)
    cost_Contract_Capacity = round(cost_Contract_Capacity * tariff_adjust_factor)

    annual_cost_summary = {
        "資料天數": len(df_ami["datetime"].dt.date.unique()),
        "起始日期": start_date,
        "結束日期": end_date,
        "年用電度數(度)": total_annual_kwh,
        "年基本電費(元)": cost_Contract_Capacity,
        "年流動電費(元)": total_annual_fee,
        "年總電費(元)": total_annual_fee + cost_Contract_Capacity,
        "年平均電費(元/度)": round(
            (total_annual_fee + cost_Contract_Capacity) / total_annual_kwh, 2
        ),
    }

    # 簡易是按戶計算的，所以不需要超約費用
    if "簡易" in tou_program:
        annual_cost_summary["年超約費用(元)"] = 0
        annual_cost_summary["年超約天數(天)"] = 0
        annual_cost_summary["日平均超約度數(kWh)"] = 0
        return annual_cost_summary

    # Step 4: 計算超約費用
    df_ami2 = (
        df_ami.groupby(["is_summer", df_ami["datetime"].dt.month, "tou_tag"])
        .agg({"load_kw": "max"})
        .reset_index()
    )
    df_ami2.columns = ["is_summer", "month", "tou_tag", "max_load_kw"]

    df_contract = pd.concat(
        [
            get_contract_capacity_parameter(
                tou_program, price_dict, contract_capacity_old, "summer"
            ),
            get_contract_capacity_parameter(
                tou_program, price_dict, contract_capacity_old, "not_summer"
            ),
        ]
    ).reset_index(drop=True)

    # print(f"[debug] 契約容量參數：{df_contract}")

    df_ami3 = df_ami2.merge(df_contract, how="left", on=["is_summer", "tou_tag"])
    df_ami3["over_capacity_kw"] = df_ami3["max_load_kw"] - df_ami3["capacity_kw"]
    df_ami3["over_capacity_kw"] = df_ami3["over_capacity_kw"].clip(lower=0)

    df = df_ami3.copy()

    # 定義優先順序
    priority = {"尖峰": 1, "半尖峰": 2, "週六半尖峰": 3, "離峰": 4}

    # 如果 tou_tag 在 priority 中，轉成排序值
    df["priority"] = df["tou_tag"].map(priority)

    # 處理每個月份 & is_summer 分開計算
    def adjust_over_capacity(group):
        used_capacity = 0
        adjusted = []

        # 按照優先順序排序
        group = group.sort_values("priority")

        for _, row in group.iterrows():
            oc = max(row["over_capacity_kw"] - used_capacity, 0)
            adjusted.append(oc)
            # 更新已佔用的超約容量
            used_capacity += oc

        group["adj_over_capacity_kw"] = adjusted
        return group

    df = (
        df.groupby(["is_summer", "month"], group_keys=True)
        .apply(adjust_over_capacity, include_groups=False)
        .reset_index(level=["is_summer", "month"])
    )

    over_col = "adj_over_capacity_kw"

    # 10% 門檻 (每列以該列的契約容量為準)
    threshold = 0.10 * df["capacity_kw"]

    # 分攤超約量：10% 以內與超過 10% 的兩段
    df["over_within_10pct_kw"] = np.minimum(df[over_col], threshold).clip(lower=0)
    df["over_above_10pct_kw"] = (df[over_col] - threshold).clip(lower=0)

    # 計算每列的超約費用
    # 10%以內 → 2倍單價；超過10% → 3倍單價
    df["overage_fee"] = (
        2.0 * df["unit_price"] * df["over_within_10pct_kw"]
        + 3.0 * df["unit_price"] * df["over_above_10pct_kw"]
    )

    # 依 is_summer, month 匯總每月超約費用（你可依需求保留細項）
    monthly_fee = df.groupby(["is_summer", "month"], as_index=False).agg(
        total_overage_fee=("overage_fee", "sum")
    )

    # 如果也想看每月各時段明細，可額外輸出：
    detail_fee = df[
        [
            "is_summer",
            "month",
            "tou_tag",
            over_col,
            "over_within_10pct_kw",
            "over_above_10pct_kw",
            "overage_fee",
        ]
    ]
    # print(f"[debug] 每月超約費用明細：\n{detail_fee}")
    annual_cost_summary["最高超約需量(kW)"] = detail_fee["adj_over_capacity_kw"].max()

    # 主結果：每月總超約費用
    # 處理 5, 10月一半夏月，一半非夏月的問題
    monthly_fee2 = (
        monthly_fee.groupby("month")
        .agg(total_overage_fee=("total_overage_fee", "mean"))
        .reset_index()
    )

    # 將每月超約費用加總到年費用中
    annual_cost_summary["年超約費用(元)"] = round(
        monthly_fee2["total_overage_fee"].sum().round() * tariff_adjust_factor
    )
    annual_cost_summary["年總電費(元)"] += annual_cost_summary["年超約費用(元)"]
    annual_cost_summary["年平均電費(元/度)"] = round(
        annual_cost_summary["年總電費(元)"] / total_annual_kwh, 2
    )

    # Step 5：計算超約天數跟度數
    if annual_cost_summary["年超約費用(元)"] > 0:
        df_ami_contract = df_ami.merge(
            df_contract, how="left", on=["is_summer", "tou_tag"]
        )
        df_ami_contract["over_contract_kw"] = (
            df_ami_contract["load_kw"] - df_ami_contract["capacity_kw"]
        )
        df_ami_contract["over_contract_kw"] = df_ami_contract["over_contract_kw"].clip(
            lower=0
        )
        df_ami_contract2 = df_ami_contract[df_ami_contract["over_contract_kw"] > 0]

        df_ami_contract3 = (
            df_ami_contract2.groupby(df_ami_contract2["datetime"].dt.date)
            .agg({"over_contract_kw": "sum"})
            .reset_index()
        )
        df_ami_contract3["over_contract_kwh"] = (
            df_ami_contract3["over_contract_kw"] / 4
        ).round()

        annual_cost_summary["年超約天數(天)"] = df_ami_contract2[
            "datetime"
        ].dt.date.nunique()
        annual_cost_summary["日平均超約度數(kWh)"] = (
            df_ami_contract3["over_contract_kwh"].mean().round()
        )

    else:
        annual_cost_summary["年超約天數(天)"] = 0
        annual_cost_summary["日平均超約度數(kWh)"] = 0

    annual_cost_summary["年平均電費(元/度)"] = float(
        annual_cost_summary["年平均電費(元/度)"]
    )
    annual_cost_summary["最高超約需量(kW)"] = float(
        annual_cost_summary["最高超約需量(kW)"]
    )

    return annual_cost_summary


def convert_ami_to_json_15min(
    df_ami, tou_program, df_tou_2025, contract_capacity_old, tariff_adjust_factor
):
    """
    將 AMI 原始資料轉換成 JSON 15分鐘格式
    支援自動檢測寬格式和長格式資料，不依賴固定欄位名稱

    Parameters:
    -----------
    df_ami : DataFrame
        AMI 資料，支援兩種格式：
        - 長格式：2欄 (第一欄是日期/時間，第二欄是數值)
        - 寬格式：96-97欄 (第一欄是日期，後面96欄是15分鐘數值)
    tou_program : str
        電價方案名稱，用於判斷夏月期間
    holiday_lst : list
        假日清單，格式為 ['YYYY-MM-DD', ...]

    Returns:
    --------
    list : JSON 格式的 15分鐘資料
    """

    holiday_lst = [
        "2022-01-01",
        "2022-01-31",
        "2022-02-01",
        "2022-02-02",
        "2022-02-03",
        "2022-02-04",
        "2022-02-05",
        "2022-02-28",
        "2022-04-04",
        "2022-04-05",
        "2022-06-03",
        "2022-09-10",
        "2022-10-10",
        "2023-01-21",
        "2023-01-23",
        "2023-01-24",
        "2023-01-25",
        "2023-01-26",
        "2023-02-28",
        "2023-04-04",
        "2023-04-05",
        "2023-05-01",
        "2023-06-22",
        "2023-09-29",
        "2023-10-10",
        "2024-01-01",
        "2024-02-09",
        "2024-02-10",
        "2024-02-12",
        "2024-02-13",
        "2024-02-14",
        "2024-02-28",
        "2024-04-04",
        "2024-05-01",
        "2024-06-10",
        "2024-09-17",
        "2024-10-10",
        "2025-01-01",
        "2025-01-28",
        "2025-01-29",
        "2025-01-30",
        "2025-01-31",
        "2025-02-01",
        "2025-02-28",
        "2025-04-04",
        "2025-05-01",
        "2025-05-31",
        "2025-10-06",
        "2025-10-10",
    ]

    # 1. 自動檢測資料格式
    def detect_ami_format(df):
        """
        檢測 AMI 資料格式，基於欄位數量和結構而非固定欄位名稱
        - 長格式：2欄 (第一欄是日期/時間，第二欄是數值)
        - 寬格式：96-97欄 (第一欄是日期，後面96欄是15分鐘數值)
        """
        num_cols = len(df.columns)

        # 檢查是否為長格式 (2欄)
        if num_cols == 2:
            # 檢查第一欄是否為日期時間格式
            first_col_sample = str(df.iloc[0, 0])
            # 嘗試解析第一欄為日期時間
            try:
                pd.to_datetime(first_col_sample)
                return "long_format"
            except:
                return "unknown"

        # 檢查是否為寬格式 (96-97欄)
        elif num_cols == 97:
            # 檢查第一欄是否為日期格式
            first_col_sample = str(df.iloc[0, 0])
            try:
                pd.to_datetime(first_col_sample)

                # 進一步檢查後續欄位的特徵
                columns = df.columns.tolist()

                # 檢查是否有時間格式的欄位 (如 00:00, 00:15 等)
                time_pattern = any(":" in str(col) for col in columns[1:10])
                if time_pattern:
                    return "wide_time_format"
                else:
                    # 檢查是否為數字欄位 (0, 1, 2, ... 95)
                    numeric_pattern = all(str(col).isdigit() for col in columns[1:10])
                    if numeric_pattern:
                        return "wide_numeric_format"
                    else:
                        return "wide_mixed_format"
            except:
                return "unknown"

        return "unknown"

    # 2. 設定時間欄位名稱
    time = []
    for i in range(24):
        for j in range(4):
            time.append(str(i).zfill(2) + ":" + str(j * 15).zfill(2))

    # 先去掉na的row，避免錯誤，有空值就去掉
    df_ami = df_ami.dropna(how="any").reset_index(drop=True)

    # 3. 根據格式進行相應處理
    format_type = detect_ami_format(df_ami)
    print(f"[debug] 檢測到的資料格式: {format_type}")

    if format_type == "long_format":
        # 長格式 - 2欄 (日期時間, 數值)
        df_ami_long = df_ami.copy()
        # 統一欄位名稱，不管原來叫什麼
        df_ami_long.columns = ["datetime", "value"]
        df_ami_long["datetime"] = pd.to_datetime(df_ami_long["datetime"])
        # 提取時間部分用於後續處理
        df_ami_long["time"] = df_ami_long["datetime"].dt.strftime("%H:%M")

    elif format_type == "wide_time_format":
        # 寬格式 - 已有時間欄位名稱
        df_ami_copy = df_ami.copy()
        # 轉換成 long format，第一欄當作日期欄
        time_columns = df_ami_copy.columns[1:].tolist()  # 除了第一欄以外的所有欄位
        df_ami_long = pd.melt(
            df_ami_copy, id_vars=[df_ami_copy.columns[0]], value_vars=time_columns
        )
        df_ami_long.columns = ["date", "time", "value"]
        df_ami_long["datetime"] = df_ami_long["date"] + " " + df_ami_long["time"]
        df_ami_long["datetime"] = pd.to_datetime(df_ami_long["datetime"])

    elif format_type in ["wide_numeric_format", "wide_mixed_format"]:
        # 寬格式 - 數字或混合欄位名稱
        df_ami_copy = df_ami.copy()
        # 重新命名欄位：第一欄為date，後續96欄為時間
        df_ami_copy.columns = ["date"] + time
        # 轉換成 long format
        df_ami_long = pd.melt(df_ami_copy, id_vars=["date"], value_vars=time)
        df_ami_long.columns = ["date", "time", "value"]
        df_ami_long["datetime"] = df_ami_long["date"] + " " + df_ami_long["time"]
        df_ami_long["datetime"] = pd.to_datetime(df_ami_long["datetime"])

    else:
        raise ValueError(
            f"無法識別的資料格式: {format_type}，欄位: {df_ami.columns.tolist()[:10]}"
        )

    # 4. 統一後續處理
    df_ami_long.sort_values(by="datetime", inplace=True)
    df_ami_long = df_ami_long.tail(96 * 365)
    df_ami_long.reset_index(drop=True, inplace=True)

    # 5. 添加 is_summer 欄位
    if "高壓" in tou_program:
        summer_start = "05-16"
        summer_end = "10-15"
    else:
        summer_start = "06-01"
        summer_end = "09-30"

    def is_summer_period(date):
        month_day = date.strftime("%m-%d")
        return 1 if summer_start <= month_day <= summer_end else 0

    df_ami_long["is_summer"] = df_ami_long["datetime"].apply(is_summer_period)

    # 6. 添加星期幾標註
    df_ami_long["weekday"] = df_ami_long["datetime"].dt.day_name()

    # 7. 標記假日資料
    if holiday_lst:
        # df_ami_long = df_ami_long[~df_ami_long['datetime'].dt.date.astype(str).isin(holiday_lst)].copy()
        df_ami_long["weekday"] = np.where(
            df_ami_long["datetime"].dt.date.astype(str).isin(holiday_lst),
            "Holiday",
            df_ami_long["weekday"],
        )

    # 8. 計算 14 天代表日的平均值
    df_ami_long_14 = (
        df_ami_long[df_ami_long["weekday"] != "Holiday"]
        .groupby(["is_summer", "weekday", "time"])
        .agg({"value": "mean"})
        .reset_index()
    )
    df_ami_long_14["value"] = df_ami_long_14["value"].round(2)

    # extra: 產生電價資料
    annual_cost_summary = calculator_annual_cost_ami_365(
        tou_program,
        df_ami_long,
        df_tou_2025,
        price_dict,
        contract_capacity_old,
        tariff_adjust_factor,
    )

    # 9. 轉換成 JSON 格式
    # 創建季節+星期的組合欄位
    df_ami_long_14["season_weekday"] = df_ami_long_14.apply(
        lambda row: ("summer" if row["is_summer"] else "nonSummer") + row["weekday"],
        axis=1,
    )

    # 建立樞紐表
    pivot_df = df_ami_long_14.pivot(
        index="time", columns="season_weekday", values="value"
    ).reset_index()

    # 轉換成目標格式
    json_ami_15min_update = []
    pivot_df = pivot_df.sort_values("time").reset_index(drop=True)

    for idx, row in pivot_df.iterrows():
        time_dict = {"time": row["time"]}

        # 添加各個季節+星期的數值
        for col in pivot_df.columns:
            if col != "time":
                time_dict[col] = round(row[col], 2) if pd.notna(row[col]) else 0.0

        json_ami_15min_update.append(time_dict)

    return json_ami_15min_update, annual_cost_summary


# ID: 透過 ID 來找出契約容量，歷史資料庫AMI的ID
def update_config(config):
    """
    更新所有透過公式可計算的欄位，回填進 config。
    """
    b = config["儲能系統"]
    t = config["電價方案"]
    c = config["降低契約容量"]
    s = config["即時備轉"]
    d = config["可套利天數"]
    a = config["可參與輔助服務時數"]
    dr = config["日選時段型"]
    c0 = config["建置成本(第0年繳)"]
    c10 = config["維運成本(年繳)"]
    sim = config["負載模擬參數"]
    sf = config["系統服務單價"]

    b["PCS 標稱功率"] = b["單台 PCS 標稱功率"] * b["台數"]
    b["儲能容量"] = b["單台 儲能容量"] * b["台數"]
    b["C-Rate"] = round(b["PCS 標稱功率"] / b["儲能容量"], 3)
    b["實際建置容量"] = b["儲能容量"]

    # t["契約容量"] = df_capacity[df_capacity['ID'] == ID]['經常性契容'].values[0]
    # t["調整後加權平均尖峰電價"] = round(t["加權平均尖峰電價"] * t["電費調整係數"], 5)
    # t["調整後加權平均離峰電價"] = round(t["加權平均離峰電價"] * t["電費調整係數"], 5)
    # t["調整後加權平均電價"] = round(t["加權平均電價"] * t["電費調整係數"], 5)
    t["夏月最高電價"] = price_dict[(t["計費類別"], "summer")]["最高電價"]
    t["夏月最低電價"] = price_dict[(t["計費類別"], "summer")]["最低電價"]
    t["非夏月最高電價"] = price_dict[(t["計費類別"], "not_summer")]["最高電價"]
    t["非夏月最低電價"] = price_dict[(t["計費類別"], "not_summer")]["最低電價"]
    t["夏月天數"] = price_dict[(t["計費類別"], "summer")]["天數"]
    t["非夏月天數"] = price_dict[(t["計費類別"], "not_summer")]["天數"]
    t["調整後夏月最高電價"] = round(t["夏月最高電價"] * t["電費調整係數"], 5)
    t["調整後夏月最低電價"] = round(t["夏月最低電價"] * t["電費調整係數"], 5)
    t["調整後非夏月最高電價"] = round(t["非夏月最高電價"] * t["電費調整係數"], 5)
    t["調整後非夏月最低電價"] = round(t["非夏月最低電價"] * t["電費調整係數"], 5)
    # t["原始流動電費"] = round(t["年用度數"] * t["調整後加權平均電價"])

    # c["降低契約容量收益"] = round(
    #     t["契約容量"] * c["降契約容量比例"] * c["每kW契約容量費用"]
    # )

    s["投標容量"] = b["PCS 標稱功率"]

    # d["可套利天數"] = d["全年週一至週五天數"] - d["可能超約天數"]

    a["不可投標天數"] = d["可能超約天數"] + d["歲修天數"]  # 15天歲修
    # a["可參與輔助服務時數"] = (365 - a["不可投標天數"])* a["大於1000kW比例"]/100*24
    # a["可參與輔助服務天數"] = a["可參與輔助服務時數"] / 24
    # a["日選時段同時參與天數"] = min(a["可參與輔助服務天數"], dr["5月-10月天數"]) # 僅限於一種需量反應方案
    # a["僅參與輔助服務天數"] = a["可參與輔助服務天數"] - a["日選時段同時參與天數"]

    # dr['抑低契約容量'] = b["PCS 標稱功率"]
    dr["開始時段"] = dr_program_dict[dr["執行方案"]]["start_time"]
    dr["結束時段"] = dr_program_dict[dr["執行方案"]]["end_time"]
    dr["執行時數"] = dr_program_dict[dr["執行方案"]]["duration_hr"]
    dr["流動電費扣減費率"] = dr_program_dict[dr["執行方案"]]["rate"]
    # 注意這邊並非是高壓跟低壓的非夏月，而是5到10月的天數
    dr["5月-10月可參與天數"] = dr["5月-10月天數"] - d["可能超約天數"]

    c0["儲能設備"] = b["實際建置容量"] * c0["每單位建置成本"]
    c0["EMS"] = b["實際建置容量"] * sf["EMS系統含硬體_kWh"]
    c10["EMS維運成本"] = c0["EMS"] * sf["EMS保固維運費用_年_%"] / 100
    c10["電力交易雲端平台"] = (
        sf["電力交易雲端使用費_MW"] * b["PCS 標稱功率"] / 1000
        + sf["電力交易之場域通訊使用_年"]
    )
    c10["案場維運成本"] = c0["儲能設備"] * sf["案場維運費用_年_%"] / 100

    return config
