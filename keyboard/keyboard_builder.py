from typing import List, Tuple 
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


def make_row_keyboards(items: List[str]) -> ReplyKeyboardMarkup:

    keyboard = [[KeyboardButton(text=item)] for item in items]

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def make_row_inline_keyboards(items: List[Tuple[str, str]]) -> InlineKeyboardMarkup:
    keyboard = []

    for key, value in items:
        button = InlineKeyboardButton(text=key, callback_data=value)
        keyboard.append([button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)        



