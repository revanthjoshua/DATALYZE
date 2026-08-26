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
