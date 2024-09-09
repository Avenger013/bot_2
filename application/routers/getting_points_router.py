import locale
import re
import calendar

from datetime import datetime


from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardBuilder, InlineKeyboardMarkup
from sqlalchemy import select

from application.states import Systems, CalendarState
from application.database.models import Student, Task1, Task2, Task3, Task4, Task5, Task6, Task7, async_session
from application.database.requests import get_student_info, get_money_points

import application.keyboard as kb

router = Router(name=__name__)


def generate_month_calendar():
    now = datetime.now()
    year, month = now.year, now.month
    today = now.day

    _, num_days = calendar.monthrange(year, month)

    rows = []

    for day in range(1, num_days + 1):
        text = f"[{day}]" if day == today else str(day)
        button = InlineKeyboardButton(text=text, callback_data=f'day_{day}')
        if len(rows) == 0 or len(rows[-1]) >= 7:
            rows.append([button])
        else:
            rows[-1].append(button)

    back_button = InlineKeyboardButton(text='🔙 Назад', callback_data='reincarnation')
    if len(rows) == 0 or len(rows[-1]) >= 7:
        rows.append([back_button])
    else:
        rows[-1].append(back_button)

    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

    return keyboard


def get_month_year_text():
    now = datetime.now()
    month = month_name_nominative[now.month]
    year = now.year
    return f"{month} {year}"


def get_points_word(points):
    if points % 10 == 1 and points % 100 != 11:
        return "балл"
    elif 2 <= points % 10 <= 4 and (points % 100 < 10 or points % 100 >= 20):
        return "балла"
    else:
        return "баллов"


@router.callback_query(F.data.startswith('receiving'))
async def getting_points(callback: CallbackQuery, state: FSMContext):
    monetization_items = await get_money_points()
    new_markup = await kb.choosing_a_money()
    response_text = "<b>Получение баллов:</b>\n"

    for index, item in enumerate(monetization_items, start=1):
        points_word = get_points_word(item.number_of_points)
        response_text += f"        {index}) {item.task} - <b>{item.number_of_points}</b> {points_word}\n"

    response_text += (
        "\n\n🎁Выберите пункт для получения баллов!\n"
        "└ После указания необходимой информации, мы уведомим администратора и после проверки вам начисляться баллы!"
    )

    await callback.message.edit_text(text=response_text, reply_markup=new_markup, parse_mode='HTML',
                                     protect_content=True)
    await state.set_state(Systems.System)


locale.setlocale(locale.LC_TIME, 'ru_RU.utf8')

month_name_nominative = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь"
}


def generate_month_keyboard():
    months_kb = InlineKeyboardBuilder()

    for month_num in range(1, 13):
        months_kb.add(InlineKeyboardButton(text=month_name_nominative[month_num], callback_data=f'month_{month_num}'))

    months_kb.add(InlineKeyboardButton(text="🔙 Назад", callback_data='reincarnation'))

    return months_kb.adjust(3).as_markup()


