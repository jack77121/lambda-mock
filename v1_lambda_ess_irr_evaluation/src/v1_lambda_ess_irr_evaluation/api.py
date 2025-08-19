import asyncio
import json
from typing import Any, Dict
from uuid import uuid4

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

from v1_lambda_ess_irr_evaluation.schemas.ess_evaluation_req import ESSEvaluationRequest

from .database.connection import async_session_maker
from .shared.utils.lambda_response import LambdaResponseBuilder

logger = Logger(service="lambda-ess-irr-evaluation")


async def process_request(input_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the request and generate evaluation results.
    This is where your ESS IRR evaluation logic would go.
    """
    # Placeholder for actual ESS IRR evaluation logic
    # Replace this with your actual evaluation algorithm

    result = {
        "evaluation_id": str(uuid4()),
        "input_received": input_params,
        "evaluation_result": {
            "irr_score": 0.15,  # Example IRR result
            "risk_assessment": "medium",
            "recommendation": "proceed_with_caution",
        },
        "timestamp": "2025-08-01T00:00:00Z",  # Would be actual timestamp
    }

    return result


async def async_handler(event, context: LambdaContext):
    """
    Async Lambda handler for ESS IRR evaluation.
    """
    try:
        # Parse input from the event
        req_data = ESSEvaluationRequest.model_validate_json(event.get("body", "{}"))

        # Use context manager for database session
        async with async_session_maker() as session:
            try:
                # # Create new request record
                # new_request = Reqs(input_params=input_data)
                # session.add(new_request)
                # await session.commit()
                # await session.refresh(new_request)

                # # Process the request (your evaluation logic here)
                # evaluation_result = await process_request(input_data)

                # # Store the answer/result
                # new_answer = Ans(
                #     req_uuid=new_request.req_uuid, output_result=evaluation_result
                # )
                # session.add(new_answer)
                # await session.commit()
                # await session.refresh(new_answer)

                # Return successful response using LambdaResponseBuilder
                # result_data = {
                #     "request_id": str(123),
                #     "answer_id": str(321),
                #     "result": None,
                # }
                logger.info("req_data", extra=req_data.model_dump())
                result_data = req_data

                response = LambdaResponseBuilder.success(
                    data=result_data, message="ESS IRR 評估完成", status_code=200
                )

                # Add CORS headers
                response["headers"]["Access-Control-Allow-Origin"] = "*"

                return response

            except Exception:
                # Rollback will happen automatically with context manager
                await session.rollback()
                raise  # Re-raise to be caught by outer exception handler

    except json.JSONDecodeError:
        return LambdaResponseBuilder.json_decode_error()

    except Exception as e:
        # Log error (in production, use proper logging)
        logger.error("處理請求失敗", extra={"error_message": str(e)})

        return LambdaResponseBuilder.error(
            message="伺服器內部錯誤", data={"error_message": str(e)}, status_code=500
        )


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
