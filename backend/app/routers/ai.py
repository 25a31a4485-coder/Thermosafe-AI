from fastapi import APIRouter, Depends, status

from app.schemas.ai_classification import AIClassifyRequest, AIClassifyResponse
from app.services.ai_service import BaseThermalClassifier, get_classifier

router = APIRouter(prefix="/ai", tags=["AI Classification"])


@router.post(
    "/classify",
    response_model=AIClassifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Classify thermal anomaly using the AI classification service",
    description="""
    Evaluates multi-spectral thermal anomaly inputs (coordinates, radiative power, persistence,
    facility proximity, land cover, and recurrence history) and classifies the event into one of:
    - **Critical Industrial Fire**
    - **High-Risk Thermal Event**
    - **Gas Flare**
    - **Persistent Thermal Source**
    - **Low-Risk Thermal Activity**
    - **Unknown**
    
    Returns category, confidence score (0.0 to 1.0), transparent deterministic rationale, and model name.
    Built with a modular service architecture so trained machine learning models can cleanly replace
    the prototype rule engine in the future without modifying this endpoint.
    """,
)
def classify_thermal_event(
    request: AIClassifyRequest,
    classifier: BaseThermalClassifier = Depends(get_classifier),
):
    return classifier.classify(request)
