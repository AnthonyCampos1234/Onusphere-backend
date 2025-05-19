from .auth import router as auth_router
from .member import router as member_router
from .for_testing import router as testing_router
from .customer import router as customer_router
from .account import router as account_router
from .order import router as order_router
from .item import router as item_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(auth_router, prefix="/auth")
router.include_router(member_router, prefix="/member")
router.include_router(testing_router, prefix="/testing")
router.include_router(customer_router, prefix="/customer")
router.include_router(order_router, prefix="/order")
router.include_router(item_router, prefix="/item")
router.include_router(account_router, prefix="")
