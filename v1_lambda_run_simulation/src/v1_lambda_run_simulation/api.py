import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict
import pandas as pd

from aws_lambda_powertools.utilities.typing import LambdaContext

from shared.utils.lambda_response import LambdaResponseBuilder
from v1_lambda_run_simulation.schemas.run_simulation_req import (
    RunSimulationRequest,
    RunSimulationResponse,
)
# from sqlalchemy import text
# from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.core.summary_generator import run_simulation
from v1_lambda_run_simulation.utils.logger import logger

# Database setup - similar to LambdaA (commented for testing)
# async_session_maker = None
# 
# 
# def init_db():
#     """Initialize database connection"""
#     global async_session_maker
#     if async_session_maker is None:
#         import os
# 
#         engine = create_async_engine(
#             os.environ["POSTGRES_URL"],
#             echo=False,
#             pool_size=1,
#             max_overflow=0,
#         )
#         async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
# 
# 
# async def write_result_back(
#     session: AsyncSession,
#     simulation_id: str,
#     evaluate_var_result_id: str,
#     mode_key: str,
#     unit: int,
#     simulation_params: dict,
#     result_data: dict,
#     execution_time: float,
# ) -> None:
#     """
#     Write simulation result back to database
#     Similar to run_and_store but writes to PostgreSQL instead of memory
#     """
#     try:
#         # Insert simulation result
#         stmt = text("""
#             INSERT INTO simulation_results (
#                 id, evaluate_var_result_id, simulation_id, mode_key, unit,
#                 simulation_params, result_data, status,
#                 created_at, completed_at, execution_time
#             ) VALUES (
#                 :id, :evaluate_var_result_id, :simulation_id, :mode_key, :unit,
#                 :simulation_params, :result_data, :status,
#                 :created_at, :completed_at, :execution_time
#             )
#         """)
# 
#         await session.execute(
#             stmt,
#             {
#                 "id": str(uuid.uuid4()),
#                 "evaluate_var_result_id": evaluate_var_result_id,
#                 "simulation_id": simulation_id,
#                 "mode_key": mode_key,
#                 "unit": unit,
#                 "simulation_params": json.dumps(simulation_params),
#                 "result_data": json.dumps(result_data),
#                 "status": "completed",
#                 "created_at": datetime.utcnow(),
#                 "completed_at": datetime.utcnow(),
#                 "execution_time": execution_time,
#             },
#         )
# 
#         await session.commit()
#         print(f"[DEBUG] Successfully wrote result for simulation_id: {simulation_id}")
# 
#     except Exception as e:
#         await session.rollback()
#         print(f"[ERROR] Failed to write result for simulation_id {simulation_id}: {e}")
#         raise
# 
# 
# async def write_error_result(
#     session: AsyncSession,
#     simulation_id: str,
#     evaluate_var_result_id: str,
#     mode_key: str,
#     unit: int,
#     simulation_params: dict,
#     error_message: str,
# ) -> None:
#     """Write error result to database"""
#     try:
#         stmt = text("""
#             INSERT INTO simulation_results (
#                 id, evaluate_var_result_id, simulation_id, mode_key, unit,
#                 simulation_params, status, error_message, created_at
#             ) VALUES (
#                 :id, :evaluate_var_result_id, :simulation_id, :mode_key, :unit,
#                 :simulation_params, :status, :error_message, :created_at
#             )
#         """)
# 
#         await session.execute(
#             stmt,
#             {
#                 "id": str(uuid.uuid4()),
#                 "evaluate_var_result_id": evaluate_var_result_id,
#                 "simulation_id": simulation_id,
#                 "mode_key": mode_key,
#                 "unit": unit,
#                 "simulation_params": json.dumps(simulation_params),
#                 "status": "error",
#                 "error_message": error_message,
#                 "created_at": datetime.utcnow(),
#             },
#         )
# 
#         await session.commit()
#         print(
#             f"[DEBUG] Successfully wrote error result for simulation_id: {simulation_id}"
#         )
# 
#     except Exception as e:
#         await session.rollback()
#         print(
#             f"[ERROR] Failed to write error result for simulation_id {simulation_id}: {e}"
#         )
#         raise


