import logging 
from typing import Optional, List

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from database.crud import CrudCategory, CrudFurniture

from keyboard.button_template import country_of_origin_kb, kitchen_subcategory_inline_kb, furniture_cancel_kb, finish_keyboard, admin_kb
from keyboard.keyboard_builder import make_row_inline_keyboards, make_row_keyboards

from states.states import NewFurnitureStates, RemoveFurnitureStates

from handlers.admin.main_admin import settings_bot


router = Router()



async def cancel_and_return_to_admin(message: types.Message, state: FSMContext):
    await state.clear()

    from keyboard.button_template import admin_kb

    user = message.from_user
    user_name = user.full_name if user else 'Администратор'
    user_id = user.id if user else '—'

    admin_text = (
        '🔧 <b>Панель администратора</b>\n\n'
        f'Здравствуйте, <b>{user_name}</b> (<code>{user_id}</code>)\n\n'
        'Выберите действие из меню ниже:'
    )

    await message.answer(text=admin_text, reply_markup=types.ReplyKeyboardRemove())
    await message.answer(text='Панель администратора:', reply_markup=make_row_inline_keyboards(admin_kb))


async def send_success_summary(
        message: types.Message,
        category: str, 
        kitchen_type: str | None,
        country: str,
        photos_count: int,
        description: str):
    text = (
        '🎉 <b>Мебель успешно добавлена!</b>\n\n'
        f'• Категория: {category}\n'
        f"• Тип кухни: {kitchen_type or 'Не указан'}\n"
        f'• Страна: {country}\n'
        f'• Фотографий: {photos_count}\n\n'
        f'• 📄 <b>Описание:</b>\n{description}'
    )

    await message.answer(text, reply_markup=types.ReplyKeyboardRemove())


async def handle_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])

    photo_id = message.photo[-1].file_id
    photos.append(photo_id)

    await state.update_data(photos=photos)

    if len(photos) >= 10:
        await message.answer(
            '📸 Достигнут лимит (10 photo).\n'
            'Нажмите «Завершить добавление».'
        )
    else:
        await message.answer(
            f'✅ Фото добавлено ({len(photos)}/10)\n'
            'Отправьте ещё или нажмите «Завершить добавление».'
        )


async def save_photos_and_notify(
        message: types.Message,
        crud: CrudFurniture,
        furniture_id: int,
        photos: list[str]):
    
    success = await crud.add_photos_to_furniture(furniture_id, photos)

    if success:
        await message.answer(
            '✅ <b>Фотографии добавлены</b>\n'
            'Все фотографии успешно сохранены.'
        )
    else:
        await message.answer(
            '⚠️ <b>Предупреждение</b>\n\n'
            'Мебель создана, но фото не были добавлены.'
        )


async def finish_furniture_creation(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])

    if not photos:
        await message.answer(
            '⚠️ <b>Нет фотографий</b>\n\n'
            'Пожалуйста, отправьте хотя бы одну фотографию мебели.'
        )
        return 

    description = data.get('description_new_furniture', 'Нет описания')
    category = data.get('category_name', 'Без категории')
    country = data.get('country_name', 'Не указана')
    kitchen_type = data.get('kitchen_type')

    if kitchen_type and 'кухн' in category.lower():
        description = f'[{kitchen_type}] {description}'

    crud = CrudFurniture()
    furniture = await crud.create_furniture(
        description=description,
        category=category,
        country=country,
        kitchen_type=kitchen_type
    )    

    if not furniture:
        await message.answer(
            '❌ <b>Ошибка сохранения</b>\n\n'
            'Произошла ошибка при сохранении мебели.'
        )
        return 

    await save_photos_and_notify(
        message=message,
        crud=crud,
        furniture_id=furniture.id,
        photos=photos
    )

    await send_success_summary(
        message=message,
        category=category,
        kitchen_type=kitchen_type,
        country=country,
        photos_count=len(photos),
        description=description
    )

    await state.clear()

    
    admin_text = (
        '🔧 <b>Панель Администратора</b>\n\n'
        'Действие успешно завершено. Вы вернулись в главное меню.\n'
        'Выберите следующую задачу ниже:'
    )
    await message.answer(text=admin_text, reply_markup=make_row_inline_keyboards(admin_kb))


