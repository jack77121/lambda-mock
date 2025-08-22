import copy
import os
import sqlite3
import time
from itertools import product

import numpy as np
import numpy_financial as npf
import pandas as pd

from ...utils.logger import logger
from . import calculator, config_loader


def get_ami_db_path():
    """Get the correct path to ami_data.db file"""
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    db_path = os.path.join(script_dir, "ami_data.db")
    return db_path


# === 全域母表：所有可能出現的行 ===
ALL_ROW_LABELS = [
    "建置容量(kWh)",
    "實際可用容量(kWh)",
    "投標容量",
    "保留容量",
    "降契約容量",
    "電價差收益",
    "日選時段型",
    "輔助服務價金",
    "日選時段收益",
    "日內套利收益",
    "總收入",
    "土地租金",
    "保險費用",
    "維運+監控EMS費用",
    "聚合分潤比例",
    "利息費用",
    "總支出",
    "總支出(不含利息)",
    "Net Cash",
]

# === 每個模式需要哪些行 ===
SCENARIO_ROWS = {
    "energy_only": [
        "建置容量(kWh)",
        "實際可用容量(kWh)",
        "保留容量",
        "降契約容量",
        "電價差收益",
        "總收入",
        "土地租金",
        "保險費用",
        "維運+監控EMS費用",
        "利息費用",
        "總支出",
        "總支出(不含利息)",
        "Net Cash",
    ],
    "energy_lc": [
        "建置容量(kWh)",
        "實際可用容量(kWh)",
        "保留容量",
        "降契約容量",
        "電價差收益",
        "用電大戶收益",
        "總收入",
        "土地租金",
        "保險費用",
        "維運+監控EMS費用",
        "利息費用",
        "總支出",
        "總支出(不含利息)",
        "Net Cash",
    ],
    "energy_dr": [
        "建置容量(kWh)",
        "實際可用容量(kWh)",
        "保留容量",
        "降契約容量",
        "電價差收益",
        "日選時段型",
        "總收入",
        "土地租金",
        "保險費用",
        "維運+監控EMS費用",
        "利息費用",
        "總支出",
        "總支出(不含利息)",
        "Net Cash",
    ],
    "energy_dr_regulation": [
        "建置容量(kWh)",
        "實際可用容量(kWh)",
        "投標容量",
        "保留容量",
        "降契約容量",
        "電價差收益",
        "日選時段型",
        "輔助服務價金",
        "總收入",
        "土地租金",
        "保險費用",
        "維運+監控EMS費用",
        "聚合分潤比例",
        "利息費用",
        "總支出",
        "總支出(不含利息)",
        "Net Cash",
    ],
    "energy_regulation": [
        "建置容量(kWh)",
        "實際可用容量(kWh)",
        "投標容量",
        "保留容量",
        "降契約容量",
        "電價差收益",
        "輔助服務價金",
        "總收入",
        "土地租金",
        "保險費用",
        "維運+監控EMS費用",
        "聚合分潤比例",
        "利息費用",
        "總支出",
        "總支出(不含利息)",
        "Net Cash",
    ],
    # 你可以自己新增更多模式
}


