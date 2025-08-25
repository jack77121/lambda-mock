"""Schema for single simulation request"""
from typing import Optional
from pydantic import BaseModel, Field


class SingleSimulationRequest(BaseModel):
    """單一模擬計算請求"""
    
    # Core simulation parameters (extracted from run_simulation function)
    config: dict = Field(..., description="配置參數")
    unit: int = Field(..., description="台數")
    df_ami: Optional[dict] = Field(None, description="AMI 數據 (序列化後的 DataFrame)")
    mode: str = Field("energy_only", description="運作模式")
    dr_program: Optional[str] = Field(None, description="DR 方案")
    sp_program: Optional[str] = Field(None, description="即時備轉方案")
    lc_program: Optional[str] = Field(None, description="用電大戶方案")
    year: int = Field(15, description="評估年限")
    
    # Additional metadata for result storage
    evaluate_var_result_id: str = Field(..., description="評估變數結果ID (用於群組識別)")
    mode_key: str = Field(..., description="模式組合鍵 (例如: '電價套利-日選2h-即時單一')")
    simulation_id: str = Field(..., description="此次模擬的唯一識別碼")


class SingleSimulationResponse(BaseModel):
    """單一模擬計算回應"""
    
    success: bool = Field(..., description="執行是否成功")
    simulation_id: str = Field(..., description="模擬ID")
    evaluate_var_result_id: str = Field(..., description="群組ID")
    error_message: Optional[str] = Field(None, description="錯誤訊息")
    execution_time: Optional[float] = Field(None, description="執行時間 (秒)")