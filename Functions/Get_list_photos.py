import os

# Получение списка фотографий в папке
def get_photos(folder, extensions=('.jpg', '.jpeg', '.png')):
    photos = []
    for item in os.listdir(folder):
        print(item)
        item_path = os.path.join(folder, item)
        if os.path.isfile(item_path):
            # Извлекаем расширение файла
            file_extension = os.path.splitext(item)[1].lower()
            if file_extension in extensions:
                photos.append(item_path)
    return photos

abs_path = '/home/user/Pictures/123/Мужское/Nike/'
a = get_photos(abs_path)
print(len(a))
