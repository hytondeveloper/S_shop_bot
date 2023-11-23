import os
import sqlite3

async def DB_add_user(database_path, user_id, reg_date, user_name):
    """
    Функция отвечающая за клиентскую БД пользователей.
    :param database_path: str (Путь к файлу базы данных)
    :param user_id: int (Ай ди юзера)
    :param reg_date: str (Дата регистрации в боте)
    :param user_name: str (Имя пользователя)
    :param status: int (Показывает статус пользователя-заблокирован ли он, 0 = не заблокирован / 1 = заблочен)
    :return: bool
    """
    # Получите абсолютный путь к файлу базы данных
    db_path = os.path.join(database_path, 'users.db')


    if not os.path.exists(db_path):
        # Создаем новую базу данных и таблицу
        conn = sqlite3.connect(db_path)
        conn.execute('''CREATE TABLE users
                    (id INT PRIMARY KEY     NOT NULL,
                    reg_date           TEXT    NOT NULL,
                    user_name           TEXT    NOT NULL,
                    status           INT    NOT NULL);''')
        conn.close()

    conn = sqlite3.connect(db_path)

    # Проверяем юзера в базе данных
    cursor = conn.execute("SELECT status FROM users WHERE id=?", (user_id,))
    result = cursor.fetchone()

    if result is None:
        # Если юзера нет в базе данных, то добавляем данные в таблицу
        conn.execute("INSERT INTO users (id, reg_date, user_name, status) VALUES (?, ?, ?, ?)",
                     (user_id, reg_date, user_name, 0))
        conn.commit()
        conn.close()
        print('+ Данные добавлены +')
        return True
    else:
        # Если юзер есть, проверяем его статус
        if result[0] == 0:
            print('+ Статус пользователя: 0 +')
            conn.close()
            return True
        else:
            print('+ Статус пользователя: 1 +')
            conn.close()
            return False

