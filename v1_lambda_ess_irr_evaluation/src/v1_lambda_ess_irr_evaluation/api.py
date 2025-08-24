print("DEBUG: Starting imports in api.py")

import asyncio
import json

print("DEBUG: Basic imports successful")

from aws_lambda_powertools.utilities.typing import LambdaContext

print("DEBUG: LambdaContext import successful")

try:
    print("DEBUG: Attempting to import from shared.core.summary_generator")
    from shared.core.summary_generator import run_all_simulations
    print("DEBUG: shared.core.summary_generator import successful")
except Exception as e:
    print(f"DEBUG: Failed to import from shared.core.summary_generator: {e}")
    raise

try:
    print("DEBUG: Attempting to import from shared.utils.lambda_response")
    from shared.utils.lambda_response import LambdaResponseBuilder
    print("DEBUG: shared.utils.lambda_response import successful")
except Exception as e:
    print(f"DEBUG: Failed to import from shared.utils.lambda_response: {e}")
    raise

try:
    print("DEBUG: Attempting to import from v1_lambda_ess_irr_evaluation.schemas.ess_evaluation_req")
    from v1_lambda_ess_irr_evaluation.schemas.ess_evaluation_req import ESSEvaluationRequest
    print("DEBUG: v1_lambda_ess_irr_evaluation.schemas.ess_evaluation_req import successful")
except Exception as e:
    print(f"DEBUG: Failed to import from v1_lambda_ess_irr_evaluation.schemas.ess_evaluation_req: {e}")
    raise

try:
    print("DEBUG: Attempting to import from v1_lambda_ess_irr_evaluation.database.connection")
    from v1_lambda_ess_irr_evaluation.database.connection import async_session_maker
    print("DEBUG: v1_lambda_ess_irr_evaluation.database.connection import successful")
except Exception as e:
    print(f"DEBUG: Failed to import from v1_lambda_ess_irr_evaluation.database.connection: {e}")
    raise

try:
    print("DEBUG: Attempting to import from v1_lambda_ess_irr_evaluation.utils.logger")
    from v1_lambda_ess_irr_evaluation.utils.logger import logger
    print("DEBUG: v1_lambda_ess_irr_evaluation.utils.logger import successful")
except Exception as e:
    print(f"DEBUG: Failed to import from v1_lambda_ess_irr_evaluation.utils.logger: {e}")
    raise

try:
    print("DEBUG: Attempting to import from v1_lambda_ess_irr_evaluation.utils.tools")
    from v1_lambda_ess_irr_evaluation.utils.tools import (
        get_tou_csv,
        parse_dataframe_to_summary_schema,
        parse_dict_summary_to_cashflow_schema,
    )
    print("DEBUG: v1_lambda_ess_irr_evaluation.utils.tools import successful")
except Exception as e:
    print(f"DEBUG: Failed to import from v1_lambda_ess_irr_evaluation.utils.tools: {e}")
    raise


async def async_handler(event, context: LambdaContext):
    """
    Async Lambda handler for ESS IRR evaluation.
    """
    try:
        # Parse input from the event
        req_data = ESSEvaluationRequest.model_validate_json(event.get("body", "{}"))

        # Return immediate response to client
        response = LambdaResponseBuilder.success(
            data="mock-id", message=None, status_code=200
        )
        response["headers"]["Access-Control-Allow-Origin"] = "*"

        # Start background processing
        asyncio.create_task(process_in_background(req_data))

        return response

    except json.JSONDecodeError:
        return LambdaResponseBuilder.json_decode_error()

    except Exception as e:
        # Log error (in production, use proper logging)
        logger.error("處理請求失敗", extra={"error_message": str(e)})

        return LambdaResponseBuilder.error(
            message="伺服器內部錯誤", data={"error_message": str(e)}, status_code=500
        )


async def process_in_background(req_data: ESSEvaluationRequest):
    """
    Background processing function for long-running ESS evaluation.
    """
    try:
        # Get the directory of this script to construct absolute path to CSV file
        df_tou_2025 = get_tou_csv()

        # Use context manager for database session
        async with async_session_maker() as session:
            try:
                logger.info("req_data", extra=req_data.model_dump())
                logger.info("start run_all_simulations...")
                df_results, dict_summary, dict_annual_cost_summary = (
                    run_all_simulations(
                        config=req_data.config.model_dump(by_alias=True),
                        json_ami_hourly_update=req_data.manual_curve_data,
                        json_ami_15min=req_data.ami_uploaded_raw_data,
                        ID=req_data.chartId,
                        contract_capacity_old=req_data.contract_capacity_old.model_dump(
                            by_alias=True
                        ),
                        contract_capacity_new=req_data.contract_capacity_new.model_dump(
                            by_alias=True
                        ),
                        tou_program=req_data.priceType,
                        industry_class=req_data.industry,
                        tariff_adjust_factor=req_data.tariff,
                        df_tou_2025=df_tou_2025,
                        units=req_data.units.split(",")
                        if req_data.units is not None
                        else req_data.units,
                        dr方案選項=req_data.dr方案選項,
                        即時備轉方案選項=req_data.即時備轉方案選項,
                        用電大戶方案=req_data.用電大戶方案,
                        year=req_data.year,
                    )
                )
                logger.info("finished run_all_simulations, start parsing...")

                # Parse df_results to the summary schema
                summary_output_data = parse_dataframe_to_summary_schema(df_results)

                # Parse dict_summary to the cashflow schema
                cashflow_output_data = parse_dict_summary_to_cashflow_schema(
                    dict_summary
                )

                final_evaluation_result = {
                    "summary": summary_output_data,
                    "cashflow": cashflow_output_data,
                    # "fileId": file_id,
                    # "originalElecPrice": dict_annual_cost_summary,
                }

                logger.info(
                    "finished parsing, ready to return",
                    extra={"final_evaluation_result": final_evaluation_result},
                )

            except Exception:
                # Rollback will happen automatically with context manager
                await session.rollback()
                raise  # Re-raise to be caught by outer exception handler

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
