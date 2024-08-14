import glob
import re
import hashlib
import os

from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup, InlineKeyboardBuilder

from application.states import PasswordCheck, FeedbackState
from application.database.requests import get_homework_with_details, get_teacher_by_password, get_users_by_ids, \
    get_student_by_id, get_homework_by_file_hash, get_teacher_by_id, update_feedback_sent
from application.database.models import PointsHistory, async_session

router = Router(name=__name__)

file_hash_map = {}


@router.message(Command('teacher'))
async def register_students(message: Message, state: FSMContext):
    await message.answer(text='Введите пароль:', reply_markup=ReplyKeyboardRemove(), protect_content=True)
    await state.set_state(PasswordCheck.EnterPassword)


@router.message(PasswordCheck.EnterPassword)
async def check_password(message: Message, state: FSMContext):
    commands = ['/profile', '/homework', '/top', '/leader', '/monetization', '/info', '/support', '/mark',
                '/start', '/newsletter']
    input_text = message.text

    if input_text in commands:
        await state.clear()
        await message.answer(text="Обнаружена команда. Пожалуйста, введите команду ещё раз.", protect_content=True)
        return

    input_password = input_text.strip()
    teacher = await get_teacher_by_password(input_password)

    if teacher:
        teacher_full_name = f'{teacher.name} {teacher.last_name}'
        await message.answer(text=f'Пароль верен! Здравствуйте, {teacher_full_name}!', protect_content=True)
        keyboard = await students_choice(teacher.id)
        await message.answer(text='Выберите ученика, чтобы посмотреть его домашние задания:', reply_markup=keyboard,
                             protect_content=True)
        await state.clear()
    else:
        await message.answer(text='🙈 Извините, пароль не верен, попробуйте еще раз.', protect_content=True)


async def students_choice(teacher_id: int) -> InlineKeyboardMarkup:
    directories = {
        "application/media/photo": "*.jpg",
        "application/media/text": "*.txt",
        "application/media/video": "*.mp4",
        "application/media/links": "*.html",
        "application/media/voice": "*.ogg",
    }

    student_ids = set()
    for directory, ext in directories.items():
        files = glob.glob(f"{directory}/{teacher_id}_*{ext}")
        for filename in files:
            match = re.search(rf"{teacher_id}_(\d+)_", filename)
            if match:
                student_ids.add(match.group(1))

    if not student_ids:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Нет доступных домашних заданий", callback_data="no_homework")]
        ])
        return keyboard

    students_choice_kb = InlineKeyboardBuilder()
    students = await get_users_by_ids(list(student_ids))
    for student in students:
        full_name = f'{student.name} {student.last_name}'
        students_choice_kb.add(InlineKeyboardButton(text=full_name, callback_data=f'student_{student.id}_{teacher_id}'))
    return students_choice_kb.adjust(2).as_markup()


async def generate_hash(file_path):
    filename = os.path.basename(file_path)
    file_hash = hashlib.md5(filename.encode()).hexdigest()
    file_hash_map[file_hash] = file_path
    return file_hash


@router.callback_query(F.data.startswith('student_'))
async def student_files(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split('_')
    student_id = parts[1]
    teacher_id = parts[2]

    directories = {
        "application/media/photo": f"{teacher_id}_{student_id}_*.jpg",
        "application/media/text": f"{teacher_id}_{student_id}_*.txt",
        "application/media/video": f"{teacher_id}_{student_id}_*.mp4",
        "application/media/links": f"{teacher_id}_{student_id}_*.html",
        "application/media/voice": f"{teacher_id}_{student_id}_*.ogg",
    }

    files_found = False
    for directory, pattern in directories.items():
        full_pattern = f"{directory}/{pattern}"
        files = glob.glob(full_pattern)

        for filename in files:
            files_found = True
            file_hash = await generate_hash(filename)

            buttons = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Принять", callback_data=f'accepted_{file_hash}'),
                 InlineKeyboardButton(text="Отклонить", callback_data=f'decline_{file_hash}')],
                [InlineKeyboardButton(text="Обратная связь", callback_data=f'feedback_{file_hash}')]
            ])

            if filename.endswith('_video_2.mp4'):
                keyboard = buttons
            elif filename.endswith('_links_2.html'):
                keyboard = buttons
            else:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Принять", callback_data=f'accept_{file_hash}'),
                     InlineKeyboardButton(text="Отклонить", callback_data=f'decline_{file_hash}')],
                    [InlineKeyboardButton(text="Обратная связь", callback_data=f'feedback_{file_hash}')]
                ])

            file_input = FSInputFile(path=filename)

            await bot.send_document(chat_id=callback.from_user.id, document=file_input, reply_markup=keyboard,
                                    protect_content=True)

    if not files_found:
        await callback.message.answer(text="У этого ученика нет отправленных домашних заданий.", protect_content=True)


@router.callback_query(F.data.startswith('accept_'))
async def accept_homework(callback: CallbackQuery):
    file_hash = callback.data.split('_', 1)[1]

    async with async_session() as session:
        homework, student = await get_homework_with_details(session, file_hash)

        if not homework:
            await callback.answer(text="Домашнее задание не найдено.", show_alert=True)
            return

        if not student:
            await callback.answer(text="Студент не найден.", show_alert=True)
            return

        if not homework.feedback_sent:
            await callback.answer(text="Необходимо отправить обратную связь перед принятием домашнего задания.",
                                  show_alert=True)
            return

        points_to_add = 3
        student.point = (student.point or 0) + points_to_add

        new_points_history = PointsHistory(student_id=student.id, points_added=points_to_add, date_added=datetime.now())
        session.add(new_points_history)

        await session.commit()

        file_path = file_hash_map.get(file_hash)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    updated_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверено", callback_data=f'checked_{file_hash}')]
    ])

    await callback.message.edit_reply_markup(reply_markup=updated_keyboard)


