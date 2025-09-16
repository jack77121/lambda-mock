import numpy as np
import pandas as pd


def loan_pmt_per_year(loan, loan_year, loan_interest_rate_percent):
    # print('融資金額(NTD)：', loan, ' 融資年限(Year)：', loan_year, '融資年利率(%):', loan_interest_rate_percent)
    monthly_interest = loan_interest_rate_percent / 12
    monthly_loan_term = loan_year * 12  # 融資月限    = 融資年限 * 12個月
    PMT = (((1 + monthly_interest) ** monthly_loan_term) * monthly_interest) / (
        ((1 + monthly_interest) ** monthly_loan_term) - 1
    )
    loan_paid_per_year = loan * PMT * 12  # 每年還銀行的總額
    return loan_paid_per_year


# 計算每個季節的可轉移電量
def calculate_transferable_energy(
    df_ami,
    tou_program,
    contract_capacity,
    pcs_max_kW,
    time_periods,
    consider_large_consumer=False,  # 新增參數
):
    mask = (df_ami["timestamp"] >= time_periods[0][0]) & (
        df_ami["timestamp"] <= time_periods[0][1]
    )
    df_segment = df_ami.loc[mask].copy()

    df_segment["可放電功率"] = np.where(
        df_segment["tou_level"] == "high",
        df_segment["load_kw"].clip(upper=pcs_max_kW),
        0,
    )
    # 離峰充電的上限
    charging_upper_limit = (
        contract_capacity["經常契約"]
        + contract_capacity["半尖峰契約/非夏月契約"]
        + contract_capacity["週六半尖峰契約"]
        + contract_capacity["離峰契約"]
    )

    df_segment["可充電功率"] = np.where(
        # 只在離峰時段充電
        df_segment["tou_level"] == "low",
        np.minimum(charging_upper_limit - df_segment["load_kw"], pcs_max_kW).clip(
            lower=0
        ),
        0,
    )
    if any(keyword in tou_program for keyword in ["二段式", "批次"]):
        df_contract_1 = pd.DataFrame(
            {
                "is_summer": [1, 1, 1, 1],
                "tou_tag": ["尖峰", "半尖峰", "週六半尖峰", "離峰"],
                "contract_capacity": [
                    contract_capacity["經常契約"],
                    contract_capacity["經常契約"]
                    + contract_capacity["半尖峰契約/非夏月契約"],
                    contract_capacity["經常契約"]
                    + contract_capacity["半尖峰契約/非夏月契約"]
                    + contract_capacity["週六半尖峰契約"],
                    contract_capacity["經常契約"]
                    + contract_capacity["半尖峰契約/非夏月契約"]
                    + contract_capacity["週六半尖峰契約"]
                    + contract_capacity["離峰契約"],
                ],
            }
        )
        df_contract_0 = pd.DataFrame(
            {
                "is_summer": [0, 0, 0, 0],
                "tou_tag": ["尖峰", "半尖峰", "週六半尖峰", "離峰"],
                "contract_capacity": [
                    contract_capacity["經常契約"]
                    + contract_capacity["半尖峰契約/非夏月契約"],
                    contract_capacity["經常契約"]
                    + contract_capacity["半尖峰契約/非夏月契約"],
                    contract_capacity["經常契約"]
                    + contract_capacity["半尖峰契約/非夏月契約"]
                    + contract_capacity["週六半尖峰契約"],
                    contract_capacity["經常契約"]
                    + contract_capacity["半尖峰契約/非夏月契約"]
                    + contract_capacity["週六半尖峰契約"]
                    + contract_capacity["離峰契約"],
                ],
            }
        )
        # print(pd.concat([df_contract_1, df_contract_0]))
        df_segment = pd.merge(
            df_segment,
            pd.concat([df_contract_1, df_contract_0]),
            left_on=["is_summer", "tou_tag"],
            right_on=["is_summer", "tou_tag"],
            how="left",
        )

    else:
        df_contract = pd.DataFrame(
            {
                "tou_tag": ["尖峰", "半尖峰", "週六半尖峰", "離峰"],
                "contract_capacity": [
                    contract_capacity["經常契約"],
                    contract_capacity["經常契約"]
                    + contract_capacity["半尖峰契約/非夏月契約"],
                    contract_capacity["經常契約"]
                    + contract_capacity["半尖峰契約/非夏月契約"]
                    + contract_capacity["週六半尖峰契約"],
                    contract_capacity["經常契約"]
                    + contract_capacity["半尖峰契約/非夏月契約"]
                    + contract_capacity["週六半尖峰契約"]
                    + contract_capacity["離峰契約"],
                ],
            }
        )
        # print(df_contract)
        df_segment = pd.merge(
            df_segment, df_contract, left_on="tou_tag", right_on="tou_tag", how="left"
        )

    df_segment["over_capacity_kw"] = (
        df_segment["load_kw"] - df_segment["contract_capacity"]
    ).clip(lower=0)

    # 計算超約調整等價電量，若是超約時，就無法完全套利，需扣除在其他時段的可放電量所減少的效益
    # 依照電力需求時段的重要性排序：尖峰最高，離峰最低
    tou_tag_mapping = {
        "尖峰": 0,  # 最高電價時段
        "半尖峰": 0.52,  # 次高電價時段
        "週六半尖峰": 0,  # 週六半尖峰時段
        "離峰": 1,  # 最低電價時段
    }

    df_segment["tou_tag_numeric"] = df_segment["tou_tag"].replace(tou_tag_mapping)
    df_segment["weight_over_capacity_kw"] = (
        df_segment["over_capacity_kw"] * df_segment["tou_tag_numeric"]
    )

    df_ami2 = (
        df_segment.groupby(["season", "weekday2"])
        .agg(
            {
                "可放電功率": "sum",
                "可充電功率": "sum",
                "over_capacity_kw": "sum",
                "weight_over_capacity_kw": "sum",
            }
        )
        .div(4)
        .reset_index()
        .rename(
            columns={
                "可放電功率": "可放電量",
                "可充電功率": "可充電量",
                "over_capacity_kw": "超約電量",
                "weight_over_capacity_kw": "超約調整等價電量",
            }
        )
        .round(2)
    )

    # 若考慮 large consumer，直接統計 18:00~19:45 這段時段
    if consider_large_consumer:
        mask_lc = (df_segment["timestamp"] >= "18:00") & (
            df_segment["timestamp"] <= "19:45"
        )
        df_lc = df_segment.loc[mask_lc]
        lc_stats = (
            df_lc.groupby(["season", "weekday2"])
            .agg({"可放電功率": "sum", "over_capacity_kw": "sum"})
            .div(4)
            .reset_index()
            .rename(
                columns={
                    "可放電功率": "用電大戶義務可放電量",
                    "over_capacity_kw": "用電大戶超約電量",
                }
            )
            .round()
        )
        # 只用在儲能可以避免超約下，又同時參與用電大戶

        df_ami2 = pd.merge(df_ami2, lc_stats, on=["season", "weekday2"], how="left")
        df_ami2["避免超約電量"] = (
            df_ami2["超約電量"] - df_ami2["用電大戶超約電量"]
        ).clip(lower=0)

    return df_segment, df_ami2


