import telebot
import webbrowser
from telebot import types


bot = telebot.TeleBot('7398122095:AAH_v61qXH31kLoJ_K5FGGskF7hLrtMZX_w')

manager_chat_id = '-4240460478'
# image = 'меню.jpg'
# file = open('./' + image, 'rb')
# @bot.message_handler(commands=['site', 'website'])
# def site(message):
#     webbrowser.open('http://127.0.0.1:8000/')

# @bot.message_handler(commands=['start'])
# def main(message):
#     bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}')


# @bot.message_handler(commands=['help'])
# def main(message):
#     bot.send_message(message.chat.id, 'Чем я могу тебе помочь?')


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton('Перейти на сайт')
    markup.row(btn1)
    btn2 = types.KeyboardButton('Посмотреть меню')
    markup.row(btn2)
    btn3 = types.KeyboardButton('Акции и скидки')
    markup.row(btn3)
    btn4 = types.KeyboardButton('Адреса и время работы')
    markup.row(btn4)
    btn5 = types.KeyboardButton('Связаться с менеджером')
    markup.row(btn5)
    btn6 = types.KeyboardButton('Забронировать/отменить бронированирование столика')
    markup.row(btn6)
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}', reply_markup=markup)
    bot.register_next_step_handler(message, on_click)


@bot.message_handler(func=lambda message: True)
def on_click(message):
    if message.text == 'Перейти на сайт':
        webbrowser.open('http://127.0.0.1:8000/')
    elif message.text == 'Посмотреть меню':
        bot.reply_to(message, 'Вот наше меню, также советуем посмотреть наши акции!')
        image = 'меню.jpg'
        file = open('./' + image, 'rb')
        bot.send_photo(message.chat.id, file)
    elif message.text == 'Акции и скидки':
        bot.reply_to(message, "Наши сезонные акции, также доступны скидки в день рождения(при предъявлении паспорта или других документов, удостоверяющих личность)")
        image1 = 'акции.jpg'
        file = open('./' + image1, 'rb')
        bot.send_photo(message.chat.id, file)
    elif message.text == 'Адреса и время работы':
        bot.send_message(message.chat.id, """г.Москва ул. Иситовна, д.2б
        пн-сб: 9.00 - 23.00
        вс-выходной""")
    elif message.text == 'Связаться с менеджером':
        bot.send_message(message.chat.id, "Ваше сообщение будет передано менеджеру. \
                                              \nВведите ваш вопрос или сообщение:")
        bot.register_next_step_handler(message, handle_manager_message)
    elif message.text == 'Забронировать/отменить бронированирование столика':
        bot.send_message(message.chat.id, 'Для бронирования или его отмены, Вы можете воспользоваться нашим сайтом http://127.0.0.1:8000/')
    else:
        bot.send_message(message.chat.id, "Я не понимаю ваш запрос.")


def handle_manager_message(message):
    user_message = message.text
    user_info = f"Пользователь: @{message.from_user.username} (ID: {message.from_user.id})\n" \
                f"Сообщение: {user_message}"

    send_message_to_manager(manager_chat_id, user_info)

    bot.send_message(message.chat.id, "Ваше сообщение успешно отправлено менеджеру. \
                                            \nМы свяжемся с вами в ближайшее время.")


def send_message_to_manager(chat_id, message):
    try:
        bot.send_message(chat_id, message)
    except Exception as e:
        print(f"Ошибка при отправке сообщения менеджеру: {e}")


bot.polling(none_stop=True)