@router.callback_query(F.data.startswith('accepted_'))
async def accept_homework(callback: CallbackQuery):
    file_hash = callback.data.split('_', 1)[1]

    async with async_session() as session:
        homework, student = await get_homework_with_details(session, file_hash)

        if not homework:
            await callback.answer(text="Домашнее задание не найдено.", show_alert=True)
            return

        if not student:
            await callback.answer(text="Студент не найден.", show_alert=True)
            return

        if not homework.feedback_sent:
            await callback.answer(text="Необходимо отправить обратную связь перед принятием домашнего задания.",
                                  show_alert=True)
            return

        points_to_add = 2
        student.point = (student.point or 0) + points_to_add

        new_points_history = PointsHistory(student_id=student.id, points_added=points_to_add, date_added=datetime.now())
        session.add(new_points_history)

        await session.commit()

        file_path = file_hash_map.get(file_hash)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    updated_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверено", callback_data=f'checked_{file_hash}')]
    ])

    await callback.message.edit_reply_markup(reply_markup=updated_keyboard)


@router.callback_query(F.data.startswith('decline_'))
async def decline_homework(callback: CallbackQuery):
    file_hash = callback.data.split('_', 1)[1]

    async with async_session() as session:
        homework, student = await get_homework_with_details(session, file_hash)

        if not homework:
            await callback.answer(text="Домашнее задание не найдено.", show_alert=True)
            return

        if not student:
            await callback.answer(text="Студент не найден.", show_alert=True)
            return

        if not homework.feedback_sent:
            await callback.answer(text="Необходимо отправить обратную связь перед отклонением домашнего задания.",
                                  show_alert=True)
            return

        await session.commit()

        file_path = file_hash_map.get(file_hash)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    updated_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверено", callback_data=f'checked_{file_hash}')]
    ])

    await callback.message.edit_reply_markup(reply_markup=updated_keyboard)


@router.callback_query(F.data.startswith('checked_'))
async def checked_homework(callback: CallbackQuery):
    await callback.answer(text="Это домашнее задание уже проверено.", show_alert=True)


@router.callback_query(F.data.startswith('no_homework'))
async def checked_homework(callback: CallbackQuery):
    await callback.answer(text="Для вас нет заданий для проверки.", show_alert=True)


@router.callback_query(F.data.startswith('feedback_'))
async def feedback_homework(callback: CallbackQuery, state: FSMContext):
    file_hash = callback.data.split('_', 1)[1]

    async with async_session() as session:
        homework = await get_homework_by_file_hash(session, file_hash)
        if not homework:
            await callback.message.answer(text="Домашнее задание не найдено.", protect_content=True)
            return

        student = await get_student_by_id(session, homework.student_id)
        if not student:
            await callback.message.answer(text="Студент не найден.", protect_content=True)
            return

        teacher = await get_teacher_by_id(session, homework.teacher_id)
        if not teacher:
            await callback.message.answer(text="Преподаватель не найден.", protect_content=True)
            return

        teacher_full_name = f'{teacher.name} {teacher.last_name}'

        await state.update_data(student_tg_id=student.tg_id, teacher_full_name=teacher_full_name,
                                homework_id=homework.id)
        await state.set_state(FeedbackState.WaitingForText)

        cancel_button = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Отмена отправки", callback_data="car_feedback")]
            ]
        )

        await callback.message.answer(text="Введите текст обратной связи для студента:", reply_markup=cancel_button,
                                      protect_content=True)

    await callback.answer()


@router.message(F.text, FeedbackState.WaitingForText)
async def receive_feedback_text(message: Message, state: FSMContext, bot: Bot):
    feedback_text = message.text
    data = await state.get_data()
    student_tg_id = data.get('student_tg_id')
    teacher_full_name = data.get('teacher_full_name')
    homework_id = data.get('homework_id')

    text = (
        f"📬 У вас новая обратная связь: {feedback_text}\n\n"
        f"🎓 Преподаватель: {teacher_full_name}."
    )

    try:
        await bot.send_message(chat_id=student_tg_id, text=text)
        await message.answer(text="Обратная связь отправлена студенту.", protect_content=True)

        async with async_session() as session:
            await update_feedback_sent(session, homework_id)

    except Exception as e:
        await message.answer(text=f"Не удалось отправить сообщение студенту: {e}", protect_content=True)

    await state.clear()


@router.message(F.photo | F.video | F.document | F.sticker | F.voice | F.location | F.contact | F.poll,
                FeedbackState.WaitingForText)
async def wrong_type_for_text(message: Message):
    await message.answer(text="🥺Вы выбрали не тот тип домашнего задания (ожидался текст). Попробуйте еще раз.",
                         protect_content=True)


@router.callback_query(F.data.startswith('car_feedback'), FeedbackState.WaitingForText)
async def checked_homework(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(text="Отправка обратной связи отменена.", reply_markup=None, protect_content=True)


@router.callback_query(F.data.startswith('car'))
async def checked_homework(callback: CallbackQuery):
    await callback.answer(text="Отмена недоступна.", show_alert=True)