# === 主函式 ===
def generate_summary(
    config,
    df_ami,
    mode="energy_dr_regulation",
    years=15,
    include_contract_saving=False,
    is_aggregation=False,
    lc_mode="義務時數型",
):
    if mode not in SCENARIO_ROWS:
        raise ValueError(f"Unsupported mode: {mode}")

    # 初始化 DataFrame
    years_list = [f"Year {i}" for i in range(1, years + 1)]
    row_labels = SCENARIO_ROWS[mode]
    df_summary = pd.DataFrame(index=row_labels, columns=years_list).fillna("")

    # === 填資料 ===

    # 基本參數
    cfg = config["儲能系統"]
    建置容量 = cfg["實際建置容量"]
    儲能容量 = cfg["儲能容量"]
    SOC上限 = cfg["SOC上限"]
    SOC下限 = cfg["SOC下限"]
    年衰減率 = cfg["儲能健康度年衰減率"] / 100
    cycles = config["儲能系統"]["每日最大循環次數"]

    # 是否是用電大戶
    if lc_mode in ["義務時數型", "累進回饋型"]:
        consider_large_consumer = True
    else:
        consider_large_consumer = False

    if "建置容量(kWh)" in row_labels:
        df_summary.loc["建置容量(kWh)"] = [建置容量] * years

    if "實際可用容量(kWh)" in row_labels:
        base_kWh = 儲能容量 * (SOC上限 - SOC下限) / 100
        usable_kWh = [
            round(base_kWh * (1 - 年衰減率 * (i - 1)), 3) for i in range(1, years + 1)
        ]
        df_summary.loc["實際可用容量(kWh)"] = usable_kWh

    if "投標容量" in row_labels:
        if is_aggregation:
            df_summary.loc["投標容量"] = [config["即時備轉"]["投標容量"]] * years
        else:
            if config["即時備轉"]["投標容量"] < 1000:
                df_summary.loc["投標容量"] = [0] * years
            else:
                df_summary.loc["投標容量"] = [config["即時備轉"]["投標容量"]] * years

    if "保留容量" in row_labels:
        df_summary.loc["保留容量"] = [0] * years

    if "降契約容量" in row_labels:
        if include_contract_saving:
            df_summary.loc["降契約容量"] = [
                config["降低契約容量"]["降低契約容量收益"]
            ] * years
        else:
            df_summary.loc["降契約容量"] = [0] * years

    if "電價差收益" in row_labels:
        # 尖峰價 = config['電價方案']['調整後加權平均尖峰電價']
        # 離峰價 = config['電價方案']['調整後加權平均離峰電價']
        夏月最高電價 = config["電價方案"]["調整後夏月最高電價"]
        夏月最低電價 = config["電價方案"]["調整後夏月最低電價"]
        非夏月最高電價 = config["電價方案"]["調整後非夏月最高電價"]
        非夏月最低電價 = config["電價方案"]["調整後非夏月最低電價"]
        夏月天數 = config["電價方案"]["夏月天數"]
        非夏月天數 = config["電價方案"]["非夏月天數"]

        # 套利天數 = config['可套利天數']['可套利天數']

        # 補上可充放電量，夏月跟非夏月都更新
        df_ami, df_ami2 = calculator.calculate_transferable_energy(
            df_ami,
            config["電價方案"]["契約容量"],
            config["儲能系統"]["PCS 標稱功率"],
            [("00:00", "23:45")],
            consider_large_consumer,
        )
        # print('config pcs', config['儲能系統']['PCS 標稱功率'])
        # print(df_ami2)

        損失率 = cfg["電能損失率(Round Trip)"] / 100

        delta_kWh = df_summary.loc["實際可用容量(kWh)"] - df_summary.loc["保留容量"]
        # #print('delta_kWh',type(delta_kWh), delta_kWh)

        # 計算每年的每日平均可轉移電量

        result_te_summer = calculator.batch_calculate_transfered_energy(
            df_ami2, delta_kWh, "summer", 損失率, consider_large_consumer
        )

        夏月每日可以轉移度數 = result_te_summer["可轉移電量"]
        夏月每日用電大戶放電度數 = result_te_summer["用電大戶義務可轉移電量"]

        if config["儲能系統"]["每日最大循環次數"] == 1:
            result_te_not_summer = calculator.batch_calculate_transfered_energy(
                df_ami2, delta_kWh, "not_summer", 損失率, consider_large_consumer
            )
            非夏月可以轉移度數 = result_te_not_summer["可轉移電量"]
            非夏月每日用電大戶放電度數 = result_te_not_summer["用電大戶義務可轉移電量"]

        elif config["儲能系統"]["每日最大循環次數"] == 2:
            # 確認有兩個高峰
            if (
                calculator.count_high_peaks(
                    df_ami[
                        (df_ami["is_summer"] == 0) & (df_ami["weekday2"] == "Monday")
                    ].tou_level
                )
                == 2
            ):
                # time_periods = [('00:00', '10:45'), ('11:00', '23:45')]
                # 第一循環
                _, df_ami2_2 = calculator.calculate_transferable_energy(
                    df_ami,
                    config["電價方案"]["契約容量"],
                    config["儲能系統"]["PCS 標稱功率"],
                    time_periods=[("00:00", "10:45")],
                )
                非夏月可以轉移度數_1 = calculator.batch_calculate_transfered_energy(
                    df_ami2_2, delta_kWh, "not_summer", 損失率
                )["可轉移電量"]

                # 第二循環，只有第二循環才會有用電大戶
                _, df_ami2_2 = calculator.calculate_transferable_energy(
                    df_ami,
                    config["電價方案"]["契約容量"],
                    config["儲能系統"]["PCS 標稱功率"],
                    time_periods=[("11:00", "23:45")],
                    consider_large_consumer=consider_large_consumer,
                )
                result_te_not_summer_2 = calculator.batch_calculate_transfered_energy(
                    df_ami2_2, delta_kWh, "not_summer", 損失率, consider_large_consumer
                )
                非夏月可以轉移度數_2 = result_te_not_summer_2["可轉移電量"]
                非夏月每日用電大戶放電度數 = result_te_not_summer_2[
                    "用電大戶義務可轉移電量"
                ]
                # print('非夏月可以轉移度數_1', 非夏月可以轉移度數_1 , '非夏月可以轉移度數_2', 非夏月可以轉移度數_2)
                非夏月可以轉移度數 = 非夏月可以轉移度數_1 + 非夏月可以轉移度數_2

            # 如果只有一個高峰，則不分時段
            else:
                result_te_not_summer = calculator.batch_calculate_transfered_energy(
                    df_ami2, delta_kWh, "not_summer", 損失率, consider_large_consumer
                )
                非夏月可以轉移度數 = result_te_not_summer["可轉移電量"]
                非夏月每日用電大戶放電度數 = result_te_not_summer[
                    "用電大戶義務可轉移電量"
                ]
                config["儲能系統"]["每日最大循環次數"] = 1

        # 只有一個高峰
        else:
            result_te_not_summer = calculator.batch_calculate_transfered_energy(
                df_ami2, delta_kWh, "not_summer", 損失率, consider_large_consumer
            )
            非夏月可以轉移度數 = result_te_not_summer["可轉移電量"]
            非夏月每日用電大戶放電度數 = result_te_not_summer["用電大戶義務可轉移電量"]

        # print('非夏月可以轉移度數', 非夏月可以轉移度數)
        # print(pd.DataFrame({'夏月': 夏月每日可以轉移度數, '非夏月': 非夏月可以轉移度數, '可用容量': delta_kWh.values}))

        # 充電度數 * 充電效率 * 放電效率 = 放電度數
        # 往返效率 =  放電度數/充電度數 = 充電效率 * 放電效率
        # 充電效率 = 放電效率 = 往返效率^(1/2)

        # print('用電大戶放電度數_夏月', 夏月每日用電大戶放電度數)
        # print('用電大戶放電度數_非夏月', 非夏月每日用電大戶放電度數)

        # a. 價差
        a = (夏月最高電價 - 夏月最低電價) * 夏月天數 * 夏月每日可以轉移度數 + (
            非夏月最高電價 - 非夏月最低電價
        ) * 非夏月天數 * 非夏月可以轉移度數

        # b. 充電成本
        b = (
            夏月最低電價 * 夏月天數 * 夏月每日可以轉移度數 * 損失率
            + 非夏月最低電價 * 非夏月天數 * 非夏月可以轉移度數 * 損失率
        )

        # #print('result', a-b)
        # 直接assign 要小心，沒有index 要加 values，從頭到尾插入
        df_summary.loc["電價差收益"] = (a - b).values

        # #print('電價差收益', df_summary.loc["電價差收益"])

    if "用電大戶收益" in row_labels:
        # print ('[debug] 用電大戶配合用電', config['再生能源義務用戶']['義務裝置容量'])
        # print('[debug] 方案', lc_mode)

        # print('用電大戶放電度數_夏月', 夏月每日用電大戶放電度數)
        # print('用電大戶放電度數_非夏月', 非夏月每日用電大戶放電度數)
        用電大戶放電度數 = (
            夏月天數 * 夏月每日用電大戶放電度數
            + 非夏月天數 * 非夏月每日用電大戶放電度數
        ).round()
        # print('[debug] 用電大戶放電度數:', 用電大戶放電度數)
        lc_reduction_fee = [
            calculator.compute_large_consumer_reduction(
                config["再生能源義務用戶"]["義務裝置容量"], x, lc_mode
            )
            for x in 用電大戶放電度數
        ]
        # print('[debug] 用電大戶配合用電:', lc_reduction_fee)
        df_summary.loc["用電大戶收益"] = lc_reduction_fee

    if "日選時段型" in row_labels:
        delta_kWh = df_summary.loc["實際可用容量(kWh)"] - df_summary.loc["保留容量"]

        # 抑低契約容量 = config['日選時段型']['抑低契約容量']

        抑低契約容量 = []
        # #print(df_ami2)
        for avail_kWh in delta_kWh:
            df_result, dr_kw = calculator.calculate_dr_capacity(
                df_ami,
                config["日選時段型"]["開始時段"],
                config["日選時段型"]["結束時段"],
                config["日選時段型"]["執行時數"],
                avail_kWh * np.sqrt(1 - 損失率),
            )
            抑低契約容量.append(dr_kw)

        抑低契約容量 = pd.Series(抑低契約容量)
        # #print('抑低契約容量', 抑低契約容量)

        當日執行率 = config["日選時段型"]["當日執行率"]
        執行時數 = config["日選時段型"]["執行時數"]
        扣減電價 = config["日選時段型"]["流動電費扣減費率"]
        扣減倍率 = config["日選時段型"]["扣減比率"]
        可參與天數 = config["日選時段型"]["5月-10月可參與天數"]

        日選收益 = (
            抑低契約容量
            * 當日執行率
            * 執行時數
            * 扣減電價
            * 扣減倍率
            * 可參與天數
            / 10000
        )
        # #print('日選收益', 日選收益)
        # df_summary.loc["日選時段型"] = [round(日選收益, 2)] * years
        df_summary.loc["日選時段型"] = 日選收益.values

    if "輔助服務價金" in row_labels:
        效能價格 = config["即時備轉"]["1級效能價格"]
        容量價格 = config["即時備轉"]["容量價格"]
        # 每日參與時數 = 24
        日選執行時數 = config["日選時段型"]["執行時數"]
        # 僅輔助日 = config['可參與輔助服務時數']['僅參與輔助服務天數']
        # 同時輔助日 = config['可參與輔助服務時數']['日選時段同時參與天數']
        得標比例 = config["即時備轉"]["得標容量比例"] / 100
        折扣比例 = config["即時備轉"]["折扣比例"] / 100

        # 聚合後折扣 = config['可參與輔助服務時數']['聚合後收益折扣'] / 100
        # 大於1000比例 = config['可參與輔助服務時數']['大於1000kW比例'] / 100
        每月觸發次數 = config["即時備轉"]["每月觸發次數"]
        日前電價 = config["即時備轉"]["日前電能邊際價格"]

        # 1MW以上才可以投標
        if is_aggregation:
            投標容量 = config["即時備轉"]["投標容量"]
        else:
            if config["即時備轉"]["投標容量"] < 1000:
                投標容量 = 0
            else:
                投標容量 = config["即時備轉"]["投標容量"]

        不可投標天數 = config["可參與輔助服務時數"]["不可投標天數"]

        # 先把歲修排在非工作日
        非工作日 = 365 - 夏月天數 - 非夏月天數 - 不可投標天數
        # 日選執行時數 = config['日選時段型']['執行時數']

        輔助服務價金 = []
        # #print(df_ami)

        for avail_kWh in delta_kWh:
            df_ami_weekend = df_ami[df_ami["weekday"] != "week"].copy()
            df_ami_week = df_ami[df_ami["weekday"] == "week"].copy()

            # 非工作日的特徵
            series_ami_weekend = calculator.spining_weekend_load_kw_stats(
                df_ami_weekend, config["儲能系統"]["PCS 標稱功率"]
            )
            # #print('series_ami_weekend', series_ami_weekend)
            # 工作日的特徵，但區分夏月跟非夏月
            df_ami_week2 = calculator.compute_spinning_summary(
                df_ami_week, config["儲能系統"]["PCS 標稱功率"], avail_kWh
            )

            # print('df_ami_week2', df_ami_week2)

            sp_total_single, sp_total_agg = calculator.compute_total_spinning_gain_sum(
                series_ami_weekend,
                df_ami_week2,
                非工作日,
                夏月天數,
                非夏月天數,
                容量價格,
                效能價格,
                日選執行時數,
                cycles,
            )
            # print('sp_total_single', sp_total_single, sp_total_agg)
            if is_aggregation:
                輔助服務價金.append(sp_total_agg)
            else:
                # 單一案場投標量 小於1000kW，不能參加
                if 投標容量 < 1000:
                    輔助服務價金.append(0)
                else:
                    輔助服務價金.append(sp_total_single)

        # a = (
        #     (效能價格 + 容量價格) * (每日參與時數 - 2) * 僅輔助日 +
        #     (效能價格 + 容量價格) * (每日參與時數 - 2 - 日選執行時數) * 同時輔助日
        # ) * 投標容量 / 1000 * 得標比例 * 折扣比例

        b = 每月觸發次數 * 日前電價 * 12 * 投標容量 / 1000

        # #print(輔助服務價金)
        輔助服務價金 = pd.Series(輔助服務價金) * 得標比例 * 折扣比例
        輔助服務價金 = 輔助服務價金 + b
        # #print(輔助服務價金)
        # #print('b:',b)

        # 輔助服務價金 = (a + b) * 聚合後折扣 * 大於1000比例
        df_summary.loc["輔助服務價金"] = 輔助服務價金.values

    # === 小計總收入 ===
    income_rows = [
        "降契約容量",
        "電價差收益",
        "日選時段型",
        "輔助服務價金",
        "用電大戶收益",
    ]
    total_income = sum(
        df_summary.loc[row] for row in income_rows if row in df_summary.index
    )
    df_summary.loc["總收入"] = total_income

    # === 支出部分 ===
    if "土地租金" in row_labels:
        土地租金單價 = config["維運成本(年繳)"]["土地年租金"]
        df_summary.loc["土地租金"] = [儲能容量 * 土地租金單價] * years

    if "保險費用" in row_labels:
        保險費率 = config["維運成本(年繳)"]["保險費率"]
        df_summary.loc["保險費用"] = [
            config["建置成本(第0年繳)"]["儲能設備"] * 保險費率 / 100
        ] * years

    if "維運+監控EMS費用" in row_labels:
        維運成本 = config["維運成本(年繳)"]["案場維運成本"]
        EMS維運成本 = config["維運成本(年繳)"]["EMS維運成本"]
        其他固定成本 = config["維運成本(年繳)"]["其他固定成本"]
        # 只有即時備轉才需要電力交易費用
        if "regulation" in mode:
            電力交易費用 = config["維運成本(年繳)"]["電力交易雲端平台"]
        else:
            電力交易費用 = 0

        # TODO: 維運成本 kW or kWh 計價
        df_summary.loc["維運+監控EMS費用"] = (
            [維運成本 + EMS維運成本 + 電力交易費用 + 其他固定成本]
        ) * years

    if "聚合分潤比例" in row_labels:
        聚合分潤比例 = config["聚合分潤"]["聚合分潤比例"] / 100
        if is_aggregation:
            df_summary.loc["聚合分潤比例"] = (
                df_summary.loc["輔助服務價金"] * 聚合分潤比例
            )
        else:
            df_summary.loc["聚合分潤比例"] = df_summary.loc["輔助服務價金"] * 0

    if "利息費用" in row_labels:
        建置成本 = (
            config["建置成本(第0年繳)"]["儲能設備"]
            + config["建置成本(第0年繳)"]["儲能設備安裝"]
            + config["建置成本(第0年繳)"]["高壓設備"]
            + config["建置成本(第0年繳)"]["高壓設備安裝"]
            + config["建置成本(第0年繳)"]["設計/監造/簽證費用"]
            + config["建置成本(第0年繳)"]["其他"]
            + config["建置成本(第0年繳)"]["EMS"]
        )

        貸款成數 = config["融資成本"]["貸款成數"] / 100

        if 貸款成數 <= 0:
            # 如果貸款成數為0，則不計算利息費用
            df_summary.loc["利息費用"] = [0] * years
        else:
            利率 = config["融資成本"]["利息費用"] / 100
            # 利率為0, 輸出錯誤
            if 利率 <= 0:
                raise ValueError("利率必須大於0")

            年限 = config["融資成本"]["攤還年限"]

            貸款金額 = 建置成本 * 貸款成數
            年本息 = calculator.loan_pmt_per_year(貸款金額, 年限, 利率)
            貸款支出 = [年本息] * min(年限, years) + [0] * max(0, years - 年限)

            df_summary.loc["利息費用"] = 貸款支出

    # === 小計總支出 ===
    expense_rows = [
        "土地租金",
        "保險費用",
        "維運+監控EMS費用",
        "聚合分潤比例",
        "利息費用",
    ]
    total_expense = sum(
        df_summary.loc[row] for row in expense_rows if row in df_summary.index
    )
    total_expense_ex_interest = sum(
        df_summary.loc[row]
        for row in expense_rows
        if row in df_summary.index and row != "利息費用"
    )

    df_summary.loc["總支出"] = total_expense
    df_summary.loc["總支出(不含利息)"] = total_expense_ex_interest

    # === Net Cash ===
    df_summary.loc["Net Cash"] = df_summary.loc["總收入"] - df_summary.loc["總支出"]

    # #print("Summary DataFrame:")
    # #print(df_summary)

    # === ROI/IRR ===
    淨現金總和 = df_summary.loc["Net Cash"].sum()
    自備資金 = 建置成本 * (1 - 貸款成數)

    # === 處理 Year 0 ===
    df_summary.insert(0, "Year 0", np.nan)  # 先填 0
    # 1. 與 Year 1 相同的欄位
    copy_rows = ["建置容量(kWh)", "實際可用容量(kWh)", "投標容量", "保留容量"]
    for row in copy_rows:
        if row in df_summary.index:
            df_summary.at[row, "Year 0"] = df_summary.at[row, "Year 1"]

    # 2. 自備資金支出與淨現金流
    df_summary.at["總支出", "Year 0"] = 自備資金
    df_summary.at["總支出(不含利息)", "Year 0"] = 自備資金
    df_summary.at["Net Cash", "Year 0"] = -自備資金

    # print(f"[debug] 淨現金總和: {淨現金總和:.2f}")
    # print(f"[debug] 自備資金: {自備資金:.2f}")

    ROI = (淨現金總和 - 自備資金) / 自備資金
    # cash_flows = [-自備資金] + df_summary.loc["Net Cash"].tolist()
    cash_flows = df_summary.loc["Net Cash"].tolist()
    IRR = npf.irr(cash_flows)

    # Annual_ROI = (1 + ROI) ** (1/years) - 1
    # 出現-1時，其實表示全部賠光，計算可能就沒意義，所以報錯
    if ROI > -1:
        Annual_ROI = (1 + ROI) ** (1 / years) - 1
    else:
        Annual_ROI = float("nan")  # 或者直接設為 0、或顯示錯誤訊息

    Average_ROI = ROI / years

    # 顯示
    # #print(f"ROI: {ROI:.2%}")
    # #print(f"IRR: {IRR:.2%}")
    # #print(f"Annual ROI: {Annual_ROI:.2%}")
    # #print(f"Average ROI: {Average_ROI:.2%}")

    return df_summary, ROI, IRR, Annual_ROI, Average_ROI


