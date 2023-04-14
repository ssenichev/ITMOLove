import telebot
import os
import random

# bot = telebot.TeleBot()


@bot.message_handler(content_types=['photo'])
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



