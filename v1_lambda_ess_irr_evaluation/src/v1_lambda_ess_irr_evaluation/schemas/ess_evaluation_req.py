from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ContractCapacity(BaseModel):
    """契約容量結構"""

    經常契約: float = Field(..., description="經常契約容量")
    半尖峰契約_非夏月契約: float = Field(
        0, alias="半尖峰契約/非夏月契約", description="半尖峰契約/非夏月契約"
    )
    週六半尖峰契約: float = Field(0, description="週六半尖峰契約")
    離峰契約: float = Field(0, description="離峰契約")

    @field_validator("經常契約")
    @classmethod
    def validate_regular_contract(cls, v: float) -> float:
        return v

    @field_validator("半尖峰契約_非夏月契約")
    @classmethod
    def validate_semi_peak_contract(cls, v: float) -> float:
        return v

    @field_validator("週六半尖峰契約")
    @classmethod
    def validate_saturday_semi_peak_contract(cls, v: float) -> float:
        return v

    @field_validator("離峰契約")
    @classmethod
    def validate_off_peak_contract(cls, v: float) -> float:
        return v


class ElectricityPlan(BaseModel):
    """電價方案設定"""

    契約容量: Optional[float] = Field(None, description="契約容量")
    計費類別: Optional[str] = Field(None, description="計費類別")
    行業別: Optional[str] = Field(None, description="行業別")
    夏月天數: Optional[float] = Field(None, description="夏月天數")
    非夏月天數: Optional[float] = Field(None, description="非夏月天數")
    夏月最高電價: Optional[float] = Field(None, description="夏月最高電價")
    夏月最低電價: Optional[float] = Field(None, description="夏月最低電價")
    非夏月最高電價: Optional[float] = Field(None, description="非夏月最高電價")
    非夏月最低電價: Optional[float] = Field(None, description="非夏月最低電價")
    電費調整係數: Optional[float] = Field(None, description="電費調整係數")

    @field_validator("契約容量")
    @classmethod
    def validate_contract_capacity(cls, v: Optional[float]) -> Optional[float]:
        return v

    @field_validator("計費類別")
    @classmethod
    def validate_billing_type(cls, v: Optional[str]) -> Optional[str]:
        return v

    @field_validator("行業別")
    @classmethod
    def validate_industry(cls, v: Optional[str]) -> Optional[str]:
        return v


class ContractReduction(BaseModel):
    """降低契約容量設定"""

    每kW契約容量費用: Optional[float] = Field(None, description="每kW契約容量費用")
    年契約容量費用: Optional[float] = Field(None, description="年契約容量費用")
    降契約容量比例: Optional[float] = Field(None, description="降契約容量比例")
    降低契約容量收益: Optional[float] = Field(None, description="降低契約容量收益")

    @field_validator("每kW契約容量費用")
    @classmethod
    def validate_per_kw_cost(cls, v: Optional[float]) -> Optional[float]:
        return v


class EnergySystem(BaseModel):
    """儲能系統設定"""

    單台_PCS_標稱功率: float = Field(
        ..., alias="單台 PCS 標稱功率", description="單台 PCS 標稱功率"
    )
    單台_儲能容量: float = Field(
        ..., alias="單台 儲能容量", description="單台 儲能容量"
    )
    台數: Optional[int] = Field(None, description="台數")
    PCS_標稱功率: Optional[float] = Field(
        None, alias="PCS 標稱功率", description="PCS 標稱功率"
    )
    儲能容量: Optional[float] = Field(None, description="儲能容量")
    實際建置容量: Optional[float] = Field(None, description="實際建置容量")
    電能損失率RoundTrip: float = Field(
        ..., alias="電能損失率(Round Trip)", description="電能損失率"
    )
    儲能健康度年衰減率: float = Field(..., description="儲能健康度年衰減率")
    SOC上限: float = Field(..., description="SOC上限")
    SOC下限: float = Field(..., description="SOC下限")
    每日最大循環次數: int = Field(..., description="每日最大循環次數")

    @field_validator("單台_PCS_標稱功率")
    @classmethod
    def validate_single_pcs_power(cls, v: float) -> float:
        return v

    @field_validator("單台_儲能容量")
    @classmethod
    def validate_single_storage_capacity(cls, v: float) -> float:
        return v

    @field_validator("每日最大循環次數")
    @classmethod
    def validate_daily_cycles(cls, v: int) -> int:
        return v