def batch_calculate_transfered_energy(
    df_ami2, avail_kWh_series, season, rtt_loss_rate, consider_large_consumer=False
):
    """
    同時回傳一般可轉移電量與用電大戶義務可轉移電量
    Returns:
        dict: {
            '可轉移電量': pd.Series,
            '用電大戶義務可轉移電量': pd.Series
        }
    """
    df_season = df_ami2.query("season == @season").copy()

    # 一般可轉移電量
    results_normal = []
    for avail_kWh in avail_kWh_series:
        df_season["可轉移電量"] = np.minimum(
            avail_kWh * np.sqrt(1 - rtt_loss_rate),
            np.minimum(df_season["可放電量"], df_season["可充電量"]),
        )

        # 如果超約可以用儲能完全抵銷，需扣減超約調整等價電量，否則，就不管超約！
        # 記住，夏月，非夏月，結果可能不同，可能非夏月可以避免超約，夏月不行
        if avail_kWh * np.sqrt(1 - rtt_loss_rate) > df_season["超約電量"].max():
            df_season["可轉移電量"] = (
                df_season["可轉移電量"] - df_season["超約調整等價電量"]
            ).clip(lower=0)

        mean_kWh = df_season[
            df_season["weekday2"].isin(
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            )
        ]["可轉移電量"].mean()
        results_normal.append(round(mean_kWh, 2))

    # 用電大戶義務可轉移電量
    results_large_consumer = []
    if consider_large_consumer and "用電大戶義務可放電量" in df_season.columns:
        for avail_kWh in avail_kWh_series:
            # 如果超約可以用儲能完全抵銷，則用電大戶義務可轉移電量將會減少，反之，就跟原本一樣
            if avail_kWh * np.sqrt(1 - rtt_loss_rate) > df_season["超約電量"].max():
                # 每天計算
                df_season["避免超約後可用電量"] = (
                    avail_kWh * np.sqrt(1 - rtt_loss_rate) - df_season["避免超約電量"]
                ).clip(lower=0)
                df_season["用電大戶義務可轉移電量"] = np.minimum(
                    df_season["避免超約後可用電量"],
                    np.minimum(
                        df_season["用電大戶義務可放電量"], df_season["可充電量"]
                    ),
                ).clip(lower=0)
                mean_kWh = df_season[
                    df_season["weekday2"].isin(
                        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    )
                ]["用電大戶義務可轉移電量"].mean()
                results_large_consumer.append(round(mean_kWh, 2))

            else:
                df_season["用電大戶義務可轉移電量"] = np.minimum(
                    avail_kWh * np.sqrt(1 - rtt_loss_rate),
                    np.minimum(
                        df_season["用電大戶義務可放電量"], df_season["可充電量"]
                    ),
                ).clip(lower=0)
                mean_kWh = df_season[
                    df_season["weekday2"].isin(
                        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    )
                ]["用電大戶義務可轉移電量"].mean()
                results_large_consumer.append(round(mean_kWh, 2))
    else:
        results_large_consumer = [0] * len(avail_kWh_series)

    return {
        "可轉移電量": pd.Series(results_normal),
        "用電大戶義務可轉移電量": pd.Series(results_large_consumer),
    }


# 篩出固定時間區間的資料
def filter_summer_week_data(
    df, start_time_str, end_time_str, only_summer=True, only_weekday=True
):
    """
    根據夏月與工作日條件，篩選指定時間區間內的資料。

    Parameters:
        df (pd.DataFrame): 原始資料，需包含 'is_summer', 'weekday', 'timestamp' 欄位
        start_time_str (str): 起始時間 (格式如 '18:00')
        end_time_str (str): 結束時間 (格式如 '20:00')
        only_summer (bool): 是否僅篩選夏月資料 (is_summer == 1)
        only_weekday (bool): 是否僅篩選工作日資料 (weekday == 'week')

    Returns:
        pd.DataFrame: 篩選後的資料
    """
    # print ('filter_summer_week_data', start_time_str, end_time_str)

    df_filtered = df.copy()

    if only_summer:
        df_filtered = df_filtered[df_filtered["is_summer"] == 1]
    if only_weekday:
        df_filtered = df_filtered[df_filtered["weekday"] == "week"]

    # df_filtered['timestamp'] = pd.to_datetime(df_filtered['timestamp'])
    df_filtered["timestamp"] = pd.to_datetime(df_filtered["timestamp"], format="%H:%M")

    # start_time = pd.to_datetime(start_time_str).time()
    # end_time = pd.to_datetime(end_time_str).time()

    start_time = pd.to_datetime(start_time_str, format="%H:%M").time()
    end_time = pd.to_datetime(end_time_str, format="%H:%M").time()

    mask = (df_filtered["timestamp"].dt.time >= start_time) & (
        df_filtered["timestamp"].dt.time < end_time
    )
    return df_filtered[mask]


