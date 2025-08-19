from pydantic import BaseModel, Field, field_validator


class ESSEvaluationRequest(BaseModel):
    capacity: float = Field(..., description="契約容量")
    tou: str = Field(..., description="時間電價")

    @field_validator("capacity")
    @classmethod
    def validate_capacity(cls, v: float) -> float:
        if not v:
            raise ValueError("契約容量為必填")
        if v <= 0:
            raise ValueError("契約容量必須 >= 0")
        return v

    @field_validator("tou")
    @classmethod
    def validate_tou(cls, v: str) -> str:
        if not v:
            raise ValueError("時間電價為必填")
        return v
