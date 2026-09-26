import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from database.crud import CrudCategory

from keyboard.button_template import build_cancel_kb, admin_kb
from keyboard.keyboard_builder import make_row_inline_keyboards

from states.states import NewCategoryStates    

from handlers.admin.main_admin import settings_bot

router = Router()


# Вспомогательная функция для красивого возврата админа в меню
async def return_to_admin_menu(message: types.Message):

    user = message.from_user
    user_name = user.full_name if user else 'Администратор'
    user_id = user.id if user else '—'

    admin_text = (
        '🔧 <b>Панель Администратора</b>\n\n'
        f'Здравствуйте, <b>{user_name}</b> (<code>{user_id}</code>)\n\n'
        'Выберите действие из меню ниже — кнопки аккуратно сгруппированы по задачам:\n\n'
    )
    await message.answer(text=admin_text, reply_markup=make_row_inline_keyboards(admin_kb))


@router.callback_query(F.data == 'new_category_furniture')
async def new_category_furniture_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.clear()

    prompt = (
        '🆕 <b>Создание новой категории мебели</b>\n\n'
        'Введите название категории.\n\n'
        '🔹 Совет: добавьте эмодзи в начале названия — это делает меню заметнее.\n\n'
        'Примеры:\n'
        '<code>🛏️ Спальная мебель</code>\n'
        '<code>🍽️ Кухонная мебель</code>\n'
        '<code>🛋️ Мягкая мебель</code>\n'
        '<code>🪑 Столы и стулья</code>\n'
        '<code>🗄️ Тумбы и комоды</code>\n'
        '<code>🛌 Кровати</code>\n'
        '<code>🛏️ Матрасы</code>\n'
        '<code>🚪 Шкафы</code>\n'
        'Отправьте название или нажмите «Отменить».'
    )

    await callback_query.message.answer(
        text=prompt,
        reply_markup=make_row_inline_keyboards(build_cancel_kb),
    )
    await state.set_state(NewCategoryStates.name_category)


@router.message(NewCategoryStates.name_category)
async def name_category_furniture(message: types.Message, state: FSMContext):
    name_category = message.text.strip() if message.text else ''

    if not name_category:
        await message.answer('⚠️ Название не может быть пустым. Пожалуйста, введите название категории.')
        return 

    crud = CrudCategory()
    exists = await crud.check_category_by_name(name_category)
    if exists:
        await message.answer('⚠️ Категория с таким именем уже существует в базе!')
        return 

    await state.update_data(name_category=name_category)

    promt = (
        f'✅ Название сохранено: <b>{name_category}</b>\n\n'
        'Теперь введите <b>краткое описание</b> для категории – одно–две фразы.\n'
        'Описание поможет покупателям быстрее понять, что внутри категории.\n\n'
        'Если хотите отменить – нажмите «Отменить».'
    )

    await message.answer(text=promt, reply_markup=make_row_inline_keyboards(build_cancel_kb))
    await state.set_state(NewCategoryStates.description_category)


@router.message(NewCategoryStates.description_category)
async def description_category_furniture(message: types.Message, state: FSMContext):
    description_category = message.text.strip() if message.text else ''

    if not description_category:
        await message.answer('⚠️ Описание не может быть пустым. Пожалуйста, введите описание категории.')
        return

    await state.update_data(description_category=description_category)

    data = await state.get_data()
    name = data.get('name_category', '<без названия>')
    description = description_category

    preview = (
        '🎯 <b>Предпросмотр новой категории</b>\n\n'
        f'{name}\n'
        f'<i>{description}</i>\n\n'
        'Проверьте, всё ли верно. When будете готовы — нажмите «Сохранить», '
        'или используйте «Отменить», чтобы прервать создание.'
    ) 

    keyboard_for_preview = list(build_cancel_kb) + [('✅ Сохранить', 'save_category')]
    await message.answer(text=preview, reply_markup=make_row_inline_keyboards(keyboard_for_preview))


@router.callback_query(F.data == 'save_category')
async def save_category(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    data = await state.get_data()
    name_category = data.get('name_category')
    description_category = data.get('description_category')

    if not name_category or not description_category:
        await callback_query.message.answer('❗ Данные неполные — начните заново.')
        await state.clear()
        return 

    crud = CrudCategory()
    add_category = await crud.create_category(name=name_category, description=description_category)

    if add_category:
        await callback_query.answer(text='🎉 Успешно: категория сохранена в базе', show_alert=True)
        
        await callback_query.message.answer(
            f'🎉 <b>Категория успешно создана!</b>\n\n'
            f'• Название: <b>{name_category}</b>\n'
            f'• Описание: {description_category}'
        )
        
        await return_to_admin_menu(callback_query.message)
    else:
        await callback_query.answer('❌ Произошла ошибка при сохранении. Обратитесь к администратору.')

    await state.clear()        


@router.callback_query(F.data == 'cancel_category')
async def cancel_category_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer('Операция отменена ✖', show_alert=True)
    await state.clear()

    try:
        await callback_query.message.answer('❌ Операция создания категории отменена.')
        await return_to_admin_menu(callback_query.message)
    except Exception as e:
        logging.error(f'Не удалось отправить сообщение после отмены: {e}')


from states.states import RemoveCategoryStates

@router.callback_query(F.data == 'remove_category')
async def start_remove_category(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    
    crud = CrudCategory()
    categories = await crud.get_all_categories()
    
    if not categories:
        await callback_query.message.answer('🗄️ В базе данных пока нет ни одной категории для удаления.')
        return

    text = '🗑️ <b>Удаление категории</b>\n\nВыберите категорию для удаления. <b>Внимание:</b> удаление категории сотрет и всю мебель внутри нее!'
    
    buttons = [(cat.name, f'del_cat_{cat.name}') for cat in categories]
    buttons.append(('❌ Отмена', 'back_to_main'))
    
    await callback_query.message.edit_text(text=text, reply_markup=make_row_inline_keyboards(buttons))
    await state.set_state(RemoveCategoryStates.choose_category)


@router.callback_query(RemoveCategoryStates.choose_category, F.data.startswith('del_cat_'))
async def process_delete_category(callback_query: types.CallbackQuery, state: FSMContext):
    category_name = callback_query.data.replace('del_cat_', '')
    
    crud = CrudCategory()
    success = await crud.delete_category_by_name(category_name)
    
    if success:
        await callback_query.answer(f'🎉 Категория "{category_name}" удалена!', show_alert=True)
    else:
        await callback_query.answer('❌ Ошибка при удалении категории.', show_alert=True)
        
    await state.clear()
    await settings_bot(callback_query)

