import os
import re
import datetime
import hashlib

from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func, and_, or_
from aiogram.exceptions import TelegramBadRequest

from application.states import HomeworkState2
from application.database.models import Student, Homework, async_session

import application.keyboard as kb

router = Router(name=__name__)


@router.callback_query(F.data.startswith('vid_send'))
async def call_submitting_homework_2(callback: CallbackQuery, state: FSMContext):
    tg_id = callback.from_user.id
    await callback.message.edit_text(text='Выберите преподавателя, которому вы хотите отправить домашнее задание:',
                                     reply_markup=await kb.choice_teacher(tg_id), protect_content=True)
    await state.set_state(HomeworkState2.ChoiceTeacher2)


@router.callback_query(F.data.startswith('2_canceled'))
async def call_submitting_homework_2_2(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    tg_id = callback.from_user.id
    await callback.message.edit_text(text='Выберите преподавателя, которому вы хотите отправить домашнее задание:',
                                     reply_markup=await kb.choice_teacher(tg_id), protect_content=True)
    await state.set_state(HomeworkState2.ChoiceTeacher2)


@router.callback_query(F.data.startswith('choice_'), HomeworkState2.ChoiceTeacher2)
async def teacher_selected_for_homework_2(callback: CallbackQuery, state: FSMContext):
    teacher_id = callback.data.split('_')[1]
    await state.update_data(teacher_id=teacher_id)
    await callback.message.edit_text(text='В каком виде вы хотите отправить видео?', reply_markup=kb.dz_type_2,
                                     protect_content=True)
    await state.set_state(HomeworkState2.ChoosingDZType2)


@router.callback_query(F.data.startswith('vvv'), HomeworkState2.ChoosingDZType2)
async def dz_type_video_2(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='😁Отлично, теперь пришлите видео вашего домашнего задания!',
                                     reply_markup=kb.tree_can_send, protect_content=True)
    await state.set_state(HomeworkState2.WaitingForVideo2)


@router.callback_query(F.data.startswith('lll'), HomeworkState2.ChoosingDZType2)
async def dz_type_links_2(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text='😁Отлично, теперь пришлите ссылку, по которой можно будет ознакомиться с вашим видео!',
        reply_markup=kb.tree_can_send, protect_content=True)
    await state.set_state(HomeworkState2.WaitingForLinks2)


async def generate_hash_2(file_path):
    filename = os.path.basename(file_path)
    return hashlib.md5(filename.encode()).hexdigest()


async def check_video_submission_limit(student_id):
    today = datetime.utcnow()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    async with async_session() as session:
        count = await session.scalar(
            select(func.count(Homework.id)).where(
                and_(
                    Homework.student_id == student_id,
                    Homework.submission_time >= start_of_month,
                    or_(
                        Homework.file_type == 'video_2',
                        Homework.file_type == 'links_2'
                    )
                )
            )
        )
        return count < 2


@router.message(F.video, HomeworkState2.WaitingForVideo2)
async def receive_homework_video_2(message: Message, state: FSMContext):
    tg_id = message.from_user.id

    async with async_session() as session:
        try:
            student = await session.scalar(select(Student).where(Student.tg_id == tg_id))
            if not student:
                await message.answer(text="Студент не найден в базе данных.", protect_content=True)
                return
            student_id = student.id

            if not await check_video_submission_limit(student_id):
                await message.answer(
                    text="Вы уже отправили видео два раза в этом месяце. Пожалуйста, попробуйте в следующем месяце.",
                    protect_content=True)
                return
        except Exception as e:
            await message.answer(text=f"Произошла ошибка при доступе к базе данных: {str(e)}", protect_content=True)
            return

    data = await state.get_data()
    teacher_id = data.get('teacher_id')

    video_id = message.video.file_id

    await state.update_data(video_id=video_id, student_id=student_id, teacher_id=teacher_id)
    await message.answer(text="🧐Всё верно? Окончательно отправить?", reply_markup=kb.confirmation_video_2,
                         protect_content=True)


@router.callback_query(F.data.in_(['iv_2_confirm', 'oed_2_change']), HomeworkState2.WaitingForVideo2)
async def confirm_homework_video_2(callback: CallbackQuery, state: FSMContext, bot: Bot):
    call_data = callback.data

    await callback.message.edit_reply_markup(reply_markup=None)

    if call_data == 'iv_2_confirm':
        data = await state.get_data()
        video_id = data['video_id']
        student_id = data['student_id']
        teacher_id = data['teacher_id']

        async with async_session() as session:
            student = await session.scalar(select(Student).where(Student.id == student_id))
            if not student:
                await callback.message.answer(text="Произошла ошибка при поиске данных студента.", protect_content=True)
                return

        full_name = f'{student.name} {student.last_name}'

        try:
            file = await bot.get_file(video_id)
            file_path = file.file_path

            directory = "application/media/video"
            if not os.path.exists(directory):
                os.makedirs(directory)

            timestamp = datetime.now().strftime("%d_%m_%Y_%H-%M-%S")
            filename = f"{directory}/{teacher_id}_{student_id}_{full_name}_{timestamp}_video_2.mp4"

            await bot.download_file(file_path, filename)

            file_hash = await generate_hash_2(filename)

            async with async_session() as session:
                new_homework = Homework(
                    student_id=student_id,
                    teacher_id=teacher_id,
                    file_hash=file_hash,
                    file_type='video_2',
                    submission_time=datetime.now()
                )
                session.add(new_homework)
                await session.commit()

            await callback.message.answer(text="✅Видео успешно отправлено!", reply_markup=kb.menu, protect_content=True)
            await state.clear()
        except TelegramBadRequest as e:
            if "file is too big" in str(e):
                text = (
                    "<b>✉️Ошибка!</b>\n\n"
                    "😔Извините, ваше видео слишком много весит (максимум 50 МБ)!\n"
                    "├ Попробуйте начать заново, выбрав отправку в виде ссылки.\n"
                    "└ Или отправьте другое видео, меньшего размера."
                )
                await callback.message.edit_text(text=text, reply_markup=kb.inline_keyboard_error_video,
                                                 parse_mode='HTML', protect_content=True)
            else:
                await callback.message.answer(text="😔Произошла ошибка при отправке видео.", reply_markup=kb.menu1,
                                              protect_content=True)
    elif call_data == 'oed_2_change':
        await callback.message.answer(text="😌Отлично, отправьте свое домашнее задание ещё раз.",
                                      reply_markup=kb.tree_can_send, protect_content=True)

    await callback.answer()


def find_links(text):
    url_regex = r'https?://[^\s]+'
    return re.findall(url_regex, text)


async def save_homework_with_links(directory_links, filename_links, links):
    if not os.path.exists(directory_links):
        os.makedirs(directory_links)

    with open(filename_links, 'w', encoding='utf-8') as file:
        file.write('<html><body>\n')
        for link in links:
            file.write(f'<a href="{link}">{link}</a><br>\n')
        file.write('</body></html>')


@router.message(F.text, HomeworkState2.WaitingForLinks2)
async def receive_homework_text_2(message: Message, state: FSMContext):
    tg_id = message.from_user.id

    commands = ['/profile', '/homework', '/top', '/leader', '/monetization', '/info', '/support', '/mark',
                '/start', '/newsletter']
    input_text = message.text

    if input_text in commands:
        await state.clear()
        await message.answer(text="Обнаружена команда. Пожалуйста, введите команду ещё раз.", protect_content=True)
        return

    async with async_session() as session:
        try:
            student = await session.scalar(select(Student).where(Student.tg_id == tg_id))
            if not student:
                await message.answer(text="Студент не найден в базе данных.", protect_content=True)
                return
            student_id = student.id

            if not await check_video_submission_limit(student_id):
                await message.answer(
                    text="Вы уже отправили ссылку два раза в этом месяце. Пожалуйста, попробуйте в следующем месяце.",
                    protect_content=True)
                return
        except Exception as e:
            await message.answer(text=f"Произошла ошибка при доступе к базе данных: {str(e)}", protect_content=True)
            return

    data = await state.get_data()
    teacher_id = data.get('teacher_id')

    links = find_links(message.text)
    if not links:
        await message.answer(text="❎Вы отправили текст, а нужно ссылку!")
        return

    await state.update_data(text=message.text, student_id=student_id, teacher_id=teacher_id)
    await message.answer(text="🧐Всё верно? Окончательно отправить?", reply_markup=kb.confirmation_text_2,
                         protect_content=True)


@router.callback_query(F.data.in_(['et_2_confirm', 'tx_2_change']), HomeworkState2.WaitingForLinks2)
async def confirm_homework_text_2(callback: CallbackQuery, state: FSMContext):
    call_data = callback.data
    data = await state.get_data()

    await callback.message.edit_reply_markup(reply_markup=None)

    if call_data == 'et_2_confirm':
        text = data.get('text')
        student_id = data.get('student_id')
        teacher_id = data.get('teacher_id')

        async with async_session() as session:
            student = await session.scalar(select(Student).where(Student.id == student_id))
            if not student:
                await callback.message.answer(text="Произошла ошибка при поиске данных студента.", protect_content=True)
                return

        full_name = f'{student.name} {student.last_name}'
        timestamp = datetime.now().strftime("%d_%m_%Y_%H-%M-%S")
        links = find_links(text)

        directory_links = "application/media/links"
        filename_links = f"{directory_links}/{teacher_id}_{student_id}_{full_name}_{timestamp}_links_2.html"
        await save_homework_with_links(directory_links, filename_links, links)

        file_hash = await generate_hash_2(filename_links)

        async with async_session() as session:
            new_homework = Homework(
                student_id=student_id,
                teacher_id=teacher_id,
                file_hash=file_hash,
                file_type='links_2',
                submission_time=datetime.now()
            )
            session.add(new_homework)
            await session.commit()

        response_message = "✅Домашнее задание (ссылка) успешно отправлено!"
        await callback.message.answer(text=response_message, reply_markup=kb.menu)
        await state.clear()
    elif call_data == 'tx_2_change':
        await callback.message.answer(text="😌Отлично, отправьте домашнее задание ещё раз.",
                                      reply_markup=kb.tree_can_send, protect_content=True)

    await callback.answer()


@router.message(F.photo | F.text | F.document | F.sticker | F.voice | F.location | F.contact | F.poll,
                HomeworkState2.WaitingForVideo2)
async def wrong_type_for_video_2(message: Message):
    await message.answer(text="🥺Вы отправили не тот тип сообщения (ожидалось видео). Попробуйте еще раз.",
                         reply_markup=kb.tree_can_send, protect_content=True)


@router.message(F.photo | F.video | F.document | F.sticker | F.voice | F.location | F.contact | F.poll,
                HomeworkState2.WaitingForLinks2)
async def wrong_type_for_links_2(message: Message):
    await message.answer(text="🥺Вы отправили не тот тип сообщения (ожидалась ссылка). Попробуйте еще раз.",
                         reply_markup=kb.tree_can_send, protect_content=True)
