import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher

from application.database.models import async_main
from config import TOKEN
from application.routers import router as main_router
from application.utils.commands import set_commands
from application.middleware import ResetStateMiddleware
from application.scheduler import start_scheduler


async def main():
    await async_main()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.message.middleware.register(ResetStateMiddleware())
    dp.include_router(main_router)

    await set_commands(bot)
    start_scheduler()
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')