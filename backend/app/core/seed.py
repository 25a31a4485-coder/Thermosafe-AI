import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.models.facility import IndustrialFacility
from app.models.thermal_event import ThermalEvent
from app.models.ai_classification import AIClassification
from app.models.operator_team import EmergencyResponseTeam
from app.models.user import User, UserRole
from app.core.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

DEMO_FACILITIES = [
    {
        "name": "Jamnagar Petrochemical Complex",
        "latitude": 22.3039,
        "longitude": 70.8022,
        "industry_type": "Refinery & Petrochemicals",
        "operator": "Reliance Petroleum Ltd. (DEMO)",
        "risk_level": "High",
        "address": "Sector 4, Refinery Corridor, Jamnagar, Gujarat, India",
        "is_demo": True
    },
    {
        "name": "Hazira Industrial Port & Manufacturing Hub",
        "latitude": 21.1167,
        "longitude": 72.6500,
        "industry_type": "Steel & Bulk Chemical Processing",
        "operator": "Hazira Industrial Consortium (DEMO)",
        "risk_level": "High",
        "address": "Coastal Industrial Zone, Hazira, Surat, Gujarat, India",
        "is_demo": True
    },
    {
        "name": "Mumbai High Offshore Extraction Platform",
        "latitude": 19.4167,
        "longitude": 71.3333,
        "industry_type": "Offshore Oil & Gas Production",
        "operator": "Oil & Natural Gas Corp (DEMO)",
        "risk_level": "Medium",
        "address": "Arabian Sea Offshore Sector B, 160km West of Mumbai Coast, Maharashtra, India",
        "is_demo": True
    },
    {
        "name": "Korba Super Thermal Power Plant",
        "latitude": 22.3595,
        "longitude": 82.7501,
        "industry_type": "Thermal Power Generation",
        "operator": "National Thermal Power Corp (DEMO)",
        "risk_level": "Medium",
        "address": "Power Plant Road, Korba District, Chhattisgarh, India",
        "is_demo": True
    },
    {
        "name": "Dahej Chemical SEZ Buffer Area",
        "latitude": 21.7052,
        "longitude": 72.5873,
        "industry_type": "Chemical Manufacturing & Agro-Chemicals",
        "operator": "Dahej Petrochemical SEZ Authority (DEMO)",
        "risk_level": "Low",
        "address": "Zone 2 Agro Buffer, Dahej Coastal SEZ, Gujarat, India",
        "is_demo": True
    },
    {
        "name": "Visakhapatnam Coastal Steel Complex",
        "latitude": 17.6868,
        "longitude": 83.2185,
        "industry_type": "Primary Steel & Heavy Metallurgy",
        "operator": "Rashtriya Ispat Nigam Ltd. (DEMO)",
        "risk_level": "High",
        "address": "Blast Furnace Sector, Steel Plant Road, Visakhapatnam, Andhra Pradesh, India",
        "is_demo": True
    },
    {
        "name": "Manali Petrochemical Industrial Park",
        "latitude": 13.1670,
        "longitude": 80.2600,
        "industry_type": "Specialty Petrochemicals & Chlor-Alkali",
        "operator": "Chennai Industrial Development Board (DEMO)",
        "risk_level": "High",
        "address": "Express Highway Corridor, Manali, Chennai, Tamil Nadu, India",
        "is_demo": True
    },
    {
        "name": "Mundra Ultra Mega Port & Coal Terminal",
        "latitude": 22.8397,
        "longitude": 69.7042,
        "industry_type": "Port Logistics & Bulk Coal Handling",
        "operator": "Mundra Port Logistics (DEMO)",
        "risk_level": "Medium",
        "address": "South Port Perimeter, Gulf of Kutch, Mundra, Gujarat, India",
        "is_demo": True
    }
]

