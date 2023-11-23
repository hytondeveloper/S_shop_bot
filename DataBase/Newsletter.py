import sqlite3
import os
from main import bot


async def send_newsletter_to_all_users(database_path, message):
    """
    Функция отвечающая за рассылку сообщение по БД клиентов
    """

    # Получите абсолютный путь к файлу базы данных
    db_path = os.path.join(database_path, 'users.db')

    if not os.path.exists(db_path):
        return 'Нет БД'

    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Получаем всех пользователей
    cursor.execute("SELECT id FROM users")
    all_users = cursor.fetchall()

    # Отправляем сообщение каждому пользователю
    for user_id in all_users:
        try:
            await bot.send_message(user_id[0], message)
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user_id[0]}: {e}")

    # Закрываем соединение с базой данных
    cursor.close()
    conn.close()