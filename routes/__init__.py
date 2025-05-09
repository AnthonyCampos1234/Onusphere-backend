from .auth import router as auth_router
from .account import router as account_router
from .for_testing import router as testing_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(auth_router, prefix="/auth")
router.include_router(account_router, prefix="/pipeline")
router.include_router(testing_router, prefix="/testing")
