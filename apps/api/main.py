from fastapi import FastAPI

from apps.api.routes.a2a import router as a2a_router
from apps.api.routes.health import router as health_router
from apps.api.routes.orders import router as orders_router
from apps.api.routes.risk import router as risk_router
from src.aegis_croo.config import SERVICE_NAME


app = FastAPI(title=SERVICE_NAME)
app.include_router(health_router)
app.include_router(risk_router)
app.include_router(a2a_router)
app.include_router(orders_router)
