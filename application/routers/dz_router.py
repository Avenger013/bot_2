import os
import re
import datetime
import hashlib

from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from aiogram.exceptions import TelegramBadRequest

from application.states import HomeworkState
from application.database.models import Student, Homework, async_session
from application.database.requests import get_student

import application.keyboard as kb

router = Router(name=__name__)


async def info_homework(callback: CallbackQuery, reply_markup):
    homework_text = (
        "<b>✉️ Отправка ДЗ</b>\n\n"
        "Есть 3 варианта на выбор:\n\n"
        "📨Отправить выполненное ДЗ\n"
        "├ Домашнее задание назначает ваш преподаватель на занятии\n"
        "├ Дз можно отправлять в виде: <b>фото</b>, <b>видео</b>, <b>текста</b>, <b>голосового</b> или <b>ссылки</b>\n"
        "└ За его выполнение вы получите <b>+3 балла</b>, после проверки преподавателем\n\n"
        "📆 Отправить еженедельное задание (отметиться о его выполнении)\n"
        "├ Задание автоматически выставляется всем ученикам, каждые 7 дней задание меняется\n"
        "├ Задание отличается согласно выбранному направлению обучения: вокал, гитара или оба направления сразу\n"
        "├ Чтобы заработать балл, необходимо ежедневно заходить в систему и нажимать кнопку <b>«Отметиться»</b>\n"
        "├ После набора 7 отметок в течение недели, они спишутся, и вы автоматически получите <b>+1 балл</b>\n"
        "├ С началом новой недели и сменой задания, ваш счетчик отметок обнулится\n"
        "└ Проверка выполнения задания отсутствует, полагаемся на вашу ответственность и желание развиваться\n\n"
        "📹Отправить видео с полной версией песни в своем исполнении\n"
        "├ Песню выбираете любую, по своему желанию\n"
        "├ Можно отправлять максимум 2 раза в месяц\n"
        "└ За выполнение вы получите <b>+2 балла</b>, после просмотра преподавателем"
    )
    await callback.message.edit_text(text=homework_text, parse_mode='HTML', reply_markup=reply_markup,
                                     protect_content=True)


@router.message(F.text == '✉️ Отправка ДЗ')
@router.message(Command('homework'))
async def submitting_homework(message: Message):
    tg_id = message.from_user.id
    async with async_session() as session:
        student = await get_student(session, tg_id)
        if student:
            homework_text = (
                "<b>✉️ Отправка ДЗ</b>\n\n"
                "Есть 3 варианта на выбор:\n\n"
                "📨Отправить выполненное ДЗ\n"
                "├ Данное домашнее задание назначил ваш преподаватель\n"
                "├ Дз можно отправлять в виде: <b>фото</b>, <b>видео</b>, <b>текста</b>, <b>голосового</b> или <b>ссылки</b>\n"
                "└ За его выполнение вы получите <b>+3 балла</b>, после проверки преподавателем\n\n"
                "📆 Отправить еженедельное задание (отметиться о его выполнении)\n"
                "├ Задание автоматически выставляется всем ученикам, каждые 7 дней задание меняется\n"
                "├ Задание отличается согласно выбранному направлению обучения: вокал, гитара или оба направления сразу\n"
                "├ Чтобы заработать балл, необходимо ежедневно заходить в систему и нажимать кнопку <b>«Отметиться»</b>\n"
                "├ После набора 7 отметок в течение недели, они спишутся, и вы автоматически получите <b>+1 балл</b>\n"
                "├ С началом новой недели и сменой задания, ваш счетчик отметок обнулится\n"
                "└ Проверка выполнения задания отсутствует, полагаемся на вашу ответственность и желание развиваться\n\n"
                "📹Отправить видео с полной версией песни в своем исполнении\n"
                "├ Песню выбираете любую, по своему желанию\n"
                "├ Можно отправлять максимум 2 раза в месяц\n"
                "└ За выполнение вы получите <b>+2 балла</b>, после просмотра преподавателем"
            )
            await message.answer(text=homework_text, parse_mode='HTML', reply_markup=kb.inline_homework1,
                                 protect_content=True)
        else:
            await message.answer(
                text=f'{message.from_user.first_name}, это ваш первый вход. \nПожалуйста, пройдите быструю регистрацию.',
                reply_markup=kb.registration, protect_content=True
            )


