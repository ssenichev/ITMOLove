import json
import re

import pandas as pd
import requests
import telebot
import sqlite3 as sq
import parse
from hardcode import *
import os
import random
from time import sleep

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
        cursor.execute("INSERT INTO temp_isu (tg_id, isu, course, faculty, program, credentials) VALUES (?, ?, ?, ?, ?, ?)", params)
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
        cursor.execute("SELECT tg_id, isu, course, faculty, program, credentials FROM temp_isu WHERE tg_id=?", [str(call.message.chat.id)])
        tg_id, isu, course, faculty, program, name = cursor.fetchone()

        cursor.execute("UPDATE main SET (ISU, faculty, major, grade, credentials) =(?, ?, ?, ?, ?) WHERE tg_id =?",
                       (int(isu), faculty, program, course, name, call.message.chat.id))
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


@bot.message_handler(content_types=['photo'])
def add_bio(message):
    cursor.execute("UPDATE main SET bio =? WHERE tg_id =?", [str(message.text), str(message.chat.id)])
    db.commit()
    msg = bot.send_message(message.chat.id, "Отправьте ваши фотографии")
    bot.register_next_step_handler(msg, download_photos)


# @bot.message_handler(content_types=['photo'])
# def add_profile_photo(message):
#     bot.register_next_step_handler(message, download_photos)


def download_photos(message):
    """
    Asks user to upload multiple photos and stores it in directory called res
    :param message:
    :return:
    """
    # find the largest photo in the list
    largest_photo = max(message.photo, key=lambda p: p.width * p.height)
    file_id = largest_photo.file_id

    file_info = bot.get_file(file_id)
    file_path = file_info.file_path
    file_name = f'{message.chat.id}{random.randint(1, 100)}.jpg'
    downloaded_file = bot.download_file(file_path)
    # save the downloaded file to your local machine
    with open(f'res/{file_name}', 'wb') as f:
        f.write(downloaded_file)
    sleep(2)
    # download_ph = bot.send_message(message.chat.id, "Фотографии добавлены")
    # bot.register_next_step_handler(download_ph, registration_finale)
    registration_finale(message)


def get_photos(tg_id=691476720):
    """
    Finds all photos from specific telegram user by his tg_id, returns a list of photos
    :param tg_id:
    :return:
    """
    prefix = str(tg_id)

    # get a list of all files in the directory
    files = os.listdir('res')

    # filter the list to only include files that start with the prefix
    filtered_files = [f for f in files if f.startswith(prefix)]

    # create the filtered list of files
    photo_list = []
    for file_name in filtered_files:
        with open(os.path.join('res', file_name), 'rb') as f:
            # add each photo to the list of PhotoSize objects
            photo_list.append(telebot.types.InputMediaPhoto(f.read()))
    return photo_list


def send_photos_with_text(message, target_tg_id=691476720,  displayed_text="zhopa"):
    """
    Sends a message with photos of specific user. User is determined by target_tg_id, displayed_text is just text
    :param message:
    :param target_tg_id:
    :param displayed_text:
    :return:
    """
    # set the text displayed underneath
    photo_list = get_photos(target_tg_id)
    print(photo_list)
    try:
        photo_list[0].caption = displayed_text
        bot.send_media_group(chat_id=message.chat.id, media=photo_list)
    except IndexError:
        bot.send_message(message.chat.id, "Мы не знаем где ваши фото")
    # use send_media_group() method to send all photos in one message


def registration_finale(message):
    bot.send_message(message.chat.id, "Вот так выглядит ваша анкета:")

    cursor.execute("SELECT tg_id, isu, grade, faculty, major, credentials, bio FROM main WHERE tg_id=?", [str(message.chat.id)])
    tg_id, isu, course, faculty, program, credentials, bio = cursor.fetchone()
    send_photos_with_text(message, target_tg_id=message.chat.id, displayed_text=f"{credentials}\n"
                                                                                f"{faculty}\n"
                                                                                f"{program}\n"
                                                                                f"{course}\n"
                                                                                f"{bio}")


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "*написать приветствие*")

    params = (message.chat.id, str(message.chat.username))
    cursor.execute("INSERT INTO main (tg_id, tg_username) VALUES (?, ?)", params)

    isu = bot.send_message(message.chat.id, "Введите ваш номер ИСУ")
    bot.register_next_step_handler(isu, isu_parse)


bot.infinity_polling()