DEMO_OPERATOR_TEAMS = [
    {
        "name": "Jamnagar Petrochemical Hazmat & Fire Battalion",
        "team_type": "Industrial Fire Brigade & Hazmat",
        "facility_name": "Jamnagar Petrochemical Complex",
        "latitude": 22.3120,
        "longitude": 70.7950,
        "contact_person": "Chief Fire Officer Rajesh Mehta",
        "contact_phone": "+91-288-2234-911",
        "contact_email": "emergency.jamnagar@reliance-petro.demo",
        "radio_frequency": "VHF 156.800 MHz (Tactical Ch 16)",
        "coverage_radius_km": 65.0,
        "status": "available",
        "is_demo": True
    },
    {
        "name": "Hazira Coastal Chemical Emergency Unit",
        "team_type": "Hazmat & Chemical Response Unit",
        "facility_name": "Hazira Industrial Port & Manufacturing Hub",
        "latitude": 21.1250,
        "longitude": 72.6410,
        "contact_person": "Commander Suresh Patel",
        "contact_phone": "+91-261-2870-999",
        "contact_email": "hazmat.hazira@industrial-corridor.demo",
        "radio_frequency": "UHF 453.225 MHz (Hazmat Net 2)",
        "coverage_radius_km": 55.0,
        "status": "available",
        "is_demo": True
    },
    {
        "name": "Mumbai Offshore Maritime Fire & Rescue Vessel",
        "team_type": "Offshore Marine Emergency Vessel",
        "facility_name": "Mumbai High Offshore Extraction Platform",
        "latitude": 19.4250,
        "longitude": 71.3200,
        "contact_person": "Captain Vikramaditya Roy",
        "contact_phone": "+91-22-2655-0199",
        "contact_email": "marine.rescue@ongc-offshore.demo",
        "radio_frequency": "Marine VHF Ch 16 / MF 2182 kHz",
        "coverage_radius_km": 80.0,
        "status": "available",
        "is_demo": True
    },
    {
        "name": "Korba Super Thermal Power Plant Emergency Brigade",
        "team_type": "Heavy Industrial Fire Unit",
        "facility_name": "Korba Super Thermal Power Plant",
        "latitude": 22.3650,
        "longitude": 82.7420,
        "contact_person": "Station Officer A. K. Verma",
        "contact_phone": "+91-7759-241-101",
        "contact_email": "fire.control@ntpc-korba.demo",
        "radio_frequency": "VHF 162.400 MHz (Plant Safety)",
        "coverage_radius_km": 50.0,
        "status": "available",
        "is_demo": True
    },
    {
        "name": "Dahej Petrochemical Rapid Response Squadron",
        "team_type": "Petrochemical Hazmat Squadron",
        "facility_name": "Dahej Chemical SEZ Buffer Area",
        "latitude": 21.7120,
        "longitude": 72.5790,
        "contact_person": "Lead Officer Deepali Joshi",
        "contact_phone": "+91-2641-256-112",
        "contact_email": "rapidresponse@dahej-sez.demo",
        "radio_frequency": "UHF 462.562 MHz (SEZ Emergency)",
        "coverage_radius_km": 45.0,
        "status": "available",
        "is_demo": True
    }
]

DEMO_EVENTS = [
    {
        "event_id": "DEMO-EVT-001",
        "facility_name": "Jamnagar Petrochemical Complex",
        "latitude": 22.3039,
        "longitude": 70.8022,
        "hours_ago": 2,
        "event_type": "Critical Industrial Fire",
        "thermal_intensity": "1250 MW",
        "persistence": "Continuous (36+ hours active)",
        "confidence": 0.98,
        "risk_score": 96.5,
        "risk_priority": "CRITICAL",
        "land_cover": "Heavy Industrial Zone",
        "data_source": "NASA FIRMS VIIRS (DEMO)",
        "status": "active",
        "ai_classification": {
            "classification": "Critical Industrial Fire",
            "confidence": 0.98,
            "explanation": "Catastrophic heat anomaly detected with intense radiant energy (1250 MW) co-located with refinery hydrocracker unit. Severe risk of secondary tank boilover.",
            "model_name": "ThermalWatch-AI-v2.3"
        }
    },
    {
        "event_id": "DEMO-EVT-002",
        "facility_name": "Hazira Industrial Port & Manufacturing Hub",
        "latitude": 21.1167,
        "longitude": 72.6500,
        "hours_ago": 5,
        "event_type": "High-Risk Thermal Event",
        "thermal_intensity": "680 MW",
        "persistence": "Recurrent (Last 8 hours)",
        "confidence": 0.92,
        "risk_score": 84.0,
        "risk_priority": "HIGH",
        "land_cover": "Industrial Storage & Steel Mill",
        "data_source": "NASA FIRMS MODIS (DEMO)",
        "status": "active",
        "ai_classification": {
            "classification": "High-Risk Thermal Event",
            "confidence": 0.92,
            "explanation": "Sudden thermal flare adjacent to raw chemical storage silos. Exceeds historical operational baseline by 280%. Containment alert active.",
            "model_name": "ThermalWatch-AI-v2.3"
        }
    },
    {
        "event_id": "DEMO-EVT-003",
        "facility_name": "Mumbai High Offshore Extraction Platform",
        "latitude": 19.4167,
        "longitude": 71.3333,
        "hours_ago": 14,
        "event_type": "Gas Flare",
        "thermal_intensity": "320 MW",
        "persistence": "Semi-continuous (Scheduled flaring)",
        "confidence": 0.95,
        "risk_score": 52.0,
        "risk_priority": "MEDIUM",
        "land_cover": "Offshore Marine Platform",
        "data_source": "NASA FIRMS VIIRS (DEMO)",
        "status": "monitoring",
        "ai_classification": {
            "classification": "Gas Flare",
            "confidence": 0.96,
            "explanation": "High-temperature intermittent gas burn off from pressure relief ventilation stack. Verified operational flaring activity.",
            "model_name": "ThermalWatch-AI-v2.3"
        }
    },
    {
        "event_id": "DEMO-EVT-004",
        "facility_name": "Korba Super Thermal Power Plant",
        "latitude": 22.3595,
        "longitude": 82.7501,
        "hours_ago": 72,
        "event_type": "Persistent Thermal Source",
        "thermal_intensity": "410 MW",
        "persistence": "Continuous (Historical 90+ days)",
        "confidence": 0.89,
        "risk_score": 41.5,
        "risk_priority": "MEDIUM",
        "land_cover": "Power Generation & Slag Yard",
        "data_source": "NASA FIRMS SLSTR (DEMO)",
        "status": "monitoring",
        "ai_classification": {
            "classification": "Persistent Thermal Source",
            "confidence": 0.94,
            "explanation": "Baseline thermal signature from coal-fired boiler flue exhaust and slag cooling bed. No anomalous perimeter spread detected.",
            "model_name": "ThermalWatch-AI-v2.3"
        }
    },
    {
        "event_id": "DEMO-EVT-005",
        "facility_name": "Dahej Chemical SEZ Buffer Area",
        "latitude": 21.7052,
        "longitude": 72.5873,
        "hours_ago": 24,
        "event_type": "Low-Risk Thermal Activity",
        "thermal_intensity": "45 MW",
        "persistence": "Transient (< 2 hours)",
        "confidence": 0.74,
        "risk_score": 18.0,
        "risk_priority": "LOW",
        "land_cover": "Scrubland / Industrial Buffer",
        "data_source": "NASA FIRMS VIIRS (DEMO)",
        "status": "contained",
        "ai_classification": {
            "classification": "Low-Risk Thermal Activity",
            "confidence": 0.88,
            "explanation": "Low radiant power detected outside active processing perimeter. Matches controlled vegetation clearing along utility easement.",
            "model_name": "ThermalWatch-AI-v2.3"
        }
    }
]


