from aiogram import Router, Bot, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext

from application.states import Newsletter, AdminVerification
from application.database.requests import get_users, get_admin, get_newsletter_password, add_administrator

router = Router(name=__name__)


class AdminProtect(Filter):

    async def __call__(self, message: Message):
        admins_tg_id = await get_admin()
        return message.from_user.id in admins_tg_id


@router.message(Command('newsletter'))
async def admin(message: Message, state: FSMContext):
    admins_tg_id = await get_admin()
    if message.from_user.id in admins_tg_id:
        await state.set_state(Newsletter.Text)
        await message.answer(text='Отправьте пост для рассылки по всем пользователям бота!', protect_content=True)
    else:
        await state.set_state(AdminVerification.Awaiting_password)
        await message.answer(text='Извините, это команда только для админов. Если вы новый админ, введите пароль:',
                             protect_content=True)


@router.message(AdminVerification.Awaiting_password)
async def admin_password_input(message: Message, state: FSMContext):
    input_password = message.text
    newsletter_password = await get_newsletter_password()
    if input_password == newsletter_password:
        await add_administrator(message.from_user.id)
        await state.clear()
        await state.set_state(Newsletter.Text)
        await message.answer(
            text='Спасибо, вы добавлены. Теперь вы можете отправить пост для рассылки по всем пользователям бота!',
            protect_content=True)
    else:
        await state.clear()
        await message.answer(text='Неверный пароль. Попробуйте еще раз или обратитесь к текущему админу за помощью.',
                             protect_content=True)
        await state.set_state(AdminVerification.Awaiting_password)


@router.message(AdminProtect(), Newsletter.Text, F.content_type == ContentType.TEXT)
async def get_admin_text(message: Message, state: FSMContext, bot: Bot):
    users = await get_users()
    for Student in users:
        try:
            await bot.send_message(chat_id=Student.tg_id, text=message.text)
        except Exception as e:
            print(f'User banned or error: {e}')
    await message.answer(text='Текстовая рассылка завершена!', protect_content=True)
    await state.clear()


@router.message(AdminProtect(), Newsletter.Text, F.content_type == ContentType.PHOTO)
async def get_admin_photo(message: Message, state: FSMContext, bot: Bot):
    users = await get_users()
    caption = message.caption
    photo = message.photo[-1].file_id
    for Student in users:
        try:
            await bot.send_photo(chat_id=Student.tg_id, photo=photo, caption=caption)
        except Exception as e:
            print(f'User banned or error: {e}')
    await message.answer(text='Рассылка завершена!', protect_content=True)
    await state.clear()
