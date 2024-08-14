import os
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message
from moviepy.editor import VideoFileClip

router = Router(name=__name__)


def compress_video(input_file, output_file, target_bitrate="1M"):
    clip = VideoFileClip(input_file)
    clip.write_videofile(output_file, bitrate=target_bitrate, codec="libx264")
    return output_file


@router.message(Command('video'))
async def request_video(message: Message):
    await message.answer("Пожалуйста, отправьте видео для сжатия.")


@router.message(F.video)
async def handle_video(message: Message, bot: Bot):
    video_file = await bot.get_file(message.video.file_id)
    file_path = video_file.file_path
    file_name = file_path.split("/")[-1]

    original_file_path = f'application/media/tasks_vocal/{file_name}'
    compressed_file_path = original_file_path.replace('.mp4', '_compressed.mp4')

    await bot.download_file(file_path, original_file_path)

    compress_video(original_file_path, compressed_file_path)

    os.remove(original_file_path)

    await message.answer("Видео сжато и готово к использованию!")