def seed_demo_facilities(db: Session, force: bool = False) -> dict:
    """
    Seeds clearly labelled demo industrial facilities across key industrial zones.
    """
    facilities_created = 0
    facility_map = {}
    for fac_data in DEMO_FACILITIES:
        facility = db.query(IndustrialFacility).filter(IndustrialFacility.name == fac_data["name"]).first()
        if facility:
            if force:
                facility.latitude = fac_data["latitude"]
                facility.longitude = fac_data["longitude"]
                facility.industry_type = fac_data["industry_type"]
                facility.operator = fac_data["operator"]
                facility.risk_level = fac_data["risk_level"]
                facility.address = fac_data["address"]
                facility.is_demo = True
                db.flush()
            facility_map[facility.name] = facility
        else:
            facility = IndustrialFacility(**fac_data)
            db.add(facility)
            db.flush()
            facilities_created += 1
            facility_map[facility.name] = facility

    db.commit()
    total_demo = db.query(IndustrialFacility).filter(IndustrialFacility.is_demo == True).count()
    logger.info(f"Seeded {facilities_created} demo industrial facilities. Total demo facilities: {total_demo}")
    return {
        "status": "success",
        "facilities_created": facilities_created,
        "total_demo_facilities": total_demo,
        "facility_map": facility_map,
        "message": f"Successfully seeded {facilities_created} new demo industrial facilities."
    }


def seed_demo_operator_teams(db: Session, facility_map: dict = None, force: bool = False) -> dict:
    """
    Seeds industrial emergency response and operator teams positioned near major industrial facilities.
    """
    if facility_map is None:
        fac_res = seed_demo_facilities(db=db, force=False)
        facility_map = fac_res["facility_map"]

    teams_created = 0
    for team_data in DEMO_OPERATOR_TEAMS:
        existing = db.query(EmergencyResponseTeam).filter(EmergencyResponseTeam.name == team_data["name"]).first()
        if existing:
            if force:
                fac = facility_map.get(team_data["facility_name"])
                existing.team_type = team_data["team_type"]
                existing.facility_id = fac.id if fac else None
                existing.latitude = team_data["latitude"]
                existing.longitude = team_data["longitude"]
                existing.contact_person = team_data["contact_person"]
                existing.contact_phone = team_data["contact_phone"]
                existing.contact_email = team_data["contact_email"]
                existing.radio_frequency = team_data["radio_frequency"]
                existing.coverage_radius_km = team_data["coverage_radius_km"]
                existing.status = team_data["status"]
                existing.is_demo = True
                db.flush()
            continue

        fac = facility_map.get(team_data["facility_name"])
        team = EmergencyResponseTeam(
            name=team_data["name"],
            team_type=team_data["team_type"],
            facility_id=fac.id if fac else None,
            latitude=team_data["latitude"],
            longitude=team_data["longitude"],
            contact_person=team_data["contact_person"],
            contact_phone=team_data["contact_phone"],
            contact_email=team_data["contact_email"],
            radio_frequency=team_data["radio_frequency"],
            coverage_radius_km=team_data["coverage_radius_km"],
            status=team_data["status"],
            is_demo=True
        )
        db.add(team)
        teams_created += 1

    db.commit()
    total_teams = db.query(EmergencyResponseTeam).filter(EmergencyResponseTeam.is_demo == True).count()
    logger.info(f"Seeded {teams_created} demo operator teams. Total demo teams: {total_teams}")
    return {
        "status": "success",
        "teams_created": teams_created,
        "total_demo_teams": total_teams,
        "message": f"Successfully seeded {teams_created} industrial emergency response teams."
    }


