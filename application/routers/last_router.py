from aiogram import Router
from aiogram.types import Message

import application.keyboard as kb

router = Router(name=__name__)


@router.message()
async def not_identified(message: Message):
    await message.answer(
        text='Извините, я вас не понимаю😔, попробуйте воспользоваться кнопками ниже или командами из <b>Меню</b>',
        reply_markup=kb.menu1, parse_mode='HTML', protect_content=True
    )