async def process_run_simulation(
    request: RunSimulationRequest,
) -> RunSimulationResponse:
    """
    Process run simulation
    """
    start_time = time.time()

    try:
        # init_db()  # Commented for testing

        # Convert serialized df_ami back to DataFrame if needed
        
        df_ami = None
        if request.df_ami and isinstance(request.df_ami, dict):
            df_ami = pd.DataFrame(request.df_ami)


        logger.info(
            f"[DEBUG] Starting run simulation: {request.simulation_id}, mode: {request.mode}"
        )

        # Execute run_simulation - this is the core logic from summary_generator.py
        result, df_summary = run_simulation(
            config=request.config,
            unit=request.unit,
            df_ami=df_ami,
            mode=request.mode,
            dr_program=request.dr_program,
            sp_program=request.sp_program,
            lc_program=request.lc_program,
            year=request.year,
        )

        execution_time = time.time() - start_time
        logger.info(
            f"[DEBUG] Simulation completed in {execution_time:.2f}s: {request.simulation_id}"
        )

        # Prepare result data (similar to what run_and_store did)
        result_data = {
            "gain": result,  # The result dict from run_simulation
            "df_summary": df_summary.to_dict() if df_summary is not None else None,
            "config": request.config,  # Store config for reference
        }

        # Prepare simulation parameters for storage
        simulation_params = {
            "unit": request.unit,
            "mode": request.mode,
            "dr_program": request.dr_program,
            "sp_program": request.sp_program,
            "lc_program": request.lc_program,
            "year": request.year,
        }

        # Write result back to database (commented for testing - using logger instead)
        # async with async_session_maker() as session:
        #     await write_result_back(
        #         session=session,
        #         simulation_id=request.simulation_id,
        #         evaluate_var_result_id=request.evaluate_var_result_id,
        #         mode_key=request.mode_key,
        #         unit=request.unit,
        #         simulation_params=simulation_params,
        #         result_data=result_data,
        #         execution_time=execution_time,
        #     )
        
        # For testing: log the result instead of writing to database
        logger.info("Simulation completed successfully", extra={
            "simulation_id": request.simulation_id,
            "evaluate_var_result_id": request.evaluate_var_result_id,
            "mode_key": request.mode_key,
            "unit": request.unit,
            "execution_time": round(execution_time, 2),
            "result_ROI": result.get('ROI', 'N/A'),
            "result_IRR": result.get('IRR', 'N/A'),
            "result_Annual_ROI": result.get('Annual_ROI', 'N/A'),
            "result_Average_ROI": result.get('Average_ROI', 'N/A')
        })

        return RunSimulationResponse(
            success=True,
            simulation_id=request.simulation_id,
            evaluate_var_result_id=request.evaluate_var_result_id,
            execution_time=execution_time,
        )

    except Exception as e:
        execution_time = time.time() - start_time
        error_message = str(e)
        logger.error(
            f"[ERROR] Simulation failed: {request.simulation_id}, error: {error_message}"
        )

        # try:
        #     # Write error result to database
        #     async with async_session_maker() as session:
        #         simulation_params = {
        #             "unit": request.unit,
        #             "mode": request.mode,
        #             "dr_program": request.dr_program,
        #             "sp_program": request.sp_program,
        #             "lc_program": request.lc_program,
        #             "year": request.year,
        #         }
        # 
        #         await write_error_result(
        #             session=session,
        #             simulation_id=request.simulation_id,
        #             evaluate_var_result_id=request.evaluate_var_result_id,
        #             mode_key=request.mode_key,
        #             unit=request.unit,
        #             simulation_params=simulation_params,
        #             error_message=error_message,
        #         )
        # except Exception as db_error:
        #     print(f"[ERROR] Failed to write error result to database: {db_error}")
        
        # For testing: log the error instead of writing to database
        logger.error("Simulation failed", extra={
            "simulation_id": request.simulation_id,
            "evaluate_var_result_id": request.evaluate_var_result_id,
            "mode_key": request.mode_key,
            "error_message": error_message,
            "execution_time": round(execution_time, 2)
        })

        return RunSimulationResponse(
            success=False,
            simulation_id=request.simulation_id,
            evaluate_var_result_id=request.evaluate_var_result_id,
            error_message=error_message,
            execution_time=execution_time,
        )


async def async_handler(
    event: Dict[str, Any], context: LambdaContext
) -> Dict[str, Any]:
    """
    Async Lambda handler for run simulation
    """
    try:
        # Parse input
        if isinstance(event, dict) and "body" in event:
            # If coming from API Gateway
            body = json.loads(event["body"])
        else:
            # Direct Lambda invocation
            body = event

        request = RunSimulationRequest.model_validate(body)

        # Process simulation
        result = await process_run_simulation(request)

        response = LambdaResponseBuilder.success(
            data=result.model_dump_json(),
            status_code=200
        )

        response["headers"]["Access-Control-Allow-Origin"] = "*"
        return response

    except json.JSONDecodeError as e:
        return LambdaResponseBuilder.json_decode_error()

    except Exception as e:
        logger.error("處理請求失敗", extra={"error_message": str(e)})
        return LambdaResponseBuilder.error(
            message="伺服器內部錯誤", data={"error_message": str(e)}, status_code=500
        )


def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Lambda handler entry point - wraps async handler
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(async_handler(event, context))
