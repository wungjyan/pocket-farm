from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.farms import router as farms_router
from app.api.v1.endpoints.plots import router as plots_router
from app.api.v1.endpoints.productions import router as productions_router
from app.api.v1.endpoints.species import router as species_router
from app.api.v1.endpoints.users import router as users_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(farms_router)
router.include_router(plots_router)
router.include_router(productions_router)
router.include_router(species_router)
router.include_router(users_router)
