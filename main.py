import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import DeleteWebhook


from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(current_dir, '.env'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)


from settings.config import ConfigBot
from handlers.admin import router as admin_main_router
from handlers.client import router as client_router

from database.engine import async_engine
from database.models import Base


async def main():
    if not ConfigBot.TOKEN:
        logging.error('❌ Ошибка: ТОКЕН БОТА НЕ НАЙДЕН! Проверьте файл .env в корне проекта.')
        return

    logging.info('🗄 Проверка и автоматическое создание таблиц базы данных...')
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logging.info('🚀 Инициализация бота...')
    bot = Bot(token=ConfigBot.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    dp.include_routers(admin_main_router, client_router)

    logging.info('🧹 Удаление старых вебхуков и зависших обновлений...')
    await bot(DeleteWebhook(drop_pending_updates=True))

    logging.info('🤖 Бот успешно запущен и слушает команды!')
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except TelegramBadRequest as e:
        logging.error(f'Telegram API error: {e}')
    except KeyboardInterrupt:
        logging.info('Бот остановлен пользователем')
    except Exception as e:
        logging.critical(f'Критическая ошибка при работе бота: {e}', exc_info=True)
