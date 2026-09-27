import logging 
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from keyboard.button_template import admin_kb
from keyboard.keyboard_builder import make_row_inline_keyboards

from database.crud import CrudCategory


router = Router()
db_category = CrudCategory()


@router.callback_query(F.data == 'settings_bot')
async def settings_bot(callback_query: types.CallbackQuery):

    admin_text = (
        '🔧 <b>Панель Администратора</b>\n\n'
        f'Здравствуйте, <b>{callback_query.from_user.full_name}</b> '
        f'(<code>{callback_query.from_user.id}</code>)\n\n'
        'Выберите действие из меню ниже — кнопки аккуратно сгруппированы по задачам:\n\n'
    )

    try:
        await callback_query.message.edit_text(text=admin_text, reply_markup=make_row_inline_keyboards(admin_kb))
    except Exception as e:
        logging.warning(f'Не удалось отредактировать сообщение: {e}')    
        await callback_query.message.answer(text=admin_text, reply_markup=make_row_inline_keyboards(admin_kb))


@router.callback_query(F.data == 'list_categories_furniture')
async def show_all_categories_admin(callback_query: types.CallbackQuery):
    await callback_query.answer()
    
    categories = await db_category.get_all_categories()

    if not categories:
        text = (
            '📁 <b>Список категорий мебели</b>\n\n'
            'В базе данных пока <b>нет ни одной категории</b>.'
        )
    else:
        text = '📁 <b>Список существующих категорий:</b>\n\n'
        for idx, cat in enumerate(categories, start=1):
            text += f'{idx}. <b>{cat.name}</b>\n'
            if cat.description:
                text += f'📝 <i>{cat.description}</i>\n'
            text += '────────────────────\n'

    keyboard = [('⬅️ Назад в админку', 'settings_bot')]
    
    await callback_query.message.edit_text(text=text, reply_markup=make_row_inline_keyboards(keyboard))


@router.callback_query(F.data == 'cancel_category')
async def cancel_category_operation(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer('Операция отменена ✖', show_alert=True)
    await state.clear()
    await settings_bot(callback_query)


@router.callback_query(F.data == 'cancel_furniture')
async def cancel_furniture_operation(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer('Операция отменена ✖', show_alert=True)
    await state.clear()
    await settings_bot(callback_query)






             