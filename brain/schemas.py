from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class TechnicalAnalysisOutput(BaseModel):
    trend: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    signal: Literal["BUY_CE", "BUY_PE", "SELL_CE", "SELL_PE", "NO_TRADE"]
    support_level: float
    resistance_level: float
    confidence: float = Field(..., ge=0.0, le=1.0)
    key_drivers: List[str]

class GreeksAnalysisOutput(BaseModel):
    iv_regime: Literal["LOW_VOL", "NORMAL_VOL", "HIGH_VOL", "EXTREME_VOL"]
    pcr_signal: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    recommended_strategy: Literal["BUY_CALL", "BUY_PUT", "IRON_CONDOR", "SHORT_STRADDLE", "NO_TRADE"]
    delta_exposure: float
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str

class SentimentAnalysisOutput(BaseModel):
    macro_bias: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    unusual_activity_summary: str
    vix_bias: Literal["RISK_ON", "RISK_OFF", "NEUTRAL"]
    confidence: float = Field(..., ge=0.0, le=1.0)

class RiskAssessmentOutput(BaseModel):
    approved: bool
    risk_score: float = Field(..., ge=0.0, le=100.0) # Higher means safer
    max_allowed_lots: int
    veto_reason: Optional[str] = None

class FinalTradingSignal(BaseModel):
    signal_id: str
    timestamp: str
    symbol: str
    action: Literal["BUY_CE", "BUY_PE", "SELL_CE", "SELL_PE", "NO_TRADE"]
    strike_price: float
    option_type: Literal["CE", "PE"]
    expiry: str
    recommended_lots: int
    entry_target_range: List[float]
    stop_loss_points: float
    take_profit_points: float
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    agents_consensus_pct: float
    risk_vetoed: bool
    rationale: str
