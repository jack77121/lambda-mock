import asyncio
import json
import uuid
from itertools import product
from aws_lambda_powertools.utilities.typing import LambdaContext
from sst import Resource
from shared.core import config_loader, calculator
from shared.utils.lambda_response import LambdaResponseBuilder
from v1_lambda_ess_irr_evaluation.schemas.ess_evaluation_req import ESSEvaluationRequest
from v1_lambda_ess_irr_evaluation.utils.logger import logger
from v1_lambda_ess_irr_evaluation.utils.tools import get_tou_csv


async def async_handler(event, context: LambdaContext):
    """
    Async Lambda handler for ESS IRR evaluation.
    """
    try:
        # Parse input from the event
        req_data = ESSEvaluationRequest.model_validate_json(event.get("body", "{}"))

        # Generate evaluate_var_result_id if not provided
        if not req_data.evaluate_var_result_id:
            req_data.evaluate_var_result_id = str(uuid.uuid4())

        # Return immediate response to client with evaluate_var_result_id
        # response = LambdaResponseBuilder.success(
        #     data={"evaluate_var_result_id": req_data.evaluate_var_result_id}, status_code=200
        # )
        result = await process_in_background(req_data)
        response = LambdaResponseBuilder.success(
            data=result, status_code=200
        )
        response["headers"]["Access-Control-Allow-Origin"] = "*"
        # logger.info("Start background processing")
        # Start background processing
        # asyncio.create_task(process_in_background(req_data))



        return response

    except json.JSONDecodeError:
        return LambdaResponseBuilder.json_decode_error()

    except Exception as e:
        # Log error (in production, use proper logging)
        logger.error("處理請求失敗", extra={"error_message": str(e)})

        return LambdaResponseBuilder.error(
            message="伺服器內部錯誤", data={"error_message": str(e)}, status_code=500
        )


async def generate_simulation_parameters(req_data: ESSEvaluationRequest, df_tou_2025) -> tuple[dict, list[dict]]:
    """
    Generate all simulation parameters (extracted from run_all_simulations)
    Returns: (base_config, simulation_tasks)
    """
    # Prepare base configuration (from run_all_simulations)
    config = req_data.config.model_dump(by_alias=True) if req_data.config else config_loader.load_config()
    
    # Basic parameters setup
    contract_capacity_old = req_data.contract_capacity_old.model_dump(by_alias=True)
    main_contract_capacity = contract_capacity_old["經常契約"]
    
    config["電價方案"]["契約容量"] = main_contract_capacity
    config["電價方案"]["計費類別"] = req_data.priceType
    config["電價方案"]["行業別"] = req_data.industry
    config["電價方案"]["電費調整係數"] = req_data.tariff
    
    # Handle large consumer requirements
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
    else:
        config["再生能源義務用戶"]["義務裝置容量"] = 0
        req_data.用電大戶方案 = []
    
    # Process AMI data (from run_all_simulations)
    if (req_data.manual_curve_data is not None) and (len(req_data.manual_curve_data) > 0):
        logger.info("[debug] Using manual curve data")
        # Handle manual curve data scaling logic here if needed
        import sqlite3
        import pandas as pd
        from shared.core.summary_generator import get_ami_db_path
        conn = sqlite3.connect(get_ami_db_path())
        query = "SELECT * FROM week_all WHERE ID = " + str(req_data.chartId)
        df_ami_raw = pd.read_sql(query, conn)
        conn.close()
        df_ami_raw = config_loader.scale_15min_by_hour(df_ami_raw, req_data.manual_curve_data)
    elif (req_data.ami_uploaded_raw_data is not None) and (len(req_data.ami_uploaded_raw_data) > 0):
        logger.info("[debug] Using uploaded AMI data")
        df_ami_raw = config_loader.ami_15min_json_to_df(req_data.ami_uploaded_raw_data)
    else:
        logger.info("[debug] Using scaled AMI data based on contract capacity")
        import sqlite3
        import pandas as pd
        from shared.core.summary_generator import get_ami_db_path
        conn = sqlite3.connect(get_ami_db_path())
        query = "SELECT * FROM week_all WHERE ID = " + str(req_data.chartId)
        df_ami_raw = pd.read_sql(query, conn)
        conn.close()
        df_ami_raw["variable"] = pd.to_datetime(
            df_ami_raw["variable"], format="%H:%M:%S.%f"
        ).dt.strftime("%H:%M")
        
        origin_capacity = int(df_ami_raw["value"].max().round())
        df_ami_raw["value"] = (
            df_ami_raw["value"] * main_contract_capacity / origin_capacity
        ).round()
    
    df_ami = config_loader.norm_ami(df_ami_raw, df_tou_2025, req_data.priceType)
    
    # Determine unit options
    if req_data.units is None:
        台數選項 = calculator.generate_fixed_step_combinations(
            int(main_contract_capacity * 0.8),
            pcs_power=int(config["儲能系統"]["單台 PCS 標稱功率"]),
            max_groups=4,
        )
    else:
        台數選項 = [int(x.strip()) for x in req_data.units.split(",")] if req_data.units else [1]
    
    if not 台數選項:
        台數選項 = [1]
    
    # Generate all simulation tasks (extracted from run_all_simulations logic)
    simulation_tasks = []
    
    dr有值 = bool(req_data.dr方案選項)
    sp有值 = bool(req_data.即時備轉方案選項)
    lc有值 = bool(req_data.用電大戶方案)
    
    # Energy only (always included)
    for 台數 in 台數選項:
        simulation_tasks.append({
            "unit": 台數,
            "mode": "energy_only",
            "dr_program": None,
            "sp_program": None,
            "lc_program": None,
            "mode_key": "電價套利"
        })
    
    # Generate other simulation combinations based on available options
    if lc有值 and not dr有值 and not sp有值:
        for 台數, 方案 in product(台數選項, req_data.用電大戶方案):
            simulation_tasks.append({
                "unit": 台數,
                "mode": "energy_lc",
                "dr_program": None,
                "sp_program": None,
                "lc_program": 方案,
                "mode_key": f"電價套利-{方案}"
            })
    
    if dr有值 and not sp有值 and not lc有值:
        for 台數, dr方案 in product(台數選項, req_data.dr方案選項):
            simulation_tasks.append({
                "unit": 台數,
                "mode": "energy_dr",
                "dr_program": dr方案,
                "sp_program": None,
                "lc_program": None,
                "mode_key": f"電價套利-日選{dr方案}"
            })
    
    if not dr有值 and sp有值 and not lc有值:
        for 台數, sp方案 in product(台數選項, req_data.即時備轉方案選項):
            sp_str = "單一" if sp方案 == "single" else "聚合"
            simulation_tasks.append({
                "unit": 台數,
                "mode": "energy_regulation",
                "dr_program": "0h",
                "sp_program": sp方案,
                "lc_program": None,
                "mode_key": f"電價套利-即時{sp_str}"
            })
    
    # Combined modes
    if dr有值 and sp有值 and not lc有值:
        # DR + 即時備轉
        for 台數, dr方案 in product(台數選項, req_data.dr方案選項):
            simulation_tasks.append({
                "unit": 台數,
                "mode": "energy_dr",
                "dr_program": dr方案,
                "sp_program": None,
                "lc_program": None,
                "mode_key": f"電價套利-日選{dr方案}"
            })
        
        for 台數, sp方案 in product(台數選項, req_data.即時備轉方案選項):
            sp_str = "單一" if sp方案 == "single" else "聚合"
            simulation_tasks.append({
                "unit": 台數,
                "mode": "energy_regulation",
                "dr_program": "0h",
                "sp_program": sp方案,
                "lc_program": None,
                "mode_key": f"電價套利-即時{sp_str}"
            })
        
        for 台數, dr方案, sp方案 in product(台數選項, req_data.dr方案選項, req_data.即時備轉方案選項):
            sp_str = "單一" if sp方案 == "single" else "聚合"
            simulation_tasks.append({
                "unit": 台數,
                "mode": "energy_dr_regulation",
                "dr_program": dr方案,
                "sp_program": sp方案,
                "lc_program": None,
                "mode_key": f"電價套利-日選{dr方案}-即時{sp_str}"
            })
    
    # Add more combinations as needed...
    
    return config, simulation_tasks, df_ami


