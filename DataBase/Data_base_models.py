import os
import sqlite3


async def data_base_models(abs_path_database, model):
    """
    Функция отвечающая за БД моделей кроссовок.
    :param abs_path_database: str (абсолютный путь к файлу базы данных)
    :param model: str (Модель обуви)
    :param size: float (Размер пары обуви)
    :param price: float (Цена пары обуви)
    :return:
    """
    # Получите абсолютный путь к файлу базы данных
    db_path = os.path.join(abs_path_database, 'database_models.db')

    # Проверяем наличие файла базы данных
    if not os.path.exists(db_path):
        # Создаем новую базу данных и таблицу
        conn = sqlite3.connect(db_path)
        conn.execute('''CREATE TABLE database_models
                (model TEXT     NOT NULL,
                size TEXT,
                price TEXT);''')
        conn.close()

    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)

    # проверяем модель кроссовок в БД:
    cursor = conn.execute("SELECT size, price FROM database_models WHERE model=?", (model,))
    result = cursor.fetchone()

    if result is not None:
        size, price = result
        # size=размер, price=цена
        text = f'Модель: {model.upper()}\nРазмеры: {size}\nЦена: {price}'
        # Закрываем соединение с базой данных
        conn.close()
        return text

    else:
        # Закрываем соединение с базой данных
        conn.close()
        # Модель не найдена, обработайте этот случай по вашему усмотрению
        text = f'Данные о модели не найдены'
        return text


########################################################################################################################

async def get_all_models(abs_path_database):
    """
    Функция отвеающая за сбор всех моделей кроссовок с БД --> 'database_models.db'
    :return list: Список всх моделей из БД
    """

    # Получите абсолютный путь к файлу базы данных
    db_path = os.path.join(abs_path_database, 'database_models.db')
    # Подключитесь к базе данных, используя абсолютный путь
    conn = sqlite3.connect(db_path)
    # Выполняем SQL-запрос для выбора всех моделей
    cursor = conn.execute("SELECT DISTINCT model FROM database_models")
    # Получаем результаты запроса
    models = [row[0] for row in cursor.fetchall()]
    # Закрываем соединение с базой данных
    conn.close()

    return models



########################################################################################################################
async def add_models_to_db(abs_path_database, models):
    """
    Функция для добавления моделей кроссовок в БД без заполнения размера и цены.
    :param abs_path_database: str (абсолютный путь к файлу базы данных)
    :param models: list of str (список моделей обуви)
    :return: str (сообщение о результате операции)
    """

    # Получите абсолютный путь к файлу базы данных
    db_path = os.path.join(abs_path_database, 'database_models.db')
    # Проверяем наличие файла базы данных
    if not os.path.exists(db_path):
        # Создаем новую базу данных и таблицу
        conn = sqlite3.connect(db_path)
        conn.execute('''CREATE TABLE database_models
                (model TEXT     NOT NULL,
                size TEXT,
                price TEXT);''')
        conn.close()

    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    for model in models:
        # Проверяем, есть ли модель в БД
        cursor = conn.execute("SELECT model FROM database_models WHERE model=?", (model,))
        result = cursor.fetchone()
        if result is None:
            # Модель не найдена, добавляем ее в БД
            conn.execute("INSERT INTO database_models (model) VALUES (?)", (model,))
            conn.commit()

    # Закрываем соединение с базой данных
    conn.close()

    return ('✅ Модели успешно добавлены в базу данных мой хозяин❗️\n⚠️ Прошу Вас не забывать о том, что кнопкой <Обновить '
            '🔧 БД> пользуйтесь ТОЛЬКО при необходимости ☝🏽, а то я могу 🔩поломаться⚙️\nДоброго Вам здоровьеца 💪🏽, хорошего'
            ' настроения 🤙🏽 и нереальных продаж💵\nВаш слуга ➡️ 🦾🤖 бот')


# # Пример использования функции
# list1 = ['new-balance-574-groen-lichtgroen-groen-0196', 'new-balance-574-donkerblauw-blauw-donkerblauw-019', 'lacoste white', 'lacoste black', 'vans', 'какие то модные тяги', 'lacost standart', 'nike_air_max', 'nike_airvapormax_plus']
# database_name = 'database_models.db'
# add_models_to_database(list1, database_name)