def seed_default_users(db: Session, force: bool = False) -> None:
    """
    Seeds default administrator and operator accounts for testing and production bootstrap.
    """
    default_users = [
        {
            "full_name": "System Administrator",
            "email": "admin@thermosafe.ai",
            "password": "AdminPassword123!",
            "role": UserRole.ADMIN
        },
        {
            "full_name": "Field Operations Controller",
            "email": "operator@thermosafe.ai",
            "password": "OperatorPassword123!",
            "role": UserRole.OPERATOR
        }
    ]

    for u_data in default_users:
        existing = db.query(User).filter(User.email.ilike(u_data["email"])).first()
        if not existing:
            user = User(
                full_name=u_data["full_name"],
                email=u_data["email"],
                hashed_password=hash_password(u_data["password"]),
                role=u_data["role"],
                is_active=True
            )
            db.add(user)
    db.commit()


def seed_demo_thermal_events(db: Session, force: bool = False) -> dict:
    """
    Seeds realistic industrial demo facilities, operator teams, thermal events, and AI classifications.
    If force is False, only seeds when no demo thermal events currently exist.
    """
    # 0. Seed default accounts
    seed_default_users(db=db, force=force)

    # 1. Seed Facilities first
    fac_res = seed_demo_facilities(db=db, force=force)
    facility_map = fac_res["facility_map"]

    # 2. Seed Operator Teams
    seed_demo_operator_teams(db=db, facility_map=facility_map, force=force)

    existing_count = db.query(ThermalEvent).filter(ThermalEvent.is_demo == True).count()
    if existing_count > 0 and not force:
        logger.info(f"Database already contains {existing_count} demo thermal events. Skipping event seed.")
        return {
            "status": "already_seeded",
            "events_count": existing_count,
            "facilities_count": len(facility_map),
            "message": "Demo events and facilities already populated."
        }

    now = datetime.now(timezone.utc)
    events_created = 0
    for evt_data in DEMO_EVENTS:
        existing = db.query(ThermalEvent).filter(ThermalEvent.event_id == evt_data["event_id"]).first()
        if existing:
            if force:
                db.delete(existing)
                db.flush()
            else:
                continue

        facility = facility_map.get(evt_data["facility_name"])
        detected_time = now - timedelta(hours=evt_data["hours_ago"])

        thermal_event = ThermalEvent(
            event_id=evt_data["event_id"],
            latitude=evt_data["latitude"],
            longitude=evt_data["longitude"],
            detected_at=detected_time,
            event_type=evt_data["event_type"],
            thermal_intensity=evt_data["thermal_intensity"],
            persistence=evt_data["persistence"],
            confidence=evt_data["confidence"],
            risk_score=evt_data["risk_score"],
            risk_priority=evt_data["risk_priority"],
            facility_id=facility.id if facility else None,
            land_cover=evt_data["land_cover"],
            data_source=evt_data["data_source"],
            status=evt_data["status"],
            is_demo=True
        )
        db.add(thermal_event)
        db.flush()

        # Add AI Classification
        ai_data = evt_data["ai_classification"]
        ai_record = AIClassification(
            thermal_event_id=thermal_event.id,
            classification=ai_data["classification"],
            confidence=ai_data["confidence"],
            explanation=ai_data["explanation"],
            model_name=ai_data["model_name"]
        )
        db.add(ai_record)
        events_created += 1

    db.commit()
    logger.info(f"Successfully seeded {events_created} demo thermal events.")
    return {
        "status": "success",
        "events_created": events_created,
        "facilities_created": fac_res["facilities_created"],
        "total_demo_events": db.query(ThermalEvent).filter(ThermalEvent.is_demo == True).count(),
        "total_demo_facilities": fac_res["total_demo_facilities"],
        "message": f"Successfully seeded {events_created} realistic industrial demo events."
    }