# 計算 最小的DR容量
def calculate_dr_capacity(df_ami, df_ami2, start_time, end_time, dr_hr, bms_kWh):
    df_season = df_ami2[
        (df_ami2["season"] == "summer")
        & (
            df_ami2["weekday2"].isin(
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            )
        )
    ]

    # 計算抑低時段長度（小時）
    dr_avail_kWh = bms_kWh / dr_hr

    # 夏月工作日：計算平均可放電量
    df_filtered2 = filter_summer_week_data(
        df_ami, start_time, end_time, only_summer=True, only_weekday=True
    )

    df_grouped = (
        df_filtered2.groupby("weekday2")
        .agg({"可放電功率": "mean", "weekday": "count", "over_capacity_kw": "mean"})
        .reset_index()
    )

    df_grouped["weekday"] = df_grouped["weekday"] / 4
    df_grouped = df_grouped.rename(
        columns={
            "可放電功率": "平均可放電量",
            "weekday": "小時數",
            "over_capacity_kw": "平均超約電量",
        }
    )

    # 儲能可解決超約時，計算超約的影響，並扣掉多降的；反之，就不避免超約，套到滿
    if bms_kWh > df_season["超約電量"].max():
        # 考慮放電限制
        df_grouped["平均最大可放電量"] = np.minimum(
            df_grouped["平均可放電量"],
            dr_avail_kWh - df_grouped["平均超約電量"].clip(lower=0),
        )
    else:
        df_grouped["平均最大可放電量"] = np.minimum(
            df_grouped["平均可放電量"], dr_avail_kWh
        )

    # 非夏月工作日 baseline
    df_baseline = filter_summer_week_data(
        df_ami, start_time, end_time, only_summer=False, only_weekday=True
    )
    df_baseline = (
        df_baseline.groupby("weekday2")
        .agg({"可放電功率": "mean", "weekday": "count"})
        .reset_index()
    )

    # 最大可抑低量：取 baseline 和最大可放電量的最小值
    df_grouped["最大可抑低量"] = np.minimum(
        df_grouped["平均最大可放電量"], df_baseline["可放電功率"]
    )

    # 計算平均抑低契約容量
    dr_contract_kw = df_grouped["最大可抑低量"].mean()

    return df_grouped, dr_contract_kw


# 計算模擬即時備轉所需要參數
# max_bms_kW 最大輸出功率
def spining_weekend_load_kw_stats(df, max_bms_kW):
    total_mean = df["load_kw"].mean()
    total_mean = min(total_mean, max_bms_kW)

    filtered = df[df["load_kw"] > 1000]
    ratio = len(filtered) / len(df) if len(df) > 0 else 0
    filtered_mean = filtered["load_kw"].mean() if ratio > 0 else 0
    filtered_mean = min(filtered_mean, max_bms_kW) if ratio > 0 else 0

    return pd.Series(
        {
            "load_kw_mean": total_mean,
            "load_kw_gt1000_mean": filtered_mean,
            "gt1000_ratio": ratio,
        }
    )


# 計算即時備轉模擬統計資料，好計算收益
def compute_spinning_summary(df_ami_week, max_bms_kW, avail_kWh):
    """
    計算即時備轉模擬統計表格。
    - df_ami_week: 含有 load_kw, 可放電功率, tou_level, tou, season 等欄位的 DataFrame
    - max_bms_kW: 單位為 kW，整體最大輸出功率
    - avail_kWh: 加總的電池容量（單位 kWh）
    回傳: 包含可放電功率、小時數、平均負載等統計欄位的 df_ami_week2
    """
    # 標記尖峰與非尖峰
    df_ami_week = df_ami_week.copy()
    df_ami_week["spinning_level"] = np.where(df_ami_week["tou_level"] == "high", 1, 0)

    # 計算小時數與平均可放電功率
    df_ami_week2 = (
        df_ami_week.groupby(["season", "spinning_level"])
        .agg({"可放電功率": "mean", "tou": "count", "load_kw": "mean"})
        .reset_index()
        .rename(columns={"tou": "小時數"})
    )

    df_ami_week2["小時數"] = df_ami_week2["小時數"] / (4 * 5)
    df_ami_week2["總放電時數"] = avail_kWh / df_ami_week2["可放電功率"]

    # 計算負載統計
    df_stats = (
        df_ami_week.groupby(["season", "spinning_level"], group_keys=False)
        .apply(
            lambda group, **kwargs: spining_weekend_load_kw_stats(group, max_bms_kW),
            include_groups=False,
        )
        .reset_index()
    )

    df_ami_week2 = pd.concat(
        [
            df_ami_week2,
            df_stats[["load_kw_gt1000_mean", "gt1000_ratio", "load_kw_mean"]],
        ],
        axis=1,
    )

    return df_ami_week2


