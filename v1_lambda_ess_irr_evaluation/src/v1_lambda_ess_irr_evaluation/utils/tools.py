import os

import pandas as pd

from ..shared.core.calculator import (
    calculate_max_profit_by_mode,
    get_formula_display_data_by_mode,
)
from .logger import logger


def parse_dataframe_to_summary_schema(df_results: pd.DataFrame) -> dict:
    summary_output = {"roi": [], "irr": [], "year_roi": [], "avg_roi": []}

    metric_map = {
        "roi": "ROI",
        "irr": "IRR",
        "year_roi": "Annual_ROI",
        "avg_roi": "Average_ROI",
    }

    id_column = "mode_comb"
    x_column = "台數"

    if df_results.empty:
        # If DataFrame is empty, return the basic structure with empty lists for each metric
        return summary_output

    # Ensure essential columns exist
    if id_column not in df_results.columns:
        print(
            f"Error: ID column '{id_column}' not found in DataFrame. Returning empty summary."
        )
        return summary_output

    if x_column not in df_results.columns:
        print(
            f"Error: X-axis column '{x_column}' not found in DataFrame. Returning empty summary."
        )
        return summary_output

    # Get unique IDs from the id_column, ensure they are strings, and sort them for consistent output order.
    try:
        # Attempt to convert all to string first, then get unique, then sort.
        # This handles cases where mode_comb might have mixed types before conversion.
        unique_ids = sorted(list(df_results[id_column].astype(str).unique()))
    except Exception as e:
        print(
            f"Error converting ID column '{id_column}' to string or sorting: {e}. Returning empty summary."
        )
        return summary_output

    for summary_key, metric_col_name in metric_map.items():
        metric_heatmaps_for_current_key = []

        # Check if the current metric column exists in the DataFrame
        if metric_col_name not in df_results.columns:
            print(
                f"Warning: Metric column '{metric_col_name}' for summary key '{summary_key}' not found. Data for this metric will be empty for all IDs."
            )
            # For each unique_id, create a heatmap entry with empty data
            for uid in unique_ids:  # unique_ids are already strings
                metric_heatmaps_for_current_key.append({"id": uid, "data": []})
            summary_output[summary_key] = metric_heatmaps_for_current_key
            continue  # Move to the next metric in metric_map

        for unique_id_val in unique_ids:  # unique_id_val is already a string
            # Filter DataFrame for the current unique_id_val
            # Ensure comparison is string-to-string by converting df column to str for filtering
            strategy_specific_df = df_results[
                df_results[id_column].astype(str) == unique_id_val
            ].copy()

            data_points = []
            if not strategy_specific_df.empty:
                # Sort by x_column (e.g., '台數') numerically.
                # Ensure x_column can be sorted numerically if it's not already numeric.
                try:
                    strategy_specific_df[x_column] = pd.to_numeric(
                        strategy_specific_df[x_column]
                    )
                    strategy_specific_df.sort_values(by=x_column, inplace=True)
                except ValueError:
                    print(
                        f"Warning: Could not convert column '{x_column}' to numeric for sorting for id '{unique_id_val}'. Data points may not be sorted correctly."
                    )
                except Exception as e:
                    print(
                        f"Warning: Error sorting by '{x_column}' for id '{unique_id_val}': {e}. Data points may not be sorted correctly."
                    )

                for _, row in strategy_specific_df.iterrows():
                    # x_column ('台數') should exist as checked earlier
                    x_val = str(row[x_column])

                    # Metric value for y, handling potential NaNs
                    y_val_raw = row[metric_col_name]
                    # pd.isna handles various forms of missing data including np.nan and pd.NA
                    y_val = None if pd.isna(y_val_raw) else float(y_val_raw)

                    data_points.append({"x": x_val, "y": y_val})

            # Append heatmap object for the current strategy ID.
            metric_heatmaps_for_current_key.append(
                {
                    "id": unique_id_val,  # unique_id_val is already a string
                    "data": data_points,
                }
            )

        summary_output[summary_key] = metric_heatmaps_for_current_key

    return summary_output


def get_y1_score(strategy: str, df: pd.DataFrame, max_profit: float) -> float:
    y1_profit = 0

    if "義務時數型" in strategy:
        y1_profit = df.loc["用電大戶收益", "Year 1"]
    elif "累進回饋型" in strategy:
        y1_profit = df.loc["用電大戶收益", "Year 1"]
    elif "日選" in strategy:
        y1_profit = df.loc["日選時段型", "Year 1"]
    elif "即時" in strategy:
        y1_profit = df.loc["輔助服務價金", "Year 1"]
    elif "電價" in strategy:
        y1_profit = df.loc["電價差收益", "Year 1"]

    return 0 if max_profit == 0 else round(y1_profit / max_profit * 100)


def get_y1_strategy_profit(
    calc_detail_reveal: list[dict], y1_cash_flow: dict
) -> list[dict]:
    for index, detail in enumerate(calc_detail_reveal):
        if "義務時數型" in detail["strategy"] or "累進回饋型" in detail["strategy"]:
            calc_detail_reveal[index]["y1_profit"] = y1_cash_flow["用電大戶收益"]
        elif "日選" in detail["strategy"]:
            calc_detail_reveal[index]["y1_profit"] = y1_cash_flow["日選時段收益"]
        elif "即時" in detail["strategy"]:
            calc_detail_reveal[index]["y1_profit"] = y1_cash_flow["輔助服務價金"]
        else:  # 電價差收益
            calc_detail_reveal[index]["y1_profit"] = y1_cash_flow["電價差收益"]
    return calc_detail_reveal


