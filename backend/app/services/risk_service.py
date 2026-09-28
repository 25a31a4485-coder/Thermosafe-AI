import re
import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple

from app.schemas.risk_assessment import RiskAnalysisRequest, RiskAnalysisResponse

logger = logging.getLogger("risk_service")


class BaseRiskEngine(ABC):
    """
    Abstract interface for thermal risk assessment engines.
    
    This architecture enables the scoring methodology, weight distribution,
    or predictive safety model to be upgraded or calibrated without modifying
    API endpoints, data contracts, or consumer clients.
    """

    @abstractmethod
    def evaluate_risk(self, request: RiskAnalysisRequest) -> RiskAnalysisResponse:
        """Calculates multi-factor composite risk score and factor breakdown."""
        pass


class PrototypeHeuristicRiskEngine(BaseRiskEngine):
    """
    Transparent prototype risk assessment engine.
    
    =============================================================================
    PROTOTYPE RISK METHODOLOGY DISCLAIMER:
    This engine implements a heuristic rule-based prototype risk assessment model
    developed for exploratory triage and operational demonstration. It is NOT
    an officially certified, actuarially verified, or regulatory-approved industrial
    safety model (e.g. OSHA, IEC 61508, or SEVESO III compliant).
    
    Risk scores (0–100) are computed through multi-factor weighted aggregation across
    thermal radiative output, temporal duration, infrastructure distance, population
    exposure, historical recurrence, and AI classification modifiers.
    
    Standardized Risk Priority Tiers:
      - Low:      0 – 24
      - Moderate: 25 – 49
      - High:     50 – 74
      - Critical: 75 – 100
    =============================================================================
    """

    METHODOLOGY_TAG = "ThermalSafe Prototype Risk Index v1.0 (Experimental Heuristic Model - Not Officially Validated)"

    def _parse_mw(self, intensity_str: str) -> float:
        """Extracts numerical Megawatts (MW) from intensity string or keyword."""
        if not intensity_str:
            return 0.0
        match = re.search(r"(\d+(\.\d+)?)", intensity_str)
        if match:
            return float(match.group(1))
        
        lower = intensity_str.lower()
        if "critical" in lower:
            return 1200.0
        elif "high" in lower:
            return 650.0
        elif "moderate" in lower or "medium" in lower:
            return 320.0
        elif "low" in lower:
            return 45.0
        return 0.0

    def _calc_thermal_factor(self, mw: float, intensity_str: str) -> float:
        """Calculates thermal intensity sub-score factor on a 0 to 100 scale."""
        if mw >= 1200.0:
            return 100.0
        elif mw >= 800.0:
            return 85.0 + ((mw - 800.0) / 400.0) * 15.0
        elif mw >= 400.0:
            return 65.0 + ((mw - 400.0) / 400.0) * 20.0
        elif mw >= 150.0:
            return 40.0 + ((mw - 150.0) / 250.0) * 25.0
        elif mw >= 30.0:
            return 15.0 + ((mw - 30.0) / 120.0) * 25.0
        elif mw > 0.0:
            return (mw / 30.0) * 15.0
        
        lower = intensity_str.lower()
        if "critical" in lower:
            return 95.0
        elif "high" in lower:
            return 75.0
        elif "moderate" in lower or "medium" in lower:
            return 50.0
        elif "low" in lower:
            return 20.0
        return 0.0

    def _calc_persistence_factor(self, persistence_str: str) -> float:
        """Calculates temporal persistence sub-score factor on a 0 to 100 scale."""
        lower = (persistence_str or "").lower()
        if "continuous" in lower or "36+" in lower or "sustained" in lower or "90+" in lower:
            return 95.0
        elif "recurrent" in lower or "8 hours" in lower or "reoccurring" in lower:
            return 75.0
        elif "semi-continuous" in lower or "scheduled" in lower or "intermittent" in lower:
            return 50.0
        elif "transient" in lower or "< 2" in lower or "< 4" in lower or "1 hour" in lower:
            return 20.0
        return 45.0

    def _calc_industrial_proximity_factor(
        self,
        dist_km: Optional[float],
        facility_name: Optional[str]
    ) -> float:
        """Calculates industrial infrastructure proximity factor on a 0 to 100 scale."""
        if dist_km is not None:
            if dist_km <= 0.2:
                return 100.0
            elif dist_km <= 1.0:
                return 85.0 - (dist_km - 0.2) * 15.0
            elif dist_km <= 3.0:
                return 65.0 - (dist_km - 1.0) * 10.0
            elif dist_km <= 8.0:
                return 40.0 - (dist_km - 3.0) * 5.0
            elif dist_km <= 15.0:
                return 15.0
            else:
                return 5.0
        
        # Infer from facility presence / keywords if exact distance not supplied
        if facility_name and facility_name.strip():
            fac_lower = facility_name.lower()
            if any(k in fac_lower for k in ["refinery", "chemical", "petrochemical", "hydrocracker"]):
                return 95.0
            elif any(k in fac_lower for k in ["port", "steel", "terminal", "power", "platform"]):
                return 85.0
            elif "buffer" in fac_lower or "perimeter" in fac_lower:
                return 35.0
            return 75.0
        
        return 10.0

    def _calc_population_proximity_factor(self, pop_km: Optional[float]) -> Tuple[float, bool]:
        """Calculates population proximity factor (returns (factor, is_data_available))."""
        if pop_km is None:
            return 0.0, False
        
        if pop_km <= 1.0:
            return 100.0, True
        elif pop_km <= 2.5:
            return 85.0, True
        elif pop_km <= 5.0:
            return 55.0, True
        elif pop_km <= 10.0:
            return 30.0, True
        else:
            return 10.0, True

    def _calc_historical_factor(self, occurrences: int) -> float:
        """Calculates historical recurrence factor on a 0 to 100 scale."""
        if occurrences >= 20:
            return 85.0
        elif occurrences >= 10:
            return 70.0
        elif occurrences >= 5:
            return 55.0
        elif occurrences >= 2:
            return 40.0
        elif occurrences == 1:
            return 25.0
        return 15.0

    def _calc_context_modifier(
        self,
        ai_class: Optional[str],
        event_type: Optional[str]
    ) -> float:
        """Calculates context modifier based on AI classification and event type."""
        combined = f"{ai_class or ''} {event_type or ''}".lower()
        if "critical industrial fire" in combined or "blaze" in combined:
            return 12.0
        elif "high-risk" in combined:
            return 6.0
        elif "gas flare" in combined or "flaring" in combined:
            # Controlled operational combustion reduces catastrophic runaway risk
            return -12.0
        elif "persistent thermal source" in combined:
            return -6.0
        elif "low-risk" in combined:
            return -15.0
        return 0.0

    def _determine_priority(self, score: float) -> str:
        """Maps composite score to standardized risk priority."""
        if score >= 75.0:
            return "Critical"
        elif score >= 50.0:
            return "High"
        elif score >= 25.0:
            return "Moderate"
        return "Low"

    def evaluate_risk(self, req: RiskAnalysisRequest) -> RiskAnalysisResponse:
        """
        Calculates multi-factor risk assessment response.
        """
        mw = self._parse_mw(req.thermal_intensity)
        f_thermal = self._calc_thermal_factor(mw, req.thermal_intensity)
        f_persist = self._calc_persistence_factor(req.persistence)
        f_ind_prox = self._calc_industrial_proximity_factor(
            req.industrial_facility_proximity_km,
            req.nearby_industrial_facility
        )
        f_pop_prox, has_pop_data = self._calc_population_proximity_factor(req.population_proximity_km)
        f_hist = self._calc_historical_factor(req.historical_recurrence or 0)
        modifier = self._calc_context_modifier(req.ai_classification, req.event_type)

        # Dynamic weighting based on population data availability
        if has_pop_data:
            w_thermal = 0.30
            w_persist = 0.20
            w_ind = 0.20
            w_pop = 0.15
            w_hist = 0.05
            raw_score = (
                (f_thermal * w_thermal)
                + (f_persist * w_persist)
                + (f_ind_prox * w_ind)
                + (f_pop_prox * w_pop)
                + (f_hist * w_hist)
                + modifier
            )
        else:
            w_thermal = 0.35
            w_persist = 0.25
            w_ind = 0.25
            w_pop = 0.00
            w_hist = 0.05
            raw_score = (
                (f_thermal * w_thermal)
                + (f_persist * w_persist)
                + (f_ind_prox * w_ind)
                + (f_hist * w_hist)
                + modifier
            )

        # Enforce scale constraints: 0.0 to 100.0
        bounded_score = max(0.0, min(100.0, round(raw_score, 1)))
        priority = self._determine_priority(bounded_score)

        # Build detailed explanation
        pop_str = f"{f_pop_prox:.1f} (dist: {req.population_proximity_km}km)" if has_pop_data else "Not provided (re-weighted to industrial & thermal factors)"
        explanation = (
            f"Prototype risk score {bounded_score}/100 ({priority}). Contributing factors: "
            f"Thermal Output={f_thermal:.1f} ({mw:.0f} MW), "
            f"Persistence={f_persist:.1f} ('{req.persistence}'), "
            f"Industrial Proximity={f_ind_prox:.1f}, "
            f"Population Exposure={pop_str}, "
            f"Historical Cluster={f_hist:.1f} ({req.historical_recurrence or 0} events), "
            f"Context Modifier={modifier:+.1f} ('{req.ai_classification or req.event_type or 'Standard'}')."
        )

        logger.info(f"Evaluated risk: Score={bounded_score}, Priority={priority}, AI={req.ai_classification}")

        return RiskAnalysisResponse(
            risk_score=bounded_score,
            risk_priority=priority,
            thermal_factor=round(f_thermal, 1),
            persistence_factor=round(f_persist, 1),
            industrial_proximity_factor=round(f_ind_prox, 1),
            population_proximity_factor=round(f_pop_prox, 1),
            historical_factor=round(f_hist, 1),
            explanation=explanation,
            methodology=self.METHODOLOGY_TAG
        )


# Global singleton instance for prototype risk engine
_risk_engine_instance: Optional[BaseRiskEngine] = None


def get_risk_engine() -> BaseRiskEngine:
    """
    Factory dependency providing the active risk assessment engine.
    Allows calibrated or trained safety models to replace this prototype
    without altering existing router endpoints or callers.
    """
    global _risk_engine_instance
    if _risk_engine_instance is None:
        _risk_engine_instance = PrototypeHeuristicRiskEngine()
    return _risk_engine_instance