# 計算非工作日的即時備轉收益，同時包括夏月跟非夏月
def compute_spinning_gain_A(
    series_ami_weekend, non_working_days, capacity_price, performance_price
):
    """
    計算非工作日的即時備轉收益
    """
    rate = capacity_price + performance_price

    # 單一用戶收益計算
    sp_A_case_single = (
        non_working_days
        * 24
        * rate
        * series_ami_weekend["load_kw_gt1000_mean"]
        / 1000
        * series_ami_weekend["gt1000_ratio"]
    )

    # 聚合後收益計算
    sp_A_case_agg = (
        non_working_days * 24 * rate * series_ami_weekend["load_kw_mean"] / 1000
    )

    return sp_A_case_single, sp_A_case_agg


# B. 計算工作日的即時備轉收益，包括夏月跟非夏月
# 同時考慮執行需量反應負載管理措施的情境
def compute_spinning_gain_B(
    df, season, days, capacity_price, performance_price, dr_hour, cycles
):
    # 尖峰的行為
    row_1 = df[(df["season"] == season) & (df["spinning_level"] == 1)].iloc[0]
    # 非尖峰的行為
    row_0 = df[(df["season"] == season) & (df["spinning_level"] == 0)].iloc[0]

    # TODO：放電時段不投的時數可能可以少點，所以先用round取代ceil
    if season == "summer":
        # 假設放電時段都不投
        不可投標時數_1 = max(np.ceil(row_1["總放電時數"]), dr_hour)
        # 假設充放電時數一樣，充電也不投
        不可投標時數_0 = row_1["總放電時數"].round()
    else:
        # 非夏月的情況，才會受2循環影響
        # 假設放電時段都不投
        不可投標時數_1 = max(np.ceil(row_1["總放電時數"]), dr_hour) * cycles
        # 假設充放電時數一樣，充電也不投
        不可投標時數_0 = row_1["總放電時數"].round() * cycles

    小時數_1 = row_1["小時數"]
    小時數_0 = row_0["小時數"]

    daily_benefit_single = (capacity_price + performance_price) * (
        小時數_1 - 不可投標時數_1
    ) * row_1["load_kw_gt1000_mean"] / 1000 * row_1["gt1000_ratio"] + (
        capacity_price + performance_price
    ) * (小時數_0 - 不可投標時數_0) * row_0["load_kw_gt1000_mean"] / 1000 * row_0[
        "gt1000_ratio"
    ]
    total_single = days * daily_benefit_single

    # 聚合場域計算
    daily_benefit_agg = (capacity_price + performance_price) * (
        小時數_1 - 不可投標時數_1
    ) * row_1["load_kw_mean"] / 1000 + (capacity_price + performance_price) * (
        小時數_0 - 不可投標時數_0
    ) * row_0["load_kw_mean"] / 1000
    total_agg = days * daily_benefit_agg

    return total_single, total_agg


def compute_total_spinning_gain_sum(
    series_ami_weekend,
    df_ami_week2,
    non_working_days,
    working_days_summer,
    working_days_not_summer,
    capacity_price,
    performance_price,
    dr_hour,
    cycles,
):
    # Case A: 非工作日收益
    sp_A_single, sp_A_agg = compute_spinning_gain_A(
        series_ami_weekend, non_working_days, capacity_price, performance_price
    )
    # print('case A')
    # print('sp_A_single', sp_A_single)
    # print('sp_A_agg', sp_A_agg)

    # Case B: 非夏月收益
    sp_B_single_ns, sp_B_agg_ns = compute_spinning_gain_B(
        df_ami_week2,
        "not_summer",
        working_days_not_summer,
        capacity_price,
        performance_price,
        dr_hour,
        cycles,
    )

    # Case B: 夏月收益
    sp_B_single_s, sp_B_agg_s = compute_spinning_gain_B(
        df_ami_week2,
        "summer",
        working_days_summer,
        capacity_price,
        performance_price,
        dr_hour,
        cycles,
    )

    # 合計總收益
    total_single = sp_A_single + sp_B_single_ns + sp_B_single_s
    total_agg = sp_A_agg + sp_B_agg_ns + sp_B_agg_s

    return total_single, total_agg