class LoadSimulation(BaseModel):
    """負載模擬參數"""

    夏月每日可轉移度數: Optional[float] = Field(None, description="夏月每日可轉移度數")
    非夏月每日可轉移度數: Optional[float] = Field(
        None, description="非夏月每日可轉移度數"
    )

    @field_validator("夏月每日可轉移度數")
    @classmethod
    def validate_summer_transferable(cls, v: Optional[float]) -> Optional[float]:
        return v


class ConstructionCost(BaseModel):
    """建置成本(第0年繳)"""

    每單位建置成本: float = Field(..., description="每單位建置成本")
    儲能設備: Optional[float] = Field(None, description="儲能設備")
    儲能設備安裝: float = Field(0, description="儲能設備安裝")
    高壓設備: float = Field(0, description="高壓設備")
    高壓設備安裝: float = Field(0, description="高壓設備安裝")
    設計_監造_簽證費用: float = Field(
        0, alias="設計/監造/簽證費用", description="設計/監造/簽證費用"
    )
    EMS: Optional[float] = Field(None, description="EMS")
    其他: float = Field(0, description="其他")

    @field_validator("每單位建置成本")
    @classmethod
    def validate_unit_cost(cls, v: float) -> float:
        return v


class OperationCost(BaseModel):
    """維運成本(年繳)"""

    土地年租金: float = Field(0, description="土地年租金")
    保險費率: float = Field(..., description="保險費率")
    案場維運成本: Optional[float] = Field(None, description="案場維運成本")
    EMS維運成本: Optional[float] = Field(None, description="EMS維運成本")
    電力交易雲端平台: Optional[float] = Field(None, description="電力交易雲端平台")
    其他固定成本: float = Field(..., description="其他固定成本")

    @field_validator("保險費率")
    @classmethod
    def validate_insurance_rate(cls, v: float) -> float:
        return v


class SystemServicePrice(BaseModel):
    """系統服務單價"""

    EMS系統含硬體_kWh: float = Field(..., description="EMS系統含硬體_kWh")
    電力交易雲端使用費_MW: float = Field(..., description="電力交易雲端使用費_MW")
    電力交易之場域通訊使用_年: float = Field(
        ..., description="電力交易之場域通訊使用_年"
    )
    EMS保固維運費用_年_百分比: float = Field(
        ..., alias="EMS保固維運費用_年_%", description="EMS保固維運費用_年_%"
    )
    案場維運費用_年_百分比: float = Field(
        ..., alias="案場維運費用_年_%", description="案場維運費用_年_%"
    )

    @field_validator("EMS系統含硬體_kWh")
    @classmethod
    def validate_ems_hardware_cost(cls, v: float) -> float:
        return v


class AggregationProfit(BaseModel):
    """聚合分潤設定"""

    聚合分潤比例: float = Field(..., description="聚合分潤比例")

    @field_validator("聚合分潤比例")
    @classmethod
    def validate_aggregation_profit_ratio(cls, v: float) -> float:
        return v


class ArbitrageSettings(BaseModel):
    """可套利天數設定"""

    可能超約天數: float = Field(0, description="可能超約天數")
    歲修天數: float = Field(..., description="歲修天數")

    @field_validator("歲修天數")
    @classmethod
    def validate_maintenance_days(cls, v: float) -> float:
        return v


class SpinningReserve(BaseModel):
    """即時備轉設定"""

    投標容量: Optional[float] = Field(None, description="投標容量")
    一級效能價格: float = Field(..., alias="1級效能價格", description="1級效能價格")
    容量價格: float = Field(..., description="容量價格")
    得標容量比例: float = Field(..., description="得標容量比例")
    折扣比例: float = Field(..., description="折扣比例")
    每月觸發次數: float = Field(..., description="每月觸發次數")
    日前電能邊際價格: float = Field(..., description="日前電能邊際價格")
    保留比例: Optional[float] = Field(None, description="保留比例")
    保留容量: Optional[float] = Field(None, description="保留容量")

    @field_validator("一級效能價格")
    @classmethod
    def validate_performance_price(cls, v: float) -> float:
        return v


