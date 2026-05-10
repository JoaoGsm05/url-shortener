from fastapi import APIRouter

from app.api.v1.endpoints import urls

router = APIRouter()
router.include_router(urls.router, tags=["urls"])
