import asyncio
import json
from typing import Any, Dict
from uuid import uuid4

from .database.connection import async_session_maker
from .shared.models import Ans, Reqs


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


async def async_handler(event, context):
    """
    Async Lambda handler for ESS IRR evaluation.
    """
    try:
        # Parse input from the event
        if isinstance(event.get("body"), str):
            input_data = json.loads(event["body"])
        else:
            input_data = event.get("body", {})

        # Use context manager for database session
        async with async_session_maker() as session:
            try:
                # Create new request record
                new_request = Reqs(input_params=input_data)
                session.add(new_request)
                await session.commit()
                await session.refresh(new_request)

                # Process the request (your evaluation logic here)
                evaluation_result = await process_request(input_data)

                # Store the answer/result
                new_answer = Ans(
                    req_uuid=new_request.req_uuid, output_result=evaluation_result
                )
                session.add(new_answer)
                await session.commit()
                await session.refresh(new_answer)

                # Return successful response
                return {
                    "statusCode": 200,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                    },
                    "body": json.dumps(
                        {
                            "success": True,
                            "request_id": str(new_request.req_uuid),
                            "answer_id": str(new_answer.ans_uuid),
                            "result": evaluation_result,
                        }
                    ),
                }

            except Exception:
                # Rollback will happen automatically with context manager
                await session.rollback()
                raise  # Re-raise to be caught by outer exception handler

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"success": False, "error": "Invalid JSON in request body"}
            ),
        }

    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"Error processing request: {str(e)}")

        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "success": False,
                    "error": "Internal server error",
                    "error_message": str(e),
                }
            ),
        }


def handler(event, context):
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
