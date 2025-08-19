from typing import Any, Dict, TypeVar

from pydantic import ValidationError

from ..schemas.base_model import ApiResponseBase

T = TypeVar("T")


class LambdaResponseBuilder:
    @staticmethod
    def success(
        data: Any, message: str = None, status_code: int = 200
    ) -> Dict[str, Any]:
        response = ApiResponseBase(success=True, message=message, data=data)

        return {
            "statusCode": status_code,
            "headers": {"Content-Type": "application/json"},
            "body": response.model_dump_json(),
        }

    @staticmethod
    def error(
        message: str,
        data: Any = None,
        status_code: int = 500,
    ) -> Dict[str, Any]:
        response = ApiResponseBase(success=False, message=message, data=data)

        return {
            "statusCode": status_code,
            "headers": {"Content-Type": "application/json"},
            "body": response.model_dump_json(),
        }

    @staticmethod
    def validation_error(validation_error: ValidationError) -> Dict[str, Any]:
        errors = validation_error.errors()
        # error_details = {}

        # for error in errors:
        #     field = ".".join(str(x) for x in error["loc"])
        #     error_details[field] = error["msg"]

        first_error_msg = errors[0]["msg"] if errors else ""
        message = (
            f"請求資料格式錯誤: {first_error_msg}"
            if first_error_msg
            else "請求資料格式錯誤"
        )

        return LambdaResponseBuilder.error(
            data=None,
            message=message,
            status_code=400,
        )

    @staticmethod
    def json_decode_error() -> Dict[str, Any]:
        return LambdaResponseBuilder.error(
            data=None,
            message="JSON 格式錯誤，請檢查請求內容",
            status_code=400,
        )
