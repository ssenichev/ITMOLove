import json
import re

import pandas as pd
import requests
import telebot
import sqlite3 as sq
import parse
from hardcode import *
from photoservice import *

bot = telebot.TeleBot(token)
db = sq.connect('grinder.db', check_same_thread=False)
cursor = db.cursor()


def isu_parse(message):
    isu = message.text
    if len(isu) == 6:
        driver = parse.setup_browser(login_url="https://isu.ifmo.ru/", login=isu_username, password=isu_password)
        course, faculty, program, name = parse.get_student_info(isu=isu, driver=driver, timeout=3)

        bot.send_message(message.chat.id, f"Имя: {name}\n"
                                          f"Факультет: {faculty}\n"
                                          f"ОП: {program}\n"
                                          f"Курс: {course}")

        params = (message.chat.id, isu, course, faculty, program, name)
        cursor.execute("INSERT INTO temp_isu (tg_id, isu, course, faculty, program, name) VALUES (?, ?, ?, ?, ?, ?)", params)
        db.commit()

        confirmation_markup = telebot.types.InlineKeyboardMarkup()
        confirmation_markup.add(telebot.types.InlineKeyboardButton('Да', callback_data='isu_verification|yes'),
                                telebot.types.InlineKeyboardButton('Нет', callback_data='isu_verification|no'))
        bot.send_message(message.chat.id, "Верны ли ваши данные?", reply_markup=confirmation_markup)

    else:
        isu = bot.send_message(message.chat.id, "Введите корректный номер ИСУ")
        bot.register_next_step_handler(isu, isu_parse)


@bot.callback_query_handler(func=lambda call: call.data.startswith('isu_verification'))
def isu_verification(call):
    if call.data == 'isu_verification|yes':
        cursor.execute("SELECT tg_id, isu, course, faculty, program, name FROM temp_isu WHERE tg_id='148249969'")
        tg_id, isu, course, faculty, program, name = cursor.fetchone()

        cursor.execute("UPDATE main SET (ISU, faculty, major, grade) =(?, ?, ?, ?) WHERE tg_id =?",
                       (int(isu), faculty, program, course, call.message.chat.id))
        set_gender(call.message)

    elif call.data == 'isu_verification|no':
        isu = bot.send_message(call.message.chat.id, "Введите ваш номер ИСУ")
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
    add_profile_photo(message)


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

    isu = bot.send_message(message.chat.id, "Введите ваш номер ИСУ")
    bot.register_next_step_handler(isu, isu_parse)


bot.infinity_polling()