# dr_program: '0h', '1h', '2h', '3h', '4h', '5h', '6h', '7h', '8h'
# sp_program: 'single', 'agg'


def run_simulation(
    config,
    unit,
    df_ami,
    mode="energy_only",
    dr_program=None,
    sp_program=None,
    lc_program=None,
    year=15,
):
    start_time = time.time()
    logger.info("[run_simulation]")
    config["儲能系統"]["台數"] = unit

    if mode == "energy_dr":
        assert dr_program is not None, "需提供 DR 方案參數"
        config["日選時段型"]["執行方案"] = dr_program

    # DR跟即時備轉都做
    if mode == "energy_dr_regulation":
        assert sp_program in ["single", "agg"], "即時備轉方案需為 'single' 或 'agg'"
        config["日選時段型"]["執行方案"] = dr_program

    # 雖不會用到dr，但update_config還是要提供。
    if mode == "energy_only":
        config["日選時段型"]["執行方案"] = "0h"

    if mode == "energy_regulation":
        assert sp_program in ["single", "agg"], "即時備轉方案需為 'single' 或 'agg'"
        config["日選時段型"]["執行方案"] = "0h"

    if mode == "energy_lc":
        assert lc_program in [
            "義務時數型",
            "累進回饋型",
        ], "用電大戶方案需為 '義務時數型' 或 '累進回饋型'"
        config["日選時段型"]["執行方案"] = "0h"

    config = config_loader.update_config(config)
    # df_ami = config_loader.norm_ami(df_ami_raw, df_tou_2025, ID, config['電價方案']['計費類別'])

    if (mode == "energy_dr_regulation") | (mode == "energy_regulation"):
        df_summary, ROI, IRR, Annual_ROI, Average_ROI = generate_summary(
            config,
            df_ami,
            mode=mode,
            years=year,
            include_contract_saving=False,
            is_aggregation=(sp_program == "agg"),
            lc_mode=lc_program,
        )
    else:
        df_summary, ROI, IRR, Annual_ROI, Average_ROI = generate_summary(
            config,
            df_ami,
            mode=mode,
            years=year,
            include_contract_saving=False,
            is_aggregation=False,
            lc_mode=lc_program,
        )

    result = {
        "台數": unit,
        "ROI": ROI,
        "IRR": IRR,
        "Annual_ROI": Annual_ROI,
        "Average_ROI": Average_ROI,
        "模式": mode,
    }

    if (mode == "energy_only") | (mode == "energy_regulation") | (mode == "energy_lc"):
        result["DR方案"] = "0h"
    else:
        result["DR方案"] = dr_program

    if mode == "energy_dr_regulation":
        result["即時備轉方案"] = sp_program
    else:
        result["即時備轉方案"] = "-"

    if mode == "energy_lc":
        result["用電大戶方案"] = lc_program
    else:
        result["用電大戶方案"] = "-"

    end_time = time.time()
    execution_time = end_time - start_time
    logger.info("[run_simulation]", extra={"completed in": f"{execution_time:.2f} sec"})
    return result, df_summary


