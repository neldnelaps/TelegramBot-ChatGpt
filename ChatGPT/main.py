from aiogram.types import message
import openai
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

openai.api_key = ''
API_TOKEN = ''
 
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler()
async def send (message: types.Message):
    print(message.text)
    response = openai.Completion.create(
    model="text-davinci-003",
    prompt=message.text,
    temperature=0.9,
    max_tokens=150,
    top_p=1,
    frequency_penalty=0.0,
    presence_penalty=0.6,
    stop=[" Human:", " AI:"]
)
    await message.answer(response['choices'][0]['text'])

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)