async def process_in_background(req_data: ESSEvaluationRequest):
    """
    Background processing function - now delegates to parallel LambdaB executions
    """
    try:
        # Generate evaluate_var_result_id if not provided
        if not req_data.evaluate_var_result_id:
            req_data.evaluate_var_result_id = str(uuid.uuid4())
        
        logger.info("req_data", extra=req_data.model_dump())
        logger.info(f"Starting parallel simulation with evaluate_var_result_id: {req_data.evaluate_var_result_id}")
        
        # Get TOU data
        df_tou_2025 = get_tou_csv()
        
        # Generate all simulation parameters
        config, simulation_tasks, df_ami = await generate_simulation_parameters(req_data, df_tou_2025)
        
        logger.info(f"Generated {len(simulation_tasks)} simulation tasks")
        
        # Convert DataFrame to dict for serialization
        df_ami_dict = df_ami.to_dict() if df_ami is not None else None
        

        # just for query single task parameter testing:
        task = simulation_tasks[0]
        payload = {
                "config": config,
                "unit": task["unit"],
                "df_ami": df_ami_dict,
                "mode": task["mode"],
                "dr_program": task["dr_program"],
                "sp_program": task["sp_program"],
                "lc_program": task["lc_program"],
                "year": req_data.year,
                "evaluate_var_result_id": req_data.evaluate_var_result_id,
                "mode_key": task["mode_key"],
                "simulation_id": str(uuid.uuid4())
            }
        return payload

        # Launch all simulations in parallel using SST Link
        # for task in simulation_tasks:
        #     simulation_id = str(uuid.uuid4())
            
        #     # Prepare payload for LambdaB
        #     payload = {
        #         "config": config,
        #         "unit": task["unit"],
        #         "df_ami": df_ami_dict,
        #         "mode": task["mode"],
        #         "dr_program": task["dr_program"],
        #         "sp_program": task["sp_program"],
        #         "lc_program": task["lc_program"],
        #         "year": req_data.year,
        #         "evaluate_var_result_id": req_data.evaluate_var_result_id,
        #         "mode_key": task["mode_key"],
        #         "simulation_id": simulation_id
        #     }
            
            # # Async invoke LambdaB using SST Link
            # try:
            #     Resource.SingleSimulation.invoke(
            #         InvocationType='Event',  # Async invocation
            #         Payload=json.dumps(payload)
            #     )
            #     logger.info(f"Launched simulation: {simulation_id} ({task['mode_key']})")
            # except Exception as e:
            #     logger.error(f"Failed to launch simulation {simulation_id}: {e}")
        
        logger.info(f"All {len(simulation_tasks)} simulations launched successfully. Results will be written to evaluate_var_result_id: {req_data.evaluate_var_result_id}")
        
        # LambdaA completes immediately after delegating all tasks
        
    except Exception as e:
        logger.error("背景處理失敗", extra={"error_message": str(e)})


def handler(event: dict[str, any], context: LambdaContext) -> dict[str, any]:
    """
    Lambda handler entry point - wraps async handler.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(async_handler(event, context))
