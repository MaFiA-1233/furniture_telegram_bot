from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from keyboard.keyboard_builder import make_row_inline_keyboards, make_row_keyboards
from keyboard.button_template import kitchen_subcategory_inline_kb, country_of_origin_kb, admin_kb
from database.crud import CrudUser, CrudCategory, CrudFurniture
from database.models import Furniture
from utils.filters import IsAdminFilter
from handlers.admin.main_admin import settings_bot

router = Router()

db_user = CrudUser()
db_category = CrudCategory()
db_furniture = CrudFurniture()


@router.message(CommandStart())
async def cmd_start(message: Message, edit_message: bool = False):
    if not edit_message:
        user = await db_user.get_user_by_telegram_id(message.from_user.id)
        if not user:
            user = await db_user.create_user(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                firstname=message.from_user.first_name,
                lastname=message.from_user.last_name
            )
            if user.is_admin:
                await message.answer('👑 <b>Вы автоматически назначены главным администратором бота!</b>')

    categories = await db_category.get_all_categories()
    
    welcome_text = (
        'Добро пожаловать! 🛋️\n\n'
        'Найдите идеальную мебель для любого уголка вашего дома.\n\n'
        'Просто выберите категорию ниже:\n'
        '• Посмотрите каталог моделей.\n'
        '• Получите информацию.\n'
        '• Оформите быстрый заказ.\n\n'
        '🔄 В любой момент можно вернуться «Назад».\n'
        '📞 Для завершения заказа потребуется ваше имя и телефон.\n\n'
        'Выбирайте, с чего начнём? 👇'
    )

    buttons_data = [(cat.name, f'client_cat_{cat.name}') for cat in categories]
    buttons_data.append(('ℹ️ О компании / Контакты', 'about_company'))
    buttons_data.append(('⚙️ Настройки бота', 'settings_bot'))
    reply_markup = make_row_inline_keyboards(buttons_data)

    if edit_message:
        await message.edit_text(text=welcome_text, reply_markup=reply_markup)
    else:
        await message.answer(text=welcome_text, reply_markup=reply_markup)


@router.callback_query(F.data == 'back_to_main')
async def back_to_main_catalog(callback_query: CallbackQuery):
    await callback_query.answer()
    await cmd_start(message=callback_query.message, edit_message=True)


@router.callback_query(F.data.startswith('client_cat_'))
async def show_category_items(callback: CallbackQuery):
    category_name = callback.data.replace('client_cat_', '')
    category_lower = category_name.lower()
    
    if 'кухн' in category_lower or 'кухон' in category_lower:
        await callback.answer()
        
        text = (
            f'🍳 <b>Категория: {category_name}</b>\n\n'
            'Выберите интересующий вас <b>тип кухни</b> ниже 👇'
        )
        
        client_kitchen_buttons = []
        for t, d in kitchen_subcategory_inline_kb:
            if d == 'back_to_main':
                client_kitchen_buttons.append((t, d))
            else:
                client_kitchen_buttons.append((t, f'client_sub:{d}'))
        
        await callback.message.edit_text(text=text, reply_markup=make_row_inline_keyboards(client_kitchen_buttons))
        return

    elif any(word in category_lower for word in ['спальн', 'мягк', 'стол', 'стул']):
        await callback.answer()
        
        text = (
            f'🌍 <b>Категория: {category_name}</b>\n\n'
            'Выберите <b>страну происхождения</b> интересующей вас мебели 👇'
        )
        
        client_country_buttons = []
        for text_btn, data_btn in country_of_origin_kb:
            if data_btn == 'back_to_main':
                client_country_buttons.append((text_btn, data_btn))
            else:
                client_country_buttons.append((text_btn, f'client_country:{data_btn}'))
        
        await callback.message.edit_text(text=text, reply_markup=make_row_inline_keyboards(client_country_buttons))
        return

    items = await db_furniture.get_furniture_by_category(category_name)
    
    if not items:
        await callback.answer('В этой категории пока нет товаров!', show_alert=True)
        return
        
    await callback.answer()
    await callback.message.answer(f'📂 <b>Категория: {category_name}</b>\nПоказываем доступные models:\n────────────────────')
    
    for item in items:
        photos = await db_furniture.get_photos_by_furniture_id(item.id)
        caption = f'🆔 <b>Товар #{item.id}</b>\n\n📝 <b>Описание:</b>\n{item.description}'
        
        if photos:
            await callback.message.answer_photo(photo=photos[0].file_id, caption=caption)
        else:
            await callback.message.answer(caption)


