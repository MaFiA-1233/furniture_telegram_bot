from aiogram import Router

from utils.filters import IsAdminFilter

from .main_admin import router as main_admin_router
from .new_category_handler import router as category_router
from .new_furniture_handler import router as furniture_router

router = Router()

router.message.filter(IsAdminFilter())
router.callback_query.filter(IsAdminFilter())

router.include_routers(main_admin_router, category_router, furniture_router)