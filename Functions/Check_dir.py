import os

async def get_folders_with_photos(BASE_DIR):
    """
    Функция для получения названий фотографий по заданному пути
    :param BASE_DIR: --> заданный путь
    :return: Список из полученных названий
    """
    photo_model_names = []

    for item in os.listdir(BASE_DIR):
        item_path = os.path.join(BASE_DIR, item)

        if os.path.isdir(item_path):
            # Рекурсивный вызов для подпапки и собирание данных из нее
            subfolder_photo_model_names = await get_folders_with_photos(item_path)
            photo_model_names.extend(subfolder_photo_model_names)
        else:
            file_extension = os.path.splitext(item)[1].lower()
            if file_extension in ('.jpg', '.jpeg', '.png'):
                model_name = os.path.splitext(item)[0].lower()
                photo_model_names.append(model_name)
                # print(model_name)

    return photo_model_names