def parse_parameter_from_strategy(strategy: str) -> tuple[str, str | None]:
    if "義務時數型" in strategy:
        return "large_consumer", "義務時數型"
    elif "累進回饋型" in strategy:
        return "large_consumer", "累進回饋型"
    elif "日選" in strategy:
        return "dr_daily", None
    elif "即時" in strategy:
        return "spinning_service", None
    return "arbitrage", None


def parse_max_profit_parameter_reveal(
    strategy: str, config: dict, df: pd.DataFrame
) -> dict:
    # Split strategy by "-" and process each part
    strategy_parts = strategy.split("-")
    calc_detail_reveal = []
    for part in strategy_parts:
        part = part.strip()  # Remove any whitespace
        if not part:  # Skip empty parts
            continue
        # Process each part of the strategy
        param1, param2 = parse_parameter_from_strategy(part)
        max_profit = calculate_max_profit_by_mode(config, param1, param2)
        y1_profit = get_y1_score(part, df, max_profit)
        parameters_output = get_formula_display_data_by_mode(config, param1, y1_profit)
        calc_detail_reveal.append(
            {
                "strategy": part,
                "max_profit": max_profit,
                "parameters": parameters_output,
            }
        )
    return calc_detail_reveal


def parse_dict_summary_to_cashflow_schema(dict_summary: dict) -> dict:
    """
    Parses the dict_summary (dictionary of DataFrames) into the cashflow schema
    as defined by EvaluationResType.cashflow.
    """
    cashflow_output = {}

    def get_value(df, row_name, year_column, default=0.0):
        if row_name in df.index and year_column in df.columns:
            val = df.loc[row_name, year_column]
            # Ensure val is not a DataFrame or Series before pd.isna
            if isinstance(val, (pd.Series, pd.DataFrame)):
                # This case should ideally not happen if df is structured as expected
                # (metrics as index, years as columns)
                # If it does, we might need to handle it or it indicates an issue upstream
                return default  # Or handle appropriately
            return default if pd.isna(val) else float(val)
        return default

    for id_key, obj in dict_summary.items():
        if not isinstance(id_key, tuple) or len(id_key) != 2:
            print(f"[debug]Warning: Skipping invalid key in dict_summary: {id_key}")
            continue
        df_cashflow_detail = obj["df"]
        num_units, strategy_name = id_key
        calc_detail_reveal = parse_max_profit_parameter_reveal(
            strategy_name, obj["config"], obj["df"]
        )

        # Ensure num_units can be cast to string for the key
        try:
            output_key = f"{strategy_name}.{str(num_units)}"
        except Exception as e:
            print(
                f"Warning: Could not format key for {(num_units, strategy_name)}: {e}. Skipping."
            )
            continue

        yearly_data_list = []
        cumulative_net_cash_flow = 0.0

        # Determine the correct order of year columns if not already sorted
        # Assuming columns are like 'Year 0', 'Year 1', ...
        year_columns = sorted(
            [col for col in df_cashflow_detail.columns if col.startswith("Year")],
            key=lambda x: int(x.split(" ")[1]),
        )
        y1_cash_flow = None
        for year_index, year_column_name in enumerate(
            year_columns
        ):  # Iterate in sorted order of years
            # Map internal DataFrame row names to output JSON keys
            price_diff_profit = get_value(
                df_cashflow_detail, "電價差收益", year_column_name
            )
            day_select_profit = get_value(
                df_cashflow_detail, "日選時段型", year_column_name
            )  # As requested
            ancillary_service_profit = get_value(
                df_cashflow_detail, "輔助服務價金", year_column_name
            )
            # major player
            major_player_profit = get_value(
                df_cashflow_detail, "用電大戶收益", year_column_name
            )

            # For '總支出', use the '總支出' row, not '總支出(不含利息)'
            total_expenses = get_value(df_cashflow_detail, "總支出", year_column_name)
            net_cash_flow = get_value(df_cashflow_detail, "Net Cash", year_column_name)

            cumulative_net_cash_flow += net_cash_flow

            year_data_dict = {
                "year": year_column_name,  # e.g., "Year 0", "Year 1"
                "電價差收益": price_diff_profit,
                "日選時段收益": day_select_profit,
                "輔助服務價金": ancillary_service_profit,
                "用電大戶收益": major_player_profit,
                "總支出": -total_expenses,
                "淨現金流": net_cash_flow,
                "累積現金流": cumulative_net_cash_flow,
            }
            yearly_data_list.append(year_data_dict)
            if year_index == 1:
                y1_cash_flow = year_data_dict
        calc_detail_reveal = get_y1_strategy_profit(calc_detail_reveal, y1_cash_flow)

        cashflow_output[output_key] = {
            "chart_data": yearly_data_list,
            "calc_detail_reveal": calc_detail_reveal,
        }

    return cashflow_output


def get_tou_csv():
    try:
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        csv_path = os.path.join(
            script_dir, "..", "shared", "core", "tou_data_simple_2025.csv"
        )

        logger.info(
            f"Attempting to read CSV from: {csv_path}",
            extra={"script_path": script_path, "script_dir": script_dir},
        )

        return pd.read_csv(csv_path)
    except FileNotFoundError:
        logger.error(f"Could not find the CSV file at the expected path: {csv_path}")

        raise
