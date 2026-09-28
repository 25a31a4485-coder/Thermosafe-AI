import re
import math
import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime, timezone

from app.schemas.ai_classification import AIClassifyRequest, AIClassifyResponse
from app.core.database import SessionLocal
from app.models.facility import IndustrialFacility

logger = logging.getLogger("ai_service")


def haversine_dist(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class BaseThermalClassifier(ABC):
    """
    Abstract interface for thermal anomaly AI classification engines.
    """

    @abstractmethod
    def classify(self, request: AIClassifyRequest) -> AIClassifyResponse:
        """Evaluates thermal features and returns a standardized classification response."""
        pass


class HeuristicPrototypeClassifier(BaseThermalClassifier):
    """
    Transparent, AI-assisted / evidence-based thermal-source classification prototype.
    
    IMPORTANT NOTICE:
    This engine is an explicit transparent evidence-based heuristic classification engine
    designed for SIH26162 thermal anomaly segregation. It is NOT a trained statistical
    machine-learning or deep-learning model. It evaluates domain heuristics across
    satellite Fire Radiative Power (MW), temporal persistence signatures, infrastructure
    co-location, land-cover context, and historical cluster recurrence.
    """

    MODEL_NAME = "ThermalSafe-RuleEngine-Prototype-v1"

    def _parse_mw(self, intensity_str: str) -> float:
        """Parses numeric Megawatts (MW) from intensity string or keyword."""
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

    def _resolve_facility_association(self, req: AIClassifyRequest) -> Dict[str, Any]:
        """
        Resolves nearby industrial facility context, computes distance, and determines association confidence.
        Note: Proximity does NOT automatically mean source/cause.
        """
        fac_name = req.nearby_industrial_facility
        fac_id = req.facility_id
        fac_type = req.facility_type or "Industrial Facility"
        dist_km = req.facility_distance_km

        if dist_km is None or not fac_name:
            # Attempt spatial lookup in database
            try:
                with SessionLocal() as db:
                    facilities = db.query(IndustrialFacility).all()
                    closest = None
                    min_dist = float("inf")
                    for f in facilities:
                        d = haversine_dist(req.latitude, req.longitude, f.latitude, f.longitude)
                        if d < min_dist:
                            min_dist = d
                            closest = f
                    if closest and min_dist <= 15.0:
                        fac_name = closest.name
                        fac_id = closest.id
                        fac_type = closest.industry_type
                        dist_km = round(min_dist, 2)
            except Exception as e:
                logger.debug(f"Facility association db query notice: {e}")

        if fac_name and dist_km is not None and dist_km <= 5.0:
            assoc_conf = max(0.20, min(0.96, round(1.0 - (dist_km / 7.0), 2)))
            assoc_reason = (
                f"Nearby industrial infrastructure '{fac_name}' identified at {dist_km:.2f} km. "
                "Contextual spatial association established; proximity is an operational factor, not confirmed sole causation."
            )
            return {
                "facility_id": fac_id,
                "facility_name": fac_name,
                "facility_type": fac_type,
                "distance_km": dist_km,
                "association_reason": assoc_reason,
                "association_confidence": assoc_conf
            }
        elif fac_name:
            return {
                "facility_id": fac_id,
                "facility_name": fac_name,
                "facility_type": fac_type,
                "distance_km": dist_km,
                "association_reason": f"Facility '{fac_name}' referenced in telemetry context.",
                "association_confidence": 0.40
            }

        return {
            "facility_id": None,
            "facility_name": None,
            "facility_type": None,
            "distance_km": None,
            "association_reason": "No industrial facility identified within immediate perimeter.",
            "association_confidence": 0.0
        }

    def _determine_persistence(self, persistence_str: str, history: int) -> str:
        """Categorizes temporal persistence into ONE_TIME_EVENT, REPEATED_ACTIVITY, or PERSISTENT_SOURCE."""
        p_lower = (persistence_str or "").lower()
        if "continuous" in p_lower or "persistent" in p_lower or "36+" in p_lower or "90+" in p_lower or history >= 15:
            return "PERSISTENT_SOURCE"
        elif "recurrent" in p_lower or "semi-continuous" in p_lower or "repeated" in p_lower or history >= 2 or "8 hour" in p_lower:
            return "REPEATED_ACTIVITY"
        return "ONE_TIME_EVENT"

    def _evaluate_rules(self, req: AIClassifyRequest) -> Tuple[str, float, str, str, str, str, str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Evaluates input telemetry against the SIH26162 taxonomy and segregation rules:
        1. INDUSTRIAL_FIRE (Critical Industrial Fire, Industrial Fire)
        2. FOREST_OR_WILDFIRE (Forest/Wildfire)
        3. AGRICULTURAL_BURNING (Agricultural Burning)
        4. GAS_FLARE (Gas Flare)
        5. MINING_THERMAL_ACTIVITY (Mining Activity)
        6. PERSISTENT_INDUSTRIAL_THERMAL_SOURCE (Persistent Industrial Thermal Source)
        7. OTHER_THERMAL_EVENT (Low-Risk Thermal Activity, Other Thermal Event)
        8. UNKNOWN (Unknown / Insufficient Evidence)
        """
        mw = self._parse_mw(req.thermal_intensity)
        persistence_lower = (req.persistence or "").lower()
        facility_lower = (req.nearby_industrial_facility or "").lower()
        land_cover_lower = (req.land_cover or "").lower()
        has_facility = bool(req.nearby_industrial_facility and req.nearby_industrial_facility.strip())
        history = req.historical_occurrences or 0

        # Persistence resolution
        persistence_status = self._determine_persistence(req.persistence, history)
        is_continuous = persistence_status == "PERSISTENT_SOURCE"
        is_transient = persistence_status == "ONE_TIME_EVENT"

        # Facility association
        fac_assoc = self._resolve_facility_association(req)
        has_nearby_fac = bool(fac_assoc.get("facility_name"))
        fac_name = fac_assoc.get("facility_name") or req.nearby_industrial_facility

        # Specific context flags
        is_flare_context = (
            "flare" in facility_lower or "flare" in persistence_lower or "offshore" in facility_lower
            or "platform" in facility_lower or "offshore" in land_cover_lower or "marine" in land_cover_lower
            or "refinery" in facility_lower
        )
        is_power_or_baseline = (
            "power" in facility_lower or "power" in land_cover_lower or "boiler" in persistence_lower
            or "slag" in land_cover_lower or history >= 10
        )
        is_mining_context = (
            "mining" in land_cover_lower or "mine" in land_cover_lower or "quarry" in land_cover_lower
            or "open pit" in land_cover_lower or "overburden" in land_cover_lower or "coal" in facility_lower
        )
        is_forest_context = (
            ("forest" in land_cover_lower or "wildfire" in land_cover_lower or "woodland" in land_cover_lower or "jungle" in land_cover_lower or "timber" in land_cover_lower)
            and not has_nearby_fac
        )
        is_agri_context = (
            ("agricultural" in land_cover_lower or "crop" in land_cover_lower or "stubble" in land_cover_lower or "paddy" in land_cover_lower or "farm" in land_cover_lower)
            and not has_nearby_fac
        )
        is_industrial_zone = (
            has_facility or has_nearby_fac or "industrial" in land_cover_lower or "refinery" in land_cover_lower or "steel" in land_cover_lower
        )

        # -----------------------------------------------------------------
        # 1. Critical Industrial Fire / Industrial Fire (INDUSTRIAL)
        # -----------------------------------------------------------------
        if (mw >= 750.0 or "critical" in req.thermal_intensity.lower()) and is_industrial_zone and is_continuous and not is_flare_context:
            conf = min(0.98, max(0.93, 0.90 + (mw / 5000.0)))
            site_label = fac_name or "Heavy Industrial Perimeter"
            expl = (
                f"Severe thermal anomaly with extreme radiant power ({mw:.0f} MW) co-located with critical industrial "
                f"facility '{site_label}' exhibiting continuous duration. Multi-tank containment breach or structural blaze suspected."
            )
            tax_code = "INDUSTRIAL_FIRE"
            tax_label = "Industrial Fire"
            group = "INDUSTRIAL"
            classif_label = "Critical Industrial Fire"

        # -----------------------------------------------------------------
        # 2. Gas Flare (INDUSTRIAL)
        # -----------------------------------------------------------------
        elif is_flare_context and 80.0 <= mw <= 700.0 and not ("fire" in persistence_lower and mw > 500):
            conf = min(0.96, max(0.90, 0.92 + (0.04 if "flare" in facility_lower or "flare" in persistence_lower else 0.0)))
            target_site = fac_name or "Offshore/Refinery Platform"
            expl = (
                f"Thermal signature ({mw:.0f} MW) matches operational flaring profile at '{target_site}'. "
                f"Infrared emission corresponds to scheduled or pressure-relief gaseous combustion."
            )
            tax_code = "GAS_FLARE"
            tax_label = "Gas Flare"
            group = "INDUSTRIAL"
            classif_label = "Gas Flare"

        # -----------------------------------------------------------------
        # 3. Persistent Industrial Thermal Source (INDUSTRIAL)
        # -----------------------------------------------------------------
        elif is_power_or_baseline and (is_continuous or history >= 10) and 100.0 <= mw <= 700.0:
            conf = min(0.95, max(0.88, 0.88 + min(0.06, history * 0.003)))
            site_name = fac_name or "Industrial Facility"
            expl = (
                f"Baseline chronic thermal emitter at '{site_name}' with {history} historical occurrences in vicinity. "
                f"Thermal power ({mw:.0f} MW) is consistent with continuous boiler flue exhaust or slag cooling."
            )
            tax_code = "PERSISTENT_INDUSTRIAL_THERMAL_SOURCE"
            tax_label = "Persistent Industrial Thermal Source"
            group = "INDUSTRIAL"
            classif_label = "Persistent Thermal Source"

        # -----------------------------------------------------------------
        # 4. Forest / Wildfire (NATURAL/FOREST)
        # -----------------------------------------------------------------
        elif is_forest_context:
            conf = min(0.94, max(0.82, 0.80 + (mw / 2000.0)))
            expl = (
                f"Thermal radiance ({mw:.0f} MW) detected in '{req.land_cover or 'Forest Zone'}' without associated industrial "
                "infrastructure. Profile indicates active canopy/surface vegetative wildfire progression."
            )
            tax_code = "FOREST_OR_WILDFIRE"
            tax_label = "Forest/Wildfire"
            group = "NATURAL/FOREST"
            classif_label = "Forest/Wildfire"

        # -----------------------------------------------------------------
        # 5. Agricultural Burning (NATURAL/FOREST)
        # -----------------------------------------------------------------
        elif is_agri_context:
            conf = min(0.90, max(0.75, 0.72 + (0.1 if is_transient else 0.0)))
            expl = (
                f"Localized transient thermal anomaly ({mw:.0f} MW) co-located with cropland/agricultural sector. "
                "Signature corresponds to seasonal post-harvest stubble or biomass residue burning."
            )
            tax_code = "AGRICULTURAL_BURNING"
            tax_label = "Agricultural Burning"
            group = "NATURAL/FOREST"
            classif_label = "Agricultural Burning"

        # -----------------------------------------------------------------
        # 6. Mining Thermal Activity (INDUSTRIAL)
        # -----------------------------------------------------------------
        elif is_mining_context:
            conf = min(0.92, max(0.80, 0.78 + (mw / 3000.0)))
            expl = (
                f"Thermal signature ({mw:.0f} MW) detected in open-pit mining or overburden sector. "
                "Infrared emission matches heavy extraction machinery or localized coal-seam thermal reaction."
            )
            tax_code = "MINING_THERMAL_ACTIVITY"
            tax_label = "Mining Activity"
            group = "INDUSTRIAL"
            classif_label = "Mining Activity"

        # -----------------------------------------------------------------
        # 7. High-Risk Thermal Event (INDUSTRIAL)
        # -----------------------------------------------------------------
        elif (mw >= 380.0 or "high" in req.thermal_intensity.lower()) and is_industrial_zone and not is_flare_context:
            conf = min(0.93, max(0.86, 0.86 + (mw / 3000.0)))
            target_fac = fac_name or "Industrial Sector"
            expl = (
                f"Elevated thermal radiative output ({mw:.0f} MW) adjacent to '{target_fac}'. Exceeds operational baseline; "
                f"triggers high-risk priority inspection for runaway overheating or storage hazard."
            )
            tax_code = "INDUSTRIAL_FIRE"
            tax_label = "Industrial Fire"
            group = "INDUSTRIAL"
            classif_label = "High-Risk Thermal Event"

        # -----------------------------------------------------------------
        # 8. Unknown / Insufficient Evidence (UNKNOWN)
        # -----------------------------------------------------------------
        elif mw <= 0.0 or (not has_facility and not req.land_cover) or (mw > 1000.0 and is_transient and not is_industrial_zone):
            expl = (
                f"Inconclusive telemetry (MW: {mw:.0f}, persistence: '{req.persistence}'). Features do not satisfy "
                "rule engine threshold criteria for definitive categorization."
            )
            conf = 0.45
            tax_code = "UNKNOWN"
            tax_label = "Unknown / Insufficient Evidence"
            group = "UNKNOWN"
            classif_label = "Unknown"

        # -----------------------------------------------------------------
        # 9. Low-Risk Thermal Activity / Other (OTHER)
        # -----------------------------------------------------------------
        elif (0.0 < mw < 120.0 or "low" in req.thermal_intensity.lower()) and is_transient and not ("refinery" in facility_lower or "chemical" in facility_lower):
            conf = min(0.88, max(0.74, 0.74 + (1.0 - (mw / 200.0)) * 0.1))
            expl = (
                f"Low radiant power ({mw:.0f} MW) with transient duration in '{req.land_cover or 'buffer sector'}'. "
                f"Consistent with controlled agricultural stubble clearing, perimeter brush maintenance, or transient localized burn."
            )
            tax_code = "OTHER_THERMAL_EVENT"
            tax_label = "Other Thermal Event"
            group = "OTHER"
            classif_label = "Low-Risk Thermal Activity"

        # -----------------------------------------------------------------
        # Fallback to nearest reasonable category
        # -----------------------------------------------------------------
        elif mw >= 300.0:
            conf = 0.72
            tax_code = "INDUSTRIAL_FIRE" if is_industrial_zone else "OTHER_THERMAL_EVENT"
            tax_label = "Industrial Fire" if is_industrial_zone else "Other Thermal Event"
            group = "INDUSTRIAL" if is_industrial_zone else "OTHER"
            classif_label = "High-Risk Thermal Event" if is_industrial_zone else "Other Thermal Event"
            expl = f"Elevated thermal power ({mw:.0f} MW) without conclusive baseline profile."
        elif mw >= 100.0:
            conf = 0.70
            tax_code = "OTHER_THERMAL_EVENT"
            tax_label = "Other Thermal Event"
            group = "OTHER"
            classif_label = "Low-Risk Thermal Activity"
            expl = f"Moderate thermal power ({mw:.0f} MW) under non-industrial conditions."
        else:
            conf = 0.40
            tax_code = "UNKNOWN"
            tax_label = "Unknown / Insufficient Evidence"
            group = "UNKNOWN"
            classif_label = "Unknown"
            expl = "Weak thermal signal with ambiguous geographic and persistence context."

        # Structured supporting evidence factors
        supporting_factors = [
            {
                "factor": "Radiative Power",
                "value": f"{mw:.0f} MW",
                "weight": 0.35,
                "description": "Satellite Fire Radiative Power (MW) output"
            },
            {
                "factor": "Temporal Persistence",
                "value": req.persistence,
                "weight": 0.25,
                "description": f"Observation frequency and duration ({persistence_status})"
            },
            {
                "factor": "Infrastructure Proximity",
                "value": fac_name or "No facility within 5 km",
                "weight": 0.25,
                "description": fac_assoc.get("association_reason")
            },
            {
                "factor": "Land Cover / Environment",
                "value": req.land_cover or "General Terrestrial",
                "weight": 0.15,
                "description": f"Segregation category: {group}"
            }
        ]

        return (
            classif_label,
            round(conf, 2),
            expl,
            tax_code,
            tax_label,
            group,
            persistence_status,
            fac_assoc,
            supporting_factors
        )

    def classify(self, request: AIClassifyRequest) -> AIClassifyResponse:
        """
        Executes deterministic heuristic rules against input telemetry.
        Returns a validated AIClassifyResponse conforming to SIH26162 requirements.
        """
        (
            classification,
            confidence,
            explanation,
            tax_code,
            tax_label,
            group,
            persistence_status,
            fac_assoc,
            supporting_factors
        ) = self._evaluate_rules(request)

        # Enforce confidence constraint: strictly between 0.0 and 1.0
        bounded_confidence = max(0.01, min(0.99, confidence))

        logger.info(
            f"Classified event at ({request.latitude}, {request.longitude}) -> {classification} "
            f"[{group} / {tax_code}] (conf: {bounded_confidence:.2f}) via {self.MODEL_NAME}"
        )

        return AIClassifyResponse(
            classification=classification,
            confidence=bounded_confidence,
            explanation=explanation,
            model_name=self.MODEL_NAME,
            taxonomy_code=tax_code,
            taxonomy_label=tax_label,
            industrial_natural_group=group,
            reason=f"AI-assisted / evidence-based thermal-source classification: {explanation}",
            supporting_factors=supporting_factors,
            facility_association=fac_assoc,
            persistence_status=persistence_status,
            classification_timestamp=datetime.now(timezone.utc)
        )


# Global singleton instance for prototype classifier
_classifier_instance: Optional[BaseThermalClassifier] = None


def get_classifier() -> BaseThermalClassifier:
    """
    Factory dependency providing the active AI classifier.
    """
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = HeuristicPrototypeClassifier()
    return _classifier_instance