@router.callback_query(F.data.startswith('cancel'))
async def call_cancels(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await info_homework(callback, reply_markup=kb.inline_homework1)


@router.callback_query(F.data.startswith('send'))
async def call_submitting(callback: CallbackQuery):
    await info_homework(callback, reply_markup=kb.inline_homework)


@router.callback_query(F.data.startswith('dz_send'))
async def call_submitting_homework(callback: CallbackQuery, state: FSMContext):
    tg_id = callback.from_user.id
    await callback.message.edit_text(text='Выберите преподавателя, которому вы хотите отправить домашнее задание:',
                                     reply_markup=await kb.choice_teacher(tg_id), protect_content=True)
    await state.set_state(HomeworkState.ChoiceTeacher)


@router.callback_query(F.data.startswith('1_canceled'))
async def call_submitting_homework(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    tg_id = callback.from_user.id
    await callback.message.edit_text(text='Выберите преподавателя, которому вы хотите отправить домашнее задание:',
                                     reply_markup=await kb.choice_teacher(tg_id), protect_content=True)
    await state.set_state(HomeworkState.ChoiceTeacher)


@router.callback_query(F.data.startswith('choice_'), HomeworkState.ChoiceTeacher)
async def teacher_selected_for_homework(callback: CallbackQuery, state: FSMContext):
    teacher_id = callback.data.split('_')[1]
    await state.update_data(teacher_id=teacher_id)
    await callback.message.edit_text(text='Какой тип домашнего задания вы хотите отправить?', reply_markup=kb.dz_type,
                                     protect_content=True)
    await state.set_state(HomeworkState.ChoosingDZType)


@router.callback_query(F.data.startswith('p_p'), HomeworkState.ChoosingDZType)
async def dz_type_photo(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='😁Отлично, теперь пришлите фото вашего домашнего задания!',
                                     reply_markup=kb.tree_can_send, protect_content=True)
    await state.set_state(HomeworkState.WaitingForPhoto)


@router.callback_query(F.data.startswith('v_v'), HomeworkState.ChoosingDZType)
async def dz_type_video(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='😁Отлично, теперь пришлите видео вашего домашнего задания!',
                                     reply_markup=kb.tree_can_send, protect_content=True)
    await state.set_state(HomeworkState.WaitingForVideo)


@router.callback_query(F.data.startswith('t_l'), HomeworkState.ChoosingDZType)
async def dz_type_text_link(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text='😁Отлично, теперь напишите сообщение преподавателю или скиньте ссылку вашего домашнего задания!',
        reply_markup=kb.tree_can_send, protect_content=True)
    await state.set_state(HomeworkState.WaitingForTextAndLinks)


@router.callback_query(F.data.startswith('o_i'), HomeworkState.ChoosingDZType)
async def dz_type_text_link(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='😁Отлично, теперь запишите голосовое сообщение и отправьте в чат!',
                                     reply_markup=kb.tree_can_send, protect_content=True)
    await state.set_state(HomeworkState.WaitingForVoice)


@router.callback_query(F.data.startswith('a_a'), HomeworkState.ChoosingDZType)
async def dz_type_audio(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='😁Отлично, теперь отправьте ваш аудиофайл (mp3)!',
                                     reply_markup=kb.tree_can_send, protect_content=True)
    await state.set_state(HomeworkState.WaitingForAudio)


@router.message(F.audio, HomeworkState.WaitingForAudio)
async def receive_homework_audio(message: Message, state: FSMContext):
    tg_id = message.from_user.id

    async with async_session() as session:
        student = await session.scalar(select(Student).where(Student.tg_id == tg_id))
        if not student:
            await message.answer(text="🚫Студент не найден в базе данных.", protect_content=True)
            return
        student_id = student.id

    data = await state.get_data()
    teacher_id = data.get('teacher_id')

    audio_id = message.audio.file_id

    await state.update_data(audio_id=audio_id, student_id=student_id, teacher_id=teacher_id)
    await message.answer(text="🧐Всё верно? Окончательно отправить?", reply_markup=kb.confirmation_audio,
                         protect_content=True)


@router.callback_query(F.data.in_(['au_confirm', 'au_change']), HomeworkState.WaitingForAudio)
async def confirm_homework_audio(callback: CallbackQuery, state: FSMContext, bot: Bot):
    call_data = callback.data

    await callback.message.edit_reply_markup(reply_markup=None)

    if call_data == 'au_confirm':
        data = await state.get_data()
        audio_id = data['audio_id']
        student_id = data['student_id']
        teacher_id = data['teacher_id']

        async with async_session() as session:
            student = await session.scalar(select(Student).where(Student.id == student_id))
            if not student:
                await callback.message.answer(text="🚫Произошла ошибка при поиске данных студента.", protect_content=True)
                return

        full_name = f'{student.name} {student.last_name}'

        file = await bot.get_file(audio_id)
        file_path = file.file_path

        directory = "application/media/audio"
        if not os.path.exists(directory):
            os.makedirs(directory)

        timestamp = datetime.now().strftime("%d_%m_%Y_%H-%M-%S")
        filename = f"{directory}/{teacher_id}_{student_id}_{full_name}_{timestamp}_audio.mp3"

        await bot.download_file(file_path, filename)

        file_hash = await generate_hash_2(filename)

        async with async_session() as session:
            new_homework = Homework(
                student_id=student_id,
                teacher_id=teacher_id,
                file_hash=file_hash,
                file_type='audio',
                submission_time=datetime.now()
            )
            session.add(new_homework)
            await session.commit()

        await callback.message.answer(text="✅Домашнее задание (аудиофайл) успешно отправлено!", reply_markup=kb.menu,
                                      protect_content=True)
        await state.clear()
    elif call_data == 'au_change':
        await callback.message.answer(text="😌Отлично, отправьте аудиофайл еще раз.",
                                      reply_markup=kb.tree_can_send, protect_content=True)

    await callback.answer()


@router.message(F.photo, HomeworkState.WaitingForPhoto)
async def receive_homework_photo(message: Message, state: FSMContext):
    tg_id = message.from_user.id

    state_data = await state.get_data()
    current_media_group_id = state_data.get('current_media_group_id')

    if message.media_group_id and message.media_group_id == current_media_group_id:
        return

    if message.media_group_id:
        await state.update_data(current_media_group_id=message.media_group_id)
        await message.answer(text="🚫Пожалуйста, отправьте только одно фото, попробуйте еще раз!",
                             reply_markup=kb.tree_can_send, protect_content=True)
        return

    async with async_session() as session:
        student = await session.scalar(select(Student).where(Student.tg_id == tg_id))
        if not student:
            await message.answer(text="🚫Студент не найден в базе данных.", protect_content=True)
            return
        student_id = student.id

    data = await state.get_data()
    teacher_id = data.get('teacher_id')

    photo_id = message.photo[-1].file_id

    await state.update_data(photo_id=photo_id, student_id=student_id, teacher_id=teacher_id)
    await message.answer(text="🧐Всё верно? Окончательно отправить?", reply_markup=kb.confirmation, protect_content=True)


async def generate_hash_2(file_path):
    filename = os.path.basename(file_path)
    return hashlib.md5(filename.encode()).hexdigest()


@router.callback_query(F.data.in_(['confirm', 'change']), HomeworkState.WaitingForPhoto)
async def confirm_homework_photo(callback: CallbackQuery, state: FSMContext, bot: Bot):
    call_data = callback.data

    await callback.message.edit_reply_markup(reply_markup=None)

    if call_data == 'confirm':
        data = await state.get_data()
        photo_id = data['photo_id']
        student_id = data['student_id']
        teacher_id = data['teacher_id']

        async with async_session() as session:
            student = await session.scalar(select(Student).where(Student.id == student_id))
            if not student:
                await callback.message.answer(text="🚫Произошла ошибка при поиске данных студента.",
                                              protect_content=True)
                return

        full_name = f'{student.name} {student.last_name}'

        file = await bot.get_file(photo_id)
        file_path = file.file_path

        directory = "application/media/photo"
        if not os.path.exists(directory):
            os.makedirs(directory)

        timestamp = datetime.now().strftime("%d_%m_%Y_%H-%M-%S")
        filename = f"{directory}/{teacher_id}_{student_id}_{full_name}_{timestamp}_photo.jpg"

        await bot.download_file(file_path, filename)

        file_hash = await generate_hash_2(filename)

        async with async_session() as session:
            new_homework = Homework(
                student_id=student_id,
                teacher_id=teacher_id,
                file_hash=file_hash,
                file_type='photo',
                submission_time=datetime.now()
            )
            session.add(new_homework)
            await session.commit()

        await callback.message.answer(text="✅Домашнее задание (фото) успешно отправлено!", reply_markup=kb.menu,
                                      protect_content=True)
        await state.clear()
    elif call_data == 'change':
        await callback.message.answer(text="😌Отлично, отправьте свое домашнее задание ещё раз.",
                                      reply_markup=kb.tree_can_send, protect_content=True)

    await callback.answer()


@router.message(F.video, HomeworkState.WaitingForVideo)
async def receive_homework_video(message: Message, state: FSMContext):
    tg_id = message.from_user.id

    async with async_session() as session:
        student = await session.scalar(select(Student).where(Student.tg_id == tg_id))
        if not student:
            await message.answer(text="🚫Студент не найден в базе данных.", protect_content=True)
            return
        student_id = student.id

    data = await state.get_data()
    teacher_id = data.get('teacher_id')

    video_id = message.video.file_id

    await state.update_data(video_id=video_id, student_id=student_id, teacher_id=teacher_id)
    await message.answer(text="🧐Всё верно? Окончательно отправить?", reply_markup=kb.confirmation_video,
                         protect_content=True)


@router.callback_query(F.data.in_(['vi_confirm', 'deo_change']), HomeworkState.WaitingForVideo)
async def confirm_homework_video(callback: CallbackQuery, state: FSMContext, bot: Bot):
    call_data = callback.data

    await callback.message.edit_reply_markup(reply_markup=None)

    if call_data == 'vi_confirm':
        data = await state.get_data()
        video_id = data['video_id']
        student_id = data['student_id']
        teacher_id = data['teacher_id']

        async with async_session() as session:
            student = await session.scalar(select(Student).where(Student.id == student_id))
            if not student:
                await callback.message.answer(text="🚫Произошла ошибка при поиске данных студента.",
                                              protect_content=True)
                return

        full_name = f'{student.name} {student.last_name}'

        try:
            file = await bot.get_file(video_id)
            file_path = file.file_path

            directory = "application/media/video"
            if not os.path.exists(directory):
                os.makedirs(directory)

            timestamp = datetime.now().strftime("%d_%m_%Y_%H-%M-%S")
            filename = f"{directory}/{teacher_id}_{student_id}_{full_name}_{timestamp}_video.mp4"

            await bot.download_file(file_path, filename)

            file_hash = await generate_hash_2(filename)

            async with async_session() as session:
                new_homework = Homework(
                    student_id=student_id,
                    teacher_id=teacher_id,
                    file_hash=file_hash,
                    file_type='video',
                    submission_time=datetime.now()
                )
                session.add(new_homework)
                await session.commit()

            await callback.message.answer(text="✅Домашнее задание (видео) успешно отправлено!", reply_markup=kb.menu,
                                          protect_content=True)
            await state.clear()
        except TelegramBadRequest as e:
            if "file is too big" in str(e):
                text = (
                    "✉️<b>Ошибка!</b>\n\n"
                    "😔Извините, ваше видео слишком много весит (максимум 50 МБ)!\n"
                    "├ Попробуйте начать заново, выбрав отправку в виде ссылки.\n"
                    "└ Или отправьте другое видео, меньшего размера."
                )
                await callback.message.edit_text(text=text, reply_markup=kb.inline_keyboard_error_video,
                                                 parse_mode='HTML', protect_content=True)
            else:
                await callback.message.answer(text="😔Произошла ошибка при отправке видео.", reply_markup=kb.menu1,
                                              protect_content=True)
    elif call_data == 'deo_change':
        await callback.message.answer(text="😌Отлично, отправьте свое домашнее задание ещё раз.",
                                      reply_markup=kb.tree_can_send, protect_content=True)

    await callback.answer()


def format_text(text, line_length=80):
    lines = []
    while text:
        if len(text) > line_length:
            space_index = text.rfind(' ', 0, line_length)
            if space_index == -1:
                space_index = line_length
            lines.append(text[:space_index])
            text = text[space_index:].lstrip()
        else:
            lines.append(text)
            break
    return '\n'.join(lines)


def find_links(text):
    url_regex = r'https?://[^\s]+'
    return re.findall(url_regex, text)


@router.message(F.text, HomeworkState.WaitingForTextAndLinks)
async def receive_homework_text(message: Message, state: FSMContext):
    tg_id = message.from_user.id

    commands = ['/profile', '/homework', '/top', '/leader', '/monetization', '/info', '/support', '/mark',
                '/start', '/newsletter']
    input_text = message.text

    if input_text in commands:
        await state.clear()
        await message.answer(text="Обнаружена команда. Пожалуйста, введите команду ещё раз.", protect_content=True)
        return

    async with async_session() as session:
        student = await session.scalar(select(Student).where(Student.tg_id == tg_id))
        if not student:
            await message.answer(text="Студент не найден в базе данных.", protect_content=True)
            return
        student_id = student.id

    data = await state.get_data()
    teacher_id = data.get('teacher_id')

    await state.update_data(text=message.text, student_id=student_id, teacher_id=teacher_id)
    await message.answer(text="🧐Всё верно? Окончательно отправить?", reply_markup=kb.confirmation_text,
                         protect_content=True)


async def save_homework_with_links(directory_links, filename_links, links):
    if not os.path.exists(directory_links):
        os.makedirs(directory_links)

    with open(filename_links, 'w', encoding='utf-8') as file:
        file.write('<html><body>\n')
        for link in links:
            file.write(f'<a href="{link}">{link}</a><br>\n')
        file.write('</body></html>')


async def save_homework_text(directory, filename, text_content):
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(filename, 'w', encoding='utf-8') as file:
        file.write(text_content)


@router.callback_query(F.data.in_(['te_confirm', 'xt_change']), HomeworkState.WaitingForTextAndLinks)
async def confirm_homework_text(callback: CallbackQuery, state: FSMContext):
    call_data = callback.data
    data = await state.get_data()

    await callback.message.edit_reply_markup(reply_markup=None)

    if call_data == 'te_confirm':
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

        if links:
            directory_links = "application/media/links"
            filename_links = f"{directory_links}/{teacher_id}_{student_id}_{full_name}_{timestamp}_links.html"
            await save_homework_with_links(directory_links, filename_links, links)

            file_hash = await generate_hash_2(filename_links)

            async with async_session() as session:
                new_homework = Homework(
                    student_id=student_id,
                    teacher_id=teacher_id,
                    file_hash=file_hash,
                    file_type='links',
                    submission_time=datetime.now()
                )
                session.add(new_homework)
                await session.commit()

            response_message = "✅Домашнее задание (ссылка) успешно отправлено!"
        else:
            text_content = format_text(text)
            directory = "application/media/text"
            filename = f"{directory}/{teacher_id}_{student_id}_{full_name}_{timestamp}_text.txt"
            await save_homework_text(directory, filename, text_content)

            file_hash = await generate_hash_2(filename)

            async with async_session() as session:
                new_homework = Homework(
                    student_id=student_id,
                    teacher_id=teacher_id,
                    file_hash=file_hash,
                    file_type='text',
                    submission_time=datetime.now()
                )
                session.add(new_homework)
                await session.commit()

            response_message = "✅Сообщение преподавателю успешно отправлено!"

        await callback.message.answer(text=response_message, reply_markup=kb.menu, protect_content=True)
        await state.clear()
    elif call_data == 'xt_change':
        await callback.message.answer(text="😌Отлично, отправьте домашнее задание ещё раз.",
                                      reply_markup=kb.tree_can_send, protect_content=True)

    await callback.answer()


@router.message(F.voice, HomeworkState.WaitingForVoice)
async def receive_homework_voice(message: Message, state: FSMContext):
    tg_id = message.from_user.id

    async with async_session() as session:
        student = await session.scalar(select(Student).where(Student.tg_id == tg_id))
        if not student:
            await message.answer(text="Студент не найден в базе данных.", protect_content=True)
            return
        student_id = student.id

    data = await state.get_data()
    teacher_id = data.get('teacher_id')

    voice_id = message.voice.file_id

    await state.update_data(voice_id=voice_id, student_id=student_id, teacher_id=teacher_id)
    await message.answer(text="🧐Всё верно? Окончательно отправить?", reply_markup=kb.confirmation_voice,
                         protect_content=True)


@router.callback_query(F.data.in_(['voi_confirm', 'ce_change']), HomeworkState.WaitingForVoice)
async def confirm_homework_voice(callback: CallbackQuery, state: FSMContext, bot: Bot):
    call_data = callback.data

    await callback.message.edit_reply_markup(reply_markup=None)

    if call_data == 'voi_confirm':
        data = await state.get_data()
        voice_id = data['voice_id']
        student_id = data['student_id']
        teacher_id = data['teacher_id']

        async with async_session() as session:
            student = await session.scalar(select(Student).where(Student.id == student_id))
            if not student:
                await callback.message.answer(text="Произошла ошибка при поиске данных студента.", protect_content=True)
                return

        full_name = f'{student.name} {student.last_name}'

        file = await bot.get_file(voice_id)
        file_path = file.file_path

        directory = "application/media/voice"
        if not os.path.exists(directory):
            os.makedirs(directory)

        timestamp = datetime.now().strftime("%d_%m_%Y_%H-%M-%S")
        filename = f"{directory}/{teacher_id}_{student_id}_{full_name}_{timestamp}_voice.ogg"

        await bot.download_file(file_path, filename)

        file_hash = await generate_hash_2(filename)

        async with async_session() as session:
            new_homework = Homework(
                student_id=student_id,
                teacher_id=teacher_id,
                file_hash=file_hash,
                file_type='voice',
                submission_time=datetime.now()
            )
            session.add(new_homework)
            await session.commit()

        await callback.message.answer(text="✅Домашнее задание (голосовое сообщение) успешно отправлено!",
                                      reply_markup=kb.menu, protect_content=True)
        await state.clear()
    elif call_data == 'ce_change':
        await callback.message.answer(text="😌Отлично, отправьте ваше домашнее задание ещё раз.",
                                      reply_markup=kb.tree_can_send, protect_content=True)
    await callback.answer()


@router.message(F.video | F.text | F.document | F.sticker | F.voice | F.location | F.contact | F.poll | F.audio,
                HomeworkState.WaitingForPhoto)
async def wrong_homework_type(message: Message):
    await message.answer(text="🥺Вы выбрали не тот тип домашнего задания (ожидалось фото). Попробуйте еще раз.",
                         reply_markup=kb.tree_can_send, protect_content=True)


@router.message(F.photo | F.text | F.document | F.sticker | F.voice | F.location | F.contact | F.poll | F.audio,
                HomeworkState.WaitingForVideo)
async def wrong_type_for_video(message: Message):
    await message.answer(text="🥺Вы выбрали не тот тип домашнего задания (ожидалось видео). Попробуйте еще раз.",
                         reply_markup=kb.tree_can_send, protect_content=True)


@router.message(F.photo | F.video | F.document | F.sticker | F.voice | F.location | F.contact | F.poll | F.audio,
                HomeworkState.WaitingForTextAndLinks)
async def wrong_type_for_text_and_links(message: Message):
    await message.answer(
        text="🥺Вы выбрали не тот тип домашнего задания (ожидалось текстовое сообщение или ссылка). Попробуйте еще раз.",
        reply_markup=kb.tree_can_send, protect_content=True)


@router.message(F.photo | F.video | F.text | F.document | F.sticker | F.location | F.contact | F.poll | F.audio,
                HomeworkState.WaitingForVoice)
async def wrong_type_for_voice(message: Message):
    await message.answer(text="🥺Вы выбрали не тот тип домашнего задания (ожидалось голосовое). Попробуйте еще раз.",
                         reply_markup=kb.tree_can_send, protect_content=True)


@router.message(F.photo | F.video | F.text | F.document | F.sticker | F.voice | F.location | F.contact | F.poll,
                HomeworkState.WaitingForAudio)
async def wrong_type_for_audio(message: Message):
    await message.answer(text="🥺Вы выбрали не тот тип домашнего задания (ожидался аудиофайл). Попробуйте еще раз.",
                         reply_markup=kb.tree_can_send, protect_content=True)