def run_and_store(mode_key, 台數, df, results, mode, dict_summary, gain, config):
    results.append(gain)
    mode.append(mode_key)
    # 存成 dict，包含 df 和 config（建議用 deepcopy 避免後續被覆蓋）
    dict_summary[(台數, mode_key)] = {"df": df, "config": copy.deepcopy(config)}


def simulate_energy_only(台數選項, config, df_ami, year, results, mode, dict_summary):
    for 台數 in 台數選項:
        gain, df = run_simulation(
            config=config, unit=台數, df_ami=df_ami, mode="energy_only", year=year
        )
        run_and_store("電價套利", 台數, df, results, mode, dict_summary, gain, config)


def simulate_lc(
    台數選項, 用電大戶方案, config, df_ami, year, results, mode, dict_summary
):
    for 台數, 方案 in product(台數選項, 用電大戶方案):
        gain, df = run_simulation(
            config=config,
            unit=台數,
            df_ami=df_ami,
            mode="energy_lc",
            lc_program=方案,
            year=year,
        )
        run_and_store(
            f"電價套利-{方案}", 台數, df, results, mode, dict_summary, gain, config
        )


def simulate_dr(
    台數選項, dr方案選項, config, df_ami, year, results, mode, dict_summary
):
    for 台數, dr方案 in product(台數選項, dr方案選項):
        gain, df = run_simulation(
            config=config,
            unit=台數,
            df_ami=df_ami,
            mode="energy_dr",
            dr_program=dr方案,
            year=year,
        )
        run_and_store(
            f"電價套利-日選{dr方案}",
            台數,
            df,
            results,
            mode,
            dict_summary,
            gain,
            config,
        )


