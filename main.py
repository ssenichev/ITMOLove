import json
import re

import pandas as pd
import requests
import telebot
import sqlite3 as sq
from token import token

bot = telebot.TeleBot(token)
db = sq.connect('grinder.db', check_same_thread=False)
cursor = db.cursor()


def isu_parse(message):
    isu = message.text
    # тут парсинг или другое что-то
    confirmation = bot.send_message(message.chat.id, "Верны ли ваши данные:")
    # вывести данные
    bot.register_next_step_handler(confirmation, _isu_parse, isu)


def _isu_parse(message, isu: str):
    if message.text == r'Да':
        cursor.execute("UPDATE main SET ISU =? WHERE tg_id =?", (int(isu), message.chat.id))
        db.commit()
        set_gender(message)

    else:
        isu = bot.send_message(message.chat.id, "Введите ваш номер ИСУ")
        bot.register_next_step_handler(isu, isu_parse)


def set_gender(message):
    gender_markup = telebot.types.InlineKeyboardMarkup()
    gender_markup.add(telebot.types.InlineKeyboardButton('Мужчина', callback_data='male'),
                      telebot.types.InlineKeyboardButton('Женщина', callback_data='female'),
                      telebot.types.InlineKeyboardButton('Иное', callback_data='trans'))
    bot.send_message(message.chat.id, text='Ваш гендер?', reply_markup=gender_markup)


@bot.callback_query_handler(func=lambda call: call.data in ['male', 'female', 'trans'])
def _set_gender(call):
    cursor.execute("UPDATE main SET gender =? WHERE tg_id =?", (call.data, call.message.chat.id))
    db.commit()
    set_ed_level(call.message)


def set_ed_level(message):
    education_markup = telebot.types.InlineKeyboardMarkup()
    education_markup.add(telebot.types.InlineKeyboardButton('Бакалавриат', callback_data='bachelor'),
                         telebot.types.InlineKeyboardButton('Магистратура', callback_data='master'),
                         telebot.types.InlineKeyboardButton('Аспирантура', callback_data='xz'))
    bot.send_message(message.chat.id, text='Уровень вашего образования?', reply_markup=education_markup)


@bot.callback_query_handler(func=lambda call: call.data in ['bachelor', 'master', 'xz'])
def _set_ed_level(call):
    cursor.execute("UPDATE main SET education_level =? WHERE tg_id =?", (call.data, call.message.chat.id))
    db.commit()
    bio = bot.send_message(call.message.chat.id, "Напишите вкратце о себе")
    bot.register_next_step_handler(bio, add_bio)


def add_bio(message):
    cursor.execute("UPDATE main SET bio =? WHERE tg_id =?", (message.text, message.chat.id))
    db.commit()


@bot.message_handler(content_types=['photo'])
def add_profile_photo(message):
    bot.send_message(message.chat.id, "Отправьте ваши фотографии")
    fileID = message.photo[-1].file_id
    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)

    # тут просто код спизженный, пока так, дальше это надо будет сохранять просто в дб
    with open(f"{message.chat.id}.jpg", 'wb') as new_file:
        new_file.write(downloaded_file)


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "*написать приветствие*")

    params = (message.chat.id, str(message.chat.username))
    cursor.execute("INSERT INTO main (tg_id, tg_username) VALUES (?, ?)", params)
    db.commit()

    isu = bot.send_message(message.chat.id, "Введите ваш номер ИСУ")
    bot.register_next_step_handler(isu, isu_parse)


bot.infinity_polling()
