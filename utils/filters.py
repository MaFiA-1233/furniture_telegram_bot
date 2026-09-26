from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from database.crud import CrudUser

class IsAdminFilter(Filter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        tg_id = event.from_user.id
        
        db_user = CrudUser()
        user = await db_user.get_user_by_telegram_id(tg_id)
        
        if user and hasattr(user, 'is_admin'):
            return bool(user.is_admin)
            
        return False