@router.callback_query(F.data == 'new_furniture')
async def new_furniture_function(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.answer()

    text = (
        '🛋 <b>Добавление новой мебели</b>\n\n'
        '📝 <b>Шаг 1 из 5:</b> Описание мебели\n\n'
        'Пожалуйста, введите <b>подробное описание</b> мебели:\n'
        '• Материалы и отделка\n'
        '• Габариты (Д×Ш×В)\n'
        '• Особенности конструкции\n'
        '• Стиль и назначение\n\n'
        '<i>Пример:</i>\n'
        "<code>Элегантный кожаный диван \"Комфорт\" с мягким наполнением, \n"
        'размеры 200×90×85 см, каркас из березовой фанеры, \n'
        'подушки сиденья на пружинном блоке, цвет черный.</code>'
    )

    if callback_query.message:
        await callback_query.message.answer(text, reply_markup=make_row_inline_keyboards(furniture_cancel_kb))
    await state.set_state(NewFurnitureStates.description)


@router.message(NewFurnitureStates.description)
async def get_description_new_furniture(message: types.Message, state: FSMContext):
    description_furniture = message.text.strip() if message.text else ''
    if not description_furniture:
        await message.answer(
            '⚠️ <b>Ошибка ввода</b>\n\n'
            'Описание не может быть пустым. Пожалуйста, введите описание мебели.'
        )
        return 

    await state.update_data(description_new_furniture=description_furniture)

    crud = CrudCategory()
    categories = await crud.get_all_categories()

    if not categories:
        await message.answer(
            '📬 <b>Категории отсутствуют</b>\n\n'
            'В базе пока нет категорий мебели.\n'
            'Сначала создайте хотя бы одну категорию в разделе админки.'
        )
        await state.clear()
        return 

    text = (
        '✅ <b>Описание сохранено</b>\n\n'
        '📋 <b>Шаг 2 из 5:</b> Выбор категории\n\n'
        'Теперь выберите <b>категорию</b> для этой мебели из списка ниже 👇 '
    )

    category_buttons = [cat.name for cat in categories]
    await message.answer(text, reply_markup=make_row_keyboards(category_buttons))
    await state.set_state(NewFurnitureStates.category)


@router.message(NewFurnitureStates.category)
async def get_category(message: types.Message, state: FSMContext):
    category_name = message.text.strip() if message.text else ''

    if not category_name:
        await message.answer(
            '⚠️ <b>Ошибка выбора</b>\n\n'
            'Пожалуйста, выберите категорию из предложенного списка.'
        )
        return
    await state.update_data(category_name=category_name)

    category_lower = category_name.lower()

    if 'кухн' in category_lower or 'кухон' in category_lower:
        text = (
            f'📦 <b>Категория выбрана:</b> {category_name}\n\n'
            f'📋 <b>Шаг 3 из 4:</b> Тип кухни\n\n'
            f'Теперь выберите <b>тип кухни</b> из списка ниже:'
        )
        await message.answer(text, reply_markup=make_row_inline_keyboards(kitchen_subcategory_inline_kb))
        await state.set_state(NewFurnitureStates.kitchen_type)

    elif any(word in category_lower for word in ['спальн', 'мягк', 'стол', 'стул']):
        text = (
            f'📦 <b>Категория выбрана:</b> {category_name}\n\n'
            f'📋 <b>Шаг 3 из 4:</b> Страна производства\n\n'
            f'Теперь укажите <b>страну происхождения</b> мебели 🌍\n'
            f'Выберите из списка ниже:'
        )
        await message.answer(text, reply_markup=make_row_inline_keyboards(country_of_origin_kb))
        await state.set_state(NewFurnitureStates.country)

    else:
        await state.update_data(country_name='Не указана')
        await state.update_data(kitchen_type=None)

        text = (
            f'📦 <b>Категория выбрана:</b> {category_name}\n\n'
            f'📋 <b>Шаг 3 из 3:</b> Фотографии\n\n'
            f'Для этой категории выбор подкатегорий не требуется.\n'
            f'Теперь отправьте <b>фотографии</b> мебели 📸 (не более 10).\n\n'
            f'Когда закончите, нажмите кнопку <b>«Завершить добавление»</b> ниже.'
        )
        await message.answer(text, reply_markup=make_row_keyboards(finish_keyboard))
        await state.set_state(NewFurnitureStates.photos)
        await state.update_data(photos=[])


@router.callback_query(NewFurnitureStates.kitchen_type)
async def get_kitchen_type(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    
    kitchen_callback = callback_query.data

    if kitchen_callback == 'straight_kitchen':
        kitchen_type = '📏 Прямая'
    elif kitchen_callback == 'corner_kitchen':
        kitchen_type = '📐 Угловая'
    else:
        kitchen_type = kitchen_callback

    await state.update_data(kitchen_type=kitchen_type)
    await state.update_data(country_name=None)

    text = (
        f'🍳 <b>Тип кухни выбран:</b> {kitchen_type}\n\n'
        f'📋 <b>Шаг 4 из 4:</b> Фотографии\n\n'
        f'Теперь отправьте <b>фотографии</b> мебели 📸 (не более 10).\n\n'
        f'Когда закончите, нажмите кнопку <b>«Завершить добавление»</b> ниже.'
    )

    await callback_query.message.answer(text, reply_markup=make_row_keyboards(finish_keyboard))
    await state.set_state(NewFurnitureStates.photos)
    await state.update_data(photos=[])



@router.callback_query(NewFurnitureStates.country)
async def get_country(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    country_callback = callback_query.data

    if country_callback == 'russian_origin':
        country_name = '🇷🇺 Россия'
    elif country_callback == 'turkey_origin':
        country_name = '🇹🇷 Турция'
    else:
        country_name = country_callback

    await state.update_data(country_name=country_name)
    await state.update_data(kitchen_type=None)

    text = (
        f'🌍 <b>Страна выбрана:</b> {country_name}\n\n'
        f'📋 <b>Шаг 4 из 4:</b> Фотографии\n\n'
        f'Теперь отправьте <b>фотографии</b> мебели 📸 (не более 10).\n\n'
        f'Когда закончите, нажмите кнопку <b>«Завершить добавление»</b> ниже.'
    )
    await callback_query.message.answer(text, reply_markup=make_row_keyboards(finish_keyboard))
    await state.set_state(NewFurnitureStates.photos)
    await state.update_data(photos=[])



@router.message(NewFurnitureStates.photos)
async def get_photos(message: types.Message, state: FSMContext):
    if message.text == '✅ Завершить добавление':
        await finish_furniture_creation(message, state)
        return

    if message.text == '❌ Отменить':
        await cancel_and_return_to_admin(message, state)
        return

    if message.photo:
        await handle_photo(message, state)
        return

    await message.answer(
        '⚠️ <b>Неподдерживаемый формат</b>\n\n'
        'Отправьте фотографию или используйте кнопки ниже.'
    )


@router.callback_query(F.data == 'remove_furniture')
async def start_remove_furniture(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    
    crud = CrudFurniture()
    items = await crud.get_all_furniture()
    
    if not items:
        await callback_query.message.answer('🗭 В базе данных пока нет ни одного товара для удаления.')
        return

    text = '🗑️ <b>Удаление мебели</b>\n\nВыберите модель из списка ниже для полного удаления из каталога:'
    
    buttons = [(f'🆔 #{item.id} | {item.description[:20]}...', f'del_furn_{item.id}') for item in items]
    buttons.append(('❌ Отмена', 'back_to_admin'))
    
    await callback_query.message.edit_text(text=text, reply_markup=make_row_inline_keyboards(buttons))
    await state.set_state(RemoveFurnitureStates.choose_furniture)


@router.callback_query(RemoveFurnitureStates.choose_furniture)
async def process_delete_furniture(callback_query: types.CallbackQuery, state: FSMContext):
    click_data = callback_query.data if callback_query.data else ''

    if 'cancel' in click_data or 'back' in click_data:
        await callback_query.answer('Операция отменена ✖', show_alert=True)
        await state.clear()
        await settings_bot(callback_query)
        return

    if click_data.startswith('del_furn_'):
        furniture_id = int(click_data.replace('del_furn_', ''))
        
        crud = CrudFurniture()
        success = await crud.delete_furniture_by_id(furniture_id)
        
        if success:
            await callback_query.answer('🎉 Товар успешно удален!', show_alert=True)
        else:
            await callback_query.answer('❌ Ошибка при удалении товара.', show_alert=True)
            
        await state.clear()
        await settings_bot(callback_query)
