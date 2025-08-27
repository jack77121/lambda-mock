import asyncio
import json
import time
import uuid
from typing import Any, Dict

import pandas as pd
from aws_lambda_powertools.utilities.typing import LambdaContext
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.core.summary_generator import run_simulation
from shared.models.generated_models import EvaluateTasks
from shared.utils.lambda_response import LambdaResponseBuilder
from v1_lambda_run_simulation.schemas.run_simulation_req import (
    RunSimulationRequest,
    RunSimulationResponse,
)
from v1_lambda_run_simulation.utils.logger import logger

# Database setup - similar to LambdaA (commented for testing)
async_session_maker = None


#
#
def init_db():
    """Initialize database connection"""
    global async_session_maker
    if async_session_maker is None:
        import os

        engine = create_async_engine(
            os.environ["POSTGRES_URL"],
            echo=False,
            pool_size=1,
            max_overflow=0,
        )
        async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


#
#
async def write_result_back(
    session: AsyncSession,
    simulation_id: str,
    result: dict,
) -> None:
    """
    Write simulation result back to database
    Updates EvaluateTasks table with result and status
    """
    try:
        # Convert simulation_id to UUID if it's a string
        task_uuid = uuid.UUID(simulation_id)

        # Query and update the evaluate task
        stmt = (
            update(EvaluateTasks)
            .where(EvaluateTasks.task_id == task_uuid)
            .values(result=result, status="SUCCESS")
        )

        await session.execute(stmt)

        await session.commit()
        print(f"[DEBUG] Successfully wrote result for simulation_id: {simulation_id}")

    except Exception as e:
        await session.rollback()
        print(f"[ERROR] Failed to write result for simulation_id {simulation_id}: {e}")
        raise


#
#
async def write_error_result(
    session: AsyncSession,
    simulation_id: str,
    error_message: str,
) -> None:
    """
    Write error result to database
    Updates EvaluateTasks table with error message and FAILED status
    """
    try:
        # Convert simulation_id to UUID if it's a string
        task_uuid = uuid.UUID(simulation_id)

        # Query and update the evaluate task with error
        stmt = (
            update(EvaluateTasks)
            .where(EvaluateTasks.task_id == task_uuid)
            .values(status="FAILED")
        )

        await session.execute(stmt)

        await session.commit()
        print(
            f"[DEBUG] Successfully wrote error result for simulation_id: {simulation_id}"
        )

    except Exception as e:
        await session.rollback()
        print(
            f"[ERROR] Failed to write error result for simulation_id {simulation_id}: {e}"
        )
        raise


async def process_run_simulation(
    request: RunSimulationRequest,
) -> RunSimulationResponse:
    """
    Process run simulation
    """
    start_time = time.time()

    try:
        init_db()  # Commented for testing

        # Convert serialized df_ami back to DataFrame if needed

        df_ami = None
        if request.df_ami and isinstance(request.df_ami, dict):
            df_ami = pd.DataFrame(request.df_ami)

        logger.info(
            f"[DEBUG] Starting run simulation: {request.simulation_id}, mode: {request.mode}"
        )

        # Execute run_simulation - this is the core logic from summary_generator.py
        gain, df_summary = run_simulation(
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
        result = {
            "gain": gain,  # The gain dict from run_simulation
            "df_summary": df_summary.to_dict() if df_summary is not None else None,
        }

        # Write result back to database (commented for testing - using logger instead)
        async with async_session_maker() as session:
            await write_result_back(
                session=session,
                simulation_id=request.simulation_id,
                result=result,
            )

        logger.info(
            "Simulation completed successfully",
            extra={
                "simulation_id": request.simulation_id,
                "evaluate_var_result_id": request.evaluate_var_result_id,
                "mode_key": request.mode_key,
                "unit": request.unit,
                "execution_time": round(execution_time, 2),
                "result_ROI": gain.get("ROI", "N/A"),
                "result_IRR": gain.get("IRR", "N/A"),
                "result_Annual_ROI": gain.get("Annual_ROI", "N/A"),
                "result_Average_ROI": gain.get("Average_ROI", "N/A"),
            },
        )

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

        try:
            # Write error result to database
            async with async_session_maker() as session:
                await write_error_result(
                    session=session,
                    simulation_id=request.simulation_id,
                    error_message=error_message,
                )
        except Exception as db_error:
            print(f"[ERROR] Failed to write error result to database: {db_error}")

        # For testing: log the error instead of writing to database
        logger.error(
            "Simulation failed",
            extra={
                "simulation_id": request.simulation_id,
                "evaluate_var_result_id": request.evaluate_var_result_id,
                "mode_key": request.mode_key,
                "error_message": error_message,
                "execution_time": round(execution_time, 2),
            },
        )

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
            # logger.info(f"req json body: {event['body']}")
            body = json.loads(event["body"])
        else:
            # Direct Lambda invocation
            # logger.info(f"req json body: {json.dumps(event)}")
            body = event

        request = RunSimulationRequest.model_validate(body)

        # Process simulation
        result = await process_run_simulation(request)

        response = LambdaResponseBuilder.success(
            data=result.model_dump_json(), status_code=200
        )

        response["headers"]["Access-Control-Allow-Origin"] = "*"
        return response

    except json.JSONDecodeError:
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
