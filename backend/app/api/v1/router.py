from fastapi import APIRouter
from app.api.v1.auth_routes import router as auth_router
from app.api.v1.company_routes import router as company_router
from app.api.v1.kpi_routes import router as kpi_router
from app.api.v1.data_routes import router as data_router
from app.api.v1.report_routes import router as report_router
from app.api.v1.alert_routes import router as alert_router
from app.api.v1.detection_routes import router as detection_router
from app.api.v1.prediction_routes import router as prediction_router
from app.api.v1.recommendation_routes import router as recommendation_router
from app.api.v1.noah_routes import router as noah_router
from app.api.v1.inventory_routes import router as inventory_router

api_router = APIRouter()
from app.api.v1.dataset_library_routes import router as dataset_library_router
from app.api.v1.stakeholder_routes import router as stakeholder_router
api_router.include_router(dataset_library_router)
api_router.include_router(stakeholder_router)
from app.api.v1.source_routes import router as source_router
api_router.include_router(source_router)
from app.api.v1.analysis_routes import router as analysis_router
api_router.include_router(analysis_router)

api_router.include_router(auth_router)
api_router.include_router(company_router)
api_router.include_router(kpi_router)
api_router.include_router(data_router)
api_router.include_router(report_router)
api_router.include_router(alert_router)
api_router.include_router(detection_router)
api_router.include_router(prediction_router)
api_router.include_router(recommendation_router)
api_router.include_router(noah_router)
api_router.include_router(inventory_router)

from app.api.v1 import internal_cron_routes
api_router.include_router(internal_cron_routes.router)