class AncillaryHours(BaseModel):
    """可參與輔助服務時數"""

    不可投標天數: Optional[float] = Field(None, description="不可投標天數")

    @field_validator("不可投標天數")
    @classmethod
    def validate_non_bid_days(cls, v: Optional[float]) -> Optional[float]:
        return v


class DemandResponse(BaseModel):
    """日選時段型設定"""

    執行方案: Optional[str] = Field(None, description="執行方案")
    抑低契約容量: Optional[float] = Field(None, description="抑低契約容量")
    開始時段: Optional[int] = Field(None, description="開始時段")
    結束時段: Optional[int] = Field(None, description="結束時段")
    執行時數: Optional[int] = Field(None, description="執行時數")
    流動電費扣減費率: Optional[float] = Field(None, description="流動電費扣減費率")
    當日執行率: float = Field(..., description="當日執行率")
    扣減比率: float = Field(..., description="扣減比率")
    五月_十月天數: float = Field(..., alias="5月-10月天數", description="5月-10月天數")
    五月_十月可參與天數: Optional[float] = Field(
        None, alias="5月-10月可參與天數", description="5月-10月可參與天數"
    )

    @field_validator("當日執行率")
    @classmethod
    def validate_execution_rate(cls, v: float) -> float:
        return v


class LargeConsumer(BaseModel):
    """再生能源義務用戶設定"""

    義務裝置容量: Optional[float] = Field(None, description="義務裝置容量")
    義務裝置容量比例: float = Field(..., description="義務裝置容量比例")
    早鳥抵減比例: float = Field(0, description="早鳥抵減比例")
    既設抵減比例: float = Field(0, description="既設抵減比例")

    @field_validator("義務裝置容量比例")
    @classmethod
    def validate_obligation_capacity_ratio(cls, v: float) -> float:
        return v


class FinancingCost(BaseModel):
    """融資成本設定"""

    貸款成數: float = Field(..., description="貸款成數")
    利息費用: float = Field(..., description="利息費用")
    攤還年限: int = Field(..., description="攤還年限")

    @field_validator("貸款成數")
    @classmethod
    def validate_loan_ratio(cls, v: float) -> float:
        return v

    @field_validator("利息費用")
    @classmethod
    def validate_interest_rate(cls, v: float) -> float:
        return v

    @field_validator("攤還年限")
    @classmethod
    def validate_loan_term(cls, v: int) -> int:
        return v


class AdvancedConfig(BaseModel):
    """進階設定總配置"""

    電價方案: ElectricityPlan = Field(
        default_factory=ElectricityPlan, description="電價方案"
    )
    降低契約容量: ContractReduction = Field(
        default_factory=ContractReduction, description="降低契約容量"
    )
    儲能系統: EnergySystem = Field(..., description="儲能系統")
    負載模擬參數: LoadSimulation = Field(
        default_factory=LoadSimulation, description="負載模擬參數"
    )
    建置成本_第0年繳: ConstructionCost = Field(
        ..., alias="建置成本(第0年繳)", description="建置成本(第0年繳)"
    )
    維運成本_年繳: OperationCost = Field(
        ..., alias="維運成本(年繳)", description="維運成本(年繳)"
    )
    系統服務單價: SystemServicePrice = Field(..., description="系統服務單價")
    聚合分潤: AggregationProfit = Field(..., description="聚合分潤")
    可套利天數: ArbitrageSettings = Field(..., description="可套利天數")
    即時備轉: SpinningReserve = Field(..., description="即時備轉")
    可參與輔助服務時數: AncillaryHours = Field(
        default_factory=AncillaryHours, description="可參與輔助服務時數"
    )
    日選時段型: DemandResponse = Field(..., description="日選時段型")
    再生能源義務用戶: LargeConsumer = Field(..., description="再生能源義務用戶")
    融資成本: FinancingCost = Field(..., description="融資成本")

    @field_validator("儲能系統")
    @classmethod
    def validate_energy_system(cls, v: EnergySystem) -> EnergySystem:
        return v


