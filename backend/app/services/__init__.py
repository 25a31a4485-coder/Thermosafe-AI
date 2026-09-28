"""
Services Package for SIH26162.
"""
from app.services.ai_service import (
    BaseThermalClassifier,
    HeuristicPrototypeClassifier,
    get_classifier,
)
from app.services.risk_service import (
    BaseRiskEngine,
    PrototypeHeuristicRiskEngine,
    get_risk_engine,
)
from app.services.firms_service import (
    FIRMSService,
    get_firms_service,
)
from app.services.notification_service import (
    BaseNotificationChannel,
    DatabaseNotificationChannel,
    NotificationDispatcher,
    get_notification_service,
)
from app.services.analytics_service import (
    AnalyticsService,
    get_analytics_service,
)
from app.services.report_service import (
    ReportService,
    get_report_service,
)
from app.services.operator_routing_service import (
    find_nearest_responsible_team,
    OperatorRoutingService,
)
from app.services.orchestration_service import (
    process_thermal_event,
    build_smart_notification_content,
)

__all__ = [
    "BaseThermalClassifier",
    "HeuristicPrototypeClassifier",
    "get_classifier",
    "BaseRiskEngine",
    "PrototypeHeuristicRiskEngine",
    "get_risk_engine",
    "FIRMSService",
    "get_firms_service",
    "BaseNotificationChannel",
    "DatabaseNotificationChannel",
    "NotificationDispatcher",
    "get_notification_service",
    "AnalyticsService",
    "get_analytics_service",
    "ReportService",
    "get_report_service",
    "find_nearest_responsible_team",
    "OperatorRoutingService",
    "process_thermal_event",
    "build_smart_notification_content",
]