def simulate_sp(
    台數選項, sp方案選項, config, df_ami, year, results, mode, dict_summary
):
    for 台數, sp方案 in product(台數選項, sp方案選項):
        sp_str = "單一" if sp方案 == "single" else "聚合"
        gain, df = run_simulation(
            config=config,
            unit=台數,
            df_ami=df_ami,
            mode="energy_regulation",
            dr_program="0h",
            sp_program=sp方案,
            year=year,
        )
        run_and_store(
            f"電價套利-即時{sp_str}",
            台數,
            df,
            results,
            mode,
            dict_summary,
            gain,
            config,
        )


def simulate_dr_sp(
    台數選項, dr方案選項, sp方案選項, config, df_ami, year, results, mode, dict_summary
):
    for 台數, dr方案, sp方案 in product(台數選項, dr方案選項, sp方案選項):
        sp_str = "單一" if sp方案 == "single" else "聚合"
        mode_key = f"電價套利-日選{dr方案}-即時{sp_str}"
        gain, df = run_simulation(
            config=config,
            unit=台數,
            df_ami=df_ami,
            mode="energy_dr_regulation",
            dr_program=dr方案,
            sp_program=sp方案,
            year=year,
        )
        run_and_store(mode_key, 台數, df, results, mode, dict_summary, gain, config)


