import asyncio
import logging
from datetime import datetime
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, and_

from application.database.models import async_session, DailyCheckIn, Student, DailyCheckInVocal
from config import TOKEN

bot = Bot(token=TOKEN)


async def check_and_notify_students():
    today = datetime.now().date()

    async with async_session() as session:
        students = await session.execute(select(Student))
        students = students.scalars().all()

        for student in students:
            specialisation_student = student.specialisation_student

            if specialisation_student == "Гитара" or specialisation_student == "Вокал и Гитара":
                daily_check_in_guitar = await session.execute(
                    select(DailyCheckIn)
                    .where(and_(DailyCheckIn.student_id == student.id, DailyCheckIn.date == today))
                )
                daily_check_in_guitar = daily_check_in_guitar.scalars().first()

            if specialisation_student == "Вокал" or specialisation_student == "Вокал и Гитара":
                daily_check_in_vocal = await session.execute(
                    select(DailyCheckInVocal)
                    .where(and_(DailyCheckInVocal.student_id == student.id, DailyCheckInVocal.date == today))
                )
                daily_check_in_vocal = daily_check_in_vocal.scalars().first()

            if specialisation_student == "Вокал":
                if not daily_check_in_vocal:
                    await bot.send_message(
                        chat_id=student.tg_id,
                        text="📌Вы сегодня еще не отмечались, отметьтесь пожалуйста!",
                        protect_content=True
                    )
            elif specialisation_student == "Гитара":
                if not daily_check_in_guitar:
                    await bot.send_message(
                        chat_id=student.tg_id,
                        text="📌Вы сегодня еще не отмечались, отметьтесь пожалуйста!",
                        protect_content=True
                    )
            elif specialisation_student == "Вокал и Гитара":
                if not daily_check_in_guitar and not daily_check_in_vocal:
                    await bot.send_message(
                        chat_id=student.tg_id,
                        text="📌Вы сегодня еще не отмечались по обеим специализациям, отметьтесь пожалуйста!",
                        protect_content=True
                    )
                elif not daily_check_in_guitar:
                    await bot.send_message(
                        chat_id=student.tg_id,
                        text="📌Вы сегодня еще не отметились по Гитаре, отметьтесь пожалуйста!",
                        protect_content=True
                    )
                elif not daily_check_in_vocal:
                    await bot.send_message(
                        chat_id=student.tg_id,
                        text="📌Вы сегодня еще не отметились по Вокалу, отметьтесь пожалуйста!",
                        protect_content=True
                    )

scheduler = AsyncIOScheduler()

scheduler.add_job(check_and_notify_students, 'cron', hour=15)


def start_scheduler():
    scheduler.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_scheduler()
    asyncio.get_event_loop().run_forever()