@router.callback_query(F.data.startswith('client_sub:'))
async def show_kitchen_sub_items(callback: CallbackQuery):
    parts = callback.data.split(':', 1)
    kitchen_callback = parts[1]

    await callback.answer()

    if kitchen_callback == 'straight_kitchen':
        target_type = '📏 Прямая'
    elif kitchen_callback == 'corner_kitchen':
        target_type = '📐 Угловая'
    else:
        target_type = kitchen_callback

    async with db_furniture.session() as session:
        stmt = select(Furniture).where(
            Furniture.kitchen_type == target_type
        )
        result = await session.execute(stmt)
        items = list(result.scalars().all())

    if not items:
        await callback.message.answer(f'🍳 <b>{target_type}</b>\n\nВ этой подкатегории пока нет моделей. ⏳')
        return

    await callback.message.answer(f'📂 <b>Подкатегория: {target_type}</b>\nПоказываем модели:\n────────────────────')
    for item in items:
        photos = await db_furniture.get_photos_by_furniture_id(item.id)
        caption = f'🆔 <b>Товар #{item.id}</b>\n🍳 Тип: {item.kitchen_type}\n\n📝 <b>Описание:</b>\n{item.description}'
        if photos:
            await callback.message.answer_photo(photo=photos[0].file_id, caption=caption)
        else:
            await callback.message.answer(caption)


@router.callback_query(F.data.startswith('client_country:'))
async def show_country_sub_items(callback: CallbackQuery):
    parts = callback.data.split(':', 1)
    country_callback = parts[1]

    await callback.answer()

    if country_callback == 'russian_origin':
        target_country = '🇷🇺 Россия'
    elif country_callback == 'turkey_origin':
        target_country = '🇹🇷 Турция'
    else:
        target_country = country_callback

    async with db_furniture.session() as session:
        stmt = select(Furniture).where(
            Furniture.country_origin == target_country
        )
        result = await session.execute(stmt)
        items = list(result.scalars().all())

    if not items:
        await callback.message.answer(f'🌍 <b>{target_country}</b>\n\nВ этой подкатегории пока нет моделей. ⏳')
        return

    await callback.message.answer(f'📂 <b>Подкатегория: {target_country}</b>\nПоказываем модели:\n────────────────────')
    for item in items:
        photos = await db_furniture.get_photos_by_furniture_id(item.id)
        caption = f'🆔 <b>Товар #{item.id}</b>\n🌍 Страна: {item.country_origin}\n\n📝 <b>Описание:</b>\n{item.description}'
        if photos:
            await callback.message.answer_photo(photo=photos[0].file_id, caption=caption)
        else:
            await callback.message.answer(caption)


@router.message(Command('admin'), IsAdminFilter())
async def cmd_admin_panel(message: Message):
    admin_text = (
        '🔧 <b>Панель Администратора</b>\n\n'
        f'Здравствуйте, <b>{message.from_user.full_name}</b> '
        f'(<code>{message.from_user.id}</code>)\n\n'
        'Выберите действие из меню ниже:'
    )
    await message.answer(text=admin_text, reply_markup=make_row_inline_keyboards(admin_kb))


@router.callback_query(F.data == 'settings_bot', IsAdminFilter())
async def open_admin_panel_callback(callback_query: CallbackQuery):
    await callback_query.answer('➡️')
    await settings_bot(callback_query)


@router.callback_query(F.data == 'settings_bot')
async def open_admin_panel_denied(callback_query: CallbackQuery):
    await callback_query.answer(text='⚠️ Доступ запрещен!\n\nВы не являетесь администратором.', show_alert=True)