@router.callback_query(F.data.startswith('reincarnation'))
async def getting_points_2(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await getting_points(callback, state)


async def set_state_and_respond(callback, state, new_state, text, markup=None):
    await callback.message.edit_text(text=text, reply_markup=markup)
    await state.set_state(new_state)


async def set_state_and_respond_2(callback, state, new_state, text):
    await callback.message.edit_text(text=text, reply_markup=kb.reincarnation)
    await state.set_state(new_state)


@router.callback_query(F.data.startswith('choose_task_'), Systems.System)
async def process_choose_task(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split('_')[2])

    if task_id in {1, 6}:
        calendar_markup = generate_month_calendar()
        month_year_text = get_month_year_text()
        text = f"Пожалуйста, выберите день ({month_year_text}):"
        new_state = CalendarState.Waiting_for_date if task_id == 1 else CalendarState.Waiting_for_date_event
        await set_state_and_respond(callback, state, new_state, text, calendar_markup)

    elif task_id in {2, 3}:
        months_kb = generate_month_keyboard()
        text = "Пожалуйста, выберите месяц:"
        new_state = CalendarState.Waiting_for_month if task_id == 2 else CalendarState.Waiting_for_performance
        await set_state_and_respond(callback, state, new_state, text, months_kb)

    elif task_id in {4, 5}:
        text = "📎 Пожалуйста, отправьте ссылку для проверки."
        new_state = CalendarState.Waiting_for_link if task_id == 4 else CalendarState.Waiting_for_link_review
        await set_state_and_respond_2(callback, state, new_state, text)

    elif task_id == 7:
        text = "Отправьте номер телефона, приглашенного ученика (без +7 или 8 в начале, только 10 цифр):"
        await set_state_and_respond_2(callback, state, CalendarState.Waiting_for_phone, text)


@router.callback_query(CalendarState.Waiting_for_date)
@router.callback_query(CalendarState.Waiting_for_date_event)
async def process_simple_calendar(callback: CallbackQuery, state: FSMContext):
    selected_day = callback.data.split('_')[1]

    current_date = datetime.now().date()

    try:
        selected_date = datetime(year=current_date.year, month=current_date.month, day=int(selected_day)).date()
    except ValueError:
        await callback.answer(text="Выберите корректный день.", show_alert=True)
        return

    if selected_date > current_date:
        await callback.answer(text="Вы не можете выбрать дату позже сегодняшней.", show_alert=True)
        return

    tg_id = callback.from_user.id

    async with async_session() as session:
        student, _, _, _ = await get_student_info(session, tg_id)

        if student:
            student_last_name = student.last_name
            student_first_name = student.name
            student_phone = student.phone
            student_id = student.id

            date_str = selected_date.strftime("%d.%m.%Y")

            query = select(Task6).filter_by(student_id=student_id, date=selected_date.strftime("%d.%m.%Y"))
            result = await session.execute(query)
            existing_task = result.scalars().first()

            if existing_task:
                await callback.answer(text="Вы уже выбрали эту дату. Пожалуйста, выберите другую.", show_alert=True)
                return

            if await state.get_state() == CalendarState.Waiting_for_date_event:
                new_task = Task6(
                    student_id=student_id,
                    name=student_first_name,
                    last_name=student_last_name,
                    phone=student_phone,
                    date=date_str,
                    is_approved=0
                )
            else:
                query = select(Task1).filter_by(student_id=student_id, date=selected_date.strftime("%d.%m.%Y"))
                result = await session.execute(query)
                existing_task = result.scalars().first()

                if existing_task:
                    await callback.answer(text="Вы уже выбрали эту дату. Пожалуйста, выберите другую.", show_alert=True)
                    return

                new_task = Task1(
                    student_id=student_id,
                    name=student_first_name,
                    last_name=student_last_name,
                    phone=student_phone,
                    date=date_str,
                    is_approved=0
                )

            session.add(new_task)
            await session.commit()
            await callback.message.edit_text(
                text='Данные отправлены администратору для проверки.',
                reply_markup=kb.back3
            )
            await state.clear()
        else:
            await callback.message.edit_text('Не удалось найти информацию о пользователе.')
            await state.clear()


@router.callback_query(F.data.startswith('month_'), CalendarState.Waiting_for_month)
async def process_choose_month(callback: CallbackQuery, state: FSMContext):
    month_num = int(callback.data.split('_')[1])
    current_year = datetime.now().year
    month_name_str = month_name_nominative[month_num]

    tg_id = callback.from_user.id
    async with async_session() as session:
        student, _, _, _ = await get_student_info(session, tg_id)

        if student:
            student_last_name = student.last_name
            student_first_name = student.name
            student_phone = student.phone
            student_id = student.id

            query = select(Task2).filter_by(student_id=student_id, month=month_name_str, year=current_year)
            result = await session.execute(query)
            existing_task = result.scalars().first()

            if existing_task:
                await callback.answer(text="Вы уже выбрали этот месяц. Пожалуйста, выберите другой.", show_alert=True)
                return

            new_task = Task2(
                student_id=student_id,
                name=student_first_name,
                last_name=student_last_name,
                phone=student_phone,
                month=month_name_str,
                year=current_year,
                is_approved=0
            )
            session.add(new_task)
            await session.commit()
            await callback.message.edit_text(text='Данные отправлены администратору для проверки.',
                                             reply_markup=kb.back3)
            await state.clear()
        else:
            await callback.message.edit_text('Не удалось найти информацию о пользователе.')
            await state.clear()


@router.callback_query(F.data.startswith('month_'), CalendarState.Waiting_for_performance)
async def process_choose_month(callback: CallbackQuery, state: FSMContext):
    month_num = int(callback.data.split('_')[1])
    current_year = datetime.now().year
    month_name_str = month_name_nominative[month_num]

    tg_id = callback.from_user.id
    async with async_session() as session:
        student, _, _, _ = await get_student_info(session, tg_id)

        if student:
            student_last_name = student.last_name
            student_first_name = student.name
            student_phone = student.phone
            student_id = student.id
            new_task = Task3(
                student_id=student_id,
                name=student_first_name,
                last_name=student_last_name,
                phone=student_phone,
                month=month_name_str,
                year=current_year,
                is_approved=0
            )
            session.add(new_task)
            await session.commit()
            await callback.message.edit_text(text='Данные отправлены администратору для проверки.',
                                             reply_markup=kb.back3)
            await state.clear()
        else:
            await callback.message.edit_text('Не удалось найти информацию о пользователе.')
            await state.clear()


def find_links(text):
    url_regex = r'https?://[^\s]+'
    return re.findall(url_regex, text)


@router.message(F.text, CalendarState.Waiting_for_link)
async def process_received_link(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    links = find_links(message.text)

    if not links:
        await message.answer(text="❌ Пожалуйста, отправьте корректную ссылку!")
        return

    async with async_session() as session:
        student = await session.scalar(select(Student).where(Student.tg_id == tg_id))
        if not student:
            await message.answer(text="❌ Студент не найден.")
            await state.clear()
            return

        current_date = datetime.now().strftime("%d.%m.%Y")

        student_last_name = student.last_name
        student_first_name = student.name
        student_phone = student.phone
        student_id = student.id
        new_task = Task4(
            student_id=student_id,
            name=student_first_name,
            last_name=student_last_name,
            phone=student_phone,
            date=current_date,
            link=links[0],
            is_approved=0
        )
        session.add(new_task)
        await session.commit()
        await message.answer(text='Данные отправлены администратору для проверки.', reply_markup=kb.back3)

    await state.clear()


@router.message(F.text, CalendarState.Waiting_for_link_review)
async def process_received_link_review(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    links = find_links(message.text)

    if not links:
        await message.answer(text="❌ Пожалуйста, отправьте корректную ссылку!")
        return

    async with async_session() as session:
        student = await session.scalar(select(Student).where(Student.tg_id == tg_id))
        if not student:
            await message.answer(text="❌ Студент не найден.")
            await state.clear()
            return

        current_date = datetime.now().strftime("%d.%m.%Y")

        student_last_name = student.last_name
        student_first_name = student.name
        student_phone = student.phone
        student_id = student.id
        new_task = Task5(
            student_id=student_id,
            name=student_first_name,
            last_name=student_last_name,
            phone=student_phone,
            date=current_date,
            link=links[0],
            is_approved=0
        )
        session.add(new_task)
        await session.commit()
        await message.answer(text='Данные отправлены администратору для проверки.', reply_markup=kb.back3)

    await state.clear()


@router.message(F.photo | F.video | F.document | F.sticker | F.voice | F.location | F.contact | F.poll | F.audio,
                CalendarState.Waiting_for_link)
async def wrong_message_type(message: Message):
    await message.answer(text="❌ Ожидалась ссылка, а не другое сообщение. Попробуйте еще раз.")


@router.message(CalendarState.Waiting_for_phone)
async def receive_phone(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    raw_phone = message.text.strip()

    if not raw_phone.isdigit() or len(raw_phone) != 10:
        await message.answer(
            text="Неверный формат номера телефона. Пожалуйста, введите 10 цифр номера, без +7 или 8 в начале",
            protect_content=True
        )
        return

    async with async_session() as session:
        student, _, _, _ = await get_student_info(session, tg_id)
        if student:
            formatted_phone = f"+7 ({raw_phone[:3]}) {raw_phone[3:6]}-{raw_phone[6:8]}-{raw_phone[8:]}"
            student_last_name = student.last_name
            student_first_name = student.name
            student_phone = student.phone
            student_id = student.id
            new_task = Task7(
                student_id=student_id,
                name=student_first_name,
                last_name=student_last_name,
                phone=student_phone,
                phone_friend=formatted_phone,
                is_approved=0
            )
            session.add(new_task)
            await session.commit()
            await message.answer(text='Данные отправлены администратору для проверки.', reply_markup=kb.back3)
        else:
            await message.answer(text="Не удалось найти информацию о пользователе.")
    await state.clear()