# 計算分析的台數
def generate_fixed_step_combinations(contract_capacity, pcs_power=125, max_groups=4):
    max_units = contract_capacity // pcs_power

    if max_units == 0:
        return []

    step = max(1, max_units // max_groups)
    unit_options = list(range(step, max_units + 1, step))[:max_groups]

    # result = []
    # for i, units in enumerate(unit_options, start=1):
    #     result.append({
    #         '組合': f'組合{i}',
    #         '台數': units,
    #         '總功率(kW)': units * pcs_power
    #     })
    return unit_options


def count_high_peaks(tou_levels):
    peaks = 0
    in_peak = False

    for level in tou_levels:
        if level == "high":
            if not in_peak:
                peaks += 1
                in_peak = True
        else:
            in_peak = False  # reset if not high

    return peaks


def compute_large_consumer_reduction(
    obligated_capacity_kW: float,
    total_discharge_kWh: float,
    plan_type: str = "義務時數型",  # 'FHC' = 義務時數型, 'TGR' = 累進回饋型
) -> float:
    """
    計算年度電費扣減金額。

    total_discharge_kWh: 年度總放電度數 (kWh)
    obligated_capacity_kW: 義務裝置容量 (kW)
    plan_type: 'FHC' 或 'TGR'

    回傳: 電費扣減總金額 (元)
    """
    if plan_type == "義務時數型":
        obligated_discharge_kWh = obligated_capacity_kW * 400
        reduction_kWh = max(total_discharge_kWh - obligated_discharge_kWh, 0)
        return reduction_kWh * 10

    elif plan_type == "累進回饋型":
        tier1 = obligated_capacity_kW * 150
        tier2 = obligated_capacity_kW * 400

        tier1_kWh = min(total_discharge_kWh, tier1)
        tier2_kWh = min(max(total_discharge_kWh - tier1, 0), tier2 - tier1)
        tier3_kWh = max(total_discharge_kWh - tier2, 0)

        return tier1_kWh * 1 + tier2_kWh * 2 + tier3_kWh * 5

    else:
        raise ValueError("plan_type 必須為 '義務時數型' 或 '累進回饋型'")


def calculate_max_arbitrage_profit(config):
    """
    計算儲能系統在理想情況下的最大電價套利收益（年總額）。
    假設每日完整充放一次，SOC與損失率皆考慮，使用調整後電價計算。

    Returns:
        float: 年電價套利淨收益（單位：元）
    """
    # 儲能參數
    儲能容量 = config["儲能系統"]["儲能容量"]
    SOC上限 = config["儲能系統"]["SOC上限"]
    SOC下限 = config["儲能系統"]["SOC下限"]
    損失率 = config["儲能系統"]["電能損失率(Round Trip)"] / 100
    每日最大循環次數 = config["儲能系統"]["每日最大循環次數"]

    # 調整後電價與天數
    夏月天數 = config["電價方案"]["夏月天數"]
    非夏月天數 = config["電價方案"]["非夏月天數"]
    夏月最高電價 = config["電價方案"]["調整後夏月最高電價"]
    夏月最低電價 = config["電價方案"]["調整後夏月最低電價"]
    非夏月最高電價 = config["電價方案"]["調整後非夏月最高電價"]
    非夏月最低電價 = config["電價方案"]["調整後非夏月最低電價"]

    # 每日最大可轉移度數
    base_kWh = 儲能容量 * (SOC上限 - SOC下限) / 100 * np.sqrt(1 - 損失率)
    夏月每日可轉移度數 = base_kWh
    非夏月每日可轉移度數 = base_kWh * 每日最大循環次數

    # 理論收益計算
    a = (夏月最高電價 - 夏月最低電價) * 夏月天數 * 夏月每日可轉移度數 + (
        非夏月最高電價 - 非夏月最低電價
    ) * 非夏月天數 * 非夏月每日可轉移度數

    b = (
        夏月最低電價 * 夏月天數 * 夏月每日可轉移度數 * 損失率
        + 非夏月最低電價 * 非夏月天數 * 非夏月每日可轉移度數 * 損失率
    )

    電價差收益 = a - b

    return round(電價差收益, 2)


def calculate_max_large_consumer_profit(config, lc_mode):
    """
    計算用電大戶方案下的最大理論收益（限制為每日 2 小時最大放電，考慮儲能與PCS功率限制）。

    Args:
        config (dict): 模擬參數設定
        calculator (object): 提供 compute_large_consumer_reduction 方法的物件
        lc_mode (str): 用電大戶方案代碼

    Returns:
        float: 最大預估收益（元/年）
    """
    # 參數提取
    儲能容量 = config["儲能系統"]["儲能容量"]
    SOC上限 = config["儲能系統"]["SOC上限"]
    SOC下限 = config["儲能系統"]["SOC下限"]
    PCS功率 = config["儲能系統"]["PCS 標稱功率"]
    義務裝置容量 = config["再生能源義務用戶"]["義務裝置容量"]
    損失率 = config["儲能系統"]["電能損失率(Round Trip)"] / 100

    夏月天數 = config["電價方案"]["夏月天數"]
    非夏月天數 = config["電價方案"]["非夏月天數"]

    # 每日最大放電度數（受電量與功率限制）
    base_kWh = 儲能容量 * (SOC上限 - SOC下限) / 100 * np.sqrt(1 - 損失率)
    max_power_kWh = PCS功率 * 2  # 每日最大放電量（取決於 2 小時內可釋出功率）
    每日最大可放電度數 = min(base_kWh, max_power_kWh)

    # 年度總放電度數（假設夏/非夏每日皆可完整放電）
    總放電度數 = (夏月天數 + 非夏月天數) * 每日最大可放電度數

    # 最大收益計算
    max_profit = compute_large_consumer_reduction(義務裝置容量, 總放電度數, lc_mode)
    if max_profit == 0:
        return 1.0

    return round(max_profit, 2)


def calculate_max_dr_daily_time_range_profit(config):
    """
    計算「日選時段型」需量反應的最大理論收益（元），
    抑低契約容量取 min(PCS功率, 儲能可用容量 ÷ 執行時數)。

    Returns:
        float: 年最大收益（元）
    """
    # 儲能參數
    儲能容量 = config["儲能系統"]["儲能容量"]
    SOC上限 = config["儲能系統"]["SOC上限"]
    SOC下限 = config["儲能系統"]["SOC下限"]
    PCS功率 = config["儲能系統"]["PCS 標稱功率"]
    損失率 = config["儲能系統"]["電能損失率(Round Trip)"] / 100
    base_kWh = 儲能容量 * (SOC上限 - SOC下限) / 100 * np.sqrt(1 - 損失率)

    # DR 參數
    執行時數 = config["日選時段型"]["執行時數"]
    當日執行率 = config["日選時段型"]["當日執行率"]
    扣減電價 = config["日選時段型"]["流動電費扣減費率"]
    扣減倍率 = config["日選時段型"]["扣減比率"]
    可參與天數 = config["日選時段型"]["5月-10月可參與天數"]

    # 抑低契約容量取儲能能力與功率限制的最小值
    最大有效抑低容量 = min(PCS功率, base_kWh / 執行時數)

    # 年收益估算
    日選收益 = (
        最大有效抑低容量
        * 當日執行率
        * 執行時數
        * 扣減電價
        * 扣減倍率
        * 可參與天數
        / 10000
    )

    return round(日選收益, 2)


def calculate_max_spinning_service_profit(config):
    """
    計算即時備轉服務最大理論收益（元/年），區分夏月工作日、非夏月工作日、非工作日。
    """
    # 價格與條件參數
    投標容量 = config["即時備轉"]["投標容量"]
    容量價格 = config["即時備轉"]["容量價格"]
    效能價格 = config["即時備轉"]["1級效能價格"]
    得標比例 = config["即時備轉"]["得標容量比例"] / 100
    折扣比例 = config["即時備轉"]["折扣比例"] / 100
    每月觸發次數 = config["即時備轉"]["每月觸發次數"]
    日前電價 = config["即時備轉"]["日前電能邊際價格"]

    # 時間參數
    夏月天數 = config["電價方案"]["夏月天數"]
    非夏月天數 = config["電價方案"]["非夏月天數"]
    不可投標天數 = config["可參與輔助服務時數"]["不可投標天數"]
    日選執行時數 = config["日選時段型"]["執行時數"]

    # 電池參數
    儲能容量 = config["儲能系統"]["儲能容量"]
    SOC上限 = config["儲能系統"]["SOC上限"]
    SOC下限 = config["儲能系統"]["SOC下限"]
    PCS功率 = config["儲能系統"]["PCS 標稱功率"]
    每日最大循環次數 = config["儲能系統"]["每日最大循環次數"]

    base_kWh = 儲能容量 * (SOC上限 - SOC下限) / 100
    電池放電時數 = np.ceil(base_kWh / PCS功率)

    # 可投標日數區分
    夏月工作日 = 夏月天數
    非夏月工作日 = 非夏月天數
    非工作日 = 365 - 夏月工作日 - 非夏月工作日 - 不可投標天數

    # 各時段可參與時數
    夏月工作日執行時數 = 24 - max(日選執行時數, 電池放電時數) * 2
    非夏月工作日執行時數 = (
        24
        - max(日選執行時數, 電池放電時數) * 2
        - 電池放電時數 * 2 * (每日最大循環次數 - 1)
    )
    非工作日執行時數 = 24

    # === 輔助服務收益 a ===
    total_hours = (
        夏月工作日 * 夏月工作日執行時數
        + 非夏月工作日 * 非夏月工作日執行時數
        + 非工作日 * 非工作日執行時數
    )

    a = (容量價格 + 效能價格) * total_hours * 投標容量 / 1000 * 得標比例 * 折扣比例

    # === 額外電能收益 b ===
    b = 每月觸發次數 * 日前電價 * 12 * 投標容量 / 1000

    return round(a + b, 2)


# 電價套利
def get_arbitrage_formula_display_data(config, score=None):
    def get_strategy_suggestion(score):
        if score is None or score == 0:
            return {
                "label": "不適用",
                "suggestions": [
                    "您目前無法參與此方案，可能尚未啟用該功能或參數限制導致收益為 0。"
                ],
            }
        elif score >= 99:
            return {
                "label": "接近最佳",
                "suggestions": [
                    "績效接近理論最大值！若想要突破理論值，可調整 SOC 上下限或降低損失率，增加單次循環可充放的電量。",
                ],
            }
        else:
            return {
                "label": "優化建議",
                "suggestions": [
                    "收益未達最大值，可能因離峰時段無法充分充電，或尖峰時段未能完全放電，顯示電池配置容量可能太大！",
                ],
            }

    return {
        "公式解釋": [
            "每日可轉移度數 = 儲能容量 × (SOC上限 - SOC下限) ÷ 100",
            "夏月每日可轉移度數 = 每日可轉移度數",
            "非夏月每日可轉移度數 = 每日可轉移度數 × 每日最大循環次數",
            "收益項目 = [(夏月最高電價 - 夏月最低電價) × 夏月天數 × 夏月每日可轉移度數 +",
            "               (非夏月最高電價 - 非夏月最低電價) × 非夏月天數 × 非夏月每日可轉移度數] × (1 - 損失率 ÷ 2)",
            "損耗成本 = [夏月最低電價 × 夏月天數 × 夏月每日可轉移度數 +",
            "               非夏月最低電價 × 非夏月天數 × 非夏月每日可轉移度數] × 損失率",
            "電價套利淨收益 = 收益項目 - 損耗成本",
        ],
        "參數": [
            {
                "label": "儲能容量",
                "value": config["儲能系統"]["儲能容量"],
                "unit": "kWh",
            },
            {"label": "SOC上限", "value": config["儲能系統"]["SOC上限"], "unit": "%"},
            {"label": "SOC下限", "value": config["儲能系統"]["SOC下限"], "unit": "%"},
            {
                "label": "每日最大循環次數",
                "value": config["儲能系統"]["每日最大循環次數"],
                "unit": "次",
            },
            {
                "label": "損失率",
                "value": config["儲能系統"]["電能損失率(Round Trip)"],
                "unit": "%",
            },
            {
                "label": "夏月天數",
                "value": config["電價方案"]["夏月天數"],
                "unit": "天",
            },
            {
                "label": "非夏月天數",
                "value": config["電價方案"]["非夏月天數"],
                "unit": "天",
            },
            {
                "label": "夏月最高電價",
                "value": config["電價方案"]["調整後夏月最高電價"],
                "unit": "元/kWh",
            },
            {
                "label": "夏月最低電價",
                "value": config["電價方案"]["調整後夏月最低電價"],
                "unit": "元/kWh",
            },
            {
                "label": "非夏月最高電價",
                "value": config["電價方案"]["調整後非夏月最高電價"],
                "unit": "元/kWh",
            },
            {
                "label": "非夏月最低電價",
                "value": config["電價方案"]["調整後非夏月最低電價"],
                "unit": "元/kWh",
            },
        ],
        "策略建議": get_strategy_suggestion(score),
    }


# 用電大戶義務
def get_large_consumer_formula_display_data(config, score=None):
    def get_strategy_suggestion(score):
        if score is None or score == 0:
            return {
                "label": "不適用",
                "suggestions": ["契約容量5000kW以上才需要滿足用電大戶義務。"],
            }
        elif score >= 99:
            return {
                "label": "接近最佳",
                "suggestions": [
                    "績效接近理論最大值！若想要突破理論值，可調整 SOC 上下限或降低損失率，增加單次循環可充放的電量。",
                ],
            }
        else:
            return {
                "label": "優化建議",
                "suggestions": [
                    "收益未達最大值，可能因離峰時段無法充分充電，或義務時段的下午6-8點未能完全放電，顯示電池配置容量可能太大！",
                ],
            }

    return {
        "公式解釋": [
            "可放電電量限制 = 儲能容量 × (SOC上限 - SOC下限) ÷ 100 * np.sqrt(1 - 損失率)",
            "功率限制電量 = PCS標稱功率 × 2（即每日 18–20 時可釋放電量）",
            "每日可放電度數 = min(可放電電量限制, 功率限制電量)",
            "總放電度數 = (夏月天數 + 非夏月天數) × 每日可放電度數",
            # ↓ 根據 plan_type 分類說明 ↓
            "▍[方案一：義務時數型（FHC）]",
            "年度義務放電量 = 義務裝置容量 × 400",
            "可扣減放電量 = max(總放電度數 − 年度義務放電量, 0)",
            "收益（元）= 可扣減放電量 × 10（元/kWh）",
            "▍[方案二：累進回饋型（TGR）]",
            "級距一：0–150 × 義務容量，每度回饋 1 元",
            "級距二：150–400 × 義務容量，每度回饋 2 元",
            "級距三：超過 400 × 義務容量，每度回饋 5 元",
            "收益（元）= 各級距放電量 × 對應回饋金額",
        ],
        "參數": [
            {
                "label": "儲能容量",
                "value": config["儲能系統"]["儲能容量"],
                "unit": "kWh",
            },
            {"label": "SOC上限", "value": config["儲能系統"]["SOC上限"], "unit": "%"},
            {"label": "SOC下限", "value": config["儲能系統"]["SOC下限"], "unit": "%"},
            {
                "label": "損失率",
                "value": config["儲能系統"]["電能損失率(Round Trip)"],
                "unit": "%",
            },
            {
                "label": "PCS標稱功率",
                "value": config["儲能系統"]["PCS 標稱功率"],
                "unit": "kW",
            },
            {
                "label": "義務裝置容量",
                "value": config["再生能源義務用戶"]["義務裝置容量"],
                "unit": "kW",
            },
            {
                "label": "夏月天數",
                "value": config["電價方案"]["夏月天數"],
                "unit": "天",
            },
            {
                "label": "非夏月天數",
                "value": config["電價方案"]["非夏月天數"],
                "unit": "天",
            },
        ],
        "策略建議": get_strategy_suggestion(score),
    }


# 日選時段型需量反應
def get_dr_daily_time_range_formula_display_data(config, score=None):
    def get_strategy_suggestion(score):
        if score is None or score == 0:
            return {
                "label": "不適用",
                "suggestions": [
                    "您目前無法參與此方案，可能與其他方案衝突，例如已經選用用電大戶義務。"
                ],
            }
        elif score >= 99:
            return {
                "label": "接近最佳",
                "suggestions": [
                    "績效接近理論最大值！若想要突破理論值，可調整 SOC 上下限或降低損失率，增加單次循環可充放的電量。",
                ],
            }
        else:
            return {
                "label": "優化建議",
                "suggestions": [
                    "離峰時段無法充分充電，把電池充飽。",
                    "日選時段的下午6-8時(2H)、下午4-8時(4H)、下午4-10時(6H)用電不足，導致未能完全放電，顯示電池配置容量可能太大！",
                ],
            }

    return {
        "公式解釋": [
            "可用電量 = 儲能容量 × (SOC上限 − SOC下限) ÷ 100 * np.sqrt(1 - 損失率)",
            "最大有效抑低容量 = min(PCS標稱功率, 可用電量 ÷ 執行時數)",
            "日選收益 = 最大有效抑低容量 × 當日執行率 /100 × 執行時數 × 扣減電價 × 扣減倍率/100 × 可參與天數",
        ],
        "參數": [
            {
                "label": "儲能容量",
                "value": config["儲能系統"]["儲能容量"],
                "unit": "kWh",
            },
            {"label": "SOC上限", "value": config["儲能系統"]["SOC上限"], "unit": "%"},
            {"label": "SOC下限", "value": config["儲能系統"]["SOC下限"], "unit": "%"},
            {
                "label": "損失率",
                "value": config["儲能系統"]["電能損失率(Round Trip)"],
                "unit": "%",
            },
            {
                "label": "PCS標稱功率",
                "value": config["儲能系統"]["PCS 標稱功率"],
                "unit": "kW",
            },
            {
                "label": "執行時數",
                "value": config["日選時段型"]["執行時數"],
                "unit": "小時",
            },
            {
                "label": "當日執行率",
                "value": config["日選時段型"]["當日執行率"],
                "unit": "%",
            },
            {
                "label": "扣減電價",
                "value": config["日選時段型"]["流動電費扣減費率"],
                "unit": "元/kWh",
            },
            {
                "label": "扣減倍率",
                "value": config["日選時段型"]["扣減比率"],
                "unit": "%",
            },
            {
                "label": "可參與天數",
                "value": config["日選時段型"]["5月-10月可參與天數"],
                "unit": "天",
            },
        ],
        "策略建議": get_strategy_suggestion(score),
    }


# 即時備轉服務
def get_spinning_service_formula_display_data(config, score=None):
    """
    回傳即時備轉服務收益估算的公式說明與參數。
    """
    # 參數提取
    儲能容量 = config["儲能系統"]["儲能容量"]
    SOC上限 = config["儲能系統"]["SOC上限"]
    SOC下限 = config["儲能系統"]["SOC下限"]
    PCS功率 = config["儲能系統"]["PCS 標稱功率"]
    base_kWh = 儲能容量 * (SOC上限 - SOC下限) / 100
    電池放電時數 = int(np.ceil(base_kWh / PCS功率))

    日選執行時數 = config["日選時段型"]["執行時數"]
    每日最大循環次數 = config["儲能系統"]["每日最大循環次數"]

    夏月天數 = config["電價方案"]["夏月天數"]
    非夏月天數 = config["電價方案"]["非夏月天數"]
    不可投標天數 = config["可參與輔助服務時數"]["不可投標天數"]

    夏月工作日 = 夏月天數
    非夏月工作日 = 非夏月天數
    非工作日 = 365 - 夏月工作日 - 非夏月工作日 - 不可投標天數

    def get_strategy_suggestion(score):
        if score is None or score == 0:
            return {
                "label": "不適用",
                "suggestions": [
                    "您目前無法參與此方案，可能與其他方案衝突，例如已經選用用電大戶義務。"
                ],
            }
        elif score >= 99:
            return {
                "label": "接近最佳",
                "suggestions": [
                    "績效接近理論最大值！若想要突破理論值，可調整 SOC 上下限或降低損失率，增加單次循環可充放的電量。",
                ],
            }
        else:
            return {
                "label": "優化建議",
                "suggestions": [
                    "待命率超過1MW的時段太少，導致可投標量太少。",
                    "搭配電價套利、日選時段時段型需量反應等方案，配合方案充放電，導致可投標的時數減少。",
                ],
            }

    return {
        "公式解釋": [
            "base_kWh = 儲能容量 × (SOC上限 - SOC下限) ÷ 100",
            "電池放電時數 = ceil(base_kWh ÷ PCS 標稱功率)",
            "夏月工作日執行時數 = 24 - max(日選執行時數, 電池放電時數) × 2",
            "非夏月工作日執行時數 = 24 - max(日選執行時數, 電池放電時數) × 2 + 電池放電時數 × 2 × 每日最大循環次數",
            "非工作日執行時數 = 24",
            "total_hours = 夏月工作日 × 夏月工作日執行時數 + 非夏月工作日 × 非夏月工作日執行時數 + 非工作日 × 24",
            "輔助收益 a = (容量價格 + 效能價格) × total_hours × 投標容量 ÷ 1000 × 得標比例 × 折扣比例",
            "輔助收益 b = 每月觸發次數 × 日前電價 × 12個月 × 投標容量 ÷ 1000",
            "總收益 = a + b",
        ],
        "參數": [
            {"label": "儲能容量", "value": 儲能容量, "unit": "kWh"},
            {"label": "SOC上限", "value": SOC上限, "unit": "%"},
            {"label": "SOC下限", "value": SOC下限, "unit": "%"},
            {"label": "PCS 標稱功率", "value": PCS功率, "unit": "kW"},
            {"label": "base_kWh", "value": base_kWh, "unit": "kWh"},
            {"label": "電池放電時數", "value": 電池放電時數, "unit": "小時"},
            {"label": "每日最大循環次數", "value": 每日最大循環次數, "unit": "次"},
            {"label": "日選執行時數", "value": 日選執行時數, "unit": "小時"},
            {"label": "夏月天數", "value": 夏月天數, "unit": "天"},
            {"label": "非夏月天數", "value": 非夏月天數, "unit": "天"},
            {"label": "非工作日", "value": 非工作日, "unit": "天"},
            {"label": "不可投標天數", "value": 不可投標天數, "unit": "天"},
        ],
        "策略建議": get_strategy_suggestion(score),
    }


def calculate_max_profit_by_mode(config, mode, lc_mode=None):
    """
    根據指定模式回傳對應的最大理論收益（元/年）。

    Args:
        config (dict): 模擬設定
        mode (str): 模式代碼，可選值：
                    - "arbitrage"
                    - "large_consumer"
                    - "dr_daily"
                    - "spinning_service"
        lc_mode (str, optional): 若為 large_consumer 模式，需指定其子方案代碼

    Returns:
        float: 最大理論收益（元）
    """
    if mode == "arbitrage":
        return calculate_max_arbitrage_profit(config)
    elif mode == "large_consumer":
        if not lc_mode:
            raise ValueError("large_consumer 模式需要指定 lc_mode")
        return calculate_max_large_consumer_profit(config, lc_mode)
    elif mode == "dr_daily":
        return calculate_max_dr_daily_time_range_profit(config)
    elif mode == "spinning_service":
        return calculate_max_spinning_service_profit(config)
    else:
        raise ValueError(f"未支援的模式代碼: {mode}")


def get_formula_display_data_by_mode(config, mode, score=None):
    """
    根據指定的模式回傳對應的收益公式說明與參數。

    Args:
        config (dict): 模擬設定
        mode (str): 模式代碼，可選值：
                    - "arbitrage"
                    - "large_consumer"
                    - "dr_daily"
                    - "spinning_service"
        lc_mode (str, optional): large_consumer 模式下需指定的子方案代碼

    Returns:
        dict: 包含公式解釋與參數的字典
    """
    if mode == "arbitrage":
        return get_arbitrage_formula_display_data(config, score)
    elif mode == "large_consumer":
        return get_large_consumer_formula_display_data(config, score)
    elif mode == "dr_daily":
        return get_dr_daily_time_range_formula_display_data(config, score)
    elif mode == "spinning_service":
        return get_spinning_service_formula_display_data(config, score)
    else:
        raise ValueError(f"未支援的模式代碼: {mode}")
