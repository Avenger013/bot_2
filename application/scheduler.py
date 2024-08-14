import asyncio
import logging
from datetime import datetime
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, and_

from application.database.models import async_session, DailyCheckIn, Student
from config import TOKEN

bot = Bot(token=TOKEN)


async def check_and_notify_students():
    today = datetime.now().date()

    async with async_session() as session:
        students = await session.execute(select(Student))
        students = students.scalars().all()

        for student in students:
            daily_check_in = await session.execute(
                select(DailyCheckIn)
                .where(and_(DailyCheckIn.student_id == student.id, DailyCheckIn.date == today))
            )
            daily_check_in = daily_check_in.scalars().first()

            if not daily_check_in:
                await bot.send_message(chat_id=student.tg_id,
                                       text="📌Вы сегодня еще не отмечались, отметьтесь, пожалуйста!",
                                       protect_content=True)

scheduler = AsyncIOScheduler()

scheduler.add_job(check_and_notify_students, 'cron', hour=15)


def start_scheduler():
    scheduler.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_scheduler()
    asyncio.get_event_loop().run_forever()
