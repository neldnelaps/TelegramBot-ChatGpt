import logging
import time
from aiogram import Bot, Dispatcher, executor, types
import openai
from aiogram.types.message import ContentType

bot_token = '****:*******'
api_key = '**************'
pay_key = '****:TEST:****'

# Set up logging
logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_token)
dp = Dispatcher(bot)

openai.api_key = api_key

# prices
PRICE = types.LabeledPrice(label="Подписка на 1 месяц", amount=500*100)  # в копейках (руб)

# Create a dictionary to store messages for each user
messages = {}

# buy
@dp.message_handler(commands=['buy'])
async def buy(message: types.Message):
    if pay_key.split(':')[1] == 'TEST':
        await bot.send_message(message.chat.id, "Тестовый платеж!!!")

    await bot.send_invoice(message.chat.id,
                           title="Подписка на бота",
                           description="Активация подписки на бота на 1 месяц",
                           provider_token=pay_key,
                           currency="rub",
                           photo_url="",
                           photo_width=416,
                           photo_height=234,
                           photo_size=416,
                           is_flexible=False,
                           prices=[PRICE],
                           start_parameter="one-month-subscription",
                           payload="test-invoice-payload")
# pre checkout  (must be answered in 10 seconds)
@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

# successful payment
@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    print("SUCCESSFUL PAYMENT:")
    payment_info = message.successful_payment.to_python()
    for k, v in payment_info.items():
        print(f"{k} = {v}")

    await bot.send_message(message.chat.id,
                           f"Платеж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} прошел успешно!!!")
                          


# Handle the /start command
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    try:
        username = message.from_user.username
    except AttributeError:
        await message.answer("Please set a username in Telegram settings and try again.")
        return
    messages[username] = []
    await message.answer(
        "Hello, I'm bot powered on API GPT-3.5-turbo (ChatGPT).\n These are your options:\n/help - Show this help "
        "message\n/newtopic - Start a new chat\n/image - Create image on prompt\n/buy - pay for a 1 month subscription"
        )

# Handle the /newtopic command
@dp.message_handler(commands=['newtopic'])
async def new_topic_cmd(message: types.Message):
    username = message.from_user.username
    messages[username] = []
    await message.answer("Created new chat!")

@dp.message_handler(commands=['image'])
async def image_cmd(message: types.Message):
    user_message = message.text
    username = message.from_user.username
    # If this is the first message from the user, create a new list to store messages
    if username not in messages:
        messages[username] = []
    # Add user's message to the message list
    messages[username].append({"role": "user", "content": user_message})
    messages[username].append({"role": "system", "content": "You are a Helpful assistant."})

    # Log the user's message
    logging.info(f'{username}: {user_message}')

    # Check if this message is a reply to a previous message from the bot
    should_respond = not message.reply_to_message or message.reply_to_message.from_user.id == bot.id

    # If this is a new message or a message that the bot needs to respond to
    if should_respond:
        response = openai.Image.create(
        prompt=user_message,
        n=1,
        size="1024x1024"
        )
        image_url = response['data'][0]['url']
        await message.answer(image_url)


# Handle the /help command
@dp.message_handler(commands=['help'])
async def help_cmd(message: types.Message):
    help_text = "/help - Show this help message\n/newtopic - Start a new chat\n/image - Create image on prompt\n/buy - pay for a 1 month subscription"
    await message.answer(help_text)

# Handle all other messages
@dp.message_handler()
async def echo_msg(message: types.Message):
    user_message = message.text
    username = message.from_user.username
    # If this is the first message from the user, create a new list to store messages
    if username not in messages:
        messages[username] = []
    # Add user's message to the message list
    messages[username].append({"role": "user", "content": user_message})
    messages[username].append({"role": "system", "content": "You are a Helpful assistant."})

    # Log the user's message
    logging.info(f'{username}: {user_message}')

    # Check if this message is a reply to a previous message from the bot
    should_respond = not message.reply_to_message or message.reply_to_message.from_user.id == bot.id

    # If this is a new message or a message that the bot needs to respond to
    if should_respond:
        # Use OpenAI to generate a response
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages[username],
            temperature=0.7,
            frequency_penalty=0.1,
            presence_penalty=0.1,
            user=username
        )
        chatgpt_response = completion.choices[0]['message']
        messages[username].append({"role": "assistant", "content": chatgpt_response['content']})

        # Log the bot's response
        logging.info(f'ChatGPT response: {chatgpt_response["content"]}')

        # Send the bot's response to the chat
        await message.reply(chatgpt_response['content'], parse_mode='Markdown')

logging.info("Bot started at %s", time.strftime('%Y-%m-%d %H:%M:%S'))
executor.start_polling(dp, skip_updates=True)