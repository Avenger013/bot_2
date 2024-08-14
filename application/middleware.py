from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Awaitable, Dict, Any


class ResetStateMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        commands_to_reset = ['/profile', '/homework', '/top', '/leader', '/monetization', '/info', '/support',
                             '/mark', '/start', '/newsletter']

        if event.text:
            if any(event.text.startswith(command) for command in commands_to_reset):
                state = data.get('state')
                if state is not None:
                    await state.clear()
                    print("Состояние сброшено.")

        return await handler(event, data)