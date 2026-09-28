from fastapi import APIRouter, Depends, status

from app.schemas.risk_assessment import RiskAnalysisRequest, RiskAnalysisResponse
from app.services.risk_service import BaseRiskEngine, get_risk_engine

router = APIRouter(prefix="/risk", tags=["Risk Assessment Engine"])


@router.post(
    "/analyze",
    response_model=RiskAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate composite risk score and factor breakdown for thermal event",
    description="""
    Evaluates multi-factor risk for a thermal anomaly event across 7 domain inputs:
    1. **Thermal Intensity** (MW / radiative power)
    2. **Persistence** (temporal duration pattern)
    3. **Industrial Facility Proximity** (on-site or buffer distance)
    4. **Population Proximity** (settlement exposure if data is available)
    5. **Historical Recurrence** (localized cluster detections)
    6. **AI Classification** (contextual risk modifier)
    7. **Event Type** (hazard designation)
    
    Standardized Risk Priorities:
    - **Low**: 0 – 24
    - **Moderate**: 25 – 49
    - **High**: 50 – 74
    - **Critical**: 75 – 100
    
    Returns composite score, priority category, 5 factor sub-scores, and methodology explanation.
    Built with a modular service interface to support plugging in officially certified or machine-learning
    safety models in the future.
    """,
)
def analyze_thermal_risk(
    request: RiskAnalysisRequest,
    risk_engine: BaseRiskEngine = Depends(get_risk_engine),
):
    return risk_engine.evaluate_risk(request)