class AMICurveDataPoint(BaseModel):
    hour: str = Field(..., description="時間")
    summer_monday: float = Field(..., description="夏月週一")
    summer_tuesday: float = Field(..., description="夏月週二")
    summer_wednesday: float = Field(..., description="夏月週三")
    summer_thursday: float = Field(..., description="夏月週四")
    summer_friday: float = Field(..., description="夏月週五")
    summer_saturday: float = Field(..., description="夏月週六")
    summer_sunday: float = Field(..., description="夏月週日")
    non_summer_monday: float = Field(..., description="非夏月週一")
    non_summer_tuesday: float = Field(..., description="非夏月週二")
    non_summer_wednesday: float = Field(..., description="非夏月週三")
    non_summer_thursday: float = Field(..., description="非夏月週四")
    non_summer_friday: float = Field(..., description="非夏月週五")
    non_summer_saturday: float = Field(..., description="非夏月週六")
    non_summer_sunday: float = Field(..., description="非夏月週日")


class ESSEvaluationRequest(BaseModel):
    """ESS評估請求"""

    config: AdvancedConfig = Field(..., description="進階配置")
    manual_curve_data: Optional[AMICurveDataPoint] = Field(None, description="手拉負載")
    ami_uploaded_raw_data: Optional[AMICurveDataPoint] = Field(
        None, description="上傳負載"
    )
    units: Optional[str] = Field(None, description="購買台數")
    contract_capacity_old: ContractCapacity = Field(..., description="原契約容量")
    contract_capacity_new: ContractCapacity = Field(..., description="新契約容量")
    priceType: str = Field(..., description="電價類別")
    industry: str = Field(..., description="行業別")
    profitSpec: str = Field("", description="獲利規格")
    userId: str = Field(..., description="使用者ID")
    chartId: str = Field(..., description="圖表ID")
    workDay: list[str] = Field(..., description="工作日")
    workHour: list[int] = Field(..., description="工作時間")
    workThreshold: float = Field(..., description="工作閾值")
    restThreshold: float = Field(..., description="休息閾值")
    tariff: float = Field(..., description="電費調整係數")
    dr方案選項: list[str] = Field(default_factory=list, description="DR方案選項")
    即時備轉方案選項: list[str] = Field(
        default_factory=list, description="即時備轉方案選項"
    )
    year: int = Field(15, description="評估年限")
    用電大戶方案: list[str] = Field(default_factory=list, description="用電大戶方案")

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: AdvancedConfig) -> AdvancedConfig:
        return v

    @field_validator("manual_curve_data")
    @classmethod
    def validate_manual_curve_data(cls, v: AMICurveDataPoint) -> AMICurveDataPoint:
        return v

    @field_validator("units")
    @classmethod
    def validate_units(cls, v: str) -> str:
        return v

    @field_validator("contract_capacity_old")
    @classmethod
    def validate_contract_capacity_old(cls, v: ContractCapacity) -> ContractCapacity:
        return v

    @field_validator("contract_capacity_new")
    @classmethod
    def validate_contract_capacity_new(cls, v: ContractCapacity) -> ContractCapacity:
        return v

    @field_validator("priceType")
    @classmethod
    def validate_price_type(cls, v: str) -> str:
        return v

    @field_validator("industry")
    @classmethod
    def validate_industry(cls, v: str) -> str:
        return v

    @field_validator("profitSpec")
    @classmethod
    def validate_profit_spec(cls, v: str) -> str:
        return v

    @field_validator("userId")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        return v

    @field_validator("chartId")
    @classmethod
    def validate_chart_id(cls, v: str) -> str:
        return v

    @field_validator("workDay")
    @classmethod
    def validate_work_day(cls, v: list[str]) -> list[str]:
        return v

    @field_validator("workHour")
    @classmethod
    def validate_work_hour(cls, v: list[int]) -> list[int]:
        return v

    @field_validator("workThreshold")
    @classmethod
    def validate_work_threshold(cls, v: float) -> float:
        return v

    @field_validator("restThreshold")
    @classmethod
    def validate_rest_threshold(cls, v: float) -> float:
        return v

    @field_validator("tariff")
    @classmethod
    def validate_tariff(cls, v: float) -> float:
        return v

    @field_validator("dr方案選項")
    @classmethod
    def validate_dr_options(cls, v: list[str]) -> list[str]:
        return v

    @field_validator("即時備轉方案選項")
    @classmethod
    def validate_spinning_options(cls, v: list[str]) -> list[str]:
        return v

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        return v

    @field_validator("用電大戶方案")
    @classmethod
    def validate_large_consumer_options(cls, v: list[str]) -> list[str]:
        return v