# 這個函式會執行所有的模擬，並回傳結果
# contract_capacity_old = {
#     "經常契約": 5000,
#     "半尖峰契約/非夏月契約": 0,
#     "週六半尖峰契約": 0,
#     "離峰契約": 0
# }


def run_all_simulations(
    config,
    json_ami_hourly_update,
    json_ami_15min,
    ID,
    contract_capacity_old,
    contract_capacity_new,
    tou_program,
    industry_class,
    tariff_adjust_factor,
    df_tou_2025,
    units,
    dr方案選項=["2h", "4h", "6h"],
    即時備轉方案選項=["single", "agg"],
    用電大戶方案=["義務時數型", "累進回饋型"],
    year=15,
):
    # === input 檢查 ===
    if not isinstance(ID, (int, str)):
        raise ValueError(f"ID 格式錯誤，應為 int 或 str，實際為 {type(ID)}")

    # print(f"[debug] contract_capacity_old: {contract_capacity_old}")
    if not isinstance(contract_capacity_old, dict):
        raise ValueError(
            f"契約容量(contract_capacity_old) 格式錯誤，應為字典格式，實際為 {type(contract_capacity_old)}"
        )
    required_keys = ["經常契約", "半尖峰契約/非夏月契約", "週六半尖峰契約", "離峰契約"]
    for key in required_keys:
        if key not in contract_capacity_old:
            raise ValueError(f"契約容量字典缺少必要的鍵: {key}")
        if (
            not isinstance(contract_capacity_old[key], (int, float))
            or contract_capacity_old[key] < 0
        ):
            raise ValueError(
                f"契約容量[{key}] 格式錯誤，應為非負數，實際為 {contract_capacity_old[key]}"
            )

    if not isinstance(contract_capacity_new, dict):
        raise ValueError(
            f"契約容量(contract_capacity_new) 格式錯誤，應為字典格式，實際為 {type(contract_capacity_new)}"
        )
    required_keys = ["經常契約", "半尖峰契約/非夏月契約", "週六半尖峰契約", "離峰契約"]
    for key in required_keys:
        if key not in contract_capacity_new:
            raise ValueError(f"契約容量字典缺少必要的鍵: {key}")
        if (
            not isinstance(contract_capacity_new[key], (int, float))
            or contract_capacity_new[key] < 0
        ):
            raise ValueError(
                f"契約容量[{key}] 格式錯誤，應為非負數，實際為 {contract_capacity_new[key]}"
            )

    if not isinstance(tou_program, str) or not tou_program:
        raise ValueError("計費類別(tou_program) 格式錯誤，應為非空字串")
    if not isinstance(industry_class, str) or not industry_class:
        raise ValueError("行業別(industry_class) 格式錯誤，應為非空字串")
    if not isinstance(tariff_adjust_factor, (int, float)):
        raise ValueError("電費調整係數(tariff_adjust_factor) 格式錯誤，應為數字")
    if df_tou_2025 is None or not hasattr(df_tou_2025, "shape"):
        raise ValueError("df_tou_2025 格式錯誤，應為 DataFrame")
    if units is not None and not isinstance(units, (list, tuple)):
        raise ValueError("units 格式錯誤，應為 list 或 tuple 或 None")
    if dr方案選項 is not None and not isinstance(dr方案選項, (list, tuple)):
        raise ValueError("dr方案選項 格式錯誤，應為 list、tuple 或 None")
    if 即時備轉方案選項 is not None and not isinstance(即時備轉方案選項, (list, tuple)):
        raise ValueError("即時備轉方案選項 格式錯誤，應為 list、tuple 或 None")
    if 用電大戶方案 is not None and not isinstance(用電大戶方案, (list, tuple)):
        raise ValueError("用電大戶方案 格式錯誤，應為 list、tuple 或 None")

    if not isinstance(year, int) or year <= 0:
        raise ValueError("year 格式錯誤，應為正整數")

    results = []
    mode = []
    dict_summary = {}
    if config is None:
        config = config_loader.load_config()

    # set config 參數，注意，如果是改基本參數，要回首頁改，這邊能改的財務試算的那些參數
    # TODO: 真正排程影響到的契約容量是寫在這邊的config，目前是用原本的設定去跑
    # 設定主要契約容量
    main_contract_capacity = contract_capacity_old["經常契約"]
    config["電價方案"]["契約容量"] = main_contract_capacity
    config["電價方案"]["計費類別"] = tou_program
    config["電價方案"]["行業別"] = industry_class
    config["電價方案"]["電費調整係數"] = tariff_adjust_factor
    # 用電大戶義務
    if main_contract_capacity >= 5000:
        config["再生能源義務用戶"]["義務裝置容量"] = (
            config["電價方案"]["契約容量"]
            * config["再生能源義務用戶"]["義務裝置容量比例"]
            / 100
            * (
                100
                - config["再生能源義務用戶"]["早鳥抵減比例"]
                - config["再生能源義務用戶"]["既設抵減比例"]
            )
            / 100
        )
        # print(f"[debug] 義務裝置容量: {config['再生能源義務用戶']['義務裝置容量']} kW")
    else:
        config["再生能源義務用戶"]["義務裝置容量"] = 0
        用電大戶方案 = []

    # 依據手動曲線更新，如果有的話，直接照著更新的曲線來縮放 AMI 數據，否則照契約容量縮放
    # 原始資料是15分鐘，負載生成跟手拉是小時資料，所以需要縮放
    if (json_ami_hourly_update is not None) and (len(json_ami_hourly_update) > 0):
        print("[debug] 2. 使用手動曲線更新縮放 AMI 數據")

        # 重新连接到 SQLite 数据库
        conn = sqlite3.connect(get_ami_db_path())

        # 查询 'ID'
        query = "SELECT * FROM week_all WHERE ID = " + str(ID)
        df_ami_raw = pd.read_sql(query, conn)
        # 关闭数据库连接
        conn.close()
        df_ami_raw["variable"] = pd.to_datetime(
            df_ami_raw["variable"], format="%H:%M:%S.%f"
        ).dt.strftime("%H:%M")

        df_ami_raw = config_loader.scale_15min_by_hour(
            df_ami_raw, json_ami_hourly_update
        )
    elif (json_ami_15min is not None) and (len(json_ami_15min) > 0):
        print("[debug] 3. 使用手動曲線更新縮放 AMI 數據")
        df_ami_raw = config_loader.ami_15min_json_to_df(json_ami_15min)

    else:
        # 依據輸入契約容量，縮放 AMI 數據，直接用最大負載作為契約容量，與負載生成時一樣
        # origin_capacity = int(df_ami_raw["value"].max().round() / 0.9)
        print("[debug] 1. 使用契約容量縮放 AMI 數據")
        start_time = time.time()
        logger.info("start reading ami db")
        # 重新连接到 SQLite 数据库
        conn = sqlite3.connect(get_ami_db_path())

        # 查询 'ID'
        query = "SELECT * FROM week_all WHERE ID = " + str(ID)
        df_ami_raw = pd.read_sql(query, conn)
        # 关闭数据库连接
        conn.close()
        end_time = time.time()
        logger.info(
            "finished reading ami db",
            extra={"execution_time": f"{(end_time-start_time):.2f}"},
        )
        df_ami_raw["variable"] = pd.to_datetime(
            df_ami_raw["variable"], format="%H:%M:%S.%f"
        ).dt.strftime("%H:%M")

        origin_capacity = int(df_ami_raw["value"].max().round())
        # 縮放
        df_ami_raw["value"] = (
            df_ami_raw["value"] * main_contract_capacity / origin_capacity
        ).round()

    df_ami = config_loader.norm_ami(df_ami_raw, df_tou_2025, tou_program)

    dict_annual_cost_summary = config_loader.calculator_annual_cost(
        df_ami,
        tou_program,
        contract_capacity_old,
        contract_capacity_new,
        tariff_adjust_factor,
    )

    # 依據契約容量，決定台數
    if units is None:
        台數選項 = calculator.generate_fixed_step_combinations(
            int(main_contract_capacity * 0.8),
            pcs_power=int(config["儲能系統"]["單台 PCS 標稱功率"]),
            max_groups=4,
        )
    else:
        台數選項 = units

    # 如果沒有台數選項，則設為1
    if not 台數選項:
        台數選項 = [1]

    print("[debug] 台數選項", 台數選項)

    # 判斷模式組合
    dr有值 = bool(dr方案選項)
    sp有值 = bool(即時備轉方案選項)
    lc有值 = bool(用電大戶方案)

    # 共用 energy_only
    simulate_energy_only(台數選項, config, df_ami, year, results, mode, dict_summary)

    # 各功能模組呼叫
    # 1.A 只有lc
    if lc有值 and not dr有值 and not sp有值:
        simulate_lc(
            台數選項, 用電大戶方案, config, df_ami, year, results, mode, dict_summary
        )
    # 1.B 只有dr
    if dr有值 and not sp有值 and not lc有值:
        simulate_dr(
            台數選項, dr方案選項, config, df_ami, year, results, mode, dict_summary
        )

    # 1.C 只有即時備轉
    if not dr有值 and sp有值 and not lc有值:
        simulate_sp(
            台數選項,
            即時備轉方案選項,
            config,
            df_ami,
            year,
            results,
            mode,
            dict_summary,
        )

    # 2.A  DR + 即時備轉方案
    if dr有值 and sp有值 and not lc有值:
        simulate_dr(
            台數選項, dr方案選項, config, df_ami, year, results, mode, dict_summary
        )
        simulate_sp(
            台數選項,
            即時備轉方案選項,
            config,
            df_ami,
            year,
            results,
            mode,
            dict_summary,
        )
        simulate_dr_sp(
            台數選項,
            dr方案選項,
            即時備轉方案選項,
            config,
            df_ami,
            year,
            results,
            mode,
            dict_summary,
        )

    # 2.B  DR + 用電大戶方案
    if dr有值 and not sp有值 and lc有值:
        simulate_dr(
            台數選項, dr方案選項, config, df_ami, year, results, mode, dict_summary
        )
        simulate_lc(
            台數選項, 用電大戶方案, config, df_ami, year, results, mode, dict_summary
        )
        # simulate_dr_sp(台數選項, dr方案選項, 用電大戶方案, config, df_ami, year, results, mode, dict_summary)

    # 2.C  即時備轉 + 用電大戶方案
    if not dr有值 and sp有值 and lc有值:
        simulate_sp(
            台數選項,
            即時備轉方案選項,
            config,
            df_ami,
            year,
            results,
            mode,
            dict_summary,
        )
        simulate_lc(
            台數選項, 用電大戶方案, config, df_ami, year, results, mode, dict_summary
        )
        # simulate_dr_sp(台數選項, 即時備轉方案選項, 用電大戶方案, config, df_ami, year, results, mode, dict_summary)

    # 3. 全部
    if dr有值 and sp有值 and lc有值:
        simulate_lc(
            台數選項, 用電大戶方案, config, df_ami, year, results, mode, dict_summary
        )
        simulate_dr(
            台數選項, dr方案選項, config, df_ami, year, results, mode, dict_summary
        )
        simulate_sp(
            台數選項,
            即時備轉方案選項,
            config,
            df_ami,
            year,
            results,
            mode,
            dict_summary,
        )
        simulate_dr_sp(
            台數選項,
            dr方案選項,
            即時備轉方案選項,
            config,
            df_ami,
            year,
            results,
            mode,
            dict_summary,
        )

    # 合併結果
    df_results = pd.DataFrame(results)
    df_results["mode_comb"] = mode

    return df_results, dict_summary, dict_annual_cost_summary


def export_dict_summary_to_excel(dict_summary, filename="所有模式財務摘要.xlsx"):
    """
    將 dict_summary 內所有 DataFrame 輸出到同一個 Excel，每個分頁名稱為 key（如 16_電價套利）
    """

    with pd.ExcelWriter(filename) as writer:
        for key, obj in dict_summary.items():
            # key 可能是 tuple，例如 (16, '電價套利')
            if isinstance(key, tuple):
                sheet_name = f"{key[0]}_{key[1]}"
            else:
                sheet_name = str(key)
            # Excel 分頁名稱最長31字，且不能有部分特殊字元
            sheet_name = (
                sheet_name[:31]
                .replace("/", "_")
                .replace("\\", "_")
                .replace("*", "_")
                .replace("?", "_")
                .replace("[", "_")
                .replace("]", "_")
            )
            obj["df"].to_excel(writer, sheet_name=sheet_name)
    print(f"[debug] 已匯出所有分頁到 {filename}！")
