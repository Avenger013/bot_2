import os
import datetime

# from moviepy.editor import VideoFileClip

from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, Message
from sqlalchemy import select, and_

from application.database.models import DailyCheckIn, PointsHistory, async_session
from application.database.requests import get_student, get_tasks_for_the_week

import application.keyboard as kb

router = Router(name=__name__)


# def compress_video(input_file, output_file, target_bitrate="1M"):
#     clip = VideoFileClip(input_file)
#     clip.write_videofile(output_file, bitrate=target_bitrate, codec="libx264")
#     return output_file


async def send_attachments(bot, tg_id, attachments, specialisation):
    folder = 'tasks' if specialisation == 'Гитара' else 'tasks_vocal'
    photos = []
    attachment_list = attachments.split(',')
    for attachment in attachment_list:
        file_path = f'application/media/{folder}/{attachment.strip()}'
        if os.path.exists(file_path):
            file_input = FSInputFile(path=file_path)
            if file_path.endswith('.jpg'):
                photos.append(InputMediaPhoto(media=file_input))
            elif file_path.endswith('.mp4'):
                # compressed_file_path = file_path.replace('.mp4', '_compressed.mp4')
                # compress_video(file_path, compressed_file_path)
                # file_input = FSInputFile(path=compressed_file_path)

                await bot.send_video(chat_id=tg_id, video=file_input, protect_content=True)

                # os.remove(compressed_file_path)
    if photos:
        await bot.send_media_group(chat_id=tg_id, media=photos, protect_content=True)


async def show_homework(bot, tg_id, date_of_registration, specialisation_student):
    bot_week_quest, task_number = await get_tasks_for_the_week(date_of_registration, specialisation_student)
    response_text = "📋 <b>Задание на текущую неделю:</b>\n\n"

    if bot_week_quest:
        if specialisation_student == 'Гитара':
            response_text += f"Задание №{task_number}: {bot_week_quest.quest}\n\n"
        else:
            response_text += "Простые упражнения, которые помогут сделать голос сильнее и красивее! "
            response_text += "Задание выдаётся на пять дней, два дня отдых! "
            response_text += "Но даже в дни отдыха не забывайте заходить и отмечаться, чтобы получить балл!\n\n"
            response_text += f"Задание №{task_number}: {bot_week_quest.quest_vocal}\n\n"
        attachment = bot_week_quest.attachment if specialisation_student == 'Гитара' else bot_week_quest.attachment_vocal
        if bot_week_quest and attachment:
            await send_attachments(bot, tg_id, attachment, specialisation_student)
    else:
        response_text += "Задание на неделю еще не выставлено."

    return response_text


@router.message(Command('mark'))
async def submit_homework_mark(message: Message, bot: Bot):
    tg_id = message.from_user.id

    async with async_session() as session:
        student = await get_student(session, tg_id)
        if not student:
            await message.answer(
                text=f'{message.from_user.first_name}, это ваш первый вход. \nПожалуйста, пройдите быструю регистрацию.',
                reply_markup=kb.registration, protect_content=True
            )
            return

        if student.specialisation_student == 'Вокал и Гитара':
            await message.answer(text="Выберите специализацию для задания:", reply_markup=kb.specialisation_keyboard,
                                 protect_content=True)
        else:
            response_text = await show_homework(bot, tg_id, student.date_of_registration,
                                                student.specialisation_student)
            await message.answer(text=response_text, reply_markup=kb.back6, parse_mode='HTML', protect_content=True)


@router.callback_query(F.data.startswith('specialisation_'))
async def handle_specialisation_choice(callback: CallbackQuery, bot: Bot):
    tg_id = callback.from_user.id
    chosen_specialisation = callback.data.split('_')[1]

    async with async_session() as session:
        student = await get_student(session, tg_id)
        if not student:
            await callback.message.answer(text="Ваш аккаунт не найден в системе.", protect_content=True)
            return

        specialisation_student = 'Гитара' if chosen_specialisation == 'guitar' else 'Вокал'
        response_text = await show_homework(bot, tg_id, student.date_of_registration, specialisation_student)
        await callback.message.answer(text=response_text, reply_markup=kb.back6, parse_mode='HTML',
                                      protect_content=True)


@router.callback_query(F.data.startswith('zd_send'))
async def submit_homework(callback: CallbackQuery, bot: Bot):
    tg_id = callback.from_user.id

    async with async_session() as session:
        student = await get_student(session, tg_id)
        if not student:
            await callback.message.answer(text="Ваш аккаунт не найден в системе.", protect_content=True)
            return

    if student.specialisation_student == 'Вокал и Гитара':
        await callback.message.answer(text="Выберите специализацию для задания:",
                                      reply_markup=kb.specialisation_keyboard,
                                      protect_content=True)
    else:
        response_text = await show_homework(bot, tg_id, student.date_of_registration,
                                            student.specialisation_student)
        await callback.message.answer(text=response_text, reply_markup=kb.back5, parse_mode='HTML',
                                      protect_content=True)


@router.callback_query(F.data.startswith('check_in'))
async def check_in_homework(callback: CallbackQuery):
    tg_id = callback.from_user.id
    today = datetime.now().date()

    async with async_session() as session:
        student = await get_student(session, tg_id)
        if not student:
            await callback.message.answer(text="Ваш аккаунт не найден в системе.", protect_content=True)
            return

        date_of_registration = student.date_of_registration.date()
        current_week = (today - date_of_registration).days // 7

        daily_check_in = await session.execute(
            select(DailyCheckIn)
            .where(and_(DailyCheckIn.student_id == student.id, DailyCheckIn.date == today))
        )
        daily_check_in = daily_check_in.scalars().first()

        if daily_check_in:
            daily_check_in_text = (
                "Вы уже отметились сегодня, не забудьте отметиться завтра!"
                f"Ваше текущее количество отметок: {daily_check_in.check_in_count}"
            )
            await callback.message.edit_text(text=daily_check_in_text, reply_markup=kb.back3, protect_content=True)
            return

        last_check_in = await session.execute(
            select(DailyCheckIn)
            .where(DailyCheckIn.student_id == student.id)
            .order_by(DailyCheckIn.date.desc())
        )
        last_check_in = last_check_in.scalars().first()

        last_week = (last_check_in.date - date_of_registration).days // 7 if last_check_in else None
        if last_week is not None and last_week != current_week:
            last_check_in.check_in_count = 0

        if last_check_in and last_check_in.date < today:
            last_check_in.check_in_count += 1
            last_check_in.date = today

            if last_check_in.check_in_count >= 7:
                points_to_add = 1
                student.point = (student.point or 0) + points_to_add
                last_check_in.check_in_count = 0

                new_points_history = PointsHistory(student_id=student.id, points_added=points_to_add,
                                                   date_added=datetime.now())
                session.add(new_points_history)

                last_check_in_text = (
                    "Поздравляем! Вы набрали 7 отметок и получили <b>+1 балл</b>.\n"
                    "Количество баллов можно посмотреть в <b>личном кабинете!</b>"
                )
                await callback.message.edit_text(text=last_check_in_text, parse_mode='HTML', reply_markup=kb.back3,
                                                 protect_content=True)
            else:
                await callback.message.edit_text(
                    text="Отметка успешно учтена!", reply_markup=kb.back3, protect_content=True)

            await session.commit()
        else:
            new_check_in = DailyCheckIn(student_id=student.id, date=today, check_in_count=1)
            session.add(new_check_in)
            await session.commit()
            await callback.message.edit_text(text="Отметка успешно учтена! Это ваша первая отметка.",
                                             reply_markup=kb.back3, protect_content=True)
